import json,secrets
from pathlib import Path
assert env.cr.dbname=='torrepulia_cinematic_install'
p=Path('/tmp/stock-design-auth.json');auth=json.loads(p.read_text())
page=env['website.page'].browse(auth['qa_page_id']).exists()
view=env['ir.ui.view'].browse(auth['qa_view_id']).exists()
user=env['res.users'].browse(auth['user_id']).exists()
assert not page or page.url.startswith('/qa-stock-builder-') and page.website_id.id==auth['website_id']
assert not view or view.key.startswith('torrepulia.stock.builder.qa.')
assert user and user.login.startswith('stock-builder-') and user.login.endswith('@example.invalid')
if page:page.unlink()
if view.exists():view.unlink()
user.with_context(no_reset_password=True,tracking_disable=True).write({'active':False,'password':secrets.token_urlsafe(48)})
env.cr.commit()
p.unlink()
Path('/tmp/stock-design-cleanup-checks.json').write_text(json.dumps({'qa_page_removed':not page.exists(),'qa_view_removed':not view.exists(),'qa_user_archived':not user.active,'auth_file_removed':not p.exists()},indent=2))
print('Temporary page removed; QA user archived and password rotated; private credentials removed.')
