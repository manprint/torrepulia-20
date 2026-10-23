from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import (
    align_home_family, link_report_2024, move_bag_in_box, refresh_editorial_pages)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    link_report_2024(env)
    move_bag_in_box(env)
    refresh_editorial_pages(env)
    align_home_family(env)
