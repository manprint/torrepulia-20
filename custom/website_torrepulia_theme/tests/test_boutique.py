from datetime import date

from lxml import html

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOilProfile(TransactionCase):
    def test_lab_rows_scale_regulated_values_and_skip_missing(self):
        profile = self.env['torrepulia.oil.profile'].create({
            'name': 'Raccolto di prova', 'lab': 'Frantoio di prova', 'report_date': date(2024, 11, 19),
            'acidity': 0.17, 'k270': 0.3, 'polyphenols': 588.98})
        rows = {row['label']: row for row in profile._torrepulia_lab_rows()}
        self.assertEqual(set(rows), {'Acidità', 'K270', 'Polifenoli totali'})
        self.assertEqual(rows['Acidità']['ratio'], 21)
        self.assertEqual(rows['K270']['ratio'], 100)
        self.assertIsNone(rows['Polifenoli totali']['ratio'])
        self.assertIn('589', rows['Polifenoli totali']['value'])
        self.assertIn('Frantoio di prova', profile._torrepulia_source())
        self.assertFalse(profile._torrepulia_facts())


@tagged('post_install', '-at_install')
class TestBoutiqueProductPage(HttpCase):
    def test_product_page_offers_formats_assurances_and_identity_card(self):
        website = self.env['website'].search([], limit=1)
        website.write({'torrepulia_theme_enabled': True, 'torrepulia_shipping_note': 'Nota di spedizione di prova'})
        profile = self.env['torrepulia.oil.profile'].create({'name': 'Raccolto di prova', 'acidity': 0.2})
        tin, box = self.env['product.template'].create([
            {'name': 'Boutique tin', 'is_published': True, 'website_id': website.id, 'list_price': 69,
             'torrepulia_format_name': 'Latta 5 L', 'torrepulia_oil_profile_id': profile.id},
            {'name': 'Boutique box', 'is_published': True, 'website_id': website.id, 'list_price': 69,
             'torrepulia_format_name': 'Bag in Box 5 L'}])
        page = self.url_open(tin.website_url).text
        self.assertIn('tp-formats', page)
        self.assertIn(box.website_url, page)
        self.assertIn('aria-current="page"', page)
        self.assertIn('Nota di spedizione di prova', page)
        self.assertIn("Carta d'identità dell'olio", page)
        self.assertIn('Raccolto di prova', page)
        self.assertNotIn("Carta d'identità dell'olio", self.url_open(box.website_url).text)

    def test_brand_fonts_are_self_hosted(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        website._torrepulia_use_local_fonts()
        self.assertFalse(website.with_context(website_id=website.id)._get_font_urls())
        head = self.url_open('/').text.partition('</head>')[0]
        self.assertNotIn('fonts.googleapis.com', head)

    def test_shop_lists_one_format_per_row_without_search_or_sorting(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        litre = self.env['product.base.unit'].create({'name': 'L'})
        website.show_product_reference_price = True
        tin = self.env['product.template'].create({
            'name': 'Row tin', 'is_published': True, 'website_id': website.id, 'list_price': 69,
            'torrepulia_format_name': 'Latta 5 L', 'torrepulia_shop_audience': 'La scorta di famiglia.',
            'base_unit_id': litre.id, 'base_unit_count': 5})
        page = html.fromstring(self.url_open('/shop').content)
        rows = [row for row in page.xpath('//li[@class="tp-shop-row"]') if row.xpath('string(.//h2)') == 'Latta 5 L']
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertIn('Disponibile subito', row.text_content())
        self.assertIn('La scorta di famiglia.', row.text_content())
        # 69 for 5 L, whatever the test database's language and currency.
        self.assertRegex(row.xpath('string(.//*[@class="tp-shop-unit-price"])'), r'13[.,]80')
        self.assertEqual(row.xpath('.//div[@class="tp-shop-row-action"]/a/@href'), [tin.website_url])
        self.assertFalse(page.xpath('//*[contains(concat(" ", @class, " "), " products_header ")] | //*[@id="o_wsale_products_grid"]'))
        # Without a seasonal campaign there is no new-oil band.
        self.assertFalse(page.xpath('//section[@class="tp-season"]'))
