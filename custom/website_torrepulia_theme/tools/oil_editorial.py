"""Inspect or publish only the first two oil sections; preserve later owner edits."""
import sys
from local_qa import shell

SOURCE = '''
import copy,json
from datetime import datetime
from lxml import etree
module='website_torrepulia_theme'
page=env['website.page'].search([('url','=','/l-olio')])
assert len(page)==1
view=page.view_id.with_context(lang='en_US')
root=etree.fromstring(view.arch_db.encode())
wrap=root.xpath('.//div[@id="wrap"]')[0]
print(json.dumps({'view':view.id,'sections':[(n.tag,n.get('data-snippet'),n.get('id')) for n in wrap],
    'opening_copy':[''.join(n.itertext()) for section in list(wrap)[:2] for n in section.xpath('.//h1|.//h2|.//h3|.//p')],
    'photo':wrap[0].xpath('.//img[contains(@class,"tp-oil-photo")]/@src')}))
if __APPLY__:
    assert wrap[0].get('data-snippet')=='s_torrepulia_cultivar_opening'
    assert wrap[1].get('data-name') in ['Le origini della cultivar','Origini della Peranzana']
    tail=[etree.tostring(n) for n in list(wrap)[2:]]
    copy_xpath='.//h1|.//h2|.//h3|.//p'
    copy_before=[''.join(n.itertext()) for s in list(wrap)[:2] for n in s.xpath(copy_xpath)]
    other=[env.ref(module+'.'+key).with_context(lang='en_US').arch_db for key in ['page_home_view','page_story_view']]
    backup=view.copy({'name':'Oil before editorial opening','active':False,'arch_fs':False,
        'key':module+'.oil_before_editorial_'+datetime.now().strftime('%Y%m%d_%H%M%S')})
    doc=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/s_cultivar_editorial.xml')
    for index,template in enumerate(doc.getroot()):
        name=template.get('id')
        section=copy.deepcopy(template.find('section'))
        fragment=etree.Element('t',{'t-name':module+'.'+name})
        fragment.text='\\n'
        fragment.append(copy.deepcopy(section))
        values={'name':template.get('name'),'type':'qweb','key':module+'.'+name,
            'arch_db':etree.tostring(fragment,encoding='unicode'),'arch_fs':False}
        snippet=env.ref(module+'.'+name,raise_if_not_found=False)
        if snippet:snippet.with_context(lang='en_US').write(values)
        else:
            snippet=env['ir.ui.view'].with_context(lang='en_US').create(values)
            env['ir.model.data'].create({'module':module,'name':name,'model':'ir.ui.view','res_id':snippet.id,'noupdate':False})
        if __RESTYLE__:
            previous=wrap[index]
            old=previous.xpath(copy_xpath)
            new=section.xpath(copy_xpath)
            assert len(old)==len(new), 'Inspect changed owner content before restyling'
            for original,target in zip(old,new):
                replacement=copy.deepcopy(original)
                replacement.set('class',target.get('class',''))
                target.getparent().replace(target,replacement)
            if index==0:
                original=previous.xpath('.//img[contains(@class,"tp-oil-photo")]')[0]
                target=section.xpath('.//img[contains(@class,"tp-oil-photo")]')[0]
                replacement=copy.deepcopy(original)
                replacement.set('sizes',target.get('sizes'))
                target.getparent().replace(target,replacement)
        wrap.replace(wrap[index],section)
    assert root.xpath('.//*[@id="processo"]'), 'Existing production anchor required'
    view.write({'arch_db':etree.tostring(root,encoding='unicode'),'arch_fs':False})
    assert tail==[etree.tostring(n) for n in list(etree.fromstring(view.arch_db.encode()).xpath('.//div[@id="wrap"]')[0])[2:]]
    if __RESTYLE__:
        saved=etree.fromstring(view.arch_db.encode()).xpath('.//div[@id="wrap"]')[0]
        assert copy_before==[''.join(n.itertext()) for s in list(saved)[:2] for n in s.xpath(copy_xpath)]
    assert other==[env.ref(module+'.'+key).with_context(lang='en_US').arch_db for key in ['page_home_view','page_story_view']]
    palette=env.ref(module+'.snippets').with_context(lang='en_US')
    arch=etree.fromstring(palette.arch_db.encode())
    key=module+'.s_torrepulia_cultivar_history'
    if not arch.xpath('.//t[@t-snippet="'+key+'"]'):
        target=next(n for n in arch.iter('xpath') if 'website.s_banner' in n.get('expr',''))
        source=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/snippets.xml')
        target.append(copy.deepcopy(source.xpath('//t[@t-snippet="'+key+'"]')[0]))
        palette.write({'arch_db':etree.tostring(arch,encoding='unicode'),'arch_fs':False})
    env['ir.attachment'].search([('url','=like','/web/assets/%'),('mimetype','=','text/css')]).unlink()
    env.cr.commit()
    print(json.dumps({'backup':backup.key,'published':view.id,'later_sections_unchanged':True}))
'''

if __name__=='__main__':
    source=SOURCE.replace('__APPLY__',repr('--apply' in sys.argv or '--restyle' in sys.argv))
    print(shell(source.replace('__RESTYLE__',repr('--restyle' in sys.argv)),database='torrepulia_cinematic_install'))
