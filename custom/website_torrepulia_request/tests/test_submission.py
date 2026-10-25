import secrets
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .test_request import RequestCase


@tagged('post_install', '-at_install')
class TestFinalSubmission(RequestCase):
    def setUp(self):
        super().setUp()
        self.sales.email = 'sales-notification@example.invalid'
        # Isolate the cron to rows created by this test, including committed QA
        # fixtures retained by the concurrency harness in this disposable DB.
        self.env['torrepulia.request.notification'].search([]).write({'retry_at': '2099-01-01 00:00:00'})

    def final(self, site, session, draft, digest=None, payload=None):
        state = site._request_selection_state(session)
        payload = payload or {'selection_id': state['selection_id'], 'revision': state['revision'],
            'operation_id': secrets.token_hex(16), 'contact_name': 'Final Guest',
            'email': 'final-guest@example.invalid', 'phone': '', 'notes': '<script>notes</script>', 'privacy_accepted': True}
        digest = digest or secrets.token_hex(32)
        result = site._request_submit_review(session, payload, digest,
            self.env['product.pricelist'].search([], limit=1).with_env(site.env),
            site.env['account.fiscal.position'], lambda: None)
        return result, digest, payload

    def test_crm_handoff_snapshot_stage_and_fresh_selection(self):
        self.website.torrepulia_request_user_id = self.sales
        source = self.env['utm.source'].create({'name': 'Original source'})
        campaign = self.env['utm.campaign'].create({'name': 'Actual campaign'})
        original_stages = self.env['crm.stage'].search([])
        before = {model: self.env[model].search_count([]) for model in
                  ('sale.order', 'account.move', 'payment.transaction', 'stock.move', 'res.partner', 'mail.mail')}
        site, session, draft = self._draft()
        self._line(draft, site)
        draft.write({'campaign_id': campaign.id, 'source_id': source.id})
        self.final(site, session, draft)
        lead = draft.opportunity_id
        self.assertEqual(lead.type, 'opportunity')
        self.assertEqual(lead.stage_id.name, 'Richiesta web ricevuta')
        self.assertFalse(lead.stage_id.is_won)
        self.assertEqual(lead.stage_id.team_ids, self.team)
        self.assertNotIn(lead.stage_id, original_stages)
        self.assertEqual(lead.torrepulia_website_id, self.website)
        self.assertEqual(lead.torrepulia_request_origin, 'Richiesta sito web')
        self.assertEqual(lead.campaign_id, campaign)
        self.assertEqual(lead.source_id, source)
        self.assertEqual(lead.user_id, self.sales)
        self.assertIn('&lt;script&gt;notes&lt;/script&gt;', lead.description)
        self.assertFalse(lead.partner_id)
        self.assertEqual(lead.torrepulia_request_ids, draft)
        self.assertEqual(draft.line_ids.snapshot['quantity'], 2)
        self.assertEqual(set(draft.notification_ids.mapped('kind')), {'customer', 'internal'})
        # A fresh empty draft already exists, before the next public read.
        fresh = self.env['torrepulia.request'].search([('website_id', '=', site.id), ('state', '=', 'draft')])
        self.assertEqual(len(fresh), 1)
        self.assertFalse(fresh.line_ids)
        for model, count in before.items():
            self.assertEqual(self.env[model].search_count([]), count, model)

    def test_replay_preserves_later_selection_and_new_intentional_submission(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        result, digest, payload = self.final(site, session, draft)
        fresh = site._torrepulia_session_request(session, create=True)
        self._line(fresh, site)
        replay, _, _ = self.final(site, session, draft, digest, payload)
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['reference'], result['reference'])
        self.assertEqual(fresh.line_ids.quantity, 2)
        later, _, _ = self.final(site, session, fresh, digest)
        self.assertNotEqual(later['reference'], result['reference'])
        self.assertEqual(len(draft.notification_ids), 2)
        self.assertEqual(len(fresh.notification_ids), 2)
        self.assertNotEqual(draft.opportunity_id, fresh.opportunity_id)
        # Page authorization expires independently from submission deduplication.
        self.env.cr.execute("UPDATE torrepulia_request SET submitted_at = NOW() - INTERVAL '25 hours' WHERE id = %s", [draft.id])
        draft.invalidate_recordset()
        replay, _, _ = self.final(site, session, draft, digest, payload)
        self.assertTrue(replay['replayed'])
        self.assertEqual(replay['reference'], result['reference'])

    def test_atomic_failure_after_crm_does_not_lose_selection(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        count = self.env['crm.lead'].search_count([])
        token = dict(session)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            with patch.object(type(self.env['torrepulia.request.notification']), 'create', side_effect=ValidationError('Outbox failure')):
                self.final(site, session, draft)
        draft.invalidate_recordset()
        self.assertEqual(draft.state, 'draft')
        self.assertFalse(draft.opportunity_id)
        self.assertFalse(draft.line_ids.snapshot)
        self.assertFalse(draft.public_receipt)
        self.assertEqual(draft.line_ids.quantity, 2)
        self.assertEqual(session, token)
        self.assertEqual(self.env['crm.lead'].search_count([]), count)

    def test_mail_preparation_queue_retry_and_no_contact_matching(self):
        existing = self.env['res.partner'].create({'name': 'Unrelated account', 'email': 'visitor@example.invalid'})
        site, session, draft = self._draft()
        self._line(draft, site)
        count = self.env['res.partner'].search_count([])
        self._submit(draft, site)
        customer = draft.notification_ids.filtered(lambda item: item.kind == 'customer')
        with patch.object(type(self.env['mail.template']), 'send_mail', side_effect=ValidationError('Template unavailable')):
            self.env['torrepulia.request.notification']._cron_prepare()
        self.assertEqual(draft.state, 'submitted')
        self.assertEqual(customer.state, 'failed')
        self.assertTrue(draft.opportunity_id.exists())
        self.assertFalse(draft.partner_id)
        self.assertFalse(draft.opportunity_id.partner_id)
        draft.notification_ids.write({'retry_at': fields.Datetime.now()})
        with patch.object(type(self.env['mail.mail']), 'send', side_effect=AssertionError('No SMTP during preparation')):
            self.env['torrepulia.request.notification']._cron_prepare()
            self.env['torrepulia.request.notification']._cron_prepare()
        self.assertEqual(customer.state, 'queued', customer.error)
        self.assertEqual(customer.mail_id.email_to, 'visitor@example.invalid')
        self.assertFalse(customer.mail_id.recipient_ids)
        self.assertEqual(self.env['res.partner'].search_count([]), count)
        self.assertEqual(existing.name, 'Unrelated account')
        self.assertEqual(len(draft.notification_ids.mail_id), 2)
        self.assertEqual(draft.notification_ids.filtered(lambda item: item.kind == 'internal').mail_id.email_to, self.sales.email)
        self.assertIn('non conferma un ordine', customer.mail_id.body_html)
        self.assertIn(draft.name, customer.mail_id.body_html)
        self.assertIn(self.product.name, customer.mail_id.body_html)
        # Native SMTP failure must not mutate or recreate the business request.
        with patch.object(type(self.env['ir.mail_server']), '_connect__', side_effect=ConnectionError('Synthetic SMTP failure')) as smtp:
            customer.mail_id.send()
        smtp.assert_called_once()
        self.env['torrepulia.request.notification']._cron_prepare()
        self.assertEqual(customer.mail_state, 'exception')
        self.assertEqual(draft.state, 'submitted')
        self.assertEqual(len(draft.notification_ids.mail_id), 2)

    def test_submission_wakes_preparation_and_mail_queue(self):
        prepare = self.env.ref('website_torrepulia_request.cron_prepare_request_notifications')
        queue = self.env.ref('mail.ir_cron_mail_scheduler_action')
        Trigger = self.env['ir.cron.trigger'].sudo()
        before = {cron: Trigger.search_count([('cron_id', '=', cron.id)]) for cron in (prepare, queue)}
        site, session, draft = self._draft()
        self._line(draft, site)
        self._submit(draft, site)
        # The receipt does not wait for the five-minute run nor for the hourly mail queue.
        self.assertEqual(Trigger.search_count([('cron_id', '=', prepare.id)]), before[prepare] + 1)
        with patch.object(type(self.env['mail.mail']), 'send', side_effect=AssertionError('No SMTP during preparation')):
            self.env['torrepulia.request.notification']._cron_prepare()
        self.assertEqual(Trigger.search_count([('cron_id', '=', queue.id)]), before[queue] + 1)

    def test_receipt_prices_only_when_authorized_at_both_boundaries(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        self.final(site, session, draft)
        customer = draft.notification_ids.filtered(lambda item: item.kind == 'customer')
        self.assertIn('Totale prodotti della richiesta', customer._body_html())
        self.website.torrepulia_request_show_prices = False
        hidden = customer._body_html()
        self.assertNotIn('Totale prodotti', hidden)
        self.assertNotIn(draft.public_receipt['products_total_display'], hidden)
        fresh = site._torrepulia_session_request(session, create=True)
        self._line(fresh, site)
        self.final(site, session, fresh)
        self.website.torrepulia_request_show_prices = True
        self.assertNotIn('Totale prodotti', fresh.notification_ids.filtered(lambda item: item.kind == 'customer')._body_html())

    def test_notification_acl_and_wrong_stage(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        self._submit(draft, site)
        for user in (self.public, self.portal):
            with self.assertRaises(AccessError):
                draft.notification_ids.with_user(user).read(['state'])
        self.assertEqual(len(draft.with_user(self.sales).notification_ids.read(['state'])), 2)
        with self.assertRaises(AccessError):
            draft.notification_ids.with_user(self.sales).write({'state': 'pending'})
        won = self.env['crm.stage'].create({'name': 'Won test', 'is_won': True})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.website.torrepulia_request_stage_id = won
        other_team = self.env['crm.team'].create({'name': 'Other team'})
        stage = self.env['crm.stage'].create({'name': 'Other team stage', 'team_ids': [fields.Command.set(other_team.ids)]})
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.website.torrepulia_request_stage_id = stage

    def test_native_contact_normalization_and_invalid_phone(self):
        site, session, draft = self._draft()
        self._line(draft, site)
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            draft._submit(site, {'contact_name': 'Guest', 'email': 'guest@example.invalid', 'phone': 'not a phone'})
        draft.invalidate_recordset()
        self.assertEqual(draft.state, 'draft')
        self.assertFalse(draft.opportunity_id)
        draft._submit(site, {'contact_name': '  Guest  ', 'email': 'GUEST@example.invalid', 'phone': '+39 06 6982 0000'})
        self.assertEqual(draft.contact_name, 'Guest')
        self.assertEqual(draft.phone, '+390669820000')
        self.assertEqual(draft.opportunity_id.phone, draft.phone)

    def test_native_utm_cookie_attribution_is_preserved_at_submission(self):
        campaign = self.env['utm.campaign'].create({'name': 'Final native cookie campaign'})
        source = self.env['utm.source'].create({'name': 'Final native cookie source'})
        with patch('odoo.addons.utm.models.utm_mixin.request', SimpleNamespace(cookies={
                'odoo_utm_campaign': campaign.name, 'odoo_utm_source': source.name})):
            site, session, draft = self._draft()
        self.assertEqual(draft.campaign_id, campaign)
        self.assertEqual(draft.source_id, source)
        self._line(draft, site)
        self._submit(draft, site)
        self.assertEqual(draft.opportunity_id.campaign_id, campaign)
        self.assertEqual(draft.opportunity_id.source_id, source)
        self.assertEqual(draft.submission_snapshot['campaign'], campaign.name)
