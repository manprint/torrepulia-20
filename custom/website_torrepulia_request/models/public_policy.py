"""Website-only output policy, including materialised Website Builder copies.

Never writes views/content, product prices, quantities or native stock policy.
Portal quotations/payment and backend responses are deliberately outside scope.
"""
import json
import re
from urllib.parse import urlsplit

from lxml import etree, html

from odoo import models
from odoo.http import request
from .commerce import public_storefront


ECONOMIC_KEY = re.compile(r'price|discount|subtotal|amount|total|offers|tracking_info', re.I)
MONEY = re.compile(r'(?:[€£$]\s*\d[\d.,\u00a0 ]*|\d[\d.,\u00a0 ]*\s*(?:€|£|\$|EUR\b|USD\b|euro\b))', re.I)
PRICE_CLASSES = {'product_price', 'oe_price', 'oe_default_price', 'oe_compare_list_price',
                 'o_product_price_unit', 'option-price', 'tp-reservation-price',
                 'variant_price_extra', 'badge_price_extra', 'sign_badge_price_extra',
                 'o_wsale_price_range', 'o_wsale_product_price', 'oe_currency_value'}


def economic_data(value, summary_url, hide_prices=True, host=''):
    if isinstance(value, dict):
        clean = {key: economic_data(item, summary_url, hide_prices, host)
                 for key, item in value.items() if not hide_prices or key in ('show_prices', 'hide_price') or not ECONOMIC_KEY.search(key)}
        if hide_prices and 'hide_price' in value:
            clean['hide_price'] = True
        return clean
    if isinstance(value, list):
        return [economic_data(item, summary_url, hide_prices, host) for item in value]
    if isinstance(value, str) and '<' in value and '>' in value:
        return storefront_html(value, summary_url, hide_prices, host)
    return MONEY.sub('', value) if hide_prices and isinstance(value, str) else value


def storefront_html(source, summary_url, hide_prices, host=''):
    full = bool(re.search(r'<html\b|<!doctype', source, re.I))
    root = html.document_fromstring(source) if full else html.fragment_fromstring(source, create_parent='div')
    body = root.find('body') if full else None
    if body is not None:
        body.set('data-tp-request-mode', '1')
        body.set('data-tp-request-prices', '1' if not hide_prices else '0')
        body.set('data-tp-request-summary-url', summary_url)
    for anchor in root.xpath('.//a[@href]'):
        target = urlsplit(anchor.get('href'))
        if target.netloc not in ('', host):
            continue
        if re.fullmatch(r'(?:/[A-Za-z_-]+)?/shop/cart/?', target.path):
            anchor.set('href', summary_url)
            anchor.set('title', 'La tua richiesta')
            anchor.set('aria-label', 'La tua richiesta')
            anchor.text = None
            for child in list(anchor):
                anchor.remove(child)
            etree.SubElement(anchor, 'span', {'class': 'tp-request-label'}).text = 'La tua richiesta'
            if anchor.xpath('ancestor::header'):
                anchor.set('class', (anchor.get('class', '') + ' tp-request-header').strip())
                anchor.set('data-tp-request-header', '')
                etree.SubElement(anchor, 'span', {'data-tp-request-header-count': '', 'aria-hidden': 'true'}).text = '…'
            for parent in anchor.iterancestors():
                classes = parent.get('class', '').split()
                if 'o_wsale_my_cart' in classes:
                    parent.set('class', ' '.join(item for item in classes if item != 'o_wsale_my_cart'))
    for button in root.xpath('.//button[@name="add_to_cart"] | .//a[@id="add_to_cart"]'):
        for child in list(button):
            button.remove(child)
        button.text = 'Aggiungi alla richiesta'
        button.set('aria-label', 'Aggiungi alla richiesta')
        button.set('title', 'Aggiungi alla richiesta')
        button.set('data-action', 'add_to_cart')
    for node in list(root.iter()):
        if not isinstance(node.tag, str):
            continue
        if node.tag not in ('script', 'style') and node.text and node.text.strip().startswith('Acquista'):
            node.text = node.text.replace('Acquista', 'Scegli', 1)
        if not hide_prices:
            continue
        classes = set(node.get('class', '').split())
        name = node.get('name', '')
        if (classes & PRICE_CLASSES or node.get('itemprop') in ('price', 'priceCurrency', 'offers')
                or node.get('data-oe-type') == 'monetary'
                or name in ('packaging_price', 'tax_indicator', 'product_price', 'product_price_strikethrough')
                or (node.tag == 'del' and node.xpath('.//*[contains(concat(" ", @class, " "), " oe_currency_value ")]'))
                or node.get('id') == 'o_wsale_price_range_option'
                or (node.tag == 'meta' and re.search(r'price|amount', node.get('property', ''), re.I))):
            if node.getparent() is not None:
                node.drop_tree()
            continue
        for key in list(node.attrib):
            if key.startswith('data-') and (ECONOMIC_KEY.search(key) and key not in ('data-tp-request-prices',)):
                del node.attrib[key]
            elif key.startswith('data-') and node.get(key, '').startswith(('{', '[')):
                try:
                    node.set(key, json.dumps(economic_data(json.loads(node.get(key)), summary_url, True, host)))
                except (ValueError, TypeError):
                    pass
        if node.tag == 'script' and node.get('type') == 'application/ld+json' and node.text:
            try:
                node.text = json.dumps(economic_data(json.loads(node.text), summary_url, True, host), ensure_ascii=True)
            except ValueError:
                node.drop_tree()
        elif node.tag not in ('script', 'style'):
            if node.text:
                node.text = MONEY.sub('', node.text)
            if node.tail:
                node.tail = MONEY.sub('', node.tail)
    if full:
        return html.tostring(root, encoding='unicode', doctype='<!DOCTYPE html>')
    return (root.text or '') + ''.join(html.tostring(child, encoding='unicode') for child in root)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _post_dispatch(cls, response):
        if (public_storefront() and request.env.website._torrepulia_request_enabled()
                and response.status_code == 200 and not response.is_streamed):
            website = request.env.website
            # An authorised Builder session needs the original document, so
            # saving a page never persists a redacted copy. A public query flag
            # cannot opt out of the public price policy.
            # The Odoo 20 client action opens its document through
            # /website/force/... in an iframe, without enable_editor in that
            # document's URL. Rewriting branded fields there makes the editor
            # treat header/footer fields as changed and save rendered copies.
            # A forged iframe header never grants this editor-only exemption.
            editing = (request.env.user.has_group('website.group_website_restricted_editor') and
                       (request.params.get('enable_editor') or
                        request.httprequest.headers.get('Sec-Fetch-Dest') == 'iframe'))
            if not editing:
                if getattr(response, 'is_qweb', False):
                    response.flatten()
                hide = not website._torrepulia_request_prices_visible()
                summary = website._torrepulia_request_url()
                if response.mimetype == 'text/html':
                    response.set_data(storefront_html(response.get_data(as_text=True), summary, hide, request.httprequest.host))
                elif response.mimetype == 'application/json':
                    data = json.loads(response.get_data(as_text=True))
                    response.set_data(json.dumps(economic_data(data, summary, hide, request.httprequest.host), ensure_ascii=True))
                response.headers['Cache-Control'] = 'private, no-store'
                response.headers['Vary'] = 'Cookie'
        return super()._post_dispatch(response)
