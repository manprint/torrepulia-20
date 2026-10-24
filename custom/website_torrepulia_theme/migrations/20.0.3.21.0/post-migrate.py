from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import add_process_photos


def migrate(cr, version):
    # La Peranzana: the harvest net photo under the process intro, the owner's step photos untouched.
    add_process_photos(api.Environment(cr, SUPERUSER_ID, {}))
