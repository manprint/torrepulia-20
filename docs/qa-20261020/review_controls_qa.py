import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        page = await browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install')
        await page.goto('http://127.0.0.1:8069/prenotailtuoolio', wait_until='networkidle')
        await page.locator('.tp-campaign-quantity').first.wait_for()
        await page.locator('.tp-campaign-card [data-campaign-step="1"]').first.click()
        await page.wait_for_function("document.querySelector('[data-review-key]')?.value === '1'")
        await page.locator('[name="notes"]').fill('Bozza di collaudo, non inviare')
        await page.locator('[data-review-step="1"]').first.evaluate('el => {el.click(); el.click();}')
        await page.wait_for_function("document.querySelector('[data-review-key]')?.value === '2'")
        await page.locator('[data-review-step="1"]').first.wait_for(state='visible')
        assert await page.locator('[name="notes"]').input_value() == 'Bozza di collaudo, non inviare'
        await page.wait_for_function("document.querySelector('.tp-campaign-quantity')?.value === '2'")
        assert not errors, errors
        print('PASS final controls: in-flight repeated click blocked; authoritative quantity two on both widgets; notes retained; no JS errors.')
        await browser.close()

asyncio.run(main())
