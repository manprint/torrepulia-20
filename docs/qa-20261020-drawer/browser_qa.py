import asyncio
import json
from pathlib import Path
from urllib.parse import parse_qs
from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:8069'
OUT = Path('/tmp/torrepulia-drawer-evidence')

async def main():
    OUT.mkdir(exist_ok=True)
    checks, errors = [], []
    def passed(text):
        checks.append(text); print('PASS', text, flush=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        ctx = await browser.new_context(viewport={'width':1440, 'height':1000})
        page = await ctx.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto(BASE + '/web/login?db=torrepulia_cinematic_install')
        await page.goto(BASE + '/shop', wait_until='networkidle')
        header = page.locator('[data-tp-request-header]:visible').first
        url = page.url
        await header.click()
        drawer = page.locator('dialog.tp-request-drawer')
        await drawer.wait_for(state='visible')
        await drawer.get_by_text('La tua richiesta è ancora vuota', exact=True).wait_for()
        assert page.url == url
        await page.keyboard.press('Escape')
        await drawer.wait_for(state='hidden')
        assert await header.evaluate('el => document.activeElement === el')
        passed('header opens empty sidebar without navigation; Escape closes and restores focus')
        rows = page.locator('.oe_product_cart .tp-request-action-row')
        for index, quantity in ((0, 2), (1, 1)):
            await rows.nth(index).locator('.tp-catalog-quantity-input').fill(str(quantity))
            await rows.nth(index).locator('.tp-request-tile-add').click()
            await page.locator('.tp-request-confirmation').wait_for(state='visible')
            await page.get_by_role('button', name='Continua a scegliere', exact=True).click()
        await header.click()
        await drawer.locator('.tp-drawer-line').nth(1).wait_for()
        assert 'Quantità: 2' in await drawer.inner_text()
        assert 'Quantità: 1' in await drawer.inner_text()
        assert '€' in await drawer.inner_text()
        assert page.url == url
        await page.evaluate('window.scrollTo(0, 0)')
        await page.screenshot(path=str(OUT / 'drawer-desktop.png'), full_page=False, caret='initial')
        for _ in range(6):
            await page.keyboard.press('Tab')
            assert await drawer.evaluate('el => el.contains(document.activeElement)')
        passed('sidebar contains both selected products, authoritative quantities and EUR totals; keyboard focus stays inside')
        await page.set_viewport_size({'width':390, 'height':844})
        await page.screenshot(path=str(OUT / 'drawer-mobile.png'), full_page=False, caret='initial')
        assert await drawer.evaluate('el => el.getBoundingClientRect().width <= innerWidth')
        assert await drawer.locator('.tp-drawer-footer').is_visible()
        await drawer.get_by_role('link', name='VAI AL RIEPILOGO', exact=True).click()
        await page.wait_for_url('**/la-tua-richiesta')
        await page.locator('[data-review-lines] .tp-review-line').nth(1).wait_for()
        area = page.locator('[name="delivery_area"]')
        assert await area.get_attribute('required') is None
        assert await page.locator('.tp-review-field-help').evaluate('el => getComputedStyle(el).fontSize') == '11px'
        await area.fill('71017 Torremaggiore')
        await page.locator('[name="contact_name"]').fill('Collaudo sidebar')
        await page.locator('[name="email"]').fill('drawer-qa@example.invalid')
        await page.locator('[name="notes"]').fill('Recapiti da conservare in caso di errore')
        await page.locator('[name="privacy_accepted"]').check()
        await page.evaluate('window.scrollTo(0, 0)')
        await page.screenshot(path=str(OUT / 'contact-mobile.png'), full_page=True, caret='initial')
        await page.set_viewport_size({'width':1440, 'height':1000})
        await page.screenshot(path=str(OUT / 'contact-desktop.png'), full_page=True, caret='initial')
        captured = []
        async def submit(route):
            payload = json.loads(parse_qs(route.request.post_data)['payload'][0])
            captured.append(payload)
            await route.fulfill(status=422, content_type='application/json', body=json.dumps({
                'ok':False, 'message':'Errore simulato: dati conservati.', 'fields':[]}))
        await page.route('**/torrepulia/request/submit', submit)
        await page.locator('button[type="submit"]').click()
        await page.locator('[data-review-error]').wait_for(state='visible')
        assert captured[0]['delivery_area'] == '71017 Torremaggiore'
        assert await area.input_value() == '71017 Torremaggiore'
        assert await page.locator('[name="notes"]').input_value() == captured[0]['notes']
        passed('optional area field, 11px help, AJAX payload and preservation after simulated submission failure')
        other = await browser.new_page()
        await other.goto(BASE + '/web/login?db=torrepulia_cinematic_install')
        await other.goto(BASE + '/shop', wait_until='networkidle')
        await other.locator('[data-tp-request-header]:visible').first.click()
        await other.locator('dialog').get_by_text('La tua richiesta è ancora vuota', exact=True).wait_for()
        passed('a different anonymous browser context cannot see the selected products')
        await page.goto(BASE + '/prenotailtuoolio', wait_until='networkidle')
        await page.locator('[name="delivery_area"]').wait_for()
        passed('same optional field is present in the seasonal shared form')
        assert not errors, errors
        await browser.close()
    (OUT / 'checks.json').write_text(json.dumps({'checks':checks, 'javascript_errors':errors}, indent=2))

asyncio.run(main())
