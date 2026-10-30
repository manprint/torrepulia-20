from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import NEW_OIL_GUIDE, create_guide


def migrate(cr, version):
    # Third guide, the new oil of the season, unpublished: the owner reads it and publishes it from the editor.
    create_guide(api.Environment(cr, SUPERUSER_ID, {}), NEW_OIL_GUIDE)
