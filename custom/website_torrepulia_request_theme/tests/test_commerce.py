import json

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestThemeRequestCommerce(HttpCase):
    def test_formats_request_prices_and_native_fallback(self):
        website = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Theme test team', 'company_id': website.company_id.id})
        website.write({'torrepulia_request_team_id': team.id, 'torrepulia_commercial_mode': 'request',
                       'torrepulia_theme_enabled': True, 'torrepulia_request_show_prices': True})
        product = self.env['product.template'].create({'name': 'Theme commerce oil', 'is_published': True,
            'list_price': 143.25, 'torrepulia_format_name': 'Test format', 'torrepulia_format_detail': '5 L'})
        if 'torrepulia_campaign_id' in website._fields:
            website.torrepulia_campaign_id = False
        orders = self.env['sale.order'].search_count([])

        def formats(promoted=False):
            response = self.url_open('/torrepulia/formats', data=json.dumps({
                'jsonrpc': '2.0', 'method': 'call', 'params': {'ids': product.ids, 'promoted': promoted}}),
                headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertNotIn('error', data, data)
            return data['result']['html']

        visible = formats()
        self.assertIn('Aggiungi alla richiesta', visible)
        self.assertIn('data-tp-request-add-template', visible)
        self.assertIn('option-price', visible)
        promoted = formats(promoted=True)
        self.assertIn('early-purchase', promoted)
        self.assertIn('data-tp-request-add-template', promoted)
        self.assertNotIn('shop-layout', promoted)
        product.write({'is_storable': True, 'allow_out_of_stock_order': False,
            'out_of_stock_message': '<p>Formato esaurito QA: <a href="/prenotailtuoolio">Prenota</a></p>'})
        for output in (formats(), formats(promoted=True)):
            self.assertIn('Formato esaurito QA:', output)
            self.assertNotIn('data-tp-request-add-template', output)
            self.assertNotIn('tp-request-preorder-link', output)
        product.allow_out_of_stock_order = True
        website.torrepulia_request_show_prices = False
        hidden = formats()
        self.assertIn('Aggiungi alla richiesta', hidden)
        self.assertNotIn('143.25', hidden)
        self.assertNotIn('143,25', hidden)
        self.assertNotIn('option-price', hidden)
        website.torrepulia_commercial_mode = 'shop'
        native = formats()
        self.assertNotIn('data-tp-request-add-template', native)
        self.assertIn('option-price', native)
        self.assertEqual(self.env['sale.order'].search_count([]), orders)
        self.assertEqual(product.list_price, 143.25)

    def test_editorial_title_sections_and_other_formats(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        product = self.env['product.template'].create({'name': 'Editorial QA oil', 'is_published': True,
            'torrepulia_format_name': 'Editorial format', 'torrepulia_web_title': 'Titolo configurato QA',
            'torrepulia_sensory_profile': '<p>Note sensoriali approvate QA</p>',
            'torrepulia_food_pairings': '<p>Abbinamenti approvati QA</p>',
            'torrepulia_shipping_storage': '<p>Condizioni approvate QA</p>'})
        other = self.env['product.template'].create({'name': 'Other format QA', 'is_published': True,
            'torrepulia_format_name': 'Other format'})
        page = self.url_open(product.website_url)
        self.assertEqual(page.status_code, 200)
        self.assertIn('Titolo configurato QA', page.text)
        self.assertIn('<summary>Profilo sensoriale</summary>', page.text)
        self.assertIn('<summary>Abbinamenti in cucina</summary>', page.text)
        self.assertIn('<summary>Spedizione e conservazione</summary>', page.text)
        self.assertIn('Note sensoriali approvate QA', page.text)
        # The storage guide, once published, closes the storage section.
        guide = self.env.ref('website_torrepulia_theme.blog_post_storage_guide', raise_if_not_found=False)
        if guide:
            guide.is_published = False
            self.assertNotIn('tp-product-guide', self.url_open(product.website_url).text)
            guide.is_published = True
            self.assertIn('<a href="%s">Leggi la guida' % guide.website_url, self.url_open(product.website_url).text)
        # Subtitle: format (not in the title), default denomination, contents.
        self.assertIn('Editorial format · Olio extravergine di oliva Peranzana', page.text)
        product.write({'torrepulia_web_title': False, 'torrepulia_sensory_profile': '<p><br></p>'})
        page = self.url_open(product.website_url)
        self.assertNotIn('<summary>Profilo sensoriale</summary>', page.text)
        self.assertIn('Editorial QA oil', page.text)
        product.write({'name': 'La Regina, Editorial format 5 litri', 'torrepulia_format_detail': '5 litri',
                       'torrepulia_denomination': 'Olio extravergine di oliva'})
        page = self.url_open(product.website_url).text
        self.assertIn('La Regina,<span class="tp-title-format"> Editorial format 5 litri</span>', page)
        self.assertIn('<p class="product-subtitle">Olio extravergine di oliva · 5 litri</p>', page)
        product.torrepulia_denomination = False
        self.assertIn('<p class="product-subtitle">5 litri</p>', self.url_open(product.website_url).text)
        for mode in ['request', 'shop']:
            if mode == 'request':
                team = self.env['crm.team'].create({'name': 'Editorial team', 'company_id': website.company_id.id})
                website.torrepulia_request_team_id = team
            website.torrepulia_commercial_mode = mode
            result = self.url_open('/torrepulia/formats', data=json.dumps({'jsonrpc':'2.0', 'method':'call',
                'params': {'ids': [product.id, other.id], 'exclude_template_id': product.id}}),
                headers={'Content-Type':'application/json'}).json()
            self.assertNotIn('error', result, result)
            output = result['result']['html']
            self.assertNotIn('data-product="%s"' % product.id, output)
            self.assertIn('data-product="%s"' % other.id, output)

    def test_native_ribbon_restored_with_prices_hidden(self):
        website = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Ribbon team', 'company_id': website.company_id.id})
        website.write({'torrepulia_theme_enabled': True, 'torrepulia_commercial_mode': 'request',
            'torrepulia_request_team_id': team.id, 'torrepulia_request_show_prices': False})
        ribbon = self.env['product.ribbon'].create({'name': 'Nastro configurato QA', 'assign': 'manual'})
        product = self.env['product.template'].create({'name':'Ribbon QA oil','is_published':True,
            'torrepulia_format_name':'Ribbon format', 'website_ribbon_id': ribbon.id, 'list_price': 143.25})
        result = self.url_open('/torrepulia/formats', data=json.dumps({'jsonrpc':'2.0', 'method':'call',
            'params': {'ids':product.ids}}), headers={'Content-Type':'application/json'}).json()
        self.assertNotIn('error', result, result)
        output = result['result']['html']
        self.assertIn('mc-format-ribbon', output)
        self.assertIn('o_ribbons', output)
        self.assertEqual(output.count('Nastro configurato QA'), 2)
        self.assertNotIn('143.25', output)
        self.assertNotIn('option-price', output)
