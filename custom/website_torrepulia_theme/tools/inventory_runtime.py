"""Read native database views/assets in both local databases before cleanup."""
import json
from pathlib import Path
from local_qa import shell

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'docs' / 'qa-final'
output.mkdir(exist_ok=True)
for database in ['torrepulia_cinematic_install', 'odoo_dev']:
    data = json.loads(shell('''
import json
views = env['ir.ui.view'].with_context(active_test=False, lang='en_US').search([('arch_db', 'ilike', 'website_torrepulia_theme')])
assets = env['ir.asset'].with_context(active_test=False).search([])
attachments = env['ir.attachment'].search([('mimetype', 'in', ['text/scss', 'text/css', 'application/javascript'])])
print(json.dumps({'views': [{'id': view.id, 'key': view.key, 'active': view.active, 'arch': view.arch_db, 'arch_prev': view.arch_prev if 'arch_prev' in view._fields else ''} for view in views],
    'assets': assets.read(['name', 'path', 'active']),
    'custom_assets': [{'id': item.id, 'url': item.url, 'text': (item.raw or b'').decode('utf-8', 'replace')} for item in attachments if not (item.url or '').startswith('/web/assets/')],
    'pages': env['website.page'].search([]).read(['url', 'is_published', 'view_id'])}, ensure_ascii=False))
''', database=database))
    path = output / f'runtime-{database}.json'
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(database, len(data['views']), 'views (including archives),', len(data['assets']), 'asset rules')
