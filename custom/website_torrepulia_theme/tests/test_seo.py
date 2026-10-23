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

    def test_terms_lead_to_the_sales_terms_page(self):
        if not self.env['website.page'].search_count([('url', '=', '/termini-e-condizioni')]):
            self.skipTest('No sales terms page in this database')
        response = self.url_open('/terms', allow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.headers['Location'].endswith('/termini-e-condizioni'))
