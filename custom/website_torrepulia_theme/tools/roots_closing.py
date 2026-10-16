"""Explicit local publication of the three closing Radici snippets, with backup."""
import json
import sys
from pathlib import Path
from local_qa import shell

SOURCE = '''
import copy,json
from datetime import datetime
from lxml import etree
module='website_torrepulia_theme'
names=['s_torrepulia_roots_transition','s_torrepulia_roots_values','s_torrepulia_roots_cta']
view=env.ref(module+'.page_story_view').with_context(lang='en_US')
root=etree.fromstring(view.arch_db.encode())
wrap=root.xpath('.//div[@id="wrap"]')[0]
report={'page':view.id,'sections':[node.get('data-snippet') for node in wrap if node.tag=='section']}
if __APPLY__:
    opening=[node for node in wrap if node.get('data-snippet') in ['s_torrepulia_story_opening','s_torrepulia_story_chapters']]
    assert len(opening)==2, 'Expected the two approved opening snippets'
    before=[etree.tostring(node) for node in opening]
    home=env.ref(module+'.page_home_view').with_context(lang='en_US')
    home_before=home.arch_db
    previous=[node for node in wrap if node.get('data-snippet') in ['s_torrepulia_editorial','s_torrepulia_cta']+names]
    assert len(previous) in [2,3] and len(wrap)==len(opening)+len(previous), 'Inspect unexpected page sections first'
    polish=__POLISH__
    copy_xpath='.//h1|.//h2|.//h3|.//figcaption|.//p[not(contains(@class,"tp-roots-values-subtitle"))]'
    copy_before=[''.join(node.itertext()) for node in root.xpath(copy_xpath)]
    backup=view.copy({'name':'Radici before closing redesign','active':False,'arch_fs':False,
        'key':module+'.roots_before_closing_'+datetime.now().strftime('%Y%m%d_%H%M%S')})
    document=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/s_roots_closing.xml')
    sections=[]
    for name in names:
        template=document.xpath('/odoo/template[@id="'+name+'"]')[0]
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
        if polish:
            matches=[node for node in previous if node.get('data-snippet')==name]
            assert len(matches)==1, 'Polish requires the three existing closing sections'
            section=copy.deepcopy(matches[0])
            def classes(node,add=(),remove=()):
                tokens=[token for token in node.get('class','').split() if token not in remove]
                node.set('class',' '.join(dict.fromkeys(tokens+list(add))))
            if name==names[0]:
                row=section.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," row ")]')[0]
                image_col=next(node for node in row if node.xpath('.//img'))
                text_col=next(node for node in row if node.xpath('.//p[contains(@class,"lead")]'))
                heading=section.find('.//h2')
                heading.getparent().remove(heading)
                heading_col=etree.Element('div',{'class':'col-12 col-md-6 order-2 order-md-3 o_colored_level'})
                classes(heading,remove=['mt-4'])
                heading_col.append(heading)
                classes(row,add=['gx-5','gy-4','align-items-center'],remove=['g-5'])
                classes(image_col,add=['order-1'],remove=['order-2','order-3','order-md-2','order-md-3'])
                classes(text_col,add=['order-3','order-md-2'],remove=['order-1','order-2','order-md-3'])
                padding=text_col.xpath('.//div')[0]
                classes(padding,add=['p-md-4','pe-2','pe-md-5','tp-roots-transition-copy'])
                for node in list(row):row.remove(node)
                row.extend([image_col,heading_col,text_col])
            elif name==names[1]:
                heading=section.find('.//h2')
                classes(heading,add=['mb-3'],remove=['mb-5'])
                if not section.xpath('.//p[contains(@class,"tp-roots-values-subtitle")]'):
                    subtitle=copy.deepcopy(template.xpath('.//p[contains(@class,"tp-roots-values-subtitle")]')[0])
                    heading.addnext(subtitle)
                for numeral in section.xpath('.//p[contains(@class,"tp-roots-numeral")]'):
                    classes(numeral,add=['h5'])
                for paragraph in section.xpath('.//div[contains(@class,"col-md-4")]/p[not(@aria-hidden)]'):
                    classes(paragraph,add=['text-dark','tp-roots-description'],remove=['text-muted'])
        sections.append(section)
    index=wrap.index(previous[0])
    for node in previous:wrap.remove(node)
    for offset,section in enumerate(sections):wrap.insert(index+offset,section)
    view.write({'arch_db':etree.tostring(root,encoding='unicode'),'arch_fs':False})
    current=etree.fromstring(view.arch_db.encode()).xpath('.//div[@id="wrap"]')[0]
    assert [etree.tostring(node) for node in current[:2]]==before, 'Opening must remain byte-for-byte unchanged'
    assert home.arch_db==home_before, 'Homepage must remain unchanged'
    if polish:
        assert [''.join(node.itertext()) for node in etree.fromstring(view.arch_db.encode()).xpath(copy_xpath)]==copy_before, 'Existing copy must remain unchanged'
    # Append only the new palette entries; keep any existing builder customizations.
    palette=env.ref(module+'.snippets').with_context(lang='en_US')
    arch=etree.fromstring(palette.arch_db.encode())
    target=next(node for node in arch.iter('xpath') if 'website.s_banner' in node.get('expr',''))
    source=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/snippets.xml')
    for name in names:
        key=module+'.'+name
        if not arch.xpath('.//t[@t-snippet="'+key+'"]'):
            target.append(copy.deepcopy(source.xpath('//t[@t-snippet="'+key+'"]')[0]))
    if not arch.text:arch.text='\\n'
    palette.write({'arch_db':etree.tostring(arch,encoding='unicode'),'arch_fs':False})
    env['ir.attachment'].search([('url','=like','/web/assets/%'),('mimetype','=','text/css')]).unlink()
    env.cr.commit()
    report.update({'backup':backup.key,'openingUnchanged':True,'homeUnchanged':True,
        'sections':[node.get('data-snippet') for node in current]})
print(json.dumps(report))
'''
polish='--polish' in sys.argv
apply='--apply' in sys.argv or polish
result=json.loads(shell(SOURCE.replace('__APPLY__',str(apply)).replace('__POLISH__',str(polish)),database='torrepulia_cinematic_install'))
print(json.dumps(result,indent=2))
if apply:
    output=Path(__file__).resolve().parents[1]/'docs/qa-about'
    output.mkdir(exist_ok=True)
    (output/'closing-publication.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
