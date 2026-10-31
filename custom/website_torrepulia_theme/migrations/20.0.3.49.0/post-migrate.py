from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import add_harvest_media_to_pages, six_hour_milling
from odoo.addons.website_torrepulia_theme.models.guides import NEW_OIL_GUIDE, NEW_OIL_GUIDE_OLIVES_SECTIONS, refresh_guide_sections


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # The 2026 harvest: clips and photos on /l-olio, a photo for each chapter on /aboutus.
    add_harvest_media_to_pages(env)
    # The new oil guide: the olives on the branch; a section the owner rewrote stays.
    refresh_guide_sections(env, NEW_OIL_GUIDE, NEW_OIL_GUIDE_OLIVES_SECTIONS)
    # The milling is within 6 hours of the harvest, not 8: every page, guide and /llms.txt.
    six_hour_milling(env)
