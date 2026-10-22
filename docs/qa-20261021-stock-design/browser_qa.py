import asyncio,json
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright
BASE='http://127.0.0.1:8069'
OUT=Path('/tmp/stock-design-evidence')
async def measure(frame):
 return await frame.locator('.oe_product_cart').evaluate_all('''cards=>cards.map(e=>{
 const image=e.querySelector('.oe_product_image').getBoundingClientRect(),a=e.querySelector('.tp-request-preorder-link,.tp-request-tile-add'),m=e.querySelector('.tp-request-stock-message');
 if(!a)return null; const r=a.getBoundingClientRect(),c=e.getBoundingClientRect(),s=getComputedStyle(a);
 return {name:e.getAttribute('aria-label'),image_bottom:image.bottom,action_top:r.top,action_bottom:r.bottom,action_width:r.width,card_width:c.width,contained:r.left>=c.left-1&&r.right<=c.right+1,position:s.position,transform:s.transform,radius:s.borderRadius,font:s.fontFamily,notice:m?{border:getComputedStyle(m).borderWidth,background:getComputedStyle(m).backgroundColor}:null};}).filter(Boolean)''')
def validate(rows):
 assert rows,rows
 for row in rows:
  assert row['action_top']>=row['image_bottom'],row
  assert row['contained'] and row['transform']=='none',row
  assert abs(row['action_width']-row['card_width'])<2,row
  if row['notice']:assert row['notice']['border']=='0px',row
 assert max(r['action_bottom'] for r in rows)-min(r['action_bottom'] for r in rows)<2,rows
async def main():
 OUT.mkdir(exist_ok=True);checks=[];errors=[];rpc_errors=[];updates=[]
 auth=json.loads(Path('/tmp/stock-design-auth.json').read_text())
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  anonymous=await browser.new_context(viewport={'width':1440,'height':1000})
  page=await anonymous.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/web/login?db='+auth['database'])
  await page.goto(BASE+'/shop',wait_until='networkidle',timeout=120000)
  await page.locator('.tp-request-preorder-link').first.wait_for()
  for width in [1440,768,390,360]:
   await page.set_viewport_size({'width':width,'height':1000})
   rows=await measure(page);validate(rows)
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   checks.append({'surface':'shop','width':width,'cards':rows,'no_overflow':True})
   if width in [1440,390]:
    await page.locator('.oe_product_cart').first.scroll_into_view_if_needed()
    await page.screenshot(path=str(OUT/f'shop-{width}.png'),caret='initial')
  product_url=await page.locator('.oe_product_cart').filter(has=page.locator('.tp-request-stock-message')).first.locator('a[href^="/shop/"]').first.get_attribute('href')
  await page.goto(BASE+product_url,wait_until='networkidle')
  await page.locator('#tp_request_stock_notice').wait_for()
  assert not await page.locator('#add_to_cart_wrap').is_visible()
  assert await page.locator('#tp_request_stock_notice .tp-request-preorder-link').get_attribute('href')=='/prenotailtuoolio'
  assert await page.locator('#tp_request_stock_notice .badge').count()==0
  for width in [1440,390]:
   await page.set_viewport_size({'width':width,'height':1000})
   await page.locator('#tp_request_stock_notice').scroll_into_view_if_needed()
   await page.screenshot(path=str(OUT/f'product-{width}.png'),caret='initial')
   checks.append({'surface':'product','width':width,'shared_notice':True,'native_add_hidden':True})
  await page.goto(BASE+'/',wait_until='networkidle')
  holder=page.locator('.mc-catalog').first
  await holder.locator('.tp-request-preorder-link').first.wait_for(state='attached')
  for width in [1440,390]:
   await page.set_viewport_size({'width':width,'height':1000})
   await holder.scroll_into_view_if_needed()
   assert await holder.locator('.tp-request-stock-message:visible').count()==1
   assert await holder.locator('.tp-request-preorder-link:visible').first.get_attribute('href')=='/prenotailtuoolio'
   await holder.screenshot(path=str(OUT/f'formats-{width}.png'),caret='initial')
   checks.append({'surface':'formats','width':width,'neutral_notice':True,'preorder_link':True})
  ctx=await browser.new_context(viewport={'width':1440,'height':1000})
  response=await ctx.request.post(BASE+'/web/session/authenticate',data=json.dumps({'jsonrpc':'2.0','method':'call','params':{'db':auth['database'],'login':auth['login'],'password':auth['password']}}),headers={'Content-Type':'application/json'})
  assert (await response.json())['result']['uid']==auth['user_id']
  builder=await ctx.new_page();builder.on('pageerror',lambda e:errors.append(str(e)))
  builder.on('request',lambda r:updates.append(r.url) if '/torrepulia/request/update' in r.url else None)
  async def collect(res):
   if res.request.method=='POST' and 'json' in res.headers.get('content-type',''):
    try:
     data=await res.json()
     if data.get('error'):rpc_errors.append({'url':res.url,'message':data['error'].get('data',{}).get('message','RPC error')})
    except Exception:pass
  builder.on('response',collect)
  async def open_editor(path,selector):
   await builder.goto(BASE+'/odoo/action-website.website_preview?website_id='+str(auth['website_id'])+'&path='+quote(path,safe='')+'&enable_editor=1',wait_until='domcontentloaded',timeout=120000)
   await builder.get_by_role('button',name='Save',exact=True).wait_for(timeout=90000)
   for _ in range(200):
    for frame in builder.frames:
     if frame!=builder.main_frame and await frame.locator(selector).count():
      await frame.locator(selector).first.wait_for(state='visible');return frame
    await builder.wait_for_timeout(100)
   raise AssertionError('Builder iframe missing')
  frame=await open_editor('/shop','.tp-request-preorder-link')
  await builder.wait_for_timeout(500)
  before=await measure(frame);validate(before)
  await frame.locator('.oe_product_cart').first.hover()
  hovered=await measure(frame);validate(hovered)
  await builder.screenshot(path=str(OUT/'builder-shop.png'),caret='initial')
  checks.append({'surface':'builder_shop','before':before,'hovered':hovered,'no_overlap':True})
  await builder.get_by_role('button',name='Discard',exact=True).click()
  await builder.get_by_role('button',name='Save',exact=True).wait_for(state='hidden')
  frame=await open_editor(auth['qa_url'],'.mc-catalog .tp-request-preorder-link')
  await frame.locator('.mc-catalog').first.scroll_into_view_if_needed()
  await builder.screenshot(path=str(OUT/'builder-formats.png'),caret='initial')
  heading=frame.locator('#shop-title')
  await heading.evaluate("e=>e.textContent='Formati: verifica finale Builder'")
  await heading.dispatch_event('input')
  builder_lang=(await frame.locator('html').get_attribute('lang')).replace('-','_')
  await builder.get_by_role('button',name='Save',exact=True).click()
  await builder.get_by_role('button',name='Save',exact=True).wait_for(state='hidden',timeout=60000)
  result=await ctx.request.post(BASE+'/web/dataset/call_kw/ir.ui.view/read',data=json.dumps({'jsonrpc':'2.0','method':'call','params':{'model':'ir.ui.view','method':'read','args':[[auth['qa_view_id']],['arch_db']],'kwargs':{'context':{'lang':builder_lang}}}}),headers={'Content-Type':'application/json'})
  arch=(await result.json())['result'][0]['arch_db']
  assert 'Formati: verifica finale Builder' in arch
  assert 'tp-request-stock-message' not in arch and 'tp-request-preorder-link' not in arch
  await builder.goto(BASE+auth['qa_url'],wait_until='networkidle')
  await builder.locator('.tp-request-preorder-link').first.wait_for()
  assert await builder.locator('#shop-title').inner_text()=='Formati: verifica finale Builder'
  checks.append({'surface':'builder_formats','saved_and_reloaded':True,'runtime_content_not_saved':True})
  assert not updates,updates
  assert not errors and not rpc_errors,{'js':errors,'rpc':rpc_errors}
  await browser.close()
 (OUT/'checks.json').write_text(json.dumps({'checks':checks,'javascript_errors':errors,'rpc_errors':rpc_errors,'selection_updates_in_builder':updates},indent=2))
 print('PASS public desktop/tablet/mobile and actual Website Builder: no image overlap, stable hover, isolated save/reload, no selection mutations or JS/RPC errors.')
asyncio.run(main())
