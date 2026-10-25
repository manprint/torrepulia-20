from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # Product pages in the words of 25/10, like the home and La Peranzana.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['product.template'].with_context(active_test=False)._torrepulia_retext_sensory()
