import copy

from lxml import etree

from odoo import api, models
from odoo.tools.translate import StoredTranslations
from odoo.addons.website_torrepulia_theme.controllers.reservation import QUANTITIES


LEGACY = {'s_torrepulia_reservation_hero', 's_torrepulia_reservation_conditions',
          's_torrepulia_reservation_form'}
SNIPPET = 's_torrepulia_request_campaign'


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
            if not section.xpath('.//*[@data-review-lazy]'):
                target = snippet.xpath('.//*[@data-review-lazy]')[0]
                section.append(copy.deepcopy(target))
                changed = True
        if not legacy:
            if changed:
                return etree.tostring(root, encoding='unicode')
            return arch
    if not existing:
        first = legacy[0] if legacy else None
        replacement = copy.deepcopy(snippet)
        replacement.set('data-visual-bullets', '1')
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
                if after != before:
                    backup = dict(website.torrepulia_campaign_page_backup or {})
                    backup.setdefault(str(view.id), {'key': view.key, 'translations': before})
                    website.torrepulia_campaign_page_backup = backup
                    view.write({'arch_db': StoredTranslations(after), 'arch_fs': False, 'arch_updated': True})
