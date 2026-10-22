from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class RequestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.team = cls.env['crm.team'].create({'name': 'Request test team', 'company_id': cls.company.id})
        cls.website = cls.env['website'].create({
            'name': 'Request test website', 'company_id': cls.company.id,
            'torrepulia_request_team_id': cls.team.id, 'torrepulia_commercial_mode': 'request',
        })
        cls.other_site = cls.env['website'].create({'name': 'Standard test website', 'company_id': cls.company.id})
        cls.public = cls.env.ref('base.public_user')
        cls.portal = cls.env['res.users'].create({
            'name': 'Test portal', 'login': 'request-portal@example.invalid',
            'group_ids': [fields.Command.set(cls.env.ref('base.group_portal').ids)],
        })
        cls.sales = cls.env['res.users'].create({
            'name': 'Test sales', 'login': 'request-sales@example.invalid',
            'company_id': cls.company.id, 'company_ids': [fields.Command.set(cls.company.ids)],
            'group_ids': [fields.Command.set(cls.env.ref('sales_team.group_sale_salesman').ids)],
        })
        cls.team.member_ids = cls.sales
        cls.product = cls.env['product.product'].create({
            'name': 'Native catalog test', 'sale_ok': True, 'is_published': True,
            'website_id': cls.website.id, 'list_price': 37.5,
        })

    def _visitor_site(self, site=None, user=None):
        site = site if site is not None else self.website
        return site.with_user(user or self.public).with_context(website_id=site.id)

    def _draft(self, user=None):
        site = self._visitor_site(user=user)
        session = {}
        return site, session, site._torrepulia_session_request(session, create=True)

    def _line(self, draft, site, **kwargs):
        return draft._set_selection(site, self.product.with_env(site.env), 2, **kwargs)

    def _submit(self, draft, site):
        return draft._submit(site, {'contact_name': 'Test visitor', 'email': 'visitor@example.invalid'})

@tagged('post_install', '-at_install')
class TestQuoteRequest(RequestCase):
    def test_standard_defaults_and_independent_settings(self):
        standard = self._visitor_site(self.other_site)
        self.assertFalse(standard._torrepulia_request_enabled())
        self.assertFalse(standard._torrepulia_session_request({}, create=True))
        self.website.torrepulia_request_show_prices = False
        self.assertFalse(self.website._torrepulia_request_prices_visible())
        self.assertTrue(standard._torrepulia_request_prices_visible())
        self.assertEqual(standard._torrepulia_request_url(), '/la-tua-richiesta')
        self.website.torrepulia_request_summary_url = '/richiesta-personalizzata'
        self.assertEqual(self.website._torrepulia_request_url(), '/richiesta-personalizzata')
        self.assertEqual(standard._torrepulia_request_url(), '/la-tua-richiesta')
        settings = self.env['res.config.settings'].create({'website_id': self.website.id})
        settings.torrepulia_request_draft_days = 14
        self.assertEqual(self.website.torrepulia_request_draft_days, 14)
        self.assertEqual(self.other_site.torrepulia_request_draft_days, 30)

    def test_selection_has_no_commercial_side_effects(self):
        counts = {model: self.env[model].search_count([]) for model in
                  ('sale.order', 'crm.lead', 'res.partner', 'mail.mail')}
        price = self.product.list_price
        site, session, draft = self._draft()
        line = self._line(draft, site)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.uom_id, self.product.uom_id)
        self.assertFalse(draft.partner_id)
        self.assertEqual(draft, site._torrepulia_session_request(session))
        self.assertNotEqual(session['torrepulia_request_%s' % site.id], draft.session_digest)
        for model, count in counts.items():
            self.assertEqual(self.env[model].search_count([]), count, model)
        self.assertEqual(self.product.list_price, price)

    def test_session_isolation_and_rotation(self):
        site, session, draft = self._draft()
        self.assertFalse(site._torrepulia_session_request({}))
        forged = {'torrepulia_request_%s' % site.id: str(draft.id)}
        self.assertFalse(site._torrepulia_session_request(forged))
        self.other_site.write({'torrepulia_request_team_id': self.team.id, 'torrepulia_commercial_mode': 'request'})
        other = self._visitor_site(self.other_site)
        copied = {'torrepulia_request_%s' % other.id: session['torrepulia_request_%s' % site.id]}
        self.assertFalse(other._torrepulia_session_request(copied))
        self._line(draft, site)
        self._submit(draft, site)
        self.assertFalse(site._torrepulia_session_request(session))
        self.assertNotEqual(draft, site._torrepulia_session_request(session, create=True))

    def test_submission_and_immutable_snapshot(self):
        site, session, draft = self._draft()
        line = self._line(draft, site)
        source = self.env['utm.source'].create({'name': 'Catalogo test'})
        campaign = self.env['utm.campaign'].create({'name': 'Campagna test'})
        draft.write({'origin': '/shop', 'source_id': source.id, 'campaign_id': campaign.id})
        before_leads = self.env['crm.lead'].search_count([])
        before_orders = self.env['sale.order'].search_count([])
        before_partners = self.env['res.partner'].search_count([])
        before_mail = self.env['mail.mail'].search_count([])
        self._submit(draft, site)
        self.assertEqual(draft.state, 'submitted')
        self.assertEqual(draft.opportunity_id.company_id, self.company)
        self.assertEqual(draft.opportunity_id.team_id, self.team)
        self.assertFalse(draft.opportunity_id.user_id)
        self.assertEqual(draft.opportunity_id.campaign_id, campaign)
        self.assertEqual(draft.opportunity_id.source_id, source)
        self.assertEqual(draft.submission_snapshot['origin'], '/shop')
        self.assertEqual(self.env['crm.lead'].search_count([]), before_leads + 1)
        self.assertEqual(self.env['sale.order'].search_count([]), before_orders)
        self.assertEqual(self.env['res.partner'].search_count([]), before_partners)
        self.assertEqual(self.env['mail.mail'].search_count([]), before_mail)
        name = line.snapshot['name']
        self.product.name = 'Changed catalog title'
        self.assertEqual(line.snapshot['name'], name)
        for action in (lambda: draft.write({'notes': 'tampered'}),
                       lambda: line.write({'quantity': 9}), lambda: line.unlink(),
                       lambda: draft.unlink(), lambda: self._submit(draft, site),
                       lambda: self._line(draft, site)):
            with self.assertRaises(ValidationError):
                action()
        self.assertEqual(self.env['crm.lead'].search_count([]), before_leads + 1)

    def test_public_portal_acl_and_sales_rules(self):
        site, session, draft = self._draft()
        line = self._line(draft, site)
        for user in (self.public, self.portal):
            for record in (draft, line):
                with self.assertRaises(AccessError):
                    record.with_user(user).read(['id'])
                with self.assertRaises(AccessError):
                    record.with_user(user).write({})
                with self.assertRaises(AccessError):
                    record.with_user(user).unlink()
            for model in ('torrepulia.request', 'torrepulia.request.line'):
                with self.assertRaises(AccessError):
                    self.env[model].with_user(user).create({})
        self.assertEqual(draft.with_user(self.sales).read(['name'])[0]['name'], draft.name)
        self.assertEqual(line.with_user(self.sales).read(['quantity'])[0]['quantity'], 2)
        draft.with_user(self.sales).write({'notes': 'Internal draft note'})
        line.with_user(self.sales).write({'quantity': 3})
        self.assertEqual(line.quantity, 3)
        self.team.member_ids = False
        with self.assertRaises(AccessError):
            draft.with_user(self.sales).read(['name'])
        with self.assertRaises(AccessError):
            line.with_user(self.sales).read(['quantity'])
        with self.assertRaises(AccessError):
            draft.with_user(self.sales).write({'notes': 'forbidden'})
        with self.assertRaises(AccessError):
            line.with_user(self.sales).write({'quantity': 4})

    def test_company_isolation(self):
        company = self.env['res.company'].create({'name': 'Other request company'})
        team = self.env['crm.team'].create({'name': 'Other team', 'company_id': company.id})
        website = self.env['website'].create({
            'name': 'Other company website', 'company_id': company.id,
            'torrepulia_request_team_id': team.id, 'torrepulia_commercial_mode': 'request',
        })
        draft = website._torrepulia_session_request({}, create=True)
        with self.assertRaises(AccessError):
            draft.with_user(self.sales).read(['name'])
        manager = self.env['res.users'].create({
            'name': 'Test manager', 'login': 'request-manager@example.invalid',
            'company_id': self.company.id, 'company_ids': [fields.Command.set(self.company.ids)],
            'group_ids': [fields.Command.set(self.env.ref('sales_team.group_sale_manager').ids)],
        })
        with self.assertRaises(AccessError):
            draft.with_user(manager).read(['name'])
        with self.assertRaises(ValidationError):
            self.website.torrepulia_request_team_id = team
        site, session, own_draft = self._draft()
        alien = self.env['product.product'].create({
            'name': 'Other company product', 'company_id': company.id, 'is_published': True,
        })
        with self.assertRaises((AccessError, ValidationError)):
            own_draft._set_selection(site, alien.with_env(site.env), 1)

    def test_catalog_validation_without_allowlist(self):
        site, session, draft = self._draft()
        unrestricted = self.env['product.product'].create({'name': 'Any published product', 'is_published': True})
        self.assertTrue(draft._set_selection(site, unrestricted.with_env(site.env), 1))
        self.product.is_published = False
        with self.assertRaises((AccessError, ValidationError)):
            self._line(draft, site)
        self.product.is_published = True
        self.product.website_id = self.other_site
        with self.assertRaises((AccessError, ValidationError)):
            self._line(draft, site)
        self.product.website_id = self.website
        for qty in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValidationError):
                draft._set_selection(site, self.product.with_env(site.env), qty)
        with self.assertRaises(ValidationError):
            self._line(draft, site, custom_values={'999999': 'foreign attribute'})

    def test_native_variant_and_custom_configuration(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Personalizzazione', 'create_variant': 'no_variant',
            'value_ids': [fields.Command.create({'name': 'Testo libero', 'is_custom': True})],
        })
        variant_attribute = self.env['product.attribute'].create({
            'name': 'Formato nativo', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Formato A'}),
                          fields.Command.create({'name': 'Formato B'})],
        })
        template = self.env['product.template'].create({
            'name': 'Prodotto configurabile', 'is_published': True,
            'attribute_line_ids': [fields.Command.create({
                'attribute_id': attribute.id,
                'value_ids': [fields.Command.set(attribute.value_ids.ids)],
            }), fields.Command.create({
                'attribute_id': variant_attribute.id,
                'value_ids': [fields.Command.set(variant_attribute.value_ids.ids)],
            })],
        })
        value = template.valid_product_template_attribute_line_ids.product_template_value_ids.filtered('is_custom')
        site, session, draft = self._draft()
        product = template.product_variant_ids[-1].with_env(site.env)
        with self.assertRaises(ValidationError):
            draft._set_selection(site, product, 1, no_variant_values=value.with_env(site.env))
        line = draft._set_selection(site, product, 1,
                                    no_variant_values=value.with_env(site.env),
                                    custom_values={str(value.id): 'Richiesta di prova'})
        self._submit(draft, site)
        self.assertEqual(line.product_id, product)
        self.assertEqual(line.no_variant_value_ids, value)
        self.assertEqual(line.snapshot['custom_values'], {str(value.id): 'Richiesta di prova'})

    def test_cleanup_and_expired_session(self):
        site, session, old = self._draft()
        old.last_activity = fields.Datetime.now() - timedelta(days=31)
        self.assertFalse(site._torrepulia_session_request(session))
        fresh = site._torrepulia_session_request(session, create=True)
        _, _, sent = self._draft()
        self._line(sent, site)
        self._submit(sent, site)
        lead = sent.opportunity_id
        self.env['torrepulia.request']._cron_expire_drafts()
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists())
        self.assertTrue(sent.exists())
        self.assertTrue(lead.exists())

    def test_invalid_contact_and_unpublished_at_submission(self):
        site, session, draft = self._draft()
        with self.assertRaises(ValidationError):
            self._submit(draft, site)
        self._line(draft, site)
        with self.assertRaises(ValidationError):
            draft._submit(site, {'contact_name': 'Test', 'email': 'invalid'})
        self.product.is_published = False
        with self.assertRaises((AccessError, ValidationError)):
            self._submit(draft, site)
        self.assertEqual(draft.state, 'draft')
        self.assertFalse(draft.opportunity_id)

    def test_authenticated_contact_and_catalog_access(self):
        site, session, draft = self._draft(user=self.portal)
        self.assertEqual(draft.partner_id, self.portal.partner_id)
        self.website.ecommerce_access = 'logged_in'
        self.assertFalse(self._visitor_site()._torrepulia_session_request({}, create=True))
        self.assertTrue(site._torrepulia_session_request(session))

    def test_settings_validation(self):
        for value in ('https://example.invalid', '//example.invalid', '/x?next=y', '/x\\y', '/%2fevil'):
            with self.assertRaises(ValidationError):
                self.website.torrepulia_request_summary_url = value
        with self.assertRaises(ValidationError):
            self.website.torrepulia_request_draft_days = 0
        with self.assertRaises(ValidationError):
            self.website.torrepulia_request_team_id = False
        with self.assertRaises(ValidationError):
            self.website.torrepulia_request_user_id = self.portal
        self.website.torrepulia_request_user_id = self.sales
        self.assertEqual(self.website.torrepulia_request_user_id, self.sales)

    def test_native_quotation_link(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        self._submit(draft, site)
        order = self.env['sale.order'].create({
            'partner_id': self.portal.partner_id.id, 'company_id': self.company.id,
            'opportunity_id': draft.opportunity_id.id, 'torrepulia_request_id': draft.id,
        })
        self.assertEqual(order.state, 'draft')
        self.assertEqual(draft.quotation_ids, order)
        self.assertEqual(draft.opportunity_id.torrepulia_request_ids, draft)
        with self.assertRaises(ValidationError):
            order.opportunity_id = False
