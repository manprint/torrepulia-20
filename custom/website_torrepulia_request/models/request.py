import math
import secrets
from datetime import timedelta

from odoo import api, fields, models, _, tools
from odoo.fields import Domain
from odoo.exceptions import AccessError, ValidationError


class QuoteRequest(models.Model):
    _name = 'torrepulia.request'
    _inherit = 'utm.mixin'
    _description = 'Richiesta di preventivo website'
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char('Riferimento', required=True, readonly=True, copy=False, default='/')
    website_id = fields.Many2one('website', required=True, ondelete='restrict', index=True, check_company=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', index=True)
    lang = fields.Char('Lingua', required=True)
    state = fields.Selection([('draft', 'Bozza'), ('submitted', 'Inviata')], default='draft', required=True, copy=False)
    session_digest = fields.Char(required=True, copy=False, groups='base.group_system')
    last_activity = fields.Datetime(default=fields.Datetime.now, required=True)
    submitted_at = fields.Datetime(readonly=True, copy=False)
    submission_snapshot = fields.Json(readonly=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Contatto autenticato', check_company=True, ondelete='restrict')
    contact_name = fields.Char('Nome')
    email = fields.Char('Email')
    phone = fields.Char('Telefono')
    address = fields.Text('Indirizzo fornito')
    notes = fields.Text('Note')
    team_id = fields.Many2one('crm.team', required=True, check_company=True, ondelete='restrict')
    user_id = fields.Many2one('res.users', check_company=True, ondelete='restrict')
    line_ids = fields.One2many('torrepulia.request.line', 'request_id', copy=True)
    opportunity_id = fields.Many2one('crm.lead', readonly=True, copy=False, check_company=True, ondelete='restrict')
    quotation_ids = fields.One2many('sale.order', 'torrepulia_request_id', readonly=True)
    source_id = fields.Many2one('utm.source', ondelete='set null')
    campaign_id = fields.Many2one('utm.campaign', ondelete='set null')
    medium_id = fields.Many2one('utm.medium', ondelete='set null')
    origin = fields.Char('Origine')

    _reference_unique = models.Constraint('UNIQUE(name)', 'Il riferimento deve essere univoco.')
    _session_unique = models.Constraint('UNIQUE(session_digest)', 'La sessione deve essere univoca.')

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access('create')
        for vals in vals_list:
            if vals.get('state', 'draft') != 'draft' or vals.get('opportunity_id') or vals.get('submitted_at'):
                raise ValidationError(_('Creare prima una bozza.'))
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('torrepulia.request')
            vals['selection_id'] = secrets.token_hex(16)
            vals.setdefault('company_id', self.env['website'].browse(vals['website_id']).company_id.id)
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            record._lock_draft()
        if self.filtered(lambda r: r.state == 'submitted'):
            raise ValidationError(_('Una richiesta inviata è una fotografia immutabile.'))
        if {'name', 'website_id', 'company_id', 'session_digest', 'selection_id', 'state', 'submitted_at', 'opportunity_id'} & vals.keys():
            raise ValidationError(_('Transizione della richiesta non consentita.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _protect_submitted(self):
        for record in self:
            record._lock_draft()

    def _lock_draft(self):
        self.ensure_one()
        self.check_access('write')
        # Serialise edits/submission/cleanup so a double click cannot create two leads.
        self.env.cr.execute('SELECT id FROM torrepulia_request WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        if not self.exists() or self.state != 'draft':
            raise ValidationError(_('La richiesta non è più modificabile.'))

    def _set_selection(self, visitor_website, product, quantity, *, uom=None,
                       no_variant_values=None, custom_values=None, line=None):
        """Private adapter API. Product must be browsed in the visitor environment.

        custom_values = {str(native_ptav_id): text}. No prices/editorial overrides.
        Zero quantity removes only the specified line of this draft.
        """
        self._lock_draft()
        if (visitor_website.id != self.website_id.id or not visitor_website._torrepulia_selection_enabled()
                or not visitor_website.has_ecommerce_access()):
            raise AccessError(_('Website non autorizzato.'))
        try:
            quantity = float(quantity)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValidationError(_('Quantità non valida.')) from error
        if not math.isfinite(quantity) or quantity < 0:
            raise ValidationError(_('Quantità non valida.'))
        if line and line not in self.line_ids:
            raise AccessError(_('Riga non autorizzata.'))
        if quantity == 0:
            if line:
                line.unlink()
            self.last_activity = fields.Datetime.now()
            return self.env['torrepulia.request.line']
        uom = uom or product.uom_id
        no_variant_values = no_variant_values or product.env['product.template.attribute.value']
        custom_values = custom_values or {}
        self._validate_selection_configuration(visitor_website, product, uom, no_variant_values, custom_values)
        quantity = self._quantity_for_website(visitor_website, quantity, uom)
        vals = {
            'product_id': product.id, 'quantity': quantity, 'uom_id': uom.id,
            'no_variant_value_ids': [fields.Command.set(no_variant_values.ids)],
            'custom_values': custom_values,
        }
        if line:
            line.write(vals)
        else:
            line = self.env['torrepulia.request.line'].create(dict(vals, request_id=self.id))
        line.selection_snapshot = line._snapshot_values()
        self.last_activity = fields.Datetime.now()
        return line

    def _validate_selection_configuration(self, visitor_website, product, uom, no_variant_values, custom_values):
        product.ensure_one()
        product.check_access('read')
        if not visitor_website._torrepulia_selection_allows(product):
            raise ValidationError(_('Il prodotto non è prenotabile: acquistalo dal carrello o attendi la prossima campagna.'))
        template = product.product_tmpl_id
        domain = visitor_website.sale_product_domain()
        if (not product.active or not template.is_published
                or not visitor_website.env['product.template'].search_count(domain & Domain('id', '=', template.id))):
            raise ValidationError(_('Il prodotto non è accessibile nel catalogo di questo website.'))
        if uom not in product._get_available_uoms():
            raise ValidationError(_('Unità di misura non consentita per il prodotto.'))
        valid = template.valid_product_template_attribute_line_ids.product_template_value_ids
        if (no_variant_values - valid or any(v.attribute_id.create_variant != 'no_variant' for v in no_variant_values)):
            raise ValidationError(_('Configurazione senza variante non valida.'))
        combination = product.product_template_attribute_value_ids | no_variant_values
        if not template._is_combination_possible(combination):
            raise ValidationError(_('Combinazione prodotto non valida.'))
        if not isinstance(custom_values, dict):
            raise ValidationError(_('Configurazione personalizzata non valida.'))
        allowed_custom = combination.filtered('is_custom')
        if set(custom_values) != {str(v.id) for v in allowed_custom} or any(
                not isinstance(v, str) or not v.strip() or len(v) > 1024
                or any(char == '\x00' or 0xD800 <= ord(char) <= 0xDFFF for char in v)
                for v in custom_values.values()):
            raise ValidationError(_('Valori personalizzati non validi o mancanti.'))

    def _shipping_lead_values(self, shipping):
        """Native address fields of the opportunity: "New quotation" copies them on the customer it creates."""
        if not shipping:
            return {}
        if not isinstance(shipping, dict) or set(shipping) != {'street', 'zip', 'city', 'state_code'}:
            raise ValidationError(_('Indirizzo di spedizione non valido.'))
        italy = self.env.ref('base.it')
        province = self.env['res.country.state'].sudo().search(
            [('country_id', '=', italy.id), ('code', '=', shipping['state_code'])], limit=1)
        if not province:
            raise ValidationError(_('Provincia non valida.'))
        return {'street': shipping['street'], 'zip': shipping['zip'], 'city': shipping['city'],
                'state_id': province.id, 'country_id': italy.id}

    def _submit(self, visitor_website, contact):
        """Only final submission creates an opportunity; it never creates a contact/order.

        Caller must first resolve this record through the session capability.
        Notifications are persisted here; rendering and delivery run separately.
        """
        self._lock_draft()
        if (visitor_website.id != self.website_id.id or not visitor_website._torrepulia_selection_enabled()
                or not visitor_website.has_ecommerce_access()):
            raise AccessError(_('Website non autorizzato.'))
        if not self.line_ids:
            raise ValidationError(_('Selezionare almeno un prodotto.'))
        if not isinstance(contact, dict):
            raise ValidationError(_('Dati di contatto non validi.'))
        clean = {}
        for key in ('contact_name', 'email', 'phone', 'address', 'notes'):
            value = contact.get(key, '')
            # Public notes remain capped at 5000 before the validated area label
            # is appended; allow room for that optional 256-character context.
            limit = 5300 if key == 'notes' else 5000 if key == 'address' else 256
            if (not isinstance(value, str) or len(value) > limit
                    or any(ord(char) == 0 or 0xD800 <= ord(char) <= 0xDFFF for char in value)):
                raise ValidationError(_('Dati di contatto non validi.'))
            clean[key] = value.strip()
        clean['email'] = tools.email_normalize(clean['email'])
        if not clean['contact_name'] or not clean['email']:
            raise ValidationError(_('Nome e indirizzo email valido sono obbligatori.'))
        clean['phone'] = visitor_website._request_normalize_phone(clean['phone'])
        # Revalidate all products at the final boundary in the real visitor context.
        for line in self.line_ids:
            self._set_selection(
                visitor_website, visitor_website.env['product.product'].browse(line.product_id.id),
                line.quantity, uom=visitor_website.env['uom.uom'].browse(line.uom_id.id),
                no_variant_values=visitor_website.env['product.template.attribute.value'].browse(line.no_variant_value_ids.ids),
                custom_values=line.custom_values, line=line)
            line.snapshot = line._snapshot_values()
        clean['partner_id'] = visitor_website._torrepulia_request_partner().id or False
        shipping = self._shipping_lead_values(contact.get('shipping'))
        self.write(clean)
        site = self.website_id.sudo()
        site._check_torrepulia_request_settings()
        stage = site._request_crm_stage()
        source = self.source_id or self.env.ref('website_torrepulia_request.source_website_request')
        # Explicit website/company configuration wins over public-user defaults.
        lead = self.env['crm.lead'].sudo().with_company(self.company_id).with_context(
            mail_create_nosubscribe=True, mail_create_nolog=True, tracking_disable=True,
        ).create({
            'name': '%s — %s' % (self.name, self.contact_name), 'type': 'opportunity',
            'company_id': self.company_id.id, 'team_id': site.torrepulia_request_team_id.id,
            'user_id': site.torrepulia_request_user_id.id or False,
            'partner_id': self.partner_id.id or False,
            'contact_name': self.contact_name, 'email_from': self.email, 'phone': self.phone,
            'source_id': source.id, 'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'stage_id': stage.id,
            'torrepulia_website_id': site.id,
            'torrepulia_request_origin': 'Richiesta sito web',
            'description': tools.plaintext2html(self.notes or ''),
            **shipping,
        })
        # Internal transition bypasses the public write guard, not ORM validation.
        super(QuoteRequest, self).write({
            'state': 'submitted', 'submitted_at': fields.Datetime.now(),
            'source_id': source.id, 'origin': self.origin or 'Richiesta sito web',
            'opportunity_id': lead.id, 'team_id': site.torrepulia_request_team_id.id,
            'user_id': site.torrepulia_request_user_id.id or False,
            'submission_snapshot': {
                'website': site.name, 'company': self.company_id.name, 'lang': self.lang,
                'origin': self.origin or 'Richiesta sito web', 'source': source.name,
                'campaign': self.campaign_id.name, 'medium': self.medium_id.name,
                'contact': clean,
            },
        })
        notifications = self.env['torrepulia.request.notification'].create([
            {'request_id': self.id, 'kind': kind} for kind in ('internal', 'customer')])
        # The receipt leaves within seconds; the five-minute run only retries.
        notifications._trigger_cron('website_torrepulia_request.cron_prepare_request_notifications')
        return True

    @api.model
    def _cron_expire_drafts(self):
        for website in self.env['website'].search([]):
            cutoff = fields.Datetime.now() - timedelta(days=website.torrepulia_request_draft_days)
            drafts = self.search([('website_id', '=', website.id), ('state', '=', 'draft'),
                                  ('last_activity', '<', cutoff)], limit=500)
            for draft in drafts:
                self.env.cr.execute('SELECT id FROM torrepulia_request WHERE id = %s FOR UPDATE SKIP LOCKED', [draft.id])
                if not self.env.cr.fetchone():
                    continue
                draft.invalidate_recordset()
                if draft.state == 'draft' and draft.last_activity < cutoff:
                    draft.unlink()


class QuoteRequestLine(models.Model):
    _name = 'torrepulia.request.line'
    _description = 'Riga richiesta di preventivo'
    _check_company_auto = True

    request_id = fields.Many2one('torrepulia.request', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True)
    product_id = fields.Many2one('product.product', required=True, ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one(related='product_id.product_tmpl_id')
    quantity = fields.Float(required=True, digits='Product Unit', default=1)
    uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    no_variant_value_ids = fields.Many2many('product.template.attribute.value')
    custom_values = fields.Json(default=dict)
    snapshot = fields.Json(readonly=True, copy=False)

    _positive_qty = models.Constraint('CHECK(quantity > 0 AND quantity < \'Infinity\'::float)', 'La quantità deve essere positiva e finita.')

    def _snapshot_values(self):
        self.ensure_one()
        return {
            'product_id': self.product_id.id, 'template_id': self.product_template_id.id,
            'name': self.product_id.display_name, 'default_code': self.product_id.default_code,
            'quantity': self.quantity, 'uom_id': self.uom_id.id,
            'default_uom_id': self.product_id.uom_id.id,
            'uom_name': self.uom_id.name, 'uom_factor': self.uom_id.factor,
            'attributes': [{'id': v.id, 'name': v.display_name} for v in
                           self.product_id.product_template_attribute_value_ids | self.no_variant_value_ids],
            'custom_values': self.custom_values or {},
        }

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access('create')
        for vals in vals_list:
            self.env['torrepulia.request'].browse(vals['request_id'])._lock_draft()
        return super().create(vals_list)

    def write(self, vals):
        for request in self.request_id:
            request._lock_draft()
        if 'request_id' in vals:
            raise ValidationError(_('Non è possibile trasferire le righe.'))
        return super().write(vals)

    def unlink(self):
        for request in self.request_id:
            request._lock_draft()
        return super().unlink()


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    torrepulia_request_ids = fields.One2many('torrepulia.request', 'opportunity_id', string='Richieste website')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    torrepulia_request_id = fields.Many2one(
        'torrepulia.request', string='Richiesta website', check_company=True, ondelete='restrict', copy=False,
        domain="[('state', '=', 'submitted'), ('company_id', '=', company_id)]")

    @api.constrains('torrepulia_request_id', 'company_id', 'opportunity_id')
    def _check_torrepulia_request(self):
        for order in self.filtered('torrepulia_request_id'):
            if (order.torrepulia_request_id.state != 'submitted'
                    or order.opportunity_id != order.torrepulia_request_id.opportunity_id):
                raise ValidationError(_('Il preventivo deve appartenere all’opportunità della richiesta inviata.'))
