from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import retext_payment


def migrate(cr, version):
    # Reservations are paid on the order confirmation: "paghi alla spedizione" leaves the saved pages.
    retext_payment(api.Environment(cr, SUPERUSER_ID, {}))
