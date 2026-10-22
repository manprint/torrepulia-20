import asyncio,json,re,secrets
from pathlib import Path
from playwright.async_api import async_playwright,expect

async def main():
 auth=json.loads(Path('/tmp/torrepulia-builder-auth.json').read_text());assert auth['database']=='torrepulia_cinematic_install'
 out=Path('/tmp/torrepulia-builder-evidence');out.mkdir(exist_ok=True)
 errors=[];console=[];steps=[]
 def passed(text):steps.append(text);print('PASS '+text,flush=True)
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  ctx=await browser.new_context(viewport={'width':1440,'height':1000})
  page=await ctx.new_page();page.set_default_timeout(30000)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('console',lambda m:console.append(m.text) if m.type=='error' else None)
  try:
   await page.goto('http://127.0.0.1:8069/web/login?db='+auth['database'],wait_until='domcontentloaded')
   await page.goto('http://127.0.0.1:8069/shop',wait_until='domcontentloaded')
   assert await page.locator('body').get_attribute('data-tp-request-mode')=='1'
   buttons=page.locator('button[data-product-template-id][data-action="add_to_cart"]')
   await buttons.first.wait_for();assert await buttons.count()>=2
   for index in range(2):
    await buttons.nth(index).click()
    confirmation=page.locator('.tp-request-confirmation')
    await confirmation.wait_for(state='visible')
    await expect(confirmation).to_contain_text('Prodotto aggiunto alla richiesta')
    await expect(page.locator('[data-tp-request-header-count]').first).to_have_text(str(index+1))
    await confirmation.get_by_role('button',name='Continua a scegliere',exact=True).click()
    assert '/shop' in page.url
   passed('anonymous catalog: two products added by actual buttons, success feedback, no forced navigation, header count 2')
   await page.locator('[data-tp-request-header]').first.click()
   quantities=page.locator('[data-review-key]')
   await expect(quantities).to_have_count(2)
   await quantities.first.fill('3');await quantities.first.press('Tab')
   await expect(page.locator('[data-tp-request-header-count]').first).to_have_text('4')
   assert await page.get_by_role('spinbutton',name=re.compile('Quantit. di ')).count()==2
   await expect(quantities.first).to_have_value('3')
   await page.wait_for_timeout(1000)
   await page.get_by_role('button',name='Invia richiesta',exact=True).click()
   assert await page.locator('input[name="contact_name"]').evaluate('(e)=>e===e.ownerDocument.activeElement')
   passed('review: quantity change updates server-driven header to 4; accessible product labels; invalid empty form focuses contact name without submission')
   for width,height in [(360,900),(390,900),(768,1024),(1440,1000)]:
    await page.set_viewport_size({'width':width,'height':height})
    await page.keyboard.press('Escape')
    await page.locator('h1').click()
    await page.evaluate('window.scrollTo(0,0)')
    await page.wait_for_timeout(250)
    dimensions=await page.evaluate('({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
    assert dimensions['scroll']<=dimensions['width']+1,(width,dimensions)
    await page.screenshot(path=str(out/('review-'+str(width)+'.png')),full_page=True)
   passed('review rendered at 360, 390, 768 and 1440 px with no horizontal document overflow')
   # Explicitly empty this test visitor selection via the real remove buttons.
   await page.set_viewport_size({'width':1440,'height':1000})
   for expected in (1,0):
    await page.locator('[data-review-remove]').first.click()
    await expect(page.locator('[data-review-key]')).to_have_count(expected)
   await expect(page.locator('[data-review-empty]')).to_be_visible()
   await expect(page.locator('[data-tp-request-header-count]').first).to_have_text('0')
   passed('real remove controls empty the selection; header returns to zero and no active contact form remains')
   assert not errors and not console,{'js':errors,'console':console}
  except Exception as exc:
   print('FAILED:',str(exc),flush=True)
   print('BODY:',(await page.locator('body').inner_text())[:3000],flush=True)
   await page.screenshot(path=str(out/'storefront-test-failure.png'),full_page=True)
   raise
  finally:
   # Clean only this independent browser session even when a UI assertion fails.
   try:
    b=await (await ctx.request.get('http://127.0.0.1:8069/torrepulia/request/current')).json()
    state=b['state']
    if state['quantity']:
     await ctx.request.post('http://127.0.0.1:8069/torrepulia/request/update',form={'csrf_token':b['csrf_token'],'payload':json.dumps({'operation':'clear','operation_id':secrets.token_hex(16),'selection_id':state['selection_id'],'revision':state['revision']})})
   except Exception:pass
   (out/'storefront-results.json').write_text(json.dumps({'steps':steps,'js':errors,'console':console},indent=2))
   print('JS:',json.dumps(errors),'CONSOLE:',json.dumps(console),flush=True)
   await browser.close()
asyncio.run(main())
