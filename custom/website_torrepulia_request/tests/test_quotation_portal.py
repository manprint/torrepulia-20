import json
from unittest.mock import patch

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestRequestQuotationPortal(HttpCase):
    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Quotation portal team', 'company_id': self.website.company_id.id})
        self.website.write({'torrepulia_commercial_mode': 'request', 'torrepulia_request_team_id': team.id,
                            'torrepulia_request_show_prices': False})
        self.product = self.env['product.product'].create({'name': 'Quotation portal product', 'list_price': 37.5,
            'is_published': True, 'website_id': self.website.id})
        self.customer = self.env['res.partner'].create({'name': 'Synthetic Portal Customer', 'email': 'quotation-portal@example.invalid'})
        visitor = self.website.with_user(self.env.ref('base.public_user')).with_context(website_id=self.website.id)
        draft = visitor._torrepulia_session_request({}, create=True)
        draft._set_selection(visitor, self.product.with_env(visitor.env), 2)
        draft._submit(visitor, {'contact_name': self.customer.name, 'email': self.customer.email})
        draft = draft.with_env(self.env)
        self.source = draft
        action = draft.action_prepare_quotation()
        wizard = self.env[action['res_model']].with_context(**action['context']).create({'partner_id': self.customer.id})
        self.order = self.env['sale.order'].browse(wizard.action_prepare()['res_id'])

    def test_native_portal_signature_confirms_without_second_approval(self):
        self.order.write({'require_signature': True, 'prepayment_percent': 0})
        self.order.action_quotation_sent()
        token = self.order._portal_ensure_token()
        page = self.url_open('/my/orders/%s?access_token=%s' % (self.order.id, token))
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('oe_currency_value', page.text)  # Hidden catalog prices must not redact an authorized quote.
        payload = {'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {
            'access_token': token, 'name': self.customer.name,
            'signature': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a2ioAAAAASUVORK5CYII='}}
        with patch.object(type(self.env['mail.mail']), 'send', return_value=True), \
                patch.object(type(self.env['ir.mail_server']), '_connect__', side_effect=AssertionError('No real SMTP')), \
                patch.object(type(self.env['ir.actions.report']), '_render_qweb_pdf', return_value=(b'%PDF Synthetic test report', 'pdf')):
            response = self.url_open('/my/orders/%s/accept' % self.order.id, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()['result']
        self.assertNotIn('error', result, response.text)
        self.order.invalidate_recordset()
        self.assertEqual(self.order.state, 'sale')
        self.assertTrue(self.order.signature)
        self.assertEqual(self.order.signed_by, self.customer.name)
        self.assertEqual(self.source.state, 'submitted')
        self.assertEqual(self.source.line_ids.quantity, 2)

    def test_native_portal_payment_route_reachable_with_request_mode(self):
        self.order.write({'require_signature': False, 'prepayment_percent': 1})
        self.order.action_quotation_sent()
        token = self.order._portal_ensure_token()
        response = self.url_open('/my/orders/%s?access_token=%s&allow_payment=yes' % (self.order.id, token))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('payment', response.text)
        if not self.env['ir.module.module'].search_count([('name', '=', 'payment_demo'), ('state', '=', 'installed')]):
            self.skipTest('Install payment_demo in the isolated test database for the fake transaction route.')
        provider = self.env.ref('payment.payment_provider_demo')
        provider.write({'is_live': False, 'is_published': True})
        params = {'access_token': token, 'provider_id': provider.id,
                  'payment_method_id': self.env.ref('payment_demo.payment_method_demo').id,
                  'token_id': None, 'amount': self.order.amount_total, 'flow': 'direct',
                  'tokenization_requested': False, 'landing_route': '/payment/status'}
        transaction = self.url_open('/my/orders/%s/transaction' % self.order.id,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': params}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(transaction.status_code, 200, transaction.text)
        self.assertNotIn('error', transaction.json(), transaction.text)
        self.assertIn('amount', transaction.json()['result'])
        self.order.invalidate_recordset()
        self.assertEqual(len(self.order.transaction_ids), 1)
        self.assertEqual(self.order.transaction_ids.state, 'draft')
