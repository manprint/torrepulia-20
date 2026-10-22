"""Audit live data and remove only fixtures explicitly recorded by this QA run."""
import hashlib,json,runpy,secrets,os
from pathlib import Path
import psycopg2

def run(env):
 path=Path('/tmp/torrepulia-builder-auth.json')
 a=json.loads(path.read_text())
 assert env.cr.dbname==a['database']=='torrepulia_cinematic_install'
 snapshot=runpy.run_path('/mnt/torrepulia/custom/website_torrepulia_request_campaign/tools/migration_qa.py')['snapshot']
 assert snapshot(env.cr)==a['business_before'], 'Business data changed; investigate before cleanup'
 page=env['website.page'].search([('website_id','=',a['website_id']),('url','=','/prenotailtuoolio')],limit=1)
 hashes={lang:hashlib.sha256(arch.encode()).hexdigest() for lang,arch in page.view_id._fields['arch_db']._get_stored_translations(page.view_id).items()}
 assert hashes==a['original_arch_hashes'], 'Original editorial page changed'
 site=env['website'].browse(a['website_id'])
 settings={'mode':site.torrepulia_commercial_mode,'show_prices':site.torrepulia_request_show_prices,'campaign_id':site.torrepulia_campaign_id.id,'team_id':site.torrepulia_request_team_id.id}
 assert settings==a['original_settings'], 'Original website settings changed'
 before=psycopg2.connect(host=os.environ['HOST'],user=os.environ['USER'],password=os.environ['PASSWORD'],dbname='torrepulia_builder_before_audit')
 cur=before.cursor()
 cur.execute("SELECT id,arch_db,arch_fs FROM ir_ui_view WHERE key LIKE 'website_torrepulia_theme.%'")
 theme={r[0]:r[1:] for r in cur.fetchall()}
 env.cr.execute('SELECT id,arch_db,arch_fs FROM ir_ui_view WHERE id IN %s',(tuple(theme),))
 assert {r[0]:r[1:] for r in env.cr.fetchall()}==theme, 'Shared theme differs from backup'
 cur.execute('SELECT id,name,manual_url,new_window,parent_id,sequence FROM website_menu')
 menus={r[0]:r[1:] for r in cur.fetchall()}
 env.cr.execute('SELECT id,name,manual_url,new_window,parent_id,sequence FROM website_menu WHERE id IN %s',(tuple(menus),))
 assert {r[0]:r[1:] for r in env.cr.fetchall()}==menus, 'Historical menus differ from backup'
 before.close()
 qa=env['website.page'].browse(a['qa_page_id'])
 assert not qa.is_published and qa.url==a['qa_url'] and qa.url.startswith('/_torrepulia-builder-qa-')
 view=qa.view_id
 assert view.id==a['qa_view_id'] and view.key.startswith('torrepulia.builder.qa.')
 qa.unlink()
 if view.exists():view.unlink()
 camps=env['torrepulia.request.campaign'].browse(a['qa_campaign_ids'])
 assert set(camps.mapped('name'))==set(a['qa_campaign_names'])
 assert all(c.name.startswith('QA Builder ') and c.website_id==site for c in camps)
 camps.unlink()
 user=env['res.users'].browse(a['user_id'])
 assert user.login==a['login'] and user.login.startswith('tp-builder-qa-') and user.login.endswith('@example.invalid')
 drafts=env['torrepulia.request'].search([('partner_id','=',user.partner_id.id),('state','=','draft')])
 drafts.unlink()
 user.write({'active':False,'password':secrets.token_urlsafe(48)})
 modules=env['ir.module.module'].search([('name','in',['website_torrepulia_request','website_torrepulia_request_theme','website_torrepulia_request_campaign'])])
 result={'database':env.cr.dbname,'business_fingerprints_unchanged':True,'original_page_all_translations_unchanged':True,'shared_theme_and_historical_menus_match_backup':True,'website_settings_unchanged':True,'qa_page_and_campaigns_deleted':True,'qa_user_deactivated_password_rotated':True,'modules':[{ 'name':m.name,'state':m.state,'version':m.installed_version} for m in modules], 'original_campaign':{'name':site.torrepulia_campaign_id.name,'state':site.torrepulia_campaign_id.state,'products':len(site.torrepulia_campaign_id.line_ids)}}
 env.cr.commit()
 Path('/tmp/torrepulia-builder-evidence/final-audit.json').write_text(json.dumps(result,indent=2))
 path.unlink()
 print(json.dumps(result,indent=2))
