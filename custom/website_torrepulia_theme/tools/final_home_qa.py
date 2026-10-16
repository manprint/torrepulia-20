"""Read-only public homepage QA on the owner's final local composition."""
import json
import os
import sys
import tempfile
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'qa-final'
OUT.mkdir(exist_ok=True)
IMAGES = Path(os.environ.get('TORREPULIA_QA_IMAGES', OUT))
IMAGES.mkdir(parents=True, exist_ok=True)
ROUND = sys.argv[1] if len(sys.argv) > 1 else 'baseline'
BASE = 'http://127.0.0.1:8069'
cache = Path(os.environ.get('TORREPULIA_QA_CACHE', Path(tempfile.gettempdir()) / 'torrepulia-qa'))
cache.mkdir(parents=True, exist_ok=True)
axe = cache / 'axe-4.10.3.min.js'
if not axe.exists():
    response = requests.get('https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.3/axe.min.js', timeout=45)
    response.raise_for_status()
    axe.write_text(response.text, encoding='utf-8')

report = {'round': ROUND, 'screenshotsRoot':str(IMAGES), 'viewports': [], 'functional': [], 'motion': {}}
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height in [(1440, 1000), (1920, 1080), (834, 1112), (390, 844), (320, 740)]:
        context = browser.new_context(viewport={'width': width, 'height': height},
            reduced_motion='reduce', locale='it-IT', has_touch=width < 900)
        context.request.get(BASE + '/web/login?db=torrepulia_cinematic_install')
        page = context.new_page()
        errors, failed = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: failed.append({'status': response.status, 'url': response.url}) if response.status >= 400 else None)
        page.goto(BASE, wait_until='networkidle', timeout=90000)
        page.locator('.mc-catalog .format-option').first.wait_for(timeout=30000)
        for section in page.locator('#wrap > section').all():
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(160)
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(400)
        metrics = page.evaluate('''() => {
            const root = document.querySelector('#wrap');
            const visible = el => el.getBoundingClientRect().width > 0 && el.getBoundingClientRect().height > 0;
            return {
                lang:document.documentElement.lang,
                heroSource:root.querySelector('.hero-photo')?.currentSrc,
                heroCovered:(() => {
                    const frame=root.querySelector('.hero').getBoundingClientRect();
                    const image=root.querySelector('.hero-photo').getBoundingClientRect();
                    return image.top<=frame.top+1 && image.left<=frame.left+1 && image.bottom>=frame.bottom-1 && image.right>=frame.right-1;
                })(),
                overflow:document.documentElement.scrollWidth-innerWidth,
                overflowNodes:[...root.querySelectorAll('*')].filter(visible).filter(el=>{
                    const r=el.getBoundingClientRect();return r.right>innerWidth+2||r.left < -2;
                }).slice(0,18).map(el=>({tag:el.tagName,cls:el.className,box:JSON.stringify(el.getBoundingClientRect())})),
                images:[...root.querySelectorAll('img')].filter(visible).filter(el=>!el.complete||!el.naturalWidth).map(el=>el.src),
                textOverflow:[...root.querySelectorAll('h1,h2,h3,p,button,.button')].filter(visible).filter(el=>el.clientWidth&&el.scrollWidth>el.clientWidth+3).map(el=>({tag:el.tagName,cls:el.className,text:el.textContent.slice(0,90),width:el.clientWidth,scroll:el.scrollWidth})),
                h1:root.querySelectorAll('h1').length,
                textAlign:[...root.querySelectorAll('.regina-copy p')].map(el=>getComputedStyle(el).textAlign),
                reducedRunning:[...root.getAnimations({subtree:true})].filter(a=>a.playState==='running').map(a=>a.animationName||'WAAPI'),
                sections:[...root.children].filter(el=>el.tagName==='SECTION').map(el=>({id:el.id,snippet:el.dataset.snippet,height:el.offsetHeight})),
                anchors:[...root.querySelectorAll('a[href^="#"]')].filter(el=>el.hash.length>1&&!document.getElementById(el.hash.slice(1))).map(el=>el.hash)
            };
        }''')
        page.add_script_tag(path=str(axe))
        a11y = page.evaluate('''async () => {
            const result=await axe.run({include:[['.tp-site']]},{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}});
            return {violations:result.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary,html:n.html}))})),incomplete:result.incomplete.map(v=>({id:v.id,count:v.nodes.length})),passes:result.passes.length};
        }''')
        page.screenshot(path=str(IMAGES / f'{ROUND}-{width}-full.png'), full_page=True)
        if width in [1440, 390]:
            for selector, name in [('.hero','hero'),('#regina','regina'),('#peranzana','peranzana'),('#territorio','closing')]:
                page.locator(selector).screenshot(path=str(IMAGES / f'{ROUND}-{width}-{name}.png'))
        result = {'width': width, 'metrics': metrics, 'errors': errors, 'failed': failed, 'a11y': a11y}
        report['viewports'].append(result)
        print(width, json.dumps({'overflow':metrics['overflow'],'textOverflow':metrics['textOverflow'],'images':metrics['images'],'errors':errors,'violations':[(v['id'],len(v['nodes'])) for v in a11y['violations']]}), flush=True)
        if width == 1440:
            for key in ['taste', 'table', 'aroma']:
                tab = page.locator(f'[data-sensory="{key}"]')
                tab.click()
                report['functional'].append({'test':'sensory-'+key,'passed':tab.get_attribute('aria-selected')=='true' and page.locator(f'[data-panel="{key}"]').is_visible()})
            tab = page.locator('[data-sensory="aroma"]')
            tab.focus();page.keyboard.press('ArrowRight')
            report['functional'].append({'test':'sensory-keyboard','passed':page.locator('[data-sensory="taste"]').get_attribute('aria-selected')=='true'})
            for option in page.locator('.mc-catalog .format-option').all():
                option.click(); identifier=option.get_attribute('data-product')
                report['functional'].append({'test':'format-'+identifier,'passed':page.locator(f'.mc-catalog [data-preview="{identifier}"]').is_visible() and page.locator(f'.mc-catalog [data-summary="{identifier}"]').is_visible()})
            for link in page.locator('#wrap a[href^="/shop"]').all():
                url=link.get_attribute('href')
                if url not in [item.get('url') for item in report['functional']]:
                    response=context.request.get(BASE+url)
                    report['functional'].append({'test':'shop-link','url':url,'passed':response.ok,'status':response.status})
        if width == 390:
            toggle=page.locator('.menu-toggle')
            toggle.click()
            report['functional'].append({'test':'mobile-menu-open','passed':page.locator('#mc-mobile-menu').is_visible()})
            toggle.click()
            hotspot=page.locator('.tp-bib-hotspot')
            hotspot.tap()
            report['functional'].append({'test':'touch-tooltip','passed':page.locator('.tp-bib-tooltip').is_visible()})
            page.keyboard.press('Escape')
            report['functional'].append({'test':'tooltip-escape','passed':not page.locator('.tp-bib-tooltip').is_visible()})
        context.close()
    context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='no-preference')
    context.request.get(BASE+'/web/login?db=torrepulia_cinematic_install')
    page=context.new_page();page.goto(BASE,wait_until='networkidle',timeout=90000)
    closing=page.locator('#territorio');closing.scroll_into_view_if_needed();page.wait_for_timeout(300)
    button=closing.locator('.mc-breeze-toggle');button.click()
    paused=closing.locator('.mc-territory-photo img').evaluate('(el)=>getComputedStyle(el).animationPlayState')
    button.click()
    resumed=closing.locator('.mc-territory-photo img').evaluate('(el)=>getComputedStyle(el).animationPlayState')
    report['motion']={'paused':paused,'resumed':resumed,'staticHero':page.locator('.hero-photo').evaluate('(el)=>getComputedStyle(el).animationName')}
    browser.close()

(OUT / f'{ROUND}-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
failures = [item for item in report['functional'] if not item['passed']]
print('FUNCTIONAL FAILURES', failures, 'MOTION', report['motion'], flush=True)
assert not failures, failures
for viewport in report['viewports']:
    metrics = viewport['metrics']
    assert not viewport['errors'] and not viewport['failed'], viewport
    assert not viewport['a11y']['violations'], viewport['a11y']['violations']
    assert metrics['overflow'] <= 1 and not metrics['textOverflow'] and not metrics['images'], metrics
    assert metrics['heroCovered'] and metrics['lang'] == 'it-IT', metrics
    assert metrics['h1'] == 1 and not metrics['anchors'] and not metrics['reducedRunning'], metrics
    assert all(value == 'left' for value in metrics['textAlign']), metrics
assert report['motion'] == {'paused':'paused', 'resumed':'running', 'staticHero':'none'}, report['motion']
