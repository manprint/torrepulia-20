from urllib.parse import urlsplit

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import Website


class TorrepuliaCrawlers(Website):
    # robots.txt and the sitemap write the address of the request, not the website
    # domain. Behind a proxy that does not forward the scheme (or without
    # proxy_mode), Odoo sees http:// and tells search engines http:// addresses
    # that only redirect. The domain set on the website is the address to publish.

    def _torrepulia_https_root(self, response):
        website = request.env.website
        domain = urlsplit(website.domain or '')
        seen = request.httprequest.url_root.rstrip('/')
        if (website.torrepulia_theme_enabled and domain.scheme == 'https'
                and urlsplit(seen).scheme == 'http' and urlsplit(seen).netloc == domain.netloc):
            response.set_data(response.get_data().replace(
                seen.encode() + b'/', ('https://%s/' % domain.netloc).encode()))
        return response

    @http.route()
    def robots(self, **kwargs):
        response = super().robots(**kwargs)
        # Rendered lazily: render now to rewrite the text.
        if hasattr(response, 'flatten'):
            response.flatten()
        return self._torrepulia_https_root(response)

    @http.route()
    def sitemap_xml_index(self, **kwargs):
        return self._torrepulia_https_root(super().sitemap_xml_index(**kwargs))
