"""Run with Odoo shell: runpy.run_path(..., init_globals={env, action, backup_path}).

No page architectures are written. Default action is a read-only plan.
"""
import json
from pathlib import Path


def run(env, action='plan', backup_path=None):
    home = env.ref('website_torrepulia_theme.page_home')
    website = home.website_id
    assert website and website.torrepulia_theme_enabled, 'Expected the provisioned Torrepulia website'
    menus = website.with_context(lang='en_US').menu_id.child_id
    fields = ['name', 'sequence', 'torrepulia_navigation_hidden', 'torrepulia_seasonal']
    specification = {
        '/shop': ('Acquista olio', 10, False, False),
        '/l-olio': ('La Peranzana', 20, False, False),
        '/aboutus': ('La famiglia', 30, False, False),
        '/contactus': ('Contatti', 40, False, False),
        '/prenotailtuoolio': ('Olio nuovo', 50, False, True),
        '/': ('Home', 60, True, False),
        '/territorio': ('Il territorio', 70, True, False),
    }
    changes = []
    for url, values in specification.items():
        matches = menus.filtered(lambda menu: menu.url == url)
        assert len(matches) == 1, f'Review missing/duplicate destination: {url}'
        menu = matches
        before = {field: menu[field] for field in fields}
        after = dict(zip(fields, values))
        if before != after:
            changes.append({'id': menu.id, 'url': url, 'before': before, 'after': after})
    if action == 'plan':
        print(json.dumps(changes, ensure_ascii=False, indent=2))
        return
    assert action in ('apply', 'restore') and backup_path
    path = Path(backup_path)
    if action == 'apply':
        if not changes:
            print('Already configured; no changes')
            return
        # Exclusive creation prevents overwriting the original rollback evidence.
        with path.open('x', encoding='utf-8') as stream:
            json.dump({'database': env.cr.dbname, 'website': website.id, 'changes': changes}, stream, ensure_ascii=False, indent=2)
        for item in changes:
            menus.browse(item['id']).write(item['after'])
    else:
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['database'] == env.cr.dbname and data['website'] == website.id
        for item in data['changes']:
            menu = menus.filtered(lambda menu: menu.id == item['id'])
            assert len(menu) == 1 and menu.url == item['url']
            current = {field: menu[field] for field in fields}
            assert current in (item['before'], item['after']), 'Menu changed since migration: review before restoring'
        for item in data['changes']:
            menus.browse(item['id']).write(item['before'])
    env.cr.commit()
    print(action, 'complete; page contents and translations preserved')


if 'env' in globals():
    run(env, globals().get('action', 'plan'), globals().get('backup_path'))
