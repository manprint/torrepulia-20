from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Launch: indexed home, home and shop metadata, share image, consent bar, 301s from the old torrepulia.it.
    env = api.Environment(cr, SUPERUSER_ID, {})
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        website._torrepulia_launch_seo()
