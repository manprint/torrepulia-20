"""Check the About Us opening, editorial grid, copy and native image markup."""
import json
import os
import sys
from pathlib import Path
from lxml import etree
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'qa-about'
OUT.mkdir(exist_ok=True)
IMAGES = Path(os.environ.get('TORREPULIA_QA_IMAGES', OUT))
IMAGES.mkdir(parents=True, exist_ok=True)
source = etree.parse(str(ROOT / 'views/snippets/s_phase_two.xml'))
expected = [' '.join(''.join(node.itertext()).split()) for node in source.xpath(
    '//template[@id="s_torrepulia_story_chapters"]//article/p[not(@class)]')]
MOTION_ONLY = '--motion-only' in sys.argv
report = json.loads((OUT / 'results.json').read_text(encoding='utf-8')) if MOTION_ONLY else {'viewports': [], 'errors': [], 'failed': []}
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(reduced_motion='reduce', locale='it-IT')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install', timeout=90000)
    page = context.new_page()
    page.on('pageerror', lambda error: report['errors'].append(str(error)))
    page.on('response', lambda response: report['failed'].append(response.url) if response.status >= 400 else None)
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.goto('http://127.0.0.1:8069/aboutus', wait_until='networkidle', timeout=90000)
    page.add_script_tag(path=str(ROOT / 'docs/qa-final/axe-4.10.3.min.js'))
    viewports = [] if MOTION_ONLY else [(1440, 1000), (1280, 720), (1024, 768), (834, 1112), (390, 844), (320, 740)]
    for width, height in viewports:
        page.set_viewport_size({'width': width, 'height': height})
        page.evaluate('window.scrollTo(0, 0)')
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(250)
        metrics = page.evaluate('''() => {
            const root=document.querySelector('#wrap');
            const articles=[...root.querySelectorAll('.tp-about-grid article')];
            const photo=root.querySelector('.tp-about-photo img');
            const caption=root.querySelector('.tp-about-photo figcaption').getBoundingClientRect();
            const photoBox=photo.getBoundingClientRect();
            return {width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,
                textOverflow:[...root.querySelectorAll('.tp-about-opening h1,.tp-about-opening p,.tp-about-generations h3,.tp-about-generations p')].filter(el=>el.scrollWidth>el.clientWidth+1).map(el=>el.textContent),
                h1:root.querySelectorAll('h1').length,
                titleFont:getComputedStyle(root.querySelector('h1')).fontSize,
                background:getComputedStyle(root.querySelector('.tp-about-opening')).backgroundColor,
                imageLoaded:photo.complete&&photo.naturalWidth>0,
                nativeImage:!photo.closest('.o_not_editable,.o_not_selectable'),
                captionInside:caption.left>=photoBox.left&&caption.right<=photoBox.right&&caption.top>=photoBox.top&&caption.bottom<=photoBox.bottom,
                years:articles.map(el=>el.querySelector('.tp-about-year')?.textContent),
                yearsDecorative:articles.every(el=>el.querySelector('.tp-about-year')?.getAttribute('aria-hidden')==='true'),
                margins:articles.map(el=>getComputedStyle(el).marginTop),
                chapters:articles.map(el=>el.getBoundingClientRect().toJSON()),
                chapterStarts:articles.map(el=>el.querySelector('.tp-about-period').getBoundingClientRect().top),
                copy:articles.map(el=>el.querySelector('p:not([class])').textContent.trim())};
        }''')
        # Low-contrast, aria-hidden watermark dates are decoration, not reading text.
        metrics['a11y'] = page.evaluate('''async () => (await axe.run({include:[['.tp-about-opening'],['.tp-about-generations']],exclude:[['.tp-about-year[aria-hidden="true"]']]},
            {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))''')
        report['viewports'].append(metrics)
        print(json.dumps({key:value for key,value in metrics.items() if key not in ['chapters','copy']}), flush=True)
        if width in [1440, 390]:
            page.screenshot(path=str(IMAGES / f'about-{width}-full.png'), full_page=True)
            page.locator('.tp-about-generations').screenshot(path=str(IMAGES / f'about-{width}-generations.png'))
    context.close()
    context = browser.new_context(viewport={'width':1440,'height':700}, reduced_motion='no-preference')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
    page=context.new_page()
    page.goto('http://127.0.0.1:8069/aboutus',wait_until='networkidle',timeout=90000)
    report['motion'] = page.locator('.tp-about-generations').evaluate('''el=>({
        enhanced:el.classList.contains('has-editorial-reveal'),
        initial:[...el.querySelectorAll('article')].map(a=>({opacity:getComputedStyle(a).opacity,
            transform:getComputedStyle(a).transform,delay:getComputedStyle(a).transitionDelay,
            duration:getComputedStyle(a).transitionDuration}))})''')
    for article in page.locator('.tp-about-grid article').all():
        article.scroll_into_view_if_needed()
        page.wait_for_timeout(1200)
    report['motion']['visible']=page.locator('.tp-about-grid article').evaluate_all('els=>els.every(el=>getComputedStyle(el).opacity==="1"&&getComputedStyle(el).transform==="none")')
    report['motion']['settings']=page.locator('.tp-about-grid article').evaluate_all('els=>els.map(el=>({delay:getComputedStyle(el).transitionDelay.split(",")[0].trim(),duration:getComputedStyle(el).transitionDuration}))')
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_timeout(100)
    report['motion']['reducedVisible']=page.locator('.tp-about-grid article').evaluate_all('els=>els.every(el=>getComputedStyle(el).opacity==="1"&&getComputedStyle(el).transform==="none")')
    context.close()
    context=browser.new_context(java_script_enabled=False)
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
    page=context.new_page()
    page.goto('http://127.0.0.1:8069/aboutus',wait_until='networkidle',timeout=90000)
    report['motion']['noJsVisible']=page.locator('.tp-about-grid article').evaluate_all('els=>els.every(el=>getComputedStyle(el).opacity==="1")')
    browser.close()
(OUT / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
assert not report['errors'] and not report['failed'], report
for metrics in report['viewports']:
    assert metrics['overflow'] <= 1 and not metrics['textOverflow'], metrics
    assert metrics['h1'] == 1 and metrics['imageLoaded'] and metrics['nativeImage'] and metrics['captionInside'], metrics
    assert metrics['years'] == ['1945','1980','2020'] and metrics['yearsDecorative'], metrics
    assert metrics['background'] == 'rgb(238, 242, 237)' and not metrics['a11y'], metrics
    assert metrics['copy'] == expected, 'The supplied paragraphs must remain exact'
    a, b, c = metrics['chapters']
    if metrics['width'] >= 992:
        assert metrics['margins'] == ['0px','80px','160px'], metrics
        first, second, third = metrics['chapterStarts']
        assert a['left'] < b['left'] < c['left'] and first < second < third, metrics
    else:
        assert metrics['margins'] == ['0px','0px','0px'], metrics
        assert abs(a['left']-b['left']) < 1 and abs(b['left']-c['left']) < 1, metrics
        assert a['bottom']+32 <= b['top'] and b['bottom']+32 <= c['top'], metrics
assert report['motion']['enhanced'] and report['motion']['visible'], report['motion']
assert report['motion']['reducedVisible'] and report['motion']['noJsVisible'], report['motion']
assert [item['delay'] for item in report['motion']['settings']] == ['0s','0.2s','0.4s'], report['motion']
assert all('0.7s' in item['duration'] for item in report['motion']['settings']), report['motion']
assert all(item['opacity']=='0' and '20)' in item['transform'] for item in report['motion']['initial']), report['motion']
print('Motion, reduced-motion and no-JS checks passed',flush=True)
