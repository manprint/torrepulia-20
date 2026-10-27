from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import FILTER_GUIDE, create_guide


def migrate(cr, version):
    # Second guide, unpublished: the owner reads it and publishes it from the editor.
    create_guide(api.Environment(cr, SUPERUSER_ID, {}), FILTER_GUIDE)
