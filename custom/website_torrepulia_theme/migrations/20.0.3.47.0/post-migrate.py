from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import NEW_OIL_GUIDE, NEW_OIL_GUIDE_SECTIONS, refresh_guide_sections


def migrate(cr, version):
    # The new oil guide: the back label, acidity and the price explained; sections the owner rewrote stay.
    refresh_guide_sections(api.Environment(cr, SUPERUSER_ID, {}), NEW_OIL_GUIDE, NEW_OIL_GUIDE_SECTIONS)
