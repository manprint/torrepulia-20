import copy
import json
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import Opener

from .test_request import RequestCase


@tagged('post_install', '-at_install')
class TestCheckoutSuspension(HttpCase):
    def setUp(self):
        super().setUp()
        self.site = self.env['website'].search([], limit=1)
        self.site.torrepulia_commercial_mode = 'shop'
        self.team = self.env['crm.team'].create({'name': 'Checkout policy team', 'company_id': self.site.company_id.id})
        self.site.torrepulia_request_team_id = self.team
        self.product = self.env['product.product'].create({'name': 'Checkout policy synthetic service', 'type': 'service',
            'is_published': True, 'website_id': self.site.id, 'list_price': 23})
        self.customer = self.env['res.partner'].create({'name': 'Checkout policy visitor', 'email': 'checkout-policy@example.invalid',
            'street': 'Synthetic street 1', 'city': 'Roma', 'zip': '00100', 'country_id': self.env.ref('base.it').id})
        self.params = {'product_template_id': self.product.product_tmpl_id.id, 'product_id': self.product.id, 'quantity': 2}
        added = self.rpc('/shop/cart/add', self.params)
        self.assertNotIn('error', added, added)
        self.cart = self.env['sale.order'].search([('website_id', '=', self.site.id), ('order_line.product_id', '=', self.product.id)])
        self.assertEqual(len(self.cart), 1)
        self.cart.write({'partner_id': self.customer.id, 'partner_invoice_id': self.customer.id,
                         'partner_shipping_id': self.customer.id})

    def rpc(self, path, params, headers=None):
        response = self.url_open(path, data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': params}),
                                 headers={'Content-Type': 'application/json', **(headers or {})})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_all_direct_checkout_pages_and_mutations_are_controlled(self):
        self.site.torrepulia_commercial_mode = 'request'
        self.site.torrepulia_request_summary_url = '/richiesta-centralizzata'
        before = self.cart.read(['state', 'partner_id', 'order_line', 'amount_total'])[0]
        counts = {model: self.env[model].search_count([]) for model in ('sale.order', 'payment.transaction', 'res.partner', 'stock.move', 'account.move')}
        for path in ['/shop/cart', '/shop/checkout?try_skip_step=true', '/shop/address', '/shop/extra_info',
                     '/shop/payment', '/shop/payment/validate', '/shop/confirmation', '/shop/print', '/shop/print/invoice']:
            response = self.url_open(path, allow_redirects=False)
            self.assertEqual(response.status_code, 303, (path, response.text))
            self.assertTrue(response.headers['Location'].endswith('/richiesta-centralizzata'))
            self.assertIn('no-store', response.headers['Cache-Control'])
        mutations = [('/shop/cart/add', self.params), ('/shop/cart/update', {'line_id': self.cart.order_line.id, 'quantity': 8}),
                     ('/shop/express_checkout', {'billing_address': {'name': 'Must not create', 'email': 'not-created@example.invalid'}}),
                     ('/shop/express/shipping_address_change', {'shipping_address': {}}),
                     ('/shop/update_address', {'partner_id': self.customer.id}),
                     ('/shop/set_delivery_method', {'delivery_method_id': False}),
                     ('/shop/get_delivery_rate', {'delivery_method_id': False}),
                     ('/website_sale/set_delivery_date', {'delivery_date': '2099-01-01'}),
                     ('/website_sale_stock/set_pickup_location', {'pickup_location_data': {}}),
                     ('/my/orders/reorder', {'order_id': self.cart.id, 'access_token': self.cart._portal_ensure_token()})]
        for path, params in mutations:
            result = self.rpc(path, params)
            self.assertIn('error', result, (path, result))
            self.assertIn('sospesi', result['error']['data']['message'])
        csrf = self.url_open('/torrepulia/request/current').json()['csrf_token']
        for path in ['/shop/address/submit', '/website/form/shop.sale.order']:
            response = self.url_open(path, data={'csrf_token': csrf, 'name': 'Do not create'})
            self.assertEqual(response.status_code, 409, response.text)
            self.assertEqual(response.json()['redirectUrl'], '/richiesta-centralizzata')
        self.cart.invalidate_recordset()
        self.assertEqual(self.cart.read(['state', 'partner_id', 'order_line', 'amount_total'])[0], before)
        for model, count in counts.items():
            self.assertEqual(self.env[model].search_count([]), count, model)

    def test_free_cart_get_and_recovery_link_cannot_confirm_merge_or_cancel(self):
        self.cart.order_line.price_unit = 0
        # Native standard checkout prepares sale_last_order_id here.
        self.url_open('/shop/checkout', allow_redirects=False)
        other = self.cart.copy({'order_line': [fields.Command.clear(), fields.Command.create({
            'product_id': self.product.id, 'product_uom_qty': 5})]})
        token = other._portal_ensure_token()
        self.site.torrepulia_commercial_mode = 'request'
        for path in ['/shop/payment/validate?sale_order_id=%s' % self.cart.id,
                     '/shop/cart?id=%s&access_token=%s' % (other.id, token),
                     '/shop/cart/add?product_id=%s&quantity=9' % self.product.id]:
            response = self.url_open(path, allow_redirects=False)
            self.assertIn(response.status_code, [303, 405])
        self.cart.invalidate_recordset(); other.invalidate_recordset()
        self.assertEqual(self.cart.state, 'draft')
        self.assertEqual(other.state, 'draft')
        self.assertEqual(self.cart.order_line.product_uom_qty, 2)
        self.assertEqual(other.order_line.product_uom_qty, 5)

    def test_existing_cart_tokens_cannot_use_checkout_or_portal_payment(self):
        self.site.torrepulia_commercial_mode = 'request'
        if not self.env.ref('payment_demo.payment_method_demo', raise_if_not_found=False):
            self.skipTest('Install payment_demo only in the isolated test database for fake payments.')
        provider = self.env.ref('payment.payment_provider_demo')
        provider.is_live = False
        token = self.cart._portal_ensure_token()
        self.cart.write({'require_signature': True, 'prepayment_percent': 1.0})
        self.assertTrue(self.cart._has_to_be_signed())
        # A legacy cart token must not acquire a signature, even when payment
        # would postpone confirmation until after the signature is written.
        accepted = self.rpc('/my/orders/%s/accept' % self.cart.id,
                            {'access_token': token, 'name': 'Cart visitor', 'signature': 'aW52YWxpZA=='})
        self.assertIn('sospeso', accepted['result']['error'])
        self.cart.invalidate_recordset()
        self.assertFalse(self.cart.signature)
        self.assertTrue(self.cart._has_to_be_signed())
        params = {'access_token': token, 'provider_id': provider.id,
            'payment_method_id': self.env.ref('payment_demo.payment_method_demo').id, 'token_id': None,
            'amount': self.cart.amount_total, 'flow': 'direct', 'tokenization_requested': False, 'landing_route': '/payment/status'}
        before = self.env['payment.transaction'].search_count([])
        with patch.object(type(self.env['payment.transaction']), '_get_processing_values', side_effect=AssertionError('No provider processing')):
            checkout = self.rpc('/shop/payment/transaction/%s' % self.cart.id, params)
            portal = self.rpc('/my/orders/%s/transaction' % self.cart.id, params)
            forged = self.rpc('/my/orders/%s/transaction' % self.cart.id, dict(params, context={'torrepulia_allow_checkout': True, 'from_portal': True}))
        for result in [checkout, portal, forged]:
            self.assertIn('error', result, result)
        self.assertIn('sospeso', portal['error']['data']['message'])
        self.assertEqual(self.env['payment.transaction'].search_count([]), before)
        self.cart.invalidate_recordset()
        self.assertEqual(self.cart.state, 'draft')

    def test_restore_same_session_and_second_standard_website(self):
        self.site.torrepulia_commercial_mode = 'request'
        other_site = self.env['website'].create({'name': 'Independent standard checkout', 'company_id': self.site.company_id.id,
            'domain': 'http://standard-checkout.example.invalid'})
        other_product = self.product.copy({'name': 'Other website checkout product', 'website_id': other_site.id, 'is_published': True})
        own_opener = self.opener
        self.opener = Opener(self)
        try:
            result = self.rpc('/shop/cart/add', {'product_template_id': other_product.product_tmpl_id.id,
                'product_id': other_product.id, 'quantity': 1}, {'Host': 'standard-checkout.example.invalid'})
            self.assertNotIn('error', result, result)
            second_cart = self.env['sale.order'].search([('website_id', '=', other_site.id), ('order_line.product_id', '=', other_product.id)])
            self.assertEqual(second_cart.order_line.product_uom_qty, 1)
        finally:
            self.opener = own_opener
        self.url_open('/shop')  # must not resurrect/reprice/reassign the saved cart
        self.assertIn('error', self.rpc('/shop/cart/add', self.params))
        self.site.torrepulia_commercial_mode = 'shop'
        restored = self.rpc('/shop/cart/add', dict(self.params, quantity=1))
        self.assertNotIn('error', restored, restored)
        self.cart.invalidate_recordset()
        self.assertEqual(self.cart.order_line.product_uom_qty, 3)
        self.assertEqual(len(self.env['sale.order'].search([('website_id', '=', self.site.id), ('order_line.product_id', '=', self.product.id)])), 1)


@tagged('post_install', '-at_install')
class TestCheckoutRecoveryAndAudit(RequestCase):
    def test_mode_transition_preserves_submitted_requests_and_reports_only_own_carts(self):
        site, session, request = self._draft()
        self._line(request, site)
        self._submit(request, site)
        snapshot = copy.deepcopy(request.submission_snapshot)
        partner = self.env['res.partner'].create({'name': 'Cart audit', 'email': 'cart-audit@example.invalid'})
        cart = self.env['sale.order'].create({'partner_id': partner.id, 'website_id': self.website.id,
            'company_id': self.company.id, 'order_line': [fields.Command.create({'product_id': self.product.id, 'product_uom_qty': 2})]})
        self.assertEqual(self.website.torrepulia_open_cart_count, 1)
        action = self.website.action_torrepulia_open_carts()
        self.assertEqual(self.env['sale.order'].search(action['domain']), cart)
        with self.assertRaises(AccessError):
            self.website.with_user(self.public).action_torrepulia_open_carts()
        self.website.torrepulia_commercial_mode = 'shop'
        self.assertEqual(request.with_user(self.sales).state, 'submitted')
        self.assertEqual(request.submission_snapshot, snapshot)
        self.assertFalse(request.quotation_ids)
        self.assertEqual(cart.order_line.product_uom_qty, 2)
        self.assertFalse(site._request_selection_state(session)['enabled'])
        self.website.torrepulia_commercial_mode = 'request'
        self.assertEqual(request.submission_snapshot, snapshot)
        self.assertFalse(cart.cart_recovery_email_sent)
        # Existing confirmed eCommerce sales remain ordinary Sales documents;
        # the boundary is the autonomous draft cart, not all website business.
        completed = cart.copy()
        completed.action_confirm()
        self.assertFalse(completed._torrepulia_suspended_catalog_carts())

    def test_recovery_cron_excludes_suspended_sites_before_marking_or_mailing(self):
        self.other_site.write({'send_abandoned_cart_followup': True, 'cart_abandoned_delay': 0})
        self.website.write({'send_abandoned_cart_followup': True, 'cart_abandoned_delay': 0})
        partner = self.env['res.partner'].create({'name': 'Recovery test', 'email': 'recovery-test@example.invalid'})
        carts = self.env['sale.order'].create([{'partner_id': partner.id, 'website_id': website.id,
            'company_id': self.company.id, 'date_order': fields.Datetime.now() - timedelta(hours=2),
            'order_line': [fields.Command.create({'product_id': self.product.id, 'product_uom_qty': 1})]}
            for website in (self.website, self.other_site)])
        # Move only these fixture timestamps past the native activation threshold.
        for website in (self.website, self.other_site):
            website.send_abandoned_cart_email_activation_time = fields.Datetime.now() - timedelta(days=1)
        selected = []
        def intercept(records):
            selected.extend(records.ids)
        with patch.object(type(carts), '_cart_recovery_email_send', intercept), \
                patch.object(type(carts), '_filter_can_send_abandoned_cart_followup', lambda records: records), \
                patch.object(type(self.env['ir.cron']), '_commit_progress', return_value=1):
            self.env['website']._cron_send_abandoned_cart_email()
        self.assertIn(carts[1].id, selected)
        self.assertNotIn(carts[0].id, selected)
        self.assertFalse(carts[0].cart_recovery_email_sent)
        with self.assertRaises(ValidationError):
            carts[0].action_recovery_email_send()
        with patch.object(type(self.env['mail.template']), 'send_mail_batch', side_effect=AssertionError('No recovery email')):
            carts[0]._cart_recovery_email_send()
        self.assertFalse(carts[0].cart_recovery_email_sent)
