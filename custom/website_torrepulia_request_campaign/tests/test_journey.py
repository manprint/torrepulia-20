import copy
import json
import secrets
from time import time
from unittest.mock import patch

from lxml import html

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import Opener


@tagged('post_install', '-at_install')
class TestRequestJourney(HttpCase):
    """Real HTTP/ORM journey; deliberately not a browser-click or visual test."""
    def setUp(self):
        super().setUp()
        self.site = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Journey synthetic team', 'company_id': self.site.company_id.id})
        self.site.write({'torrepulia_theme_enabled': True, 'torrepulia_commercial_mode': 'request',
                         'torrepulia_request_team_id': team.id, 'torrepulia_request_show_prices': False})
        self.products = self.env['product.product'].create([
            {'name': name, 'is_published': True, 'type': 'consu', 'is_storable': True, 'website_id': self.site.id}
            for name in ('Lattina — collaudo sintetico', 'Bag in Box — collaudo sintetico', 'Confezione bottiglie — collaudo sintetico')])
        self.campaign = self.env['torrepulia.request.campaign'].create({
            'name': 'Journey synthetic campaign', 'reference': 'journey-qa', 'website_id': self.site.id,
            'state': 'open', 'line_ids': [fields.Command.create({'product_id': p.id, 'sequence': i})
                                        for i, p in enumerate(self.products[:2])]})
        self.site.torrepulia_campaign_id = self.campaign

    def current(self):
        result = self.url_open('/torrepulia/request/current').json()
        self.csrf = result['csrf_token']
        return result['state']

    def update(self, operation, product, quantity):
        state = self.current()
        result = self.url_open('/torrepulia/request/update', data={'csrf_token': self.csrf, 'payload': json.dumps({
            'operation': operation, 'operation_id': secrets.token_hex(16), 'selection_id': state['selection_id'],
            'revision': state['revision'], 'product_id': product.id, 'quantity': quantity})})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()['state']

    def submit(self, payload):
        return self.url_open('/torrepulia/request/submit', data={'csrf_token': self.csrf, 'payload': json.dumps(payload)})

    def test_http_catalog_campaign_review_crm_quotation_and_manual_confirmation(self):
        before = {model: self.env[model].search_count([]) for model in
                  ('crm.lead', 'sale.order', 'res.partner', 'stock.move', 'payment.transaction', 'account.move')}
        self.assertFalse(any(self.products.mapped('qty_available')))
        self.assertEqual(self.url_open('/shop').status_code, 200)
        self.assertEqual(self.url_open(self.products[0].website_url).status_code, 200)
        self.update('add', self.products[0], 2)
        self.update('add', self.products[1], 1)
        self.update('add', self.products[2], 4)
        self.site._install_request_campaign_pages()
        self.assertEqual(self.url_open('/prenotailtuoolio').status_code, 200)
        cards = self.url_open('/torrepulia/campaign/content').json()
        self.assertTrue(cards['open'])
        self.assertEqual(len(html.fromstring(cards['html']).xpath('//*[@data-campaign-config]')), 2)
        state = self.update('set_configuration', self.products[0], 3)
        expected = dict(zip(self.products.ids, (3, 1, 4)))
        self.assertEqual({line['product_id']: line['quantity'] for line in state['lines']}, expected)
        self.assertEqual(state['quantity'], 8)
        self.assertEqual(self.url_open('/la-tua-richiesta').status_code, 200)
        preview = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertEqual({line['product_id']: line['quantity'] for line in preview['lines']}, expected)
        self.assertNotIn('products_total_display', preview)
        for model, count in before.items():
            self.assertEqual(self.env[model].search_count([]), count, model)
        payload = {'selection_id': state['selection_id'], 'revision': state['revision'],
            'operation_id': secrets.token_hex(16), 'contact_name': 'Visitatore sintetico',
            'email': 'journey-qa@example.invalid', 'phone': '', 'notes': 'Solo collaudo', 'privacy_accepted': True}
        self.assertEqual(self.submit(dict(payload, email='')).status_code, 422)
        with patch.object(type(self.env['crm.lead']), 'create', side_effect=ValidationError('CRM QA unavailable')):
            failed = self.submit(payload)
        self.assertEqual(failed.status_code, 422, failed.text)
        self.assertEqual(self.current()['quantity'], 8)
        self.assertEqual(self.env['crm.lead'].search_count([]), before['crm.lead'])
        received = self.submit(payload)
        self.assertEqual(received.status_code, 200, received.text)
        # Equivalent to retrying after the first successful response was lost.
        replay = self.submit(payload)
        self.assertTrue(replay.json()['replayed'])
        self.assertEqual(replay.json()['reference'], received.json()['reference'])
        source = self.env['torrepulia.request'].search([('selection_id', '=', state['selection_id'])])
        self.assertEqual(len(source), 1)
        self.assertEqual(self.env['crm.lead'].search_count([]), before['crm.lead'] + 1)
        self.assertEqual({line.product_id.id: line.quantity for line in source.line_ids}, expected)
        self.assertFalse(source.opportunity_id.partner_id)
        self.assertEqual(self.env['sale.order'].search_count([]), before['sale.order'])
        self.assertEqual(self.env['res.partner'].search_count([]), before['res.partner'])
        for model in ('stock.move', 'payment.transaction', 'account.move'):
            self.assertEqual(self.env[model].search_count([]), before[model], model)
        snapshot = copy.deepcopy(source.submission_snapshot)
        confirmation = self.url_open('/richiesta-inviata?email=ignored@example.invalid&request_id=%s' % source.id,
                                     allow_redirects=False)
        self.assertEqual(confirmation.status_code, 303)
        self.assertTrue(confirmation.headers['Location'].endswith('/la-tua-richiesta/conferma'))
        own = self.opener
        self.opener = Opener(self)
        try:
            self.assertEqual(self.url_open('/la-tua-richiesta/conferma?request_id=%s' % source.id).status_code, 404)
            self.assertIn('Verifica la tua richiesta', self.url_open('/richiesta-inviata?request_id=%s' % source.id).text)
        finally:
            self.opener = own
        customer = self.env['res.partner'].create({'name': payload['contact_name'], 'email': payload['email']})
        action = source.action_prepare_quotation()
        wizard = self.env[action['res_model']].with_context(**action['context']).create({'partner_id': customer.id})
        order = self.env['sale.order'].browse(wizard.action_prepare()['res_id'])
        self.assertEqual(order.state, 'draft')
        self.assertFalse(order.picking_ids)
        self.assertEqual({line.product_id.id: line.product_uom_qty for line in order.order_line}, expected)
        self.assertEqual(source.action_prepare_quotation()['res_id'], order.id)
        self.assertEqual(len(source.quotation_ids), 1)
        with patch.object(type(self.env['ir.mail_server']), '_connect__', side_effect=AssertionError('No real SMTP')):
            order.message_post(body='Accettazione email sintetica registrata per il collaudo.')
            order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.picking_ids)
        self.assertEqual(source.submission_snapshot, snapshot)
        self.assertEqual(self.current()['quantity'], 0)

    def test_old_thanks_requires_server_session_and_general_contact_still_works(self):
        direct = self.url_open('/richiesta-inviata?email=secret@example.invalid&request_id=999')
        self.assertEqual(direct.status_code, 200)
        self.assertIn('Verifica la tua richiesta', direct.text)
        self.assertNotIn('secret@example.invalid', direct.text)
        self.assertNotIn('Abbiamo ricevuto il tuo messaggio', direct.text)
        self.assertIn('no-store', direct.headers['Cache-Control'])
        page = self.env['website.page'].search([('url', '=', '/richiesta-inviata'), ('website_id', '=', self.site.id)], limit=1)
        self.assertTrue(page)
        if not page.website_indexed:
            self.assertTrue(html.fromstring(direct.text).xpath('//meta[@name="robots" and contains(@content,"noindex")]'))
        old = self.env['crm.lead'].create({'name': 'Richiesta storica sintetica', 'description': 'Storico da conservare'})
        original = old.description
        for marker in ('torrepulia_reservation', 'bib_filtrato', 'bib_non_filtrato', 'latta_filtrata', 'latta_non_filtrata'):
            rejected = self.url_open('/website/form/crm.lead', data={marker: '1', 'name': 'Old request'})
            self.assertIn('error', rejected.json())
        self.site._install_request_campaign_pages()
        self.assertEqual(old.description, original)
        before = self.env['crm.lead'].search_count([])
        sent = self.url_open('/website/form/crm.lead', data={'name': 'Il tuo messaggio',
            'contact_name': 'Contatto sintetico', 'email_from': 'contact-qa@example.invalid', 'description': 'General contact QA'})
        self.assertIn('id', sent.json(), sent.text)
        self.assertEqual(self.env['crm.lead'].search_count([]), before + 1)
        thanks = self.url_open('/richiesta-inviata')
        self.assertIn('Abbiamo ricevuto il tuo messaggio', thanks.text)
        self.assertNotIn('contact-qa@example.invalid', thanks.text)
        with patch('odoo.addons.website_torrepulia_request_campaign.controllers.campaign.time', return_value=time() + 901):
            self.assertIn('Verifica la tua richiesta', self.url_open('/richiesta-inviata').text)
        # Non-Torrepulia websites keep their own page at the same URL.
        self.site.torrepulia_theme_enabled = False
        self.assertIn('Grazie per averci scritto', self.url_open('/richiesta-inviata').text)
