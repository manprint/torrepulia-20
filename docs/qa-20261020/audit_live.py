assert env.cr.dbname == 'torrepulia_cinematic_install'
menu = env.ref('website_torrepulia_request_campaign.menu_campaigns')
assert menu.parent_id == env.ref('website.menu_site')
print('PASS menu: Website > Site > Campagne olio nuovo')
for name in ('website_torrepulia_request', 'website_torrepulia_request_campaign', 'website_torrepulia_request_theme'):
    module = env['ir.module.module'].search([('name', '=', name)])
    assert module.state == 'installed'
    print('PASS installed:', name, module.latest_version)
for view_type in ('form', 'list'):
    result = env['torrepulia.request.campaign'].get_view(view_type=view_type)
    assert result.get('arch')
print('PASS native campaign get_view(form/list) with XML development mode')
page = env['website.page'].search([('url', '=', '/prenotailtuoolio'), ('website_id.torrepulia_theme_enabled', '=', True)])
assert len(page) == 1
for arch in page.view_id._fields['arch_db']._get_stored_translations(page.view_id).values():
    assert 'data-review-lazy' in arch
    assert 'tp-campaign-next' not in arch
    assert 'data-editorial-layout="2"' in arch
print('PASS scoped seasonal migration in all stored translations')
env.cr.rollback()
