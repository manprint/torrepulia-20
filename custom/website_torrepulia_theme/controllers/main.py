from lxml import html

from odoo import http
from odoo.http import request
from odoo.tools import is_html_empty
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
        availability = {}
        for product in products:
            # Use the installed product-page API, including website warehouse, UoM,
            # current cart, minimum quantity and the sell-out-of-stock setting.
            multiple = product.product_variant_count != 1
            info = product.with_context(website_sale_product_page=True)._get_combination_info(
                only_template=multiple,
                pricelist=request.pricelist,
                fiscal_position=request.fiscal_position,
            )
            remaining = info.get('free_qty', 0)
            if not info.get('allow_out_of_stock_order'):
                remaining = max(0, remaining - int(info.get('cart_qty', 0)))
                if remaining < info.get('minimum_qty', 0):
                    remaining = 0
            sold_out = product._is_sold_out() if multiple else (
                info.get('is_storable', False)
                and not info.get('allow_out_of_stock_order') and remaining < 1
            )
            message = info.get('out_of_stock_message')
            availability[product.id] = {
                'info': info,
                'remaining': remaining,
                'blocked': sold_out or info['prevent_sale'] or (
                    not multiple and not info['is_combination_possible']
                ),
                # A template may have both sold-out and available variants: leave
                # its configurator reachable and never sum quantities across them.
                'show_stock': not multiple and info.get('is_storable') and not info['prevent_sale'],
                'has_message': not is_html_empty(message),
                # Compact list label: copy only, without Markdown-style link footnotes.
                'message_text': ' '.join(html.fromstring(str(message)).text_content().split()) if not is_html_empty(message) else '',
                'ribbon': product._get_ribbon(price_vals=prices[product.id]),
                # Same state and price per litre as the shop rows.
                'preorder': website._torrepulia_format_preorder(product),
                'sold_out': sold_out,
            }
            unit = product._get_combination_info(product_id=product.product_variant_id.id,
                pricelist=request.pricelist, fiscal_position=request.fiscal_position)
            if not unit.get('hide_price') and unit.get('base_unit_price') and unit.get('base_unit_name'):
                availability[product.id]['unit_price'] = '%s / %s' % (
                    format_amount(request.env, unit['base_unit_price'], currency), unit['base_unit_name'])
        values = {'products':products,'prices':prices,'currency':currency,
            'availability': availability, 'season': website._torrepulia_preorder_season(),
            'format_amount':lambda amount:format_amount(request.env,amount,currency)}
        template = 'website_torrepulia_theme.cinematic_promoted' if promoted else 'website_torrepulia_theme.cinematic_formats'
        return {'html':str(request.env['ir.ui.view']._render_template(template,values))}

    @http.route('/privacy', type='http', auth='public', website=True, sitemap=False)
    def privacy(self, **kwargs):
        # A real generic page is served before website.rewrite in Odoo's fallback.
        if request.env.website.torrepulia_theme_enabled:
            return request.redirect('/privacy-policy', code=301)
        return request.env['ir.http']._serve_page() or request.not_found()
