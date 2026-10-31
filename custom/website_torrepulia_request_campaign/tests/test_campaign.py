import copy
from datetime import timedelta

from lxml import etree

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.addons.website_torrepulia_request.tests.test_request import RequestCase

from ..models.page import harvest_clip, replace_legacy
from odoo.addons.website_torrepulia_theme.controllers.reservation import QUANTITIES
from odoo.addons.base.models.ir_ui_view import get_view_arch_from_file
from odoo.tools import file_path


@tagged('post_install', '-at_install')
class TestCampaign(RequestCase):
    def test_editorial_update_removes_only_obsolete_next_section(self):
        snippet = etree.fromstring('<section data-snippet="s_torrepulia_request_campaign"><div data-review-lazy=""/></section>')
        arch = '''<t><div id="wrap"><section data-snippet="s_torrepulia_request_campaign"
            data-columns="2"><h1>Titolo del gestore</h1><img src="/foto-gestore"/>
            <button data-campaign-scroll="">Scegli i tuoi formati</button><a data-campaign-review="">Completa la tua prenotazione</a>
            <div class="tp-campaign-content"/><div class="tp-campaign-next"><h2>Come prosegue</h2></div>
            <p>Testo approvato del gestore</p></section></div></t>'''
        result = replace_legacy(arch, snippet)
        self.assertNotIn('tp-campaign-next', result)
        self.assertNotIn('data-campaign-scroll', result)
        self.assertNotIn('data-campaign-review', result)
        for retained in ('Titolo del gestore', '/foto-gestore', 'data-columns="2"', 'Testo approvato del gestore'):
            self.assertIn(retained, result)
        self.assertEqual(replace_legacy(result, snippet), result)

    def test_harvest_clip_replaces_only_a_theme_photo(self):
        snippet = etree.fromstring(self.env.ref('website_torrepulia_request_campaign.s_torrepulia_request_campaign').arch_db.encode()).find('section')
        page = ('<t><div id="wrap"><section data-snippet="s_torrepulia_request_campaign"><div class="tp-campaign-hero"><h1>Titolo del gestore</h1>'
                '<img class="img-fluid tp-campaign-photo" src="%s"/></div></section></div></t>')
        theme = harvest_clip(page % '/website_torrepulia_theme/static/src/cinematic/owner/olive-raccolta-1280.webp', snippet)
        self.assertIn('data-tp-clip="olio-verde"', theme)
        self.assertIn('Titolo del gestore', theme)
        self.assertNotIn('olive-raccolta', theme)
        self.assertEqual(harvest_clip(theme, snippet), theme)
        owner = page % '/web/image/912-foto-gestore'
        self.assertEqual(harvest_clip(owner, snippet), owner)

    def test_visual_copy_migration_preserves_editorial_and_later_changes(self):
        snippet = etree.fromstring('<section><div data-review-lazy=""/></section>')
        arch = '<t><div id="wrap"><section data-snippet="s_torrepulia_request_campaign" data-editorial-layout="2"><div class="tp-campaign-hero"><h1>Titolo del gestore</h1><p class="tp-campaign-intro">Vecchia introduzione</p><img src="/foto-gestore"/></div><p>Editoriale esterno</p><div data-review-lazy=""/></section></div></t>'
        result = replace_legacy(arch, snippet)
        self.assertIn('Prenota oggi senza alcun anticipo', result)
        for retained in ('Titolo del gestore', '/foto-gestore', 'Editoriale esterno'):
            self.assertIn(retained, result)
        edited = result.replace('Prenota oggi senza alcun anticipo', 'Successiva modifica del gestore')
        self.assertEqual(replace_legacy(edited, snippet), edited)

    def test_view_arch_file_reader_in_xml_development_mode(self):
        # Exercise the exact Odoo 20 path used by --dev=xml. An inline
        # <field type="xml"><form> has no text node and crashes that reader.
        path = file_path('website_torrepulia_request_campaign/views/campaign.xml')
        for name, tag in [('campaign_list', 'list'), ('campaign_form', 'form')]:
            arch = get_view_arch_from_file(path, 'website_torrepulia_request_campaign.' + name)
            self.assertEqual(etree.fromstring(arch.encode()).tag, tag)

    def test_renamed_legacy_forms_preserve_surrounding_editorial_and_contact_form(self):
        snippet = etree.fromstring('<section data-snippet="s_torrepulia_request_campaign" data-editorial-layout="2"><h1>Titolo nuovo</h1><div data-review-lazy=""/></section>')
        for marker in ('torrepulia_reservation', *QUANTITIES):
            arch = '''<t><div id="wrap"><section data-snippet="gestore-personalizzato">
                <h2>Testo editoriale compatibile</h2><form><input name="%s"/></form>Nota esterna<p>Nota da conservare</p>
                </section><section><form data-model_name="crm.lead"><input name="name" value="Il tuo messaggio"/></form></section>
                </div></t>''' % marker
            migrated = replace_legacy(arch, snippet)
            root = etree.fromstring(migrated.encode())
            self.assertIn('Testo editoriale compatibile', migrated)
            self.assertIn('Nota da conservare', migrated)
            self.assertIn('Nota esterna', migrated)
            self.assertFalse(root.xpath('.//input[@name="%s"]' % marker))
            self.assertEqual(len(root.xpath('.//form')), 1)
            self.assertEqual(migrated.count('data-snippet="s_torrepulia_request_campaign"'), 1)
            self.assertEqual(replace_legacy(migrated, snippet), migrated)
        # Already installed/customised selectors survive residual old forms.
        arch = '<t><div id="wrap"><section data-snippet="s_torrepulia_request_campaign"><h1>Testo modificato</h1></section><form><input name="name" value="Prenotazione olio nuovo 2030"/></form></div></t>'
        migrated = replace_legacy(arch, snippet)
        self.assertIn('Testo modificato', migrated)
        self.assertNotIn('<form', migrated)

    def setUp(self):
        super().setUp()
        self.campaign = self.env['torrepulia.request.campaign'].create({
            'name': 'Campagna test', 'reference': 'campaign-test', 'website_id': self.website.id,
            'state': 'open', 'line_ids': [fields.Command.create({'product_id': self.product.id})]})
        self.website.torrepulia_campaign_id = self.campaign

    def test_preorder_link_only_for_open_website_campaign(self):
        self.assertEqual(self.website._request_preorder_url(), '/prenotailtuoolio')
        self.product.product_tmpl_id.out_of_stock_message = False
        self.assertEqual(self.product.product_tmpl_id._request_stock_notice(self.website)['preorder_url'], '/prenotailtuoolio')
        self.campaign.state = 'closed'
        self.assertFalse(self.website._request_preorder_url())
        self.campaign.write({'state':'open', 'opens_at':fields.Datetime.now()+timedelta(days=1)})
        self.assertFalse(self.website._request_preorder_url())
        self.campaign.write({'opens_at':False,'closes_at':fields.Datetime.now()-timedelta(days=1)})
        self.assertFalse(self.website._request_preorder_url())
        other = self.env['website'].create({'name':'Other preorder website','company_id':self.website.company_id.id})
        self.assertFalse(other._request_preorder_url())

    def test_dates_close_only_showcase_and_leave_selection(self):
        self.assertTrue(self.campaign._is_open())
        site, session, draft = self._draft()
        self._line(draft, site)
        self.campaign.closes_at = fields.Datetime.now() - timedelta(minutes=1)
        self.assertFalse(self.campaign._is_open())
        self.assertTrue(site._torrepulia_request_enabled())
        self.assertEqual(site._request_selection_state(session)['quantity'], 2)
        self.campaign.write({'opens_at': fields.Datetime.now() + timedelta(days=1), 'closes_at': False})
        self.assertFalse(self.campaign._is_open())
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.campaign.closes_at = self.campaign.opens_at - timedelta(hours=1)

    def test_company_website_and_public_acl(self):
        visitor = self._visitor_site()
        self.assertEqual(visitor._public_request_campaign().id, self.campaign.id)
        self.assertFalse(self._visitor_site(self.other_site)._public_request_campaign(self.campaign.id))
        self.assertFalse(visitor._public_request_campaign(-1))
        for user in (self.public, self.portal):
            with self.assertRaises(AccessError):
                self.campaign.with_user(user).read(['name'])
            with self.assertRaises(AccessError):
                self.campaign.line_ids.with_user(user).read(['product_id'])
            with self.assertRaises(AccessError):
                self.campaign.with_user(user).write({'state': 'closed'})
        self.campaign.with_user(self.sales).write({'name': 'Edited through native UI'})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.other_site.torrepulia_campaign_id = self.campaign
        foreign = self.env['product.product'].create({'name': 'Foreign site product', 'website_id': self.other_site.id})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env['torrepulia.request.campaign.line'].create({'campaign_id': self.campaign.id, 'product_id': foreign.id})
        company = self.env['res.company'].create({'name': 'Campaign other company'})
        foreign_website = self.env['website'].create({'name': 'Company B campaign site', 'company_id': company.id})
        foreign_campaign = self.env['torrepulia.request.campaign'].create({
            'name': 'Company B campaign', 'reference': 'company-b', 'website_id': foreign_website.id})
        with self.assertRaises(AccessError):
            foreign_campaign.with_user(self.sales).read(['name'])
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.campaign.website_id = self.other_site

    def test_variant_order_is_explicit_and_catalog_is_unrestricted(self):
        attr = self.env['product.attribute'].create({'name': 'Filtrazione', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Filtrato'}), fields.Command.create({'name': 'Non filtrato'})]})
        template = self.env['product.template'].create({'name': 'Configured native oil', 'is_published': True,
            'attribute_line_ids': [fields.Command.create({'attribute_id': attr.id,
                'value_ids': [fields.Command.set(attr.value_ids.ids)]})]})
        a, b = template.product_variant_ids
        self.campaign.line_ids.unlink()
        lines = self.env['torrepulia.request.campaign.line'].create([
            {'campaign_id': self.campaign.id, 'product_id': a.id, 'sequence': 20},
            {'campaign_id': self.campaign.id, 'product_id': b.id, 'sequence': 10}])
        self.assertEqual(self.campaign.line_ids.sorted('sequence').product_id.ids, [b.id, a.id])
        lines[0].sequence = 0
        self.assertEqual(self.campaign.line_ids.sorted('sequence').product_id.ids, [a.id, b.id])
        site, session, draft = self._draft()
        # A product absent from the campaign remains valid in the shared catalog.
        self._line(draft, site)
        draft._set_selection(site, a.with_env(site.env), 1)
        draft._set_selection(site, b.with_env(site.env), 2)
        self.assertEqual(sorted(draft.line_ids.mapped('quantity')), [1, 2, 2])
        self.assertEqual(len(draft.line_ids), 3)

    def test_scoped_migration_is_idempotent_preserves_builder_and_seo(self):
        self.website.torrepulia_theme_enabled = True
        arch = '''<t t-name="test.campaign.migration"><t t-call="website.layout"><div id="wrap">
        <section data-snippet="custom-before"><p>Editoriale del gestore</p></section>
        <section data-snippet="s_torrepulia_reservation_hero"><h1>Vecchio titolo</h1><img class="tp-reservation-hero-image" src="/gestore/foto-originale.jpg" alt="Foto del gestore"/></section>
        <section data-snippet="s_torrepulia_reservation_form"><form><input name="bib_filtrato"/></form></section>
        <section data-snippet="custom-after"><p>Altro contenuto conservato</p></section>
        </div></t></t>'''
        view = self.env['ir.ui.view'].create({'name': 'Migration fixture', 'type': 'qweb', 'arch_db': arch,
            'website_id': self.website.id, 'key': 'test.campaign.migration'})
        page = self.env['website.page'].create({'name': 'Custom seasonal page', 'url': '/prenotailtuoolio',
            'view_id': view.id, 'website_id': self.website.id, 'is_published': True,
            'website_indexed': False, 'website_meta_title': 'SEO del gestore'})
        self.env['res.lang']._activate_lang('it_IT')
        self.campaign.with_context(lang='it_IT').introduction = 'Vecchio testo italiano lungo'
        before = dict(view._fields['arch_db']._get_stored_translations(view))
        self.website._install_request_campaign_pages()
        migrated = view.arch_db
        self.assertNotIn('<form', migrated)
        self.assertIn('Editoriale del gestore', migrated)
        self.assertIn('Altro contenuto conservato', migrated)
        self.assertIn('/gestore/foto-originale.jpg', migrated)
        self.assertIn('Foto del gestore', migrated)
        self.assertEqual(migrated.count('data-snippet="s_torrepulia_request_campaign"'), 1)
        self.assertEqual(self.website.torrepulia_campaign_page_backup[str(view.id)]['translations'], before)
        self.assertFalse(page.website_indexed)
        self.assertEqual(page.website_meta_title, 'SEO del gestore')
        self.assertEqual(self.campaign.introduction, 'Filtrato o non filtrato, anche insieme: scegli le quantità per ogni formato.')
        self.assertEqual(self.campaign.with_context(lang='it_IT').introduction, self.campaign.introduction)
        self.campaign.introduction = 'Modifica successiva del gestore'
        self.website._install_request_campaign_pages()
        self.assertEqual(self.campaign.introduction, 'Modifica successiva del gestore')
        self.assertEqual(view.arch_db, migrated)
        snippet = etree.fromstring('<section data-snippet="s_torrepulia_request_campaign"><div data-review-lazy=""/></section>')
        translated = arch.replace('Editoriale del gestore', 'Texte conservé')
        self.assertIn('Texte conservé', replace_legacy(translated, copy.deepcopy(snippet)))
