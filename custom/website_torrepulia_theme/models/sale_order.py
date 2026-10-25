"""The order confirmation sent before the milling: Torrepulia's email, PDF title and attachment name.

A reservation becomes a native quotation; on the Torrepulia site it is called "Conferma d'ordine"
everywhere the customer sees it. Orders of other websites keep Odoo's wording and template.
"""
from odoo import models
from odoo.tools import format_amount, format_date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _torrepulia_website(self):
        """The Torrepulia website of the order: its own, or the company's one for backend quotations."""
        self.ensure_one()
        website = self.website_id.sudo()
        if not website:
            website = self.env['website'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)
        return website if website.torrepulia_theme_enabled else self.env['website']

    def _compute_type_name(self):
        super()._compute_type_name()
        for order in self:
            if order.state in ('draft', 'sent') and order._torrepulia_website():
                order.type_name = "Conferma d'ordine"

    def _find_mail_template(self):
        self.ensure_one()
        if not self.env.context.get('proforma') and self.state in ('draft', 'sent') and self._torrepulia_website():
            template = self.env.ref('website_torrepulia_theme.mail_order_confirmation', raise_if_not_found=False)
            if template:
                return template
        return super()._find_mail_template()

    def _torrepulia_confirmation_html(self):
        """Email body: tables and inline styles, absolute links to the site the customer knows."""
        self.ensure_one()
        website = self._torrepulia_website()
        base_url = website.get_base_url()
        currency = self.currency_id
        lines = self.order_line.filtered(lambda line: not line.display_type)
        delivery = lines.filtered('is_delivery') if 'is_delivery' in lines._fields else lines.browse()
        products = lines - delivery
        partner = self.company_id.partner_id
        vat = (self.company_id.vat or '').replace(' ', '')
        return self.env['ir.qweb']._render('website_torrepulia_theme.mail_order_confirmation_body', {
            'order': self,
            'first_name': (self.partner_id.name or '').split(' ')[0],
            'rows': [{
                'name': line.product_id.display_name or line.name,
                'quantity': '%g' % line.product_uom_qty,
                'thumbnail': '%s/web/image/product.product/%s/image_128' % (base_url, line.product_id.id),
                'subtotal': format_amount(self.env, line.price_total, currency),
            } for line in products],
            'shipping': delivery and (format_amount(self.env, sum(delivery.mapped('price_total')), currency)
                                      if sum(delivery.mapped('price_total')) else 'Gratuita'),
            'total': format_amount(self.env, self.amount_total, currency),
            'deadline': self.validity_date and format_date(self.env, self.validity_date, date_format='d MMMM y'),
            'portal_url': base_url + self.get_portal_url(),
            'base_url': base_url,
            'logo_url': '%s/web/image/website/%s/logo/240x120' % (base_url, website.id),
            'company': {
                'name': self.company_id.name, 'phone': self.company_id.phone,
                'address': ' · '.join(filter(None, [partner.street, ' '.join(filter(None, [partner.zip, partner.city]))])),
                'vat': vat[2:] if len(vat) > 2 and vat[:2].isalpha() else vat,
            },
        })
