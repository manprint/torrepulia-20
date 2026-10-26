from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import recopy_cookie_policy


def migrate(cr, version):
    # The cookie policy lists the cookies the site sets, GA4 and the Meta Pixel included.
    recopy_cookie_policy(api.Environment(cr, SUPERUSER_ID, {}))
