from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import cart_count_for_the_cache


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Visitors with a cart got a 500 on the cached pages: the header copies get Odoo's counter.
    cart_count_for_the_cache(env)
