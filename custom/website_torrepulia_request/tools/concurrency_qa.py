"""Run through Odoo shell ONLY on the dedicated disposable test database.

runpy.run_path('/mnt/torrepulia/custom/website_torrepulia_request/tools/concurrency_qa.py')['run'](env)
"""
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import hashlib
import re
import secrets
from threading import Barrier

from odoo import api
from odoo.http.retrying import retrying


def run(env):
    if env.cr.dbname != 'torrepulia_request_test':
        raise RuntimeError('This QA commits fixtures; use ONLY torrepulia_request_test.')
    # Recover only this script's precisely named fixtures from an interrupted run.
    leftovers = env['website'].search([('name', '=like', 'Concurrency QA %')]).filtered(
        lambda site: re.fullmatch(r'Concurrency QA [0-9a-f]{12}', site.name))
    if leftovers:
        names = leftovers.mapped('name')
        requests = env['torrepulia.request'].search([('website_id', 'in', leftovers.ids)])
        if requests.filtered(lambda item: item.state != 'draft'):
            raise RuntimeError('Refusing cleanup of a submitted QA request.')
        requests.unlink()
        env['product.template'].search([('name', 'in', names)]).unlink()
        leftovers.unlink()
        env['crm.team'].search([('name', 'in', names)]).unlink()
        env.cr.commit()
    suffix = secrets.token_hex(6)
    team = env['crm.team'].create({'name': 'Concurrency QA ' + suffix, 'company_id': env.company.id})
    website = env['website'].create({
        'name': 'Concurrency QA ' + suffix, 'company_id': env.company.id,
        'torrepulia_request_team_id': team.id, 'torrepulia_commercial_mode': 'request',
    })
    product = env['product.product'].create({'name': 'Concurrency QA ' + suffix, 'is_published': True})
    website_id, product_id, company_id = website.id, product.id, website.company_id.id
    public_id = env.ref('base.public_user').id
    registry = env.registry
    session = {'torrepulia_request_%s' % website_id: secrets.token_hex(32)}
    visitor = website.with_user(public_id).with_context(website_id=website_id)
    state = visitor._request_selection_state(session)
    env.cr.commit()

    def parallel(payloads=None, initial_session=None):
        barrier = Barrier(2)

        def worker(index):
            with registry.cursor() as cr:
                actor = api.Environment(cr, public_id, {'website_id': website_id, 'allowed_company_ids': [company_id]})
                site = actor['website'].browse(website_id)
                # Both transactions establish a snapshot before either writes.
                site.read(['name'])
                barrier.wait(timeout=15)
                local_session = dict(initial_session if initial_session is not None else session)
                operation = partial(site._request_selection_apply, local_session, payloads[index]) if payloads else partial(site._request_selection_state, local_session)
                return retrying(operation, env=actor, close_on_commit=False)

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, (0, 1)))

    try:
        same = dict(operation='add', operation_id=secrets.token_hex(16), selection_id=state['selection_id'],
                    revision=state['revision'], product_id=product_id, quantity=2)
        duplicate = parallel([same, same])
        assert all(result['ok'] and result['state']['quantity'] == 2 for result in duplicate), duplicate
        assert sorted(result['replayed'] for result in duplicate) == [False, True], duplicate
        print('PASS concurrent duplicate increment: one application, one replay, total 2')

        state = duplicate[0]['state']
        different = [dict(same, operation_id=secrets.token_hex(16), quantity=1,
                          selection_id=state['selection_id'], revision=state['revision']) for i in range(2)]
        raced = parallel(different)
        assert sum(result['ok'] for result in raced) == 1, raced
        assert all(result['state']['quantity'] == 3 for result in raced), raced
        losing_index = next(i for i, result in enumerate(raced) if not result['ok'])
        losing = raced[losing_index]['state']
        revised = dict(different[losing_index], revision=losing['revision'])
        env.cr.rollback()
        env.invalidate_all()
        result = retrying(partial(visitor._request_selection_apply, session, revised), env=visitor.env, close_on_commit=False)
        assert result['ok'] and result['state']['quantity'] == 4, result
        print('PASS concurrent distinct edits: one conflict, explicit reapply preserves both increments')

        fresh_session = {'torrepulia_request_%s' % website_id: secrets.token_hex(32)}
        initialized = parallel(initial_session=fresh_session)
        assert initialized[0]['selection_id'] == initialized[1]['selection_id'], initialized
        env.cr.rollback()
        env.invalidate_all()
        digest = hashlib.sha256(next(iter(fresh_session.values())).encode()).hexdigest()
        assert env['torrepulia.request'].search_count([('website_id', '=', website_id), ('session_digest', '=', digest)]) == 1
        print('PASS concurrent initialization: one session, one draft, same selection identity')
    finally:
        env.cr.rollback()
        env.invalidate_all()
        env['torrepulia.request'].search([('website_id', '=', website_id)]).unlink()
        product.product_tmpl_id.unlink()
        website.unlink()
        team.unlink()
        env.cr.commit()
