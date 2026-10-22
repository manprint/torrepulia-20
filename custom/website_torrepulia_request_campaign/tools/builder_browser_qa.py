import asyncio,json,re
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright

async def main():
 auth=json.loads(Path('/tmp/torrepulia-builder-auth.json').read_text())
 assert auth['database']=='torrepulia_cinematic_install'
 out=Path('/tmp/torrepulia-builder-evidence');out.mkdir(exist_ok=True)
 errors=[];console=[];rpc=[];updates=[];steps=[]
 def passed(name):steps.append(name);print('PASS '+name,flush=True)
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  ctx=await browser.new_context(viewport={'width':1440,'height':1000})
  r=await ctx.request.post('http://127.0.0.1:8069/web/session/authenticate',data=json.dumps({'jsonrpc':'2.0','method':'call','params':{'db':auth['database'],'login':auth['login'],'password':auth['password']}}),headers={'Content-Type':'application/json'})
  assert (await r.json()).get('result',{}).get('uid')==auth['user_id']
  page=await ctx.new_page();page.set_default_timeout(30000)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:console.append(m.text) if m.type=='error' else None)
  page.on('request',lambda r:updates.append(r.url) if '/torrepulia/request/update' in r.url else None)
  async def response(res):
   if res.request.method=='POST' and 'json' in res.headers.get('content-type',''):
    try:
     b=await res.json()
     if b.get('error'):
      rpc.append(b['error'].get('data',{}).get('message',str(b['error'])))
      print('RPC DEBUG',res.url,b['error'].get('data',{}).get('debug'),flush=True)
    except Exception:pass
  page.on('response',response)
  async def campaign_frame():
   for _ in range(100):
    for frame in page.frames:
     if frame!=page.main_frame and await frame.locator('.tp-campaign').count():return frame
    await page.wait_for_timeout(100)
   raise AssertionError('Campaign iframe unavailable')
  async def open_editor(path):
   await page.goto('http://127.0.0.1:8069/odoo/action-website.website_preview?website_id='+str(auth['website_id'])+'&path='+quote(path,safe='')+'&enable_editor=1',wait_until='domcontentloaded',timeout=120000)
   await page.get_by_role('button',name='Save',exact=True).wait_for(timeout=90000)
   return await campaign_frame()
  try:
   frame=await open_editor('/prenotailtuoolio')
   await frame.locator('.tp-campaign h1').first.click()
   manage=page.get_by_role('button',name='Gestisci campagna e prodotti',exact=True)
   await manage.wait_for()
   async with ctx.expect_page() as popup:
    await manage.click()
   manager=await popup.value
   dialog=manager
   await dialog.locator('.o_field_widget[name="name"] input').wait_for()
   assert await dialog.locator('.o_field_widget[name="name"] input').input_value()=='Nuovo raccolto'
   await manager.screenshot(path=str(out/'campaign-original-form-fixed.png'),full_page=True,caret='initial')
   await manager.close()
   await page.get_by_role('button',name='Discard',exact=True).click()
   await page.get_by_role('button',name='Save',exact=True).wait_for(state='hidden')
   passed('actual seasonal page: Builder opens, native campaign form opens in separate tab and editor discards without lifecycle errors')
   frame=await open_editor(auth['qa_url'])
   await frame.locator('.tp-campaign-quantity').first.wait_for()
   await page.wait_for_timeout(700)
   assert await frame.locator('.tp-campaign-quantity').count()==2
   assert await frame.locator('.tp-campaign-quantity').first.is_disabled()
   print('DIRTY initial',await frame.locator('.o_dirty').count(),flush=True)
   await frame.locator('.tp-campaign h1').first.click()
   # Default screenshot caret hiding writes inline styles to every editable
   # field, polluting the Builder history and causing unrelated view saves.
   await page.screenshot(path=str(out/'builder-options-fixed.png'),full_page=True,caret='initial')
   async with ctx.expect_page() as popup:
    await page.get_by_role('button',name='Gestisci campagna e prodotti',exact=True).click()
   manager=await popup.value
   manager.on('pageerror',lambda e:errors.append(str(e)))
   manager.on('response',response)
   dialog=manager
   await dialog.locator('.o_field_widget[name="name"] input').wait_for()
   assert await dialog.locator('.o_field_widget[name="name"] input').input_value()==auth['qa_campaign_names'][0]
   print('DIRTY dialog opened',await frame.locator('.o_dirty').count(),flush=True)
   intro=dialog.locator('.o_field_widget[name="introduction"] textarea')
   await intro.click()
   await manager.keyboard.insert_text('Testo editoriale di collaudo temporaneo')
   print('DIRTY intro entered',await frame.locator('.o_dirty').count(),flush=True)
   rows=dialog.locator('.o_field_widget[name="line_ids"] .o_data_row')
   assert await rows.count()==2
   await rows.last.locator('.o_list_record_remove button').click()
   await dialog.get_by_text('Add a line',exact=True).click()
   product=dialog.locator('.o_field_widget[name="product_id"] input').last
   await product.click()
   await manager.keyboard.insert_text(auth['products'][1]['name'])
   await manager.locator('.o-autocomplete--dropdown-item').filter(has_text=auth['products'][1]['name']).first.click()
   await intro.click()
   assert await rows.count()==2
   print('DIRTY product chosen',await frame.locator('.o_dirty').count(),flush=True)
   # Native list handle, real mouse gestures.
   src=await rows.last.locator('.o_handle_cell').bounding_box();dst=await rows.first.bounding_box()
   assert src and dst
   await manager.mouse.move(src['x']+src['width']/2,src['y']+src['height']/2)
   await manager.mouse.down()
   await manager.mouse.move(src['x']+src['width']/2,dst['y']+2,steps=20)
   await manager.wait_for_timeout(300)
   await manager.mouse.up()
   await manager.screenshot(path=str(out/'campaign-products-picker-reorder.png'),full_page=True,caret='initial')
   await manager.locator('.o_form_button_save').click()
   await manager.locator('.o_form_button_save').wait_for(state='hidden')
   await manager.close()
   print('DIRTY form closed',await frame.locator('.o_dirty').count(),flush=True)
   passed('campaign form: existing product chosen from native picker and editorial text saved')
   await page.get_by_role('button',name='Aggiorna anteprima',exact=True).click()
   await page.wait_for_timeout(800)
   cards=frame.locator('[data-campaign-config]')
   configs=[json.loads(await cards.nth(i).get_attribute('data-campaign-config')) for i in range(await cards.count())]
   assert [c['product_id'] for c in configs]==[auth['products'][1]['id'],auth['products'][0]['id']],configs
   passed('native drag handle reorders products and authoritative preview follows saved order')
   print('DIRTY refreshed',await frame.locator('.o_dirty').count(),flush=True)
   # Test content editing and snippet cloning through the actual toolbar.
   await frame.locator('section.tp-campaign').first.click(position={'x':4,'y':4})
   await page.get_by_text('Style',exact=True).click()
   print('DIRTY style',await frame.locator('.o_dirty').count(),flush=True)
   await page.get_by_role('button',name='Duplicate this block',exact=True).first.click()
   await page.wait_for_timeout(800)
   assert await frame.locator('section.tp-campaign').count()==2
   print('DIRTY clone',await frame.locator('.o_dirty').count(),flush=True)
   heading=frame.locator('.tp-campaign h1').first
   await heading.dblclick()
   # Keep the iframe's native caret; focusing a non-focusable heading again
   # would reset the contenteditable selection to its ancestor.
   await page.keyboard.insert_text('Collaudo Builder Torrepulia temporaneo')
   passed('snippet duplicated through native overlay and editable heading changed')
   builder_lang=(await frame.locator('html').get_attribute('lang')).replace('-','_')
   print('SAVE DIRTY',await frame.locator('.o_dirty').evaluate_all('(els)=>els.map(e=>({id:e.id,view:e.dataset.oeId,xpath:e.dataset.oeXpath}))'),flush=True)
   await page.get_by_role('button',name='Save',exact=True).click()
   await page.get_by_role('button',name='Save',exact=True).wait_for(state='hidden',timeout=60000)
   assert not updates,updates
   passed('Builder saved and destroyed cleanly without writing visitor selection')
   result=await ctx.request.post('http://127.0.0.1:8069/web/dataset/call_kw/ir.ui.view/read',data=json.dumps({'jsonrpc':'2.0','method':'call','params':{'model':'ir.ui.view','method':'read','args':[[auth['qa_view_id']],['arch_db']],'kwargs':{'context':{'lang':builder_lang}}}}),headers={'Content-Type':'application/json'})
   arch=(await result.json())['result'][0]['arch_db']
   assert 'Collaudo Builder Torrepulia temporaneo' in arch
   assert 'data-campaign-config' not in arch and 'tp-campaign-quantity' not in arch
   assert arch.count('data-snippet="s_torrepulia_request_campaign"')==2
   passed('stored view contains duplicated configuration/editorial only, no runtime product cards or visitor/demo quantities')
   await page.goto('http://127.0.0.1:8069'+auth['qa_url'],wait_until='domcontentloaded')
   await page.get_by_role('heading',name=re.compile('Collaudo Builder Torrepulia temporaneo')).first.wait_for()
   await page.screenshot(path=str(out/'builder-saved-reloaded.png'),full_page=True,caret='initial')
   passed('saved page reloads with changed heading and duplicate snippets')
   # An additional mount/unmount after saving catches destroy() regressions.
   frame=await open_editor(auth['qa_url'])
   await page.get_by_role('button',name='Discard',exact=True).click()
   await page.get_by_role('button',name='Save',exact=True).wait_for(state='hidden')
   passed('editor reopens and exits again after save without invalidation/overlay errors')
   assert not errors and not rpc and not console,{'js':errors,'rpc':rpc,'console':console}
  except Exception as exc:
   print('FAILED:',str(exc),flush=True)
   details=page.get_by_text('See technical details',exact=False)
   if await details.count():await details.first.click()
   print('BODY:',(await page.locator('body').inner_text())[:4500],flush=True)
   await page.screenshot(path=str(out/'builder-test-failure.png'),full_page=True,caret='initial')
   raise
  finally:
   (out/'builder-results.json').write_text(json.dumps({'steps':steps,'js':errors,'rpc':rpc,'console':console,'selection_writes':updates},indent=2))
   print('JS:',json.dumps(errors),'RPC:',json.dumps(rpc),'CONSOLE:',json.dumps(console),flush=True)
   await browser.close()
asyncio.run(main())
