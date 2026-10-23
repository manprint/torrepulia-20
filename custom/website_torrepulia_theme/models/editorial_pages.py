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
from datetime import datetime

from lxml import etree

from .website import MODULE, inline_puglia_map

HOME_KEY = MODULE + '.page_home_view'
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
)
REPORT_2024 ='/%s/static/src/docs/rapporto-di-prova-raccolto-2024.pdf' % MODULE
OIL_DESCRIPTION = ('La Peranzana di Torremaggiore e come nasce La Regina: raccolta, molitura, '
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


def refresh_editorial_pages(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for key, plan in PAGES.items():
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


def align_home_family(env):
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    for view in Views.search([('key', '=', HOME_KEY)]):
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        cleaned = {lang: retext_home(arch) for lang, arch in stored.items()}
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


def link_report_2024(env):
    env['torrepulia.oil.profile'].search([
        ('harvest_year', '=', 2024), ('report_url', '=', False)]).report_url = REPORT_2024
