"""Reset only unpublished QA fixtures, from an authenticated Odoo shell."""
import json
from pathlib import Path
from lxml import etree
from odoo import fields
from odoo.tools.translate import StoredTranslations

def run(env):
 assert env.cr.dbname=='torrepulia_cinematic_install'
 a=json.loads(Path('/tmp/torrepulia-builder-auth.json').read_text())
 page=env['website.page'].browse(a['qa_page_id'])
 assert not page.is_published and page.url.startswith('/_torrepulia-builder-qa-')
 camps=env['torrepulia.request.campaign'].browse(a['qa_campaign_ids'])
 assert all(c.name.startswith('QA Builder ') for c in camps)
 for c in camps:
  c.write({'introduction':False,'line_ids':[fields.Command.clear(),*[fields.Command.create({'product_id':p['id'],'sequence':i*10}) for i,p in enumerate(a['products'])]]})
 original=env['website.page'].search([('website_id','=',a['website_id']),('url','=','/prenotailtuoolio')],limit=1)
 changed={}
 for lang,arch in original.view_id._fields['arch_db']._get_stored_translations(original.view_id).items():
  root=etree.fromstring(arch.encode())
  if root.get('t-name'):root.set('t-name',page.view_id.key)
  for section in root.xpath('.//*[@data-snippet="s_torrepulia_request_campaign"]'):
   section.set('data-campaign',json.dumps({'id':camps[0].id,'name':camps[0].name,'display_name':camps[0].name}))
  changed[lang]=etree.tostring(root,encoding='unicode')
 page.view_id.write({'arch_db':StoredTranslations(changed),'arch_fs':False})
 env.cr.commit()
 print('PASS isolated QA fixture reset')
