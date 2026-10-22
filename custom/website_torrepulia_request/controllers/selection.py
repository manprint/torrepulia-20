import hashlib
import hmac
import json

from odoo import http, _
from odoo.exceptions import AccessError, ValidationError, MissingError
from odoo.http import request


class RequestSelection(http.Controller):
    def _website(self):
        website = request.env.website
        key = 'torrepulia_request_%s' % website.id
        if not request.session.get(key) and website._torrepulia_selection_enabled() and website.has_ecommerce_access():
            # Same established session in parallel tabs starts with the same
            # capability. Login rotates sid but preserves this server-side value.
            secret = request.env['ir.config_parameter'].sudo().get_str('database.secret')
            request.session[key] = hmac.new(secret.encode(),
                ('torrepulia-selection:%s:%s' % (request.session.sid, website.id)).encode(),
                hashlib.sha256).hexdigest()
        return website

    def _response(self, values, status=200):
        return request.make_json_response(values, status=status, headers=[
            ('Cache-Control', 'no-store, private, max-age=0'), ('Vary', 'Cookie'),
            ('X-Content-Type-Options', 'nosniff'),
        ])

    @http.route('/torrepulia/request/current', type='http', auth='public', website=True,
                methods=['GET'], sitemap=False)
    def current(self, **kwargs):
        website = self._website()
        return self._response({'ok': True, 'csrf_token': request.csrf_token(),
                               'state': website._request_selection_state(request.session)})

    @http.route('/torrepulia/request/update', type='http', auth='public', website=True,
                methods=['POST'], csrf=True, sitemap=False)
    def update(self, payload=None, **kwargs):
        website = self._website()
        if not isinstance(payload, str) or len(payload.encode()) > 32768 or kwargs:
            return self._response({'ok': False, 'code': 'invalid', 'message': _('Operazione non valida.')}, 422)
        try:
            values = json.loads(payload)
            # Roll back the entire operation before returning a recoverable error.
            with request.env.cr.savepoint():
                result = website._request_selection_apply(request.session, values)
                if result['ok'] and values.get('operation') == 'add':
                    result['state']['addition'] = website._request_addition_details(
                        request.session, values, request.pricelist, request.fiscal_position)
            return self._response(result, 200 if result['ok'] else 409)
        except (ValueError, ValidationError, AccessError, MissingError) as error:
            message = str(error) if isinstance(error, ValidationError) else _('Prodotto o selezione non accessibile. Ricarica la selezione e riprova.')
            return self._response({'ok': False, 'code': 'invalid', 'message': message,
                                   'state': website._request_selection_state(request.session)}, 422)
