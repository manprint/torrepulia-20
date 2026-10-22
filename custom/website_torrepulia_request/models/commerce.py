from urllib.parse import urlsplit
from lxml import html

from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.fields import Domain


def public_storefront():
    # Some editor requests are marked frontend but carry no website (e.g.
    # after saving a view). They are not public storefront responses.
    return bool(request and request.is_frontend and request.env.website and not request.httprequest.path.startswith(
        ('/my/', '/web/', '/report/', '/payment/')))


class Website(models.Model):
    _inherit = 'website'

    def _request_preorder_url(self):
        """Optional seasonal integration; the base addon never assumes an open campaign."""
        self.ensure_one()
        return False

    def _create_cart(self):
        if self._torrepulia_request_enabled():
            raise ValidationError(_('Usa Aggiungi alla richiesta per selezionare i prodotti.'))
        return super()._create_cart()

    def _request_catalog_template(self, template_id):
        self.ensure_one()
        if not self._torrepulia_request_enabled() or not self.has_ecommerce_access():
            raise ValidationError(_('Il catalogo richieste non è accessibile.'))
        if isinstance(template_id, bool) or not isinstance(template_id, int):
            raise ValidationError(_('Prodotto non valido.'))
        product = self.env['product.template'].search(
            self.sale_product_domain() & Domain('id', '=', template_id) & Domain('is_published', '=', True), limit=1)
        if not product:
            raise ValidationError(_('Prodotto non accessibile nel catalogo corrente.'))
        return product


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _request_stock_notice(self, website):
        """Project configured HTML into copy and semantic links, without saved inline styling."""
        self.ensure_one()
        root = html.fragment_fromstring(str(self.out_of_stock_message or ''), create_parent='div')
        local_hosts = {urlsplit(website.get_base_url()).netloc}
        if request and request.env.website == website:
            local_hosts.add(request.httprequest.host)
        links = []
        for anchor in list(root.iter('a')):
            href = (anchor.get('href') or '').strip()
            target = urlsplit(href)
            label = ' '.join(anchor.text_content().split())
            if (not target.netloc or target.netloc in local_hosts) and target.path.rstrip('/') == '/prenotailtuoolio':
                anchor.drop_tree()
            elif href and target.scheme in ('', 'http', 'https', 'mailto', 'tel'):
                links.append({'url': href, 'label': label or href})
                anchor.drop_tree()
        # Preserve paragraph breaks without html2plaintext's Markdown emphasis
        # markers, which would otherwise appear literally in the storefront.
        for node in root.iter():
            if node is not root and node.tag in ('br', 'p', 'div', 'li', 'section'):
                node.tail = '\n' + (node.tail or '')
        message = '\n'.join(' '.join(line.split()) for line in root.text_content().splitlines() if line.strip())
        return {'message': message, 'links': links,
                'preorder_url': website._request_preorder_url()}

    def _request_inline_variants(self):
        """Only existing, complete native variants; complex configurators stay explicit."""
        self.ensure_one()
        lines = self.valid_product_template_attribute_line_ids
        if (self.type == 'combo' or len(self._get_available_uoms()) > 1
                or not lines or any(line.attribute_id.create_variant != 'always' for line in lines)
                or len(self.product_variant_ids) > 12):
            return self.env['product.product']
        return self.product_variant_ids.filtered(lambda product: product.active and
            self._is_combination_possible(product.product_template_attribute_value_ids))

    def _request_needs_configuration(self):
        self.ensure_one()
        return bool(self.product_variant_count != 1 or self.valid_product_template_attribute_line_ids
                    or len(self._get_available_uoms()) > 1 or self.type == 'combo')

    def _get_combination_info(self, *args, **kwargs):
        info = super()._get_combination_info(*args, **kwargs)
        website = public_storefront() and self.env.website
        # Seasonal products carry their own preorder action instead of a stock notice.
        if (website and website._torrepulia_selection_enabled()
                and info.get('is_storable') and not info.get('allow_out_of_stock_order')
                and not website._torrepulia_preorder_product_url(self)):
            info['tp_request_stock_notice'] = self._request_stock_notice(self.env.website)
        return info

    def _search_render_results_prices(self, mapping, combination_info):
        if public_storefront() and not self.env.website._torrepulia_request_prices_visible():
            return ''
        return super()._search_render_results_prices(mapping, combination_info)
