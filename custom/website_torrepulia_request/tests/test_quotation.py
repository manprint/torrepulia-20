import copy
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .test_request import RequestCase


@tagged('post_install', '-at_install')
class TestRequestQuotation(RequestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Quotation test customer', 'email': 'quotation@example.invalid'})

    def submitted(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        self._submit(draft, site)
        return draft

    def wizard(self, request, revision=False, reason='', user=None):
        request = request.with_user(user or self.sales)
        action = request.action_new_quotation_revision() if revision else request.action_prepare_quotation()
        self.assertEqual(action['res_model'], 'torrepulia.request.quotation.wizard')
        return self.env[action['res_model']].with_user(user or self.sales).with_context(**action['context']).create({
            'partner_id': self.customer.id, 'reason': reason})

    def prepare(self, request):
        action = self.wizard(request).action_prepare()
        return self.env['sale.order'].browse(action['res_id'])

    def test_explicit_customer_native_terms_prices_and_snapshot(self):
        request = self.submitted()
        before = copy.deepcopy(request.submission_snapshot), copy.deepcopy(request.line_ids.snapshot)
        # A native customer pricelist must win over any public receipt amount.
        pricelist = self.env['product.pricelist'].create({'name': 'Quotation native price', 'currency_id': self.company.currency_id.id,
            'company_id': self.company.id, 'item_ids': [fields.Command.create({'applied_on': '1_product',
                'product_tmpl_id': self.product.product_tmpl_id.id, 'compute_price': 'fixed', 'fixed_price': 19.25})]})
        self.customer.with_company(self.company).property_product_pricelist = pricelist
        term = self.env['account.payment.term'].create({'name': 'Quotation native term', 'company_id': self.company.id})
        self.customer.with_company(self.company).property_payment_term_id = term
        fiscal = self.env['account.fiscal.position'].create({'name': 'Quotation fiscal position', 'company_id': self.company.id})
        self.customer.with_company(self.company).property_account_position_id = fiscal
        counts = {model: self.env[model].search_count([]) for model in ('stock.move', 'account.move', 'payment.transaction')}
        action = request.with_user(self.sales).action_prepare_quotation()
        self.assertFalse(action['context']['default_partner_id'])
        wizard = self.wizard(request).with_context(default_price_unit=0.01,
            default_pricelist_id=self.env['product.pricelist'].search([], limit=1).id)
        order = self.env['sale.order'].browse(wizard.action_prepare()['res_id'])
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.partner_id, self.customer)
        self.assertEqual(order.company_id, self.company)
        self.assertEqual(order.pricelist_id, pricelist)
        self.assertEqual(order.payment_term_id, term)
        self.assertEqual(order.fiscal_position_id, fiscal)
        self.assertEqual(order.order_line.price_unit, 19.25)
        self.assertEqual(order.order_line.product_id, self.product)
        self.assertEqual(order.order_line.product_uom_qty, 2)
        self.assertEqual(order.order_line.product_uom_id, self.product.uom_id)
        self.assertFalse(order.website_id)
        self.assertEqual(order.assigned_website_id, self.website)
        self.assertEqual(order.opportunity_id, request.opportunity_id)
        self.assertEqual(order.origin, request.name)
        self.assertEqual(order.opportunity_id.partner_id, self.customer)
        self.assertFalse(request.partner_id)
        self.assertEqual(wizard.action_prepare()['res_id'], order.id)
        self.assertEqual(request.with_user(self.sales).action_prepare_quotation()['res_id'], order.id)
        order.order_line.write({'product_uom_qty': 7, 'price_unit': 11})
        self.product.name = 'Renamed after receiving the customer request'
        self.assertEqual(request.line_ids.received_name, before[1]['name'])
        self.assertEqual((request.submission_snapshot, request.line_ids.snapshot), before)
        self.assertEqual(request.line_ids.quantity, 2)
        for model, count in counts.items():
            self.assertEqual(self.env[model].search_count([]), count)

    def test_distinct_variants_custom_values_and_sales_uom(self):
        attribute = self.env['product.attribute'].create({'name': 'Quotation format', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'Small'}), fields.Command.create({'name': 'Large'})]})
        custom = self.env['product.attribute'].create({'name': 'Quotation label', 'create_variant': 'no_variant',
            'value_ids': [fields.Command.create({'name': 'Text', 'is_custom': True})]})
        template = self.env['product.template'].create({'name': 'Quotation variants', 'is_published': True, 'website_id': self.website.id,
            'attribute_line_ids': [fields.Command.create({'attribute_id': attr.id, 'value_ids': [fields.Command.set(attr.value_ids.ids)]}) for attr in (attribute, custom)]})
        a, b = template.product_variant_ids
        value = template.valid_product_template_attribute_line_ids.product_template_value_ids.filtered('is_custom')
        pack = self.env['uom.uom'].create({'name': 'Quotation pack six', 'relative_uom_id': a.uom_id.id, 'relative_factor': 6})
        template.uom_ids |= pack
        self.sales.group_ids |= self.env.ref('uom.group_uom')
        self.env.user.group_ids |= self.env.ref('uom.group_uom')
        site, session, draft = self._draft()
        for product, qty, uom, text in [(a, 2, a.uom_id, 'Customer A'), (b, 3, b.uom_id, 'Customer B'), (a, 1, pack, 'A pack')]:
            draft._set_selection(site, product.with_env(site.env), qty, uom=uom.with_env(site.env),
                no_variant_values=value.with_env(site.env), custom_values={str(value.id): text})
        self._submit(draft, site)
        order = self.prepare(draft)
        actual = {(line.product_id.id, line.product_uom_id.id, line.product_uom_qty,
                   line.product_custom_attribute_value_ids.custom_value) for line in order.order_line}
        self.assertEqual(actual, {(a.id, a.uom_id.id, 2, 'Customer A'), (b.id, b.uom_id.id, 3, 'Customer B'), (a.id, pack.id, 1, 'A pack')})
        self.assertTrue(all(line.product_no_variant_attribute_value_ids == value for line in order.order_line))

    def test_revisions_are_explicit_traced_and_double_dialogs_converge(self):
        request = self.submitted()
        first = self.prepare(request)
        w1 = self.wizard(request, revision=True)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            w1.action_prepare()
        w1.reason = 'Customer requested an alternative'
        w2 = self.wizard(request, revision=True, reason='Same review opened twice')
        second = self.env['sale.order'].browse(w1.action_prepare()['res_id'])
        self.assertNotEqual(first, second)
        self.assertEqual(second.torrepulia_revision_of_id, first)
        self.assertEqual(second.torrepulia_revision_reason, w1.reason)
        self.assertTrue(second.message_ids.filtered(lambda message: w1.reason in str(message.body)))
        self.assertEqual(w2.action_prepare()['res_id'], second.id)
        self.assertEqual(w1.action_prepare()['res_id'], second.id)
        self.assertEqual(len(request.quotation_ids), 2)
        second.action_cancel()
        self.assertEqual(request.with_user(self.sales).action_prepare_quotation()['res_id'], first.id)

    def test_archived_product_and_creation_failure_preserve_source(self):
        request = self.submitted()
        wizard = self.wizard(request)
        self.product.active = False
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            wizard.action_prepare()
        self.assertFalse(request.quotation_ids)
        self.product.active = True
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            with patch.object(type(self.env['sale.order']), 'create', side_effect=ValidationError('Synthetic sales error')):
                wizard.action_prepare()
        self.assertFalse(request.quotation_ids)
        self.assertFalse(request.opportunity_id.partner_id)
        self.assertEqual(request.state, 'submitted')
        self.assertEqual(request.line_ids.quantity, 2)

    def test_public_portal_other_sales_and_cross_company_are_rejected(self):
        request = self.submitted()
        for user in (self.public, self.portal):
            with self.assertRaises(AccessError):
                request.with_user(user).action_prepare_quotation()
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                self.env['torrepulia.request.quotation.wizard'].with_user(user).create({'request_id': request.id, 'partner_id': self.customer.id})
        outsider = self.env['res.users'].create({'name': 'Quotation outsider', 'login': 'quotation-outsider@example.invalid',
            'group_ids': [fields.Command.set(self.env.ref('sales_team.group_sale_salesman').ids)]})
        with self.assertRaises(AccessError):
            request.with_user(outsider).action_prepare_quotation()
        other_company = self.env['res.company'].create({'name': 'Quotation other company'})
        foreign = self.env['res.partner'].create({'name': 'Foreign quotation customer', 'company_id': other_company.id})
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.wizard(request).partner_id = foreign
        self.assertFalse(request.quotation_ids)

    def test_manual_email_acceptance_uses_native_confirmation_and_delivery(self):
        request = self.submitted()
        self.product.write({'is_storable': True, 'invoice_policy': 'order'})
        order = self.prepare(request)
        order.message_post(body='Accordo accettato via email — prova interna', subtype_xmlid='mail.mt_note')
        self.assertEqual(order.state, 'draft')
        order.with_user(self.sales).action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertTrue(order.picking_ids)
        self.assertEqual(sum(order.picking_ids.move_ids.mapped('product_uom_qty')), 2)
        self.assertEqual(order.invoice_status, 'to invoice')
        self.assertEqual(request.with_user(self.sales).action_prepare_quotation()['res_id'], order.id)
