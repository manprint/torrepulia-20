import json,secrets
from pathlib import Path
assert env.cr.dbname == 'torrepulia_cinematic_install'
website=env['website'].search([('torrepulia_theme_enabled','=',True)],limit=1)
assert website
password=secrets.token_urlsafe(32)
user=env['res.users'].with_context(no_reset_password=True,tracking_disable=True,mail_create_nosubscribe=True).create({
 'name':'Stock design Builder QA temporary','login':'stock-builder-'+secrets.token_hex(8)+'@example.invalid','password':password,
 'group_ids':[(6,0,[env.ref(x).id for x in ('base.group_system','website.group_website_designer','website.group_website_restricted_editor')])],
 'company_id':website.company_id.id,'company_ids':[(6,0,[website.company_id.id])]})
source=env['website.page'].search([('website_id','=',website.id),('url','=','/')],limit=1)
assert source
view=source.view_id.copy({'key':'torrepulia.stock.builder.qa.'+secrets.token_hex(8),'arch_fs':False,'arch_updated':True})
page=source.copy({'name':'Stock design Builder QA temporary','url':'/qa-stock-builder-'+secrets.token_hex(8),
 'view_id':view.id,'website_indexed':False,'is_published':True})
auth={'database':env.cr.dbname,'login':user.login,'password':password,'user_id':user.id,'website_id':website.id,
 'qa_page_id':page.id,'qa_view_id':view.id,'qa_url':page.url}
p=Path('/tmp/stock-design-auth.json');p.write_text(json.dumps(auth));p.chmod(0o600)
env.cr.commit()
print('Temporary Builder user and isolated page prepared; credentials private.')
