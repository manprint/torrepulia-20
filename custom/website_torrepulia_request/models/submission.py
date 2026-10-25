"""Final CRM handoff and durable, independently processed notifications."""
from datetime import timedelta

from psycopg2.extensions import TransactionRollbackError

from odoo import api, fields, models, _, tools
from odoo.exceptions import ConcurrencyError, UserError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation

from .review import ReviewValidation


class Website(models.Model):
    _inherit = 'website'

    torrepulia_request_stage_id = fields.Many2one('crm.stage', string='Fase iniziale richieste')

    def _request_normalize_phone(self, phone):
        self.ensure_one()
        if not phone:
            return ''
        partner = self._torrepulia_request_partner()
        country = partner.country_id or self.company_id.country_id
        try:
            return phone_validation.phone_format(phone, country.code, country.phone_code,
                                                 force_format='E164', raise_exception=True)
        except UserError as error:
            raise ReviewValidation(_('Verifica il telefono e, se necessario, indica il prefisso internazionale.'), ['phone']) from error

    @api.constrains('torrepulia_request_stage_id', 'torrepulia_request_team_id')
    def _check_request_stage(self):
        for website in self:
            stage = website.torrepulia_request_stage_id
            if stage and (stage.is_won or stage.team_ids and website.torrepulia_request_team_id not in stage.team_ids):
                raise ValidationError(_('La fase iniziale deve essere aperta e accessibile al team destinatario.'))

    def _request_crm_stage(self):
        """Called only on the validated website configuration under scoped sudo.

        Provision one team-scoped stage on first submission. Never modify existing
        stages, probabilities or opportunities. Website write serializes provision.
        """
        self.ensure_one()
        self._check_request_stage()
        if not self.torrepulia_request_stage_id:
            stage = self.env['crm.stage'].create({
                'name': 'Richiesta web ricevuta', 'sequence': 0, 'is_won': False,
                'team_ids': [fields.Command.set(self.torrepulia_request_team_id.ids)],
            })
            self.torrepulia_request_stage_id = stage
        return self.torrepulia_request_stage_id


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    torrepulia_request_stage_id = fields.Many2one(related='website_id.torrepulia_request_stage_id', readonly=False)


class Lead(models.Model):
    _inherit = 'crm.lead'

    torrepulia_website_id = fields.Many2one('website', string='Website richiesta', readonly=True, check_company=True)
    torrepulia_request_origin = fields.Char('Origine richiesta', readonly=True)


class Request(models.Model):
    _inherit = 'torrepulia.request'

    notification_ids = fields.One2many('torrepulia.request.notification', 'request_id', readonly=True)


class Notification(models.Model):
    _name = 'torrepulia.request.notification'
    _description = 'Notifica richiesta website'
    _order = 'id'
    _check_company_auto = True

    request_id = fields.Many2one('torrepulia.request', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True)
    kind = fields.Selection([('internal', 'Team commerciale'), ('customer', 'Ricevuta cliente')], required=True)
    state = fields.Selection([('pending', 'Da preparare'), ('queued', 'In coda email'), ('failed', 'Preparazione fallita')],
                             default='pending', required=True, readonly=True)
    mail_id = fields.Many2one('mail.mail', readonly=True, ondelete='set null')
    mail_state = fields.Selection(related='mail_id.state', string='Stato email')
    attempts = fields.Integer(readonly=True)
    retry_at = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True)
    error = fields.Text('Errore preparazione', readonly=True)

    _one_notification = models.Constraint('UNIQUE(request_id, kind)', 'Notifica già predisposta per questa richiesta.')

    def _recipients(self):
        self.ensure_one()
        record = self.request_id
        if self.kind == 'customer':
            return record.email
        users = (record.team_id.member_ids | record.team_id.user_id | record.user_id).filtered(
            lambda user: user.active and not user.share and record.company_id in user.company_ids)
        return ','.join(sorted({email for user in users if (email := tools.email_normalize(user.email or ''))}))

    def _mail_subject(self):
        self.ensure_one()
        record = self.request_id
        reservation = (record.public_receipt or {}).get('reservation')
        if self.kind == 'customer':
            return _('La tua prenotazione %s è registrata', record.name) if reservation else _('Richiesta ricevuta %s', record.name)
        return (_('Nuova prenotazione %s · %s', record.name, record.contact_name) if reservation
                else _('Richiesta sito web %s', record.name))

    def _mail_rows(self, base_url, show_prices):
        """Receipt rows as the email shows them: plain strings, absolute image URLs."""
        record = self.request_id
        rows = []
        for row in (record.public_receipt or {}).get('lines') or [line.snapshot for line in record.line_ids]:
            # The variant name already carries its values ("Latta 5 LT (Filtrato)").
            details = [value for value in (
                (value.get('name', '') if isinstance(value, dict) else value).split(': ')[-1]
                for value in row.get('attributes', [])) if value not in row.get('name', '')]
            details += row.get('custom_text', list((row.get('custom_values') or {}).values()))
            rows.append({
                'name': row.get('name', ''), 'details': ' · '.join(filter(None, details)),
                'quantity': '%g' % row['quantity'],
                'thumbnail': base_url + row['thumbnail'] if row.get('thumbnail') else False,
                'subtotal': show_prices and row.get('subtotal_display') or False,
            })
        return rows

    def _body_html(self):
        """Escape all customer/product text; use the immutable server-side receipt.

        No recalculation from mutable catalog data, no partial totals, and no
        amounts if hidden either at submission or at preparation time.
        """
        self.ensure_one()
        record = self.request_id
        website = record.website_id
        receipt = record.public_receipt or {}
        show_prices = bool(receipt.get('show_prices') and website.torrepulia_request_show_prices)
        base_url = website.get_base_url()
        partner = record.company_id.partner_id
        vat = (record.company_id.vat or '').replace(' ', '')
        return self.env['ir.qweb']._render('website_torrepulia_request.mail_request_body', {
            'kind': self.kind, 'record': record, 'reservation': receipt.get('reservation'),
            'first_name': (record.contact_name or '').split(' ')[0],
            'rows': self._mail_rows(base_url, show_prices),
            'total': show_prices and receipt.get('products_total_display') or False,
            'base_url': base_url, 'logo_url': '%s/web/image/website/%s/logo/240x120' % (base_url, website.id),
            'lead_url': record.opportunity_id and '%s/odoo/crm/%s' % (base_url, record.opportunity_id.id),
            'company': {
                'name': record.company_id.name, 'email': record.company_id.email, 'phone': record.company_id.phone,
                'address': ' · '.join(filter(None, [partner.street, ' '.join(filter(None, [partner.zip, partner.city]))])),
                'vat': vat[2:] if len(vat) > 2 and vat[:2].isalpha() else vat,
            },
        })

    @api.model
    def _cron_prepare(self):
        """Transactional outbox -> native mail queue. Never contact SMTP here.

        Failed rendering/recipients are isolated per notification and retried
        hourly (five attempts). SMTP failures belong to the native mail queue.
        A queued row is never recreated, even if its mail is later deleted.
        """
        candidates = self.search([('state', 'in', ['pending', 'failed']), ('attempts', '<', 5),
                                  ('retry_at', '<=', fields.Datetime.now())], limit=100)
        queued = False
        for item in candidates:
            self.env.cr.execute('SELECT id FROM torrepulia_request_notification WHERE id = %s FOR UPDATE SKIP LOCKED', [item.id])
            if not self.env.cr.fetchone():
                continue
            item.invalidate_recordset()
            if item.state == 'queued' or item.mail_id:
                continue
            attempt = item.attempts + 1
            try:
                with self.env.cr.savepoint():
                    if item.request_id.state != 'submitted':
                        raise ValidationError(_('La richiesta non è stata ricevuta.'))
                    recipients = item._recipients()
                    if not recipients:
                        raise ValidationError(_('Nessun destinatario email valido configurato.'))
                    template = self.env.ref('website_torrepulia_request.mail_request_' + item.kind)
                    mail_id = template.with_company(item.company_id).with_context(lang=item.request_id.lang).send_mail(
                        item.id, force_send=False, email_values={
                            'email_to': recipients, 'email_cc': False,
                            'recipient_ids': [fields.Command.clear()], 'recipient_cc_ids': [fields.Command.clear()],
                            'auto_delete': False,
                        })
                    item.write({'state': 'queued', 'mail_id': mail_id, 'attempts': attempt, 'error': False})
                    queued = True
            except (ConcurrencyError, TransactionRollbackError):
                raise
            except Exception as error:
                # Store a useful internal diagnostic without placing PII in logs.
                item.write({'state': 'failed', 'attempts': attempt, 'error': str(error)[:2000],
                            'retry_at': fields.Datetime.now() + timedelta(hours=1)})
        if queued:
            # Odoo's queue manager runs hourly: the receipt must not wait for it.
            self._trigger_cron('mail.ir_cron_mail_scheduler_action')

    @api.model
    def _trigger_cron(self, xmlid):
        # Wakes the cron worker at commit; the scheduled interval stays as the safety net.
        cron = self.env.ref(xmlid, raise_if_not_found=False)
        if cron:
            cron.sudo()._trigger()
