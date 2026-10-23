import json
import re

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_open

from ..models.editorial_pages import (
    HOME_REPLACEMENTS, PAGES, REPORT_2024, move_bag_in_box, rebuild_arch, refresh_editorial_pages, retext_home)

OIL_KEY, STORY_KEY, LAND_KEY = list(PAGES)
OIL_SAVED = ('<t t-name="oil"><t t-call="website.layout"><div id="wrap" class="oe_structure">'
             '<section data-snippet="s_torrepulia_cultivar_opening"><h1>Vecchio</h1></section>'
             '<section data-snippet="s_torrepulia_cultivar_history"><p>Luoghi</p></section>'
             '<section data-snippet="s_torrepulia_production_process"><p>Card 01</p></section>'
             '<section data-snippet="s_torrepulia_sensory"><p>Profilo del gestore</p></section>'
             '<section data-snippet="s_text_block"><p>Sezione aggiunta dal gestore</p></section>'
             '<section data-snippet="s_torrepulia_pairings"><p>Abbinamenti</p></section>'
             '<section data-snippet="s_torrepulia_packaging"><p>Bag in Box</p></section>'
             '<section data-snippet="s_torrepulia_roots_cta"><p>Shop</p></section>'
             '</div></t></t>')
STORY_SAVED = ('<t t-name="story"><t t-call="website.layout"><div id="wrap" class="oe_structure">'
               '<section data-snippet="s_torrepulia_story_opening"><div><h1>La terra si coltiva.</h1>'
               '<p class="tp-about-subtitle">Vecchio</p><figure><img src="/web/image/781"/></figure></div></section>'
               '<section data-snippet="s_torrepulia_story_chapters"><p>testimone secolare</p></section>'
               '<section data-snippet="s_torrepulia_roots_transition"><p>vendemmie</p></section>'
               '<section data-snippet="s_torrepulia_roots_values"><p>Filiera Corta Certificata</p></section>'
               '<section data-snippet="s_torrepulia_roots_cta"><p>Shop</p></section>'
               '</div></t></t>')
LAND_SAVED = ('<t t-name="land"><t t-call="website.layout"><div id="wrap" class="oe_structure">'
              '<section data-snippet="s_torrepulia_landscape"><h1>Orizzonte</h1></section>'
              '<section data-snippet="s_torrepulia_land_story"><p>Terreni drenanti</p></section>'
              '<section data-snippet="s_torrepulia_brand_story"><p>la più antica tradizione familiare</p></section>'
              '<section data-snippet="s_torrepulia_cta"><p>Acquista il nostro olio</p></section>'
              '</div></t></t>')
# Claims the owner cannot document, and the errors found in the 23/10 critique.
# Centuries-old trees are real; a centuries-old family story is not (it starts in 1945).
UNDOCUMENTED = re.compile(r'(?i)certificat|testimone secolare|benefic|salute|sostenibil|vendemmi|nonno Vincenzo|Sacco')


def sections(arch):
    return [section.get('data-snippet') for section in etree.fromstring(arch).iter('section')]


@tagged('post_install', '-at_install')
class TestEditorialPages(TransactionCase):
    def test_oil_page_gets_analysis_and_choice_without_bag_in_box(self):
        rebuilt = rebuild_arch(self.env, OIL_SAVED, PAGES[OIL_KEY])
        self.assertEqual(sections(rebuilt), [
            's_torrepulia_cultivar_opening', 's_torrepulia_cultivar_history', 's_torrepulia_production_process',
            's_torrepulia_oil_analysis', 's_torrepulia_sensory', 's_text_block', 's_torrepulia_pairings',
            's_torrepulia_choice_oil'])
        self.assertIn('Profilo del gestore', rebuilt)
        self.assertIn('Sezione aggiunta dal gestore', rebuilt)
        self.assertIn(REPORT_2024, rebuilt)
        self.assertIn('Rapporto di prova del frantoio', rebuilt)
        # The home map is inlined: a t-call would take the section away from the Builder.
        self.assertIn('mc-puglia-map', rebuilt)
        self.assertNotIn('t-call="website_torrepulia_theme', rebuilt)
        self.assertIn('Ordina dalle scorte', rebuilt)
        self.assertIn('/prenotailtuoolio', rebuilt)
        self.assertIsNone(UNDOCUMENTED.search(rebuilt))
        self.assertEqual(rebuild_arch(self.env, rebuilt, PAGES[OIL_KEY]), rebuilt)

    def test_family_page_keeps_owner_photo_and_drops_undocumented_claims(self):
        rebuilt = rebuild_arch(self.env, STORY_SAVED, PAGES[STORY_KEY])
        self.assertIn('/web/image/781', rebuilt)
        self.assertNotIn('La terra si coltiva', rebuilt)
        self.assertIn('Papà Michele sul trattore e nonno Santino Vincenzo.', rebuilt)
        self.assertIn('oltre 1000 piante', rebuilt)
        self.assertIn('Franco e Salvatore Leone', rebuilt)
        self.assertEqual(sections(rebuilt)[-1], 's_torrepulia_choice_family')
        self.assertEqual(sections(rebuilt)[2], 's_torrepulia_roots_trees')
        self.assertIn('alcuni già secolari', rebuilt)
        self.assertIn('<dt>Curiamo</dt>', rebuilt)
        self.assertIsNone(UNDOCUMENTED.search(rebuilt))
        self.assertEqual(rebuild_arch(self.env, rebuilt, PAGES[STORY_KEY]), rebuilt)

    def test_family_quote_placeholders_never_reach_visitors(self):
        for arch in (rebuild_arch(self.env, OIL_SAVED, PAGES[OIL_KEY]),
                     rebuild_arch(self.env, STORY_SAVED, PAGES[STORY_KEY])):
            placeholders = etree.fromstring(arch).xpath("//*[contains(@class, 'tp-placeholder')]")
            self.assertTrue(placeholders)
            for node in placeholders:
                self.assertIn('d-none', node.get('class').split())
                self.assertIn('SEGNAPOSTO', ''.join(node.itertext()))

    def test_every_language_is_rebuilt_once_with_backup(self):
        view = self.env['ir.ui.view'].create({
            'name': 'Oil page', 'type': 'qweb', 'key': OIL_KEY, 'arch': '<t t-name="oil"><p>Prima</p></t>',
            'website_meta_description': 'Scopri la Peranzana, il processo produttivo di La Regina.'})
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s',
                            [json.dumps({'en_US': OIL_SAVED, 'it_IT': OIL_SAVED}), view.id])
        view.invalidate_recordset()
        refresh_editorial_pages(self.env)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = self.env.cr.fetchone()[0]
        self.assertEqual(set(stored), {'en_US', 'it_IT'})
        self.assertTrue(all('s_torrepulia_oil_analysis' in arch for arch in stored.values()))
        self.assertIn('analisi del raccolto 2024', view.website_meta_description)
        backup = [('key', '=like', 'website_torrepulia_theme.before_editorial_pages_%s_%%' % view.id)]
        Views = self.env['ir.ui.view'].with_context(active_test=False)
        self.assertEqual(Views.search_count(backup), 1)
        refresh_editorial_pages(self.env)
        self.assertEqual(Views.search_count(backup), 1)

    def test_bag_in_box_explainer_moves_to_its_product_page(self):
        box, tin = self.env['product.template'].create([
            {'name': 'Bag in Box di prova', 'torrepulia_format_name': 'Bag in Box 5 L'},
            {'name': 'Latta di prova', 'torrepulia_format_name': 'Latta 5 L'}])
        move_bag_in_box(self.env)
        self.assertIn('tp-bib', box.website_description)
        self.assertNotIn('tp-bib-cta', box.website_description)
        self.assertNotIn('tp-bib', tin.website_description or '')

    def test_test_report_is_published_whole(self):
        with file_open(REPORT_2024.lstrip('/'), 'rb') as report:
            self.assertEqual(report.read(5), b'%PDF-')

    def test_home_family_matches_la_famiglia(self):
        saved = ''.join(old for old, _new in HOME_REPLACEMENTS)
        aligned = retext_home(saved)
        for _old, new in HOME_REPLACEMENTS:
            self.assertIn(new, aligned)
        self.assertNotIn('Santino e Michele.', aligned)
        self.assertNotIn('tecnologie di conservazione', aligned)
        self.assertIn('nonno Santino Vincenzo', aligned)
        self.assertEqual(retext_home(aligned), aligned)
        self.assertEqual(retext_home('<p>Testo riscritto dal gestore</p>'), '<p>Testo riscritto dal gestore</p>')

    def test_land_page_tells_the_place_not_the_family_again(self):
        rebuilt = rebuild_arch(self.env, LAND_SAVED, PAGES[LAND_KEY])
        self.assertEqual(sections(rebuilt), [
            's_torrepulia_landscape', 's_torrepulia_land_story', 's_torrepulia_land_history',
            's_torrepulia_land_grove', 's_torrepulia_choice_land'])
        self.assertIn('30 gennaio 1710', rebuilt)
        self.assertIn('mc-puglia-map', rebuilt)
        self.assertNotIn('antica tradizione', rebuilt)
        self.assertNotIn('drenanti', rebuilt)
        self.assertIn('Ordina dalle scorte', rebuilt)
        self.assertIsNone(UNDOCUMENTED.search(rebuilt))
        self.assertEqual(rebuild_arch(self.env, rebuilt, PAGES[LAND_KEY]), rebuilt)
