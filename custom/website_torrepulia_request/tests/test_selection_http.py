import json
import secrets

from odoo import fields
from odoo.tests import HttpCase, tagged
from odoo.tests.common import Opener


@tagged('post_install', '-at_install')
class TestSelectionHttp(HttpCase):
    def test_csrf_private_responses_and_http_roundtrip(self):
        website = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'HTTP request test', 'company_id': website.company_id.id})
        website.write({'torrepulia_request_team_id': team.id, 'torrepulia_commercial_mode': 'request'})
        product = self.env['product.product'].create({'name': 'HTTP native product', 'is_published': True})
        response = self.url_open('/torrepulia/request/current')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response.headers['Cache-Control'])
        bootstrap = response.json()
        self.assertTrue(bootstrap['state']['enabled'])
        payload = {'operation': 'add', 'operation_id': secrets.token_hex(16),
                   'selection_id': bootstrap['state']['selection_id'], 'revision': 0, 'product_id': product.id, 'quantity': 2}
        invalid = self.url_open('/torrepulia/request/update', data={'payload': json.dumps(payload)})
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state']['quantity'], 0)
        posted = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload),
        })
        self.assertEqual(posted.status_code, 200, posted.text)
        state = posted.json()['state']
        self.assertEqual(state['quantity'], 2)
        self.assertNotIn('session_digest', posted.text)
        self.assertNotIn('partner_id', posted.text)
        retry = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload),
        })
        self.assertEqual(retry.json()['state']['quantity'], 2)
        self.assertTrue(retry.json()['replayed'])
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state'], state)
        # Reject authoritative commercial fields instead of trusting them.
        forged = dict(payload, operation_id=secrets.token_hex(16), price_unit=0)
        response = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(forged),
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['state']['quantity'], 2)
        oversized_integer = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': '{"product_id":' + '1' * 5000 + '}',
        })
        self.assertEqual(oversized_integer.status_code, 422)
        # A genuinely different cookie session cannot operate on the first one.
        original_opener = self.opener
        self.opener = Opener(self)
        try:
            stranger = self.url_open('/torrepulia/request/current').json()
            self.assertEqual(stranger['state']['lines'], [])
            foreign_line = {'operation': 'set', 'operation_id': secrets.token_hex(16),
                            'selection_id': stranger['state']['selection_id'],
                            'revision': stranger['state']['revision'],
                            'line_key': state['lines'][0]['key'], 'quantity': 8}
            denied = self.url_open('/torrepulia/request/update', data={
                'csrf_token': stranger['csrf_token'], 'payload': json.dumps(foreign_line),
            })
            self.assertEqual(denied.status_code, 422)
            self.assertEqual(denied.json()['state']['lines'], [])
        finally:
            self.opener = original_opener
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state']['quantity'], 2)
        # Actual native login rotates the SID but preserves the selection data.
        portal = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Selection HTTP portal', 'login': 'selection-http@example.invalid',
            'password': 'SelectionTestOnlyPassword',
            'group_ids': [fields.Command.set(self.env.ref('base.group_portal').ids)],
        })
        logged_in = self.url_open('/web/login', data={
            'csrf_token': bootstrap['csrf_token'], 'login': portal.login,
            'password': 'SelectionTestOnlyPassword', 'redirect': '/torrepulia/request/current',
        })
        self.assertEqual(logged_in.status_code, 200)
        self.assertIn('application/json', logged_in.headers['Content-Type'])
        self.assertEqual(logged_in.json()['state']['selection_id'], state['selection_id'])
        self.assertEqual(logged_in.json()['state']['quantity'], 2)
