from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # The header and footer extensions were generic: a new website of the same database picking
    # another Odoo header (e.g. "boxed") failed validation. They now belong to the Torrepulia site.
    env = api.Environment(cr, SUPERUSER_ID, {})
    websites = env['website'].search([('torrepulia_theme_enabled', '=', True)])
    if len(websites) == 1:
        websites._torrepulia_scope_navigation()
