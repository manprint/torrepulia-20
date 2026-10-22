import json
import secrets
from types import SimpleNamespace
from unittest.mock import patch

from lxml import html

from odoo import fields
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools.misc import format_amount

from ..models.public_policy import economic_data, storefront_html
from ..models.commerce import public_storefront


@tagged('post_install', '-at_install')
class TestCommercePolicy(TransactionCase):
    def test_stock_notice_separates_configured_copy_from_campaign_action(self):
        website = self.env['website'].search([], limit=1)
        product = self.env['product.template'].create({'name':'Notice QA',
            'out_of_stock_message': '<div style="text-align:center"><strong>Prenota il raccolto!</strong> <a class="btn rounded-circle" href="/prenotailtuoolio">PRENOTA ORA!</a></div>'})
        with patch.object(type(website), '_request_preorder_url', return_value=False):
            closed = product._request_stock_notice(website)
            self.assertFalse(closed['preorder_url'])
        with patch.object(type(website), '_request_preorder_url', return_value='/prenotailtuoolio'):
            opened = product._request_stock_notice(website)
            self.assertEqual(opened['preorder_url'], '/prenotailtuoolio')
        self.assertEqual(opened['message'], 'Prenota il raccolto!')
        self.assertNotIn('PRENOTA ORA', opened['message'])
        self.assertNotIn('style', opened['message'])
        product.out_of_stock_message = '<p>Consulta <a href="/contactus">i contatti</a>.</p>'
        notice = product._request_stock_notice(website)
        self.assertFalse(notice['preorder_url'])
        self.assertEqual(notice['links'], [{'url':'/contactus','label':'i contatti'}])
        product.out_of_stock_message = False
        self.assertEqual(product._request_stock_notice(website)['message'], '')

    def test_frontend_editor_request_without_website_is_outside_public_policy(self):
        empty = self.env['website'].browse()
        fake = SimpleNamespace(is_frontend=True, env=SimpleNamespace(website=empty),
                               httprequest=SimpleNamespace(path='/website/save_xml'))
        with patch('odoo.addons.website_torrepulia_request.models.commerce.request', fake):
            self.assertFalse(public_storefront())
            fake.env.website = self.env['website'].search([], limit=1)
            fake.httprequest.path = '/shop'
            self.assertTrue(public_storefront())

    def test_builder_copies_and_structured_data(self):
        source = '''<!doctype html><html><body><header><div class="o_wsale_my_cart">
        <a href="/shop/cart">Carrello</a></div></header>
        <button name="add_to_cart" data-product-id="7" data-action="buy_now">Acquista ora</button>
        <div class="product_price"><span>123,45 €</span></div>
        <span>Confezione speciale 123,45 €</span>
        <script type="application/ld+json">{"@type":"Product","name":"Olio","offers":{"price":123.45}}</script>
        <input data-product-tracking-info='{"price":123.45}'/>
        </body></html>'''
        output = storefront_html(source, '/riepilogo-configurato', True)
        tree = html.fromstring(output)
        self.assertNotIn('123', output)
        self.assertNotIn('offers', output)
        self.assertEqual(tree.xpath('//header//a/@href'), ['/riepilogo-configurato'])
        self.assertTrue(tree.xpath('//*[@data-tp-request-header]'))
        self.assertFalse(tree.xpath('//*[contains(@class,"o_wsale_my_cart")]'))
        self.assertEqual(tree.xpath('//button/text()'), ['Aggiungi alla richiesta'])
        self.assertEqual(tree.xpath('//button/@data-action'), ['add_to_cart'])
        self.assertEqual(tree.xpath('//button/@data-product-id'), ['7'])
        self.assertIn('"name": "Olio"', output)
        visible = storefront_html(source, '/riepilogo-configurato', False)
        self.assertIn('123,45', visible)
        self.assertIn('offers', visible)

    def test_combination_redaction_keeps_configuration(self):
        data = {'price': 123, 'list_price': 234, 'has_discounted_price': True,
                'hide_price': False, 'product_id': 9, 'is_combination_possible': True,
                'free_qty': 0, 'values': [{'value': 7, 'price_extra': 4}],
                'price_extra_html': '<b>4 €</b>'}
        cleaned = economic_data(data, '/la-tua-richiesta')
        self.assertEqual(cleaned, {'hide_price': True, 'product_id': 9,
                                  'is_combination_possible': True, 'free_qty': 0,
                                  'values': [{'value': 7}]})
        self.assertEqual(economic_data(data, '/la-tua-richiesta', False), data)

    def test_dynamic_snippet_removes_entire_monetary_wrappers(self):
        source = '<div><span name="product_price"><span class="oe_currency_value">12.00</span> €</span><del><small><span class="oe_currency_value">15.00</span> €</small></del><strong>Olio</strong></div>'
        result = storefront_html(source, '/la-tua-richiesta', True)
        self.assertNotIn('€', result)
        self.assertNotIn('product_price', result)
        self.assertNotIn('<del', result)
        self.assertIn('<strong>Olio</strong>', result)


@tagged('post_install', '-at_install')
class TestCommerceHttp(HttpCase):
    def test_variant_availability_and_website_warehouse(self):
        attribute = self.env['product.attribute'].create({'name': 'Stock filtration', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Filtrato'}), fields.Command.create({'name': 'Non filtrato'})]})
        template = self.env['product.template'].create({'name': 'Warehouse variant QA',
            'is_published': True, 'is_storable': True, 'allow_out_of_stock_order': False,
            'out_of_stock_message': '<p>Variante esaurita QA</p>',
            'attribute_line_ids': [fields.Command.create({'attribute_id': attribute.id,
                'value_ids': [fields.Command.set(attribute.value_ids.ids)]})]})
        available, exhausted = template.product_variant_ids
        # Test-only stock: the unavailable variant exists solely in another warehouse.
        primary = self.env['stock.warehouse'].create({'name': 'Website warehouse QA', 'code': 'QAON',
            'company_id': self.site.company_id.id})
        self.site.warehouse_id = primary
        other = self.env['stock.warehouse'].create({'name': 'Other website warehouse QA', 'code': 'QASTK',
            'company_id': self.site.company_id.id})
        self.env['stock.quant']._update_available_quantity(available, self.site.warehouse_id.lot_stock_id, 4)
        self.env['stock.quant']._update_available_quantity(exhausted, other.lot_stock_id, 7)
        self.add(available, 2)
        bootstrap = self.url_open('/torrepulia/request/current').json()
        payload = {'operation': 'add', 'operation_id': secrets.token_hex(16),
            'selection_id': bootstrap['state']['selection_id'], 'revision': bootstrap['state']['revision'],
            'product_id': exhausted.id, 'quantity': 1}
        response = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 422, response.text)
        tree = html.fromstring(self.url_open('/shop').content)
        inputs = tree.xpath('//input[contains(@class,"tp-catalog-variant-input")]')
        flags = {int(node.get('value')): node.get('data-sold-out') for node in inputs}
        self.assertEqual(flags[available.id], '0')
        self.assertEqual(flags[exhausted.id], '1')
        state = self.url_open('/torrepulia/request/current').json()['state']
        self.assertEqual(len(state['lines']), 1)
        self.assertEqual(state['lines'][0]['product_id'], available.id)
        self.assertEqual(state['quantity'], 2)

    def test_sold_out_catalog_message_api_and_seasonal_preorder(self):
        self.product.write({'is_storable': True, 'allow_out_of_stock_order': False,
            'out_of_stock_message': '<p>Esaurito QA: <a href="/prenotailtuoolio">Prenota il nuovo raccolto</a></p>'})
        orders = self.env['sale.order'].search_count([])
        shop = self.url_open('/shop')
        self.assertEqual(shop.status_code, 200)
        self.assertIn('Esaurito QA:', shop.text)
        combination = self.rpc('/website_sale/get_combination_info', {
            'product_template_id': self.product.product_tmpl_id.id, 'product_id': self.product.id,
            'combination': [], 'add_qty': 1})['result']
        self.assertIn('Esaurito QA:', combination['tp_request_stock_notice']['message'])

        tree = html.fromstring(shop.content)
        self.assertFalse(tree.xpath('//*[@data-tp-request-add-template="%s"]' % self.product.product_tmpl_id.id))
        bootstrap = self.url_open('/torrepulia/request/current').json()
        payload = {'operation': 'add', 'operation_id': secrets.token_hex(16),
            'selection_id': bootstrap['state']['selection_id'], 'revision': bootstrap['state']['revision'],
            'product_id': self.product.id, 'quantity': 2}
        response = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 422, response.text)
        self.assertFalse(self.url_open('/torrepulia/request/current').json()['state']['lines'])
        # The seasonal path remains a deliberate preorder, even with no physical stock.
        payload.update(operation='set_configuration', operation_id=secrets.token_hex(16))
        response = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['state']['quantity'], 2)
        self.product.allow_out_of_stock_order = True
        self.assertEqual(self.add(self.product, 1)['quantity'], 3)
        shop = self.url_open('/shop')
        self.assertTrue(html.fromstring(shop.content).xpath(
            '//*[@data-tp-request-add-template="%s"]' % self.product.product_tmpl_id.id))
        self.assertNotIn('Esaurito QA:', shop.text)
        self.assertEqual(self.env['sale.order'].search_count([]), orders)

    def test_addition_receipt_prices_only_added_quantity_and_hides_amounts(self):
        orders = self.env['sale.order'].search_count([])
        self.add(self.product, 2)
        state = self.add(self.product, 3)
        self.assertEqual(state['quantity'], 5)
        self.assertEqual(state['addition']['quantity'], 3)
        self.assertEqual(state['addition']['product_id'], self.product.id)
        self.assertIn('370.35', state['addition']['subtotal_display'])
        self.site.torrepulia_request_show_prices = False
        hidden = self.add(self.product, 1)['addition']
        self.assertNotIn('subtotal_display', hidden)
        self.assertNotIn('currency', hidden)
        self.assertEqual(self.env['sale.order'].search_count([]), orders)

    def test_inline_variants_are_real_explicit_and_keep_independent_lines(self):
        attr = self.env['product.attribute'].create({'name': 'Filtrazione', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Filtrato'}), fields.Command.create({'name': 'Non filtrato'})]})
        template = self.env['product.template'].create({'name': 'Inline oil', 'is_published': True,
            'attribute_line_ids': [fields.Command.create({'attribute_id': attr.id,
                'value_ids': [fields.Command.set(attr.value_ids.ids)]})]})
        variants = template.product_variant_ids
        self.assertEqual(len(variants), 2)
        self.assertEqual(set(template._request_inline_variants().ids), set(variants.ids))
        self.add(variants[0], 2)
        state = self.add(variants[1], 3)
        self.assertEqual(sorted(line['quantity'] for line in state['lines']), [2, 3])
        self.assertEqual(state['addition']['product_id'], variants[1].id)
        self.assertIn(variants[1].product_template_attribute_value_ids.name, state['addition']['name'])
        self.assertEqual(len(template.product_variant_ids), 2)

    def setUp(self):
        super().setUp()
        self.site = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Commerce test team', 'company_id': self.site.company_id.id})
        self.site.write({'torrepulia_request_team_id': team.id,
                         'torrepulia_commercial_mode': 'request', 'torrepulia_request_show_prices': True})
        self.product = self.env['product.product'].create({
            'name': 'Commerce oil test', 'is_published': True, 'list_price': 123.45})

    def rpc(self, path, params):
        return self.url_open(path, data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params}),
                             headers={'Content-Type': 'application/json'}).json()

    def add(self, product, quantity=2):
        bootstrap = self.url_open('/torrepulia/request/current').json()
        payload = {'operation': 'add', 'operation_id': secrets.token_hex(16),
                   'selection_id': bootstrap['state']['selection_id'], 'revision': bootstrap['state']['revision'],
                   'product_id': product.id, 'quantity': quantity}
        response = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['state']

    def test_catalog_product_preview_and_standard_fallback(self):
        orders = self.env['sale.order'].search_count([])
        shop = self.url_open('/shop')
        self.assertEqual(shop.status_code, 200)
        self.assertIn('data-tp-request-mode="1"', shop.text)
        self.assertIn('Aggiungi alla richiesta', shop.text)
        self.assertIn('data-tp-request-header', shop.text)
        page = self.url_open(self.product.website_url)
        self.assertEqual(page.status_code, 200)
        self.assertIn('Aggiungi alla richiesta', page.text)
        self.assertTrue(self.url_open('/torrepulia/request/product?template_id=%s' % self.product.product_tmpl_id.id).json()['product_id'])
        state = self.add(self.product)
        self.assertEqual(state['quantity'], 2)
        preview = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertTrue(preview['lines'][0]['subtotal_display'])
        self.assertTrue(preview['products_total_display'])
        native = self.rpc('/website_sale/get_combination_info', {
            'product_template_id': self.product.product_tmpl_id.id, 'product_id': self.product.id,
            'combination': [], 'add_qty': 2})['result']
        self.assertEqual(preview['lines'][0]['price_display'],
                         format_amount(self.env, native['price'], self.site.currency_id))
        self.assertEqual(self.url_open('/la-tua-richiesta').status_code, 200)
        self.assertEqual(self.url_open('/shop/cart', allow_redirects=False).status_code, 303)
        self.assertEqual(self.env['sale.order'].search_count([]), orders)
        # The disabled website delivers the original native template and actions.
        self.site.torrepulia_commercial_mode = 'shop'
        standard = self.url_open(self.product.website_url)
        self.assertNotIn('data-tp-request-mode="1"', standard.text)
        self.assertIn('name="add_to_cart"', standard.text)
        self.assertEqual(self.product.list_price, 123.45)

    def test_hidden_prices_all_public_surfaces(self):
        self.site.torrepulia_request_show_prices = False
        for path in ('/shop', self.product.website_url):
            # Pretending to be an editor iframe cannot bypass public redaction.
            response = self.url_open(path, headers={'Sec-Fetch-Dest': 'iframe'})
            self.assertEqual(response.status_code, 200, response.text[:200])
            self.assertNotIn('123.45', response.text)
            self.assertNotIn('123,45', response.text)
            tree = html.fromstring(response.text)
            self.assertFalse(tree.xpath('//*[@itemprop="price" or @itemprop="offers"]'))
            self.assertFalse(tree.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," oe_currency_value ")]'))
        info = self.rpc('/website_sale/get_combination_info', {
            'product_template_id': self.product.product_tmpl_id.id, 'product_id': self.product.id,
            'combination': [], 'add_qty': 2})
        self.assertNotIn('error', info, info)
        self.assertNotIn('price', info['result'])
        self.assertNotIn('list_price', info['result'])
        self.assertTrue(info['result']['hide_price'])
        self.add(self.product)
        preview = self.url_open('/torrepulia/request/preview').json()['state']
        self.assertNotIn('products_total_display', preview)
        self.assertNotIn('subtotal_display', preview['lines'][0])
        self.assertEqual(self.product.list_price, 123.45)

    def test_explicit_variants_resolve_and_catalog_isolation(self):
        attr = self.env['product.attribute'].create({'name': 'Commerce format', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Small'}), fields.Command.create({'name': 'Large'})]})
        template = self.env['product.template'].create({'name': 'Commerce configured oil', 'is_published': True,
            'attribute_line_ids': [fields.Command.create({'attribute_id': attr.id,
                'value_ids': [fields.Command.set(attr.value_ids.ids)]})]})
        meta = self.url_open('/torrepulia/request/product?template_id=%s' % template.id).json()
        self.assertTrue(meta['requires_configuration'])
        bootstrap = self.url_open('/torrepulia/request/current').json()
        variant = template.product_variant_ids[-1]
        response = self.url_open('/torrepulia/request/resolve', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps({
                'template_id': template.id, 'ptav_ids': variant.product_template_attribute_value_ids.ids})})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['product_id'], variant.id)
        self.assertEqual(self.add(variant)['lines'][0]['product_id'], variant.id)
        template.is_published = False
        denied = self.url_open('/torrepulia/request/product?template_id=%s' % template.id)
        self.assertEqual(denied.status_code, 422)
        state = self.url_open('/torrepulia/request/current').json()['state']
        self.assertFalse(state['lines'][0]['available'])
        self.assertTrue(state['lines'][0]['warning'])

    def test_cart_guard_and_builder_content_is_never_written(self):
        orders = self.env['sale.order'].search_count([])
        params = {'product_template_id': self.product.product_tmpl_id.id,
                  'product_id': self.product.id, 'quantity': 2}
        rejected = self.rpc('/shop/cart/add', params)
        self.assertIn('error', rejected)
        self.assertEqual(self.env['sale.order'].search_count([]), orders)
        source = '''<t t-name="test.request.builder"><t t-call="website.layout">
            <div id="wrap" class="oe_structure"><a href="/shop/cart">Carrello</a>
            <p class="product_price">123,45 €</p><p>Testo editoriale intatto</p></div>
            </t></t>'''
        view = self.env['ir.ui.view'].create({'name': 'Request Builder preservation', 'type': 'qweb',
            'key': 'test.request.builder', 'arch_db': source, 'website_id': self.site.id})
        self.env['website.page'].create({'name': 'Request Builder preservation', 'url': '/test-request-builder',
            'view_id': view.id, 'website_id': self.site.id, 'is_published': True})
        self.site.write({'torrepulia_request_show_prices': False,
                         'torrepulia_request_summary_url': '/riepilogo-configurato'})
        original = view.arch_db
        for path in ('/test-request-builder', '/test-request-builder?enable_editor=1'):
            response = self.url_open(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('123,45', response.text)
            self.assertIn('/riepilogo-configurato', response.text)
            self.assertIn('Testo editoriale intatto', response.text)
        view.invalidate_recordset()
        self.assertEqual(view.arch_db, original)
        # Native server operation is restored when mode is disabled.
        self.site.torrepulia_commercial_mode = 'shop'
        accepted = self.rpc('/shop/cart/add', params)
        self.assertNotIn('error', accepted, accepted)
        self.assertEqual(self.env['sale.order'].search_count([]), orders + 1)
