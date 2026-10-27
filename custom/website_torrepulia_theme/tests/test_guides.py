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
