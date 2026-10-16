"""Verify the photo/footer join geometrically and by sampling rendered pixels."""
import json
import os
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/qa-final'
IMAGES=Path(os.environ.get('TORREPULIA_QA_IMAGES',OUT))
IMAGES.mkdir(parents=True,exist_ok=True)
report={'viewports':[],'errors':[]}
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(reduced_motion='reduce')
    context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
    page=context.new_page()
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.set_viewport_size({'width':1880,'height':1000})
    page.goto('http://127.0.0.1:8069',wait_until='networkidle',timeout=90000)
    page.evaluate('document.fonts.ready')
    for width,height in [(1880,1000),(1440,1000),(834,1112),(390,844)]:
        page.set_viewport_size({'width':width,'height':height})
        page.locator('#territorio').scroll_into_view_if_needed()
        page.locator('#territorio img').first.evaluate('(el)=>el.decode()')
        page.evaluate('''() => {
            const closing=document.querySelector('#territorio').getBoundingClientRect();
            window.scrollTo({top:scrollY+closing.bottom-innerHeight*.6,behavior:'instant'});
        }''')
        page.wait_for_timeout(450)
        metrics=page.evaluate('''() => {
            const closing=document.querySelector('#territorio'),footer=document.querySelector('.tp-site>footer');
            const box=closing.getBoundingClientRect(),next=footer.getBoundingClientRect();
            return {width:innerWidth,joinY:box.bottom,sectionHeight:box.height,gap:next.top-box.bottom,
                footerColor:getComputedStyle(footer).backgroundColor,
                overlay:getComputedStyle(closing,'::after').backgroundImage,
                overflow:document.documentElement.scrollWidth-innerWidth};
        }''')
        path=IMAGES/f'closing-blend-{width}.png'
        page.screenshot(path=str(path))
        bitmap=Image.open(path).convert('RGB')
        row=round(metrics['joinY'])
        assert 5<row<height-5,metrics
        samples=[]
        for fraction in [.02,.25,.5,.75,.98]:
            x=round((width-1)*fraction)
            before=bitmap.getpixel((x,row-3))
            after=bitmap.getpixel((x,row+3))
            samples.append({'x':x,'above':before,'below':after,'delta':max(abs(a-b) for a,b in zip(before,after))})
        metrics['pixels']=samples
        report['viewports'].append(metrics)
        print(json.dumps({'width':width,'gap':metrics['gap'],'maxPixelDelta':max(s['delta'] for s in samples),'footerColor':metrics['footerColor']}),flush=True)
    browser.close()
(OUT/'closing-blend-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not report['errors'],report['errors']
for metrics in report['viewports']:
    assert abs(metrics['gap'])<=1 and metrics['overflow']<=1,metrics
    assert metrics['footerColor']=='rgb(24, 35, 31)',metrics
    assert all(sample['delta']<=2 for sample in metrics['pixels']),metrics
print('Photo/footer color continuity passed',flush=True)
