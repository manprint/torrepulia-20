import copy
import json
import re
from lxml import etree
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    torrepulia_format_name = fields.Char('Torrepulia format')
    torrepulia_format_detail = fields.Char('Torrepulia contents')
    torrepulia_unit_count = fields.Integer('Units in provisional composition', default=1)
    torrepulia_composite = fields.Boolean('Provisional composition from single unit')
    torrepulia_shop_audience = fields.Char('Per chi è questo formato', translate=True,
        help='Una frase sotto il formato nello shop, per esempio: La scorta di famiglia.')
    torrepulia_format_badge_ids = fields.Many2many(
        'product.tag', 'torrepulia_format_badge_product_rel', 'product_tmpl_id', 'tag_id',
        string='Badge nei formati',
        help='Etichette colorate dello snippet Formati. Apri una etichetta per '
             'configurarne testo, colore e visibilita. Non modifica i tag dello shop.',
    )

    def _torrepulia_format_badges(self, website):
        self.ensure_one()
        tags = self.env['product.tag'].search([
            ('id', 'in', self.torrepulia_format_badge_ids.ids),
            ('visible_to_customers', '=', True),
        ] + website.website_domain())
        badges = []
        for tag in tags:
            color = tag.color or '#294d3b'
            if re.fullmatch(r'#[0-9a-fA-F]{3}', color):
                color = '#' + ''.join(character * 2 for character in color[1:])
            if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
                color = '#294d3b'
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
                      for value in channels]
            luminance = sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722)))
            badges.append({
                'name': tag.name, 'color': color,
                'text_color': '#000000' if luminance > .179 else '#ffffff',
            })
        return badges


class Website(models.Model):
    _inherit = 'website'

    torrepulia_formats_initialized = fields.Boolean(default=False)

    def _cinematic_products(self, ids=None):
        domain = self.sale_product_domain()
        domain += [('is_published', '=', True), ('torrepulia_format_name', '!=', False)]
        if ids:
            domain += [('id', 'in', ids)]
        products = self.env['product.template'].search(domain)
        return products.sorted(key=lambda p: (ids.index(p.id) if ids and p.id in ids else {2:0,6:1}.get(p.torrepulia_unit_count, 3 if 'bag' in (p.torrepulia_format_name or '').lower() else 2), p.id))

    @api.model
    def _provision_cinematic(self):
        module = 'website_torrepulia_theme'
        for website in self.search([('torrepulia_theme_enabled', '=', True)]):
            if not website.theme_id:
                website.theme_id = self.env['ir.module.module'].search([('name','=',module)],limit=1)
            if not website.torrepulia_formats_initialized:
                existing = self.env['product.template'].search(website.sale_product_domain() + [('torrepulia_unit_count','=',6)])
                existing.torrepulia_composite = True
                website.torrepulia_formats_initialized = True
            if website.torrepulia_provisioned_version >= 3:
                continue
            products = self.env['product.template'].search(website.sale_product_domain() + [('name','ilike','La Regina')])
            for product in products:
                if product.torrepulia_format_name:
                    continue
                name = product.name.lower()
                if 'duetto' in name:
                    vals = ('Duetto','2 bottiglie da 500 ml',2)
                elif '6' in name and 'bottigl' in name:
                    vals = ('6 bottiglie','6 bottiglie da 500 ml',6)
                elif 'bag' in name:
                    vals = ('Bag in Box','5 litri',1)
                elif 'latt' in name:
                    vals = ('La lattina','5 litri',1)
                else:
                    continue
                product.write(dict(zip(['torrepulia_format_name','torrepulia_format_detail','torrepulia_unit_count'],vals)))
                product.torrepulia_composite = vals[2] == 6
            formats = website._cinematic_products()
            duetto = formats.filtered(lambda p:p.torrepulia_unit_count == 2)[:1]
            for key in ['home','story','oil','land','contact','reservation','thanks','terms','privacy','cookies']:
                page = self.env.ref(module+'.page_'+key, raise_if_not_found=False)
                if not page or page.website_id != website:
                    continue
                # Approval authorizes a one-time migration; preserve the previous full composition.
                archive = page.view_id.copy({'key': f'{module}.before_cinematic_{key}_{website.id}', 'arch_fs':False})
                self.env['website.page'].create({'view_id':archive.id,'website_id':website.id,
                    'url':f'/torrepulia-before-cinematic/{key}','is_published':False,'website_indexed':False})
                if key == 'home':
                    root = etree.Element('t',{'t-name':page.view_id.key})
                    layout = etree.SubElement(root,'t',{'t-call':'website.layout'})
                    wrap = etree.SubElement(layout,'div',{'id':'wrap','class':'oe_structure tp-page mc-page'})
                    for i in [0, 1, 5, 2, 3, 4, 6]:
                        source = etree.fromstring(self.env.ref(f'{module}.s_cinematic_{i}').arch_db.encode())
                        section = copy.deepcopy(source[0])
                        for call in section.xpath('.//t[@t-call="website_torrepulia_theme.s_puglia_map"]'):
                            map_root = etree.fromstring(self.env.ref(module + '.s_puglia_map').arch_db.encode())
                            call.getparent().replace(call, copy.deepcopy(map_root[0]))
                        if i == 1:
                            section.set('data-product-ids',json.dumps([{'id':p.id,'display_name':p.name} for p in duetto]))
                        wrap.append(section)
                        if i == 0:
                            proofs = etree.fromstring(self.env.ref(module + '.s_torrepulia_home_facts').arch_db.encode())
                            wrap.append(copy.deepcopy(proofs[0]))
                        if i == 5:
                            packaging = etree.fromstring(self.env.ref(module + '.s_torrepulia_bib_line').arch_db.encode())
                            wrap.append(copy.deepcopy(packaging[0]))
                else:
                    root = etree.fromstring(page.with_context(lang='en_US').arch_db.encode())
                    wrap = root.find('.//div[@id="wrap"]')
                    if wrap is not None:
                        wrap.set('class',wrap.get('class','')+' mc-institutional')
                page.view_id.with_context(lang='en_US').write({'arch_db':etree.tostring(root,encoding='unicode'),'arch_fs':False})
            website.torrepulia_provisioned_version = 3
