"""Public route smoke checks on the owner database or the disposable release install."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--database',choices=['torrepulia_cinematic_install','torrepulia_release_20261017'],default='torrepulia_cinematic_install')
args=parser.parse_args()
report={'database':args.database,'cases':[],'errors':[],'failedResponses':[]}
with sync_playwright() as p:
    browser=p.chromium.launch()
    context=browser.new_context(reduced_motion='reduce')
    context.request.get('http://127.0.0.1:8069/web/login?db='+args.database,timeout=120000)
    page=context.new_page()
    page.on('pageerror',lambda error:report['errors'].append(str(error)))
    page.on('response',lambda response:report['failedResponses'].append({'status':response.status,'url':response.url}) if response.status>=400 else None)
    for width in [1440,390]:
        page.set_viewport_size({'width':width,'height':1000})
        routes=['/aboutus','/l-olio','/shop']
        if args.database=='torrepulia_release_20261017':routes.insert(0,'/')
        for route in routes:
            response=page.goto('http://127.0.0.1:8069'+route,wait_until='networkidle',timeout=120000)
            page.evaluate('document.fonts.ready')
            for image in page.locator('#wrap img[loading="lazy"]').all():
                image.scroll_into_view_if_needed()
                image.evaluate('el=>el.decode().catch(()=>null)')
            result=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth-innerWidth,
                missingImages:[...document.querySelectorAll('#wrap img')].filter(el=>!el.naturalWidth).map(el=>el.src),
                h1:document.querySelectorAll('#wrap h1').length,
                ctaCount:document.querySelectorAll('.tp-roots-cta').length,
                footerColor:getComputedStyle(document.querySelector('#mc-footer')).backgroundColor})''')
            result.update({'route':route,'width':width,'status':response.status})
            assert result['status']==200 and result['overflow']<=1 and not result['missingImages'],result
            if route in ['/aboutus','/l-olio']:
                assert result['h1']==1 and result['ctaCount']==1,result
            assert result['footerColor']=='rgb(24, 35, 31)',result
            report['cases'].append(result)
            print(json.dumps(result),flush=True)
    browser.close()
out=Path(__file__).resolve().parents[1]/'docs/qa-final'
name='clean-install-browser-results.json' if args.database=='torrepulia_release_20261017' else 'release-browser-results.json'
(out/name).write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not report['errors'] and not report['failedResponses'],report
print('Release public routes passed')
