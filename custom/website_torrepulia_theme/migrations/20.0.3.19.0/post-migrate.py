from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # 3.18.0 looked the home up without a language and missed the page Odoo serves at "/".
    env = api.Environment(cr, SUPERUSER_ID, {})
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        website._torrepulia_launch_seo()
        # "Olio nuovo" in production was a plain menu entry: no outline, shown out of season too.
        website._torrepulia_flag_seasonal_menu()
    # The theme draws the filtration as a two-way switch from Odoo's pills; in production
    # the attribute was created with the default radio buttons.
    env['product.attribute'].search([('name', '=ilike', 'filtrazione'), ('display_type', '=', 'radio')]).display_type = 'pills'
