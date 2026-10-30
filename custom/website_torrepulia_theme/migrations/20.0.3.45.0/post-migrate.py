from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import swap_regina_bottle


def migrate(cr, version):
    # La Regina on the saved home shows the new studio bottle.
    swap_regina_bottle(api.Environment(cr, SUPERUSER_ID, {}))
