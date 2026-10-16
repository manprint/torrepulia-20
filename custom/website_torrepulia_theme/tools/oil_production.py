"""Inspect or publish production and pairings without replacing other oil sections."""
import sys
from local_qa import shell

SOURCE='''
import copy,json
from datetime import datetime
from lxml import etree
module='website_torrepulia_theme'
view=env.ref(module+'.page_oil_view').with_context(lang='en_US')
root=etree.fromstring(view.arch_db.encode())
wrap=root.xpath('.//div[@id="wrap"]')[0]
names=['s_torrepulia_production_process','s_torrepulia_pairings']
polish=__POLISH__
if polish:names.append('s_torrepulia_sensory')
print(json.dumps({'sections':[(n.get('data-snippet'),''.join(n.itertext())) for n in wrap if n.get('data-snippet') in names]}))
if __APPLY__:
    preserved=[etree.tostring(n) for n in wrap if n.get('data-snippet') not in names]
    backup=view.copy({'name':'Oil before production cards','active':False,'arch_fs':False,
        'key':module+'.oil_before_production_'+datetime.now().strftime('%Y%m%d_%H%M%S')})
    doc=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/s_production_process.xml')
    templates=list(doc.getroot())
    if polish:
        sensory=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/s_phase_two.xml')
        templates.append(sensory.xpath('/odoo/template[@id="s_torrepulia_sensory"]')[0])
    for template in templates:
        name=template.get('id')
        assert name in names
        matches=[n for n in wrap if n.get('data-snippet')==name]
        assert len(matches)==1
        section=copy.deepcopy(template.find('section'))
        if polish:
            desired=section
            section=copy.deepcopy(matches[0])
            if name==names[0]:
                headings=section.xpath('.//article/h3')
                assert len(headings)==4
                headings[-1].text='Confezionamento Accurato'
            elif name==names[1]:
                heading=section.find('.//h2')
                heading.set('class',desired.find('.//h2').get('class'))
                cta=section.xpath('.//a[@href="/shop"]')[0]
                wanted=desired.xpath('.//a[@href="/shop"]')[0]
                cta.set('class',wanted.get('class'))
                cta.getparent().set('class',wanted.getparent().get('class'))
            else:
                old=section.xpath('.//dl/dd')
                wanted=desired.xpath('.//dl/dd')
                assert len(old)==len(wanted)==3
                assert 'carciofo' in ''.join(old[1].itertext()) and 'mandorla' in ''.join(old[2].itertext()), 'Review owner sensory copy before replacing'
                for index in [1,2]:old[index].getparent().replace(old[index],copy.deepcopy(wanted[index]))
        # Keep the owner's existing pairing descriptions, changing only their layout.
        if name==names[1]:
            old=matches[0].xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," col-md-6 ")]/p')
            new=section.xpath('.//div[contains(concat(" ",normalize-space(@class)," ")," col-md-6 ")]/p')
            assert len(old)==len(new)==2
            for a,b in zip(old,new):b.getparent().replace(b,copy.deepcopy(a))
        wrap.replace(matches[0],section)
        fragment=etree.Element('t',{'t-name':module+'.'+name})
        fragment.text='\\n'
        fragment.append(copy.deepcopy(template.find('section')))
        env.ref(module+'.'+name).with_context(lang='en_US').write({'arch_db':etree.tostring(fragment,encoding='unicode'),'arch_fs':False})
    view.write({'arch_db':etree.tostring(root,encoding='unicode'),'arch_fs':False})
    current=etree.fromstring(view.arch_db.encode()).xpath('.//div[@id="wrap"]')[0]
    assert preserved==[etree.tostring(n) for n in current if n.get('data-snippet') not in names]
    env['ir.attachment'].search([('url','=like','/web/assets/%'),('mimetype','=','text/css')]).unlink()
    env.cr.commit()
    print(json.dumps({'backup':backup.key,'other_sections_unchanged':True}))
'''
if __name__=='__main__':
    source=SOURCE.replace('__APPLY__',repr('--apply' in sys.argv or '--polish' in sys.argv))
    print(shell(source.replace('__POLISH__',repr('--polish' in sys.argv)),database='torrepulia_cinematic_install'))
