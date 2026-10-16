"""Read builder DOM and console in an isolated local diagnostic session."""
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from local_qa import shell

account = json.loads(shell('''
import json, secrets
password = secrets.token_urlsafe(30)
login = 'builder-diagnostic-' + secrets.token_hex(5) + '@local.invalid'
user = env['res.users'].with_context(no_reset_password=True, mail_create_nosubscribe=True).create({
    'name': 'Local builder diagnostic', 'login': login, 'password': password,
    'group_ids': [(6, 0, [env.ref('base.group_user').id, env.ref('website.group_website_designer').id])]})
env.cr.commit()
print(json.dumps({'login': login, 'password': password, 'id': user.id}))
''', database='torrepulia_cinematic_install'))
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1500, 'height': 980})
        response = context.request.post('http://127.0.0.1:8069/web/session/authenticate', data={
            'jsonrpc': '2.0', 'method': 'call', 'params': {'db': 'torrepulia_cinematic_install',
            'login': account['login'], 'password': account['password']}})
        if response.json().get('error'):
            raise RuntimeError('Local diagnostic authentication failed')
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
        page.goto('http://127.0.0.1:8069/odoo/action-website.website_preview?path=%2F', wait_until='domcontentloaded')
        edit = page.get_by_role('button', name=re.compile(r'^(Edit|Modifica)$'))
        edit.wait_for(state='visible', timeout=60000)
        print('BACKEND', page.locator('body').inner_text()[-2200:], flush=True)
        edit.click()
        page.get_by_role('button', name=re.compile(r'^(Save|Salva)$')).wait_for(state='visible', timeout=60000)
        page.wait_for_timeout(8000)
        print('ERRORS', json.dumps(errors), flush=True)
        for frame in page.frames:
            print('FRAME', frame.url, flush=True)
            print(frame.evaluate('''() => ({
                wrap: document.querySelector('#wrap')?.outerHTML.slice(0,500),
                savableWrap: document.querySelector('#wrap')?.classList.contains('o_savable'),
                formatsBackground: document.querySelector('#formati') ? getComputedStyle(document.querySelector('#formati')).backgroundColor : null,
                areas: [...document.querySelectorAll('.o_editable,.o_savable,[data-oe-model]')].slice(0,12).map(el=>({tag:el.tagName,cls:el.className,attrs:[...el.attributes].filter(a=>a.name.startsWith('data-oe')||a.name==='contenteditable').map(a=>[a.name,a.value])})),
                disabled:document.querySelectorAll('.o_snippet_undroppable').length
            })'''), flush=True)
        page.screenshot(path=str(Path(__file__).resolve().parents[1] / 'docs' / 'qa' / 'builder-diagnostic.png'))
        browser.close()
finally:
    shell(f"env['res.users'].browse({account['id']}).active = False\nenv.cr.commit()", database='torrepulia_cinematic_install')
