"""Guides of the blog (website_blog, installed by the owner): written once, unpublished for review.

The text lives in docs/source like the legal pages. Links to the formats are read from the
products by internal reference, so they follow each database's addresses. Nothing is created
without the blog module, and a guide already created is never touched again: from then on it
belongs to the owner's editor.
"""
import json
from datetime import datetime

from lxml import etree, html

from odoo.tools import file_open

from .website import MODULE

STORAGE_GUIDE = {
    'xmlid': 'blog_post_storage_guide',
    'source': 'guida-conservare-olio.html',
    'name': "Come conservare l'olio extravergine di oliva",
    'subtitle': "Luce, calore e aria: dove tenerlo, quale contenitore scegliere e quanto dura dopo l'apertura.",
    # At most 60 and 160 characters: Google cuts what is longer.
    'meta_title': "Come conservare l'olio extravergine (e quanto dura aperto)",
    'meta_description': ("Dove tenere l'olio extravergine, a che temperatura, in quale contenitore e quanto dura aperto: "
                         "le regole del Consiglio Oleicolo Internazionale e degli studi."),
    'tag': 'Conservazione',
    'cover': '/website_torrepulia_theme/static/src/cinematic/owner/uliveto-file-1920.webp',
}

FILTER_GUIDE = {
    'xmlid': 'blog_post_filter_guide',
    'source': 'guida-filtrato-non-filtrato.html',
    'name': 'Olio filtrato o non filtrato: le differenze e quale scegliere',
    'subtitle': "Cos'è l'olio velato, cosa cambia nel gusto e nella durata, e perché il non filtrato va consumato nei primi mesi.",
    'meta_title': 'Olio filtrato o non filtrato: differenze e quale scegliere',
    'meta_description': ('Olio velato o limpido? Cosa cambia tra filtrato e non filtrato in gusto, polifenoli e durata, '
                         'e perché il non filtrato va consumato nei primi mesi.'),
    'tag': "Conoscere l'olio",
    'cover': '/website_torrepulia_theme/static/src/cinematic/owner/olive-cassone-1600.webp',
}

# The most searched topic of the season (Google Trends, October-November): the name stays without the
# year so the address holds every season, the year lives in the SEO title.
NEW_OIL_GUIDE = {
    'xmlid': 'blog_post_new_oil_guide',
    'source': 'guida-olio-nuovo.html',
    'name': 'Olio nuovo: quando arriva, perché pizzica e quanto costa',
    'subtitle': "Cos'è l'olio appena franto, perché è amaro e piccante, come riconoscerlo e quanto si paga nella campagna 2026/2027.",
    'meta_title': 'Olio nuovo 2026: quando arriva, perché pizzica, quanto costa',
    'meta_description': ("Quando arriva l'olio nuovo, perché pizzica in gola ed è amaro, come riconoscerlo in etichetta "
                         "e quanto costa nella campagna 2026/2027."),
    'tag': "Conoscere l'olio",
    'cover': '/website_torrepulia_theme/static/src/cinematic/owner/raccolta-reti-1920.webp',
}


def guide_content(env, website, source):
    with file_open(MODULE + '/docs/source/' + source, 'rb') as stream:
        text = etree.tostring(html.fromstring(stream.read().decode('utf-8')), method='html', encoding='unicode')
    # The old shop's internal references, the same lookup as the redirects (models/seo.py).
    # The other guides and the reservation page, where they exist in this database.
    reservation = website._torrepulia_footer_pages(['reservation'])[:1]
    links = {'__SHOP_URL__': '/shop',
             '__LATTA_URL__': website._torrepulia_old_product_url('LARGLAT5'),
             '__BIB_URL__': website._torrepulia_old_product_url('LARGBIB5'),
             '__RESERVATION_URL__': reservation.url or '/shop',
             '__STORAGE_GUIDE_URL__': published_guide_url(env, STORAGE_GUIDE) or '/blog',
             '__FILTER_GUIDE_URL__': published_guide_url(env, FILTER_GUIDE) or '/blog'}
    for token, url in links.items():
        text = text.replace(token, url)
    return text


# What the first release wrote: replaced only while the owner has not changed it.
FIRST_STORAGE_META = {
    'website_meta_title': "Come conservare l'olio extravergine di oliva | Torrepulia",
    'website_meta_description': ("Dove tenere l'olio extravergine, a che temperatura, quale contenitore scegliere e quanto dura "
                                 "dopo l'apertura: la guida basata sul Consiglio Oleicolo Internazionale e su studi universitari."),
}


def refresh_guide_meta(env, guide, first):
    data = env['ir.model.data'].search([('module', '=', MODULE), ('name', '=', guide['xmlid'])], limit=1)
    post = env['blog.post'].browse(data.res_id).exists() if data and 'blog.post' in env else None
    if not post:
        return
    values = {'website_meta_title': guide['meta_title'], 'website_meta_description': guide['meta_description']}
    post.write({field: values[field] for field, old in first.items() if (post[field] or '') in ('', old)})


def create_guide(env, guide):
    if 'blog.post' not in env:
        return env['ir.model.data']
    data = env['ir.model.data'].search([('module', '=', MODULE), ('name', '=', guide['xmlid'])], limit=1)
    if data:
        return data
    website = env['website'].search([('torrepulia_theme_enabled', '=', True)], limit=1)
    if not website:
        return data
    blog = env['blog.blog'].search([('website_id', 'in', [website.id, False])], order='website_id, id', limit=1)
    if not blog:
        blog = env['blog.blog'].create({'name': "Radici d'olio", 'website_id': website.id})
    tag = env['blog.tag'].search([('name', '=', guide['tag'])], limit=1) or env['blog.tag'].create({'name': guide['tag']})
    post = env['blog.post'].create({
        'name': guide['name'], 'subtitle': guide['subtitle'], 'blog_id': blog.id, 'tag_ids': [(4, tag.id)],
        'content': guide_content(env, website, guide['source']),
        'author_id': website.company_id.partner_id.id, 'website_id': website.id, 'is_published': False,
        'website_meta_title': guide['meta_title'], 'website_meta_description': guide['meta_description'],
        'cover_properties': '{"background-image": "url(%s)", "resize_class": "o_record_has_cover o_half_screen_height", '
                            '"opacity": "0.2", "background_color_class": "o_cc3"}' % guide['cover'],
    })
    return env['ir.model.data'].create({'module': MODULE, 'name': guide['xmlid'], 'model': 'blog.post',
                                        'res_id': post.id, 'noupdate': True})


def published_guide_url(env, guide):
    post = env.ref('%s.%s' % (MODULE, guide['xmlid']), raise_if_not_found=False) if 'blog.post' in env else None
    post = post.sudo() if post else post
    return post.website_url if post and post.is_published else False


# La Peranzana, "Il confezionamento": the oil leaves for home, the guide tells what to do when it arrives.
OIL_PAGE_SENTENCE = 'Da lì lo spediamo a casa tua.</p>'
OIL_PAGE_LINK = 'Da lì lo spediamo a casa tua. <a href="%s">Come conservarlo, una volta arrivato</a>.</p>'


def link_guide_from_oil_page(env, guide):
    """Once the guide is published; only the sentence as written, an owner rewrite stays untouched."""
    url = published_guide_url(env, guide)
    if not url:
        return
    Views = env['ir.ui.view'].sudo().with_context(active_test=False)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    for view in Views.search([('key', '=', MODULE + '.page_oil_view')]):
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        updated = {lang: arch if 'href="%s"' % url in arch else arch.replace(OIL_PAGE_SENTENCE, OIL_PAGE_LINK % url, 1)
                   for lang, arch in stored.items()}
        if updated == stored:
            continue
        view.copy({'name': 'Before the storage guide link', 'active': False, 'arch_fs': False,
                   'key': '%s.before_guide_link_%s_%s' % (MODULE, view.id, stamp)})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(updated), view.id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')


# The storage guide, "Filtrato o non filtrato": the full answer is in the filter guide, once published.
STORAGE_FILTER_SENTENCE = 'il non filtrato va consumato nei primi mesi</strong>.'
STORAGE_FILTER_LINK = ('il non filtrato va consumato nei primi mesi</strong>. Le differenze, nel gusto e nella durata, '
                       'le spieghiamo nella guida <a href="%s">olio filtrato o non filtrato</a>.')


def link_filter_guide_from_storage_guide(env):
    """Only the sentence as written: an owner rewrite stays untouched."""
    url = published_guide_url(env, FILTER_GUIDE)
    post = env.ref('%s.%s' % (MODULE, STORAGE_GUIDE['xmlid']), raise_if_not_found=False) if url else None
    if not post:
        return
    env.cr.execute('SELECT content FROM blog_post WHERE id = %s', [post.id])
    stored = env.cr.fetchone()[0] or {}
    updated = {lang: text if 'href="%s"' % url in text else text.replace(STORAGE_FILTER_SENTENCE, STORAGE_FILTER_LINK % url, 1)
               for lang, text in stored.items()}
    if updated != stored:
        env.cr.execute('UPDATE blog_post SET content = %s WHERE id = %s', [json.dumps(updated), post.id])
        post.invalidate_recordset(['content'])


# The filter guide, published 27/10: how the oil is filtered here, the filter press with cellulose sheets.
FILTER_PRESS_SOURCE = 'guida-filtro-cartoni.html'
FILTER_PRESS_BEFORE = '<h2>Il non filtrato ha più polifenoli?</h2>'
FILTER_PRESS_CTA = ('La Regina è <strong>filtrata</strong> tutto l’anno,',
                    'La Regina è <strong>filtrata</strong> con il filtro a cartoni tutto l’anno,')


def add_filter_press_section(env):
    """Before the polyphenols, once; the closing box names the method. Owner rewrites stay untouched."""
    post = env.ref('%s.%s' % (MODULE, FILTER_GUIDE['xmlid']), raise_if_not_found=False) if 'blog.post' in env else None
    if not post:
        return
    with file_open(MODULE + '/docs/source/' + FILTER_PRESS_SOURCE, 'rb') as stream:
        section = stream.read().decode('utf-8').strip()
    env.cr.execute('SELECT content FROM blog_post WHERE id = %s', [post.id])
    stored = env.cr.fetchone()[0] or {}
    updated = {}
    for lang, text in stored.items():
        if 'filtro a cartoni' not in text:
            text = text.replace(FILTER_PRESS_BEFORE, section + '\n' + FILTER_PRESS_BEFORE, 1)
            text = text.replace(*FILTER_PRESS_CTA)
        updated[lang] = text
    if updated != stored:
        env.cr.execute('UPDATE blog_post SET content = %s WHERE id = %s', [json.dumps(updated), post.id])
        post.invalidate_recordset(['content'])


# The new oil guide, 31/10: the back label with callouts, acidity, the value behind the price, no "novello".
# Each section: where it starts, where the next one starts, and a sentence only the first release had.
NEW_OIL_GUIDE_SECTIONS = [
    ('<div class="tp-guide-summary">', '<h2>Cos’è l’olio nuovo</h2>', 'si può indicare solo se tutto l’olio viene da quella raccolta.</li>'),
    ('<h2>Cos’è l’olio nuovo</h2>', '<h2>Quando arriva l’olio nuovo</h2>', 'o olio novello'),
    ('<h2>Come riconoscere l’olio nuovo in etichetta</h2>', '<h2>Quanto costa l’olio nuovo nel 2026</h2>',
     'ti dice da dove vengono le olive, per esempio'),
    ('<h2>Quanto costa l’olio nuovo nel 2026</h2>', '<h2>Come gustarlo</h2>', 'è quello che ritrovi nella conferma d’ordine'),
    ('<h2>Domande veloci</h2>', '<h2>Fonti</h2>', 'la quantità di acidi grassi liberi: per essere extravergine'),
    ('<h2>Fonti</h2>', '</section>', '(definizione di olio extravergine di oliva).</li>'),
]


def _section(text, start, end):
    begin = text.find(start)
    stop = text.find(end, begin + len(start)) if begin >= 0 else -1
    return text[begin:stop] if stop >= 0 else None


def refresh_guide_sections(env, guide, sections):
    """A section is rewritten from the source only while it still has its first wording: owner rewrites stay."""
    post = env.ref('%s.%s' % (MODULE, guide['xmlid']), raise_if_not_found=False) if 'blog.post' in env else None
    website = env['website'].search([('torrepulia_theme_enabled', '=', True)], limit=1)
    if not post or not website:
        return
    source = guide_content(env, website, guide['source'])
    env.cr.execute('SELECT content FROM blog_post WHERE id = %s', [post.id])
    stored = env.cr.fetchone()[0] or {}
    updated = {}
    for lang, text in stored.items():
        for start, end, first in sections:
            old, new = _section(text, start, end), _section(source, start, end)
            if old and new and first in old:
                text = text.replace(old, new, 1)
        updated[lang] = text
    if updated != stored:
        env.cr.execute('UPDATE blog_post SET content = %s WHERE id = %s', [json.dumps(updated), post.id])
        post.invalidate_recordset(['content'])
