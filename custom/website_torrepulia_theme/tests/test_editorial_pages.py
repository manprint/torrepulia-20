import json
import re

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools import file_open

from ..models.editorial_pages import (
    HARVEST_MEDIA, add_harvest_media, chapter_photos, original_oil_colours, six_hour_milling, six_hours, snippet_section,
    HOME_REPLACEMENTS, HOME_KEY, PAGES, PROCESS_PHOTO, recopy_arch, REPORT_2024, add_process_photo, move_bag_in_box, rebuild_arch, refine_home, refresh_editorial_pages,
    COOKIE_DESCRIPTION, COOKIE_DESCRIPTION_OLD, PRIVACY_DESCRIPTION, PRIVACY_DESCRIPTION_OLD, REFUND_CLAUSE, add_portrait_hero,
    recopy_cookie_policy, recopy_privacy_policy, retext_aroma, retext_home, retext_refund_clause)

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
                     'Foglia di pomodoro', 'mela', 'grano appena tagliati', 'frantoio partner', 'Entro 6 Ore', 'antiossidanti', 'habitat ideale',
                     'mailto:', '100% Olive'):
            self.assertNotIn(gone, refined)
        for kept in ('LA NOSTRA TERRA. IL TUO OLIO.', 'Olio extravergine Peranzana', 'Entro 6 ore', 'elegante e armonico', 'frantoio di fiducia',
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
        self.assertIn('raccolta-michele-poster.webp', updated)
        self.assertIn('/web/image/912', updated)
        self.assertEqual(add_process_photo(updated, photo), updated)

    def test_harvest_media_replaces_only_theme_photos_and_adds_the_family_once(self):
        fresh = {}
        for name, path, marker, new in HARVEST_MEDIA:
            fresh[(name, path, marker)] = next(node for node in snippet_section(self.env, name).xpath(path) if new in node.get('src'))
        static = '/website_torrepulia_theme/static/src/cinematic/'
        oil = ('<t t-name="oil"><div id="wrap">'
               '<section data-snippet="s_torrepulia_cultivar_opening"><img class="img tp-oil-photo" src="/web/image/5-gestore"/></section>'
               '<section data-snippet="s_torrepulia_production_process"><div class="tp-process-intro">'
               '<img class="img img-fluid tp-process-photo" src="%sowner/raccolta-reti-1280.webp"/></div><ol>'
               '<li class="tp-process-step"><img src="%sowner/process-harvest.webp"/><div><h3>La raccolta</h3></div></li>'
               '<li class="tp-process-step"><img src="/web/image/912"/><div><h3>Le cassette forate</h3></div></li>'
               '<li class="tp-process-step"><img src="%sowner/process-mill.webp"/><div><h3>La molitura</h3></div></li>'
               '</ol></section></div></t>') % (static, static, static)
        updated = add_harvest_media(oil, fresh)
        for expected in ('clips/raccolta-michele-poster.webp', 'clips/olio-frantoio-poster.webp', 'olive-cassone-1280.webp', '/web/image/912', '/web/image/5-gestore'):
            self.assertIn(expected, updated)
        for gone in ('raccolta-reti', 'process-mill', 'process-harvest'):
            self.assertNotIn(gone, updated)
        self.assertEqual(add_harvest_media(updated, fresh), updated)
        theme_opening = oil.replace('/web/image/5-gestore', static + 'campaign/olive-1280.webp')
        self.assertIn('chioma-carica-1280.webp', add_harvest_media(theme_opening, fresh))
        chapters = chapter_photos(self.env)
        story = ('<t t-name="story"><div id="wrap"><section data-snippet="s_torrepulia_story_chapters"><div class="tp-about-grid">'
                 '<article><p class="tp-about-year">1945</p><p>Capitolo del gestore</p></article>'
                 '<article><p class="tp-about-year">2020</p><p>Noi</p></article></div></section></div></t>')
        story = add_harvest_media(story, {}, chapters)
        self.assertEqual(story.count('tp-about-chapter-photo'), 2)
        self.assertLess(story.index('ulivo-secolare-bn-960.webp'), story.index('1945'))
        self.assertIn('franco-raccolta-960.webp', story)
        self.assertIn('Capitolo del gestore', story)
        self.assertEqual(add_harvest_media(story, {}, chapters), story)

    def test_milling_within_six_hours_everywhere_but_the_backups(self):
        self.assertEqual(six_hours('<strong>Entro 8 ore</strong> e si macinano entro 8 ore; spedito entro 48 ore'),
                         '<strong>Entro 6 ore</strong> e si macinano entro 6 ore; spedito entro 48 ore')
        arch = '<t t-name="x"><div><p>Moliamo entro 8 ore dalla raccolta.</p></div></t>'
        live = self.env['ir.ui.view'].create({'name': 'live', 'type': 'qweb', 'arch': arch})
        backup = self.env['ir.ui.view'].create({'name': 'backup', 'type': 'qweb', 'arch': arch, 'active': False})
        website = self.env['website'].search([], limit=1)
        website.llms_txt = '- la moliamo entro 8 ore dalla raccolta'
        six_hour_milling(self.env)
        self.assertIn('entro 6 ore', live.arch_db)
        self.assertIn('entro 8 ore', backup.arch_db)
        self.assertEqual(website.llms_txt, '- la moliamo entro 6 ore dalla raccolta')

    def test_the_oil_goes_back_to_its_original_colours(self):
        arch = ('<t t-name="x"><div><img src="/website_torrepulia_theme/static/src/cinematic/clips/olio-verde-poster.webp" data-tp-clip="olio-verde"/>'
                '<img src="/website_torrepulia_theme/static/src/cinematic/owner/process-bottling-verde-480.webp"/><img src="/web/image/7-verde"/></div></t>')
        live = self.env['ir.ui.view'].create({'name': 'live', 'type': 'qweb', 'arch': arch})
        original_oil_colours(self.env)
        for gone in ('olio-verde', 'bottling-verde'):
            self.assertNotIn(gone, live.arch_db)
        for kept in ('clips/olio-frantoio-poster.webp', 'data-tp-clip="olio-frantoio"', 'owner/process-bottling-480.webp', '/web/image/7-verde'):
            self.assertIn(kept, live.arch_db)

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

    def test_aroma_drops_the_fresh_olive_once(self):
        view = self.env['ir.ui.view'].create({'name': 'Aroma', 'type': 'qweb', 'key': 'website_torrepulia_theme.test_aroma',
                                              'arch': '<t t-name="aroma"><p>x</p></t>'})
        saved = ('<t t-name="aroma"><p>Al naso un fruttato medio-intenso di oliva appena colta: prima il verde.</p>'
                 '<dd>Oliva appena colta: prima il verde del <strong>pomodoro</strong>.</dd></t>')
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved}), view.id])
        retext_aroma(self.env)
        retext_aroma(self.env)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        arch = self.env.cr.fetchone()[0]['en_US']
        self.assertNotIn('appena colta', arch)
        self.assertIn('Al naso un fruttato medio-intenso: prima il verde.', arch)
        self.assertIn('<dd>Prima il verde del <strong>pomodoro</strong>.</dd>', arch)
        backups = self.env['ir.ui.view'].with_context(active_test=False).search_count(
            [('key', '=like', 'website_torrepulia_theme.before_aroma_%s_%%' % view.id)])
        self.assertEqual(backups, 1)

    def test_phones_get_the_portrait_hero_once(self):
        view = self.env['ir.ui.view'].create({'name': 'Hero', 'type': 'qweb', 'key': 'website_torrepulia_theme.test_hero',
                                              'arch': '<t t-name="hero"><p>x</p></t>'})
        photo = '/website_torrepulia_theme/static/src/cinematic/images/hero-foglie-'
        saved = ('<t t-name="hero"><section class="hero"><picture><source srcset="%(p)s640.webp 640w, %(p)s1920.webp 1920w" '
                 'sizes="(max-width: 760px) 1650px, 100vw"><img class="hero-photo" src="%(p)s1920.webp"/></source></picture></section></t>'
                 % {'p': photo})
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved, 'it_IT': saved}), view.id])
        add_portrait_hero(self.env)
        add_portrait_hero(self.env)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        for arch in self.env.cr.fetchone()[0].values():
            picture = etree.fromstring(arch).find('.//picture')
            sources = picture.xpath('.//source')
            self.assertEqual([source.get('srcset') for source in sources[:2]],
                             [photo + 'portrait-648.webp', photo + 'portrait-1080.webp'])
            self.assertEqual(len(sources), 3)
            self.assertTrue(sources[0].get('media').startswith('(max-width: 760px)'))
        backups = self.env['ir.ui.view'].with_context(active_test=False).search_count(
            [('key', '=like', 'website_torrepulia_theme.before_portrait_hero_%s_%%' % view.id)])
        self.assertEqual(backups, 1)

    def test_cookie_policy_lists_the_real_cookies_once(self):
        website = self.env['website'].search([], limit=1)
        saved = ('<t t-name="cookies"><t t-call="website.layout"><div id="wrap" class="oe_structure tp-page">'
                 '<section class="tp-section tp-legal" data-snippet="s_text_block"><div class="container tp-reading">'
                 '<h1>Cookie Policy</h1><section><p>Apri Internet Explorer</p></section></div></section>'
                 '<section data-snippet="s_text_block"><p>Nota del gestore</p></section></div></t></t>')
        # The website points at its cookie page (cookie_policy_id): reuse it when it exists.
        page = self.env['website.page'].search([('url', '=', '/cookie-policy')], limit=1)
        if not page:
            view = self.env['ir.ui.view'].create({'name': 'Cookie', 'type': 'qweb', 'arch': '<t t-name="cookies"><p>x</p></t>',
                                                  'key': 'website_torrepulia_theme.test_cookies', 'website_id': website.id})
            page = self.env['website.page'].create({'url': '/cookie-policy', 'view_id': view.id, 'website_id': website.id})
        self.env['website.page'].search([('url', '=', '/cookie-policy'), ('id', '!=', page.id)]).url = '/cookie-policy-altra'
        view = page.view_id
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved}), view.id])
        view.invalidate_recordset(['arch_db'])
        view.website_meta_description = COOKIE_DESCRIPTION_OLD
        Views = self.env['ir.ui.view'].with_context(active_test=False)
        backup_key = [('key', '=like', 'website_torrepulia_theme.before_cookie_policy_%s_%%' % view.id)]
        before = Views.search_count(backup_key)  # The module update may already have migrated this page.
        recopy_cookie_policy(self.env)
        recopy_cookie_policy(self.env)  # The new text has no Internet Explorer: nothing more to do.
        arch = view.arch
        self.assertNotIn('Internet Explorer', arch)
        for kept in ('<h1>Cookie Policy</h1>', 'Nota del gestore', '_ga_XXXXXXXXXX', '_fbp', 'website_cookies_bar',
                     'Preferenze cookie', 'Data Privacy Framework'):
            self.assertIn(kept, arch)
        self.assertEqual(arch.count('class="tp-cookie-table"'), 3)
        self.assertEqual(view.website_meta_description, COOKIE_DESCRIPTION)
        self.assertEqual(Views.search_count(backup_key), before + 1)

    def test_refund_clause_follows_the_consumer_code_once(self):
        view = self.env['ir.ui.view'].create({'name': 'Termini', 'type': 'qweb', 'key': 'website_torrepulia_theme.test_terms',
                                              'arch': '<t t-name="terms"><p>x</p></t>'})
        saved = ('<t t-name="terms"><div><p>10.3 Spese di restituzione a carico del cliente.</p>'
                 '<p>10.4 MICHELE LEONE dopo la verifica procederà con il rimborso fatta <b>ECCEZIONE delle spese di spedizione</b>. '
                 'Il rimborso avverrà entro e non oltre 30 giorni.</p>'
                 '<p>10.5 Il diritto di recesso decade.</p></div></t>')
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved, 'it_IT': saved}), view.id])
        retext_refund_clause(self.env)
        retext_refund_clause(self.env)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        for arch in self.env.cr.fetchone()[0].values():
            paragraphs = [''.join(node.itertext()) for node in etree.fromstring(arch).iter('p')]
            self.assertEqual(paragraphs[0], '10.3 Spese di restituzione a carico del cliente.')
            self.assertEqual(paragraphs[1], REFUND_CLAUSE)
            self.assertEqual(paragraphs[2], '10.5 Il diritto di recesso decade.')
        self.assertIn('comprese le spese di consegna', REFUND_CLAUSE)
        self.assertIn('entro 14 (quattordici) giorni', REFUND_CLAUSE)
        backups = self.env['ir.ui.view'].with_context(active_test=False).search_count(
            [('key', '=like', 'website_torrepulia_theme.before_refund_clause_%s_%%' % view.id)])
        self.assertEqual(backups, 1)

    def test_privacy_policy_tells_what_the_site_processes(self):
        website = self.env['website'].search([], limit=1)
        saved = ('<t t-name="privacy"><t t-call="website.layout"><div id="wrap" class="oe_structure tp-page">'
                 '<section class="tp-section tp-legal" data-snippet="s_text_block"><div class="container tp-reading">'
                 '<h1>Privacy Policy</h1><p>Questa Applicazione raccoglie alcuni Dati Personali</p></div></section></div></t></t>')
        page = self.env['website.page'].search([('url', '=', '/privacy-policy')], limit=1)
        if not page:
            view = self.env['ir.ui.view'].create({'name': 'Privacy', 'type': 'qweb', 'arch': '<t t-name="privacy"><p>x</p></t>',
                                                  'key': 'website_torrepulia_theme.test_privacy', 'website_id': website.id})
            page = self.env['website.page'].create({'url': '/privacy-policy', 'view_id': view.id, 'website_id': website.id})
        view = page.view_id
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved}), view.id])
        view.invalidate_recordset(['arch_db'])
        view.website_meta_description = PRIVACY_DESCRIPTION_OLD
        recopy_privacy_policy(self.env)
        arch = view.arch
        self.assertNotIn('Questa Applicazione raccoglie', arch)
        for kept in ('<h1>Privacy Policy</h1>', 'IONOS SE', 'Zoho Corporation', 'Prenotazione dell', 'art. 2220',
                     'Data Privacy Framework', 'garanteprivacy.it'):
            self.assertIn(kept, arch)
        self.assertNotIn('YouTube', arch)
        self.assertEqual(view.website_meta_description, PRIVACY_DESCRIPTION)
