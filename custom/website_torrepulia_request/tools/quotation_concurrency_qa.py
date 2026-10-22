"""Real RR transactions. Run ONLY in the disposable torrepulia_request_test DB."""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
import secrets

from odoo import api
from odoo.http.retrying import retrying


def run(env):
    if env.cr.dbname != 'torrepulia_request_test':
        raise RuntimeError('This QA commits fixtures: only torrepulia_request_test is allowed.')
    name = 'Quotation concurrency QA ' + secrets.token_hex(6)
    team = env['crm.team'].create({'name': name, 'company_id': env.company.id})
    site = env['website'].create({'name': name, 'company_id': env.company.id,
        'torrepulia_request_team_id': team.id, 'torrepulia_commercial_mode': 'request'})
    product = env['product.product'].create({'name': name, 'is_published': True, 'website_id': site.id})
    partner = env['res.partner'].create({'name': name, 'email': 'quotation-concurrency@example.invalid'})
    visitor = site.with_user(env.ref('base.public_user')).with_context(website_id=site.id)
    request = visitor._torrepulia_session_request({}, create=True)
    request._set_selection(visitor, product.with_env(visitor.env), 2)
    request._submit(visitor, {'contact_name': name, 'email': partner.email})
    request = request.with_env(env)
    first = env['torrepulia.request.quotation.wizard'].create({'request_id': request.id, 'partner_id': partner.id})
    second = env['torrepulia.request.quotation.wizard'].create({'request_id': request.id, 'partner_id': partner.id})
    actor_id, company_id, registry = env.uid, env.company.id, env.registry
    env.cr.commit()

    def race(wizards):
        barrier = Barrier(2)

        def worker(wizard_id):
            with registry.cursor() as cr:
                actor = api.Environment(cr, actor_id, {'allowed_company_ids': [company_id]})
                wizard = actor['torrepulia.request.quotation.wizard'].browse(wizard_id)
                wizard.read(['request_id'])  # both snapshots predate either result
                barrier.wait(timeout=15)
                return retrying(partial(wizard.action_prepare), env=actor, close_on_commit=False)['res_id']

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, wizards.ids))

    created = race(first | second)
    env.cr.rollback(); env.invalidate_all()
    assert created[0] == created[1], created
    assert len(request.quotation_ids) == 1
    assert request.quotation_ids.state == 'draft'
    assert request.quotation_ids.order_line.product_uom_qty == 2
    assert request.line_ids.quantity == 2
    print('PASS concurrent independent preparation dialogs: one native draft quotation, identical result, immutable request')

    one, two = env['torrepulia.request.quotation.wizard'].create([
        {'request_id': request.id, 'partner_id': partner.id, 'create_revision': True, 'reason': 'Synthetic revision A'},
        {'request_id': request.id, 'partner_id': partner.id, 'create_revision': True, 'reason': 'Synthetic revision B'},
    ])
    env.cr.commit()
    revisions = race(one | two)
    env.cr.rollback(); env.invalidate_all()
    assert revisions[0] == revisions[1] and revisions[0] != created[0], revisions
    assert len(request.quotation_ids) == 2
    latest = env['sale.order'].browse(revisions[0])
    assert latest.torrepulia_revision_of_id.id == created[0]
    assert latest.torrepulia_revision_reason
    assert not request.quotation_ids.picking_ids
    assert not request.quotation_ids.invoice_ids
    print('PASS concurrent revision dialogs from the same base: one traced revision, no confirmation, stock moves or invoices')
    print('Synthetic submitted fixtures retained only in the disposable test database; no SMTP or payments.')
