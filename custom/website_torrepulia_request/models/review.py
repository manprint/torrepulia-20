import hashlib
import math
import re
from datetime import timedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.misc import format_amount, formatLang

from .selection import canonical


PRIVACY_NOTICE = "Ho letto l'informativa sulla privacy e acconsento al trattamento dei dati per rispondere alla richiesta."


class ReviewValidation(ValidationError):
    def __init__(self, message, field_names=()):
        super().__init__(message)
        self.field_names = list(field_names)


def submission_values(payload):
    allowed = {'selection_id', 'revision', 'operation_id', 'contact_name', 'email', 'phone', 'notes', 'delivery_area', 'privacy_accepted'}
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ReviewValidation(_('Dati di invio non validi.'))
    if (not isinstance(payload.get('selection_id'), str) or not re.fullmatch(r'[0-9a-f]{32}', payload['selection_id'])
            or type(payload.get('revision')) is not int or payload['revision'] < 0
            or not isinstance(payload.get('operation_id'), str)
            or not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', payload['operation_id'])):
        raise ReviewValidation(_('Ricarica la selezione prima di inviare.'))
    clean, errors = {}, []
    for key in ('contact_name', 'email', 'phone', 'notes', 'delivery_area'):
        value = payload.get(key, '')
        if (not isinstance(value, str) or len(value) > (5000 if key == 'notes' else 256)
                or any(ord(char) == 0 or 0xD800 <= ord(char) <= 0xDFFF for char in value)):
            errors.append(key)
        else:
            clean[key] = value.strip()
    if not clean.get('contact_name'):
        errors.append('contact_name')
    email = tools.email_normalize(clean.get('email', ''))
    if not email:
        errors.append('email')
    if payload.get('privacy_accepted') is not True:
        errors.append('privacy_accepted')
    if errors:
        raise ReviewValidation(_('Verifica i campi indicati e la presa visione dell’informativa privacy.'), sorted(set(errors)))
    clean['email'] = email
    area = ' '.join(clean.pop('delivery_area', '').split())
    if area:
        clean['notes'] = 'CAP o Città: %s%s' % (area, '\n\n' + clean['notes'] if clean['notes'] else '')
    return clean


class ProductProduct(models.Model):
    _inherit = 'product.product'

    torrepulia_request_liters = fields.Float('Litri per unità di vendita', digits=(16, 6), default=0,
        help='Contenuto commerciale in litri per una unità di misura di vendita del prodotto. Zero: non configurato. Non è il volume logistico.')

    @api.constrains('torrepulia_request_liters')
    def _check_request_liters(self):
        if any(not math.isfinite(product.torrepulia_request_liters) or product.torrepulia_request_liters < 0 for product in self):
            raise ValidationError(_('Il contenuto in litri deve essere finito e non negativo.'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    torrepulia_request_liters = fields.Float('Litri per unità di vendita', digits=(16, 6),
        compute='_compute_request_liters', inverse='_inverse_request_liters',
        help='Per prodotti con più varianti configura il contenuto su ciascuna variante. Zero: non configurato.')

    @api.depends('product_variant_ids.torrepulia_request_liters')
    def _compute_request_liters(self):
        for template in self:
            template.torrepulia_request_liters = template.product_variant_ids.torrepulia_request_liters if len(template.product_variant_ids) == 1 else 0

    def _inverse_request_liters(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.torrepulia_request_liters = template.torrepulia_request_liters


class QuoteRequest(models.Model):
    _inherit = 'torrepulia.request'

    review_digest = fields.Char(copy=False, index=True, groups='base.group_system')
    submission_operation_id = fields.Char(copy=False, groups='base.group_system')
    submission_fingerprint = fields.Char(copy=False, groups='base.group_system')
    public_receipt = fields.Json(copy=False, readonly=True)
    privacy_accepted_at = fields.Datetime(copy=False, readonly=True)


class Website(models.Model):
    _inherit = 'website'

    def _request_addition_details(self, session, payload, pricelist, fiscal_position):
        draft = self._torrepulia_session_request(session)
        product, uom, values, custom = draft._configured_product(self, payload)
        quantity = draft._quantity_for_website(self, payload['quantity'], uom)
        result = {'product_id': product.id, 'quantity': quantity,
                  'name': product.with_context(display_default_code=False).display_name,
                  'attributes': product.product_template_attribute_value_ids.mapped('name') + values.mapped('name')}
        if self._torrepulia_request_prices_visible():
            info = product.product_tmpl_id._get_combination_info(
                combination=product.product_template_attribute_value_ids | values, product_id=product.id,
                add_qty=quantity, uom_id=uom.id, pricelist=pricelist, fiscal_position=fiscal_position)
            if not info.get('hide_price'):
                currency = info['currency']
                result.update({'subtotal_display': format_amount(self.env, currency.round(info['price'] * quantity), currency),
                               'currency': currency.name})
        return result

    def _request_review_state(self, session, pricelist, fiscal_position):
        self.ensure_one()
        state = self._request_selection_state(session)
        draft = self._torrepulia_session_request(session)
        all_liters = bool(state['lines'])
        all_prices = bool(state['lines']) and state['show_prices']
        liters_sum = products_sum = 0
        currency = pricelist.currency_id or self.currency_id
        rows = {line._configuration_key(): line for line in draft.line_ids}
        for item in state['lines']:
            line = rows[item['key']]
            saved = line.selection_snapshot or {}
            item.update({'attributes': [value['name'] for value in saved.get('attributes', [])],
                         'custom_text': list((line.custom_values or {}).values()),
                         'format': saved.get('format', ''), 'thumbnail': None})
            if not item['available']:
                all_liters = all_prices = False
                continue
            product = line.product_id.with_env(self.env)
            item['name'] = product.with_context(display_default_code=False).display_name
            item['thumbnail'] = '/web/image/product.product/%s/image_128' % product.id
            item['format'] = (product.product_tmpl_id.torrepulia_format_detail
                              if 'torrepulia_format_detail' in product.product_tmpl_id._fields else '')
            if product.torrepulia_request_liters:
                quantity = line.uom_id.with_env(self.env)._compute_quantity(item['quantity'], product.uom_id, round=False)
                liters = quantity * product.torrepulia_request_liters
                item['liters_display'] = _('%s L', formatLang(self.env, liters, digits=3))
                liters_sum += liters
            else:
                all_liters = False
            if state['show_prices']:
                info = product.product_tmpl_id._get_combination_info(
                    combination=product.product_template_attribute_value_ids | line.no_variant_value_ids.with_env(self.env),
                    product_id=product.id, add_qty=item['quantity'], uom_id=line.uom_id.id,
                    pricelist=pricelist, fiscal_position=fiscal_position)
                if info.get('hide_price'):
                    all_prices = False
                else:
                    currency = info['currency']
                    subtotal = currency.round(info['price'] * item['quantity'])
                    item['price_display'] = format_amount(self.env, info['price'], currency)
                    item['subtotal_display'] = format_amount(self.env, subtotal, currency)
                    products_sum += subtotal
        if all_liters:
            state['liters_display'] = _('%s L', formatLang(self.env, liters_sum, digits=3))
        if all_prices:
            state['products_total_display'] = format_amount(self.env, products_sum, currency)
        state['can_submit'] = bool(state['enabled'] and state['lines'] and all(line['available'] for line in state['lines']))
        return state

    def _request_receipt(self, review_digest, selection_id=None, *, submission=False):
        self.ensure_one()
        if not self._torrepulia_selection_enabled() or not self.has_ecommerce_access():
            return self.env['torrepulia.request']
        if not isinstance(review_digest, str) or not re.fullmatch(r'[0-9a-f]{64}', review_digest):
            return self.env['torrepulia.request']
        # Capability comes only from this HTTP session. Never search by public ID.
        domain = [('review_digest', '=', review_digest), ('website_id', '=', self.id),
                  ('company_id', '=', self.company_id.id), ('state', '=', 'submitted')]
        if not submission:
            domain.append(('submitted_at', '>=', fields.Datetime.now() - timedelta(hours=24)))
        if selection_id is not None:
            domain.append(('selection_id', '=', selection_id))
        return self.env['torrepulia.request'].sudo().search(domain, order='submitted_at desc, id desc', limit=1)

    def _request_submit_review(self, session, payload, review_digest, pricelist, fiscal_position, verify_captcha):
        self.ensure_one()
        if not isinstance(review_digest, str) or not re.fullmatch(r'[0-9a-f]{64}', review_digest):
            raise AccessError(_('Sessione non autorizzata.'))
        clean = submission_values(payload)
        fingerprint = hashlib.sha256(canonical(dict(clean, selection_id=payload['selection_id'],
            revision=payload['revision'], privacy_accepted=True)).encode()).hexdigest()
        # A confirmation page expires; the server-side idempotency record does
        # not. A late network retry must still never create a second opportunity.
        receipt = self._request_receipt(review_digest, payload['selection_id'], submission=True)
        if receipt:
            if receipt.submission_operation_id != payload['operation_id'] or receipt.submission_fingerprint != fingerprint:
                raise ReviewValidation(_('Questa richiesta è già stata inviata.'))
            return dict(receipt.public_receipt, replayed=True)
        draft = self._torrepulia_session_request(session)
        if not draft:
            raise ReviewValidation(_('La selezione non è più disponibile. Ricarica la richiesta.'))
        draft._lock_draft()
        if draft.selection_id != payload['selection_id'] or draft.selection_revision != payload['revision']:
            raise ReviewValidation(_('La selezione è cambiata. Controlla prodotti e quantità prima di inviare.'), ['selection'])
        state = self._request_review_state(session, pricelist, fiscal_position)
        if not state['can_submit']:
            raise ReviewValidation(_('Verifica i prodotti della richiesta prima di inviare.'), ['selection'])
        verify_captcha()
        receipt = {key: state[key] for key in ('lines', 'show_prices', 'quantity', 'products_total_display', 'liters_display') if key in state}
        receipt.update(self._request_receipt_context(), reference=draft.name)
        draft.write({'review_digest': review_digest, 'submission_operation_id': payload['operation_id'],
            'submission_fingerprint': fingerprint, 'public_receipt': receipt,
            'privacy_accepted_at': fields.Datetime.now()})
        draft._submit(self, clean)
        # Prepare the next selection in the same transaction. Replays return
        # above and must never clear a later, intentionally composed request.
        # Session storage is outside PostgreSQL: do not rotate the live token
        # before commit. The next read deterministically resolves this draft.
        self._torrepulia_session_request(dict(session), create=True)
        return dict(receipt, replayed=False)
