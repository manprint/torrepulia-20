"""Guides of the blog (website_blog, installed by the owner): written once, unpublished for review.

The text lives in docs/source like the legal pages. Links to the formats are read from the
products by internal reference, so they follow each database's addresses. Nothing is created
without the blog module, and a guide already created is never touched again: from then on it
belongs to the owner's editor.
"""
from lxml import etree, html

from odoo.tools import file_open

from .website import MODULE

STORAGE_GUIDE = {
    'xmlid': 'blog_post_storage_guide',
    'source': 'guida-conservare-olio.html',
    'name': "Come conservare l'olio extravergine di oliva",
    'subtitle': "Luce, calore e aria: dove tenerlo, quale contenitore scegliere e quanto dura dopo l'apertura.",
    'meta_title': "Come conservare l'olio extravergine di oliva | Torrepulia",
    'meta_description': ("Dove tenere l'olio extravergine, a che temperatura, quale contenitore scegliere e quanto dura "
                         "dopo l'apertura: la guida basata sul Consiglio Oleicolo Internazionale e su studi universitari."),
    'tag': 'Conservazione',
    'cover': '/website_torrepulia_theme/static/src/cinematic/owner/uliveto-file-1920.webp',
}


def guide_content(env, website, source):
    with file_open(MODULE + '/docs/source/' + source, 'rb') as stream:
        text = etree.tostring(html.fromstring(stream.read().decode('utf-8')), method='html', encoding='unicode')
    # The old shop's internal references, the same lookup as the redirects (models/seo.py).
    links = {'__SHOP_URL__': '/shop',
             '__LATTA_URL__': website._torrepulia_old_product_url('LARGLAT5'),
             '__BIB_URL__': website._torrepulia_old_product_url('LARGBIB5')}
    for token, url in links.items():
        text = text.replace(token, url)
    return text


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
