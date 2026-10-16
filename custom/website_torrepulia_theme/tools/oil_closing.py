"""Copy the owner's Radici closing to the oil page, without duplicating its CTA."""
import json
import sys
from local_qa import shell

SOURCE='''
import copy,json
from datetime import datetime
from lxml import etree
module='website_torrepulia_theme'
view=env.ref(module+'.page_oil_view').with_context(lang='en_US')
about=env.ref(module+'.page_story_view').with_context(lang='en_US')
about_before=about.arch_db
root=etree.fromstring(view.arch_db.encode())
wrap=root.xpath('.//div[@id="wrap"]')[0]
key='s_torrepulia_roots_cta'
closing=etree.fromstring(about_before.encode()).xpath('.//section[@data-snippet="'+key+'"]')
assert len(closing)==1
print(json.dumps({'sections':[n.get('data-snippet') for n in wrap],'copy':''.join(closing[0].itertext())}))
if __APPLY__:
    matches=[n for n in wrap if n.get('data-snippet') in ['s_torrepulia_cta',key]]
    assert len(matches)==1 and matches[0]==wrap[-1]
    assert wrap[-2].get('data-snippet')=='s_torrepulia_packaging'
    preserved=[etree.tostring(n) for n in list(wrap)[:-1]]
    backup=view.copy({'name':'Oil before matching Radici closing','active':False,'arch_fs':False,
        'key':module+'.oil_before_closing_'+datetime.now().strftime('%Y%m%d_%H%M%S')})
    wrap.replace(matches[0],copy.deepcopy(closing[0]))
    view.write({'arch_db':etree.tostring(root,encoding='unicode'),'arch_fs':False})
    saved=etree.fromstring(view.arch_db.encode()).xpath('.//div[@id="wrap"]')[0]
    assert preserved==[etree.tostring(n) for n in list(saved)[:-1]]
    assert etree.tostring(saved[-1])==etree.tostring(closing[0])
    assert about.arch_db==about_before
    env.cr.commit()
    print(json.dumps({'backup':backup.key,'copied_from_family':True,'other_sections_unchanged':True}))
'''

if __name__=='__main__':
    print(shell(SOURCE.replace('__APPLY__',repr('--apply' in sys.argv)),database='torrepulia_cinematic_install'))
    if '--verify' in sys.argv:
        from playwright.sync_api import sync_playwright
        results=[]
        with sync_playwright() as p:
            browser=p.chromium.launch()
            context=browser.new_context(reduced_motion='reduce')
            context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install',timeout=90000)
            page=context.new_page()
            for width in [1440,390]:
                page.set_viewport_size({'width':width,'height':900})
                page.goto('http://127.0.0.1:8069/l-olio',wait_until='networkidle',timeout=90000)
                page.locator('.tp-roots-cta').scroll_into_view_if_needed()
                result=page.evaluate('''() => {
                    const c=document.querySelector('.tp-roots-cta'),f=document.querySelector('#mc-footer');
                    return {width:innerWidth,count:document.querySelectorAll('.tp-roots-cta').length,
                        previous:c.previousElementSibling.dataset.snippet,background:getComputedStyle(c).backgroundColor,
                        footer:getComputedStyle(f).backgroundColor,title:c.querySelector('h2').textContent,
                        href:c.querySelector('a').getAttribute('href'),overflow:document.documentElement.scrollWidth-innerWidth};
                }''')
                assert result['count']==1 and result['previous']=='s_torrepulia_packaging',result
                assert result['background']==result['footer']=='rgb(24, 35, 31)',result
                assert result['title']=='Il prossimo assaggio comincia qui.' and result['href']=='/shop' and result['overflow']<=1,result
                results.append(result)
            browser.close()
        print(json.dumps({'verified':results}),flush=True)
