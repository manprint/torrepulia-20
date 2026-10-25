from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOrderConfirmation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([('company_id', '=', self.env.company.id)], limit=1)
        self.partner = self.env['res.partner'].create({'name': 'Mario Rossi', 'email': 'mario.rossi@example.invalid'})
        product = self.env['product.product'].create({'name': 'Latta di prova', 'list_price': 69.0})
        # A backend quotation, as the manager creates it from the reservation's opportunity.
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'validity_date': '2026-11-01',
            'order_line': [(0, 0, {'product_id': product.id, 'product_uom_qty': 2})]})

    def test_torrepulia_quotation_is_an_order_confirmation(self):
        self.website.torrepulia_theme_enabled = True
        template = self.order._find_mail_template()
        self.assertEqual(template, self.env.ref('website_torrepulia_theme.mail_order_confirmation'))
        self.assertEqual(self.order.type_name, "Conferma d'ordine")
        self.assertEqual(template.report_template_ids.print_report_name, "\"Conferma d'ordine %s\" % object.name")
        body = str(self.order._torrepulia_confirmation_html())
        for kept in ('Ecco la tua conferma d', 'Mario', 'Conferma e paga', self.order.get_portal_url(), 'Latta di prova',
                     'entro il <strong>1 ', 'Rispondi a questa email'):
            self.assertIn(kept, body)
        report = str(self.env['ir.actions.report']._render_qweb_html('sale.report_saleorder', self.order.ids)[0])
        self.assertIn('Conferma d', report)
        self.assertIn('Da confermare entro', report)

    def test_payment_and_confirmed_emails_replace_odoo_ones_without_frame(self):
        self.website.torrepulia_theme_enabled = True
        self.assertEqual(self.order._get_confirmation_template(), self.env.ref('website_torrepulia_theme.mail_order_confirmed'))
        original, layouts = type(self.order).message_post, []

        def spy(record, *args, **kwargs):
            layouts.append(kwargs.get('email_layout_xmlid'))
            return original(record, *args, **kwargs)

        with patch.object(type(self.order), 'message_post', spy):
            self.order._send_payment_succeeded_for_order_mail()
        # Odoo forces its "light" frame on order status emails: ours is the whole page.
        self.assertEqual(layouts, ['website_torrepulia_theme.mail_layout_bare'])
        message = self.order.message_ids[:1]
        self.assertIn('Vedi il tuo ordine', message.body)
        self.assertIn(self.order._torrepulia_payment_subject(), message.subject)
        confirmed = str(self.order._torrepulia_order_html('confirmed'))
        self.assertIn('Il tuo ordine è confermato', confirmed)

    def test_bank_transfer_email_gives_iban_and_reference(self):
        # Production has an IBAN on the transfer provider: the template is rendered against real orders on update.
        self.website.torrepulia_theme_enabled = True
        account = self.env['res.partner.bank'].create({
            'partner_id': self.env.company.partner_id.id, 'account_number': 'IT60X0542811101000000123456',
            'holder_name': 'Azienda agricola di prova'})
        provider = self.env.ref('payment.payment_provider_transfer')
        provider.write({'partner_bank_id': account.id})
        transaction = self.env['payment.transaction'].create({
            'provider_id': provider.id, 'payment_method_id': self.env.ref('payment_custom.payment_method_wire_transfer').id,
            'amount': self.order.amount_total, 'currency_id': self.order.currency_id.id,
            'partner_id': self.partner.id, 'sale_order_ids': [(6, 0, self.order.ids)]})
        transaction.with_context(payment_safe_write=True)._set_pending()
        details = dict(self.order._torrepulia_transfer_details(transaction))
        self.assertEqual(details['IBAN'].replace(' ', ''), 'IT60X0542811101000000123456')
        self.assertEqual(details['Beneficiario'], 'Azienda agricola di prova')
        self.assertTrue(details['Causale'])
        template = self.env.ref('website_torrepulia_theme.mail_order_payment')
        body = template._render_field('body_html', self.order.ids)[self.order.id]
        self.assertIn(details['IBAN'], body)
        self.assertIn('Ora completa il bonifico', body)
        self.assertIn('Completa il bonifico', self.order._torrepulia_payment_subject())

    def test_other_websites_keep_odoo_quotation(self):
        self.website.torrepulia_theme_enabled = False
        self.assertEqual(self.order._find_mail_template(), self.env.ref('sale.email_template_edi_sale'))
        self.assertNotEqual(self.order.type_name, "Conferma d'ordine")
        self.assertNotEqual(self.order._get_confirmation_template(), self.env.ref('website_torrepulia_theme.mail_order_confirmed'))
