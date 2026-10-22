"""Revert only this QA user's shared-view writes against the pre-QA backup."""
import json,os
from pathlib import Path
import psycopg2
from psycopg2.extras import Json

def run(env):
 a=json.loads(Path('/tmp/torrepulia-builder-auth.json').read_text())
 assert env.cr.dbname==a['database']=='torrepulia_cinematic_install'
 user=env['res.users'].browse(a['user_id'])
 assert user.login==a['login'] and user.login.startswith('tp-builder-qa-')
 before=psycopg2.connect(host=os.environ['HOST'],user=os.environ['USER'],password=os.environ['PASSWORD'],dbname='torrepulia_builder_before_audit')
 cur=before.cursor()
 columns=['id','arch_db','arch_fs','arch_updated','write_uid','write_date','inherit_id']
 cur.execute('SELECT '+','.join(columns)+' FROM ir_ui_view')
 baseline={r[0]:dict(zip(columns,r)) for r in cur.fetchall()}
 env.cr.execute('SELECT id,key,create_uid,write_uid FROM ir_ui_view WHERE write_uid=%s OR create_uid=%s',(user.id,user.id))
 changes=[];new=[]
 for vid,key,creator,writer in env.cr.fetchall():
  if vid==a['qa_view_id']:continue
  if vid in baseline:
   assert writer==user.id
   old=baseline[vid]
   values=[Json(old['arch_db']),old['arch_fs'],old['arch_updated'],old['write_uid'],old['write_date'],old['inherit_id'],vid,user.id]
   env.cr.execute('UPDATE ir_ui_view SET arch_db=%s,arch_fs=%s,arch_updated=%s,write_uid=%s,write_date=%s,inherit_id=%s WHERE id=%s AND write_uid=%s',values)
   changes.append({'id':vid,'key':key})
  else:
   assert creator==user.id
   new.append(vid)
 # Native copy-on-write can create website-specific variants during the test.
 views=env['ir.ui.view'].browse(new)
 assert all(v.type=='qweb' and (not v.website_id or v.website_id.id==a['website_id']) for v in views)
 views.unlink()
 cur.execute('SELECT id,name,write_uid,write_date FROM website_menu')
 menus={r[0]:r for r in cur.fetchall()}
 env.cr.execute('SELECT id FROM website_menu WHERE write_uid=%s',(user.id,))
 restored_menus=[]
 for mid, in env.cr.fetchall():
  assert mid in menus
  r=menus[mid]
  env.cr.execute('UPDATE website_menu SET name=%s,write_uid=%s,write_date=%s WHERE id=%s AND write_uid=%s',(Json(r[1]),r[2],r[3],mid,user.id))
  restored_menus.append(mid)
 env.invalidate_all()
 env.cr.commit()
 result={'restored_shared_views':changes,'deleted_qa_view_copies':new,'restored_menus':restored_menus}
 Path('/tmp/torrepulia-builder-evidence/shared-view-restoration.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
 before.close()
