import hashlib
import hmac
import json

from odoo import http, _
from odoo.exceptions import AccessError, ValidationError, UserError, MissingError
from odoo.http import request

from .commerce import RequestCommerce
from ..models.review import ReviewValidation


class RequestReview(RequestCommerce):
    @http.route('/torrepulia/request/form', type='http', auth='public', website=True,
                methods=['GET'], sitemap=False)
    def request_form(self, layout=None, **kwargs):
        website = self._website()
        if not website._torrepulia_request_enabled():
            return request.not_found()
        partner = website._torrepulia_request_partner()
        prefill = {'contact_name': partner.name or '', 'email': partner.email or '',
                   'phone': partner.phone or ''} if partner else {}
        return self._private_page('website_torrepulia_request.review_component', {'prefill': prefill,
            'campaign_review': layout == 'campaign' and 'torrepulia_campaign_id' in website._fields})

    def _review_digest(self):
        website = request.env.website
        key = 'torrepulia_review_%s' % website.id
        if not request.session.get(key):
            # Independent of the draft's rotating selection capability. Kept
            # across native login SID rotation; never sent to the browser.
            secret = request.env['ir.config_parameter'].sudo().get_str('database.secret')
            request.session[key] = hmac.new(secret.encode(),
                ('torrepulia-review:%s:%s' % (request.session.sid, website.id)).encode(), hashlib.sha256).hexdigest()
        return hashlib.sha256(request.session[key].encode()).hexdigest()

    def _private_page(self, template, values):
        response = request.render(template, values)
        response.headers['Cache-Control'] = 'private, no-store, max-age=0'
        response.headers['Vary'] = 'Cookie'
        response.headers['Referrer-Policy'] = 'same-origin'
        return response

    @http.route()
    def summary(self, **kwargs):
        website = self._website()
        if not website._torrepulia_request_enabled():
            return super().summary(**kwargs)
        self._review_digest()
        partner = website._torrepulia_request_partner()
        prefill = {'contact_name': partner.name or '', 'email': partner.email or '', 'phone': partner.phone or ''} if partner else {}
        return self._private_page('website_torrepulia_request.review_page', {'prefill': prefill})

    @http.route()
    def preview(self, **kwargs):
        website = self._website()
        state = website._request_review_state(request.session, request.pricelist, request.fiscal_position)
        return self._response({'ok': True, 'state': state})

    @http.route('/torrepulia/request/submit', type='http', auth='public', website=True,
                methods=['POST'], csrf=True, sitemap=False)
    def submit(self, payload=None, recaptcha_token_response=None, turnstile_captcha=None, **kwargs):
        website = self._website()
        try:
            if not isinstance(payload, str) or len(payload.encode()) > 16384 or kwargs:
                raise ReviewValidation(_('Dati di invio non validi.'))
            values = json.loads(payload)
            # Any validation/CRM error rolls back the complete submission,
            # including snapshots and privacy metadata; preserve the draft.
            with request.env.cr.savepoint():
                receipt = website._request_submit_review(request.session, values, self._review_digest(),
                    request.pricelist, request.fiscal_position,
                    lambda: request.env['ir.http']._verify_request_recaptcha_token('website_form'))
            return self._response({'ok': True, 'reference': receipt['reference'],
                'replayed': receipt['replayed'], 'success_url': '/la-tua-richiesta/conferma'})
        except (ValueError, AccessError, ValidationError, UserError, MissingError) as error:
            message = str(error) if isinstance(error, (ValidationError, UserError)) else _('Invio non riuscito. Verifica la selezione e riprova.')
            return self._response({'ok': False, 'message': message,
                'fields': error.field_names if isinstance(error, ReviewValidation) else [],
                'code': 'invalid'}, 422)

    @http.route('/la-tua-richiesta/conferma', type='http', auth='public', website=True,
                methods=['GET'], sitemap=False)
    def confirmation(self, **kwargs):
        website = request.env.website
        receipt = website._request_receipt(self._review_digest())
        if not receipt:
            return request.not_found()
        return self._private_page('website_torrepulia_request.review_confirmation', {
            'receipt': receipt.public_receipt,
            'show_prices': website._torrepulia_request_prices_visible()})
