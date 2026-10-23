from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import (
    SENSORY_ONLY, align_home_family, refresh_editorial_pages)


def migrate(cr, version):
    # Pages rebuilt in 20.0.3.13.0 keep any later Builder edit: only the sensory section is refreshed.
    env = api.Environment(cr, SUPERUSER_ID, {})
    refresh_editorial_pages(env, SENSORY_ONLY)
    align_home_family(env)
