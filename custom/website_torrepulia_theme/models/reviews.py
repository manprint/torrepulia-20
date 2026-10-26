"""Review request after delivery, on Odoo's "Request ratings" (website_sale).

Odoo counts the days from the order date. A Torrepulia order is paid by bank transfer or
reserved before the milling, so the oil can leave days later: here the days run from the last
delivery handed to the carrier, and the email asks for a Google review and a review on the
site. Other websites of the database keep Odoo's email and timing.
"""
from datetime import datetime, time, timedelta

from odoo import api, fields, models

# Orders shipped within this many days before the threshold are still asked: a missed cron run
# or a change of the delay does not skip anyone, and older orders are never asked on activation.
REVIEW_WINDOW_DAYS = 14


class Website(models.Model):
    _inherit = 'website'

    torrepulia_google_review_url = fields.Char(
        'Link recensioni Google',
        help='Dal Profilo dell\'attività su Google: "Chiedi recensioni", il link che apre la recensione.')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    torrepulia_google_review_url = fields.Char(related='website_id.torrepulia_google_review_url', readonly=False)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    torrepulia_review_sent = fields.Boolean('Richiesta di recensione inviata', copy=False)

    @api.model
    def _cron_send_order_rating_emails(self):
        websites = self.env['website'].search([
            ('torrepulia_theme_enabled', '=', True), ('send_order_rating_emails', '=', True),
            ('rating_email_template_id', '!=', False)])
        for order in self._torrepulia_review_due(websites):
            order.website_id.rating_email_template_id.send_mail(order.id)
            order.torrepulia_review_sent = True
        # Odoo's pass by order date must not ask our orders again: they are marked as done for it.
        if websites:
            self.search([('website_id', 'in', websites.ids), ('state', '=', 'sale'),
                         ('is_rating_email_sent', '=', False)]).is_rating_email_sent = True
        return super()._cron_send_order_rating_emails()

    @api.model
    def _torrepulia_review_due(self, websites):
        """Orders whose last outgoing delivery was done `rating_email_delay` days ago."""
        due = self.browse()
        today = fields.Date.today()
        for website in websites:
            threshold = datetime.combine(today - timedelta(days=max(0, website.rating_email_delay)), time.max)
            orders = self.search([('website_id', '=', website.id), ('state', '=', 'sale'),
                                  ('torrepulia_review_sent', '=', False),
                                  ('picking_ids.date_done', '>', threshold - timedelta(days=REVIEW_WINDOW_DAYS))])
            for order in orders:
                deliveries = order.picking_ids.filtered(
                    lambda picking: picking.picking_type_code == 'outgoing' and picking.state != 'cancel')
                if deliveries and all(picking.state == 'done' for picking in deliveries) \
                        and max(deliveries.mapped('date_done')) <= threshold:
                    due |= order
        return due

    def _torrepulia_review_html(self):
        """Email body: same frame as the order emails; Google first, then each format on the site."""
        self.ensure_one()
        website = self._torrepulia_website()
        frame = self._torrepulia_mail_frame()
        reviews_on_site = website.is_view_active('website_sale.product_comment')
        lines = self.order_line.filtered(lambda line: not line.display_type and not line.is_delivery and line.product_id)
        # The cron has no current website: read the addresses as this website writes them.
        templates = lines.product_id.product_tmpl_id.with_context(website_id=website.id)
        return self.env['ir.qweb']._render('website_torrepulia_theme.mail_order_review_body', {
            'order': self,
            'first_name': (self.partner_id.name or '').split(' ')[0],
            'google_url': website.torrepulia_google_review_url,
            'rows': [{
                'name': template.with_context(display_default_code=False).display_name,
                'thumbnail': '%s/web/image/product.template/%s/image_128' % (frame['base_url'], template.id),
                'url': '%s%s%s' % (frame['base_url'], template.website_url, '#o_product_page_reviews' if reviews_on_site else ''),
            } for template in templates],
            'reviews_on_site': reviews_on_site,
            **frame,
        })
