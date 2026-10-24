from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import recopy_pages


def migrate(cr, version):
    # Home, La Peranzana, La famiglia: the owner's words of 25/10; "frantoio di fiducia" and 1.500 olive trees everywhere.
    recopy_pages(api.Environment(cr, SUPERUSER_ID, {}))
