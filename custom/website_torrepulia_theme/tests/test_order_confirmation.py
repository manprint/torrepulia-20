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

    def test_other_websites_keep_odoo_quotation(self):
        self.website.torrepulia_theme_enabled = False
        self.assertEqual(self.order._find_mail_template(), self.env.ref('sale.email_template_edi_sale'))
        self.assertNotEqual(self.order.type_name, "Conferma d'ordine")
