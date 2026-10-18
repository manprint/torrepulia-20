"""Public, read-only responsive/keyboard checks against the local development site."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    output = Path(os.environ.get('TORREPULIA_QA_IMAGES', Path.home() / 'torrepulia-navigation-qa'))
    output.mkdir(parents=True, exist_ok=True)
    report = {'cases': [], 'errors': [], 'failures': []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(reduced_motion='reduce')
        context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install', timeout=120000)
        page = context.new_page()
        page.on('pageerror', lambda error: report['errors'].append(error.stack))
        page.goto('http://127.0.0.1:8069/shop', wait_until='domcontentloaded', timeout=120000)
        product = page.locator('.oe_product_cart a[href*="/shop/"]').first.get_attribute('href')
        assert product, 'No native product link available for product regression'
        routes = ['/', '/aboutus', '/l-olio', '/contactus', '/shop', product, '/shop/cart']
        for width in [360, 390, 768, 1440]:
            page.set_viewport_size({'width': width, 'height': 900})
            for index, route in enumerate(routes):
                response = page.goto('http://127.0.0.1:8069' + route, wait_until='domcontentloaded', timeout=120000)
                page.evaluate('document.fonts.ready')
                page.wait_for_timeout(800)
                result = page.evaluate('''() => ({
                    overflow: document.documentElement.scrollWidth - innerWidth,
                    desktop: [...document.querySelectorAll('.desktop-nav .mc-menu-items a')].map(a=>[a.textContent.trim(),a.getAttribute('href')]),
                    mobile: [...document.querySelectorAll('#mc-mobile-menu .mc-menu-items a')].map(a=>[a.textContent.trim(),a.getAttribute('href')]),
                    placeholders: document.querySelectorAll('.mc-chrome a[href="#"], #mc-footer a[href="#"]').length,
                    cartVisible: !!document.querySelector('.mc-chrome a[href="/shop/cart"]')?.getBoundingClientRect().width,
                    footerGroups: document.querySelectorAll('.mc-footer-groups nav').length,
                })''')
                result.update(width=width, route=route, status=response.status)
                report['cases'].append(result)
                if response.status != 200 or result['overflow'] > 1 or result['desktop'] != result['mobile'] or result['placeholders'] or not result['cartVisible'] or result['footerGroups'] != 4:
                    report['failures'].append(result)
                if route == '/':
                    page.screenshot(path=str(output / f'after-{width}.png'), full_page=True)
                    if width < 1101:
                        toggle = page.locator('.menu-toggle')
                        toggle.focus()
                        page.keyboard.press('Enter')
                        page.wait_for_function("document.querySelector('#mc-mobile-menu').classList.contains('show')")
                        page.wait_for_timeout(300)
                        assert page.evaluate("!!document.activeElement.closest('#mc-mobile-menu')"), 'Opening focus'
                        assert toggle.get_attribute('aria-expanded') == 'true'
                        page.screenshot(path=str(output / f'menu-{width}.png'))
                        page.keyboard.press('Escape')
                        page.wait_for_timeout(300)
                        assert toggle.evaluate('el=>el===document.activeElement'), 'Escape return focus'
                        assert toggle.get_attribute('aria-expanded') == 'false'
                print(width, route, response.status, result['overflow'], flush=True)
        browser.close()
    (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    assert not report['errors'] and not report['failures'], report
    print('Responsive navigation checks passed:', output)


if __name__ == '__main__':
    main()
