import asyncio,json
from pathlib import Path
from urllib.parse import parse_qs
from playwright.async_api import async_playwright
BASE='http://127.0.0.1:8069';OUT=Path('/tmp/seasonal-summary-evidence')
async def main():
 OUT.mkdir(exist_ok=True);checks=[];errors=[];submissions=[];navigations=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1440,'height':1100})
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/web/login?db=torrepulia_cinematic_install')
  await page.goto(BASE+'/prenotailtuoolio',wait_until='networkidle',timeout=120000)
  await page.locator('.tp-campaign-quantity').first.wait_for()
  assert await page.locator('[data-tp-review-form]').count()==1
  assert await page.locator('[data-review-lines]').count()==0
  assert await page.locator('[data-campaign-review]').count()==0
  assert await page.locator('[data-review-empty]').is_visible()
  await page.screenshot(path=str(OUT/'empty-1440.png'),full_page=True,caret='initial')
  checks.append({'case':'empty','form_count':1,'left_product_list_absent':True,'intermediate_button_absent':True})
  page.on('framenavigated',lambda f:navigations.append(f.url) if f==page.main_frame else None)
  controls=page.locator('[data-campaign-config]')
  first=controls.nth(0);second=controls.nth(1)
  await first.locator('[data-campaign-step="1"]').click()
  await page.locator('[data-tp-review-form]').wait_for(state='visible')
  await page.locator('[data-review-compact-lines] .tp-review-summary-line').first.wait_for()
  await page.evaluate('window.scrollTo(0,0)')
  await page.screenshot(path=str(OUT/'one-product-1440.png'),full_page=True,caret='initial')
  for name,value in {'contact_name':'QA riepilogo','email':'seasonal-ui@example.invalid','phone':'+1 202-555-0123','delivery_area':'Torremaggiore (FG)','notes':'Dati temporanei: nessun invio reale'}.items():
   await page.locator('[data-tp-review-form] [name="'+name+'"]').fill(value)
  await first.locator('[data-campaign-step="1"]').click()
  await page.wait_for_function("document.querySelector('.tp-campaign-quantity')?.value==='2'")
  await second.locator('[data-campaign-step="1"]').click()
  await page.wait_for_function("document.querySelectorAll('[data-review-compact-lines] .tp-review-summary-line').length===2")
  await page.wait_for_timeout(150)
  preview=await page.evaluate("fetch('/torrepulia/request/preview',{cache:'no-store'}).then(r=>r.json())")
  state=preview['state'];assert state['quantity']==3,state
  rows=page.locator('[data-review-compact-lines] .tp-review-summary-line')
  for i,line in enumerate(state['lines']):
   text=await rows.nth(i).inner_text()
   assert line['name'] in text and str(int(line['quantity'])) in text,text
   if line.get('subtotal_display'):assert line['subtotal_display'] in text,text
  assert await page.locator('[name="contact_name"]').input_value()=='QA riepilogo'
  assert not navigations,navigations
  assert await page.locator('.tp-review-contact img,.tp-review-contact [data-review-key],.tp-review-contact [data-review-remove]').count()==0
  assert await page.locator('[data-review-compact-lines] img,[data-review-compact-lines] input,[data-review-compact-lines] button').count()==0
  for name in ['phone','delivery_area']:
   assert await page.locator('[name="'+name+'"]').get_attribute('required') is not None
  for width in [1440,768,390,360]:
   await page.set_viewport_size({'width':width,'height':1100})
   layout=await page.locator('[data-tp-review-form]').evaluate('''e=>{const a=e.querySelector('.tp-review-contact').getBoundingClientRect(),b=e.querySelector('.tp-review-order-summary').getBoundingClientRect();return {left:a.toJSON(),right:b.toJSON(),ratio:a.width/(a.width+b.width)}}''')
   if width>=768:assert abs(layout['ratio']-.6)<.01,layout
   else:assert layout['right']['top']>=layout['left']['bottom'],layout
   assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   checks.append({'case':'responsive','width':width,'layout':layout,'no_overflow':True})
   if width in [1440,390]:
    await page.locator('[data-tp-review-form]').screenshot(path=str(OUT/f'form-{width}.png'),caret='initial')
    await page.evaluate('window.scrollTo(0,0)')
    await page.screenshot(path=str(OUT/f'page-{width}.png'),full_page=True,caret='initial')
  checks.append({'case':'synchronization','quantity':state['quantity'],'rows':len(state['lines']),'page_reload':False,'contact_preserved':True})
  await page.set_viewport_size({'width':1440,'height':1100})
  await page.locator('[name="phone"]').fill('')
  await page.locator('button[type="submit"]').click()
  assert await page.locator('[name="phone"]').evaluate('e=>e===document.activeElement')
  await page.locator('[name="phone"]').fill('+1 202-555-0123')
  await page.locator('[name="privacy_accepted"]').check()
  async def intercept(route):
   values=parse_qs(route.request.post_data)
   submissions.append(json.loads(values['payload'][0]))
   await route.fulfill(status=422,content_type='application/json',body=json.dumps({'ok':False,'code':'invalid','message':'Errore simulato di collaudo: nessun invio reale.','fields':['email']}))
  await page.route('**/torrepulia/campaign/submit',intercept)
  await page.locator('button[type="submit"]').click()
  await page.locator('[data-review-error]').wait_for(state='visible')
  assert len(submissions)==1,submissions
  assert submissions[0]['delivery_area']=='Torremaggiore (FG)'
  assert await page.locator('[name="email"]').evaluate('e=>e===document.activeElement')
  assert await rows.count()==2
  checks.append({'case':'validation_and_error','phone_required_focus':True,'email_error_focus':True,'selection_and_contact_retained':True,'submission_intercepted':True})
  bootstrap=await page.evaluate("fetch('/torrepulia/request/current').then(r=>r.json())")
  result=await page.evaluate('''async b=>fetch('/torrepulia/request/update',{method:'POST',body:new URLSearchParams({csrf_token:b.csrf_token,payload:JSON.stringify({operation:'clear',operation_id:crypto.randomUUID(),selection_id:b.state.selection_id,revision:b.state.revision})})}).then(r=>r.json())''',bootstrap)
  assert result['state']['quantity']==0
  assert not errors,errors
  await browser.close()
 (OUT/'checks.json').write_text(json.dumps({'checks':checks,'javascript_errors':errors,'real_submissions':0,'qa_selection_cleared':True},indent=2))
 print('PASS: single integrated form, no left cart/intermediate CTA, live quantities/prices, 60/40 desktop and mobile stack, required-field focus and intercepted-error preservation.')
asyncio.run(main())
