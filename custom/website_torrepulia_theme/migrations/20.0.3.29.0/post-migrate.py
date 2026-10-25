from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import add_portrait_hero


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Phones download the slice of the hero they show, not the 1920 px photo.
    add_portrait_hero(env)
    # Product addresses lose the internal reference: the old site's redirects point at the new ones.
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        website._torrepulia_refresh_product_redirects()
