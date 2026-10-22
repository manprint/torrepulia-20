import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    out = Path('/tmp/torrepulia-wide-evidence'); out.mkdir(exist_ok=True)
    results, errors = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        page = await browser.new_page(viewport={'width':2074, 'height':1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install')
        await page.goto('http://127.0.0.1:8069/', wait_until='networkidle')
        for width in (2074, 2560, 1440, 390):
            await page.set_viewport_size({'width':width, 'height':1000})
            row = await page.locator('section.regina').evaluate('''e => {
                const rect=e.getBoundingClientRect();
                const probe=document.createElement('span');
                probe.style.cssText='position:absolute;width:var(--gutter);height:0;visibility:hidden';
                e.append(probe); const gutter=probe.getBoundingClientRect().width; probe.remove();
                return {viewport:innerWidth, x:rect.x, width:rect.width,
                    contentX:e.querySelector('.section-line').getBoundingClientRect().x,
                    gutter,
                    scrollWidth:document.documentElement.scrollWidth};
            }''')
            assert abs(row['x']) < 1 and abs(row['width']-width) < 1, row
            assert row['scrollWidth'] <= width, row
            expected = max(0,(width-1920)/2) + row['gutter']
            assert abs(row['contentX']-expected) < 1, row
            results.append(row)
            if width in (2074,390):
                await page.evaluate("window.scrollTo({top:document.querySelector('section.regina').offsetTop-100,behavior:'instant'})")
                await page.wait_for_timeout(300)
                await page.screenshot(path=str(out/f'home-{width}-fixed.png'),caret='initial')
        await page.set_viewport_size({'width':2074,'height':1000})
        await page.locator('[data-tp-request-header]:visible').first.click()
        await page.locator('dialog.tp-request-drawer').wait_for(state='visible')
        await page.keyboard.press('Escape')
        await page.locator('dialog.tp-request-drawer').wait_for(state='hidden')
        assert await page.locator('section.regina').evaluate('e=>Math.abs(e.getBoundingClientRect().x)<1')
        assert not errors, errors
        await browser.close()
    (out/'checks.json').write_text(json.dumps({'measurements':results,'drawer_close_no_offset':True,'javascript_errors':errors},indent=2))
    print('PASS edge-to-edge backgrounds and preserved content alignment at 2074, 2560, 1440 and 390px; no horizontal overflow; sidebar closure does not shift the page.')

asyncio.run(main())
