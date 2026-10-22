import json
import secrets
from unittest.mock import patch

from lxml import html

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestHybridMode(HttpCase):
    """Native checkout for stock, seasonal preorders for the open campaign only."""

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Hybrid team', 'company_id': self.website.company_id.id})
        self.website.write({'torrepulia_theme_enabled': True, 'torrepulia_request_team_id': team.id,
                            'torrepulia_commercial_mode': 'hybrid'})
        self.seasonal, self.stock = self.env['product.product'].create([
            {'name': 'Hybrid new harvest', 'is_published': True, 'website_id': self.website.id, 'list_price': 70},
            {'name': 'Hybrid stock bottle', 'is_published': True, 'website_id': self.website.id, 'list_price': 15}])
        self.campaign = self.env['torrepulia.request.campaign'].create({
            'name': 'Hybrid campaign', 'reference': 'hybrid-test', 'website_id': self.website.id, 'state': 'open',
            'line_ids': [fields.Command.create({'product_id': self.seasonal.id})]})
        self.website.torrepulia_campaign_id = self.campaign

    def update(self, operation, product, qty):
        bootstrap = self.url_open('/torrepulia/request/current').json()
        payload = {'operation': operation, 'operation_id': secrets.token_hex(16),
            'selection_id': bootstrap['state']['selection_id'], 'revision': bootstrap['state']['revision'],
            'product_id': product.id, 'quantity': qty}
        return self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})

    def cart_add(self, product):
        response = self.url_open('/shop/cart/add', data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'product_template_id': product.product_tmpl_id.id, 'product_id': product.id, 'quantity': 1}}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_preorder_destination_follows_mode_and_campaign(self):
        site = self.website
        self.assertTrue(site._torrepulia_selection_enabled())
        self.assertFalse(site._torrepulia_request_enabled())
        self.assertEqual(site._torrepulia_preorder_product_url(self.seasonal), '/prenotailtuoolio')
        self.assertEqual(site._torrepulia_preorder_product_url(self.seasonal.product_tmpl_id), '/prenotailtuoolio')
        self.assertFalse(site._torrepulia_preorder_product_url(self.stock))
        self.assertTrue(site._torrepulia_selection_allows(self.seasonal))
        self.assertFalse(site._torrepulia_selection_allows(self.stock))
        # Full request mode keeps the whole catalogue requestable and buttons unchanged.
        site.torrepulia_commercial_mode = 'request'
        self.assertFalse(site._torrepulia_preorder_product_url(self.seasonal))
        self.assertTrue(site._torrepulia_selection_allows(self.stock))
        # Standard shop: no seasonal selection at all.
        site.torrepulia_commercial_mode = 'shop'
        self.assertFalse(site._torrepulia_selection_enabled())
        self.assertFalse(site._request_preorder_url())
        site.torrepulia_commercial_mode = 'hybrid'
        self.campaign.state = 'closed'
        self.assertFalse(site._torrepulia_preorder_product_url(self.seasonal))
        self.assertFalse(site._torrepulia_selection_allows(self.seasonal))

    def test_hybrid_mode_requires_team(self):
        with self.assertRaises(ValidationError):
            self.website.torrepulia_request_team_id = False

    def test_selection_accepts_only_open_campaign_products(self):
        self.assertTrue(self.url_open('/torrepulia/campaign/content').json()['open'])
        accepted = self.update('set_configuration', self.seasonal, 2)
        self.assertEqual(accepted.status_code, 200, accepted.text)
        self.assertEqual(accepted.json()['state']['quantity'], 2)
        for operation, product in [('add', self.seasonal), ('set_configuration', self.stock)]:
            rejected = self.update(operation, product, 1)
            self.assertEqual(rejected.status_code, 422, (operation, rejected.text))
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state']['quantity'], 2)
        self.campaign.state = 'closed'
        self.assertFalse(self.url_open('/torrepulia/campaign/content').json()['open'])
        self.assertEqual(self.update('set_configuration', self.seasonal, 3).status_code, 422)

    def test_stock_uses_native_cart_and_seasonal_cannot_be_paid(self):
        self.assertNotIn('error', self.cart_add(self.stock))
        cart = self.env['sale.order'].search([('website_id', '=', self.website.id),
                                              ('order_line.product_id', '=', self.stock.id)])
        self.assertEqual(len(cart), 1)
        self.assertEqual(self.url_open('/shop/cart', allow_redirects=False).status_code, 200)
        refused = self.cart_add(self.seasonal)
        self.assertIn('prenotazione', refused['error']['data']['message'])
        self.assertNotIn(self.seasonal, cart.order_line.product_id)
        # A cart composed before the campaign opened cannot be confirmed or paid.
        cart.order_line = [fields.Command.create({'product_id': self.seasonal.id, 'product_uom_qty': 1})]
        with self.assertRaises(ValidationError):
            cart._validate_order()
        cart.order_line.filtered(lambda line: line.product_id == self.seasonal).unlink()
        self.assertFalse(cart._torrepulia_preorder_carts())

    def test_shop_and_product_page_offer_preorder_for_campaign_products(self):
        self.env['product.product'].create({'name': 'Hybrid sold-out stock', 'is_published': True,
            'website_id': self.website.id, 'is_storable': True, 'allow_out_of_stock_order': False, 'list_price': 12})
        self.assertIn('o_wsale_my_cart', self.url_open('/shop').text)
        tree = html.fromstring(self.url_open('/shop').content)
        # Tile action of the campaign product; sold-out stock tiles carry the notice link instead.
        links = tree.xpath('//div[contains(@class, "tp-request-action-row")]/a[contains(@class, "tp-request-preorder-link")]/@href')
        self.assertEqual(links, ['/prenotailtuoolio'])
        self.assertFalse(tree.xpath('//*[@data-product-template-id="%s"][@name="add_to_cart"]' % self.seasonal.product_tmpl_id.id))
        notices = tree.xpath('//div[contains(@class, "tp-request-action-row")]/div[@class="tp-request-stock-message"]')
        self.assertTrue(notices)
        self.assertEqual(notices[0].xpath('.//a[contains(@class, "tp-request-preorder-link")]/@href'), ['/prenotailtuoolio'])
        self.assertFalse(tree.xpath('//*[contains(@class, "tp-request-tile-add")]'))
        seasonal = html.fromstring(self.url_open(self.seasonal.product_tmpl_id.website_url).content)
        self.assertTrue(seasonal.xpath('//*[@class="tp-preorder-cta"]//a[@href="/prenotailtuoolio"]'))
        stock = html.fromstring(self.url_open(self.stock.product_tmpl_id.website_url).content)
        self.assertFalse(stock.xpath('//*[@class="tp-preorder-cta"]'))
        self.assertTrue(stock.xpath('//button[@name="add_to_cart"]'))

    def test_campaign_submission_creates_opportunity_without_order(self):
        state = self.update('set_configuration', self.seasonal, 2).json()['state']
        bootstrap = self.url_open('/torrepulia/request/current').json()
        counts = {model: self.env[model].search_count([]) for model in ('crm.lead', 'sale.order')}
        payload = {'selection_id': state['selection_id'], 'revision': state['revision'],
            'operation_id': secrets.token_hex(16), 'contact_name': 'Hybrid guest',
            'email': 'hybrid@example.invalid', 'privacy_accepted': True,
            'phone': '+39 380 000 0000', 'delivery_area': '71017'}
        with patch.object(type(self.env['ir.mail_server']), 'send_email', return_value='<hybrid@example.invalid>'):
            response = self.url_open('/torrepulia/campaign/submit', data={
                'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.env['crm.lead'].search_count([]), counts['crm.lead'] + 1)
        self.assertEqual(self.env['sale.order'].search_count([]), counts['sale.order'])
