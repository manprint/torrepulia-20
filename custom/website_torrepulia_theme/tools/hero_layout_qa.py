"""Read-only regression for hero CTA/footer collisions on short viewports."""
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'qa-final'
IMAGES = Path(os.environ.get('TORREPULIA_QA_IMAGES', OUT))
IMAGES.mkdir(parents=True, exist_ok=True)
ROUND = sys.argv[1] if len(sys.argv) > 1 else 'hero-final'
report = {'round': ROUND, 'viewports': [], 'errors': []}
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(reduced_motion='reduce')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install')
    page = context.new_page()
    page.on('pageerror', lambda error: report['errors'].append(str(error)))
    page.set_viewport_size({'width': 1366, 'height': 600})
    page.goto('http://127.0.0.1:8069', wait_until='networkidle', timeout=90000)
    for width, height in [(1366, 600), (1280, 720), (1024, 600), (768, 600),
                          (1440, 1000), (390, 568), (320, 568), (740, 360)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.evaluate('window.scrollTo(0, 0)')
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(200)
        metrics = page.locator('.hero').evaluate('''hero => {
            const rect = el => el.getBoundingClientRect();
            const frame=rect(hero), copy=rect(hero.querySelector('.hero-copy'));
            const cta=rect(hero.querySelector('.hero-copy .button'));
            const footer=rect(hero.querySelector('.hero-bottom'));
            const image=rect(hero.querySelector('.hero-photo'));
            const header=rect(document.querySelector('.mc-header'));
            return {width:innerWidth,height:innerHeight,heroHeight:frame.height,
                ctaFooterGap:footer.top-cta.bottom,headerCopyGap:copy.top-header.bottom,
                footerContained:footer.bottom<=frame.bottom+1,
                heroCovered:image.top<=frame.top+1&&image.bottom>=frame.bottom-1,
                overflow:document.documentElement.scrollWidth-innerWidth,
                staticHero:getComputedStyle(hero.querySelector('.hero-photo')).animationName};
        }''')
        report['viewports'].append(metrics)
        print(json.dumps(metrics), flush=True)
        if width in [1366, 390, 1440]:
            page.locator('.hero').screenshot(path=str(IMAGES / f'{ROUND}-{width}x{height}.png'))
    browser.close()
(OUT / f'{ROUND}-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
assert not report['errors'], report['errors']
for metrics in report['viewports']:
    assert metrics['ctaFooterGap'] >= 24 and metrics['headerCopyGap'] >= 16, metrics
    assert metrics['footerContained'] and metrics['heroCovered'], metrics
    assert metrics['overflow'] <= 1 and metrics['staticHero'] == 'none', metrics
