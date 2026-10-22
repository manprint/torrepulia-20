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
        # One row per format: the state label and the single action follow stock and campaign.
        rows = {row.xpath('string(.//h2)').strip(): row for row in tree.xpath('//li[@class="tp-shop-row"]')}
        year = str(self.campaign.opens_at.year if self.campaign.opens_at else fields.Datetime.now().year)
        seasonal = rows['Hybrid new harvest']
        self.assertEqual(seasonal.xpath('string(.//*[contains(@class, "tp-shop-state")])').split(),
                         ['Raccolto', year, '·', 'in', 'prenotazione'])
        self.assertEqual(seasonal.xpath('.//div[@class="tp-shop-row-action"]/a/@href'), ['/prenotailtuoolio'])
        stock = rows['Hybrid stock bottle']
        self.assertIn('Disponibile subito', stock.text_content())
        self.assertEqual(stock.xpath('.//div[@class="tp-shop-row-action"]/a/@href'),
                         [self.stock.product_tmpl_id.website_url])
        sold_out = rows['Hybrid sold-out stock']
        self.assertIn('Temporaneamente esaurito', sold_out.text_content())
        self.assertEqual(sold_out.xpath('.//div[@class="tp-shop-row-action"]/a/@href'), ['/prenotailtuoolio'])
        # The new oil opens the page; search, sorting and wishlist are gone.
        band = tree.xpath('//section[@class="tp-season"]')
        self.assertEqual(band[0].xpath('string(.//h2)').split(), ['Olio', 'nuovo', year])
        self.assertFalse(tree.xpath('//*[contains(concat(" ", @class, " "), " products_header ")] | //*[@id="o_wsale_products_grid"]'))
        self.assertFalse(tree.xpath('//*[contains(@class, "o_add_wishlist")]'))
        seasonal = html.fromstring(self.url_open(self.seasonal.product_tmpl_id.website_url).content)
        self.assertTrue(seasonal.xpath('//*[@class="tp-preorder-cta"]//a[@href="/prenotailtuoolio"]'))
        stock = html.fromstring(self.url_open(self.stock.product_tmpl_id.website_url).content)
        self.assertFalse(stock.xpath('//*[@class="tp-preorder-cta"]'))
        self.assertTrue(stock.xpath('//button[@name="add_to_cart"]'))
        # Every label can be rewritten: seasonal ones on the campaign, the others on the website.
        self.campaign.write({'shop_state_label': 'Olio nuovo, consegna a novembre',
                             'shop_band_title': 'La nuova annata', 'shop_band_text': ''})
        self.website.write({'torrepulia_shop_available_label': 'Pronta in cantina',
                            'torrepulia_shop_sold_out_label': 'Finita per ora'})
        tree = html.fromstring(self.url_open('/shop').content)
        states = {row.xpath('string(.//h2)').strip(): row.xpath('string(.//*[contains(@class, "tp-shop-state")])')
                  for row in tree.xpath('//li[@class="tp-shop-row"]')}
        self.assertEqual(states['Hybrid new harvest'], 'Olio nuovo, consegna a novembre')
        self.assertEqual(states['Hybrid stock bottle'], 'Pronta in cantina')
        self.assertEqual(states['Hybrid sold-out stock'], 'Finita per ora')
        self.assertEqual(tree.xpath('string(//section[@class="tp-season"]//h2)'), 'La nuova annata')
        self.assertIn('Lo moliamo e lo spediamo entro 48 ore', tree.xpath('string(//section[@class="tp-season"]//p)'))
        # Out of season the band goes away.
        self.campaign.state = 'closed'
        self.assertFalse(html.fromstring(self.url_open('/shop').content).xpath('//section[@class="tp-season"]'))

    def test_preorder_page_groups_filtration_counters_in_one_card(self):
        attribute = self.env['product.attribute'].create({'name': 'Filtrazione prova', 'value_ids': [
            fields.Command.create({'name': 'Filtrato'}), fields.Command.create({'name': 'Non filtrato'})]})
        tin = self.env['product.template'].create({
            'name': 'Hybrid tin', 'is_published': True, 'website_id': self.website.id, 'list_price': 69,
            'torrepulia_format_name': 'Latta 5 L', 'torrepulia_shop_audience': 'La scorta di famiglia.',
            'attribute_line_ids': [fields.Command.create({'attribute_id': attribute.id,
                                                          'value_ids': [fields.Command.set(attribute.value_ids.ids)]})]})
        self.campaign.line_ids = [fields.Command.create({'product_id': variant.id}) for variant in tin.product_variant_ids]
        tree = html.fromstring(self.url_open('/torrepulia/campaign/content').json()['html'])
        cards = tree.xpath('//article[@class="tp-campaign-card"]')
        self.assertEqual([card.xpath('string(.//h3)') for card in cards], ['Hybrid new harvest', 'Latta 5 L'])
        choices = cards[1].xpath('.//*[@data-campaign-config]')
        self.assertEqual([json.loads(choice.get('data-campaign-config'))['product_id'] for choice in choices],
                         tin.product_variant_ids.ids)
        self.assertEqual([choice.xpath('string(.//*[@class="tp-campaign-choice-label"])').strip() for choice in choices],
                         ['Filtrato', 'Non filtrato'])
        self.assertEqual([float(choice.get('data-unit-price')) for choice in choices], [69.0, 69.0])
        self.assertIn('La scorta di famiglia.', cards[1].text_content())
        self.assertTrue(tree.xpath('//*[@data-campaign-dock]//button[@data-campaign-dock-go]'))
        # An empty selection keeps the visitor on the page, pointing back to the formats.
        self.assertEqual(tree.xpath('//h2/@id'), ['tp-campaign-formats'])
        form = html.fromstring(self.url_open('/torrepulia/request/form?layout=campaign').content)
        self.assertEqual(form.xpath('//*[@data-review-empty]//a/@href'), ['#tp-campaign-formats'])

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
