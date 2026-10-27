from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import STORAGE_GUIDE, link_guide_from_oil_page


def migrate(cr, version):
    # The storage guide is published: La Peranzana links it where the oil leaves for home.
    link_guide_from_oil_page(api.Environment(cr, SUPERUSER_ID, {}), STORAGE_GUIDE)
