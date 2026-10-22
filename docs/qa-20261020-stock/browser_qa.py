import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
BASE='http://127.0.0.1:8069'
async def main():
 out=Path('/tmp/torrepulia-stock-evidence');out.mkdir(exist_ok=True)
 results=[];errors=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1440,'height':1000})
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/web/login?db=torrepulia_cinematic_install')
  product_url=None
  for width in [1440,390]:
   await page.set_viewport_size({'width':width,'height':1000})
   await page.goto(BASE+'/shop',wait_until='networkidle',timeout=120000)
   card=page.locator('.oe_product_cart').filter(has=page.locator('.tp-request-stock-message')).first
   message=card.locator('.tp-request-stock-message')
   await message.wait_for(state='visible')
   assert await card.locator('[data-tp-request-add-template]').count()==0
   assert await card.locator('.tp-catalog-quantity').count()==0
   link=message.locator('a[href="/prenotailtuoolio"]')
   assert await link.is_visible()
   assert await link.evaluate('e=>getComputedStyle(e).opacity')=='1'
   alert_style=await message.evaluate('''e=>{const r=e.getBoundingClientRect();const b=e.querySelector('a').getBoundingClientRect();return {background:getComputedStyle(e).backgroundColor,classes:e.className,button_contained:b.left>=r.left && b.right<=r.right}}''')
   assert 'text-bg-danger' in alert_style['classes'],alert_style
   assert alert_style['background'] not in ['rgba(0, 0, 0, 0)','rgb(255, 255, 255)'],alert_style
   assert alert_style['button_contained'],alert_style
   assert await page.locator('[data-tp-request-add-template]:visible').count()>=1
   product_url=await card.locator('a[href^="/shop/"]').first.get_attribute('href')
   await message.scroll_into_view_if_needed()
   await page.screenshot(path=str(out/f'shop-{width}.png'),caret='initial')
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   results.append({'surface':'shop','width':width,'exhausted_add_hidden':True,'configured_message_and_link_visible':True,'available_product_add_visible':True,'no_overflow':True,'alert_style':alert_style})
   await page.goto(BASE+product_url,wait_until='networkidle')
   await page.wait_for_timeout(500)
   assert not await page.locator('#add_to_cart_wrap').is_visible()
   assert await page.locator('.availability_messages').get_by_text('Temporaneamente esaurito!',exact=False).is_visible()
   await page.locator('.availability_messages').scroll_into_view_if_needed()
   await page.screenshot(path=str(out/f'product-{width}.png'),caret='initial')
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   results.append({'surface':'product','width':width,'native_exhausted_add_hidden':True,'message_visible':True,'no_overflow':True})
   await page.goto(BASE+'/',wait_until='networkidle')
   holder=page.locator('.mc-catalog').first
   await holder.locator('.format-summary').first.wait_for(state='attached')
   summary=holder.locator('.format-summary').filter(has=page.locator('.tp-request-stock-message')).first
   identity=await summary.get_attribute('data-summary')
   await holder.locator('[data-product="'+identity+'"]').click()
   assert await summary.locator('.tp-request-stock-message').is_visible()
   assert await summary.locator('[data-tp-request-add-template]').count()==0
   await summary.scroll_into_view_if_needed()
   await page.screenshot(path=str(out/f'formats-{width}.png'),caret='initial')
   results.append({'surface':'choose_formats','width':width,'exhausted_add_hidden':True,'message_visible':True})
  for width in [360,768]:
   await page.set_viewport_size({'width':width,'height':1000})
   await page.goto(BASE+'/shop',wait_until='networkidle')
   message=page.locator('.tp-request-stock-message').first
   contained=await message.evaluate('''e=>{const r=e.getBoundingClientRect();const b=e.querySelector('a').getBoundingClientRect();return b.left>=r.left && b.right<=r.right}''')
   assert contained
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   results.append({'surface':'shop','width':width,'button_contained':contained,'no_overflow':True})
  await page.goto(BASE+'/',wait_until='networkidle')
  summary=page.locator('.mc-catalog .format-summary').filter(has=page.locator('.tp-request-stock-message')).first
  identity=await summary.get_attribute('data-summary')
  await page.locator('.mc-catalog [data-product="'+identity+'"]').click()
  # Follow the configured invitation into the separate seasonal preorder flow.
  await summary.locator('.tp-request-stock-message a[href="/prenotailtuoolio"]').click()
  await page.wait_for_url('**/prenotailtuoolio')
  await page.locator('.tp-campaign-quantity').first.wait_for()
  await page.wait_for_load_state('networkidle')
  await page.locator('[data-campaign-step="1"]').first.click()
  await page.wait_for_function("document.querySelector('.tp-campaign-quantity')?.value==='1'")
  await page.wait_for_timeout(250)
  state=await page.evaluate("fetch('/torrepulia/request/current',{cache:'no-store'}).then(r=>r.json())")
  assert state['state']['quantity']==1,state
  results.append({'surface':'seasonal_campaign','preorder_exhausted_product_allowed':True,'quantity':1})
  await page.set_viewport_size({'width':390,'height':1000})
  await page.screenshot(path=str(out/'campaign-390.png'),full_page=True,caret='initial')
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.evaluate('window.scrollTo(0,0)')
  await page.screenshot(path=str(out/'campaign-1440.png'),full_page=True,caret='initial')
  # Clean only this QA browser's private draft; no final submission or mail.
  result=await page.evaluate('''async b=>{let s=b.state;return fetch('/torrepulia/request/update',{method:'POST',body:new URLSearchParams({csrf_token:b.csrf_token,payload:JSON.stringify({operation:'clear',operation_id:crypto.randomUUID(),selection_id:s.selection_id,revision:s.revision})})}).then(r=>r.json())}''',state)
  assert result['state']['quantity']==0
  assert not errors,errors
  await browser.close()
 (out/'checks.json').write_text(json.dumps({'checks':results,'javascript_errors':errors,'qa_selection_cleared':True},indent=2))
 print('PASS desktop/mobile: shop, detail, formats and campaign; configured message/link; native stock hiding; seasonal preorder accepted; no JavaScript errors.')
asyncio.run(main())
