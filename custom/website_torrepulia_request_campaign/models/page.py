import copy
import re

from lxml import etree

from odoo import api, models
from odoo.http import Response
from odoo.tools.translate import StoredTranslations
from odoo.addons.website_torrepulia_theme.controllers.reservation import QUANTITIES
from ..controllers.campaign import campaign_content


LEGACY = {'s_torrepulia_reservation_hero', 's_torrepulia_reservation_conditions',
          's_torrepulia_reservation_form'}
SNIPPET = 's_torrepulia_request_campaign'
OLD_INTRODUCTION = 'La produzione della nuova campagna olearia 2026/2027 è limitata. Seleziona le confezioni per la tua tavola:'
OLD_HERO_INTRO = 'Prenota oggi senza alcun anticipo la tua quota di La Regina: lo moliamo e lo spediamo entro 48 ore.'
# Any size of the theme's default campaign photo; a photo chosen in the Builder stays.
DEFAULT_PHOTO = '/website_torrepulia_theme/static/src/cinematic/campaign/land-'
NEW_OIL_PATH = '/olio-nuovo'
# 20.0.1.15.0: the new oil leaving the separator opens the page, in place of any photo of the theme.
THEME_STATIC = '/website_torrepulia_theme/static/'
# The holder of the formats as the snippet saves it: one loading paragraph.
FAQ_PLACEHOLDER = re.compile(r'(<div[^>]*\bdata-campaign-faq\b[^>]*>)\s*(</div>)')
CONTENT_PLACEHOLDER = re.compile(r'(<div[^>]*class="[^"]*\btp-campaign-content\b[^"]*"[^>]*>)\s*<p>[^<]*</p>\s*(</div>)')


def refresh_opening(section, snippet):
    """Opening of 20.0.1.8.0: new intro and action; the photo changes only if it is still the default."""
    fresh = snippet.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " tp-campaign-hero ")]')
    if not fresh or not fresh[0].xpath('.//p[contains(@class, "tp-campaign-intro")]'):
        return
    fresh = fresh[0]
    for paragraph in section.xpath('.//p[contains(concat(" ", normalize-space(@class), " "), " tp-campaign-intro ")]'):
        if ''.join(paragraph.itertext()).strip() == OLD_HERO_INTRO:
            new = copy.deepcopy(fresh.xpath('.//p[contains(@class, "tp-campaign-intro")]')[0])
            new.tail = paragraph.tail
            paragraph.getparent().replace(paragraph, new)
            paragraph = new
        if not section.xpath('.//*[contains(@class, "tp-campaign-hero-cta")]'):
            cta = copy.deepcopy(fresh.xpath('.//a[contains(@class, "tp-campaign-hero-cta")]')[0])
            cta.tail, paragraph.tail = paragraph.tail, None
            paragraph.addnext(cta)
    for photo in section.xpath('.//img[contains(@class, "tp-campaign-photo")]'):
        if (photo.get('src') or '').startswith(DEFAULT_PHOTO):
            new = copy.deepcopy(fresh.xpath('.//img[contains(@class, "tp-campaign-photo")]')[0])
            new.tail = photo.tail
            photo.getparent().replace(photo, new)


def harvest_clip(arch, snippet):
    """The opening photo becomes the new oil clip, unless the owner uploaded their own photo."""
    root = etree.fromstring(arch.encode())
    fresh = snippet.xpath('.//img[contains(concat(" ", @class, " "), " tp-campaign-photo ")]')[0]
    changed = False
    for photo in root.xpath('.//section[@data-snippet="%s"]//img[contains(concat(" ", @class, " "), " tp-campaign-photo ")]' % SNIPPET):
        source = photo.get('src') or ''
        if source == fresh.get('src') or not source.startswith(THEME_STATIC):
            continue
        new = copy.deepcopy(fresh)
        new.tail = photo.tail
        photo.getparent().replace(photo, new)
        changed = True
    return etree.tostring(root, encoding='unicode') if changed else arch


def replace_legacy(arch, snippet):
    """Replace only recognised seasonal blocks; retain other Builder content."""
    root = etree.fromstring(arch.encode())
    wraps = root.xpath('.//div[@id="wrap"]')
    if len(wraps) != 1:
        raise ValueError('Pagina stagionale: struttura wrap ambigua; nessuna modifica applicata.')
    wrap = wraps[0]
    existing = wrap.xpath('.//section[@data-snippet="%s"]' % SNIPPET)
    legacy = wrap.xpath('.//section[@data-snippet]')
    legacy = [node for node in legacy if node.get('data-snippet') in LEGACY]
    # Recognise materialised forms even when old Builder renamed the snippet.
    for form in wrap.xpath('.//form'):
        fields = form.xpath('.//*[@name]')
        if not any(node.get('name') in ('torrepulia_reservation', *QUANTITIES)
                   or node.get('name') == 'name' and node.get('value', '').startswith('Prenotazione olio nuovo')
                   for node in fields):
            continue
        # Unknown/renamed Builder sections may contain compatible editorial
        # content. Remove only their legacy form, not the surrounding section.
        if not any(parent in legacy for parent in form.iterancestors()):
            legacy.append(form)
    if existing:
        changed = False
        for section in existing:
            for node in section.xpath('.//*[@data-campaign-scroll or @data-campaign-review]'):
                node.getparent().remove(node)
                changed = True
            if section.get('data-editorial-layout') != '2':
                section.set('data-editorial-layout', '2')
                section.set('data-columns', '2')
                for paragraph in section.xpath('.//p'):
                    text = ''.join(paragraph.itertext()).strip()
                    if text == 'Nessun pagamento richiesto in questa fase.':
                        paragraph.getparent().remove(paragraph)
                    elif text == 'Scegli i formati e le quantità. Potrai rivedere la tua richiesta e lasciarci i recapiti nel passaggio successivo.':
                        paragraph.text = 'Scegli i formati e le quantità, poi completa i recapiti qui sotto. Potrai rivedere la richiesta prima dell’invio.'
                changed = True
            if section.get('data-visual-bullets') != '1':
                for paragraph in section.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " tp-campaign-hero ")]//p[contains(concat(" ", normalize-space(@class), " "), " tp-campaign-intro ")]'):
                    for child in list(paragraph):
                        paragraph.remove(child)
                    paragraph.text = 'Prenota oggi senza alcun anticipo la tua quota di La Regina: lo moliamo e lo spediamo entro 48 ore.'
                section.set('data-visual-bullets', '1')
                changed = True
            for node in section.xpath('.//*[contains(concat(" ", normalize-space(@class), " "), " tp-campaign-next ")]'):
                node.getparent().remove(node)
                changed = True
            if section.get('data-hero-facts') != '1':
                refresh_opening(section, snippet)
                section.set('data-hero-facts', '1')
                changed = True
            if not section.xpath('.//*[@data-review-lazy]'):
                target = snippet.xpath('.//*[@data-review-lazy]')[0]
                section.append(copy.deepcopy(target))
                changed = True
            # 20.0.1.13.0: the questions move after the form, into their own holder.
            faq_holder = snippet.xpath('.//*[@data-campaign-faq]')
            if faq_holder and not section.xpath('.//*[@data-campaign-faq]'):
                section.append(copy.deepcopy(faq_holder[0]))
                changed = True
        if not legacy:
            if changed:
                return etree.tostring(root, encoding='unicode')
            return arch
    if not existing:
        first = legacy[0] if legacy else None
        replacement = copy.deepcopy(snippet)
        replacement.set('data-visual-bullets', '1')
        # A fresh snippet already carries the current opening.
        replacement.set('data-hero-facts', '1')
        photographs = wrap.xpath('.//section[@data-snippet="s_torrepulia_reservation_hero"]//img[contains(concat(" ", @class, " "), " tp-reservation-hero-image ")]')
        targets = replacement.xpath('.//img')
        if photographs and targets:
            target = targets[0]
            photo = copy.deepcopy(photographs[0])
            photo.set('class', 'img-fluid tp-campaign-photo')
            photo.attrib.pop('id', None)
            target.getparent().replace(target, photo)
        if first is not None:
            first.addprevious(replacement)
        else:
            wrap.append(replacement)
    for node in legacy:
        if (parent := node.getparent()) is not None:
            if node.tail:
                if (previous := node.getprevious()) is not None:
                    previous.tail = (previous.tail or '') + node.tail
                else:
                    parent.text = (parent.text or '') + node.tail
            parent.remove(node)
    return etree.tostring(root, encoding='unicode')


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def _install_request_campaign_pages(self):
        """Idempotent, scoped data migration, called only by module update/install."""
        snippet_view = self.env.ref('website_torrepulia_request_campaign.s_torrepulia_request_campaign')
        snippet = etree.fromstring(snippet_view.with_context(lang='en_US').arch_db.encode()).find('section')
        for website in self.search([('torrepulia_theme_enabled', '=', True)]):
            if not website.torrepulia_campaign_id:
                campaign = self.env['torrepulia.request.campaign'].search([
                    ('website_id', '=', website.id), ('reference', '=', 'nuovo-raccolto')], limit=1)
                if not campaign:
                    campaign = self.env['torrepulia.request.campaign'].create({
                        'name': 'Nuovo raccolto', 'reference': 'nuovo-raccolto', 'website_id': website.id})
                website.torrepulia_campaign_id = campaign
            pages = self.env['website.page'].search([
                ('website_id', '=', website.id), ('url', '=', '/prenotailtuoolio')])
            # Apply the requested seasonal copy once; future editorial changes survive updates.
            backup = dict(website.torrepulia_campaign_page_backup or {})
            if 'visual_bullets_copy_v1' not in backup:
                campaign = website.torrepulia_campaign_id
                backup['visual_bullets_copy_v1'] = {
                    'campaign_id': campaign.id,
                    'introduction': dict(campaign._fields['introduction']._get_stored_translations(campaign) or {}),
                }
                website.torrepulia_campaign_page_backup = backup
                introduction = campaign._fields['introduction'].default(campaign)
                languages = backup['visual_bullets_copy_v1']['introduction'].keys() | {'en_US'}
                campaign.write({'introduction': StoredTranslations({lang: introduction for lang in languages})})
            if 'opening_facts_v2' not in backup:
                campaign = website.torrepulia_campaign_id
                stored = dict(campaign._fields['introduction']._get_stored_translations(campaign) or {})
                backup['opening_facts_v2'] = {'campaign_id': campaign.id, 'introduction': stored}
                website.torrepulia_campaign_page_backup = backup
                if stored and all(value == OLD_INTRODUCTION for value in stored.values()):
                    campaign.write({'introduction': StoredTranslations({
                        lang: campaign._fields['introduction'].default(campaign) for lang in stored})})
            if not pages:
                root = etree.Element('t', {'t-name': 'torrepulia.request.campaign.page.%s' % website.id})
                layout = etree.SubElement(root, 't', {'t-call': 'website.layout'})
                wrap = etree.SubElement(layout, 'div', {'id': 'wrap', 'class': 'oe_structure'})
                wrap.append(copy.deepcopy(snippet))
                view = self.env['ir.ui.view'].create({'name': 'Prenota il tuo olio', 'type': 'qweb',
                    'key': root.get('t-name'), 'website_id': website.id,
                    'arch_db': etree.tostring(root, encoding='unicode')})
                self.env['website.page'].create({'name': 'Prenota il tuo olio', 'url': '/prenotailtuoolio',
                    'website_id': website.id, 'view_id': view.id, 'is_published': True})
            for page in pages:
                view = page.view_id
                before = dict(view._fields['arch_db']._get_stored_translations(view) or {})
                after = {lang: replace_legacy(arch, snippet) for lang, arch in before.items()}
                if 'harvest_clip_v1' not in (website.torrepulia_campaign_page_backup or {}):
                    after = {lang: harvest_clip(arch, snippet) for lang, arch in after.items()}
                if after != before:
                    backup = dict(website.torrepulia_campaign_page_backup or {})
                    backup.setdefault(str(view.id), {'key': view.key, 'translations': before})
                    website.torrepulia_campaign_page_backup = backup
                    view.write({'arch_db': StoredTranslations(after), 'arch_fs': False, 'arch_updated': True})
            backup = dict(website.torrepulia_campaign_page_backup or {})
            if 'harvest_clip_v1' not in backup:
                backup['harvest_clip_v1'] = True
                website.torrepulia_campaign_page_backup = backup
            # The menu says "Olio nuovo": the address people type leads to the campaign page.
            if not self.env['website.rewrite'].search_count([('website_id', '=', website.id), ('url_from', '=', NEW_OIL_PATH)]):
                self.env['website.rewrite'].create({'name': 'Olio nuovo', 'url_from': NEW_OIL_PATH, 'url_to': '/prenotailtuoolio',
                                                    'redirect_type': '301', 'website_id': website.id})


class WebsitePage(models.Model):
    _inherit = 'website.page'

    def _get_response(self, request):
        """Visitors and search engines get the formats in the page, not only after the script.

        The saved page keeps the placeholder (the Builder never stores prices or the campaign
        state) and the cached page too: the formats are rendered here on every visit, then the
        script refreshes them as before. Logged-in users keep the script alone.
        """
        response = super()._get_response(request)
        website = request.env.website
        if (not response or response.status_code != 200 or not website.torrepulia_theme_enabled
                or not request.env.user._is_public() or SNIPPET not in (self.view_id.sudo().arch or '')):
            return response
        if hasattr(response, 'flatten'):
            response.flatten()
        html = response.get_data(as_text=True)
        if not CONTENT_PLACEHOLDER.search(html):
            return response
        content = campaign_content(website)
        html = CONTENT_PLACEHOLDER.sub(lambda match: match.group(1) + content['html'] + match.group(2), html, count=1)
        html = FAQ_PLACEHOLDER.sub(lambda match: match.group(1) + content['faq_html'] + match.group(2), html, count=1)
        # A new response: the one from super() may be the object kept in the page cache.
        headers = response.headers.copy()
        headers.pop('Content-Length', None)
        served = Response(headers=headers, mimetype=response.mimetype, status=response.status, response=[html])
        for name in ('_cached_view_id', '_cached_page'):
            if hasattr(response, name):
                setattr(served, name, getattr(response, name))
        return served
