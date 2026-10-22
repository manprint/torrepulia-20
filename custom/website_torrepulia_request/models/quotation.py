from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


class Request(models.Model):
    _inherit = 'torrepulia.request'

    quotation_lock_version = fields.Integer(default=0, readonly=True, copy=False, groups='base.group_system')

    def _check_quotation_operator(self):
        self.ensure_one()
        self.check_access('read')
        if not self.env.user.has_group('sales_team.group_sale_salesman'):
            raise AccessError(_('Solo un operatore commerciale può preparare il preventivo.'))
        if self.company_id not in self.env.companies or self.state != 'submitted' or not self.opportunity_id:
            raise ValidationError(_('Seleziona una richiesta inviata della tua azienda.'))
        self.opportunity_id.check_access('write')
        if self.opportunity_id.company_id != self.company_id:
            raise ValidationError(_('L’opportunità deve appartenere all’azienda della richiesta.'))
        self.env['sale.order'].check_access('create')

    def _generated_quotations(self):
        """Narrow lookup after request authorization, including hidden orders.

        Do not silently create duplicates when a linked quotation has been
        reassigned to a salesperson whose order the caller cannot read.
        """
        self._check_quotation_operator()
        self.env['sale.order'].flush_model(['torrepulia_request_id'])
        self.env.cr.execute('SELECT id FROM sale_order WHERE torrepulia_request_id = %s ORDER BY id DESC', [self.id])
        orders = self.env['sale.order'].browse([row[0] for row in self.env.cr.fetchall()])
        orders.check_access('read')
        return orders

    def _quotation_wizard(self, revision=False):
        orders = self._generated_quotations()
        return {'type': 'ir.actions.act_window', 'name': _('Prepara preventivo'),
                'res_model': 'torrepulia.request.quotation.wizard', 'view_mode': 'form', 'target': 'new',
                'context': {'default_request_id': self.id,
                            'default_partner_id': (self.opportunity_id.partner_id or self.partner_id).id,
                            'default_create_revision': bool(revision or orders)}}

    def action_prepare_quotation(self):
        self.ensure_one()
        orders = self._generated_quotations()
        active = orders.filtered(lambda order: order.state != 'cancel')
        if active:
            return active[0]._torrepulia_quotation_action()
        return self._quotation_wizard()

    def action_new_quotation_revision(self):
        self.ensure_one()
        if not self._generated_quotations():
            return self._quotation_wizard()
        return self._quotation_wizard(revision=True)


class RequestLine(models.Model):
    _inherit = 'torrepulia.request.line'

    received_name = fields.Char('Prodotto ricevuto', compute='_compute_received_details')
    received_uom = fields.Char('Unità ricevuta', compute='_compute_received_details')
    received_configuration = fields.Text('Configurazione ricevuta', compute='_compute_received_details')

    @api.depends('snapshot', 'selection_snapshot')
    def _compute_received_details(self):
        for line in self:
            snapshot = line.snapshot or line.selection_snapshot or {}
            line.received_name = snapshot.get('name', '')
            line.received_uom = snapshot.get('uom_name', '')
            details = [value['name'] for value in snapshot.get('attributes', [])]
            details.extend((snapshot.get('custom_values') or {}).values())
            line.received_configuration = '\n'.join(details)

    def _quotation_line_values(self):
        self.ensure_one()
        product, uom = self.product_id, self.uom_id
        product.check_access('read')
        uom.check_access('read')
        if (not product.active or not product.sale_ok or product.type == 'combo'
                or product.company_id and product.company_id != self.company_id):
            raise ValidationError(_('Il prodotto %s non è più vendibile con questa configurazione. Qualifica la richiesta prima di proseguire.', product.display_name))
        if uom not in product._get_available_uoms() or uom.round(self.quantity) != self.quantity:
            raise ValidationError(_('L’unità o la precisione della quantità non è più valida.'))
        if self.snapshot and self.snapshot.get('uom_factor') != uom.factor:
            raise ValidationError(_('La conversione dell’unità di misura è cambiata rispetto alla richiesta ricevuta.'))
        valid = product.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        values = product.product_template_attribute_value_ids | self.no_variant_value_ids
        if (self.no_variant_value_ids - valid or any(value.attribute_id.create_variant != 'no_variant' for value in self.no_variant_value_ids)
                or not product.product_tmpl_id._is_combination_possible(values)
                or set(self.custom_values or {}) != {str(value.id) for value in values.filtered('is_custom')}):
            raise ValidationError(_('Gli attributi richiesti non sono più disponibili. La richiesta originale resta conservata.'))
        return {'product_id': product.id, 'product_uom_qty': self.quantity, 'product_uom_id': uom.id,
                'product_no_variant_attribute_value_ids': [fields.Command.set(self.no_variant_value_ids.ids)],
                'product_custom_attribute_value_ids': [fields.Command.create({
                    'custom_product_template_attribute_value_id': int(value_id), 'custom_value': text,
                }) for value_id, text in (self.custom_values or {}).items()]}


class QuotationWizard(models.TransientModel):
    _name = 'torrepulia.request.quotation.wizard'
    _description = 'Prepara preventivo da richiesta website'
    _check_company_auto = True

    request_id = fields.Many2one('torrepulia.request', required=True, readonly=True, ondelete='cascade')
    company_id = fields.Many2one(related='request_id.company_id')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, check_company=True)
    contact_name = fields.Char(related='request_id.contact_name')
    contact_email = fields.Char(related='request_id.email')
    contact_phone = fields.Char(related='request_id.phone')
    create_revision = fields.Boolean('Nuovo preventivo / revisione', readonly=True)
    reason = fields.Text('Motivazione')
    base_order_id = fields.Many2one('sale.order', readonly=True, copy=False)
    result_order_id = fields.Many2one('sale.order', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access('create')
        if any(vals.get('base_order_id') or vals.get('result_order_id') for vals in vals_list):
            raise ValidationError(_('Il preventivo di origine viene determinato dal server.'))
        for vals in vals_list:
            # ORM context defaults are client-controlled too.
            vals.update({'base_order_id': False, 'result_order_id': False})
        records = super().create(vals_list)
        for record in records:
            orders = record.request_id._generated_quotations()
            super(QuotationWizard, record).write({'base_order_id': orders[:1].id})
        return records

    def write(self, vals):
        if {'request_id', 'base_order_id', 'result_order_id'} & vals.keys():
            raise ValidationError(_('Non è possibile cambiare l’origine della preparazione.'))
        return super().write(vals)

    def action_prepare(self):
        self.ensure_one()
        self.check_access('write')
        request = self.request_id
        request._check_quotation_operator()
        # Wizard and source locks make retries and separate concurrent dialogs
        # converge. No write to the immutable submitted request is needed.
        self.env.cr.execute('SELECT id FROM torrepulia_request_quotation_wizard WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        # Odoo uses REPEATABLE READ. A read-only parent lock alone would let
        # another dialog retain a snapshot predating the newly created order.
        # Touch only this private technical counter, so native whole-transaction
        # retries get a fresh snapshot. Customer lines/contact snapshots stay fixed.
        self.env.cr.execute('UPDATE torrepulia_request SET quotation_lock_version = COALESCE(quotation_lock_version, 0) + 1 WHERE id = %s', [request.id])
        request.invalidate_recordset()
        request._check_quotation_operator()
        if self.result_order_id:
            self.result_order_id.check_access('read')
            if self.result_order_id.torrepulia_request_id != request:
                raise ValidationError(_('Il preventivo non appartiene a questa richiesta.'))
            return self.result_order_id._torrepulia_quotation_action()
        orders = request._generated_quotations()
        active = orders.filtered(lambda order: order.state != 'cancel')
        if active and (not self.create_revision or active[0] != self.base_order_id):
            super().write({'result_order_id': active[0].id})
            return active[0]._torrepulia_quotation_action()
        if orders and not self.create_revision:
            raise ValidationError(_('Per preparare un altro preventivo, scegli Nuovo preventivo / revisione.'))
        reason = (self.reason or '').strip()
        if self.create_revision and (not reason or len(reason) > 2000):
            raise ValidationError(_('Indica una motivazione della revisione, massimo 2000 caratteri.'))
        partner = self.partner_id
        partner.check_access('read')
        if not partner.active or partner.company_id and partner.company_id != request.company_id:
            raise ValidationError(_('Il cliente deve essere attivo e accessibile nell’azienda della richiesta.'))
        line_values = [line._quotation_line_values() for line in request.line_ids]
        if not line_values:
            raise ValidationError(_('La richiesta non contiene prodotti.'))
        lead = request.opportunity_id
        # This is an explicit qualification choice, never an email match.
        if lead.partner_id != partner:
            lead.partner_id = partner
        context = lead._prepare_opportunity_quotation_context()
        # Keep only native CRM defaults and the operator's language/companies:
        # arbitrary RPC default_price_unit/default_pricelist_id must not become
        # contractual values during this native recalculation.
        context.update({'lang': self.env.lang, 'tz': self.env.context.get('tz'),
                        'allowed_company_ids': [request.company_id.id] + (self.env.companies - request.company_id).ids})
        order = self.env['sale.order'].with_context(context).with_company(request.company_id).create({
            'company_id': request.company_id.id, 'partner_id': partner.id,
            'opportunity_id': lead.id, 'torrepulia_request_id': request.id,
            'origin': request.name, 'assigned_website_id': request.website_id.id,
            'order_line': [fields.Command.create(values) for values in line_values],
            'torrepulia_revision_reason': reason or False,
            'torrepulia_revision_of_id': self.base_order_id.id if self.create_revision else False,
        })
        body = Markup('%s: %s. %s') % (
            _('Preventivo preparato dalla richiesta'), request.name,
            reason if self.create_revision else _('Prima preparazione'))
        order.message_post(body=body, subtype_xmlid='mail.mt_note')
        lead.message_post(body=Markup('%s — %s') % (order.name, body), subtype_xmlid='mail.mt_note')
        super().write({'result_order_id': order.id})
        return order._torrepulia_quotation_action()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    torrepulia_revision_reason = fields.Text('Motivazione revisione richiesta', readonly=True, copy=False)
    torrepulia_revision_of_id = fields.Many2one('sale.order', string='Revisione di', readonly=True, copy=False, check_company=True)

    def _torrepulia_quotation_action(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.act_window', 'name': _('Preventivo'),
                'res_model': 'sale.order', 'view_mode': 'form', 'res_id': self.id,
                'views': [(self.env.ref('sale.view_order_form').id, 'form')], 'target': 'current'}
