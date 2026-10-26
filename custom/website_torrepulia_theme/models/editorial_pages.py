"""La Peranzana, La famiglia and Il territorio after the 23/10 critique (20.0.3.13.0 migration).

Saved Builder pages are rebuilt section by section from the snippet templates:
rewritten sections are replaced, the Bag in Box leaves /l-olio for its own
product page, the 2024 analysis is inserted after the process and both pages
close on the stock / new oil choice. Sections the owner added are kept in place.
On La famiglia the opening keeps the photo chosen in the Builder. The home family
section is aligned sentence by sentence. A disabled copy of each changed view is
kept, like the home cleanup.
"""
import copy
import json
import re
from datetime import datetime

from lxml import etree, html

from odoo.tools import file_open

from .home_copy import recopy_section, refine_section
from .website import MODULE, inline_puglia_map

HOME_KEY = MODULE + '.page_home_view'
# Set on the product page by static/src/js/bag_in_box.js: the description sanitizer strips ids.
BIB_ANCHOR = 'come-funziona'
# Home family section, aligned with La famiglia: exact sentences only, owner rewrites stay untouched.
HOME_REPLACEMENTS = (
    ("<p>Il primo uliveto, un'eredità d'amore.<br/>La nostra passione, da tre generazioni.</p>",
     "<p>Tre generazioni di olivicoltori, tra ulivi secolari e piante giovani.</p>"),
    ('alt="Santino e Michele Leone al lavoro negli uliveti di famiglia"',
     'alt="Foto d\'archivio: papà Michele sul trattore e nonno Santino Vincenzo"'),
    ('<figcaption>Santino e Michele. Le nostre radici.</figcaption>',
     '<figcaption>Papà Michele e nonno Santino Vincenzo.</figcaption>'),
    ('<span>Una famiglia. La stessa terra.</span>', '<span>Torremaggiore, dal 1945.</span>'),
    ("<p>Le nostre radici affondano negli uliveti storici coltivati da nonno Santino Vincenzo curati poi negli anni "
     "con la stessa passione e dedizione di papà Michele. Siamo cresciuti tra la terra e il profumo delle olive "
     "appena frante. Oggi noi, Franco e Salvatore, abbiamo scelto di onorare questa eredità familiare fondando "
     "Torrepulia: un progetto nato per unire i segreti della tradizione artigianale pugliese alle più moderne "
     "tecnologie di conservazione, portando l'autentico olio di Torremaggiore direttamente sulla tua tavola.</p>",
     "<p>Nonno Santino Vincenzo, tornato dalla guerra, ha ripreso a curare gli ulivi di famiglia, alcuni già "
     "secolari; papà Michele li ha fatti crescere fino a oltre 1000 piante. Noi, Franco e Salvatore, siamo "
     "cresciuti tra quegli ulivi e il profumo delle olive appena frante. Nel 2020 abbiamo fondato Torrepulia "
     "per portare il nostro olio direttamente sulla tua tavola.</p>"),
    # 20.0.3.14.0: the old trees said better.
    ("<p>Nonno Santino Vincenzo, tornato dalla guerra, ha ripreso a curare gli ulivi di famiglia, alcuni già "
     "secolari; papà Michele li ha fatti crescere fino a oltre 1000 piante. Noi, Franco e Salvatore, siamo "
     "cresciuti tra quegli ulivi e il profumo delle olive appena frante. Nel 2020 abbiamo fondato Torrepulia "
     "per portare il nostro olio direttamente sulla tua tavola.</p>",
     "<p>Nonno Santino Vincenzo, tornato dalla guerra, ha ripreso a curare i pochi ulivi di famiglia, gli stessi "
     "che oggi sono secolari; papà Michele ha fatto crescere l'uliveto fino a oltre 1000 piante. Noi, Franco e "
     "Salvatore, siamo cresciuti tra quegli alberi e il profumo delle olive appena frante. Nel 2020 abbiamo "
     "fondato Torrepulia per portare il nostro olio direttamente sulla tua tavola.</p>"),
)
REPORT_2024 = '/%s/static/src/docs/rapporto-di-prova-raccolto-2024.pdf' % MODULE
OIL_DESCRIPTION = ('La Peranzana di Torremaggiore e come nasce La Regina: raccolta, molitura, '
                   'analisi dell\'olio e abbinamenti.')
OIL_DESCRIPTION_2024 = ('La Peranzana di Torremaggiore e come nasce La Regina: raccolta, molitura, '
                        'analisi del raccolto 2024 e abbinamenti.')
LAND_DESCRIPTION = ('Torremaggiore e l\'Alto Tavoliere, nel nord della Puglia: dove crescono gli ulivi della '
                    'famiglia Leone e dove la tradizione colloca le origini della Peranzana.')
# Saved section -> template replacing it (None removes it); `after` inserts new sections.
PAGES = {
    MODULE + '.page_oil_view': {
        'replace': {
            's_torrepulia_cultivar_opening': 's_torrepulia_cultivar_opening',
            's_torrepulia_cultivar_history': 's_torrepulia_cultivar_history',
            's_torrepulia_production_process': 's_torrepulia_production_process',
            's_torrepulia_pairings': 's_torrepulia_pairings',
            's_torrepulia_sensory': 's_torrepulia_sensory',
            's_torrepulia_packaging': None,
            's_torrepulia_roots_cta': 's_torrepulia_choice_oil',
            's_torrepulia_choice_oil': 's_torrepulia_choice_oil',
        },
        'after': {'s_torrepulia_production_process': 's_torrepulia_oil_analysis'},
    },
    MODULE + '.page_story_view': {
        'replace': {
            's_torrepulia_story_chapters': 's_torrepulia_story_chapters',
            's_torrepulia_roots_transition': 's_torrepulia_roots_transition',
            's_torrepulia_roots_values': 's_torrepulia_roots_values',
            's_torrepulia_roots_cta': 's_torrepulia_choice_family',
            's_torrepulia_choice_family': 's_torrepulia_choice_family',
            's_torrepulia_roots_trees': 's_torrepulia_roots_trees',
        },
        # Only the words change: the opening photo is the owner's Builder choice.
        'retext': {'s_torrepulia_story_opening': ('h1', "p[@class='tp-about-subtitle']")},
        'after': {'s_torrepulia_story_chapters': 's_torrepulia_roots_trees'},
    },
    # Il territorio: the family story moves out (it lives on La famiglia), the place and Torremaggiore's history come in.
    MODULE + '.page_land_view': {
        'replace': {
            's_torrepulia_landscape': 's_torrepulia_landscape',
            's_torrepulia_land_story': 's_torrepulia_land_story',
            's_torrepulia_brand_story': 's_torrepulia_land_history',
            's_torrepulia_land_history': 's_torrepulia_land_history',
            's_torrepulia_land_grove': 's_torrepulia_land_grove',
            's_torrepulia_cta': 's_torrepulia_choice_land',
            's_torrepulia_choice_land': 's_torrepulia_choice_land',
        },
        'after': {'s_torrepulia_land_history': 's_torrepulia_land_grove',
                  's_torrepulia_brand_story': 's_torrepulia_land_grove'},
    },
}


def snippet_section(env, name):
    section = copy.deepcopy(etree.fromstring(env.ref(MODULE + '.' + name).arch_db.encode())[0])
    inline_puglia_map(env, section)
    return section


def rebuild_arch(env, arch, plan):
    root = etree.fromstring(arch)
    wrap = root.find('.//div[@id="wrap"]')
    if wrap is None:
        return arch
    present = {section.get('data-snippet') for section in wrap.findall('section')}
    for section in list(wrap.findall('section')):
        name = section.get('data-snippet')
        if name in plan['replace']:
            target = plan['replace'][name]
            if target is None:
                wrap.remove(section)
                continue
            if target != name and target in present:
                wrap.remove(section)
                continue
            new = snippet_section(env, target)
            wrap.replace(section, new)
            section = new
            present.add(target)
        elif name in plan.get('retext', {}):
            fresh = snippet_section(env, name)
            for path in plan['retext'][name]:
                old, text = section.find('.//' + path), fresh.find('.//' + path)
                if old is not None and text is not None:
                    text.tail = old.tail
                    old.getparent().replace(old, text)
        insert = plan['after'].get(name)
        if insert and insert not in present:
            section.addnext(snippet_section(env, insert))
            present.add(insert)
    return etree.tostring(root, encoding='unicode')


# 20.0.3.14.0: the La Peranzana sensory profile follows the owner's tasting sheet; La famiglia's 1945 chapter is reworded.
SENSORY_ONLY = {
    MODULE + '.page_oil_view': {'replace': {'s_torrepulia_sensory': 's_torrepulia_sensory'}, 'after': {}},
    MODULE + '.page_story_view': {'replace': {'s_torrepulia_story_chapters': 's_torrepulia_story_chapters'}, 'after': {}},
}


def refresh_editorial_pages(env, pages=PAGES):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for key, plan in pages.items():
        for view in Views.search([('key', '=', key)]):
            # Raw jsonb keeps every stored language, including pending Builder ones.
            env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
            stored = env.cr.fetchone()[0] or {}
            rebuilt = {lang: rebuild_arch(env, arch, plan) for lang, arch in stored.items()}
            if rebuilt == stored:
                continue
            view.copy({'name': 'Before the 23/10 critique', 'active': False, 'arch_fs': False,
                       'key': '%s.before_editorial_pages_%s_%s' % (MODULE, view.id, stamp)})
            env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(rebuilt), view.id])
    for view in Views.search([('key', '=', MODULE + '.page_oil_view')]):
        if (view.website_meta_description or '').startswith('Scopri la Peranzana, il processo produttivo'):
            view.website_meta_description = OIL_DESCRIPTION
    for view in Views.search([('key', '=', MODULE + '.page_land_view')]):
        if (view.website_meta_description or '').startswith('Il territorio di Torrepulia: Torremaggiore'):
            view.website_meta_description = LAND_DESCRIPTION
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


def retext_home(arch):
    for old, new in HOME_REPLACEMENTS:
        arch = arch.replace(old, new)
    return arch


def refine_home(env, arch, bib_url):
    """Three facts after the hero, one line for the Bag in Box, copy aligned section by section."""
    root = etree.fromstring(retext_home(arch))
    wrap = root.find('.//div[@id="wrap"]')
    if wrap is None:
        return arch
    for section in list(wrap.findall('section')):
        name = section.get('data-snippet')
        if name in ('s_torrepulia_value_proofs', 's_torrepulia_home_facts'):
            wrap.replace(section, snippet_section(env, 's_torrepulia_home_facts'))
        elif name in ('s_torrepulia_packaging', 's_torrepulia_bib_line'):
            line = snippet_section(env, 's_torrepulia_bib_line')
            for link in line.xpath(".//a[@class='tp-bib-line-link']"):
                link.set('href', bib_url)
            wrap.replace(section, line)
        else:
            refine_section(section)
    return etree.tostring(root, encoding='unicode')


def bag_in_box_url(env):
    product = env['product.template'].with_context(active_test=False).search([
        '|', ('torrepulia_format_name', 'ilike', 'bag in box'), ('name', 'ilike', 'bag in box'),
        ('is_published', '=', True)], limit=1)
    return product.website_url + '#' + BIB_ANCHOR if product else '/shop'


def align_home_family(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    bib_url = bag_in_box_url(env)
    for view in Views.search([('key', '=', HOME_KEY)]):
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        cleaned = {lang: refine_home(env, arch, bib_url) for lang, arch in stored.items()}
        if cleaned == stored:
            continue
        view.copy({'name': 'Before the family alignment', 'active': False, 'arch_fs': False,
                   'key': '%s.before_family_alignment_%s_%s' % (
                       MODULE, view.id, datetime.now().strftime('%Y%m%d_%H%M%S'))})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(cleaned), view.id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


def bag_in_box_description(env):
    """The Bag in Box explainer, without the link back to its own product page."""
    section = snippet_section(env, 's_torrepulia_packaging')
    for node in section.xpath(".//*[contains(@class, 'tp-bib-kicker') or contains(@class, 'tp-bib-cta')]"):
        node.getparent().remove(node)
    return etree.tostring(section, encoding='unicode')


def move_bag_in_box(env):
    products = env['product.template'].with_context(active_test=False).search([
        '|', ('torrepulia_format_name', 'ilike', 'bag in box'), ('name', 'ilike', 'bag in box')])
    for product in products:
        if 'tp-bib' in (product.website_description or ''):
            continue
        website = product.website_id or env['website'].search([('torrepulia_theme_enabled', '=', True)], limit=1)
        lang = website.default_lang_id.code if website else 'en_US'
        product.with_context(lang=lang).website_description = bag_in_box_description(env)


# 20.0.3.23.0: the fruity already is the olive; the aroma goes straight to tomato, artichoke and almond.
AROMA_REPLACEMENTS = (
    ('Al naso un fruttato medio-intenso di oliva appena colta: prima', 'Al naso un fruttato medio-intenso: prima'),
    ('Oliva appena colta: prima il verde del', 'Prima il verde del'),
)


def retext_aroma(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    env.cr.execute("SELECT id, arch_db FROM ir_ui_view WHERE arch_db::text LIKE %s AND active", ['%appena colta%'])
    for view_id, stored in env.cr.fetchall():
        updated = {}
        for lang, arch in (stored or {}).items():
            for old, new in AROMA_REPLACEMENTS:
                arch = arch.replace(old, new)
            updated[lang] = arch
        if updated == stored:
            continue
        view = Views.browse(view_id)
        view.copy({'name': 'Before the aroma wording', 'active': False, 'arch_fs': False,
                   'key': '%s.before_aroma_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view_id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


# 20.0.3.29.0: on a phone the hero shows a 1080 px high slice of the 1920 photo. The
# portrait crops hold that slice (cut at the 65 % of the CSS object-position, so the
# framing does not move) at a third of the weight.
HERO_PHOTO = '/website_torrepulia_theme/static/src/cinematic/images/'
HERO_PORTRAIT = ('<source media="(max-width: 760px) and (max-aspect-ratio: 3/5)" srcset="%(path)shero-foglie-portrait-648.webp"/>'
                 '<source media="(max-width: 760px) and (orientation: portrait)" srcset="%(path)shero-foglie-portrait-1080.webp"/>'
                 % {'path': HERO_PHOTO})
HERO_SOURCE = re.compile(r'<source(?=[^>]*%shero-foglie-640\.webp)' % re.escape(HERO_PHOTO))


def add_portrait_hero(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    env.cr.execute("SELECT id, arch_db FROM ir_ui_view WHERE arch_db::text LIKE %s AND active", ['%hero-foglie-640.webp%'])
    for view_id, stored in env.cr.fetchall():
        updated = {lang: arch if 'hero-foglie-portrait' in arch else HERO_SOURCE.sub(HERO_PORTRAIT + '<source', arch, count=1)
                   for lang, arch in (stored or {}).items()}
        if updated == stored:
            continue
        view = Views.browse(view_id)
        view.copy({'name': 'Before the portrait hero', 'active': False, 'arch_fs': False,
                   'key': '%s.before_portrait_hero_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view_id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


# 20.0.3.31.0: the cookie policy names what the site really sets (technical cookies, GA4, Meta Pixel),
# who provides it, for how long, and how to change the choice. 20.0.3.33.0: the privacy policy says
# what the site really processes. Only the old generic texts are replaced, with a disabled backup.
COOKIE_POLICY_OLD = 'Internet Explorer'
COOKIE_DESCRIPTION_OLD = 'Informazioni sui cookie e sul titolare del trattamento di torrepulia.it.'
COOKIE_DESCRIPTION = ('Quali cookie usa torrepulia.it, a che cosa servono, per quanto tempo restano nel browser '
                      'e come cambiare la tua scelta.')
PRIVACY_POLICY_OLD = 'Questa Applicazione raccoglie'
PRIVACY_DESCRIPTION_OLD = 'Informativa sul trattamento dei dati personali di torrepulia.it.'
PRIVACY_DESCRIPTION = ('Quali dati personali tratta torrepulia.it per ordini, prenotazioni e contatti, '
                       'per quanto tempo li conserva e quali sono i tuoi diritti.')


def legal_arch(arch, text, old_marker):
    """The legal section keeps its title and takes the new text; anything else in the page stays."""
    root = etree.fromstring(arch)
    for container in root.xpath('.//section[contains(concat(" ", @class, " "), " tp-legal ")]'
                                '/div[contains(concat(" ", @class, " "), " tp-reading ")]'):
        if old_marker not in etree.tostring(container, encoding='unicode'):
            continue
        for node in list(container):
            if node.tag != 'h1':
                container.remove(node)
        for node in text:
            container.append(copy.deepcopy(node))
    return etree.tostring(root, encoding='unicode')


def recopy_legal_page(env, url, source, old_marker, descriptions, backup):
    """The saved legal page at url takes docs/source/<source> while it still has old_marker."""
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with file_open(MODULE + '/docs/source/' + source, 'rb') as stream:
        fragment = html.fromstring(stream.read().decode('utf-8'))
    # Serialized as XML once: the saved page is an XML arch.
    text = etree.fromstring(etree.tostring(fragment, method='xml'))
    old_description, description = descriptions
    for page in env['website.page'].sudo().search([('url', '=', url)]):
        view = page.view_id
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        updated = {lang: legal_arch(arch, text, old_marker) if old_marker in arch else arch
                   for lang, arch in stored.items()}
        if updated != stored:
            view.copy({'name': 'Before the legal text of 26/10', 'active': False, 'arch_fs': False,
                       'key': '%s.%s_%s_%s' % (MODULE, backup, view.id, stamp)})
            env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view.id])
        for code, _name in env['res.lang'].get_installed():
            translated = view.with_context(lang=code)
            if (translated.website_meta_description or '').strip() in ('', old_description):
                translated.website_meta_description = description
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


def recopy_cookie_policy(env):
    recopy_legal_page(env, '/cookie-policy', 'cookie-policy.html', COOKIE_POLICY_OLD,
                      (COOKIE_DESCRIPTION_OLD, COOKIE_DESCRIPTION), 'before_cookie_policy')


def recopy_privacy_policy(env):
    recopy_legal_page(env, '/privacy-policy', 'privacy-policy.html', PRIVACY_POLICY_OLD,
                      (PRIVACY_DESCRIPTION_OLD, PRIVACY_DESCRIPTION), 'before_privacy_policy')


# 20.0.3.33.0: the refund on withdrawal as article 56 of the Codice del Consumo (D.Lgs. 206/2005)
# requires it: standard delivery included, within 14 days, same means of payment. Only the old
# clause (shipping costs excluded, 30 days) is rewritten; the rest of the owner's terms stays.
REFUND_OLD = 'ECCEZIONE delle spese di spedizione'
REFUND_CLAUSE = (
    '10.4 MICHELE LEONE rimborsa al Cliente tutti i pagamenti ricevuti, comprese le spese di consegna, '
    'senza indebito ritardo e comunque entro 14 (quattordici) giorni dal giorno in cui è informata '
    'della decisione di recedere. Non sono rimborsati i soli costi supplementari dovuti alla scelta, da parte '
    'del Cliente, di un tipo di consegna diverso dal tipo meno costoso di consegna standard offerto. Il '
    'rimborso è effettuato con lo stesso mezzo di pagamento usato per la transazione iniziale, salvo che '
    'il Cliente abbia espressamente convenuto altrimenti e a condizione che non debba sostenere alcun costo '
    'quale conseguenza del rimborso; per i pagamenti con bonifico bancario il Cliente indica l’IBAN sul '
    'quale ricevere il rimborso. MICHELE LEONE può trattenere il rimborso finché non abbia '
    'ricevuto i Prodotti oppure finché il Cliente non abbia dimostrato di averli rispediti, se '
    'precedente. Restano a carico del Cliente i soli costi diretti della restituzione dei Prodotti, come '
    'indicato al punto 10.3 (articoli 56 e 57 del D.Lgs. 206/2005, Codice del Consumo).')


def refund_clause_arch(arch):
    root = etree.fromstring(arch)
    for node in root.xpath('.//*[self::p or self::div or self::li][starts-with(normalize-space(.), "10.4")]'):
        # The innermost element holding the clause only: never a wrapper of 10.5 and the others.
        if REFUND_OLD not in ''.join(node.itertext()) or '10.5' in ''.join(node.itertext()):
            continue
        for child in list(node):
            node.remove(child)
        node.text = REFUND_CLAUSE
    return etree.tostring(root, encoding='unicode')


def retext_refund_clause(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    env.cr.execute("SELECT id, arch_db FROM ir_ui_view WHERE arch_db::text LIKE %s AND active", ['%' + REFUND_OLD + '%'])
    for view_id, stored in env.cr.fetchall():
        updated = {lang: refund_clause_arch(arch) if REFUND_OLD in arch else arch for lang, arch in (stored or {}).items()}
        if updated == stored:
            continue
        view = Views.browse(view_id)
        view.copy({'name': 'Before the refund clause of 26/10', 'active': False, 'arch_fs': False,
                   'key': '%s.before_refund_clause_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view_id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


# 20.0.3.20.0: reservations are paid on the order confirmation, before the oil leaves.
PAYMENT_REPLACEMENTS = (('paghi alla spedizione', 'paghi alla conferma dell\u2019ordine'),)


def retext_payment(env):
    """Saved pages (closings of La Peranzana, La famiglia, Il territorio) in every stored language."""
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    env.cr.execute("SELECT id, arch_db FROM ir_ui_view WHERE arch_db::text LIKE %s AND active", ['%paghi alla spedizione%'])
    for view_id, stored in env.cr.fetchall():
        updated = {}
        for lang, arch in (stored or {}).items():
            for old, new in PAYMENT_REPLACEMENTS:
                arch = arch.replace(old, new)
            updated[lang] = arch
        if updated == stored:
            continue
        view = Views.browse(view_id)
        view.copy({'name': 'Before the payment wording', 'active': False, 'arch_fs': False,
                   'key': '%s.before_payment_wording_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view_id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


def link_report_2024(env):
    env['torrepulia.oil.profile'].search([
        ('harvest_year', '=', 2024), ('report_url', '=', False)]).report_url = REPORT_2024


# 20.0.3.21.0: the harvest photo under the process intro. Only the photo is added: the steps keep the owner's Builder edits.
PROCESS_PHOTO = './/img[contains(concat(" ", @class, " "), " tp-process-photo ")]'


def add_process_photo(arch, photo):
    root = etree.fromstring(arch)
    changed = False
    for section in root.xpath('.//section[@data-snippet="s_torrepulia_production_process"]'):
        intro = section.xpath('.//div[contains(concat(" ", @class, " "), " tp-process-intro ")]')
        if not intro or section.xpath(PROCESS_PHOTO):
            continue
        intro[0].append(copy.deepcopy(photo))
        changed = True
    return etree.tostring(root, encoding='unicode') if changed else arch


def add_process_photos(env):
    photo = snippet_section(env, 's_torrepulia_production_process').xpath(PROCESS_PHOTO)[0]
    photo.tail = None
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for view in Views.search([('key', '=', MODULE + '.page_oil_view')]):
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        updated = {lang: add_process_photo(arch, photo) for lang, arch in stored.items()}
        if updated == stored:
            continue
        view.copy({'name': 'Before the harvest photo', 'active': False, 'arch_fs': False,
                   'key': '%s.before_process_photo_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view.id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


# 25/10: the owner's tasting words, the harvest at veraison and the "trusted" mill, in every saved page.
OIL_SENSORY = {
    'lead': 'Un fruttato medio-intenso, elegante e armonico.',
    'Al profumo': ('Prima il verde del <strong>pomodoro</strong> e del <strong>carciofo</strong>, '
                   'poi la <strong>mandorla fresca</strong>.'),
    'Al gusto': ('Morbido e rotondo. Amaro e piccante si sentono, delicati e ben bilanciati tra loro, senza mai '
                 'coprire il resto.'),
    'Al palato': 'Il finale &#232; pulito, con un&#8217;acidit&#224; bassa.',
}
OIL_HARVEST = ('Tra ottobre e novembre raccogliamo le olive dalla pianta all&#8217;inizio dell&#8217;invaiatura, '
               'quando il frutto comincia a cambiare colore: &#232; il momento in cui l&#8217;oliva &#232; pi&#249; '
               'ricca di polifenoli e di profumi.')
RECOPY_KEYS = (HOME_KEY, MODULE + '.page_oil_view', MODULE + '.page_story_view')
MILL_REPLACEMENTS = (('frantoio partner', 'frantoio di fiducia'), ('oltre 1000 piante', 'oltre 1.500 piante'))
# La famiglia: the owner's chapters, by year.
CHAPTERS = {
    '1945': ('Tornato dal fronte, nonno Santino Vincenzo sceglie di ripartire dalla terra. Dedica la sua vita ai pochi '
             'ulivi ereditati dal padre, curandoli con le proprie mani: sono gli stessi alberi secolari che custodiamo '
             'ancora oggi. A suo figlio Michele trasmette il sapere contadino, la passione per il lavoro nei campi e '
             'l&#8217;amore per la terra.'),
    '1980': ('Pap&#224; Michele raccoglie l&#8217;eredit&#224; del nonno: la passione per il lavoro nei campi e '
             'l&#8217;amore per la natura. Con lui l&#8217;azienda cresce fino a contare oggi oltre 1.500 piante di ulivo, '
             'prevalentemente di cultivar Peranzana, nell&#8217;agro di Torremaggiore. A guidare il lavoro resta la stessa '
             'cura per la terra, imparata dal padre e tramandata a noi.'),
    '2020': ('Noi, Franco e Salvatore, siamo cresciuti tra questi ulivi e il profumo delle olive appena frante, con la '
             'passione e i valori trasmessi da nostro padre e da nostro nonno. Franco ha coltivato la sua passione per il '
             'lavoro nei campi e la produzione dell&#8217;olio; Salvatore ha seguito un percorso in ingegneria gestionale, '
             'mantenendo vivo il desiderio di far conoscere un prodotto capace di raccontare la nostra Puglia. Nel 2020 '
             'abbiamo unito le nostre competenze per dare vita a Torrepulia e aprire un nuovo capitolo nella storia '
             'dell&#8217;azienda agricola Leone. Il nome unisce Torremaggiore e la Puglia, le nostre radici e il luogo da '
             'cui tutto comincia. Da qui portiamo il nostro olio direttamente sulla tua tavola, senza intermediari, con la '
             'stessa cura che la nostra famiglia dedica a questi ulivi da tre generazioni.'),
}
# Come lavoriamo: packed at the mill and shipped from there; analyses published from the 2026 harvest.
METHOD = {
    'Spediamo': 'Confezioniamo l&#8217;olio direttamente in frantoio e lo spediamo a casa tua, senza intermediari.',
    'Misuriamo': ('Dal raccolto 2026 facciamo analizzare l&#8217;olio nuovo e pubblichiamo il rapporto di prova intero, '
                  'cos&#236; come ci viene consegnato. <a href="/l-olio#analisi">Le analisi</a>'),
}
OIL_LEAD = ('La <strong>Peranzana</strong> &#232; la cultivar dell&#8217;Alto Tavoliere delle Puglie. &#200; a duplice '
            'attitudine: apprezzata sia per l&#8217;olio che se ne ricava sia da gustare come oliva da tavola. La '
            'coltiviamo nell&#8217;agro di <strong>Torremaggiore</strong> da tre generazioni: qui il vento, la terra '
            'fertile del Tavoliere e il sole della Puglia le danno il suo carattere distintivo. Dalle sue olive nasce '
            '<strong>La Regina</strong>, il nostro olio extravergine.')
OIL_HEARTLAND = ('Tra <strong>Torremaggiore, San Severo e San Paolo di Civitate</strong> si concentra la coltivazione '
                 'della Peranzana. I nostri uliveti si trovano nell&#8217;agro di Torremaggiore e contano oltre 1.500 '
                 'piante: dalle loro olive nasce La Regina, il nostro olio extravergine.')
OIL_PACKING = ('Confezioniamo l&#8217;olio direttamente in frantoio, in bottiglia, latta o Bag in Box, filtrato o, per '
               'chi lo preferisce, non filtrato. Da l&#236; lo spediamo a casa tua.')
HOME_FACT_1945 = '<a href="/aboutus"><strong>Dal 1945</strong><span>tre generazioni sulla stessa terra</span></a>'


def _inner(node, markup):
    fresh = etree.fromstring('<x>%s</x>' % markup)
    for child in list(node):
        node.remove(child)
    node.text = fresh.text
    for child in fresh:
        node.append(child)


def recopy_oil(root):
    for section in root.xpath('.//section[@data-snippet="s_torrepulia_sensory"]'):
        for node in section.xpath('.//p[contains(concat(" ", @class, " "), " lead ")]')[:1]:
            _inner(node, OIL_SENSORY['lead'])
        for term in section.xpath('.//dl//dt'):
            text = OIL_SENSORY.get(''.join(term.itertext()).strip())
            following = term.getnext()
            if text and following is not None and following.tag == 'dd':
                _inner(following, text)
    for step in root.xpath('.//section[@data-snippet="s_torrepulia_production_process"]//li'):
        text = {'La raccolta': OIL_HARVEST, 'Il confezionamento': OIL_PACKING}.get(step.xpath('string(.//h3)').strip())
        for node in step.xpath('.//p')[:1] if text else ():
            _inner(node, text)
    for node in root.xpath('.//section[@data-snippet="s_torrepulia_cultivar_opening"]'
                           '//p[contains(concat(" ", @class, " "), " lead ")]')[:1]:
        _inner(node, OIL_LEAD)
    for link in root.xpath('.//section[@data-snippet="s_torrepulia_cultivar_opening"]//a[@href="#analisi"]'):
        link.text = 'Le analisi del raccolto '
    for node in root.xpath('.//section[@data-snippet="s_torrepulia_cultivar_history"]'
                           '//div[contains(concat(" ", @class, " "), " tp-oil-territory ")]//p')[:1]:
        _inner(node, OIL_HEARTLAND)


def recopy_story(root):
    for article in root.xpath('.//section[@data-snippet="s_torrepulia_story_chapters"]//article'):
        year = article.xpath('string(.//p[contains(concat(" ", @class, " "), " tp-about-year ")])').strip()
        texts = article.xpath('./p[not(contains(concat(" ", @class, " "), " tp-about-year "))]')
        if year in CHAPTERS and texts:
            _inner(texts[0], CHAPTERS[year])


def recopy_method(root):
    for term in root.xpath('.//dl[contains(concat(" ", @class, " "), " tp-method-list ")]//dt'):
        text, following = METHOD.get(term.xpath('string(.)').strip()), term.getnext()
        if text and following is not None and following.tag == 'dd':
            _inner(following, text)


def recopy_home_facts(root):
    for facts in root.xpath('.//section[@data-snippet="s_torrepulia_home_facts"]'):
        for strong in facts.xpath('.//a[@href="/territorio"]/strong'):
            strong.text = 'Oltre 1.500'
        for link in facts.xpath('.//a[@href="/l-olio#analisi"]'):
            _inner(link.getparent(), HOME_FACT_1945)


def recopy_arch(arch, key, analysis=None):
    for old, new in MILL_REPLACEMENTS:
        arch = arch.replace(old, new)
    if key not in RECOPY_KEYS:
        return arch
    root = etree.fromstring(arch)
    if key == HOME_KEY:
        for section in root.xpath('.//div[@id="wrap"]/section'):
            recopy_section(section)
        recopy_home_facts(root)
    elif key == MODULE + '.page_oil_view':
        recopy_oil(root)
        # The analysis now comes from the backend: the saved 2024 figures leave the page.
        for section in root.xpath('.//section[@data-snippet="s_torrepulia_oil_analysis"]'):
            if analysis is not None and not section.xpath('.//*[contains(concat(" ", @class, " "), " tp-analysis-content ")]'):
                fresh = copy.deepcopy(analysis)
                fresh.tail = section.tail
                section.getparent().replace(section, fresh)
    recopy_story(root)
    recopy_method(root)
    return etree.tostring(root, encoding='unicode')


def recopy_pages(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    analysis = snippet_section(env, 's_torrepulia_oil_analysis')
    env.cr.execute("SELECT id FROM ir_ui_view WHERE active AND (key IN %s OR arch_db::text LIKE %s OR arch_db::text LIKE %s)",
                   [RECOPY_KEYS, '%frantoio partner%', '%oltre 1000 piante%'])
    for view in Views.browse([row[0] for row in env.cr.fetchall()]):
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        updated = {lang: recopy_arch(arch, view.key, analysis) for lang, arch in stored.items()}
        if updated == stored:
            continue
        view.copy({'name': 'Before the 25/10 copy', 'active': False, 'arch_fs': False,
                   'key': '%s.before_copy_2510_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view.id])
    # The search result no longer promises a harvest the page does not show.
    for view in Views.search([('key', '=', MODULE + '.page_oil_view')]):
        for code, _name in env['res.lang'].get_installed():
            translated = view.with_context(lang=code)
            if translated.website_meta_description == OIL_DESCRIPTION_2024:
                translated.website_meta_description = OIL_DESCRIPTION
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')
