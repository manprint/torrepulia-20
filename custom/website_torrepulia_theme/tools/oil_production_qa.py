"""Read-only responsive, overlap and motion checks for native production cards."""
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
        section=page.locator('.tp-production-cards')
        for photo in section.locator('.tp-phase-media img').all():
            photo.scroll_into_view_if_needed()
            photo.evaluate('el=>el.decode()')
        result=page.evaluate('''() => {
            const s=document.querySelector('.tp-production-cards');
            const cards=[...s.querySelectorAll('article')];
            const rows=new Set(cards.map(el=>Math.round(el.getBoundingClientRect().top)));
            const overlaps=cards.flatMap((el,i)=>{
                const img=el.querySelector('.tp-phase-media').getBoundingClientRect();
                const h=el.querySelector('h3').getBoundingClientRect();
                const p=el.querySelector('p').getBoundingClientRect(),r=el.getBoundingClientRect();
                return img.bottom>h.top+1||h.bottom>p.top+1||p.bottom>r.bottom+1?[i]:[];
            });
            const cta=document.querySelector('.tp-oil-pairings .btn');
            const sensory=document.querySelector('.tp-sensory-list'),dt=getComputedStyle(sensory.querySelector('dt')),dd=getComputedStyle(sensory.querySelector('dd'));
            const pairs=[...document.querySelectorAll('.tp-oil-pairings .row > div')].map(el=>el.getBoundingClientRect());
            return {width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,
                cards:cards.length,rows:rows.size,overlaps,
                headings:cards.map(el=>el.querySelector('h3').textContent),
                descriptionsLeft:cards.every(el=>getComputedStyle(el.querySelector('p')).textAlign==='left'),
                squareMedia:cards.every(el=>{const r=el.querySelector('.tp-phase-media').getBoundingClientRect();return Math.abs(r.width-r.height)<1}),
                pairingsLeft:[...document.querySelectorAll('.tp-oil-pairings h2,.tp-oil-pairings h3,.tp-oil-pairings p')].every(el=>getComputedStyle(el).textAlign==='left'),
                ctaBackground:getComputedStyle(cta).backgroundColor,ctaColor:getComputedStyle(cta).color,
                sensory:{case:dt.textTransform,labelSize:parseFloat(dt.fontSize),descriptionSize:parseFloat(dd.fontSize),font:dd.fontFamily,
                    notes:[...sensory.querySelectorAll('strong')].map(el=>el.textContent)},
                nitrogen:s.textContent.toLowerCase().includes('azoto'),
                mediaLoaded:[...s.querySelectorAll('.tp-phase-media img')].every(el=>el.naturalWidth>0),
                imageSources:[...s.querySelectorAll('.tp-phase-media img')].map(el=>el.getAttribute('src')),
                pairingsSideBySide:pairs[1].left>=pairs[0].right-1,
                pairingsStacked:pairs[1].top>=pairs[0].bottom,
                cta:cta.getAttribute('href'),text:cta.textContent.trim(),
                hasLegacyTimeline:!!s.querySelector('.tp-process-timeline')};
        }''')
        section.screenshot(path=str(IMAGES/f'production-{width}.png'),style='header { visibility: hidden !important; }')
        page.locator('.tp-sensory').screenshot(path=str(IMAGES/f'sensory-{width}.png'),style='header { visibility: hidden !important; }')
        page.locator('.tp-oil-pairings').screenshot(path=str(IMAGES/f'pairings-{width}.png'),style='header { visibility: hidden !important; }')
        report['cases'].append(result)
        print(json.dumps(result),flush=True)
    page.set_viewport_size({'width':1440,'height':1000})
    page.emulate_media(reduced_motion='no-preference')
    card=page.locator('.tp-production-cards article').first
    card.scroll_into_view_if_needed()
    before=card.bounding_box()
    card.hover()
    page.wait_for_timeout(400)
    report['hoverTransform']=card.locator('.tp-phase-media img').evaluate('el=>getComputedStyle(el).transform')
    report['stableCard']=before==card.bounding_box()
    page.emulate_media(reduced_motion='reduce')
    report['reducedTransform']=card.locator('.tp-phase-media img').evaluate('el=>getComputedStyle(el).transform')
    page.locator('.tp-oil-pairings .btn').click()
    page.wait_for_url('**/shop',timeout=90000)
    report['shopReached']=page.url.endswith('/shop')
    browser.close()
(OUT/'oil-production-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not report['errors'],report
for c in report['cases']:
    assert c['cards']==4 and c['rows']==(1 if c['width']>=992 else 2 if c['width']>=768 else 4),c
    assert not c['overlaps'] and c['overflow']<=1 and c['mediaLoaded'],c
    assert c['descriptionsLeft'] and c['squareMedia'] and c['pairingsLeft'],c
    assert c['headings'][-1]=='Confezionamento Accurato',c
    assert c['ctaBackground']=='rgb(24, 35, 31)' and c['ctaColor']=='rgb(255, 255, 255)',c
    assert c['sensory']['case']=='uppercase' and c['sensory']['descriptionSize']>=28 and c['sensory']['labelSize']==12,c
    assert 'Libre Caslon Display' in c['sensory']['font'] and c['sensory']['notes']==['pomodoro verde','carciofo','mandorla fresca'],c
    assert not c['nitrogen'] and not c['hasLegacyTimeline'],c
    assert c['pairingsSideBySide'] if c['width']>=768 else c['pairingsStacked'],c
    assert c['cta']=='/shop' and c['text']=='Portalo in tavola',c
assert report['hoverTransform'].startswith('matrix(1.045') and report['stableCard'],report
assert report['reducedTransform']=='none' and report['shopReached'],report
print('Production grid, text flow, authentic media, hover, reduced motion and shop CTA passed')
