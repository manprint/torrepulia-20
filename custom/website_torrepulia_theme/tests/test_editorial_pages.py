import json
import re

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_open

from ..models.editorial_pages import (
    HOME_REPLACEMENTS, HOME_KEY, PAGES, PROCESS_PHOTO, recopy_arch, REPORT_2024, add_process_photo, move_bag_in_box, rebuild_arch, refine_home, refresh_editorial_pages,
    retext_home)

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
HOME_SAVED = (
    '<t t-name="home"><t t-call="website.layout"><div id="wrap" class="oe_structure">'
    '<section data-snippet="s_cinematic_0"><div class="hero-copy"><p><strong>LA NOSTRA TERRA. IL TUO OLIO.</strong></p>'
    '<h1 id="hero-title">Olio extravergine Peranzana</h1><p class="hero-description">Descrizione</p></div></section>'
    '<section data-snippet="s_torrepulia_value_proofs"><h2>100% Olive Aziendali</h2></section>'
    '<section data-snippet="s_cinematic_1"><div class="section-line">Da Torremaggiore alla tua tavola</div>'
    '<div class="regina-copy"><p><strong>Un solo olio.</strong></p><p>Sentori intensi di oliva, erba falciata.</p>'
    '<div class="product-note"><p/></div></div></section>'
    '<section data-snippet="s_cinematic_5"><p class="mc-oil-finale"><span>Dalla nostra terra, alla tua tavola.</span></p></section>'
    '<section data-snippet="s_torrepulia_packaging"><p>Bag in Box</p></section>'
    '<section data-snippet="s_cinematic_3"><div class="mc-peranzana-origin"><p>habitat ideale</p></div>'
    '<div class="mc-sensory-panel"><p class="sensory-title">Foglia di pomodoro.</p><p class="sensory-text">mela verde</p></div>'
    '<div class="mc-sensory-panel"><p class="sensory-title">Armonico.</p><p class="sensory-text">medio-intenso</p></div>'
    '<div class="process section-pad"><div class="process-intro"><p>Filiera corta.</p></div>'
    '<article><span>Ottobre/Novembre</span><h4>Raccolta Precoce</h4><p>polifenoli e antiossidanti</p></article>'
    '<article><span>Entro 6 Ore</span><h4>Molitura a Freddo</h4><p>acidità bassissima</p></article></div></section>'
    '<section data-snippet="s_cinematic_6"><div class="territory-copy"><p>ulivi secolari</p>'
    '<a class="text-link" href="mailto:info@torrepulia.it">Vieni a conoscerci<img class="icon"/></a></div></section>'
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
        # The sensory profile follows the owner's tasting sheet.
        self.assertIn('medio-intenso, elegante e armonico', rebuilt)
        self.assertNotIn('grano appena tagliati', rebuilt)
        self.assertNotIn('lattuga', rebuilt)
        self.assertIn('Sezione aggiunta dal gestore', rebuilt)
        # The analysis is read from the backend: no harvest figures saved in the page.
        self.assertIn('tp-analysis-content', rebuilt)
        self.assertNotIn('tp-analysis-value', rebuilt)
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
        self.assertIn('oltre 1.500 piante', rebuilt)
        self.assertIn('Franco e Salvatore Leone', rebuilt)
        self.assertEqual(sections(rebuilt)[-1], 's_torrepulia_choice_family')
        self.assertEqual(sections(rebuilt)[2], 's_torrepulia_roots_trees')
        self.assertIn('sapere contadino', rebuilt)
        self.assertNotIn('magazzino', rebuilt)
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
        self.assertIn("analisi dell'olio", view.website_meta_description)
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
        # The last pair rewrites the 20.0.3.13.0 family sentence: every chain ends on the newest text.
        for _old, new in HOME_REPLACEMENTS[:-2] + HOME_REPLACEMENTS[-1:]:
            self.assertIn(new, aligned)
        self.assertNotIn('alcuni già', aligned)
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

    def test_home_facts_bag_in_box_line_and_tasting_sheet(self):
        refined = refine_home(self.env, HOME_SAVED, '/shop/bag-in-box-5-l#come-funziona')
        self.assertEqual(sections(refined), [
            's_cinematic_0', 's_torrepulia_home_facts', 's_cinematic_1', 's_cinematic_5', 's_torrepulia_bib_line',
            's_cinematic_3', 's_cinematic_6'])
        for gone in ('Da Torremaggiore alla tua tavola', 'Dalla nostra terra', 'product-note',
                     'Foglia di pomodoro', 'mela', 'grano appena tagliati', 'frantoio partner', 'Entro 6', 'antiossidanti', 'habitat ideale',
                     'mailto:', '100% Olive'):
            self.assertNotIn(gone, refined)
        for kept in ('LA NOSTRA TERRA. IL TUO OLIO.', 'Olio extravergine Peranzana', 'Entro 8 ore', 'elegante e armonico', 'frantoio di fiducia',
                     'href="/shop/bag-in-box-5-l#come-funziona"', 'href="/territorio"', 'dai secolari del nonno', 'Il formato che consigliamo', 'Dal 1945'):
            self.assertIn(kept, refined)
        self.assertIsNone(UNDOCUMENTED.search(refined))
        self.assertEqual(refine_home(self.env, refined, '/shop/bag-in-box-5-l#come-funziona'), refined)

    def test_process_photo_is_added_once_and_keeps_the_owner_steps(self):
        saved = ('<t t-name="oil"><div id="wrap"><section data-snippet="s_torrepulia_production_process">'
                 '<div class="tp-process-intro"><h2>Raccogliamo</h2></div>'
                 '<ol><li><img src="/web/image/912"/><h3>La raccolta</h3></li></ol></section></div></t>')
        photo = etree.fromstring(self.env.ref('website_torrepulia_theme.s_torrepulia_production_process').arch_db).xpath(PROCESS_PHOTO)[0]
        updated = add_process_photo(saved, photo)
        self.assertIn('raccolta-reti-1280.webp', updated)
        self.assertIn('/web/image/912', updated)
        self.assertEqual(add_process_photo(updated, photo), updated)

    def test_copy_2510_rewrites_only_the_owner_words(self):
        home = recopy_arch(HOME_SAVED, HOME_KEY)
        for gone in ('Un solo olio', 'frantoio partner', 'Armonico.'):
            self.assertNotIn(gone, home)
        for kept in ('Il carattere della nostra terra.', 'Morbido.', 'medio-intenso', 'LA NOSTRA TERRA. IL TUO OLIO.'):
            self.assertIn(kept, home)
        self.assertEqual(recopy_arch(home, HOME_KEY), home)
        oil = ('<t t-name="oil"><div id="wrap"><section data-snippet="s_torrepulia_sensory"><p class="lead">Vecchio</p>'
               '<dl><dt>Alla vista</dt><dd>Verde del gestore</dd><dt>Al profumo</dt><dd>erba e grano appena tagliati</dd></dl>'
               '</section><section data-snippet="s_torrepulia_production_process"><ol>'
               '<li><img src="/web/image/912"/><div><h3>La raccolta</h3><p>cogliamo</p></div></li>'
               '<li><div><h3>La molitura</h3><p>nel nostro frantoio partner</p></div></li></ol></section></div></t>')
        oil = recopy_arch(oil, OIL_KEY)
        for gone in ('grano appena tagliati', '<p>cogliamo</p>', 'frantoio partner', 'Vecchio'):
            self.assertNotIn(gone, oil)
        for kept in ('Verde del gestore', '/web/image/912', 'ricca di polifenoli', 'frantoio di fiducia'):
            self.assertIn(kept, oil)

    def test_la_peranzana_shows_only_a_recent_analysis(self):
        Profile = self.env['torrepulia.oil.profile']
        Profile.search([]).unlink()
        season = Profile._torrepulia_season()
        Profile.create({'name': 'Vecchio', 'harvest_year': season - 2, 'acidity': 0.17})
        Profile.create({'name': 'Senza analisi', 'harvest_year': season - 1, 'cultivar': 'Peranzana'})
        self.assertFalse(Profile._torrepulia_published_analysis())
        coming = str(self.env['ir.ui.view']._render_template(
            'website_torrepulia_theme.oil_analysis_content', {'profile': Profile.browse(), 'season': season}))
        self.assertIn('Le analisi del raccolto %s.' % season, coming)
        new = Profile.create({'name': 'Nuovo', 'harvest_year': season, 'acidity': 0.2, 'polyphenols': 600,
                              'analysis_note': 'Analisi rapida in frantoio.'})
        self.assertEqual(Profile._torrepulia_published_analysis(), new)
        shown = str(self.env['ir.ui.view']._render_template(
            'website_torrepulia_theme.oil_analysis_content', {'profile': new, 'season': season}))
        for kept in ('Le analisi del raccolto %s.' % season, 'Polifenoli totali', 'Analisi rapida in frantoio.'):
            self.assertIn(kept, shown)
