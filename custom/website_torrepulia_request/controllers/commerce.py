import json

from odoo import http, _
from odoo.exceptions import ValidationError, AccessError
from odoo.http import request
from odoo.tools.misc import format_amount
from odoo.addons.website_sale.controllers.cart import Cart

from .selection import RequestSelection


class RequestCommerce(RequestSelection):
    @http.route('/torrepulia/request/product', type='http', auth='public', website=True, methods=['GET'], sitemap=False)
    def product(self, template_id=None, **kwargs):
        try:
            product = request.env.website._request_catalog_template(int(template_id))
            return self._response({'name': product.with_context(display_default_code=False).display_name,
                                   'url': product.website_url, 'product_id': product.product_variant_id.id,
                                   'uom_id': product.uom_id.id,
                                   'requires_configuration': product._request_needs_configuration()})
        except (ValueError, TypeError, ValidationError, AccessError):
            return self._response({'error': _('Prodotto non accessibile.')}, 422)

    @http.route('/torrepulia/request/resolve', type='http', auth='public', website=True, methods=['POST'], csrf=True, sitemap=False)
    def resolve(self, payload=None, **kwargs):
        try:
            if not isinstance(payload, str) or len(payload) > 16384 or kwargs:
                raise ValidationError(_('Configurazione non valida.'))
            data = json.loads(payload)
            if not isinstance(data, dict) or set(data) - {'template_id', 'ptav_ids'}:
                raise ValidationError(_('Configurazione non valida.'))
            product = request.env.website._request_catalog_template(data.get('template_id'))
            ids = data.get('ptav_ids')
            if not isinstance(ids, list) or len(ids) > 100 or any(type(value) is not int or value <= 0 for value in ids):
                raise ValidationError(_('Attributi non validi.'))
            values = request.env['product.template.attribute.value'].browse(ids)
            valid = product.valid_product_template_attribute_line_ids.product_template_value_ids
            if values - valid or not product._is_combination_possible(values):
                raise ValidationError(_('Seleziona una combinazione valida.'))
            # Native Odoo variant creation is limited to this accessible template
            # and explicitly selected native values; no order or pricing override.
            with request.env.cr.savepoint():
                variant_id = product.create_product_variant(ids)
                if not variant_id:
                    raise ValidationError(_('La variante selezionata non è disponibile.'))
            return self._response({'product_id': variant_id})
        except (ValueError, ValidationError, AccessError):
            return self._response({'error': _('Seleziona una configurazione valida per questo prodotto.')}, 422)

    @http.route('/la-tua-richiesta', type='http', auth='public', website=True, methods=['GET'], sitemap=False)
    def summary(self, **kwargs):
        website = request.env.website
        if not website._torrepulia_request_enabled():
            return request.env['ir.http']._serve_page() or request.not_found()
        return request.render('website_torrepulia_request.selection_summary')

    @http.route('/torrepulia/request/preview', type='http', auth='public', website=True, methods=['GET'], sitemap=False)
    def preview(self, **kwargs):
        website = self._website()
        state = website._request_selection_state(request.session)
        draft = website._torrepulia_session_request(request.session)
        if draft and state['show_prices']:
            total = 0
            currency = request.pricelist.currency_id or website.currency_id
            for item in state['lines']:
                if not item['available']:
                    continue
                line = draft.line_ids.filtered(lambda row: row._configuration_key() == item['key'])[:1]
                product = line.product_id.with_env(website.env)
                info = product.product_tmpl_id._get_combination_info(
                    combination=product.product_template_attribute_value_ids | line.no_variant_value_ids.with_env(website.env),
                    product_id=product.id, add_qty=item['quantity'], uom_id=line.uom_id.id,
                    pricelist=request.pricelist, fiscal_position=request.fiscal_position)
                subtotal = currency.round(info['price'] * item['quantity'])
                item['price_display'] = format_amount(request.env, info['price'], currency)
                item['subtotal_display'] = format_amount(request.env, subtotal, currency)
                total += subtotal
            state['products_total_display'] = format_amount(request.env, total, currency)
        return self._response({'ok': True, 'state': state})


class RequestCartGuard(Cart):
    def _check_request_mode(self):
        if request.env.website._torrepulia_request_enabled():
            raise ValidationError(_('Il website raccoglie richieste di preventivo. Usa Aggiungi alla richiesta.'))

    @http.route()
    def add_to_cart(self, *args, **kwargs):
        self._check_request_mode()
        return super().add_to_cart(*args, **kwargs)

    @http.route()
    def quick_add(self, *args, **kwargs):
        self._check_request_mode()
        return super().quick_add(*args, **kwargs)

    @http.route()
    def update_cart(self, *args, **kwargs):
        self._check_request_mode()
        return super().update_cart(*args, **kwargs)

    @http.route()
    def cart(self, **kwargs):
        if request.env.website._torrepulia_request_enabled():
            return request.redirect(request.env.website._torrepulia_request_url())
        return super().cart(**kwargs)
