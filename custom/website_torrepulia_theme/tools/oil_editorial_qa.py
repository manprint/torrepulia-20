"""Read-only responsive verification of the Peranzana editorial opening."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parents[1]/'docs/qa-final'
IMAGES=Path(os.environ.get('TORREPULIA_QA_IMAGES',OUT))
IMAGES.mkdir(parents=True,exist_ok=True)
report={'cases':[],'errors':[]}
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(reduced_motion='reduce')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
    page=context.new_page()
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    for width in [1440,1024,834,390,360]:
        page.set_viewport_size({'width':width,'height':1000 if width>760 else 844})
        page.goto('http://127.0.0.1:8069/l-olio',wait_until='networkidle',timeout=90000)
        page.evaluate('document.fonts.ready')
        page.locator('.tp-oil-photo').evaluate('el=>el.decode()')
        for pin in page.locator('.tp-oil-pin').all():
            pin.scroll_into_view_if_needed()
            pin.evaluate('el=>el.decode()')
        page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
        page.wait_for_timeout(350)
        result=page.evaluate('''() => {
            const a=document.querySelector('.tp-oil-opening'),b=document.querySelector('.tp-oil-history');
            const cols=a.querySelectorAll('.row > div'),r=[...cols].map(el=>el.getBoundingClientRect());
            const header=document.querySelector('.mc-header'),hs=getComputedStyle(header);
            return {width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,
                backgrounds:[a,b].map(el=>getComputedStyle(el).backgroundColor),
                header:hs.backgroundColor,border:hs.borderBottomColor,
                columnsSideBySide:r[1].left>=r[0].right-1,
                stacked:r[1].top>=r[0].bottom,
                imageLoaded:document.querySelector('.tp-oil-photo').naturalWidth>0,
                h1:document.querySelectorAll('h1').length,
                brokenImages:[...document.images].filter(el=>el.complete&&!el.naturalWidth).map(el=>el.src),
                headings:[...b.querySelectorAll('h2,h3')].map(el=>el.textContent),
                leftAligned:[...b.querySelectorAll('h2,h3,h4,p')].every(el=>getComputedStyle(el).textAlign==='left'),
                heroTextWidth:cols[0].querySelector('.lead').getBoundingClientRect().width,
                historyColumns:b.querySelector('.tp-oil-history-story > div:last-child').getBoundingClientRect().left>b.querySelector('.tp-oil-history-story > div:first-child').getBoundingClientRect().left,
                places:[...b.querySelectorAll('.tp-oil-place h4')].map(el=>el.textContent),
                placesRows:new Set([...b.querySelectorAll('.tp-oil-place')].map(el=>Math.round(el.getBoundingClientRect().top))).size,
                territoryBackground:getComputedStyle(b.querySelector('.tp-oil-territory')).backgroundColor,
                pinsLoaded:[...b.querySelectorAll('.tp-oil-pin')].every(el=>el.naturalWidth>0)};
        }''')
        page.screenshot(path=str(IMAGES/f'oil-{width}.png'),full_page=True)
        page.locator('.tp-oil-opening').screenshot(path=str(IMAGES/f'oil-opening-{width}.png'),style='header { visibility: hidden !important; }')
        page.locator('.tp-oil-history').screenshot(path=str(IMAGES/f'oil-history-{width}.png'),style='header { visibility: hidden !important; }')
        page.locator('.tp-oil-process-link').click()
        page.wait_for_timeout(700)
        result['anchor']=page.evaluate("({hash:location.hash,top:document.querySelector('#processo').getBoundingClientRect().top})")
        page.mouse.wheel(0,-80)
        page.wait_for_timeout(700)
        result['scrollHeader']=page.locator('.mc-header').evaluate('el=>getComputedStyle(el).backgroundColor')
        if width==390:
            page.locator('.menu-toggle').click()
            page.wait_for_timeout(400)
            result['menuVisible']=page.locator('#mc-mobile-menu').is_visible()
            result['menuBackground']=page.locator('#mc-mobile-menu').evaluate('el=>getComputedStyle(el).backgroundColor')
        report['cases'].append(result)
        print(json.dumps(result),flush=True)
    browser.close()
(OUT/'oil-editorial-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not report['errors'],report
for result in report['cases']:
    assert result['overflow']<=1 and result['imageLoaded'] and not result['brokenImages'],result
    assert result['h1']==1 and result['backgrounds']==['rgb(255, 255, 255)']*2,result
    assert result['header']=='rgb(255, 255, 255)' and result['border']=='rgba(0, 0, 0, 0)',result
    assert result['columnsSideBySide'] if result['width']>=992 else result['stacked'],result
    assert result['leftAligned'] and len(result['places'])==3 and result['territoryBackground']=='rgba(0, 0, 0, 0)',result
    assert result['pinsLoaded'],result
    assert result['placesRows']==(1 if result['width']>=768 else 3),result
    assert result['historyColumns']==(result['width']>=992),result
    if result['width']>=1200:
        assert result['heroTextWidth']>=680,result
    assert result['anchor']['hash']=='#processo' and result['anchor']['top']>=0,result
    assert result['scrollHeader'] in ['rgb(255, 255, 255)','rgba(255, 255, 255, 0.97)'],result
    if result['width']==390:
        assert result['menuVisible'] and result['menuBackground']=='rgb(255, 255, 255)',result
print('Oil editorial responsive layout, media and navigation verified')
