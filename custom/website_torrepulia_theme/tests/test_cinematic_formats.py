from unittest.mock import patch

from lxml import html

from odoo.tests import TransactionCase, tagged
from odoo.addons.website_sale.tests.common import MockRequest

from ..controllers.main import TorrepuliaPrivacy


@tagged('post_install', '-at_install')
class TestCinematicFormats(TransactionCase):
    """Exercise the actual controller, native combination API and rendered controls."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.website.torrepulia_theme_enabled = True
        cls.env = cls.env(context=dict(cls.env.context, website_id=cls.website.id))
        cls.product = cls.env['product.template'].create({
            'name': 'QA format', 'is_published': True, 'sale_ok': True,
            'website_id': cls.website.id, 'list_price': 20,
            'is_storable': True, 'allow_out_of_stock_order': False,
            'torrepulia_format_name': 'QA format',
            'show_availability': True, 'available_threshold': 5,
        })

    def render_format(self, quantity, cart_quantity=0, product=None):
        product = product or self.product
        with (
            MockRequest(self.env, website=self.website),
            patch.object(type(self.website), '_get_product_available_qty', return_value=quantity),
            patch.object(type(self.env['sale.order']), '_get_cart_qty', return_value=cart_quantity),
        ):
            result = TorrepuliaPrivacy().formats(ids=product.ids)
        return html.fromstring(result['html'])

    def test_sold_out_disables_purchase_but_keeps_product_details(self):
        self.product.out_of_stock_message = '<p>Ritorna presto</p>'
        tree = self.render_format(0)
        self.assertEqual(len(tree.xpath('//*[@disabled][contains(@class, "format-link")]')), 1)
        self.assertFalse(tree.xpath('//a[contains(@class, "format-link")]'))
        self.assertIn('Ritorna presto', tree.xpath('//*[contains(@class, "format-option")]')[0].text_content())
        self.assertIn('Ritorna presto', tree.xpath('//*[contains(@class, "mc-format-stock-message")]')[0].text_content())
        self.assertEqual(tree.xpath('//*[contains(@class, "mc-format-details-link")]')[0].get('href'), self.product.website_url)
        self.assertFalse(tree.xpath('//*[@disabled][contains(@class, "format-option")]'))

    def test_sell_when_out_of_stock_keeps_purchase(self):
        self.product.allow_out_of_stock_order = True
        self.product.out_of_stock_message = '<p>Messaggio configurato</p>'
        tree = self.render_format(0)
        self.assertFalse(tree.xpath('//*[@disabled][contains(@class, "format-link")]'))
        self.assertEqual(tree.xpath('//a[contains(@class, "format-link")]')[0].get('href'), self.product.website_url)
        self.assertIn('Messaggio configurato', tree.text_content())

    def test_quantity_visibility_threshold_and_cart(self):
        tree = self.render_format(5, cart_quantity=2)
        self.assertIn('Disponibili: 3', tree.text_content())
        self.assertIn('2 nel carrello', tree.text_content())
        self.assertTrue(self.render_format(3, cart_quantity=3).xpath('//*[@disabled][contains(@class, "format-link")]'))
        self.assertNotIn('Disponibili:', self.render_format(6).text_content())
        self.product.show_availability = False
        self.assertNotIn('Disponibili:', self.render_format(3).text_content())

    def test_untracked_product_is_not_blocked(self):
        self.product.is_storable = False
        tree = self.render_format(0)
        self.assertFalse(tree.xpath('//*[@disabled][contains(@class, "format-link")]'))
        self.assertNotIn('Esaurito', tree.text_content())

    def test_native_ribbon_in_row_and_preview(self):
        ribbon = self.env['product.ribbon'].create({'name': 'QA ribbon', 'assign': 'manual'})
        self.product.website_ribbon_id = ribbon
        tree = self.render_format(4)
        self.assertEqual(tree.xpath('//*[contains(@class, "mc-format-ribbon")]')[0].text_content(), ribbon.name)
        self.assertEqual(tree.xpath('//*[contains(@class, "o_ribbons")]')[0].text_content(), ribbon.name)

    def test_multiple_configured_badges_order_color_and_escaping(self):
        tags = self.env['product.tag'].create([
            {'name': 'QA badge first', 'color': '#ffffff', 'sequence': 1},
            {'name': 'QA badge <strong>second</strong>', 'color': '#203b2f', 'sequence': 2},
        ])
        self.product.torrepulia_format_badge_ids = tags
        tree = self.render_format(0)
        badges = tree.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " mc-format-badge ")]')
        self.assertEqual([badge.text_content() for badge in badges], tags.mapped('name'))
        self.assertIn('color: #000000', badges[0].get('style'))
        self.assertIn('color: #ffffff', badges[1].get('style'))
        self.assertFalse(badges[1].xpath('.//strong'))
        self.assertTrue(tree.xpath('//*[@disabled][contains(@class, "format-link")]'))
        self.assertFalse(self.product.product_tag_ids, 'Badge assignment must not modify shop tags')

    def test_badges_hidden_and_other_website_are_not_exposed_to_public(self):
        other = self.website.copy({'name': 'QA other badge website'})
        tags = self.env['product.tag'].create([
            {'name': 'QA public badge', 'website_id': self.website.id},
            {'name': 'QA internal badge', 'visible_to_customers': False},
            {'name': 'QA other site badge', 'website_id': other.id},
        ])
        self.product.torrepulia_format_badge_ids = tags
        public_env = self.env(user=self.website.user_id)
        with (
            MockRequest(public_env, website=self.website.with_env(public_env)),
            patch.object(type(self.website), '_get_product_available_qty', return_value=0),
        ):
            tree = html.fromstring(TorrepuliaPrivacy().formats(ids=self.product.ids)['html'])
        self.assertIn('QA public badge', tree.text_content())
        self.assertNotIn('QA internal badge', tree.text_content())
        self.assertNotIn('QA other site badge', tree.text_content())

    def test_badge_color_validation_and_empty_state(self):
        self.assertFalse(self.render_format(3).xpath('//*[contains(@class, "mc-format-badges")]'))
        tags = self.env['product.tag'].create([
            {'name': 'QA short color', 'color': '#abc'},
            {'name': 'QA invalid color', 'color': 'red;position:fixed'},
            {'name': 'QA golden color', 'color': '#d4af37'},
        ])
        self.product.torrepulia_format_badge_ids = tags
        badges = self.product._torrepulia_format_badges(self.website)
        self.assertEqual(badges[0]['color'], '#aabbcc')
        self.assertEqual(badges[1]['color'], '#294d3b')
        self.assertEqual(badges[2]['text_color'], '#000000')

    def test_automatic_out_of_stock_ribbon_respects_sell_flag(self):
        ribbon = self.env['product.ribbon'].search([('assign', '=', 'out_of_stock')], limit=1)
        if not ribbon:
            ribbon = self.env['product.ribbon'].create({'name': 'QA exhausted', 'assign': 'out_of_stock'})
        ribbon.sequence = -100
        tree = self.render_format(0)
        self.assertEqual(tree.xpath('//*[contains(@class, "mc-format-ribbon")]')[0].text_content(), ribbon.name)
        self.product.allow_out_of_stock_order = True
        self.assertNotIn(ribbon.name, self.render_format(0).text_content())

    def test_four_formats_keep_independent_purchase_states(self):
        products = self.product
        for index in range(3):
            products |= self.product.copy({
                'name': 'QA format %s' % index,
                'torrepulia_format_name': 'QA format %s' % index,
                'is_published': True,
            })
        products[-1].allow_out_of_stock_order = True
        with (
            MockRequest(self.env, website=self.website),
            patch.object(type(self.website), '_get_product_available_qty', return_value=0),
            patch.object(type(self.env['sale.order']), '_get_cart_qty', return_value=0),
        ):
            tree = html.fromstring(TorrepuliaPrivacy().formats(ids=products.ids)['html'])
        self.assertEqual(len(tree.xpath('//button[contains(@class, "format-option")]')), 4)
        self.assertEqual(len(tree.xpath('//*[@disabled][contains(@class, "format-link")]')), 3)
        self.assertEqual(tree.xpath('//a[contains(@class, "format-link")]/@href'), [products[-1].website_url])

    def test_other_website_product_is_not_exposed(self):
        other = self.website.copy({'name': 'QA other website'})
        self.product.website_id = other
        tree = self.render_format(0)
        self.assertFalse(tree.xpath('//*[contains(@class, "format-option")]'))

    def test_mixed_variant_stock_keeps_configurator_reachable(self):
        attribute = self.env['product.attribute'].create({
            'name': 'QA variant',
            'value_ids': [(0, 0, {'name': 'First'}), (0, 0, {'name': 'Second'})],
        })
        self.product.attribute_line_ids = [(0, 0, {
            'attribute_id': attribute.id, 'value_ids': [(6, 0, attribute.value_ids.ids)],
        })]
        self.assertEqual(self.product.product_variant_count, 2)
        available_variant = self.product.product_variant_ids[-1]
        with (
            MockRequest(self.env, website=self.website),
            patch.object(type(self.website), '_get_product_available_qty',
                         lambda website, product, **kw: 3 if product == available_variant else 0),
        ):
            tree = html.fromstring(TorrepuliaPrivacy().formats(ids=self.product.ids)['html'])
        self.assertFalse(tree.xpath('//*[@disabled][contains(@class, "format-link")]'))
        self.assertTrue(tree.xpath('//a[contains(@class, "format-link")]'))
        self.assertNotIn('Disponibili:', tree.text_content())
