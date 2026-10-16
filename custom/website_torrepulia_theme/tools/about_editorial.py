"""Inspect or explicitly update only the two opening About Us sections."""
import sys
from local_qa import shell

RESTYLE = '--restyle' in sys.argv
APPLY = '--apply' in sys.argv or RESTYLE
print(shell('''
import copy, json
from datetime import datetime
from lxml import etree
pages=env['website.page'].search([('url','=','/aboutus')])
assert len(pages)==1, 'Choose the About Us website explicitly'
page=pages.with_context(lang='en_US')
view=page.view_id
root=etree.fromstring(view.arch_db.encode())
wrap=root.xpath('.//div[@id="wrap"]')[0]
print(json.dumps({'page':page.id,'view':view.id,'key':view.key,'arch':view.arch_db},ensure_ascii=False))
if %s:
    home=env.ref('website_torrepulia_theme.page_home_view').with_context(lang='en_US')
    home_before=home.arch_db
    originals=[]
    for name in ['s_torrepulia_story_opening','s_torrepulia_story_chapters']:
        nodes=wrap.xpath('./section[@data-snippet=%%r]' %% name)
        assert len(nodes)==1, 'Unexpected About Us composition: '+name
        originals.append(nodes[0])
    remainder=[etree.tostring(node) for node in wrap if node not in originals]
    copy_before=[''.join(node.itertext()) for node in wrap.xpath('.//h1|.//h2|.//h3|.//p|.//figcaption')]
    suffix=datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S')
    backup=view.copy({'name':'About Us before editorial '+suffix,
        'key':'website_torrepulia_theme.about_before_editorial_'+suffix,
        'active':False,'arch_fs':False})
    document=etree.parse('/mnt/torrepulia/custom/website_torrepulia_theme/views/snippets/s_phase_two.xml')
    for previous,name in zip(originals,['s_torrepulia_story_opening','s_torrepulia_story_chapters']):
        template=document.xpath('/odoo/template[@id=%%r]' %% name)[0]
        replacement=copy.deepcopy(template.find('section'))
        if %s:
            replacement=copy.deepcopy(previous)
            if name=='s_torrepulia_story_chapters':
                cards=replacement.xpath('.//div[@class="tp-about-grid"]/article')
                defaults=template.xpath('.//article')
                assert len(cards)==3, 'Three generation articles are required'
                for card,default,year in zip(cards,defaults,['1945','1980','2020']):
                    existing=card.find('span[@class="tp-about-year"]')
                    if existing is None:
                        existing=etree.Element('span',{'class':'tp-about-year','aria-hidden':'true'})
                        card.insert(0,existing)
                    existing.text=year
                    heading=card.find('h3')
                    reference=default.find('h3')
                    if ''.join(heading.itertext())==''.join(reference.itertext()):
                        heading.text=reference.text
                        for child in list(heading):heading.remove(child)
                        for child in reference:heading.append(copy.deepcopy(child))
        wrap.replace(previous,replacement)
        snippet=env.ref('website_torrepulia_theme.'+name).with_context(lang='en_US')
        fragment=etree.Element('t',{'t-name':snippet.key})
        fragment.append(copy.deepcopy(replacement))
        snippet.write({'arch_db':etree.tostring(fragment,encoding='unicode'),'arch_fs':False})
    revised=etree.tostring(root,encoding='unicode')
    view.write({'arch_db':revised,'arch_fs':False})
    assert home.arch_db==home_before, 'The homepage must remain unchanged'
    after=etree.fromstring(view.arch_db.encode()).xpath('.//div[@id="wrap"]')[0]
    preserved=[etree.tostring(node) for node in after if node.get('data-snippet') not in
        ['s_torrepulia_story_opening','s_torrepulia_story_chapters']]
    assert preserved==remainder, 'The remaining About Us sections must remain unchanged'
    if %s:
        assert [''.join(node.itertext()) for node in after.xpath('.//h1|.//h2|.//h3|.//p|.//figcaption')]==copy_before, 'Restyling must preserve saved copy'
    env['ir.attachment'].search([('url','=like','/web/assets/%%'),('mimetype','=','text/css')]).unlink()
    env.cr.commit()
    print(json.dumps({'updated':view.id,'backup':backup.key,'homeUnchanged':True,
        'remainingSectionsUnchanged':True}))
''' % (APPLY, RESTYLE, RESTYLE), database='torrepulia_cinematic_install'))
