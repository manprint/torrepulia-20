from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_cleanup import cleanup_home


def migrate(cr, version):
    cleanup_home(api.Environment(cr, SUPERUSER_ID, {}))
