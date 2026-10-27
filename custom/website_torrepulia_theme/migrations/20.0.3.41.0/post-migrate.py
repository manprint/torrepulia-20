from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import link_filter_guide_from_storage_guide


def migrate(cr, version):
    # The filter guide is published: the storage guide points to it where it talks about unfiltered oil.
    link_filter_guide_from_storage_guide(api.Environment(cr, SUPERUSER_ID, {}))
