from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import original_oil_colours


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # The oil clip and the bottling back to the phone's original colours.
    original_oil_colours(env)
