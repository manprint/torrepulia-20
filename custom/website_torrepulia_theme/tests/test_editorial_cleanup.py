import json

from odoo.tests import TransactionCase, tagged

from ..models.editorial_cleanup import HOME_KEY, clean_arch, cleanup_home

SAVED = ('<t t-name="home"><section data-snippet="s_torrepulia_value_proofs"><div class="tp-value-item">'
         '<h3>100% Olive Aziendali</h3></div></section><section class="family"><h3>Resta h3</h3>'
         '<p>con la stessa passione e&amp;nbsp;dedizione di papà Michele.&amp;nbsp; Siamo cresciuti'
         ' tra le olive appena frante.  Oggi &amp;nbsp;noi, direttamente sulla tua tavola..</p>'
         '<img class="img o_anim_rotate_in o_animate o_animate_on_scroll" style="--wanim-intensity: 23; animation-name: dummy;"/>'
         '</section></t>')


@tagged('post_install', '-at_install')
class TestEditorialCleanup(TransactionCase):
    def test_clean_arch_targets_only_known_defects(self):
        cleaned = clean_arch(SAVED)
        self.assertNotIn('&amp;nbsp;', cleaned)
        self.assertIn('e dedizione di papà Michele. Siamo', cleaned)
        self.assertIn('frante. Oggi noi', cleaned)
        self.assertIn('sulla tua tavola.</p>', cleaned)
        self.assertNotIn('o_anim', cleaned)
        self.assertNotIn('wanim', cleaned)
        self.assertIn('<h2>100% Olive Aziendali</h2>', cleaned)
        self.assertIn('<h3>Resta h3</h3>', cleaned)
        self.assertEqual(clean_arch(cleaned), cleaned)

    def test_every_language_is_cleaned_once_with_backup(self):
        view = self.env['ir.ui.view'].create({'name': 'Cleanup home', 'type': 'qweb', 'key': HOME_KEY,
                                              'arch': '<t t-name="home"><p>Prima</p></t>'})
        edited = SAVED.replace('Resta h3', 'Testo del gestore')
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s',
                            [json.dumps({'en_US': SAVED, 'it_IT': edited}), view.id])
        view.invalidate_recordset()
        cleanup_home(self.env)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = self.env.cr.fetchone()[0]
        self.assertEqual(stored, {'en_US': clean_arch(SAVED), 'it_IT': clean_arch(edited)})
        backups = self.env['ir.ui.view'].with_context(active_test=False).search(
            [('key', '=like', 'website_torrepulia_theme.before_editorial_cleanup_%s_%%' % view.id)])
        self.assertEqual(len(backups), 1)
        self.assertFalse(backups.active)
        cleanup_home(self.env)
        self.assertEqual(self.env['ir.ui.view'].with_context(active_test=False).search_count(
            [('key', '=like', 'website_torrepulia_theme.before_editorial_cleanup_%s_%%' % view.id)]), 1)
