"""Read-only responsive, copy, contrast and CTA checks for the closing Radici blocks."""
import json
import os
from pathlib import Path
from lxml import etree
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/qa-about'
IMAGES=Path(os.environ.get('TORREPULIA_QA_IMAGES',OUT))
IMAGES.mkdir(parents=True,exist_ok=True)
source=etree.parse(str(ROOT/'views/snippets/s_roots_closing.xml'))
expected=[' '.join(''.join(node.itertext()).split()) for node in source.xpath('//p[not(@aria-hidden)]')]
report={'viewports':[],'errors':[],'failed':[]}
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(reduced_motion='reduce',locale='it-IT')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
    page=context.new_page()
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.on('response',lambda response:report['failed'].append(response.url) if response.status>=400 else None)
    page.set_viewport_size({'width':1440,'height':1000})
    page.goto('http://127.0.0.1:8069/aboutus',wait_until='networkidle',timeout=90000)
    page.add_script_tag(path=str(ROOT/'docs/qa-final/axe-4.10.3.min.js'))
    for width,height in [(1440,1000),(1024,768),(834,1112),(390,844),(320,740)]:
        page.set_viewport_size({'width':width,'height':height})
        for section in page.locator('.tp-roots-transition,.tp-roots-values,.tp-roots-cta').all():
            section.scroll_into_view_if_needed()
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(300)
        metrics=page.evaluate('''() => {
            const selectors=['.tp-roots-transition','.tp-roots-values','.tp-roots-cta'];
            const sections=selectors.map(s=>document.querySelector(s));
            const button=sections[2].querySelector('a.btn'),photo=sections[0].querySelector('img');
            const boxes=selector=>[...document.querySelectorAll(selector)].map(el=>el.getBoundingClientRect().toJSON());
            return {width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,
                sections:[...document.querySelector('#wrap').children].filter(el=>el.tagName==='SECTION').slice(-3).map(el=>el.dataset.snippet),
                textOverflow:sections.flatMap(s=>[...s.querySelectorAll('h2,h3,p,a')]).filter(el=>el.scrollWidth>el.clientWidth+1).map(el=>el.textContent),
                copy:sections.flatMap(s=>[...s.querySelectorAll('p:not([aria-hidden])')]).map(el=>el.textContent.trim().replace(/\\s+/g,' ')),
                nativeEditable:sections.every(s=>!s.querySelector('.o_not_editable,.o_not_selectable,[t-call]')),
                photoLoaded:photo.complete&&photo.naturalWidth>0,
                transition:boxes('.tp-roots-transition .row > .order-1,.tp-roots-transition .row > .order-md-2'),values:boxes('.tp-roots-values .row > .col-12'),
                photoTextCenterDelta:(()=>{const a=photo.getBoundingClientRect(),b=sections[0].querySelector('.lead').getBoundingClientRect();return Math.abs((a.top+a.bottom-b.top-b.bottom)/2);})(),
                rightPadding:getComputedStyle(sections[0].querySelector('.tp-roots-transition-copy')).paddingRight,
                subtitle:sections[1].querySelector('.tp-roots-values-subtitle').textContent.trim(),
                numeralSize:getComputedStyle(sections[1].querySelector('.tp-roots-numeral')).fontSize,
                descriptionColor:getComputedStyle(sections[1].querySelector('.tp-roots-description')).color,
                ctaLines:(()=>{const range=document.createRange();range.selectNodeContents(sections[2].querySelector('h2'));return range.getClientRects().length;})(),
                footerColors:[document.querySelector('.tp-site>footer'),document.querySelector('#mc-footer')].map(el=>getComputedStyle(el).backgroundColor),
                backgrounds:sections.map(el=>getComputedStyle(el).backgroundColor),
                cta:{href:button.getAttribute('href'),label:button.textContent.trim().replace(/\\s+/g,' '),height:button.getBoundingClientRect().height}
            };
        }''')
        metrics['violations']=page.evaluate('''async()=> (await axe.run({include:[['.tp-roots-transition'],['.tp-roots-values'],['.tp-roots-cta'],['#mc-footer']]},
            {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))''')
        report['viewports'].append(metrics)
        print(json.dumps({key:value for key,value in metrics.items() if key not in ['copy','transition','values']}),flush=True)
        if width in [1440,390]:
            for name in ['transition','values','cta']:
                page.locator('.tp-roots-'+name).screenshot(path=str(IMAGES/f'roots-{width}-{name}.png'))
            page.locator('#mc-footer').screenshot(path=str(IMAGES/f'roots-{width}-footer.png'))
        if width==1440:
            button=page.locator('.tp-roots-cta .btn')
            initial=button.evaluate('(el)=>getComputedStyle(el).backgroundColor')
            button.hover();page.wait_for_timeout(220)
            report['hoverChanged']=button.evaluate('(el)=>getComputedStyle(el).backgroundColor')!=initial
    report['shopStatus']=context.request.get('http://127.0.0.1:8069/shop',timeout=90000).status
    report['otherFooters']={}
    for route in ['/','/shop']:
        page.goto('http://127.0.0.1:8069'+route,wait_until='networkidle',timeout=90000)
        report['otherFooters'][route]=page.locator('#mc-footer').evaluate('(el)=>getComputedStyle(el).backgroundColor')
    browser.close()
(OUT/'closing-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert not report['errors'] and not report['failed'],report
assert report['shopStatus']==200 and report['hoverChanged'],report
for metrics in report['viewports']:
    assert metrics['overflow']<=1 and not metrics['textOverflow'] and not metrics['violations'],metrics
    assert metrics['photoLoaded'] and metrics['nativeEditable'] and metrics['copy']==expected,metrics
    assert metrics['sections']==['s_torrepulia_roots_transition','s_torrepulia_roots_values','s_torrepulia_roots_cta'],metrics
    assert metrics['cta']['href']=='/shop' and metrics['cta']['label']=='Entra nello Shop Online' and metrics['cta']['height']>=44,metrics
    assert metrics['backgrounds']==['rgb(32, 59, 47)','rgb(255, 255, 255)','rgb(24, 35, 31)'],metrics
    assert metrics['footerColors']==['rgb(24, 35, 31)','rgb(24, 35, 31)'],metrics
    assert metrics['numeralSize']=='24px' and metrics['descriptionColor']=='rgba(24, 35, 31, 0.8)',metrics
    a,b=metrics['transition']
    first,second,third=metrics['values']
    if metrics['width']>=768:
        assert a['right']<=b['left']+1 and first['right']<=second['left']+1 and second['right']<=third['left']+1,metrics
        assert metrics['photoTextCenterDelta']<=1 and metrics['rightPadding']=='48px',metrics
        if metrics['width']>=834:assert metrics['ctaLines']==1,metrics
    else:
        assert a['bottom']<=b['top']+1 and first['bottom']<=second['top']+1 and second['bottom']<=third['top']+1,metrics
assert all(color=='rgb(24, 35, 31)' for color in report['otherFooters'].values()),report['otherFooters']
print('Closing Radici checks passed',flush=True)
