from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import add_review_privacy


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Odoo's "Request ratings" sends our email, counted from the shipment (models/reviews.py).
    native = env.ref('website_sale.mail_template_sale_order_rating', raise_if_not_found=False)
    ours = env.ref('website_torrepulia_theme.mail_order_review')
    for website in env['website'].search([('torrepulia_theme_enabled', '=', True)]):
        if not website.rating_email_template_id or website.rating_email_template_id == native:
            website.rating_email_template_id = ours
        # Odoo's 5 days after the order become 7 after the shipment: tasted, not just unpacked.
        if website.rating_email_delay == 5:
            website.rating_email_delay = 7
    # The privacy policy says it.
    add_review_privacy(env)
