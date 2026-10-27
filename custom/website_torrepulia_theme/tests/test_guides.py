from odoo.tests import TransactionCase, tagged

from ..models.guides import STORAGE_GUIDE, create_guide


@tagged('post_install', '-at_install')
class TestGuides(TransactionCase):
    """The first guide is written once, unpublished, with links to the formats of this database."""

    def test_storage_guide_is_a_draft_written_once(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        # As before the migration: the module update may already have written the guide here.
        existing = self.env['ir.model.data'].search([('module', '=', 'website_torrepulia_theme'), ('name', '=', STORAGE_GUIDE['xmlid'])])
        self.env['blog.post'].browse(existing.mapped('res_id')).unlink()
        existing.unlink()
        tin = self.env['product.template'].create({
            'name': 'La Regina latta di prova', 'default_code': 'LARGLAT5', 'is_published': True, 'website_id': website.id})
        post = self.env['blog.post'].browse(create_guide(self.env, STORAGE_GUIDE).res_id)
        self.assertEqual(post.name, STORAGE_GUIDE['name'])
        self.assertFalse(post.is_published)
        self.assertEqual(post.website_meta_title, STORAGE_GUIDE['meta_title'])
        self.assertIn('href="%s"' % tin.with_context(website_id=website.id).website_url, post.content)
        self.assertNotIn('__', post.content.replace('__init__', ''))
        self.assertIn('Consiglio Oleicolo Internazionale', post.content)
        # The owner's edits stay: a second run creates nothing and changes nothing.
        post.content = '<p>Testo del gestore</p>'
        create_guide(self.env, STORAGE_GUIDE)
        self.assertEqual(self.env['blog.post'].search_count([('name', '=', STORAGE_GUIDE['name'])]), 1)
        self.assertIn('Testo del gestore', post.content)

    def test_first_meta_is_replaced_unless_edited(self):
        from ..models.guides import FIRST_STORAGE_META, refresh_guide_meta
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        post = self.env['blog.post'].browse(create_guide(self.env, STORAGE_GUIDE).res_id)
        post.write({'website_meta_title': False, 'website_meta_description': 'Scritta dal gestore'})
        refresh_guide_meta(self.env, STORAGE_GUIDE, FIRST_STORAGE_META)
        self.assertEqual(post.website_meta_title, STORAGE_GUIDE['meta_title'])
        self.assertEqual(post.website_meta_description, 'Scritta dal gestore')
        self.assertLessEqual(len(STORAGE_GUIDE['meta_title']), 60)
        self.assertLessEqual(len(STORAGE_GUIDE['meta_description']), 160)

    def test_oil_page_links_the_guide_once_published(self):
        import json
        from ..models.guides import OIL_PAGE_SENTENCE, link_guide_from_oil_page
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        post = self.env['blog.post'].browse(create_guide(self.env, STORAGE_GUIDE).res_id)
        view = self.env['ir.ui.view'].create({'name': 'La Peranzana', 'type': 'qweb', 'arch': '<t t-name="oil"><p>x</p></t>',
                                              'key': 'website_torrepulia_theme.page_oil_view'})
        saved = '<t t-name="oil"><h3>Il confezionamento</h3><p>Da lì lo spediamo a casa tua.</p></t>'
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved}), view.id])
        self.env['ir.ui.view'].invalidate_model(['arch_db'])
        post.is_published = False
        link_guide_from_oil_page(self.env, STORAGE_GUIDE)  # A draft is not linked.
        post.is_published = True
        link_guide_from_oil_page(self.env, STORAGE_GUIDE)
        link_guide_from_oil_page(self.env, STORAGE_GUIDE)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        arch = self.env.cr.fetchone()[0]['en_US']
        self.assertEqual(arch.count('href="%s"' % post.website_url), 1)
        self.assertNotIn(OIL_PAGE_SENTENCE, arch)
        self.assertEqual(website._torrepulia_storage_guide_url(), post.website_url)

    def test_filter_guide_links_the_storage_guide_and_the_reservation(self):
        from ..models.guides import FILTER_GUIDE
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        existing = self.env['ir.model.data'].search([('module', '=', 'website_torrepulia_theme'), ('name', '=', FILTER_GUIDE['xmlid'])])
        self.env['blog.post'].browse(existing.mapped('res_id')).unlink()
        existing.unlink()
        storage = self.env['blog.post'].browse(create_guide(self.env, STORAGE_GUIDE).res_id)
        storage.is_published = True
        post = self.env['blog.post'].browse(create_guide(self.env, FILTER_GUIDE).res_id)
        self.assertFalse(post.is_published)
        self.assertIn('href="%s"' % storage.website_url, post.content)
        self.assertNotIn('__', post.content)
        self.assertIn('Consiglio Oleicolo Internazionale', post.content)
        self.assertLessEqual(len(FILTER_GUIDE['meta_title']), 60)
        self.assertLessEqual(len(FILTER_GUIDE['meta_description']), 160)
