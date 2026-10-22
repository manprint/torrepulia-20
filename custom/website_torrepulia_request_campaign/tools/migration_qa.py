"""Read-only assertions on a disposable restored database, never the original."""
import hashlib
import json
from pathlib import Path

from lxml import etree


DATABASE = 'torrepulia_migration_test'
BASELINE = '/tmp/torrepulia-migration-baseline.json'
TABLE_FIELDS = {
    'crm_lead': 'id,name,partner_id,email_from,phone,description,team_id,user_id,stage_id,company_id',
    'sale_order': 'id,name,partner_id,state,company_id,pricelist_id,currency_id',
    'sale_order_line': 'id,order_id,product_id,product_uom_id,product_uom_qty,price_unit,discount',
    'product_template': 'id,list_price,active,is_published,website_id,company_id',
    'stock_quant': 'id,product_id,location_id,quantity,reserved_quantity',
    'payment_transaction': 'id,reference,state,amount,currency_id,partner_id',
    'account_move': 'id,name,state,partner_id,amount_total,company_id',
}


def snapshot(cr):
    result = {}
    for table, fields in TABLE_FIELDS.items():
        # Trusted fixed identifiers only. Persist hashes/counts, never CRM PII.
        cr.execute('SELECT count(*), md5(coalesce(string_agg(md5(row(%s)::text), \'\' ORDER BY id), \'\')) FROM %s' % (fields, table))
        result[table] = list(cr.fetchone())
    return result


def save_baseline(cr):
    cr.execute('SELECT current_database()')
    if cr.fetchone()[0] != DATABASE:
        raise RuntimeError('Use only the disposable migration database.')
    result = {'business': snapshot(cr), 'pages': []}
    cr.execute("""SELECT p.view_id, p.website_id, p.url, p.is_published,
                  p.website_indexed, v.arch_db FROM website_page p
                  JOIN ir_ui_view v ON p.view_id=v.id
                  WHERE p.url::text LIKE '%/prenotailtuoolio%'
                     OR p.url::text LIKE '%/richiesta-inviata%'""")
    for view, site, url, published, indexed, arch in cr.fetchall():
        result['pages'].append({'view_id': view, 'website_id': site, 'url': url,
            'published': published, 'indexed': indexed,
            'translations': {lang: hashlib.sha256(value.encode()).hexdigest() for lang, value in arch.items()}})
    Path(BASELINE).write_text(json.dumps(result))
    print('PASS migration baseline: only hashes/counts and page metadata saved')


def run(env):
    if env.cr.dbname != DATABASE:
        raise RuntimeError('Use only the disposable migration database.')
    before = json.loads(Path(BASELINE).read_text())
    assert snapshot(env.cr) == before['business'], 'Historical business data changed'
    print('PASS historical CRM, orders/lines, prices, stock, payments and invoices: counts and business-field fingerprints unchanged')
    websites = env['website'].search([('torrepulia_theme_enabled', '=', True)])
    assert websites
    views = env['ir.ui.view']
    for old in before['pages']:
        page = env['website.page'].search([('view_id', '=', old['view_id']), ('website_id', '=', old['website_id'])])
        assert len(page) == 1
        assert page.is_published == old['published'] and page.website_indexed == old['indexed']
        url = dict(page._fields['url']._get_stored_translations(page))
        assert url == old['url']
        if '/prenotailtuoolio' in old['url'].values() and page.website_id in websites:
            backup = page.website_id.torrepulia_campaign_page_backup[str(old['view_id'])]['translations']
            assert {lang: hashlib.sha256(value.encode()).hexdigest() for lang, value in backup.items()} == old['translations']
            for arch in views.browse(old['view_id'])._fields['arch_db']._get_stored_translations(views.browse(old['view_id'])).values():
                tree = etree.fromstring(arch.encode())
                assert len(tree.xpath('.//*[@data-snippet="s_torrepulia_request_campaign"]')) == 1
                assert not tree.xpath('.//form[.//*[@name="torrepulia_reservation"] or .//*[@name="bib_filtrato"] or .//*[@name="bib_non_filtrato"] or .//*[@name="latta_filtrata"] or .//*[@name="latta_non_filtrata"]]')
    print('PASS restored original pages: one seasonal selector, no legacy form, original-language backup, URLs/publication/indexing unchanged')
    first = {view.id: dict(view._fields['arch_db']._get_stored_translations(view)) for view in env['website.page'].search([('url', '=', '/prenotailtuoolio')]).view_id}
    backups = {site.id: site.torrepulia_campaign_page_backup for site in websites}
    env['website']._install_request_campaign_pages()
    assert first == {view.id: dict(view._fields['arch_db']._get_stored_translations(view)) for view in views.browse(list(first))}
    assert backups == {site.id: site.torrepulia_campaign_page_backup for site in websites}
    assert all(site.torrepulia_commercial_mode == 'shop' and site.torrepulia_campaign_id.state == 'closed'
               and not site.torrepulia_campaign_id.line_ids for site in websites)
    assert not env['torrepulia.request'].search_count([])
    assert snapshot(env.cr) == before['business']
    print('PASS second migration: byte-identical translated content/backup; standard mode preserved; closed empty campaign; no requests auto-created')
    theme = env['ir.module.module'].search([('name', '=', 'website_torrepulia_theme')])
    print('Original theme recorded version unchanged:', theme.latest_version)
