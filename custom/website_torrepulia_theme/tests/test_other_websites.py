from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOtherWebsites(TransactionCase):
    """A new website of the same database may pick any Odoo header or footer, as its configurator does."""

    def _layouts(self, prefix, marker):
        # Layout templates of a family (one is active at a time), not their colour or width options.
        return self.env['ir.ui.view'].with_context(active_test=False).search([
            ('key', '=like', prefix + '%'), ('inherit_id', '=', self.env.ref('website.layout').id),
            ('website_id', '=', False)]).filtered(lambda view: marker in (view.arch_db or ''))

    def test_new_website_accepts_every_header_and_footer_layout(self):
        website = self.env['website'].create({'name': 'Altro sito'})
        Website = self.env['website'].with_context(website_id=website.id)
        for prefix, marker in (('website.template_header_', 'website.navbar'), ('website.template_footer_', 'id="footer"')):
            layouts = self._layouts(prefix, marker)
            self.assertGreater(len(layouts), 1)
            for layout in layouts:
                with self.subTest(template=layout.key), self.env.cr.savepoint():
                    for other in layouts - layout:
                        Website.viewref(other.key).with_context(website_id=website.id).write({'active': False})
                    Website.viewref(layout.key).with_context(website_id=website.id).write({'active': True})
                    self.env['ir.ui.view'].with_context(website_id=website.id)._get_template_view(
                        'website.layout')._get_combined_arch()

    def test_theme_header_and_footer_belong_to_the_torrepulia_site(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        website._torrepulia_scope_navigation()
        for name in website.SITE_ONLY_VIEWS:
            self.assertEqual(self.env.ref('website_torrepulia_theme.' + name).website_id, website)
