from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # /llms.txt answered 404: Odoo serves it only once the website has a text.
    env = api.Environment(cr, SUPERUSER_ID, {})
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        website._torrepulia_llms_txt()
