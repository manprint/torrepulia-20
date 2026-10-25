"""Launch SEO and consent: page metadata, share image, consent bar and redirects from the previous torrepulia.it.

Everything is written once and only over empty values or Odoo defaults, so a
title, description, image or redirect set by the manager always stays.
"""
import logging

from lxml import etree

from odoo import fields, models
from odoo.fields import Domain
from odoo.tools import file_open
from odoo.tools.binary import BinaryBytes

_logger = logging.getLogger(__name__)
MODULE = 'website_torrepulia_theme'

# Odoo's own placeholder descriptions, in the languages of the database.
DEFAULT_DESCRIPTIONS = {'This is the homepage of the website', 'Questa è la pagina principale del sito web'}
ORGANIZATION_DESCRIPTION = ('Azienda agricola della famiglia Leone a Torremaggiore, in Puglia: La Regina, '
                            'olio extravergine di oliva monovarietale Peranzana dai propri ulivi.')
# Shipping as the footer and the product page tell it: 24-72 working hours after one day to pack.
HANDLING_DAYS = (0, 1)
TRANSIT_DAYS = (1, 3)
# The Codice del Consumo withdrawal window, point 10 of the sales terms.
RETURN_DAYS = 14
SHOP_TITLE = 'Acquista olio extravergine Peranzana | Torrepulia'
SHOP_DESCRIPTION = ('La Regina in latta, Bag in Box e bottiglie da 500 ml: olio extravergine monovarietale '
                    'Peranzana della famiglia Leone, spedito da Torremaggiore.')

# The previous site (Odoo, same domain) as listed in its sitemap. Old product
# pages are found by internal reference; any other path keeps its own target.
OLD_PRODUCTS = {
    '/shop/olio-evo-la-regina-bag-in-box-5lt-5': 'LARGBIB5',
    '/shop/olio-evo-la-regina-conf-6-bottiglie-da-500ml-2': 'LARG6BT500',
    '/shop/olio-evo-la-regina-duetto-2-bottiglie-500ml-3': 'LARG2BT500',
    '/shop/olio-evo-la-regina-lattina-5-litri-4': 'LARGLAT5',
}
OLD_PAGES = {
    '/home': '/',
    '/blog': '/',
    '/blog/viaggi-1': '/',
    '/blog/viaggi-1/feed': '/',
    '/pwa/offline': '/',
    '/brand-listing': '/shop',
    '/shop/category/bag-in-box-2': '/shop',
    '/shop/category/bottiglia-3': '/shop',
    '/livechat': '/contactus',
    '/livechat/channel/torrepulia-com-1': '/contactus',
}


def _set_meta(record, field, value, replaceable=()):
    """Write a translated SEO field in every language where it is still empty or a default."""
    for code, _name in record.env['res.lang'].get_installed():
        localized = record.with_context(lang=code)
        current = (localized[field] or '').strip()
        if not current or current in replaceable:
            localized[field] = value


class Website(models.Model):
    _inherit = 'website'

    torrepulia_meta_pixel_id = fields.Char('Meta Pixel', help='Loaded only after consent in the cookie bar.')

    def _torrepulia_launch_seo(self):
        """Home and shop metadata, share image, indexed home, consent bar, 301s from the old site."""
        self.ensure_one()
        with file_open(MODULE + '/data/pages.xml', 'rb') as source:
            home = etree.parse(source).getroot().find('page[@key="home"]')
        # The page Odoo serves at "/" (as in website.page._get_page_info): url is translated,
        # so look it up in the website language; a website page wins over a generic one.
        pages = self.env['website.page'].with_context(lang=self.default_lang_id.code or 'en_US')
        page = pages.browse(list(pages._search(Domain('url', '=ilike', '/') & self.website_domain(),
                                               order='website_id asc', limit=1)))
        if page:
            # A home without index would keep the whole site out of search results.
            page.website_indexed = True
            _set_meta(page.view_id, 'website_meta_title', home.get('title'))
            _set_meta(page.view_id, 'website_meta_description', home.get('description'), DEFAULT_DESCRIPTIONS)

        # /shop takes its title from the view name ("Products"): set it on this website's copy.
        shop = self.with_context(website_id=self.id).viewref('website_sale.products')
        if not shop.website_id:
            shop.with_context(website_id=self.id).write({'website_meta_title': False})
            shop = self.with_context(website_id=self.id).viewref('website_sale.products')
        _set_meta(shop, 'website_meta_title', SHOP_TITLE)
        _set_meta(shop, 'website_meta_description', SHOP_DESCRIPTION)

        # Consent bar before any analytics: GA4 and the Meta Pixel follow its choice.
        self.cookies_bar = True

        if not self.social_default_image:
            with file_open(MODULE + '/static/src/img/content/torrepulia-condivisione.jpg', 'rb') as image:
                self.social_default_image = BinaryBytes(image.read(), filename='torrepulia-condivisione.jpg')

        targets = dict(OLD_PAGES)
        # Odoo's placeholder privacy page duplicates the real policy: out of the index, redirected.
        placeholder = self.env['website.page'].search([('url', '=', '/privacy'), ('website_id', 'in', [self.id, False])])
        if placeholder and self.env['website.page'].search_count([('url', '=', '/privacy-policy'), ('website_id', 'in', [self.id, False])]):
            placeholder.write({'website_indexed': False, 'is_published': False})
            targets['/privacy'] = '/privacy-policy'
        for path, code in OLD_PRODUCTS.items():
            targets[path] = self._torrepulia_old_product_url(code)
        rewrites = self.env['website.rewrite']
        existing = set(rewrites.search([('website_id', 'in', [self.id, False])]).mapped('url_from'))
        rewrites.create([{
            'name': 'torrepulia.it precedente: %s' % path, 'url_from': path, 'url_to': target,
            'redirect_type': '301', 'website_id': self.id,
        } for path, target in targets.items() if path not in existing])
        _logger.info('Torrepulia SEO: %s redirects from the previous site', len(set(targets) - existing))

    def _torrepulia_old_product(self, code):
        """Product template with this internal reference, read with this website's addresses."""
        self.ensure_one()
        env = self.with_context(website_id=self.id).env
        return (env['product.template'].search([('default_code', '=ilike', code)], limit=1)
                or env['product.product'].search([('default_code', '=ilike', code)], limit=1).product_tmpl_id)

    def _torrepulia_old_product_url(self, code):
        template = self._torrepulia_old_product(code)
        return template.website_url if template else '/shop'

    def _torrepulia_refresh_product_redirects(self):
        """Our redirects to a product page follow its address without the internal reference.

        Only a target still on the same product is updated: another target set by the manager stays.
        """
        self.ensure_one()
        rewrites = self.env['website.rewrite'].search([
            ('website_id', '=', self.id), ('url_from', 'in', list(OLD_PRODUCTS))])
        for rewrite in rewrites:
            template = self._torrepulia_old_product(OLD_PRODUCTS[rewrite.url_from])
            if (template and (rewrite.url_to or '').startswith('/shop/')
                    and rewrite.url_to.endswith('-%s' % template.id)):
                rewrite.url_to = template.website_url

    def _torrepulia_llms_txt(self):
        """Odoo's /llms.txt from the theme's text, written once: the manager edits it in the settings."""
        self.ensure_one()
        if (self.llms_txt or '').strip():
            return
        with file_open(MODULE + '/data/llms.txt', 'r') as source:
            text = source.read()
        company = self._torrepulia_footer_company()
        shipping = self.with_context(lang=self.default_lang_id.code).torrepulia_shipping_note
        contacts = [line for line in (
            company['name'],
            ', '.join(filter(None, [company['street'], company['locality']])),
            company['email'] and 'Email: %s' % company['email'],
            company['phone'] and 'Telefono: %s' % company['phone'],
        ) if line]
        self.llms_txt = text.format(
            base=self.get_base_url(),
            # The note usually opens with "Spedizione gratuita…": no label in front of it then.
            shipping=('- %s\n' if shipping.lower().startswith('spedizion') else '- Spedizione: %s\n') % shipping
            if shipping else '',
            contacts='\n## Contatti\n\n' + ''.join('- %s\n' % line for line in contacts) if contacts else '',
        )

    def _prepare_jsonld_vals(self):
        # Odoo describes the organization by name and logo only: add what the company record knows.
        vals = super()._prepare_jsonld_vals()
        if not self.torrepulia_theme_enabled:
            return vals
        company = self.company_id.sudo()
        extra = {
            'legalName': company.name,
            'description': ORGANIZATION_DESCRIPTION,
            'email': company.email,
            'telephone': company.phone,
            'address': self._build_postaladdress_jsonld_vals(company.partner_id),
            'sameAs': [company[field] for field, _label, _icon in self.TORREPULIA_SOCIALS if company[field]],
            # One policy for the whole shop: Google reads it from the organization for every product.
            'hasMerchantReturnPolicy': {
                '@type': 'MerchantReturnPolicy',
                'applicableCountry': company.country_id.code or 'IT',
                'returnPolicyCategory': 'https://schema.org/MerchantReturnFiniteReturnWindow',
                'merchantReturnDays': RETURN_DAYS,
                'returnMethod': 'https://schema.org/ReturnByMail',
            },
        }
        vals.update({key: value for key, value in extra.items() if value})
        return vals

    def _torrepulia_shipping_carrier(self):
        """The published fixed-price carrier of the checkout, for the shipping cost of the markup."""
        self.ensure_one()
        return self.env['delivery.carrier'].sudo().search([
            ('delivery_type', '=', 'fixed'), ('is_published', '=', True),
            ('website_id', 'in', [self.id, False]), ('company_id', 'in', [self.company_id.id, False]),
        ], limit=1)

    def _torrepulia_shipping_jsonld(self, price, preorder=False):
        """Shipping cost of one product as the checkout computes it, free over the carrier threshold."""
        self.ensure_one()
        carrier = self._torrepulia_shipping_carrier()
        if not carrier:
            return False
        free = carrier.free_over and price >= carrier.amount
        details = {
            '@type': 'OfferShippingDetails',
            'shippingRate': {'@type': 'MonetaryAmount', 'value': 0 if free else carrier.fixed_price,
                             'currency': self.currency_id.name},
            'shippingDestination': [{'@type': 'DefinedRegion', 'addressCountry': code}
                                    for code in (carrier.country_ids.mapped('code') or ['IT'])],
        }
        # A reservation leaves after the milling: no delivery time to promise yet.
        if not preorder:
            details['deliveryTime'] = {
                '@type': 'ShippingDeliveryTime',
                'handlingTime': {'@type': 'QuantitativeValue', 'minValue': HANDLING_DAYS[0],
                                 'maxValue': HANDLING_DAYS[1], 'unitCode': 'DAY'},
                'transitTime': {'@type': 'QuantitativeValue', 'minValue': TRANSIT_DAYS[0],
                                'maxValue': TRANSIT_DAYS[1], 'unitCode': 'DAY'},
            }
        return details

    def _enumerate_pages(self, query_string=None, force=False, ignore_custom_homepage=False):
        # The sitemap leaves out the categories carrying noindex (views/shop_templates.xml).
        # Link search in the Builder (query_string) still lists them.
        pages = super()._enumerate_pages(query_string, force, ignore_custom_homepage)
        if query_string or not self.torrepulia_theme_enabled:
            yield from pages
            return
        for page in pages:
            path = page['loc'].split('/shop/category/', 1)
            if len(path) == 2:
                _name, category_id = self.env['ir.http']._unslug(path[1].split('/', 1)[0])
                if category_id and self._torrepulia_thin_category(self.env['product.public.category'].browse(category_id)):
                    continue
            yield page

    def _torrepulia_thin_category(self, category):
        """A shop category listing one product at most: its page repeats the product page."""
        self.ensure_one()
        if not self.torrepulia_theme_enabled or not category:
            return False
        return self.env['product.template'].search_count(
            Domain(self.sale_product_domain()) & Domain('public_categ_ids', 'child_of', category.id), limit=2) < 2


def _product_description(template):
    return '%s: olio extravergine monovarietale Peranzana della famiglia Leone, da Torremaggiore.' % template.name


def _product_jsonld(vals, template, website):
    """Brand and a description for the product markup, as on the page itself."""
    if website.torrepulia_theme_enabled:
        vals.setdefault('description', template.description_sale or _product_description(template))
        vals.setdefault('brand', {'@type': 'Brand', 'name': website.name})
    return vals


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    torrepulia_meta_pixel_id = fields.Char(related='website_id.torrepulia_meta_pixel_id', readonly=False)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _default_website_meta(self):
        # Without a sales description Odoo leaves product pages with no description at all.
        res = super()._default_website_meta()
        if not self.description_sale and self.env.website.torrepulia_theme_enabled:
            description = _product_description(self)
            res['default_opengraph']['og:description'] = description
            res['default_meta_description'] = description
        return res

    def _prepare_jsonld_vals(self):
        vals = super()._prepare_jsonld_vals()
        website = self.env.website or self.env['website'].browse(self.env.context.get('host_id'))
        return _product_jsonld(vals, self, website)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _prepare_jsonld_vals(self, **kwargs):
        vals = super()._prepare_jsonld_vals(**kwargs)
        website = self.env.website or self.env['website'].browse(self.env.context.get('host_id'))
        if website.torrepulia_theme_enabled and (offer := vals.get('offers')):
            # Odoo says OutOfStock for a format of the open campaign: it is reserved, not sold out.
            preorder = bool(website._torrepulia_format_preorder(self))
            if preorder:
                offer['availability'] = 'https://schema.org/PreOrder'
            if shipping := website._torrepulia_shipping_jsonld(offer.get('price') or 0, preorder):
                offer['shippingDetails'] = shipping
        return _product_jsonld(vals, self.product_tmpl_id, website)


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    def _default_website_meta(self):
        # Odoo leaves shop categories without a description: say what the format is.
        res = super()._default_website_meta()
        if self.env.website.torrepulia_theme_enabled:
            description = ('%s: La Regina, olio extravergine monovarietale Peranzana della famiglia Leone, '
                           'spedito da Torremaggiore.' % self.name)
            res['default_opengraph']['og:description'] = description
            res['default_meta_description'] = description
        return res


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _slug(cls, value):
        # The product addresses carry the name only, not the internal reference ("larg6bt500-…").
        if (isinstance(value, models.BaseModel) and value._name in ('product.template', 'product.product')
                and value.env.website.torrepulia_theme_enabled):
            value = value.with_context(display_default_code=False)
        return super()._slug(value)
