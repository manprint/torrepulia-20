"""Real PostgreSQL transactions, ONLY the disposable torrepulia_request_test DB.

Submitted synthetic fixtures are retained: never bypass snapshot deletion guards.
"""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
import secrets

from odoo import api
from odoo.http.retrying import retrying
from odoo.addons.website_torrepulia_request.models.review import ReviewValidation


def run(env):
    if env.cr.dbname != 'torrepulia_request_test':
        raise RuntimeError('Use ONLY torrepulia_request_test: this QA commits synthetic fixtures.')
    name = 'Review concurrency QA ' + secrets.token_hex(6)
    team = env['crm.team'].create({'name': name, 'company_id': env.company.id})
    site = env['website'].create({'name': name, 'company_id': env.company.id,
        'torrepulia_request_team_id': team.id, 'torrepulia_commercial_mode': 'request',
        'torrepulia_request_show_prices': False})
    product = env['product.product'].create({'name': name, 'is_published': True, 'website_id': site.id, 'torrepulia_request_liters': 5})
    public_id = env.ref('base.public_user').id
    website_id, company_id = site.id, site.company_id.id
    visitor = site.with_user(public_id).with_context(website_id=website_id)
    session = {'torrepulia_request_%s' % website_id: secrets.token_hex(32)}
    digest = secrets.token_hex(32)
    draft = visitor._torrepulia_session_request(session, create=True)
    draft._set_selection(visitor, product.with_env(visitor.env), 2)
    state = visitor._request_selection_state(session)
    payload = {'selection_id': state['selection_id'], 'revision': state['revision'],
        'operation_id': secrets.token_hex(16), 'contact_name': 'Synthetic Review QA',
        'email': 'review-concurrency@example.invalid', 'phone': '', 'notes': '', 'privacy_accepted': True}
    registry = env.registry
    env.cr.commit()

    def race(functions):
        barrier = Barrier(2)

        def worker(index):
            with registry.cursor() as cr:
                actor = api.Environment(cr, public_id, {'website_id': website_id, 'allowed_company_ids': [company_id]})
                website = actor['website'].browse(website_id)
                website.read(['name'])  # establish both RR snapshots before writing
                barrier.wait(timeout=15)
                return retrying(partial(functions[index], website), env=actor, close_on_commit=False)

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, (0, 1)))

    def submit(website, values=payload):
        try:
            return website._request_submit_review(dict(session), values, digest,
                website.env['product.pricelist'], website.env['account.fiscal.position'], lambda: None)
        except ReviewValidation:
            return {'review_conflict': True}

    duplicate = race([submit, submit])
    assert sorted(result['replayed'] for result in duplicate) == [False, True], duplicate
    env.cr.rollback(); env.invalidate_all()
    records = env['torrepulia.request'].search([('website_id', '=', website_id), ('state', '=', 'submitted')])
    assert len(records) == 1 and records.line_ids.quantity == 2
    assert env['crm.lead'].search_count([('team_id', '=', team.id)]) == 1
    assert len(records.notification_ids) == 2
    assert env['torrepulia.request'].search_count([('website_id', '=', website_id), ('state', '=', 'draft')]) == 1
    assert not env['sale.order'].search_count([('website_id', '=', website_id)])
    print('PASS concurrent duplicate final submit: one immutable request, one opportunity, two notification intents, one prepared draft, one replay, no orders')

    def prepare_notifications(website):
        # This QA prepares native mail records only; never invokes SMTP.
        website.env['torrepulia.request.notification'].sudo()._cron_prepare()
        return True

    race([prepare_notifications, prepare_notifications])
    env.cr.rollback(); env.invalidate_all()
    customer = records.notification_ids.filtered(lambda item: item.kind == 'customer')
    assert customer.state == 'queued', customer.error
    assert len(customer.mail_id) == 1
    assert env['mail.mail'].search_count([('model', '=', 'torrepulia.request.notification'), ('res_id', '=', customer.id)]) == 1
    assert records.notification_ids.filtered(lambda item: item.kind == 'internal').state == 'failed'  # team intentionally empty
    print('PASS concurrent notification workers: one customer email queued, no SMTP, missing team recipient isolated')

    # Race a fresh submit against a quantity change at the same revision.
    draft = visitor._torrepulia_session_request(session, create=True)
    draft._set_selection(visitor, product.with_env(visitor.env), 2)
    state = visitor._request_selection_state(session)
    final_payload = dict(payload, selection_id=state['selection_id'], revision=state['revision'], operation_id=secrets.token_hex(16))
    edit_payload = {'operation': 'set', 'operation_id': secrets.token_hex(16), 'selection_id': state['selection_id'],
        'revision': state['revision'], 'line_key': state['lines'][0]['key'], 'quantity': 3}
    env.cr.commit()

    def edit(website):
        return website._request_selection_apply(dict(session), edit_payload)

    submitted, edited = race([partial(submit, values=final_payload), edit])
    assert bool(submitted.get('review_conflict')) != bool(edited.get('code') == 'conflict'), (submitted, edited)
    env.cr.rollback(); env.invalidate_all()
    record = env['torrepulia.request'].search([('website_id', '=', website_id), ('selection_id', '=', state['selection_id'])])
    if record.state == 'submitted':
        assert record.line_ids.quantity == 2 and edited['code'] == 'conflict'
    else:
        assert record.line_ids.quantity == 3 and submitted['review_conflict']
    print('PASS concurrent quantity edit/final submit: one wins, stale operation conflicts; no lost or mutable submitted lines')
    print('Synthetic submitted fixtures retained only in the disposable test database.')
