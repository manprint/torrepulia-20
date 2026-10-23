import copy
import logging

from lxml import etree, html

from odoo import api, fields, models
from odoo.tools import file_open
from odoo.tools.binary import BinaryBytes

_logger = logging.getLogger(__name__)
MODULE = 'website_torrepulia_theme'
SCOPED_VIEWS = ('torrepulia_footer', 'torrepulia_layout', 'torrepulia_shop_page',
                'torrepulia_product_page', 'torrepulia_header_contact')


def inline_puglia_map(env, root):
    """Replace calls to the Puglia map with its SVG: page content must stay plain HTML for the Builder."""
    for call in root.xpath('.//t[@t-call="%s.s_puglia_map"]' % MODULE):
        svg = etree.fromstring(env.ref(MODULE + '.s_puglia_map').arch_db.encode())[0]
        call.getparent().replace(call, copy.deepcopy(svg))


class Website(models.Model):
    _inherit = 'website'

    torrepulia_theme_enabled = fields.Boolean('Torrepulia website', default=False)
    torrepulia_provisioned_version = fields.Integer('Torrepulia content version', default=0)

    @api.model
    def _torrepulia_xmlid(self, name, record):
        xmlid = self.env['ir.model.data'].search([
            ('module', '=', MODULE), ('name', '=', name)], limit=1)
        vals = {'module': MODULE, 'name': name, 'model': record._name,
                'res_id': record.id, 'noupdate': True}
        if xmlid:
            xmlid.write(vals)
        else:
            self.env['ir.model.data'].create(vals)

    def _torrepulia_page_arch(self, seed, key):
        root = etree.Element('t', {'t-name': key})
        layout = etree.SubElement(root, 't', {'t-call': 'website.layout'})
        wrap = etree.SubElement(layout, 'div', {'id': 'wrap', 'class': 'oe_structure tp-page'})
        for item in seed:
            if item.tag == 'snippet':
                view = self.env.ref(MODULE + '.' + item.get('ref'))
                fragment = etree.fromstring(view.arch_db.encode())
                for node in fragment:
                    wrap.append(copy.deepcopy(node))
            elif item.tag == 'legal':
                section = etree.SubElement(wrap, 'section', {
                    'class': 'tp-section tp-legal', 'data-snippet': 's_text_block',
                    'data-name': seed.get('title'),
                })
                container = etree.SubElement(section, 'div', {'class': 'container tp-reading'})
                etree.SubElement(container, 'h1').text = seed.get('title').split(' | ')[0]
                with file_open(MODULE + '/docs/source/' + item.get('file'), 'rb') as source:
                    fragment = html.fromstring(source.read().decode('utf-8'))
                for node in fragment:
                    container.append(copy.deepcopy(node))
            else:
                wrap.append(copy.deepcopy(item))
        for item in wrap.xpath('.//snippet'):
            fragment = etree.fromstring(self.env.ref(MODULE + '.' + item.get('ref')).arch_db.encode())
            parent = item.getparent()
            index = parent.index(item)
            parent.remove(item)
            for offset, node in enumerate(fragment):
                parent.insert(index + offset, copy.deepcopy(node))
        # Materialized HTML gives each page independent Builder ownership.
        inline_puglia_map(self.env, wrap)
        for catalog in wrap.xpath('.//*[@t-att-data-filter-id]'):
            catalog.set('data-filter-id', str(self.env.ref('website_sale.dynamic_filter_all_products').id))
            del catalog.attrib['t-att-data-filter-id']
        return etree.tostring(root, encoding='unicode')

    # Layout extensions that rewrite Odoo's header and footer: they belong to the Torrepulia site
    # only, so another website of the database keeps whatever header or footer its builder picks.
    SITE_ONLY_VIEWS = ('navigation_layout', 'footer_editorial')

    def _torrepulia_scope_navigation(self):
        self.ensure_one()
        for name in self.SITE_ONLY_VIEWS:
            view = self.env.ref(MODULE + '.' + name, raise_if_not_found=False)
            if view and not view.website_id:
                view.website_id = self

    @api.model
    def _provision_torrepulia_site(self):
        websites = self.search([('torrepulia_theme_enabled', '=', True)])
        if not websites:
            websites = self.search([('name', 'ilike', 'Torrepulia')])
        if not websites:
            candidates = self.search([])
            if len(candidates) == 1:
                homepage = self.env['website.page'].search([
                    ('url', '=', '/'), ('website_id', '=', candidates.id)], limit=1)
                if not homepage or 's_torrepulia_' in homepage.arch_db or 'oe_empty"/>' in homepage.arch_db:
                    websites = candidates
        if len(websites) != 1:
            for name in SCOPED_VIEWS:
                view = self.env.ref(MODULE + '.' + name)
                if not view.website_id:
                    view.active = False
            _logger.warning('Torrepulia provisioning skipped: choose one website explicitly.')
            return
        website = websites.with_context(lang='en_US')
        first_run = not website.torrepulia_provisioned_version
        if first_run:
            website.write({'name': 'Torrepulia', 'torrepulia_theme_enabled': True})
            with file_open(MODULE + '/static/src/img/content/torrepulia-logo.png', 'rb') as logo:
                website.logo = BinaryBytes(logo.read(), filename='torrepulia-logo.png')
            # Scope inherited chrome to this website, including installations with multiple sites.
            for name in SCOPED_VIEWS:
                view = self.env.ref(MODULE + '.' + name)
                view.write({'website_id': website.id, 'active': True})
                self._torrepulia_xmlid(name, view)

        website._torrepulia_scope_navigation()
        contact_view = self.env.ref(MODULE + '.torrepulia_header_contact')
        if not contact_view.website_id:
            contact_view.write({'website_id': website.id, 'active': True})
            self._torrepulia_xmlid('torrepulia_header_contact', contact_view)
        header = self.env['ir.ui.view'].search([
            ('key', '=', 'website.header_text_element'),
            ('website_id', '=', website.id)], limit=1)
        header = header or self.env.ref('website.header_text_element')
        if contact_view.inherit_id != header:
            contact_view.inherit_id = header

        with file_open(MODULE + '/data/pages.xml', 'rb') as source:
            seeds = etree.parse(source).getroot()
        for seed in seeds:
            name = 'page_' + seed.get('key')
            existing = self.env.ref(MODULE + '.' + name, raise_if_not_found=False)
            if existing:
                continue
            url = seed.get('url')
            conflict = self.env['website.page'].search([
                ('url', '=', url), ('website_id', '=', website.id)], limit=1)
            if conflict:
                if url == '/' and first_run and 's_torrepulia_' in conflict.arch_db:
                    # Preserve the user's complete phase-1 composition, without deleting it.
                    conflict.write({'url': '/torrepulia-before-phase-2',
                                    'website_indexed': False, 'is_published': False})
                elif url == '/' and first_run and 'oe_empty"/>' in conflict.arch_db:
                    conflict.write({'url': '/torrepulia-before-phase-2',
                                    'website_indexed': False, 'is_published': False})
                else:
                    _logger.warning('Keeping existing page at %s on website %s', url, website.id)
                    continue
            key = MODULE + '.' + name + '_view'
            arch = self._torrepulia_page_arch(seed, key)
            legacy = self.env.ref(MODULE + '.torrepulia_homepage', raise_if_not_found=False) if url == '/' else False
            if legacy and first_run and legacy.url == '/torrepulia-home':
                view = legacy.view_id
                view.write({'arch_db': arch, 'arch_fs': False, 'website_id': website.id,
                            'website_meta_title': seed.get('title'),
                            'website_meta_description': seed.get('description')})
                page = legacy
                page.write({'url': '/', 'name': seed.get('title'), 'website_id': website.id})
                self._torrepulia_xmlid('torrepulia_homepage_view', view)
                self._torrepulia_xmlid('torrepulia_homepage', page)
            else:
                view = self.env['ir.ui.view'].with_context(lang='en_US').create({
                    'name': seed.get('title'), 'type': 'qweb', 'key': key,
                    'arch_db': arch, 'website_id': website.id,
                    'website_meta_title': seed.get('title'),
                    'website_meta_description': seed.get('description'),
                })
                page = self.env['website.page'].create({
                    'view_id': view.id, 'url': url, 'is_published': True,
                    'website_indexed': seed.get('indexed', 'true') == 'true',
                    'website_id': website.id,
                })
            self._torrepulia_xmlid(name, page)
            self._torrepulia_xmlid(name + '_view', view)
            if url == '/' and conflict:
                conflict.menu_ids.write({'page_id': page.id, 'url': '/'})

        if first_run:
            website.homepage_url = '/'
        menu_items = [('/', 'Home'), ('/shop', 'Shop'), ('/aboutus', 'La famiglia'),
                      ('/l-olio', 'La Peranzana'), ('/territorio', 'Il territorio'),
                      ('/prenotailtuoolio', 'Olio nuovo'), ('/contactus', 'Contatti')]
        for index, (url, label) in enumerate(menu_items):
            name = 'menu_' + str(index)
            if self.env.ref(MODULE + '.' + name, raise_if_not_found=False):
                continue
            menu = self.env['website.menu'].search([
                ('website_id', '=', website.id), ('url', '=', url),
                ('parent_id', '=', website.menu_id.id)], limit=1)
            if not menu:
                menu = self.env['website.menu'].create({
                    'name': label, 'url': url, 'website_id': website.id,
                    'parent_id': website.menu_id.id, 'sequence': index * 10,
                })
            self._torrepulia_xmlid(name, menu)
        for index, (old, new) in enumerate([
            ('/torrepulia-home', '/'), ('/privacy', '/privacy-policy'),
            ('/shop/terms', '/termini-e-condizioni'),
            ('/shop/category/lattina-1', '/shop?search=Lattina'),
            ('/shop/category/bag-in-box-2', '/shop?search=Bag'),
            ('/shop/category/bottiglia-3', '/shop?search=Bottiglie'),
        ]):
            name = 'redirect_' + str(index)
            if not self.env.ref(MODULE + '.' + name, raise_if_not_found=False):
                rewrite = self.env['website.rewrite'].create({
                    'name': 'Torrepulia ' + old, 'website_id': website.id,
                    'url_from': old, 'url_to': new, 'redirect_type': '301',
                })
                self._torrepulia_xmlid(name, rewrite)
        if website.torrepulia_provisioned_version < 2:
            website.torrepulia_provisioned_version = 2
