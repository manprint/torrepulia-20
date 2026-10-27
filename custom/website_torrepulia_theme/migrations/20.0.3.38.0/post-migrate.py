from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.guides import FIRST_STORAGE_META, STORAGE_GUIDE, refresh_guide_meta


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Title and description of the first guide within Google's lengths, unless already edited.
    refresh_guide_meta(env, STORAGE_GUIDE, FIRST_STORAGE_META)
    # The guides move to the footer: the "Blog" entry leaves the main menu.
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        website._torrepulia_hide_blog_menu()
