from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import STORAGE_GUIDE, create_guide


def migrate(cr, version):
    # First guide of the blog, unpublished: the owner reads it and publishes it from the editor.
    create_guide(api.Environment(cr, SUPERUSER_ID, {}), STORAGE_GUIDE)
