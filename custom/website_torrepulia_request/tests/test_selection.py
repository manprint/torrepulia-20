import secrets
import runpy
from pathlib import Path

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .test_request import RequestCase


@tagged('post_install', '-at_install')
class TestSelection(RequestCase):
    def setUp(self):
        super().setUp()
        self.site = self._visitor_site()
        self.session = {}

    def state(self, site=None, session=None):
        return (site if site is not None else self.site)._request_selection_state(
            session if session is not None else self.session)

    def payload(self, operation='add', **values):
        state = self.state()
        return dict(operation=operation, operation_id=secrets.token_hex(16),
                    selection_id=state['selection_id'], revision=state['revision'], **values)

    def apply(self, payload):
        return self.site._request_selection_apply(self.session, payload)

    def add(self, product=None, quantity=1, **values):
        return self.apply(self.payload(product_id=(product or self.product).id, quantity=quantity, **values))

    def test_increment_then_set_across_consumers(self):
        catalog = self.add(quantity=2)['state']
        self.assertEqual(catalog['lines'][0]['quantity'], 2)
        seasonal = self.state()
        self.assertEqual(seasonal, catalog)
        result = self.apply(self.payload('set_configuration', product_id=self.product.id, quantity=3))
        self.assertEqual(result['state']['lines'][0]['quantity'], 3)
        summary = self.state()
        self.assertEqual(summary['quantity'], 3)
        self.assertEqual(self.add(quantity=2)['state']['quantity'], 5)
        self.assertEqual(self.state()['line_count'], 1)

    def test_retry_and_operation_key_reuse(self):
        payload = self.payload(product_id=self.product.id, quantity=2)
        self.assertEqual(self.apply(payload)['state']['quantity'], 2)
        replay = self.apply(payload)
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['state']['quantity'], 2)
        self.add(quantity=1)
        self.assertEqual(self.apply(payload)['state']['quantity'], 3)
        with self.assertRaises(ValidationError):
            self.apply(dict(payload, quantity=3))

    def test_conflicting_tabs_and_outdated_set(self):
        self.add(quantity=2)
        key = self.state()['lines'][0]['key']
        older = self.payload('set', line_key=key, quantity=4)
        self.apply(self.payload('set', line_key=key, quantity=3))
        result = self.apply(older)
        self.assertFalse(result['ok'])
        self.assertEqual(result['code'], 'conflict')
        self.assertEqual(result['state']['quantity'], 3)
        self.assertFalse(self.env['torrepulia.request.operation'].search([('operation_id', '=', older['operation_id'])]))

    def test_other_lines_removal_and_clear_are_explicit(self):
        other = self.env['product.product'].create({'name': 'Other selection product', 'is_published': True})
        self.add(quantity=2)
        self.add(other, quantity=4)
        key = next(line['key'] for line in self.state()['lines'] if line['product_id'] == self.product.id)
        self.apply(self.payload('set', line_key=key, quantity=3))
        self.assertEqual(sorted(line['quantity'] for line in self.state()['lines']), [3, 4])
        removal = self.payload('remove', line_key=key)
        self.apply(removal)
        self.assertEqual(self.state()['quantity'], 4)
        self.assertEqual(self.apply(removal)['state']['quantity'], 4)
        clearing = self.payload('clear')
        self.apply(clearing)
        self.assertEqual(self.state()['lines'], [])
        self.add(other, quantity=1)
        self.assertEqual(self.apply(clearing)['state']['quantity'], 1)

    def test_variants_units_custom_values_and_origin(self):
        attribute = self.env['product.attribute'].create({
            'name': 'Variant identity', 'create_variant': 'always',
            'value_ids': [fields.Command.create({'name': 'A'}), fields.Command.create({'name': 'B'})],
        })
        custom_attribute = self.env['product.attribute'].create({
            'name': 'Custom identity', 'create_variant': 'no_variant',
            'value_ids': [fields.Command.create({'name': 'Free text', 'is_custom': True})],
        })
        template = self.env['product.template'].create({
            'name': 'Configured identity', 'is_published': True,
            'attribute_line_ids': [fields.Command.create({
                'attribute_id': attr.id, 'value_ids': [fields.Command.set(attr.value_ids.ids)],
            }) for attr in (attribute, custom_attribute)],
        })
        a, b = template.product_variant_ids
        value = template.valid_product_template_attribute_line_ids.product_template_value_ids.filtered('is_custom')
        config = {'no_variant_value_ids': value.ids, 'custom_values': {str(value.id): 'One'}}
        for invalid_text in ('\x00', '\ud800'):
            with self.assertRaises(ValidationError):
                self.add(a, 1, **dict(config, custom_values={str(value.id): invalid_text}))
        self.add(a, 1, **config)
        self.add(b, 1, **config)
        self.add(a, 1, **dict(config, custom_values={str(value.id): 'Two'}))
        self.add(a, 2, **config)
        state = self.state()
        self.assertEqual(state['line_count'], 3)
        self.assertEqual(sorted(line['quantity'] for line in state['lines']), [1, 1, 3])
        draft = self.site._torrepulia_session_request(self.session)
        draft.origin = 'Different editorial campaign'
        self.add(a, 1, **config)
        self.assertEqual(self.state()['line_count'], 3)
        # Odoo-native alternative UoM, available through the product's UoM list.
        uom = self.env['uom.uom'].create({'name': 'Selection pack', 'relative_uom_id': a.uom_id.id, 'relative_factor': 6})
        self.env.ref('base.user_root').group_ids |= self.env.ref('uom.group_uom')
        a.product_tmpl_id.uom_ids |= uom
        self.add(a, 1, uom_id=uom.id, **config)
        self.assertEqual(self.state()['line_count'], 4)
        old_uom = template.uom_id
        template.uom_ids |= old_uom
        template.uom_id = uom
        self.assertTrue(all(line['default_uom_id'] == uom.id for line in self.state()['lines']))

    def test_quantity_limits_and_manipulation(self):
        with self.assertRaises(ValidationError):
            self.apply(dict(self.payload('clear'), operation=[]))
        with self.assertRaises(ValidationError):
            self.add(uom_id=False)
        for value in (-1, 'bad', 'NaN', 'Infinity', True, [], 0, 1001, 1.5):
            with self.assertRaises(ValidationError):
                self.add(quantity=value)
        for unexpected in ('price_unit', 'company_id', 'team_id', 'partner_id', 'campaign_id'):
            with self.assertRaises(ValidationError):
                self.add(**{unexpected: self.company.id})
        self.website.write({'torrepulia_request_min_qty': .5, 'torrepulia_request_max_qty': 10,
                            'torrepulia_request_qty_step': .5})
        self.assertEqual(self.add(quantity=1.5)['state']['quantity'], 1.5)
        with self.assertRaises(ValidationError):
            self.add(quantity=.3)
        with self.assertRaises(ValidationError):
            self.website.torrepulia_request_qty_step = 0
        self.website.write({'torrepulia_request_min_qty': .001, 'torrepulia_request_max_qty': 10,
                            'torrepulia_request_qty_step': .001})
        with self.assertRaises(ValidationError):
            self.add(quantity=.001)

    def test_archived_or_unpublished_remains_and_can_be_removed(self):
        self.add(quantity=2)
        key = self.state()['lines'][0]['key']
        self.product.is_published = False
        state = self.state()
        self.assertEqual(state['quantity'], 2)
        self.assertFalse(state['lines'][0]['available'])
        self.assertTrue(state['lines'][0]['warning'])
        with self.assertRaises((AccessError, ValidationError)):
            self.apply(self.payload('set', line_key=key, quantity=3))
        self.product.active = False
        self.assertEqual(self.state()['quantity'], 2)
        self.apply(self.payload('remove', line_key=key))
        self.assertEqual(self.state()['lines'], [])

    def test_session_website_login_and_numeric_ids(self):
        self.add(quantity=2)
        own = self.state()
        self.assertEqual(self.state(session={})['lines'], [])
        other = {}
        payload = self.payload('set', line_key=own['lines'][0]['key'], quantity=8)
        result = self.site._request_selection_apply(other, payload)
        self.assertEqual(result['code'], 'conflict')
        self.assertEqual(result['state']['lines'], [])
        self.assertEqual(self.state()['quantity'], 2)
        self.other_site.write({'torrepulia_request_team_id': self.team.id, 'torrepulia_commercial_mode': 'request'})
        other_site = self._visitor_site(self.other_site)
        self.assertEqual(self.state(site=other_site)['lines'], [])
        self.assertEqual(self.state(site=self._visitor_site(user=self.portal)), own)
        with self.assertRaises(ValidationError):
            self.apply(self.payload('set', line_key='1', quantity=3))
        with self.assertRaises(AccessError):
            self.env['torrepulia.request.operation'].with_user(self.public).search([])

    def test_submission_is_not_resurrected_by_stale_retry(self):
        payload = self.payload(product_id=self.product.id, quantity=2)
        self.apply(payload)
        draft = self.site._torrepulia_session_request(self.session)
        self._submit(draft, self.site)
        result = self.apply(payload)
        self.assertFalse(result['ok'])
        self.assertEqual(result['state']['quantity'], 0)
        self.assertEqual(draft.line_ids.quantity, 2)

    def test_no_stock_or_commercial_side_effects(self):
        counts = {model: self.env[model].search_count([]) for model in
                  ('sale.order', 'crm.lead', 'res.partner', 'mail.mail')}
        if 'allow_out_of_stock_order' in self.product._fields:
            self.product.write({'is_storable': True, 'allow_out_of_stock_order': False})
        price = self.product.list_price
        with self.assertRaises(ValidationError):
            self.add(quantity=2)
        self.apply(self.payload('set_configuration', product_id=self.product.id, quantity=3))
        for model, count in counts.items():
            self.assertEqual(self.env[model].search_count([]), count, model)
        self.assertEqual(self.product.list_price, price)

    def test_legacy_identity_migration_preserves_existing_data(self):
        _, _, first = self._draft()
        _, _, second = self._draft()
        first_identity = first.selection_id
        original = (second.name, second.company_id, second.state, second.session_digest)
        self.env.cr.execute('UPDATE torrepulia_request SET selection_id = %s WHERE id = %s', ['legacy-default', second.id])
        migration = Path(__file__).resolve().parents[1] / 'migrations/20.0.1.1.0/pre-selection.py'
        runpy.run_path(str(migration))['migrate'](self.env.cr, '20.0.1.0.0')
        self.env.invalidate_all()
        self.assertEqual(first.selection_id, first_identity)
        self.assertRegex(second.selection_id, r'^[0-9a-f]{32}$')
        self.assertNotEqual(first.selection_id, second.selection_id)
        self.assertEqual((second.name, second.company_id, second.state, second.session_digest), original)
