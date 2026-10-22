from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.product_image import normalize_existing


def migrate(cr, version):
    normalize_existing(api.Environment(cr, SUPERUSER_ID, {}))
