from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import add_filter_press_section


def migrate(cr, version):
    # The filter guide explains the filter press with cellulose sheets used for La Regina.
    add_filter_press_section(api.Environment(cr, SUPERUSER_ID, {}))
