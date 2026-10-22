import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
BASE='http://127.0.0.1:8069'
async def main():
 out=Path('/tmp/torrepulia-product-evidence');out.mkdir(exist_ok=True)
 checks=[];errors=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1440,'height':1000})
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/web/login?db=torrepulia_cinematic_install')
  for width in [1440,390]:
   await page.set_viewport_size({'width':width,'height':1000})
   await page.goto(BASE+'/shop',wait_until='networkidle',timeout=120000)
   await page.locator('.tp-catalog-stepper').first.wait_for()
   metrics=await page.locator('.oe_product_cart').evaluate_all('''els=>els.map(e=>{
    const q=e.querySelector('.tp-catalog-quantity'),a=e.querySelector('.tp-request-tile-add'),m=e.querySelector('.tp-request-stock-message');
    return {title:e.getAttribute('aria-label'), gap:q&&a?a.getBoundingClientRect().top-q.getBoundingClientRect().bottom:null,
      left:(m||a)?.getBoundingClientRect().left,card_left:e.getBoundingClientRect().left,right:(m||a)?.getBoundingClientRect().right,card_right:e.getBoundingClientRect().right,bottom:(m||a)?.getBoundingClientRect().bottom,alert:m?{width:m.getBoundingClientRect().width,parent:m.parentElement.getBoundingClientRect().width,radius:getComputedStyle(m).borderRadius}:null};})''')
   for row in metrics:
    if row['gap'] is not None: assert row['gap']>=12,row
    assert abs(row['left']-row['card_left'])<1,row
    assert row['right']<=row['card_right']+1,row
   bottoms=[row['bottom'] for row in metrics if row['bottom']]
   assert max(bottoms)-min(bottoms)<2,metrics
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   card=page.locator('.oe_product_cart').filter(has=page.locator('.tp-request-stock-message')).first
   await card.locator('.tp-request-stock-message').scroll_into_view_if_needed()
   await page.screenshot(path=str(out/f'shop-{width}.png'),caret='initial')
   checks.append({'surface':'shop','width':width,'cards':metrics,'aligned_bottom':True,'no_overflow':True})
   detail_url=await card.locator('a[href^="/shop/"]').first.get_attribute('href')
   await page.goto(BASE+detail_url,wait_until='networkidle')
   formats=page.locator('.mc-product-formats');await formats.locator('.format-option').first.wait_for()
   current=await formats.get_attribute('data-current-product')
   assert await formats.locator('[data-product="'+current+'"]').count()==0
   native_radius=await page.locator('.availability_messages .badge').first.evaluate('e=>getComputedStyle(e).borderRadius')
   assert next(row['alert']['radius'] for row in metrics if row['alert'])==native_radius
   await formats.scroll_into_view_if_needed()
   await page.screenshot(path=str(out/f'product-{width}.png'),caret='initial')
   checks.append({'surface':'product','width':width,'current_excluded':True,'native_radius':native_radius,'title':await page.locator('#product_details h1').inner_text()})
   await page.goto(BASE+'/',wait_until='networkidle')
   holder=page.locator('.mc-catalog').first
   await holder.locator('.format-summary').first.wait_for(state='attached')
   assert await holder.locator('.mc-format-ribbon').count()>0
   assert await holder.locator('.o_ribbons').count()>0
   tabs=holder.locator('[data-product]')
   measures=[]
   for i in range(await tabs.count()):
    tab=tabs.nth(i);await tab.click()
    identity=await tab.get_attribute('data-product')
    panel=holder.locator('[data-summary="'+identity+'"]')
    measure=await panel.evaluate('''e=>{const r=e.querySelector('.tp-request-action-row').getBoundingClientRect(),l=e.querySelector('.tp-format-details-link').getBoundingClientRect(),q=e.querySelector('.tp-catalog-quantity'),a=e.querySelector('.tp-request-tile-add'),m=e.querySelector('.tp-request-stock-message');return {details_gap:l.top-r.bottom,quantity_gap:q&&a?a.getBoundingClientRect().top-q.getBoundingClientRect().bottom:null,alert:m?{width:m.getBoundingClientRect().width,parent:m.parentElement.getBoundingClientRect().width,radius:getComputedStyle(m).borderRadius}:null}}''')
    assert measure['details_gap']>=12,measure
    if measure['quantity_gap'] is not None:assert measure['quantity_gap']>=12,measure
    measures.append(measure)
   await holder.scroll_into_view_if_needed()
   await page.screenshot(path=str(out/f'formats-{width}.png'),caret='initial')
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   checks.append({'surface':'choose_formats','width':width,'ribbons_visible':True,'panels':measures,'no_overflow':True})
  assert not errors,errors
  await browser.close()
 (out/'checks.json').write_text(json.dumps({'checks':checks,'javascript_errors':errors},indent=2))
 print('PASS desktop/mobile spacing, bottom alignment, compact native-rounded alerts, ribbons, current-format exclusion; no JS errors.')
asyncio.run(main())
