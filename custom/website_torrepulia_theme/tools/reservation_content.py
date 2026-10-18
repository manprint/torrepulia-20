"""Explicit plan/apply/restore for the two provisioned Torrepulia pages only.

Run with Odoo shell using runpy.run_path and globals env/action/backup_path.
Default is read-only. No menu, metadata, publication or indexing fields are written.
"""
import copy
import hashlib
import json
from pathlib import Path

from lxml import etree
from odoo.tools.translate import StoredTranslations


MODULE = 'website_torrepulia_theme'


def stored(view):
    return dict(view._fields['arch_db']._get_stored_translations(view) or {})


def section(env, key):
    root = etree.fromstring(env.ref(MODULE + '.' + key).with_context(lang='en_US').arch_db.encode())
    result = copy.deepcopy(root.find('section'))
    assert result is not None
    return result


def transform(env, page_key, arch):
    root = etree.fromstring(arch.encode())
    wraps = root.xpath('.//div[@id="wrap"]')
    assert len(wraps) == 1, 'Review ambiguous page structure'
    wrap = wraps[0]
    if page_key == 'home':
        proofs = wrap.xpath('./section[@data-snippet="s_torrepulia_value_proofs"]')
        if proofs:
            assert len(proofs) == 1, 'Review duplicate value proofs'
            return arch  # Never overwrite a subsequently edited strip.
        hero = wrap.xpath('./section[@data-snippet="s_cinematic_0"]')
        assert len(hero) == 1, 'Review missing/duplicate homepage hero'
        before = [etree.tostring(node) for node in wrap]
        wrap.insert(wrap.index(hero[0]) + 1, section(env, 's_torrepulia_value_proofs'))
        assert before == [etree.tostring(node) for node in wrap if node.get('data-snippet') != 's_torrepulia_value_proofs']
    else:
        if wrap.xpath('./section[@data-snippet="s_torrepulia_reservation_hero"]'):
            return arch  # Preserve later Website Builder changes.
        for node in list(wrap):
            wrap.remove(node)
        wrap.text = '\n'
        for key in ['s_torrepulia_reservation_hero', 's_torrepulia_reservation_conditions', 's_torrepulia_reservation_form']:
            wrap.append(section(env, key))
    return etree.tostring(root, encoding='unicode')


def run(env, action='plan', backup_path=None):
    assert action in ('plan', 'apply', 'restore')
    pages = {key: env.ref(MODULE + '.page_' + key) for key in ('home', 'reservation')}
    website = pages['home'].website_id
    assert website and website.torrepulia_theme_enabled
    assert pages['reservation'].website_id == website and pages['reservation'].url == '/prenotailtuoolio'
    views = {key: page.view_id for key, page in pages.items()}
    assert not env['ir.ui.view.custom'].search_count([('ref_id', 'in', [v.id for v in views.values()])]), 'Review view customizations before proceeding'
    if action != 'plan':
        assert backup_path, 'An exclusive backup file is required'
        env.cr.execute('SELECT id FROM ir_ui_view WHERE id IN %s FOR UPDATE', [tuple(v.id for v in views.values())])
        for view in views.values():
            view.invalidate_recordset(['arch_db', 'arch_fs', 'arch_updated'])
    changes = []
    for key, view in views.items():
        before = stored(view)
        assert before and 'en_US' in before
        # StoredTranslations is verified against installed Odoo 20 fields_textual.py.
        # Retain each language's own Builder structure, including deferred translations.
        after = {lang: transform(env, key, arch) for lang, arch in before.items()}
        if before != after:
            changes.append({'page': key, 'view_key': view.key, 'before': before, 'after': after,
                            'arch_fs': view.arch_fs, 'arch_updated': view.arch_updated})
    if action == 'plan':
        return [{'page': item['page'], 'languages': list(item['before']),
                 'before_hash': hashlib.sha256(json.dumps(item['before'], sort_keys=True).encode()).hexdigest()}
                for item in changes]
    path = Path(backup_path)
    if action == 'apply':
        if not changes:
            return {'changed': 0}
        with path.open('x', encoding='utf-8') as stream:
            json.dump({'database': env.cr.dbname, 'website': website.id, 'changes': changes}, stream, ensure_ascii=False, indent=2)
        for item in changes:
            views[item['page']].write({'arch_db': StoredTranslations(item['after']), 'arch_fs': False, 'arch_updated': True})
            assert stored(views[item['page']]) == item['after']
    else:
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['database'] == env.cr.dbname and data['website'] == website.id
        for item in data['changes']:
            view = views[item['page']]
            assert view.key == item['view_key']
            assert stored(view) in (item['before'], item['after']), 'Page edited since apply: review before restoring'
        for item in data['changes']:
            views[item['page']].write({'arch_db': StoredTranslations(item['before']),
                                      'arch_fs': item['arch_fs'], 'arch_updated': item['arch_updated']})
        changes = data['changes']
    return {'changed': len(changes), 'action': action}


if 'env' in globals():
    print(json.dumps(run(env, globals().get('action', 'plan'), globals().get('backup_path')), ensure_ascii=True))
