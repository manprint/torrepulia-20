"""Torrepulia's order emails and PDF title.

A reservation becomes a native quotation; on the Torrepulia site it is called "Conferma d'ordine"
everywhere the customer sees it, and the payment and confirmation emails share its look. Orders of
other websites keep Odoo's wording and templates.
"""
from odoo import models
from odoo.tools import format_amount, format_date

BARE_LAYOUT = 'website_torrepulia_theme.mail_layout_bare'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _torrepulia_website(self):
        """The Torrepulia website of the order: its own, or the company's one for backend quotations."""
        self.ensure_one()
        website = self.website_id.sudo()
        if not website:
            website = self.env['website'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)
        return website if website.torrepulia_theme_enabled else self.env['website']

    def _torrepulia_free_shipping(self):
        """Distance from the free shipping of the shop carrier, for the cart total; False if none applies.

        Same carrier and same amount as the checkout (total with taxes, delivery line excluded).
        """
        self.ensure_one()
        website = self._torrepulia_website()
        if not website or self.state != 'draft' or not self._has_deliverable_products():
            return False
        carrier = website._torrepulia_shipping_carrier()
        if not carrier.free_over or carrier.amount <= 0:
            return False
        amount = self._compute_amount_total_without_delivery()
        return {'threshold': carrier.amount, 'remaining': max(carrier.amount - amount, 0),
                'progress': min(round(amount / carrier.amount * 100), 100)}

    def _compute_type_name(self):
        super()._compute_type_name()
        for order in self:
            if order.state in ('draft', 'sent') and order._torrepulia_website():
                order.type_name = "Conferma d'ordine"

    def _torrepulia_template(self, name):
        self.ensure_one()
        return self._torrepulia_website() and self.env.ref('website_torrepulia_theme.' + name, raise_if_not_found=False)

    def _find_mail_template(self):
        self.ensure_one()
        if not self.env.context.get('proforma') and self.state in ('draft', 'sent'):
            template = self._torrepulia_template('mail_order_confirmation')
            if template:
                return template
        return super()._find_mail_template()

    def _get_confirmation_template(self):
        # Sent when a card payment confirms the order, or from "Send by email" on a confirmed order.
        return self._torrepulia_template('mail_order_confirmed') or super()._get_confirmation_template()

    def _send_payment_succeeded_for_order_mail(self):
        # Replaces Odoo's "Pending Order": a bank transfer needs its details, Odoo's email has none.
        ours = self.filtered(lambda order: order._torrepulia_template('mail_order_payment'))
        ours.filtered('website_id').with_context(force_user_recomputation=True)._compute_user_id()
        for order in ours:
            order._send_order_notification_mail(order._torrepulia_template('mail_order_payment'))
        return super(SaleOrder, self - ours)._send_payment_succeeded_for_order_mail()

    def message_post_with_source(self, source_ref, *args, **kwargs):
        # Odoo forces its "light" frame on order status emails; ours are complete pages.
        if getattr(source_ref, '_name', None) == 'mail.template' and source_ref.email_layout_xmlid == BARE_LAYOUT:
            kwargs['email_layout_xmlid'] = BARE_LAYOUT
        return super().message_post_with_source(source_ref, *args, **kwargs)

    def _torrepulia_payment_subject(self):
        self.ensure_one()
        transaction = self.get_portal_last_transaction()
        if transaction.state == 'pending' and transaction.provider_id.custom_mode == 'wire_transfer':
            return 'Completa il bonifico per l’ordine %s' % self.name
        if transaction.state == 'pending':
            return 'Pagamento in elaborazione per l’ordine %s' % self.name
        return 'Pagamento ricevuto per l’ordine %s' % self.name

    def _torrepulia_transfer_details(self, transaction):
        """Rows the customer copies into the bank app: beneficiary, IBAN, amount, reference."""
        if transaction.state != 'pending' or transaction.provider_id.custom_mode != 'wire_transfer':
            return []
        account = transaction.provider_id._get_custom_bank_account()
        reference = transaction._get_communication() if hasattr(transaction, '_get_communication') else transaction.reference
        rows = [('Beneficiario', account.holder_name or account.partner_id.name), ('IBAN', account.account_number)] if account else []
        return rows + [('Importo', format_amount(self.env, transaction.amount, transaction.currency_id)),
                       ('Causale', reference or self.name)]

    def _torrepulia_order_html(self, kind):
        """Email body: tables and inline styles, absolute links to the site the customer knows."""
        self.ensure_one()
        website = self._torrepulia_website()
        base_url = website.get_base_url()
        currency = self.currency_id
        lines = self.order_line.filtered(lambda line: not line.display_type)
        delivery = lines.filtered('is_delivery') if 'is_delivery' in lines._fields else lines.browse()
        products = lines - delivery
        shipping_cost = sum(delivery.mapped('price_total'))
        transaction = self.get_portal_last_transaction().sudo()
        address = self.partner_shipping_id
        return self.env['ir.qweb']._render('website_torrepulia_theme.mail_order_confirmation_body', {
            'kind': kind,
            'order': self,
            'first_name': (self.partner_id.name or '').split(' ')[0],
            'rows': [{
                'name': line.product_id.display_name or line.name,
                'quantity': '%g' % line.product_uom_qty,
                'thumbnail': '%s/web/image/product.product/%s/image_128' % (base_url, line.product_id.id),
                'subtotal': format_amount(self.env, line.price_total, currency),
            } for line in products],
            'shipping': delivery and (format_amount(self.env, shipping_cost, currency) if shipping_cost else 'Gratuita'),
            'total': format_amount(self.env, self.amount_total, currency),
            'deadline': self.validity_date and format_date(self.env, self.validity_date, date_format='d MMMM y'),
            'pending': transaction.state == 'pending',
            'transfer': self._torrepulia_transfer_details(transaction) if kind == 'payment' else [],
            'shipping_address': [value for value in (
                address.name, address.street, address.street2,
                ' '.join(filter(None, [address.zip, address.city, address.state_id.code and '(%s)' % address.state_id.code])),
            ) if value],
            **self._torrepulia_mail_frame(),
        })

    def _torrepulia_mail_frame(self):
        """Links and company lines shared by every Torrepulia order email (header, buttons, footer)."""
        self.ensure_one()
        website = self._torrepulia_website()
        base_url = website.get_base_url()
        partner = self.company_id.partner_id
        vat = (self.company_id.vat or '').replace(' ', '')
        return {
            'portal_url': base_url + self.get_portal_url(),
            'base_url': base_url,
            'logo_url': '%s/web/image/website/%s/logo/240x120' % (base_url, website.id),
            'company': {
                'name': self.company_id.name, 'phone': self.company_id.phone,
                'address': ' · '.join(filter(None, [partner.street, ' '.join(filter(None, [partner.zip, partner.city]))])),
                'vat': vat[2:] if len(vat) > 2 and vat[:2].isalpha() else vat,
            },
        }

    def _torrepulia_confirmation_html(self):
        return self._torrepulia_order_html('confirmation')
