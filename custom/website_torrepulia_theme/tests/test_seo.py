import json
import re

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestLaunchSeo(HttpCase):
    """Search engines find the new site; old torrepulia.it addresses land on the right page."""

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        self.website.torrepulia_theme_enabled = True

    def test_old_addresses_redirect_without_overriding_the_manager(self):
        # As before the launch migration: no redirect of ours yet.
        self.env['website.rewrite'].search([('name', '=like', 'torrepulia.it precedente%')]).unlink()
        latta =self.env['product.template'].create({
            'name': 'Latta di prova', 'default_code': 'LARGLAT5', 'is_published': True, 'website_id': self.website.id})
        self.env['website.rewrite'].create({'name': 'Gestore', 'url_from': '/blog', 'url_to': '/aboutus',
                                            'redirect_type': '301', 'website_id': self.website.id})
        self.website._torrepulia_launch_seo()
        self.website._torrepulia_launch_seo()  # A second run adds nothing.
        rewrites = self.env['website.rewrite'].search([('website_id', '=', self.website.id)])
        by_path = {rewrite.url_from: rewrite for rewrite in rewrites}
        ours = rewrites.filtered(lambda rewrite: rewrite.name.startswith('torrepulia.it precedente'))
        self.assertEqual(len(ours), len(set(ours.mapped('url_from'))))
        self.assertEqual(by_path['/shop/olio-evo-la-regina-lattina-5-litri-4'].url_to, latta.website_url)
        self.assertEqual(by_path['/shop/olio-evo-la-regina-duetto-2-bottiglie-500ml-3'].url_to, '/shop')
        self.assertEqual(by_path['/blog'].url_to, '/aboutus')
        self.assertEqual(by_path['/home'].redirect_type, '301')

    def test_home_is_indexed_and_shop_speaks_italian(self):
        # As in production: every "/" page without index and with Odoo's placeholder description.
        homes = self.env['website.page'].search([('url', '=', '/')])
        homes.website_indexed = False
        homes.view_id.website_meta_title = False
        homes.view_id.website_meta_description = 'This is the homepage of the website'
        self.website._torrepulia_launch_seo()
        home = self.url_open('/').text
        self.assertNotIn('name="robots" content="noindex"', home)
        self.assertIn('Olio extravergine Peranzana della famiglia Leone</title>', home)
        self.assertNotIn('This is the homepage of the website', home)
        self.assertTrue(self.website.social_default_image)
        shop = self.url_open('/shop').text
        self.assertIn('<title>Acquista olio extravergine Peranzana | Torrepulia</title>', shop)

    def test_consent_bar_comes_before_the_meta_pixel(self):
        self.website._torrepulia_launch_seo()
        self.assertTrue(self.website.cookies_bar)
        self.website.torrepulia_meta_pixel_id = '123456789012345'
        page = self.url_open('/').text
        self.assertIn('id="tp-cookies-title"', page)
        self.assertNotIn('o_cookie_policy_link_container', page)  # The editorial footer carries the link.
        self.assertIn('data-pixel-id="123456789012345"', page)
        self.assertNotIn('data-consented', page)  # No choice yet: the Pixel waits for "Accetta".
        self.opener.cookies.set('website_cookies_bar', '{"required": true, "optional": true}')
        self.assertIn('data-consented="1"', self.url_open('/').text)
        self.website.cookies_bar = False
        self.assertNotIn('data-pixel-id', self.url_open('/').text)

    def test_llms_txt_is_served_and_the_manager_text_stays(self):
        self.website.llms_txt = False
        self.website.company_id.email = 'info@torrepulia.it'
        self.website._torrepulia_llms_txt()
        response = self.url_open('/llms.txt')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.text.startswith('# Torrepulia\n'))
        self.assertIn('(%s/l-olio)' % self.website.get_base_url(), response.text)
        self.assertIn('- Email: info@torrepulia.it', response.text)
        self.assertNotIn('{', response.text)
        self.website.llms_txt = '# Testo del gestore'
        self.website._torrepulia_llms_txt()
        self.assertEqual(self.website.llms_txt, '# Testo del gestore')

    def test_robots_and_sitemap_publish_the_https_domain(self):
        # As in production: the proxy reaches Odoo in http, the website domain is https.
        host = '127.0.0.1:%s' % self.http_port()
        self.website.domain = 'https://%s' % host
        robots = self.url_open('/robots.txt').text
        self.assertIn('Sitemap: https://%s/sitemap.xml' % host, robots)
        sitemap = self.url_open('/sitemap.xml').text
        self.assertIn('<loc>https://%s/' % host, sitemap)
        self.assertNotIn('http://%s' % host, sitemap)
        # A website without an https domain keeps the address of the request.
        self.website.domain = False
        self.assertIn('Sitemap: http://%s/sitemap.xml' % host, self.url_open('/robots.txt').text)

    def test_structured_data_describe_the_company_and_the_products(self):
        company = self.website.company_id
        company.write({'phone': '+39 0882 000000', 'city': 'Torremaggiore', 'social_instagram': 'https://www.instagram.com/torrepulia'})
        organization = self.website._prepare_jsonld_vals()
        self.assertEqual(organization['telephone'], '+39 0882 000000')
        self.assertEqual(organization['address']['addressLocality'], 'Torremaggiore')
        self.assertEqual(organization['sameAs'], ['https://www.instagram.com/torrepulia'])
        product = self.env['product.template'].create({
            'name': 'Latta di prova', 'is_published': True, 'website_id': self.website.id})
        page = self.url_open(product.website_url).text
        self.assertIn('"brand": {"@type": "Brand", "name": "%s"}' % self.website.name, page)
        self.assertIn('"description": "Latta di prova: olio extravergine monovarietale Peranzana', page)

    def test_terms_lead_to_the_sales_terms_page(self):
        if not self.env['website.page'].search_count([('url', '=', '/termini-e-condizioni')]):
            self.skipTest('No sales terms page in this database')
        response = self.url_open('/terms', allow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.headers['Location'].endswith('/termini-e-condizioni'))

    def test_product_markup_tells_shipping_and_the_organization_the_returns(self):
        self.env['delivery.carrier'].search([]).is_published = False
        carrier = self.env['delivery.carrier'].create({
            'name': 'Corriere di prova', 'delivery_type': 'fixed', 'fixed_price': 9.9, 'is_published': True,
            'free_over': True, 'amount': 99, 'website_id': self.website.id,
            'product_id': self.env['product.product'].create({'name': 'Spedizione di prova', 'type': 'service'}).id})
        cheap, rich = self.env['product.template'].create([
            {'name': 'Duetto di prova', 'list_price': 22, 'is_published': True, 'website_id': self.website.id, 'taxes_id': False},
            {'name': 'Scorta di prova', 'list_price': 120, 'is_published': True, 'website_id': self.website.id, 'taxes_id': False}])
        offers = {}
        for product in (cheap, rich):
            page = self.url_open(product.website_url).text
            markup = [json.loads(block) for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
            graph = [node for block in markup for node in block.get('@graph', [block])]
            offers[product] = next(node for node in graph if node.get('@type') == 'Product')['offers']
        self.assertEqual(offers[cheap]['shippingDetails']['shippingRate']['value'], 9.9)
        self.assertEqual(offers[rich]['shippingDetails']['shippingRate']['value'], 0)
        self.assertEqual(offers[cheap]['shippingDetails']['shippingDestination'], [{'@type': 'DefinedRegion', 'addressCountry': 'IT'}])
        self.assertEqual(offers[cheap]['shippingDetails']['deliveryTime']['transitTime']['maxValue'], 3)
        carrier.is_published = False
        self.assertFalse(self.website._torrepulia_shipping_jsonld(22))
        policy = self.website._prepare_jsonld_vals()['hasMerchantReturnPolicy']
        self.assertEqual(policy['merchantReturnDays'], 14)

    def test_one_product_categories_leave_the_index_and_the_sitemap(self):
        Category = self.env['product.public.category']
        bottles, tins = Category.create([{'name': 'Bottiglie di prova'}, {'name': 'Latte di prova'}])
        self.env['product.template'].create([
            {'name': 'Bottiglia uno', 'is_published': True, 'website_id': self.website.id, 'public_categ_ids': [bottles.id]},
            {'name': 'Bottiglia due', 'is_published': True, 'website_id': self.website.id, 'public_categ_ids': [bottles.id]},
            {'name': 'Latta sola', 'is_published': True, 'website_id': self.website.id, 'public_categ_ids': [tins.id]}])
        tins_page = self.url_open(tins.website_url).text
        self.assertIn('<meta name="robots" content="noindex"/>', tins_page)
        self.assertIn('<meta name="description" content="Latte di prova: La Regina, olio extravergine', tins_page)
        self.assertNotIn('name="robots"', self.url_open(bottles.website_url).text)
        self.env['ir.attachment'].search([('url', '=like', '/sitemap%')]).unlink()
        sitemap = self.url_open('/sitemap.xml').text
        self.assertIn(bottles.website_url, sitemap)
        self.assertNotIn(tins.website_url, sitemap)

    def test_product_addresses_leave_out_the_internal_reference(self):
        self.env['website.rewrite'].search([('name', '=like', 'torrepulia.it precedente%')]).unlink()
        tin = self.env['product.template'].create({
            'name': 'La Regina latta', 'default_code': 'LARGLAT5', 'is_published': True, 'website_id': self.website.id})
        self.assertEqual(tin.with_context(website_id=self.website.id).website_url, '/shop/la-regina-latta-%s' % tin.id)
        # Redirects written before: the target still had the reference in it.
        old = self.env['website.rewrite'].create({
            'name': 'torrepulia.it precedente: latta', 'url_from': '/shop/olio-evo-la-regina-lattina-5-litri-4',
            'url_to': '/shop/larglat5-la-regina-latta-%s' % tin.id, 'redirect_type': '301', 'website_id': self.website.id})
        manager = self.env['website.rewrite'].create({
            'name': 'Gestore', 'url_from': '/shop/olio-evo-la-regina-duetto-2-bottiglie-500ml-3',
            'url_to': '/shop', 'redirect_type': '301', 'website_id': self.website.id})
        self.website._torrepulia_refresh_product_redirects()
        self.assertEqual(old.url_to, '/shop/la-regina-latta-%s' % tin.id)
        self.assertEqual(manager.url_to, '/shop')
        self.assertIn('/shop/la-regina-latta-%s"' % tin.id, self.url_open('/shop').text)
        # The address with the reference still reaches the product.
        response = self.url_open('/shop/larglat5-la-regina-latta-%s' % tin.id, allow_redirects=False)
        self.assertIn(response.status_code, (200, 301, 302, 303))

    def test_cart_tells_how_far_free_shipping_is(self):
        self.env['delivery.carrier'].search([]).is_published = False
        self.env['delivery.carrier'].create({
            'name': 'Corriere di prova', 'delivery_type': 'fixed', 'fixed_price': 9.9, 'is_published': True,
            'free_over': True, 'amount': 99, 'website_id': self.website.id,
            'product_id': self.env['product.product'].create({'name': 'Spedizione di prova', 'type': 'service'}).id})
        bottle = self.env['product.product'].create({
            'name': 'Bottiglia di prova', 'list_price': 60, 'type': 'consu', 'is_published': True,
            'website_id': self.website.id, 'taxes_id': False})

        def add():
            response = self.url_open('/shop/cart/add', data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                'params': {'product_template_id': bottle.product_tmpl_id.id, 'product_id': bottle.id, 'quantity': 1}}),
                headers={'Content-Type': 'application/json'})
            self.assertEqual(response.status_code, 200, response.text)

        add()
        cart = self.url_open('/shop/cart').text
        self.assertIn('Ti mancano', cart)
        self.assertIn('width: 61%', cart)
        add()
        cart = self.url_open('/shop/cart').text
        self.assertNotIn('Ti mancano', cart)
        self.assertIn('La spedizione è gratuita.', cart)
