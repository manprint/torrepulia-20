from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestRequestQuotationAccounting(AccountTestInvoicingCommon):
    def setUp(self):
        super().setUp()
        self.env.user.group_ids |= self.env.ref('sales_team.group_sale_manager')
        self.customer = self.env['res.partner'].create({'name': 'Quotation accounting customer', 'email': 'quotation-accounting@example.invalid'})
        self.product_a.write({'is_published': True, 'is_storable': True, 'invoice_policy': 'order'})
        team = self.env['crm.team'].create({'name': 'Quotation accounting team', 'company_id': self.env.company.id})
        site = self.env['website'].create({'name': 'Quotation accounting website', 'company_id': self.env.company.id,
            'torrepulia_commercial_mode': 'request', 'torrepulia_request_team_id': team.id})
        self.product_a.website_id = site
        visitor = site.with_user(self.env.ref('base.public_user')).with_context(website_id=site.id)
        draft = visitor._torrepulia_session_request({}, create=True)
        draft._set_selection(visitor, self.product_a.with_env(visitor.env), 2)
        draft._submit(visitor, {'contact_name': self.customer.name, 'email': self.customer.email})
        draft = draft.with_env(self.env)
        action = draft.action_prepare_quotation()
        wizard = self.env[action['res_model']].with_context(**action['context']).create({'partner_id': self.customer.id})
        self.order = self.env['sale.order'].browse(wizard.action_prepare()['res_id'])
        self.source = draft

    def test_native_manual_confirmation_invoice_and_stock_flow(self):
        self.assertFalse(self.order.picking_ids)
        self.assertFalse(self.order.invoice_ids)
        self.order.message_post(body='Accettazione email sintetica registrata dal commerciale', subtype_xmlid='mail.mt_note')
        self.order.action_confirm()
        self.assertEqual(self.order.state, 'sale')
        self.assertTrue(self.order.picking_ids)
        self.assertEqual(self.order.invoice_status, 'to invoice')
        invoices = self.order._create_invoices()
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices.move_type, 'out_invoice')
        self.assertEqual(invoices.invoice_line_ids.product_id, self.product_a)
        self.assertEqual(invoices.invoice_line_ids.quantity, 2)
        self.assertEqual(self.source.line_ids.quantity, 2)

    def test_native_demo_payment_confirms_without_extra_manual_approval(self):
        if not self.env['ir.module.module'].search_count([('name', '=', 'payment_demo'), ('state', '=', 'installed')]):
            self.skipTest('Install payment_demo only in the isolated test database to exercise fake payments.')
        # Administrative setup of this known demo fixture only, never a live provider.
        provider = self.env.ref('payment.payment_provider_demo').sudo()
        provider.write({'company_id': self.env.company.id, 'journal_id': self.company_data['default_journal_bank'].id, 'is_live': False})
        self.order.write({'require_signature': False, 'prepayment_percent': 1})
        self.order.action_quotation_sent()
        transaction = self.env['payment.transaction'].create({
            'provider_id': provider.id, 'payment_method_id': self.env.ref('payment_demo.payment_method_demo').id,
            'partner_id': self.customer.id, 'amount': self.order.amount_total,
            'currency_id': self.order.currency_id.id, 'operation': 'online_direct',
            'reference': 'Torrepulia-native-demo-test', 'sale_order_ids': [fields.Command.set(self.order.ids)],
        })
        with patch.object(type(self.env['mail.mail']), 'send', return_value=True), \
                patch.object(type(self.env['ir.mail_server']), '_connect__', side_effect=AssertionError('No real SMTP')):
            transaction.action_demo_set_done()
        self.assertEqual(transaction.state, 'done')
        self.assertEqual(self.order.state, 'sale')
        self.assertTrue(self.order.picking_ids)
        self.assertTrue(transaction.payment_id)
        self.assertEqual(self.source.state, 'submitted')
