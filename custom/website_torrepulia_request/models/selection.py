"""The single, server-authoritative selection protocol. No cart/pricing API calls."""
import hashlib
import json
import re
import secrets
from decimal import Decimal, InvalidOperation

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def quantity_value(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValidationError(_('Quantità non numerica.'))
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValidationError(_('Quantità non numerica.')) from error
    if not number.is_finite() or number < 0 or number > Decimal('1000000000'):
        raise ValidationError(_('Quantità non valida.'))
    return number


class Website(models.Model):
    _inherit = 'website'

    @api.constrains('torrepulia_request_min_qty', 'torrepulia_request_max_qty', 'torrepulia_request_qty_step')
    def _check_request_quantity_limits(self):
        for website in self:
            low, high, step = (quantity_value(v) for v in (
                website.torrepulia_request_min_qty, website.torrepulia_request_max_qty,
                website.torrepulia_request_qty_step))
            if not low or not step or high < low or low % step or high % step:
                raise ValidationError(_('Minimo e massimo devono essere multipli del passo positivo.'))

    def _request_selection_state(self, session):
        self.ensure_one()
        draft = self._torrepulia_session_request(session, create=True)
        if draft:
            draft._lock_draft()
            return draft._selection_state(self)
        return {
            'website_id': self.id,
            'enabled': self._torrepulia_request_enabled() and self.has_ecommerce_access(),
            'selection_id': None, 'revision': 0, 'lines': [], 'line_count': 0, 'quantity': 0,
            'summary_url': self._torrepulia_request_url(),
            'show_prices': self._torrepulia_request_prices_visible(),
            'limits': {'min': self.torrepulia_request_min_qty, 'max': self.torrepulia_request_max_qty,
                       'step': self.torrepulia_request_qty_step},
        }

    def _request_selection_apply(self, session, payload):
        """Only the current visitor website and real server session may be passed here."""
        self.ensure_one()
        if not self._torrepulia_request_enabled() or not self.has_ecommerce_access():
            raise AccessError(_('La selezione richieste non è disponibile.'))
        operation, fingerprint = self.env['torrepulia.request']._validate_selection_payload(payload)
        draft = self._torrepulia_session_request(session, create=True)
        if not draft:
            return {'ok': False, 'code': 'conflict', 'state': self._request_selection_state(session)}
        return draft._apply_selection(self, payload, fingerprint)


class QuoteRequest(models.Model):
    _inherit = 'torrepulia.request'

    selection_id = fields.Char(default=lambda self: secrets.token_hex(16), required=True, copy=False)
    selection_revision = fields.Integer(default=0, required=True, copy=False)
    operation_ids = fields.One2many('torrepulia.request.operation', 'request_id')
    _selection_unique = models.Constraint('UNIQUE(selection_id)', 'Identità selezione già utilizzata.')

    @api.model
    def _validate_selection_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError(_('Operazione non valida.'))
        common = {'operation', 'operation_id', 'selection_id', 'revision'}
        fields_by_operation = {
            'add': {'product_id', 'uom_id', 'no_variant_value_ids', 'custom_values', 'quantity'},
            'set': {'line_key', 'quantity'},
            'set_configuration': {'product_id', 'uom_id', 'no_variant_value_ids', 'custom_values', 'quantity'},
            'remove': {'line_key'}, 'clear': set(),
        }
        operation = payload.get('operation')
        if not isinstance(operation, str) or operation not in fields_by_operation or set(payload) - common - fields_by_operation[operation]:
            raise ValidationError(_('Operazione o campi non consentiti.'))
        if not re.fullmatch(r'[A-Za-z0-9_-]{16,64}', str(payload.get('operation_id', ''))):
            raise ValidationError(_('Identificatore operazione non valido.'))
        revision = payload.get('revision')
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise ValidationError(_('Revisione non valida.'))
        selection_id = payload.get('selection_id')
        if not isinstance(selection_id, str) or not re.fullmatch(r'[0-9a-f]{32}', selection_id):
            raise ValidationError(_('Selezione non valida.'))
        if 'quantity' in fields_by_operation[operation]:
            quantity_value(payload.get('quantity'))
        if 'line_key' in fields_by_operation[operation] and not re.fullmatch(r'[0-9a-f]{64}', str(payload.get('line_key', ''))):
            raise ValidationError(_('Riga non valida.'))
        semantic = {k: v for k, v in payload.items() if k not in ('operation_id', 'selection_id', 'revision')}
        try:
            fingerprint = hashlib.sha256(canonical(semantic).encode()).hexdigest()
        except (ValueError, TypeError) as error:
            raise ValidationError(_('Configurazione non valida.')) from error
        return operation, fingerprint

    def _configured_product(self, website, payload):
        def native_id(value):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValidationError(_('Identificatore prodotto non valido.'))
            return value

        product_id = native_id(payload.get('product_id'))
        product = website.env['product.product'].browse(product_id).exists()
        if not product:
            raise ValidationError(_('Il prodotto non è più disponibile.'))
        product.check_access('read')
        uom = website.env['uom.uom'].browse(native_id(payload['uom_id'])).exists() if 'uom_id' in payload else product.uom_id
        values = payload.get('no_variant_value_ids', [])
        custom = payload.get('custom_values', {})
        if (not isinstance(values, list) or len(values) > 100 or len(set(map(str, values))) != len(values)
                or not isinstance(custom, dict) or len(custom) > 32):
            raise ValidationError(_('Configurazione prodotto non valida.'))
        values = website.env['product.template.attribute.value'].browse([native_id(v) for v in values])
        if len(values.exists()) != len(values):
            raise ValidationError(_('Attributi prodotto non validi.'))
        if any(not isinstance(k, str) or not re.fullmatch(r'[1-9][0-9]*', k)
               or not isinstance(v, str) or not v.strip() or len(v) > 1024 for k, v in custom.items()):
            raise ValidationError(_('Valori personalizzati non validi.'))
        custom = {k: v.strip() for k, v in custom.items()}
        self._validate_selection_configuration(website, product, uom, values, custom)
        return product, uom, values, custom

    def _quantity_for_website(self, website, quantity, uom):
        number = quantity_value(quantity)
        if number:
            low, high, step = (Decimal(str(v)) for v in (
                website.torrepulia_request_min_qty, website.torrepulia_request_max_qty,
                website.torrepulia_request_qty_step))
            if number < low or number > high or number % step:
                raise ValidationError(_('Quantità fuori dai limiti o dal passo consentito.'))
            if not uom or Decimal(str(uom.round(float(number)))) != number:
                raise ValidationError(_('Quantità non compatibile con la precisione dell’unità di misura.'))
        return float(number)

    def _apply_selection(self, website, payload, fingerprint):
        self._lock_draft()
        # Every endpoint reaches this record through a session capability first.
        if self.website_id.id != website.id or self.company_id != website.company_id:
            raise AccessError(_('Selezione non autorizzata.'))
        previous = self.env['torrepulia.request.operation'].search([
            ('request_id', '=', self.id), ('operation_id', '=', payload['operation_id']),
        ], limit=1)
        if previous:
            if previous.fingerprint != fingerprint:
                raise ValidationError(_('Identificatore già usato per un’operazione diversa.'))
            return {'ok': True, 'replayed': True, 'state': self._selection_state(website)}
        if payload.get('selection_id') != self.selection_id or payload['revision'] != self.selection_revision:
            return {'ok': False, 'code': 'conflict', 'state': self._selection_state(website)}
        operation = payload['operation']
        if operation == 'clear':
            self.line_ids.unlink()
        elif operation in ('remove', 'set'):
            lines = self.line_ids.filtered(lambda line: line._configuration_key() == payload['line_key'])
            if not lines:
                raise ValidationError(_('La riga non appartiene alla selezione corrente.'))
            if operation == 'remove' or quantity_value(payload.get('quantity')) == 0:
                lines.unlink()
            else:
                line = lines[0]
                quantity = self._quantity_for_website(website, payload['quantity'], line.uom_id.with_env(website.env))
                self._set_selection(website, line.product_id.with_env(website.env), quantity,
                                    uom=line.uom_id.with_env(website.env),
                                    no_variant_values=line.no_variant_value_ids.with_env(website.env),
                                    custom_values=line.custom_values, line=line)
                (lines - line).unlink()
        else:
            product, uom, values, custom = self._configured_product(website, payload)
            if operation == 'add' and product._is_sold_out():
                # Catalogue additions follow native stock policy. Seasonal quantities
                # deliberately remain preorders (set_configuration), without reservations.
                raise ValidationError(_('Prodotto esaurito. Consulta il messaggio di disponibilità nella scheda prodotto.'))
            key = self.env['torrepulia.request.line']._make_configuration_key(product.id, uom.id, values.ids, custom)
            lines = self.line_ids.filtered(lambda line: line._configuration_key() == key)
            requested = quantity_value(payload['quantity'])
            if operation == 'add' and not requested:
                raise ValidationError(_('La quantità da aggiungere deve essere positiva.'))
            quantity = requested + sum((Decimal(str(line.quantity)) for line in lines), Decimal(0)) if operation == 'add' else requested
            quantity = self._quantity_for_website(website, quantity, uom)
            if not quantity:
                lines.unlink()
            else:
                if not lines and len(self.line_ids) >= 200:
                    raise ValidationError(_('La selezione può contenere al massimo 200 configurazioni.'))
                line = self._set_selection(website, product, quantity, uom=uom,
                                           no_variant_values=values, custom_values=custom, line=lines[:1])
                (lines - line).unlink()
        self.write({'selection_revision': self.selection_revision + 1, 'last_activity': fields.Datetime.now()})
        self.env['torrepulia.request.operation'].create({
            'request_id': self.id, 'operation_id': payload['operation_id'],
            'fingerprint': fingerprint, 'revision': self.selection_revision,
        })
        return {'ok': True, 'replayed': False, 'state': self._selection_state(website)}

    def _selection_state(self, website):
        grouped = {}
        for line in self.line_ids.sorted('id'):
            key = line._configuration_key()
            if key in grouped:
                grouped[key]['quantity'] += line.quantity
                continue
            available = False
            try:
                product = website.env['product.product'].browse(line.product_id.id)
                self._validate_selection_configuration(website, product, line.uom_id.with_env(website.env),
                                                       line.no_variant_value_ids.with_env(website.env),
                                                       line.custom_values or {})
                available = True
            except (AccessError, ValidationError):
                pass
            saved = line.selection_snapshot or {}
            grouped[key] = {
                'key': key, 'product_id': line.product_id.id, 'uom_id': line.uom_id.id,
                'default_uom_id': product.uom_id.id if available else None,
                'no_variant_value_ids': sorted(line.no_variant_value_ids.ids),
                'custom_values': line.custom_values or {}, 'quantity': line.quantity,
                'name': saved.get('name', _('Prodotto selezionato')),
                'uom_name': saved.get('uom_name', ''), 'available': available,
                'warning': '' if available else _('Prodotto archiviato, configurazione cambiata o non più accessibile. Rimuovilo o contattaci.'),
            }
        lines = list(grouped.values())
        return {
            'website_id': website.id,
            'enabled': True, 'selection_id': self.selection_id, 'revision': self.selection_revision,
            'lines': lines, 'line_count': len(lines), 'quantity': sum(line['quantity'] for line in lines),
            'summary_url': website._torrepulia_request_url(),
            'show_prices': website._torrepulia_request_prices_visible(),
            'limits': {'min': website.torrepulia_request_min_qty, 'max': website.torrepulia_request_max_qty,
                       'step': website.torrepulia_request_qty_step},
        }


class QuoteRequestLine(models.Model):
    _inherit = 'torrepulia.request.line'

    selection_snapshot = fields.Json(readonly=True, copy=False)

    @api.model
    def _make_configuration_key(self, product_id, uom_id, values, custom):
        return hashlib.sha256(canonical({
            'product_id': product_id, 'uom_id': uom_id,
            'no_variant_value_ids': sorted(values), 'custom_values': custom or {},
        }).encode()).hexdigest()

    def _configuration_key(self):
        self.ensure_one()
        return self._make_configuration_key(self.product_id.id, self.uom_id.id,
                                            self.no_variant_value_ids.ids, self.custom_values)


class RequestOperation(models.Model):
    _name = 'torrepulia.request.operation'
    _description = 'Idempotenza operazioni selezione richiesta'

    request_id = fields.Many2one('torrepulia.request', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True)
    operation_id = fields.Char(required=True)
    fingerprint = fields.Char(required=True)
    revision = fields.Integer(required=True)
    _operation_unique = models.Constraint('UNIQUE(request_id, operation_id)', 'Operazione già elaborata.')
