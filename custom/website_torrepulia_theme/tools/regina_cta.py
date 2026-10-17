"""Make the saved Regina CTA a native editable link; leave product images dynamic."""
import sys
from local_qa import shell

SOURCE='''
import json
from datetime import datetime
from lxml import etree
module='website_torrepulia_theme'
website=env['website'].search([('torrepulia_theme_enabled','=',True)])
products=website._cinematic_products()
print(json.dumps({'products':[{'id':p.id,'format':p.torrepulia_format_name,'url':p.website_url,
    'image_from_product':bool(p.image_1920),'provisional_composition':p.torrepulia_composite} for p in products]}))
if __APPLY__:
    for key in ['page_home_view','s_cinematic_1']:
        view=env.ref(module+'.'+key).with_context(lang='en_US')
        root=etree.fromstring(view.arch_db.encode())
        matches=root.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," mc-promoted ")]')
        if not matches:
            assert root.xpath('.//div[contains(@class,"mc-regina-cta")]')
            continue
        assert len(matches)==1
        view.copy({'name':'Before native editable Regina CTA','active':False,'arch_fs':False,
            'key':module+'.before_editable_cta_'+key+'_'+datetime.now().strftime('%Y%m%d_%H%M%S')})
        holder=matches[0]
        holder.set('class','mc-regina-cta')
        link=holder.find('a')
        assert link is not None
        link.set('class','btn btn-primary button dark')
        view.write({'arch_db':etree.tostring(root,encoding='unicode'),'arch_fs':False})
    env['ir.attachment'].search([('url','=like','/web/assets/%'),('mimetype','in',['text/css','application/javascript'])]).unlink()
    env.cr.commit()
    print('Native editable Regina CTA published; product image fields unchanged')
'''
if __name__=='__main__':
    print(shell(SOURCE.replace('__APPLY__',repr('--apply' in sys.argv)),database='torrepulia_cinematic_install'))
    if '--verify' in sys.argv:
        import json
        from pathlib import Path
        from playwright.sync_api import sync_playwright
        results=[]
        with sync_playwright() as p:
            browser=p.chromium.launch()
            context=browser.new_context(reduced_motion='reduce')
            context.request.get('http://127.0.0.1:8069/web/login?db=torrepulia_cinematic_install')
            page=context.new_page()
            for width in [1440,390]:
                page.set_viewport_size({'width':width,'height':900})
                page.goto('http://127.0.0.1:8069/',wait_until='networkidle',timeout=90000)
                page.locator('.mc-catalog .format-option').first.wait_for()
                result=page.evaluate('''() => {
                    const link=document.querySelector('#regina .mc-regina-cta a');
                    const images=[...document.querySelectorAll('.mc-catalog [data-preview] img,.mc-catalog .format-thumb img')];
                    return {width:innerWidth,href:link.getAttribute('href'),label:link.textContent,
                        editableWrapper:!link.closest('.o_not_editable,.mc-promoted'),
                        productImages:images.map(el=>el.getAttribute('src')),
                        fromProducts:images.length>0&&images.every(el=>/^\\/web\\/image\\/product.template\\/\\d+\\/image_/.test(el.getAttribute('src'))),
                        overflow:document.documentElement.scrollWidth-innerWidth};
                }''')
                assert result['editableWrapper'] and result['fromProducts'] and result['overflow']<=1,result
                results.append(result)
            browser.close()
        report=Path(__file__).resolve().parents[1]/'docs/qa-final/regina-cta-results.json'
        report.write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(json.dumps(results),flush=True)
