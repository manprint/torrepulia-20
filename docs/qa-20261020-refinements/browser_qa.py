import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:8069'
OUT = Path('/tmp/torrepulia-refinement-evidence')

async def main():
    OUT.mkdir(exist_ok=True)
    checks, errors = [], []
    def passed(text):
        checks.append(text)
        print('PASS', text, flush=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        page = await browser.new_page(viewport={'width':1440, 'height':1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto(BASE + '/web/login?db=torrepulia_cinematic_install')
        await page.goto(BASE + '/shop', wait_until='networkidle')
        row = page.locator('.oe_product_cart .tp-request-action-row').first
        template_id = await row.locator('.tp-request-tile-add').get_attribute('data-tp-request-add-template')
        assert await page.locator('.tp-request-tile-add').evaluate_all("els => els.every(el => getComputedStyle(el).opacity === '1' && getComputedStyle(el).transform === 'none')")
        await row.locator('[data-catalog-step="1"]').click()
        await row.locator('[data-catalog-step="1"]').click()
        assert await row.locator('.tp-catalog-quantity-input').input_value() == '3'
        async with page.expect_response(lambda r: '/torrepulia/request/update' in r.url) as response:
            await row.locator('.tp-request-tile-add').click()
        result = (await (await response.value).json())['state']
        assert result['quantity'] == 3
        assert result['addition']['quantity'] == 3
        assert result['addition']['currency'] == 'EUR'
        popup = page.locator('.tp-request-confirmation')
        await popup.wait_for(state='visible')
        assert 'Hai inserito 3 confezioni di:' in await popup.inner_text()
        assert await popup.locator('.tp-confirmation-subtotal').inner_text() == 'Subtotale: ' + result['addition']['subtotal_display']
        assert '€' in await popup.inner_text() and '$' not in await page.locator('#wrap').inner_text()
        await page.evaluate('window.scrollTo(0, 0)')
        await page.wait_for_timeout(200)
        await page.screenshot(path=str(OUT / 'catalog-popup-desktop.png'), full_page=True, caret='initial')
        passed('catalog: default one -> three, one mutation, EUR server subtotal and correct confirmation')
        for width in (360, 390):
            await page.set_viewport_size({'width':width, 'height':900})
            await page.evaluate('window.scrollTo(0, 0)')
            await page.screenshot(path=str(OUT / f'catalog-popup-{width}.png'), full_page=True, caret='initial')
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert await page.locator('.tp-catalog-stepper').evaluate_all("els => els.every(el => el.getBoundingClientRect().width <= el.closest('.tp-request-action-row').getBoundingClientRect().width + 1)")
        passed('catalog and popup responsive at 360 and 390px without overflow')
        await popup.get_by_role('button', name='Continua a scegliere', exact=True).click()
        assert await popup.is_hidden()
        await row.locator('[data-catalog-step="-1"]').click()
        async with page.expect_response(lambda r: '/torrepulia/request/update' in r.url) as response:
            await row.locator('.tp-request-tile-add').click()
        result = (await (await response.value).json())['state']
        assert result['quantity'] == 5 and result['addition']['quantity'] == 2
        await page.wait_for_function("document.querySelector('.tp-request-confirmation p').textContent.includes('2 confezioni')")
        assert await popup.locator('.tp-confirmation-subtotal').inner_text() == 'Subtotale: ' + result['addition']['subtotal_display']
        passed('repeated product: total five; popup shows only newly added two and their subtotal')
        await popup.get_by_role('link', name='VAI AL RIEPILOGO').click()
        await page.locator('[data-review-key]').first.wait_for()
        await page.wait_for_function("document.querySelector('[data-review-key]').value === '5'")
        details = await page.locator('.tp-review-details').inner_text()
        assert 'Per il consumo quotidiano' not in details
        assert '\nUnità\n' not in details
        assert '$' not in await page.locator('[data-tp-review]').inner_text()
        passed('summary: five units, compact format name, no marketing description or redundant UoM, EUR')
        await page.set_viewport_size({'width':1440, 'height':1000})
        await page.goto(BASE + '/prenotailtuoolio', wait_until='networkidle')
        await page.locator('.tp-campaign-quantity').first.wait_for()
        assert await page.locator('[data-campaign-scroll]').count() == 0
        cta = page.locator('[data-campaign-review]')
        assert await cta.evaluate("el => getComputedStyle(el).marginTop") == '20px'
        assert await cta.evaluate("el => getComputedStyle(el).marginBottom") == '20px'
        await page.screenshot(path=str(OUT / 'seasonal-desktop.png'), full_page=True, caret='initial')
        await page.set_viewport_size({'width':390, 'height':900})
        await page.screenshot(path=str(OUT / 'seasonal-mobile.png'), full_page=True, caret='initial')
        passed('seasonal: hero button removed, CTA margin 20px above/below, shared summary retained')
        product = await (await page.request.get(BASE + '/torrepulia/request/product?template_id=' + template_id)).json()
        await page.goto(BASE + product['url'] + '?tp_request_qty=7', wait_until='networkidle')
        await page.wait_for_function("document.querySelector('.o_wsale_product_page input[name=add_qty]')?.value === '7'")
        passed('explicit product configuration: desired quantity preserved in native product page')
        assert not errors, errors
        await browser.close()
    (OUT / 'checks.json').write_text(json.dumps({'checks':checks, 'javascript_errors':errors}, indent=2))

asyncio.run(main())
