from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Il territorio is a finished page now: show it in the main menu, between La famiglia and Contatti.
    env = api.Environment(cr, SUPERUSER_ID, {})
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        env['website.menu'].search([
            ('website_id', '=', website.id), ('url', '=', '/territorio'),
            ('parent_id', '=', website.menu_id.id)]).write({'torrepulia_navigation_hidden': False, 'sequence': 35})
