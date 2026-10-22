"""Run using Odoo shell on the explicitly authorised local development DB."""
import json
import secrets
from pathlib import Path

assert env.cr.dbname == 'torrepulia_cinematic_install'
website = env['website'].search([('torrepulia_theme_enabled', '=', True)], limit=1)
assert website and website.torrepulia_campaign_id
campaign = website.torrepulia_campaign_id
approved = {
    'shipping_note': 'Spedizione in 48h dalla molitura (Nov-Dic)',
    'payment_note': 'Nessun anticipo, paghi alla spedizione',
    'price_note': 'Prezzo bloccato garantito',
}
campaign.write({key: value for key, value in approved.items() if not campaign[key]})
page = env['website.page'].search([('website_id', '=', website.id), ('url', '=', '/prenotailtuoolio')])
assert len(page) == 1
groups = [env.ref(xmlid).id for xmlid in ('base.group_system', 'website.group_website_designer',
          'website.group_website_restricted_editor', 'sales_team.group_sale_manager')]
password = secrets.token_urlsafe(32)
group_field = 'group_ids' if 'group_ids' in env['res.users']._fields else 'groups_id'
user = env['res.users'].with_context(no_reset_password=True, tracking_disable=True,
        mail_create_nosubscribe=True).create({'name': 'Torrepulia UI QA temporary',
        'login': 'ui-qa-' + secrets.token_hex(8) + '@example.invalid', 'password': password,
        group_field: [(6, 0, groups)], 'company_id': website.company_id.id,
        'company_ids': [(6, 0, [website.company_id.id])]})
view = page.view_id.copy({'key': 'torrepulia.ui.qa.' + secrets.token_hex(8), 'arch_fs': False, 'arch_updated': True})
qa_page = page.copy({'name': 'Torrepulia UI QA temporary', 'url': '/qa-torrepulia-ui-' + secrets.token_hex(8),
        'view_id': view.id, 'website_indexed': False, 'is_published': True})
auth = {'database': env.cr.dbname, 'login': user.login, 'password': password, 'user_id': user.id,
        'website_id': website.id, 'campaign_id': campaign.id, 'qa_page_id': qa_page.id,
        'qa_view_id': view.id, 'qa_url': qa_page.url, 'campaign_state': campaign.state,
        'products': [{'id': line.product_id.id, 'template_id': line.product_id.product_tmpl_id.id,
                      'name': line.product_id.name} for line in campaign.line_ids]}
path = Path('/tmp/torrepulia-ui-auth.json')
path.write_text(json.dumps(auth)); path.chmod(0o600)
env.cr.commit()
print('QA fixture prepared; credentials stored privately. Campaign state:', campaign.state,
      'product count:', len(campaign.line_ids))
