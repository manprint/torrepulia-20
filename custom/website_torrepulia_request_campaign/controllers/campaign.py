import json
from time import time

from odoo import http, fields, _
from odoo.fields import Domain
from odoo.http import request
from odoo.tools.misc import format_amount
from odoo.addons.website_torrepulia_theme.controllers.reservation import TorrepuliaReservationForm, QUANTITIES
from odoo.addons.website_torrepulia_request.controllers.review import RequestReview


class SeasonalCampaign(http.Controller):
    @http.route('/torrepulia/campaign/submit', type='http', auth='public', website=True,
                methods=['POST'], csrf=True, sitemap=False)
    def submit(self, payload=None, recaptcha_token_response=None, turnstile_captcha=None, **kwargs):
        # This entry point tightens the seasonal form's contact requirements;
        # native request ownership, replay protection and atomic CRM creation stay shared.
        try:
            values = json.loads(payload) if isinstance(payload, str) and len(payload.encode()) <= 16384 else {}
        except (ValueError, TypeError):
            values = {}
        # The order confirmation ships the oil: the reservation needs the full address.
        missing = [name for name in ('phone', 'street', 'zip', 'city', 'state_code')
                   if not isinstance(values, dict) or not isinstance(values.get(name), str) or not values[name].strip()]
        if missing:
            return RequestReview()._response({'ok': False, 'code': 'invalid',
                'message': _('Compila telefono e indirizzo di spedizione per completare la prenotazione.'), 'fields': missing}, 422)
        return RequestReview().submit(payload=payload, recaptcha_token_response=recaptcha_token_response,
                                      turnstile_captcha=turnstile_captcha, **kwargs)

    @http.route('/richiesta-inviata', type='http', auth='public', website=True,
                methods=['GET'], sitemap=False)
    def legacy_receipt(self, **kwargs):
        website = request.env.website
        if not website.torrepulia_theme_enabled:
            return request.env['ir.http']._serve_page() or request.not_found()
        if website._request_receipt(RequestReview()._review_digest()):
            response = request.redirect('/la-tua-richiesta/conferma', code=303)
        else:
            received_at = request.session.get('torrepulia_contact_received_%s' % website.id)
            recent_contact = (type(received_at) in (float, int)
                              and 0 <= time() - received_at < 900)
            # Preserve the stored page's indexing choice without rendering its
            # former success content. Native lookup resolves the current site.
            pages = request.env['website.page'].sudo()
            info = pages._get_page_info(request)
            legacy_no_index = bool(info and not pages.browse(info['id']).website_indexed)
            response = request.render('website_torrepulia_request_campaign.legacy_receipt', {
                'recent_contact': recent_contact,
                'legacy_no_index': legacy_no_index,
                'summary_url': website._torrepulia_request_url() if website._torrepulia_selection_enabled() else '/shop'})
        response.headers['Cache-Control'] = 'private, no-store, max-age=0'
        response.headers['Vary'] = 'Cookie'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response

    @http.route('/torrepulia/campaign/content', type='http', auth='public', website=True, methods=['GET'], sitemap=False)
    def content(self, campaign_id=None, demo=None, **kwargs):
        website = request.env.website
        editing = demo == '1'
        if editing and not request.env.user.has_group('website.group_website_restricted_editor'):
            return request.make_json_response({'error': _('Anteprima non autorizzata.')}, status=403)
        try:
            selected = int(campaign_id) if campaign_id else None
        except (ValueError, TypeError):
            return request.make_json_response({'error': _('Campagna non valida.')}, status=422)
        campaign = website._public_request_campaign(selected)
        now = fields.Datetime.now()
        transitions = [value for value in (campaign.opens_at, campaign.closes_at) if value and value > now] if campaign else []
        opened = bool(campaign and campaign._is_open() and website._torrepulia_selection_enabled())
        cards = []
        configurations = []
        if campaign:
            ids = campaign.line_ids.product_id.ids
            products = request.env['product.product'].search(
                Domain('id', 'in', ids) & Domain('product_tmpl_id', 'in',
                    request.env['product.template'].search(website.sale_product_domain() &
                        Domain('id', 'in', campaign.line_ids.product_id.product_tmpl_id.ids) &
                        Domain('is_published', '=', True)).ids))
            by_id = {product.id: product for product in products}
            configurations = [{'product_id': product.id, 'uom_id': product.uom_id.id} for product in products]
        if campaign and (opened or editing):
            by_template = {}
            for line in campaign.line_ids.sorted(lambda row: (row.sequence, row.id)):
                product = by_id.get(line.product_id.id)
                if not product:
                    continue
                template = product.product_tmpl_id
                can_set = (template.type != 'combo' and
                           not template.valid_product_template_attribute_line_ids.filtered(
                               lambda attr: attr.attribute_id.create_variant == 'no_variant'))
                # One card per format; each campaign variant (Filtrato, Non filtrato) is a counter in it.
                card = by_template.get(template.id)
                if not card:
                    card = by_template[template.id] = {
                        'product': product, 'name': template.torrepulia_format_name or template.name,
                        'content': line.content or template.torrepulia_shop_audience or '',
                        'description': line.description or '',
                        'price': None, 'reference_price': None, 'reference_unit': '', 'choices': []}
                    cards.append(card)
                choice = {'product': product, 'label': ', '.join(product.product_template_attribute_value_ids.mapped('name')),
                          'config': json.dumps({'product_id': product.id, 'uom_id': product.uom_id.id}),
                          'can_set': can_set, 'unit_price': None, 'price': None}
                if website._torrepulia_request_prices_visible() and not editing:
                    info = template._get_combination_info(combination=product.product_template_attribute_value_ids,
                        product_id=product.id, add_qty=1, pricelist=request.pricelist, fiscal_position=request.fiscal_position)
                    if not info.get('hide_price'):
                        currency = info['currency']
                        choice['unit_price'] = info['price']
                        choice['price'] = format_amount(request.env, info['price'], currency)
                        card['currency'] = currency.name
                        if not card['price']:
                            card['price'] = choice['price']
                            if info.get('base_unit_price') and info.get('base_unit_name'):
                                card['reference_price'] = format_amount(request.env, info['base_unit_price'], currency)
                                card['reference_unit'] = info['base_unit_name']
                card['choices'].append(choice)
            for card in cards:
                # A single price for the format unless its variants are priced differently.
                card['same_price'] = len({choice['price'] for choice in card['choices']}) == 1
        values = {'campaign': campaign, 'cards': cards, 'opened': opened, 'editing': editing,
                  'summary_url': website._torrepulia_request_url(), 'website': website}
        rendered = request.env['ir.ui.view']._render_template('website_torrepulia_request_campaign.campaign_content', values)
        response = request.make_json_response({'html': str(rendered),
            'configurations': configurations,
            'refresh_after': max(1, int((min(transitions) - now).total_seconds()) + 1) if transitions else None,
            'campaign_reference': campaign.reference if campaign else None,
            'open': opened, 'summary_url': website._torrepulia_request_url()})
        response.headers['Cache-Control'] = 'private, no-store'
        return response


class RetiredReservation(TorrepuliaReservationForm):
    @http.route()
    def website_form(self, model_name, **kwargs):
        # The native handler commits the actual record before returning.
        # Mint only a short-lived, website-scoped acknowledgement, never a
        # public record ID or permission to read CRM/customer data.
        result = super().website_form(model_name, **kwargs)
        if model_name == 'crm.lead' and request.env.website.torrepulia_theme_enabled:
            key = 'torrepulia_contact_received_%s' % request.env.website.id
            request.session.pop(key, None)
            try:
                # Odoo 20's @route wrapper normalises HTTP super calls to
                # Response objects, even when the handler returns JSON text.
                value = json.loads(result.get_data(as_text=True))
            except (ValueError, TypeError):
                value = None
            if isinstance(value, dict) and type(value.get('id')) is int and value['id'] > 0:
                request.session[key] = time()
        return result

    def _handle_website_form(self, model_name, **kwargs):
        if (model_name == 'crm.lead' and request.env.website.torrepulia_theme_enabled and
                (kwargs.get('torrepulia_reservation') or any(key in kwargs for key in QUANTITIES)
                 or str(kwargs.get('name', '')).startswith('Prenotazione olio nuovo'))):
            return json.dumps({'error': _('Il vecchio modulo è stato sostituito. Rivedi e invia la richiesta dalla pagina La tua richiesta.')})
        return super()._handle_website_form(model_name, **kwargs)
