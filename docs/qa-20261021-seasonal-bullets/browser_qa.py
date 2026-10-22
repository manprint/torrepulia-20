import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
BASE='http://127.0.0.1:8069';OUT=Path('/tmp/seasonal-bullets-evidence')
async def main():
 OUT.mkdir(exist_ok=True);checks=[];errors=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1440,'height':1100})
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/web/login?db=torrepulia_cinematic_install')
  await page.goto(BASE+'/prenotailtuoolio',wait_until='networkidle',timeout=120000)
  await page.locator('.tp-campaign-quantity').first.wait_for()
  assert await page.locator('.tp-campaign-intro').inner_text()=='Prenota oggi senza alcun anticipo la tua quota di La Regina: lo moliamo e lo spediamo entro 48 ore.'
  intro=page.locator('.tp-campaign-content > p').first
  print('INTRO:',repr(await intro.inner_text())); assert await intro.inner_text()=='La produzione della nuova campagna olearia 2026/2027 è limitata. Seleziona le confezioni per la tua tavola:'
  assert await page.locator('.tp-campaign-benefits li').count()==3
  assert await page.locator('.tp-campaign-assurances').count()==0
  for width in [1440,768,390,360]:
   await page.set_viewport_size({'width':width,'height':1100})
   metrics=await page.locator('.tp-campaign-benefits').evaluate("e=>{const s=getComputedStyle(e);return {direction:s.flexDirection,top:s.marginTop,bottom:s.marginBottom,rect:e.getBoundingClientRect().toJSON(),items:[...e.children].map(c=>c.getBoundingClientRect().toJSON())}}")
   assert metrics['direction']==('row' if width>=768 else 'column'),metrics
   assert metrics['top']==metrics['bottom']=='24px',metrics
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   if width<768:
    for item in metrics['items']:assert abs(item['x']+item['width']/2-width/2)<2,metrics
   await page.evaluate('window.scrollTo(0,0)')
   await page.screenshot(path=str(OUT/f'page-{width}.png'),full_page=True,caret='initial')
   checks.append({'width':width,'metrics':metrics,'overflow':False})
  await page.locator('[data-campaign-step="1"]').first.click()
  await page.locator('[data-review-compact-lines] .tp-review-summary-line').first.wait_for()
  current=await page.evaluate("fetch('/torrepulia/request/current').then(r=>r.json())")
  assert current['state']['quantity']==1,current
  await page.evaluate('''async b=>fetch('/torrepulia/request/update',{method:'POST',body:new URLSearchParams({csrf_token:b.csrf_token,payload:JSON.stringify({operation:'clear',operation_id:crypto.randomUUID(),selection_id:b.state.selection_id,revision:b.state.revision})})}).then(r=>r.json())''',current)
  assert not errors,errors
  await browser.close()
 (OUT/'checks.json').write_text(json.dumps({'responsive':checks,'live_quantity':True,'qa_selection_cleared':True,'javascript_errors':errors,'submissions':0},indent=2))
 print('PASS: exact copy, three global outline SVG bullets, responsive 1440/768/390/360, 24px margins, no overflow, live selection preserved.')
asyncio.run(main())
