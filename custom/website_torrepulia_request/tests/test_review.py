import json
import secrets
from unittest.mock import patch

from lxml import html

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import Opener


@tagged('post_install', '-at_install')
class TestRequestReview(HttpCase):
    def test_free_delivery_area_is_optional_and_reaches_crm_notes_once(self):
        state = self.add()
        payload = dict(self.payload(state), notes='n' * 5000,
                       delivery_area='  Torremaggiore   (FG) / 71017  ')
        rejected = self.send(dict(payload, delivery_area=['manipulated']))
        self.assertEqual(rejected.status_code, 422)
        self.assertIn('delivery_area', rejected.json()['fields'])
        response = self.send(payload)
        self.assertEqual(response.status_code, 200, response.text)
        record = self.env['torrepulia.request'].search([('selection_id', '=', state['selection_id'])])
        expected = 'CAP o Città: Torremaggiore (FG) / 71017'
        self.assertIn(expected, record.notes)
        self.assertIn(payload['notes'], record.notes)
        self.assertIn(expected, record.opportunity_id.description)
        self.assertEqual(self.send(payload).json()['reference'], response.json()['reference'])
        self.assertEqual(record.notes.count(expected), 1)
        page = html.fromstring(self.url_open('/la-tua-richiesta').content)
        self.assertTrue(page.xpath('//input[@name="delivery_area" and not(@required)]'))

    def test_embedded_form_is_private_and_uses_shared_submission(self):
        response = self.url_open('/torrepulia/request/form')
        self.assertEqual(response.status_code, 200)
        self.assertIn('private', response.headers['Cache-Control'])
        self.assertIn('no-store', response.headers['Cache-Control'])
        root = html.fromstring(response.content)
        form = root.xpath('.//form[@data-tp-review-form]')[0]
        self.assertEqual(form.get('action'), '/torrepulia/request/submit')
        self.assertTrue(form.xpath('.//*[@name="privacy_accepted"]'))
        self.assertTrue(form.xpath('.//*[@data-review-lines]'))
        self.assertIn('CONFERMA LA MIA PRENOTAZIONE', response.text)
        self.website.torrepulia_commercial_mode = 'shop'
        self.assertEqual(self.url_open('/torrepulia/request/form').status_code, 404)

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        self.team = self.env['crm.team'].create({'name': 'Review HTTP team', 'company_id': self.website.company_id.id})
        self.website.write({'torrepulia_request_team_id': self.team.id, 'torrepulia_commercial_mode': 'request',
                            'torrepulia_request_show_prices': True})
        self.products = self.env['product.product'].create([
            {'name': 'Review oil 5 L', 'is_published': True, 'list_price': 63.75, 'torrepulia_request_liters': 5},
            {'name': 'Review other 999 L', 'is_published': True, 'list_price': 21.50}])

    def add(self, product=None, quantity=2, **configuration):
        bootstrap = self.url_open('/torrepulia/request/current').json()
        self.csrf = bootstrap['csrf_token']
        payload = {'operation': 'add', 'operation_id': secrets.token_hex(16),
            'selection_id': bootstrap['state']['selection_id'], 'revision': bootstrap['state']['revision'],
            'product_id': (product or self.products[0]).id, 'quantity': quantity, **configuration}
        response = self.url_open('/torrepulia/request/update', data={'csrf_token': self.csrf, 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['state']

    def payload(self, state):
        return {'selection_id': state['selection_id'], 'revision': state['revision'],
                'operation_id': secrets.token_hex(16), 'contact_name': 'Review Guest',
                'email': 'review-guest@example.invalid', 'phone': '', 'notes': 'Contact me about delivery',
                'privacy_accepted': True}

    def send(self, payload):
        return self.url_open('/torrepulia/request/submit', data={'csrf_token': self.csrf, 'payload': json.dumps(payload)})

    def test_guest_submission_receipt_retry_and_immutable_old_selection(self):
        self.add()
        state = self.add(self.products[1], 3)
        self.assertEqual(self.url_open('/la-tua-richiesta').status_code, 200)
        counts = {model: self.env[model].search_count([]) for model in ('crm.lead', 'sale.order', 'res.partner', 'mail.mail')}
        payload = self.payload(state)
        missing_csrf = self.url_open('/torrepulia/request/submit', data={'payload': json.dumps(payload)})
        self.assertEqual(missing_csrf.status_code, 400)
        rejected = self.send(dict(payload, privacy_accepted=False))
        self.assertEqual(rejected.status_code, 422)
        self.assertIn('privacy_accepted', rejected.json()['fields'])
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state']['quantity'], 5)
        submitted = self.send(payload)
        self.assertEqual(submitted.status_code, 200, submitted.text)
        result = submitted.json()
        self.assertTrue(result['ok'])
        self.assertFalse(result['replayed'])
        self.assertNotIn(payload['email'], submitted.text)
        self.assertNotIn('opportunity_id', submitted.text)
        self.assertEqual(result['success_url'], '/la-tua-richiesta/conferma')
        record = self.env['torrepulia.request'].search([('selection_id', '=', state['selection_id'])])
        self.assertEqual(record.state, 'submitted')
        self.assertTrue(record.privacy_accepted_at)
        self.assertEqual(record.opportunity_id.email_from, payload['email'])
        confirmation = self.url_open(result['success_url'])
        self.assertEqual(confirmation.status_code, 200)
        self.assertIn('no-store', confirmation.headers['Cache-Control'])
        self.assertIn('Abbiamo ricevuto la tua richiesta', confirmation.text)
        self.assertIn(result['reference'], confirmation.text)
        for product in self.products:
            self.assertIn(product.name, confirmation.text)
        self.assertNotIn(payload['email'], confirmation.text)
        # A subsequent catalog read starts a fresh draft, without changing the receipt.
        fresh = self.url_open('/torrepulia/request/current').json()['state']
        self.assertEqual(fresh['quantity'], 0)
        self.assertNotEqual(fresh['selection_id'], state['selection_id'])
        retry = self.send(payload)
        self.assertEqual(retry.status_code, 200, retry.text)
        self.assertTrue(retry.json()['replayed'])
        self.assertEqual(retry.json()['reference'], result['reference'])
        self.assertEqual(self.send(dict(payload, notes='Changed after submit')).status_code, 422)
        stale = {'operation': 'set', 'operation_id': secrets.token_hex(16), 'selection_id': state['selection_id'],
            'revision': state['revision'], 'line_key': state['lines'][0]['key'], 'quantity': 99}
        old = self.url_open('/torrepulia/request/update', data={'csrf_token': self.csrf, 'payload': json.dumps(stale)})
        self.assertEqual(old.status_code, 409)
        self.assertEqual(record.line_ids.mapped('quantity'), [2, 3])
        self.assertEqual(record.notes, payload['notes'])
        for model, count in counts.items():
            self.assertEqual(self.env[model].search_count([]), count + (model == 'crm.lead'), model)
        own_opener = self.opener
        self.opener = Opener(self)
        try:
            denied = self.url_open('/la-tua-richiesta/conferma?request_id=%s' % record.id)
            self.assertEqual(denied.status_code, 404)
        finally:
            self.opener = own_opener
        self.assertEqual(self.url_open('/la-tua-richiesta/conferma').status_code, 200)

    def test_preview_content_prices_and_no_partial_liters(self):
        self.add()
        preview = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertIn('10.000', preview['liters_display'])
        self.assertIn('/web/image/product.product/', preview['lines'][0]['thumbnail'])
        self.assertIn('63.75', preview['lines'][0]['price_display'])
        self.assertIn('127.50', preview['products_total_display'])
        self.add(self.products[1], 1)
        partial = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertNotIn('liters_display', partial)  # never infer 999 L from a name
        self.assertNotIn('liters_display', partial['lines'][1])
        self.products[1].torrepulia_request_liters = 0.5
        complete = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertIn('10.500', complete['liters_display'])
        self.website.torrepulia_request_show_prices = False
        hidden = self.url_open('/torrepulia/request/preview')
        self.assertNotIn('price_display', hidden.text)
        self.assertNotIn('subtotal_display', hidden.text)
        self.assertNotIn('products_total_display', hidden.text)
        self.assertIn('liters_display', hidden.text)
        document = html.fromstring(self.url_open('/la-tua-richiesta').text)
        self.assertTrue(document.xpath('//*[@data-review-sum]'))
        self.assertTrue(document.xpath('//*[@data-review-delivery-note]'))
        state = self.url_open('/torrepulia/request/current').json()['state']
        response = self.send(self.payload(state))
        self.assertEqual(response.status_code, 200, response.text)
        receipt = self.url_open(response.json()['success_url'])
        self.assertNotIn('63.75', receipt.text)
        self.assertNotIn('Totale prodotti:', receipt.text)

    def test_empty_invalid_contacts_and_forged_commercial_fields(self):
        bootstrap = self.url_open('/torrepulia/request/current').json()
        self.csrf = bootstrap['csrf_token']
        page = self.url_open('/la-tua-richiesta')
        tree = html.fromstring(page.text)
        self.assertTrue(tree.xpath('//form[@data-tp-review-form and @hidden]//fieldset[@disabled]'))
        self.assertIn('La tua richiesta è ancora vuota', page.text)
        self.assertEqual(self.send(self.payload(bootstrap['state'])).status_code, 422)
        state = self.add()
        payload = self.payload(state)
        for data, field in [(dict(payload, email='bad'), 'email'), (dict(payload, contact_name=''), 'contact_name'),
                            (dict(payload, notes='\x00'), 'notes')]:
            response = self.send(data)
            self.assertEqual(response.status_code, 422)
            self.assertIn(field, response.json()['fields'])
        self.assertEqual(self.send(dict(payload, price_unit=1, team_id=self.team.id)).status_code, 422)
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state']['quantity'], 2)
        self.assertEqual(self.url_open('/la-tua-richiesta/conferma').status_code, 404)

    def test_captcha_and_crm_failures_roll_back_entire_submission(self):
        state = self.add()
        payload = self.payload(state)
        leads = self.env['crm.lead'].search_count([])
        with patch.object(type(self.env['ir.http']), '_verify_request_recaptcha_token', side_effect=ValidationError('Verifica di sicurezza non riuscita')):
            response = self.send(payload)
        self.assertEqual(response.status_code, 422, response.text)
        with patch.object(type(self.env['crm.lead']), 'create', side_effect=ValidationError('Invio temporaneamente non disponibile')):
            response = self.send(payload)
        self.assertEqual(response.status_code, 422, response.text)
        draft = self.env['torrepulia.request'].search([('selection_id', '=', state['selection_id'])])
        draft.invalidate_recordset()
        self.assertEqual(draft.state, 'draft')
        self.assertFalse(draft.public_receipt)
        self.assertFalse(draft.privacy_accepted_at)
        self.assertEqual(draft.line_ids.quantity, 2)
        self.assertEqual(self.env['crm.lead'].search_count([]), leads)
        self.assertEqual(self.send(payload).status_code, 200)

    def test_authenticated_prefill_optional_phone_and_receipt_isolation(self):
        portal = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Review Auth User', 'login': 'review-auth@example.invalid', 'email': 'review-auth@example.invalid',
            'password': 'ReviewOnlyTestPassword', 'group_ids': [fields.Command.set(self.env.ref('base.group_portal').ids)]})
        self.authenticate(portal.login, 'ReviewOnlyTestPassword')
        response = self.url_open('/la-tua-richiesta')
        self.assertIn('no-store', response.headers['Cache-Control'])
        tree = html.fromstring(response.text)
        self.assertEqual(tree.xpath('//input[@name="contact_name"]/@value'), ['Review Auth User'])
        self.assertEqual(tree.xpath('//input[@name="email"]/@value'), [portal.email])
        self.assertFalse(tree.xpath('//input[@name="phone"]/@required'))
        self.assertFalse(tree.xpath('//input[@name="address"] | //input[@name="vat"]'))
        state = self.add()
        result = self.send(self.payload(state))
        self.assertEqual(result.status_code, 200)
        record = self.env['torrepulia.request'].search([('selection_id', '=', state['selection_id'])])
        self.assertEqual(record.partner_id, portal.partner_id)
        other = self.env['website'].create({'name': 'Other receipt website', 'company_id': self.website.company_id.id,
            'torrepulia_request_team_id': self.team.id, 'torrepulia_commercial_mode': 'request'})
        self.assertFalse(other._request_receipt(record.review_digest))
        self.env.cr.execute("UPDATE torrepulia_request SET submitted_at = NOW() - INTERVAL '25 hours' WHERE id = %s", [record.id])
        record.invalidate_recordset()
        self.assertEqual(self.url_open('/la-tua-richiesta/conferma').status_code, 404)
        self.assertTrue(record.exists())

    def test_variants_custom_text_native_uom_conversion_and_stale_revision(self):
        attribute = self.env['product.attribute'].create({'name': 'Review format', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Small'}), fields.Command.create({'name': 'Large'})]})
        custom = self.env['product.attribute'].create({'name': 'Review inscription', 'create_variant': 'no_variant',
            'value_ids': [fields.Command.create({'name': 'Your text', 'is_custom': True})]})
        template = self.env['product.template'].create({'name': 'Review variant oil', 'is_published': True,
            'attribute_line_ids': [fields.Command.create({'attribute_id': attr.id,
                'value_ids': [fields.Command.set(attr.value_ids.ids)]}) for attr in (attribute, custom)]})
        a, b = template.product_variant_ids
        a.torrepulia_request_liters = 0.5
        b.torrepulia_request_liters = 5
        ptav = template.valid_product_template_attribute_line_ids.product_template_value_ids.filtered('is_custom')
        config = {'no_variant_value_ids': ptav.ids, 'custom_values': {str(ptav.id): 'Family inscription'}}
        self.add(a, 2, **config)
        original = self.add(b, 1, **config)
        pack = self.env['uom.uom'].create({'name': 'Review pack six', 'relative_uom_id': a.uom_id.id, 'relative_factor': 6})
        self.env.ref('base.user_root').group_ids |= self.env.ref('uom.group_uom')
        template.uom_ids |= pack
        self.add(a, 1, uom_id=pack.id, **config)
        preview = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertEqual(len(preview['lines']), 3)
        self.assertIn('9.000', preview['liters_display'])  # 2*0.5 + 1*5 + 6*0.5
        self.assertTrue(all('Family inscription' in line['custom_text'] for line in preview['lines']))
        self.assertTrue(all(line['attributes'] for line in preview['lines']))
        rejected = self.send(self.payload(original))
        self.assertEqual(rejected.status_code, 422)
        self.assertIn('selection', rejected.json()['fields'])
        self.assertEqual(len(self.url_open('/torrepulia/request/current').json()['state']['lines']), 3)
