"""Check opaque affixed navigation, stable scroll and responsive About photography."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/qa-final'
IMAGES=Path(os.environ.get('TORREPULIA_QA_IMAGES',OUT))
IMAGES.mkdir(parents=True,exist_ok=True)
report={'cases':[],'errors':[]}
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(reduced_motion='reduce')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
    page=context.new_page()
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    for width,height in [(1440,1000),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        for route in ['/aboutus','/']:
            page.goto('http://127.0.0.1:8069'+route,wait_until='networkidle',timeout=90000)
            page.evaluate('document.fonts.ready')
            result={'width':width,'route':route}
            if route=='/aboutus':
                result['initialHeader']=page.locator('.mc-header').evaluate('el=>({background:getComputedStyle(el).backgroundColor,border:getComputedStyle(el).borderBottomColor})')
                photo=page.locator('.tp-roots-transition img')
                photo.scroll_into_view_if_needed()
                photo.evaluate('(el)=>el.decode()')
                result.update(page.evaluate('''() => {
                    const archive=document.querySelector('.tp-roots-transition img'),a=archive.getBoundingClientRect();
                    const hero=document.querySelector('.tp-about-photo img'),b=hero.getBoundingClientRect();
                    return {archiveRatio:a.width/a.height,naturalRatio:archive.naturalWidth/archive.naturalHeight,
                        heroRatio:b.width/b.height,heroFit:getComputedStyle(hero).objectFit,
                        openingBackground:getComputedStyle(document.querySelector('.tp-about-opening')).backgroundColor,
                        generationsBackground:getComputedStyle(document.querySelector('.tp-about-generations')).backgroundColor};
                }'''))
                page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
                page.wait_for_timeout(350)
                result['photoDocBefore']=photo.evaluate('(el)=>el.getBoundingClientRect().top+scrollY')
            page.mouse.wheel(0,900)
            page.wait_for_timeout(400)
            page.mouse.wheel(0,-80)
            page.wait_for_timeout(700)
            result.update(page.evaluate('''() => {
                const header=document.querySelector('.tp-site>header'),bar=header.querySelector('.mc-header');
                return {affixed:header.classList.contains('o_header_affixed'),position:getComputedStyle(header).position,
                    background:getComputedStyle(bar).backgroundColor,color:getComputedStyle(bar).color,
                    barTop:bar.getBoundingClientRect().top,opacity:getComputedStyle(header).opacity,
                    overflow:document.documentElement.scrollWidth-innerWidth};
            }'''))
            if route=='/aboutus':
                result['photoDocAfter']=photo.evaluate('(el)=>el.getBoundingClientRect().top+scrollY')
            label='about' if route=='/aboutus' else 'home'
            page.screenshot(path=str(IMAGES/f'header-{width}-{label}.png'))
            if route=='/aboutus' and width==390:
                page.locator('.menu-toggle').click()
                page.wait_for_timeout(400)
                result['menuBackground']=page.locator('#mc-mobile-menu').evaluate('el=>getComputedStyle(el).backgroundColor')
                assert page.locator('#mc-mobile-menu').is_visible()
                page.screenshot(path=str(IMAGES/'header-390-about-menu.png'))
                page.locator('.menu-toggle').click()
            report['cases'].append(result)
            print(json.dumps(result),flush=True)
    browser.close()
(OUT/'header-media-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not report['errors'],report['errors']
for result in report['cases']:
    assert result['affixed'] and result['position']=='fixed' and abs(result['barTop'])<1,result
    assert result['opacity']=='1' and result['overflow']<=1,result
    if result['route']=='/aboutus':
        assert result['background'] in ['rgb(238, 242, 237)','rgba(238, 242, 237, 0.97)'] and result['color']=='rgb(46, 73, 59)',result
        assert result['initialHeader']=={'background':'rgb(238, 242, 237)','border':'rgba(0, 0, 0, 0)'},result
        if result['width']==390:
            assert result['menuBackground']=='rgb(238, 242, 237)',result
        assert abs(result['archiveRatio']-result['naturalRatio'])<.002,result
        assert abs(result['heroRatio']-(2 if result['width']>760 else 1.5))<.002 and result['heroFit']=='cover',result
        assert result['openingBackground']=='rgb(238, 242, 237)',result
        assert result['generationsBackground']=='rgb(238, 242, 237)',result
        assert abs(result['photoDocBefore']-result['photoDocAfter'])<1,result
    else:
        assert result['background']=='rgb(24, 35, 31)' and result['color']=='rgb(255, 255, 255)',result
print('Opaque navigation, photo proportions and pale opening verified',flush=True)
