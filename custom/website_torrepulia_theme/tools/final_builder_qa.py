"""Exercise native editing on a private home or --about page copy."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote
from playwright.sync_api import sync_playwright
from local_qa import shell

ROOT = Path(__file__).resolve().parents[1]
REGINA = '--regina' in sys.argv
ROOTS = '--roots' in sys.argv
PRODUCTION = '--oil-production' in sys.argv
OIL = '--oil' in sys.argv or PRODUCTION
ABOUT = '--about' in sys.argv or ROOTS
SOURCE_VIEW = 'website_torrepulia_theme.page_story_view' if ABOUT else 'website_torrepulia_theme.page_home_view'
if OIL:
    SOURCE_VIEW = 'website_torrepulia_theme.page_oil_view'
OUT = ROOT / 'docs' / ('qa-about' if ABOUT else 'qa-final')
OUT.mkdir(exist_ok=True)
account = json.loads(shell('''
import copy, json, secrets
from lxml import etree
suffix = secrets.token_hex(5)
password = secrets.token_urlsafe(30)
user = env['res.users'].with_context(no_reset_password=True, mail_create_nosubscribe=True).create({
 'name':'Temporary final builder verification', 'login':'final-builder-'+suffix+'@local.invalid', 'password':password,
 'group_ids':[(6,0,[env.ref('base.group_user').id,env.ref('website.group_website_designer').id])]})
home = env.ref(%r).with_context(lang='en_US')
view = home.copy({'key':'torrepulia.final_qa_'+suffix,'name':'Disposable final homepage QA','arch_fs':False})
root = etree.fromstring(view.arch_db.encode())
root.set('t-name',view.key)
view.arch_db = etree.tostring(root,encoding='unicode')
page = env['website.page'].create({'view_id':view.id,'website_id':home.website_id.id,
 'url':'/torrepulia-final-qa-'+suffix,'is_published':False,'website_indexed':False})
env.cr.commit()
print(json.dumps({'id':user.id,'login':user.login,'password':password,'page':page.id,'view':view.id,'url':page.url,'home':home.arch_db}))
''' % SOURCE_VIEW, database='torrepulia_cinematic_install'))
report = {}
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(viewport={'width':1500,'height':1000},reduced_motion='reduce')
        response=context.request.post('http://127.0.0.1:8069/web/session/authenticate', data={'jsonrpc':'2.0','method':'call',
            'params':{'db':'torrepulia_cinematic_install','login':account['login'],'password':account['password']}})
        if response.json().get('error'):
            raise RuntimeError('Temporary designer authentication failed')
        page=context.new_page(); errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8069/odoo/action-website.website_preview?path='+quote(account['url'],safe=''),wait_until='domcontentloaded',timeout=90000)
        page.get_by_role('button',name=re.compile(r'^(Edit|Modifica)$')).wait_for(timeout=60000)
        page.get_by_role('button',name=re.compile(r'^(Edit|Modifica)$')).click()
        save=page.get_by_role('button',name=re.compile(r'^(Save|Salva)$'))
        save.wait_for(timeout=60000);page.wait_for_timeout(5000)
        frame=next(frame for frame in page.frames if frame.locator('#wrap.mc-page,#wrap.tp-page').count())
        report.update(frame.evaluate('''() => ({savable:document.querySelector('#wrap').classList.contains('o_savable'),
            editable:document.querySelector('#wrap').getAttribute('contenteditable'),
            disabledSnippetGroups:document.querySelectorAll('.o_snippet_undroppable').length})'''))
        photo=frame.locator('.tp-production-cards .tp-phase-media img' if PRODUCTION else '.tp-oil-photo' if OIL else '.tp-roots-transition img' if ROOTS else '.tp-about-photo img' if ABOUT else '#peranzana .peranzana-image > img').first
        photo.scroll_into_view_if_needed();photo.dblclick()
        media_heading=page.get_by_role('heading',name=re.compile(r'Select a media|Seleziona.*media'))
        media_heading.wait_for(state='visible',timeout=60000)
        report['mediaDialogOpened']=True
        cancel=page.get_by_role('button',name=re.compile(r'^(Cancel|Annulla|Close|Chiudi)$'))
        if cancel.count():cancel.last.click()
        else:page.keyboard.press('Escape')
        media_heading.wait_for(state='hidden',timeout=30000)
        paragraph=frame.locator('.tp-production-cards p.small' if PRODUCTION else '.tp-oil-opening .lead' if OIL else '.tp-roots-transition .lead' if ROOTS else '.tp-about-subtitle' if ABOUT else '#regina .regina-copy > p').first
        paragraph.click();page.keyboard.press('End');page.keyboard.type(' [QA finale]')
        if REGINA:
            target_url=frame.locator('.mc-catalog [data-summary] a').last.get_attribute('href')
            link=frame.locator('#regina .mc-regina-cta a')
            link.scroll_into_view_if_needed()
            report['reginaEditable']=link.evaluate('el=>el.isContentEditable && !el.closest(".o_not_editable")')
            link.click()
            page.wait_for_timeout(500)
            popover=page.locator('.o-we-linkpopover')
            if not popover.count():popover=frame.locator('.o-we-linkpopover')
            popover.wait_for(state='visible',timeout=15000)
            edit=popover.locator('.o_we_edit_link')
            if edit.is_visible():edit.click()
            popover.locator('#o_we_label_link').fill('Scegli il mio formato')
            popover.locator('#o_linkpopover_url').fill(target_url)
            popover.locator('.o_we_apply_link').click()
            paragraph.click()
        save.click();save.wait_for(state='hidden',timeout=60000)
        report['errors']=errors
        screenshot_root=Path(os.environ.get('TORREPULIA_QA_IMAGES',OUT))
        screenshot_root.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(screenshot_root/('builder-regina.png' if REGINA else 'builder-oil-production.png' if PRODUCTION else 'builder-oil.png' if OIL else 'builder-roots.png' if ROOTS else 'builder-about.png' if ABOUT else 'builder-final.png')))
        browser.close()
    saved=json.loads(shell('''
import json
from lxml import etree
view=env['ir.ui.view'].browse(%s).with_context(lang='en_US')
root=etree.fromstring(view.arch_db.encode())
print(json.dumps({'textSaved':'[QA finale]' in view.arch_db,
 'reginaHref':root.xpath('.//div[@class="mc-regina-cta"]/a/@href'),
 'reginaLabel':[''.join(n.itertext()) for n in root.xpath('.//div[@class="mc-regina-cta"]/a')],
 'dynamicPricesNotPersisted':not bool(root.xpath('.//div[contains(@class,"mc-catalog")]//*[@data-product or @data-summary]')),
 'sensoryPanelsHidden':len(root.xpath('.//div[@class="mc-sensory-panel"][@hidden]')),
 'editorialRuntimeNotPersisted':not bool(root.xpath('.//*[contains(@class,"has-editorial-reveal") or contains(@class,"is-editorial-visible")]')),
 'homeUnchanged':env.ref(%r).with_context(lang='en_US').arch_db==%r}))
''' % (account['view'], SOURCE_VIEW, account['home']),database='torrepulia_cinematic_install'))
    report.update(saved)
finally:
    shell('''
page=env['website.page'].browse(%s).exists()
view=env['ir.ui.view'].browse(%s).exists()
if page:page.unlink()
if view.exists():view.unlink()
env['res.users'].browse(%s).active=False
env.cr.commit()
''' % (account['page'],account['view'],account['id']),database='torrepulia_cinematic_install')
    (OUT/('builder-regina-results.json' if REGINA else 'builder-oil-production-results.json' if PRODUCTION else 'builder-oil-results.json' if OIL else 'builder-roots-results.json' if ROOTS else 'builder-final-results.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
assert not report['errors'], report['errors']
assert report['disabledSnippetGroups'] == 0, report
assert report['editable'] == 'true', report
assert report['sensoryPanelsHidden'] == (0 if ABOUT or OIL else 2), report
assert all(report[key] for key in ['savable','mediaDialogOpened','textSaved','dynamicPricesNotPersisted','homeUnchanged']), report
assert report['editorialRuntimeNotPersisted'], report
if REGINA:
    assert report['reginaEditable'] and report['reginaHref']==[target_url] and report['reginaLabel']==['Scegli il mio formato'],report
