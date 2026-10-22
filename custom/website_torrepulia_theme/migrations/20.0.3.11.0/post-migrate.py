from odoo import api, SUPERUSER_ID

# Checkout steps are per-website records; Odoo 20 leaves some labels vague
# ("Ordina", "Check-out"). A step's button label shows on the page before it.
STEPS = {
    '/shop/cart': {'name': 'Carrello'},
    '/shop/checkout': {'name': 'Consegna', 'main_button_label': "Procedi all'acquisto"},
    '/shop/payment': {'main_button_label': 'Vai al pagamento'},
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        # Write the website's own language, the one visitors read.
        website = website.with_context(lang=website.default_lang_id.code or 'en_US')
        for href, values in STEPS.items():
            website.env['website.checkout.step'].search([
                ('website_id', '=', website.id), ('step_href', '=', href)]).write(values)
        # Bank transfer is a pay-later method on this website (see static/src/js/checkout.js).
        website.company_id.pay_later_label = "Conferma l'ordine"
