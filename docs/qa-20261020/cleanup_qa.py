import json
from pathlib import Path

assert env.cr.dbname == 'torrepulia_cinematic_install'
path = Path('/tmp/torrepulia-ui-auth.json')
auth = json.loads(path.read_text())
page = env['website.page'].browse(auth['qa_page_id']).exists()
view = env['ir.ui.view'].browse(auth['qa_view_id']).exists()
if page:
    assert page.url == auth['qa_url'] and page.website_id.id == auth['website_id']
    translations = page.view_id._fields['arch_db']._get_stored_translations(page.view_id)
    for arch in translations.values():
        assert 'ui-qa@example.invalid' not in arch
        assert 'data-tp-review-form' not in arch
        assert 'data-review-lazy' in arch
    page.unlink()
if view:
    view.unlink()
user = env['res.users'].browse(auth['user_id'])
assert user.login == auth['login']
user.with_context(tracking_disable=True).write({'active': False, 'password': __import__('secrets').token_urlsafe(48)})
env.cr.commit()
path.unlink()
print('PASS Builder saved markup contains no personal form or contact values.')
print('QA page/view removed; temporary account archived and credentials rotated/deleted.')
