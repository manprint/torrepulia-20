from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import (NEW_OIL_FIRST_META, NEW_OIL_PRICE_META,
                                                                 PERANZANA_GUIDE, create_guide, refresh_guide_meta)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Fourth guide, the Peranzana: the owner read it locally and asked to publish it straight away.
    data = create_guide(env, PERANZANA_GUIDE)
    if data:
        env['blog.post'].browse(data.res_id).is_published = True
    # The new oil guide: the price first in the title Google shows, unless the owner changed it.
    refresh_guide_meta(env, NEW_OIL_PRICE_META, NEW_OIL_FIRST_META)
