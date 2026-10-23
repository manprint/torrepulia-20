from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import align_home_family


def migrate(cr, version):
    # The home "Come funziona" link opens the Bag in Box explainer on its product page, not the page top.
    env = api.Environment(cr, SUPERUSER_ID, {})
    align_home_family(env)
