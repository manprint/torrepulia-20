from lxml import etree
from odoo import api, fields, models
from odoo.tools import file_open
from odoo.tools.binary import BinaryBytes

BASE = '/website_torrepulia_theme/static/src/cinematic/campaign/'
REPLACEMENTS = {
    'uliveto-hero-1280.webp': ('hero-1920.webp', 'Una bottiglia La Regina tra i rami di un ulivo'),
    'family-today-690.webp': ('family-1600.webp', 'Franco e Salvatore Leone tra gli ulivi'),
    'harvest-1440.webp': ('olive-1600.webp', 'Una mano tra i rami di ulivo'),
    'territory-1080.webp': ('land-1920.webp', 'Filari di ulivi al tramonto'),
    'culinary-campaign-1536.webp': ('still-life-1920.webp', 'La Regina con olive e oliera'),
    'bottle-original.jpeg': ('bottle-1600.webp', 'La Regina, bottiglia da 500 ml'),
}


def campaign_markup(root):
    for image in root.xpath('.//img[@src]'):
        source = image.get('src')
        if '/static/src/cinematic/images/' not in source:
            continue
        name = source.rsplit('/', 1)[-1]
        if name in REPLACEMENTS:
            target, alt = REPLACEMENTS[name]
            image.set('src', BASE + target)
            image.set('alt', alt)
            # Original dimensions must not reserve an obsolete aspect ratio.
            image.attrib.pop('width', None)
            image.attrib.pop('height', None)
            if target.startswith('bottle-'):
                image.set('class', (image.get('class', '') + ' mc-master-bottle').strip())
    for section in root.xpath('.//section'):
        for caption in section.xpath('.//span[@class="photo-caption"]'):
            if caption.text == 'La raccolta, nei nostri uliveti.':
                caption.text = 'La Peranzana, nei nostri uliveti.'
        for kind, css, image_xpath in [('hero', 'hero', './img')]:
            if css not in section.get('class', '').split():
                continue
            images = section.xpath(image_xpath)
            if not images or not images[0].get('src', '').startswith(BASE + kind):
                continue
            if section.xpath('./video[@data-photo-film]'):
                continue
            video = etree.Element('video', {'class': 'mc-photo-film', 'data-photo-film': kind,
                'muted': 'muted', 'loop': 'loop', 'playsinline': 'playsinline', 'preload': 'none',
                'poster': BASE + kind + '-desktop-poster.webp', 'aria-hidden': 'true'})
            section.insert(1, video)
            button = etree.SubElement(section, 'button', {'class': 'mc-film-toggle o_not_editable',
                'type': 'button', 'aria-label': 'Riproduci animazione fotografica', 'title': 'Riproduci animazione fotografica'})
            etree.SubElement(button, 'img', {'src': '/website_torrepulia_theme/static/src/cinematic/icons/play.svg', 'alt': '', 'width':'18', 'height':'18'})
    return root


class Website(models.Model):
    _inherit = 'website'

    torrepulia_campaign_version = fields.Integer(default=0)

    @api.model
    def _provision_official_branding(self):
        for website in self.search([('torrepulia_theme_enabled', '=', True), ('torrepulia_campaign_version', '<', 2)]):
            with file_open('website_torrepulia_theme/static/src/img/content/LOGO_TORREPULIA_BLUG.png', 'rb') as source:
                website.logo = BinaryBytes(source.read(), filename='Torrepulia-logo-blue.png')
            website.torrepulia_campaign_version = 2

    @api.model
    def _provision_photo_campaign(self):
        module = 'website_torrepulia_theme'
        # Keep the snippet palette current even when saved pages are already migrated.
        for index in range(7):
            view = self.env.ref(f'{module}.s_cinematic_{index}')
            # Snippet sources now contain the owner's approved photography/layout.
            # Legacy campaign replacements belong only to the one-time page migration.
            root = etree.fromstring(view.arch_db.encode())
            for call in root.xpath('.//t[@t-call="website_torrepulia_theme.s_puglia_map"]'):
                map_root = etree.fromstring(self.env.ref(module + '.s_puglia_map').arch_db.encode())
                call.getparent().replace(call, etree.fromstring(etree.tostring(map_root[0])))
            view.arch_db = etree.tostring(root, encoding='unicode')
        for website in self.search([('torrepulia_theme_enabled', '=', True), ('torrepulia_campaign_version', '<', 1)]):
            home = self.env.ref(module + '.page_home')
            if home.website_id != website:
                continue
            backup = home.view_id.copy({'key': f'{module}.before_photo_campaign_{website.id}', 'arch_fs':False})
            self.env['website.page'].create({'view_id':backup.id, 'website_id':website.id,
                'url':'/torrepulia-before-photo-campaign', 'is_published':False, 'website_indexed':False})
            languages = self.env['res.lang'].search([]).mapped('code')
            for language in languages:
                view = home.view_id.with_context(lang=language)
                root = campaign_markup(etree.fromstring(view.arch_db.encode()))
                view.write({'arch_db':etree.tostring(root,encoding='unicode'), 'arch_fs':False})
            for product in website._cinematic_products():
                name = (product.torrepulia_format_name or '').lower()
                asset = 'duetto' if product.torrepulia_unit_count == 2 else 'bottle' if product.torrepulia_unit_count == 6 else 'box' if 'bag' in name else 'tin' if 'latt' in name else None
                if not asset:
                    continue
                if product.image_1920:
                    self.env['ir.attachment'].create({'name':f'Before photo campaign - {product.name}.jpg',
                        'raw':product.image_1920, 'res_model':'product.template', 'res_id':product.id, 'public':False})
                with file_open(f'{module}/static/src/cinematic/campaign/{asset}-1600.webp', 'rb') as image:
                    product.image_1920 = BinaryBytes(image.read(), filename=f'{asset}.webp')
            website.torrepulia_campaign_version = 1
