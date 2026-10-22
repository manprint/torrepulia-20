"""Local HTTP smoke test ONLY on the disposable restored migration database.

Run inside the development container after migration_qa.py has passed. No
browser, final submission, SMTP connection or real payment is performed.
"""
import json
import os
from pathlib import Path
import runpy
import re
import secrets
import subprocess
import time
from urllib.parse import urljoin, urlsplit

import psycopg2
import requests


def run():
    database = 'torrepulia_migration_test'
    connection = dict(host=os.environ['HOST'], user=os.environ['USER'], password=os.environ['PASSWORD'])
    with psycopg2.connect(dbname=database, **connection) as con:
        with con.cursor() as cr:
            cr.execute('UPDATE ir_cron SET active=false')
            cr.execute('UPDATE ir_mail_server SET active=false')
            cr.execute("UPDATE mail_mail SET state='cancel' WHERE state in ('outgoing','exception')")
            cr.execute('UPDATE payment_provider SET is_live=false')
    args = ['odoo', '-d', database, '--db_host', connection['host'],
            '--db_user', connection['user'], '--db_password', connection['password'],
            '--max-cron-threads=0', '--log-level=info', '--log-handler=odoo:INFO']
    preparation = """import json
from odoo import fields
from odoo.fields import Domain
assert env.cr.dbname == 'torrepulia_migration_test'
site = env['website'].search([('torrepulia_theme_enabled', '=', True)], limit=1)
team = env['crm.team'].search([('name','=','Migration HTTP synthetic team'), ('company_id','=',site.company_id.id)], limit=1)
if not team:
 team = env['crm.team'].create({'name': 'Migration HTTP synthetic team', 'company_id': site.company_id.id})
site.write({'torrepulia_commercial_mode': 'request', 'torrepulia_request_team_id': team.id, 'torrepulia_request_show_prices': False})
templates = env['product.template'].search(site.sale_product_domain() & Domain('is_published','=',True))
products = templates.product_variant_ids.filtered(lambda p: p.type != 'combo' and not p.product_tmpl_id.valid_product_template_attribute_line_ids)[:2]
assert len(products) == 2, 'Two simple published products are needed for this smoke test'
site.torrepulia_campaign_id.write({'state':'open', 'line_ids': [fields.Command.clear(), *[fields.Command.create({'product_id': p.id, 'sequence': i}) for i,p in enumerate(products)]]})
print('QA_DATA=' + json.dumps([{'id':p.id,'url':p.website_url} for p in products]))
env.cr.commit()
"""
    prepared = subprocess.run([args[0], 'shell', *args[1:], '--no-http', '--logfile=/tmp/torrepulia-migration-http-prepare.log'],
                              input=preparation, text=True, capture_output=True)
    if prepared.returncode:
        Path('/tmp/torrepulia-migration-http-prepare-output.log').write_text(prepared.stdout + prepared.stderr)
        raise RuntimeError('Clone fixture preparation failed; inspect the local preparation log.')
    data = json.loads(next(line[len('QA_DATA='):] for line in prepared.stdout.splitlines() if line.startswith('QA_DATA=')))
    with open('/tmp/torrepulia-migration-http-process.log', 'w') as log:
        process = subprocess.Popen([*args, '--db-filter=^torrepulia_migration_test$', '--http-interface=127.0.0.1',
            '--http-port=8080', '--logfile=/tmp/torrepulia-migration-http.log'], stdout=log, stderr=subprocess.STDOUT)
        try:
            session = requests.Session()
            base = 'http://127.0.0.1:8080'
            for _ in range(40):
                if process.poll() is not None:
                    raise RuntimeError('Local migration HTTP server exited.')
                try:
                    if session.get(base + '/web/login?db=' + database, timeout=2, allow_redirects=False).status_code in (200, 303):
                        break
                except requests.RequestException:
                    pass
                time.sleep(0.5)
            else:
                raise RuntimeError('Local migration HTTP server did not become ready.')
            def get(path):
                # Preserve native language canonicalisation, while refusing
                # redirects to another host or an unrelated route/login page.
                target = base + path
                for _ in range(5):
                    response = session.get(target, timeout=60, allow_redirects=False)
                    if response.status_code not in (301, 302, 303, 307, 308):
                        return response
                    target = urljoin(target, response.headers['Location'])
                    parsed, original = urlsplit(target), urlsplit(path)
                    assert parsed.scheme == 'http' and parsed.netloc == '127.0.0.1:8080'
                    prefix = parsed.path[:-len(original.path)] if parsed.path.endswith(original.path) else None
                    assert prefix == '' or prefix is not None and re.fullmatch(r'/[a-zA-Z]{2,3}(?:_[a-zA-Z]{2})?', prefix), target
                raise AssertionError('Too many local language redirects')
            for path in ['/shop', data[0]['url'], '/prenotailtuoolio', '/la-tua-richiesta', '/richiesta-inviata']:
                response = get(path)
                assert response.status_code == 200, (path, response.status_code, response.headers.get('Location'))
            print('PASS restored database HTTP: catalog, real product page, migrated seasonal page, summary and neutral legacy receipt return 200')
            content = get('/torrepulia/campaign/content').json()
            assert content['open'] and len(content['configurations']) == 2
            for product, quantity in zip(data, (2, 1)):
                bootstrap = get('/torrepulia/request/current').json()
                state = bootstrap['state']
                response = session.post(base + '/torrepulia/request/update', data={
                    'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps({
                        'operation': 'add', 'operation_id': secrets.token_hex(16),
                        'selection_id': state['selection_id'], 'revision': state['revision'],
                        'product_id': product['id'], 'quantity': quantity})}, timeout=30)
                assert response.status_code == 200, response.status_code
            preview = get('/torrepulia/request/preview').json()['state']
            assert preview['quantity'] == 3 and len(preview['lines']) == 2
            assert 'products_total_display' not in preview
            old = session.post(base + '/website/form/crm.lead', data={
                'torrepulia_reservation': '2026/2027', 'name': 'Prenotazione olio nuovo 2026/2027'}, timeout=30)
            assert 'error' in old.json()
            print('PASS restored database HTTP: two existing catalog products selected, three packages in preview, hidden prices, old seasonal POST rejected')
            qa = runpy.run_path(str(Path(__file__).with_name('migration_qa.py')))
            baseline = json.loads(Path(qa['BASELINE']).read_text())
            with psycopg2.connect(dbname=database, **connection) as con:
                with con.cursor() as cr:
                    assert qa['snapshot'](cr) == baseline['business']
            print('PASS HTTP smoke leaves historical CRM/orders/prices/stock/payment/invoice fingerprints unchanged; no final send')
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == '__main__':
    run()
