from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import retext_aroma


def migrate(cr, version):
    # Home and La Peranzana: "oliva appena colta" leaves the aroma, the fruity already says it.
    retext_aroma(api.Environment(cr, SUPERUSER_ID, {}))
