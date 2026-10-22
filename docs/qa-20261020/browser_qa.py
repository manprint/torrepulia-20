import asyncio
import json
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:8069'
OUT = Path('/tmp/torrepulia-ui-evidence')

async def main():
    OUT.mkdir(exist_ok=True)
    auth = json.loads(Path('/tmp/torrepulia-ui-auth.json').read_text())
    errors, checks = [], []
    def passed(check):
        checks.append(check)
        print('PASS', check, flush=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])
        ctx = await browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = await ctx.new_page()
        page.set_default_timeout(30000)
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.goto(BASE + '/web/login?db=' + auth['database'], wait_until='domcontentloaded')
        await page.goto(BASE + '/prenotailtuoolio', wait_until='networkidle')
        await page.locator('.tp-campaign-quantity').first.wait_for()
        await page.locator('[data-review-empty]').wait_for(state='visible')
        assert await page.locator('.tp-campaign-next').count() == 0
        assert await page.locator('.tp-campaign-assurances li').count() == 6
        await page.screenshot(path=str(OUT / 'seasonal-desktop-zero.png'), full_page=True, caret='initial')
        passed('seasonal: cards, six approved assurances, no obsolete section, empty shared form')
        await page.goto(BASE + '/shop', wait_until='networkidle')
        tile = page.locator('.oe_product_cart').filter(has=page.locator(
            '[data-tp-request-add-template="%s"]' % auth['products'][0]['template_id'])).first
        await tile.locator('.tp-catalog-quantity-input').fill('2')
        await tile.locator('.tp-request-tile-add').click()
        await page.locator('[data-tp-request-header-count]').filter(has_text='2').first.wait_for()
        await page.screenshot(path=str(OUT / 'catalog-desktop-quantity.png'), full_page=True, caret='initial')
        passed('catalog: quantity two added with a single click')
        await page.goto(BASE + '/prenotailtuoolio', wait_until='networkidle')
        first = page.locator('.tp-campaign-card').first
        await page.wait_for_function("document.querySelector('.tp-campaign-quantity')?.value === '2'")
        await first.locator('[data-campaign-step="1"]').click()
        await page.wait_for_function("document.querySelector('.tp-campaign-quantity')?.value === '3'")
        await page.locator('[data-review-lines] .tp-review-line').first.wait_for()
        await page.wait_for_function("document.querySelector('[data-review-key]')?.value === '3'")
        await page.locator('.tp-campaign-card').nth(1).locator('[data-campaign-step="1"]').click()
        await page.wait_for_function("document.querySelectorAll('[data-review-lines] .tp-review-line').length === 2")
        passed('catalog two -> seasonal plus -> total three; second product preserved in shared form')
        await page.screenshot(path=str(OUT / 'seasonal-desktop-multiple.png'), full_page=True, caret='initial')
        for width in (360, 390, 820):
            await page.set_viewport_size({'width': width, 'height': 900})
            await page.screenshot(path=str(OUT / f'seasonal-{width}.png'), full_page=True, caret='initial')
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'seasonal overflow {width}'
        passed('seasonal: no horizontal overflow at 360, 390 and 820px')
        await page.set_viewport_size({'width': 1440, 'height': 1000})
        await page.goto(BASE + '/la-tua-richiesta', wait_until='networkidle')
        await page.locator('[data-review-lines] .tp-review-line').nth(1).wait_for()
        await page.locator('[data-review-step="1"]').first.click()
        await page.wait_for_function("document.querySelector('[data-review-key]')?.value === '4'")
        await page.locator('[name="contact_name"]').fill('Collaudo interfaccia')
        await page.locator('[name="email"]').fill('ui-qa@example.invalid')
        await page.locator('[name="privacy_accepted"]').check()
        await page.evaluate('window.scrollTo(0, 0)')
        await page.wait_for_timeout(200)
        await page.screenshot(path=str(OUT / 'review-desktop.png'), full_page=True, caret='initial')
        for width in (360, 390, 820):
            await page.set_viewport_size({'width': width, 'height': 900})
            await page.screenshot(path=str(OUT / f'review-{width}.png'), full_page=True, caret='initial')
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'review overflow {width}'
        passed('review: compact product stepper, shared total four, 60/40 desktop and responsive form')
        # Delay navigation after a simulated server acknowledgement: no live CRM/email is generated.
        empty_flashes = []
        await page.expose_function('reportEmptyFlash', lambda: empty_flashes.append(True))
        await page.evaluate('''() => {
            new MutationObserver(() => { if (!document.querySelector('[data-review-empty]').hidden) window.reportEmptyFlash(); })
                .observe(document.querySelector('[data-tp-review]'), {attributes:true,subtree:true});
        }''')
        await page.route('**/torrepulia/request/submit', lambda route: route.fulfill(
            content_type='application/json', body=json.dumps({'ok': True, 'success_url': '/qa-confirmation-ui'})))
        async def confirmation(route):
            await asyncio.sleep(1.2)
            await route.fulfill(content_type='text/html', body='<h1>Abbiamo ricevuto la tua richiesta</h1>')
        await page.route('**/qa-confirmation-ui', confirmation)
        await page.locator('button[type="submit"]').click(no_wait_after=True)
        await page.wait_for_url('**/qa-confirmation-ui')
        assert not empty_flashes
        passed('mock acknowledgement with slow confirmation navigation: no empty-request flash; no CRM or emails created')
        await ctx.close()
        admin = await browser.new_context(viewport={'width':1440,'height':1000})
        response = await admin.request.post(BASE + '/web/session/authenticate', data=json.dumps({
            'jsonrpc':'2.0', 'method':'call', 'params':{'db':auth['database'], 'login':auth['login'], 'password':auth['password']}}),
            headers={'Content-Type':'application/json'})
        assert (await response.json()).get('result', {}).get('uid') == auth['user_id']
        builder = await admin.new_page()
        builder.on('pageerror', lambda error: errors.append(str(error)))
        await builder.goto(BASE + '/odoo/action-website.website_preview?website_id=' + str(auth['website_id']) +
            '&path=' + quote(auth['qa_url'], safe='') + '&enable_editor=1', wait_until='domcontentloaded')
        await builder.get_by_role('button', name='Save', exact=True).wait_for(timeout=90000)
        frame = None
        for _ in range(100):
            for candidate in builder.frames:
                if candidate != builder.main_frame and await candidate.locator('.tp-campaign').count():
                    frame = candidate
                    break
            if frame:
                break
            await builder.wait_for_timeout(100)
        assert frame, 'Campaign iframe unavailable'
        await frame.locator('.tp-campaign h1').click()
        await builder.get_by_role('button', name='Gestisci campagna e prodotti', exact=True).wait_for()
        assert await frame.locator('[name="contact_name"]').count() == 0
        assert await frame.locator('.tp-campaign-quantity').first.is_disabled()
        await builder.screenshot(path=str(OUT / 'builder-isolated.png'), full_page=True, caret='initial')
        passed('Builder: editable campaign, isolated disabled quantities, no personal contact form loaded')
        await frame.locator('.tp-campaign h1').evaluate("el => el.textContent = 'Titolo temporaneo di collaudo'")
        await frame.locator('.tp-campaign h1').dispatch_event('input')
        await builder.get_by_role('button', name='Save', exact=True).click()
        await builder.get_by_role('button', name='Save', exact=True).wait_for(state='hidden')
        await builder.goto(BASE + auth['qa_url'], wait_until='networkidle')
        assert await builder.locator('.tp-campaign h1').inner_text() == 'Titolo temporaneo di collaudo'
        passed('Builder: save and exit on temporary page without lifecycle exception')
        assert not errors, errors
        await browser.close()
    (OUT / 'checks.json').write_text(json.dumps({'checks':checks, 'errors':errors}, indent=2))

asyncio.run(main())
