from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.website_sale.controllers.sale import CustomerPortal


class RequestCheckoutPortal(CustomerPortal):
    def _suspended_portal_cart(self, order_id, access_token):
        # Authenticate with the native document check before inspecting origin.
        # Invalid tokens keep the native error path and reveal no cart details.
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return self.env['sale.order']
        return order._torrepulia_suspended_catalog_carts()

    @http.route()
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        if self._suspended_portal_cart(order_id, access_token):
            # Do not store a signature or invoke native PDF/email processing.
            # Keep native signature/payment predicates intact for transactions
            # already in progress and genuine commercial quotations.
            return {'error': _('Il checkout del carrello è sospeso. Rivolgiti al commerciale per un preventivo.')}
        return super().portal_quote_accept(order_id, access_token=access_token, name=name, signature=signature)

    @http.route()
    def portal_quote_decline(self, order_id, access_token=None, decline_message=None, **kwargs):
        if cart := self._suspended_portal_cart(order_id, access_token):
            return request.redirect(cart.website_id._torrepulia_request_url(), code=303)
        return super().portal_quote_decline(order_id, access_token=access_token,
                                           decline_message=decline_message, **kwargs)
