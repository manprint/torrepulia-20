from odoo import http
from odoo.http import request

from odoo.addons.account.controllers.terms import TermsController

TERMS_URL = '/termini-e-condizioni'


class TorrepuliaTerms(TermsController):
    # Checkout and quotations link to /terms, which shows the company's invoice
    # terms (an English Odoo boilerplate by default). The sales terms of the
    # website are its own page: one address only, also for search engines.
    @http.route(sitemap=False)
    def terms_conditions(self, **kwargs):
        website = request.env.website
        if website.torrepulia_theme_enabled and request.env['website.page'].sudo().search_count(
                [('url', '=', TERMS_URL), ('website_id', 'in', [website.id, False])], limit=1):
            return request.redirect(TERMS_URL, code=301)
        return super().terms_conditions(**kwargs)
