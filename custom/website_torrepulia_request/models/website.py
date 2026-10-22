import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlsplit
from psycopg2.errors import UniqueViolation

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, ConcurrencyError


class Website(models.Model):
    _inherit = 'website'

    torrepulia_commercial_mode = fields.Selection([
        ('shop', 'Acquisto online standard'), ('request', 'Richiesta di preventivo'),
        ('hybrid', 'Acquisto online + prenotazione stagionale'),
    ], required=True, default='shop')
    torrepulia_request_show_prices = fields.Boolean('Mostra prezzi nelle richieste', default=True)
    torrepulia_request_team_id = fields.Many2one('crm.team', string='Team destinatario')
    torrepulia_request_user_id = fields.Many2one('res.users', string='Assegnatario predefinito')
    torrepulia_request_summary_url = fields.Char(
        'Pagina di riepilogo richiesta', required=True, default='/la-tua-richiesta')
    torrepulia_request_draft_days = fields.Integer('Conservazione bozze (giorni)', default=30, required=True)
    torrepulia_request_min_qty = fields.Float('Quantità minima per configurazione', default=1, required=True)
    torrepulia_request_max_qty = fields.Float('Quantità massima per configurazione', default=1000, required=True)
    torrepulia_request_qty_step = fields.Float('Incremento quantità', default=1, required=True)

    @api.constrains('torrepulia_commercial_mode', 'torrepulia_request_team_id',
                    'torrepulia_request_user_id', 'company_id',
                    'torrepulia_request_summary_url', 'torrepulia_request_draft_days')
    def _check_torrepulia_request_settings(self):
        for site in self:
            team, user = site.torrepulia_request_team_id, site.torrepulia_request_user_id
            if site.torrepulia_commercial_mode in ('request', 'hybrid') and not team:
                raise ValidationError(_('Scegliere un team destinatario per le richieste.'))
            if team and (not team.active or team.company_id and team.company_id != site.company_id):
                raise ValidationError(_('Il team deve essere attivo e appartenere all’azienda del website.'))
            if user and (not team or not user.active or user.share
                         or site.company_id not in user.company_ids
                         or user not in (team.member_ids | team.user_id)):
                raise ValidationError(_('L’assegnatario deve appartenere al team e all’azienda del website.'))
            url = site.torrepulia_request_summary_url or ''
            parsed = urlsplit(url)
            if (not url.startswith('/') or url.startswith('//') or parsed.scheme or parsed.netloc
                    or parsed.query or parsed.fragment or '\\' in url
                    or any(c.isspace() or ord(c) < 32 for c in url) or '%' in url):
                raise ValidationError(_('Il riepilogo deve essere un percorso locale senza parametri.'))
            if not 1 <= site.torrepulia_request_draft_days <= 365:
                raise ValidationError(_('La conservazione delle bozze deve essere tra 1 e 365 giorni.'))

    def _torrepulia_request_url(self):
        self.ensure_one()
        return self.torrepulia_request_summary_url

    def _torrepulia_request_enabled(self):
        """Whole catalogue collected as requests: cart and checkout are suspended."""
        self.ensure_one()
        return self.torrepulia_commercial_mode == 'request'

    def _torrepulia_selection_enabled(self):
        """Private selection, review and CRM submission are available.

        In hybrid mode the native shop keeps its checkout and only seasonal
        preorders use the selection.
        """
        self.ensure_one()
        return self.torrepulia_commercial_mode in ('request', 'hybrid')

    def _torrepulia_preorder_product_url(self, product):
        """Hybrid-mode preorder destination for a product or variant, else False.

        The base addon knows no seasonal campaign; the campaign addon overrides it.
        """
        self.ensure_one()
        return False

    def _torrepulia_selection_allows(self, product):
        self.ensure_one()
        return self._torrepulia_request_enabled() or bool(self._torrepulia_preorder_product_url(product))

    def _torrepulia_request_prices_visible(self):
        self.ensure_one()
        return not self._torrepulia_request_enabled() or self.torrepulia_request_show_prices

    def _torrepulia_request_partner(self):
        self.ensure_one()
        partner = self.env.user.partner_id
        if self.env.user._is_public() or partner.company_id and partner.company_id != self.company_id:
            return self.env['res.partner']
        return partner

    def _torrepulia_session_request(self, session, *, create=False):
        """Server-only capability boundary. Never accept a request ID from a visitor.

        Call on the current website in the actual visitor environment. A future
        HTTP adapter must use request.session and retain Odoo's CSRF protection.
        No contact, lead, cart or order is created here.
        """
        self.ensure_one()
        if not self._torrepulia_selection_enabled() or not self.has_ecommerce_access():
            return self.env['torrepulia.request']
        key = 'torrepulia_request_%s' % self.id
        token = session.get(key)
        if not isinstance(token, str) or len(token) != 64:
            if not create:
                return self.env['torrepulia.request']
            token = secrets.token_hex(32)
        # Only an unguessable secret stored server-side grants draft access.
        drafts = self.env['torrepulia.request'].sudo().with_company(self.company_id)
        for generation in range(8):
            digest = hashlib.sha256(token.encode()).hexdigest()
            self.env.cr.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', ['torrepulia:' + digest])
            candidate = drafts.search([
                ('session_digest', '=', digest), ('website_id', '=', self.id),
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            if candidate and candidate.state == 'draft' and candidate.last_activity >= fields.Datetime.now() - timedelta(days=self.torrepulia_request_draft_days):
                session[key] = token
                return candidate
            if not create:
                return drafts.browse()
            if candidate:
                # Deterministic rotation also handles simultaneous first writes
                # after expiry/submission without losing one tab's selection.
                token = hashlib.sha256((token + ':next').encode()).hexdigest()
                continue
            # Read team/user config under a narrowly scoped elevation: public users
            # cannot read arbitrary sales teams or users.
            config = self.sudo()
            config._check_torrepulia_request_settings()
            values = {
                'website_id': self.id,
                'lang': self.env.lang or self.default_lang_id.code,
                'session_digest': digest,
                'partner_id': self._torrepulia_request_partner().id or False,
                'team_id': config.torrepulia_request_team_id.id,
                'user_id': config.torrepulia_request_user_id.id,
            }
            try:
                with self.env.cr.savepoint():
                    draft = drafts.create(values)
            except UniqueViolation as error:
                # Under REPEATABLE READ a contender may have acquired its
                # snapshot before the advisory lock. Retry through Odoo's native
                # whole-transaction concurrency handler with a fresh snapshot.
                raise ConcurrencyError('Concurrent Torrepulia draft initialization') from error
            session[key] = token
            return draft
        raise ValidationError(_('Ricaricare la selezione prima di continuare.'))


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    torrepulia_commercial_mode = fields.Selection(related='website_id.torrepulia_commercial_mode', readonly=False)
    torrepulia_request_show_prices = fields.Boolean(related='website_id.torrepulia_request_show_prices', readonly=False)
    torrepulia_request_team_id = fields.Many2one(related='website_id.torrepulia_request_team_id', readonly=False)
    torrepulia_request_user_id = fields.Many2one(related='website_id.torrepulia_request_user_id', readonly=False)
    torrepulia_request_allowed_user_ids = fields.Many2many('res.users', compute='_compute_request_allowed_users')
    torrepulia_request_summary_url = fields.Char(related='website_id.torrepulia_request_summary_url', readonly=False)
    torrepulia_request_draft_days = fields.Integer(related='website_id.torrepulia_request_draft_days', readonly=False)
    torrepulia_request_min_qty = fields.Float(related='website_id.torrepulia_request_min_qty', readonly=False)
    torrepulia_request_max_qty = fields.Float(related='website_id.torrepulia_request_max_qty', readonly=False)
    torrepulia_request_qty_step = fields.Float(related='website_id.torrepulia_request_qty_step', readonly=False)

    @api.depends('torrepulia_request_team_id', 'website_company_id')
    def _compute_request_allowed_users(self):
        for config in self:
            team = config.torrepulia_request_team_id
            config.torrepulia_request_allowed_user_ids = (team.member_ids | team.user_id).filtered(
                lambda user: user.active and not user.share and config.website_company_id in user.company_ids)
