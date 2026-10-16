from odoo import http
from odoo.http import request
from odoo.tools.misc import format_amount


class TorrepuliaPrivacy(http.Controller):
    @http.route('/torrepulia/formats', type='jsonrpc', auth='public', website=True)
    def formats(self, ids=None, promoted=False):
        website = request.env.website
        if not website.torrepulia_theme_enabled:
            return {'html':''}
        ids = [int(i) for i in (ids or [])[:24] if str(i).isdigit()]
        products = website._cinematic_products(ids)
        if promoted:
            products = products[:1]
        prices = products._get_sales_prices(request.pricelist, request.fiscal_position, website)
        # Odoo 20 deliberately returns an empty pricelist when that feature is disabled.
        # Its native sales-price API already computes amounts in the website currency.
        currency = website.currency_id
        values = {'products':products,'prices':prices,'currency':currency,
            'format_amount':lambda amount:format_amount(request.env,amount,currency)}
        template = 'website_torrepulia_theme.cinematic_promoted' if promoted else 'website_torrepulia_theme.cinematic_formats'
        return {'html':str(request.env['ir.ui.view']._render_template(template,values))}

    @http.route('/privacy', type='http', auth='public', website=True, sitemap=False)
    def privacy(self, **kwargs):
        # A real generic page is served before website.rewrite in Odoo's fallback.
        if request.env.website.torrepulia_theme_enabled:
            return request.redirect('/privacy-policy', code=301)
        return request.env['ir.http']._serve_page() or request.not_found()
