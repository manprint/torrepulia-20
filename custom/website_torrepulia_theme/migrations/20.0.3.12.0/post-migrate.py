from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # The site renders Manrope and Libre Caslon Display from the theme, yet Odoo's
    # default font values still linked Inter and Inter Tight from Google Fonts.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['website'].search([('torrepulia_theme_enabled', '=', True)])._torrepulia_use_local_fonts()
