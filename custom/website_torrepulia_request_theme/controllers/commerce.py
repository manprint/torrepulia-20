from odoo import http
from odoo.http import request
from odoo.tools.misc import format_amount
from odoo.addons.website_torrepulia_theme.controllers.main import TorrepuliaPrivacy


class TorrepuliaRequestFormats(TorrepuliaPrivacy):
    @http.route()
    def formats(self, ids=None, promoted=False, exclude_template_id=None):
        # Exclusion narrows the already website-scoped native catalogue only.
        if type(exclude_template_id) is int and exclude_template_id > 0:
            request.update_context(torrepulia_exclude_template_id=exclude_template_id)
        website = request.env.website
        if not website._torrepulia_request_enabled():
            return super().formats(ids=ids, promoted=promoted)
        if not website.torrepulia_theme_enabled:
            return {'html': ''}
        ids = [int(value) for value in (ids or [])[:24] if str(value).isdigit()]
        products = website._cinematic_products(ids)
        if promoted:
            products = products[:1]
        native_prices = products._get_sales_prices(request.pricelist, request.fiscal_position, website)
        values = {'products': products, 'website': website,
                  'ribbons': {product.id: product._get_ribbon(price_vals=native_prices[product.id]) for product in products},
                  'prices': native_prices if website._torrepulia_request_prices_visible() else {},
                  'format_amount': lambda amount: format_amount(request.env, amount, request.pricelist.currency_id or website.currency_id)}
        template = ('website_torrepulia_request_theme.request_promoted' if promoted else
                    'website_torrepulia_request_theme.request_formats')
        return {'html': str(request.env['ir.ui.view']._render_template(template, values))}
