from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Campaign(models.Model):
    _name = 'torrepulia.request.campaign'
    _description = 'Vetrina stagionale Torrepulia'
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(required=True, translate=True)
    reference = fields.Char(required=True, index=True, copy=False)
    website_id = fields.Many2one('website', required=True, ondelete='cascade', default=lambda self: self.env['website'].get_current_website())
    company_id = fields.Many2one(related='website_id.company_id', store=True, index=True)
    state = fields.Selection([('closed', 'Chiusa'), ('open', 'Aperta')], required=True, default='closed')
    opens_at = fields.Datetime('Apertura dal')
    closes_at = fields.Datetime('Chiusura al')
    delivery_period = fields.Char('Periodo indicativo di consegna', translate=True)
    introduction = fields.Text('Testo editoriale', translate=True,
        default='Filtrato o non filtrato, anche insieme: scegli le quantità per ogni formato.')
    shipping_note = fields.Char('Indicazione spedizione', translate=True)
    payment_note = fields.Char('Indicazione pagamento', translate=True)
    price_note = fields.Char('Indicazione prezzo', translate=True,
        help='Condizione editoriale approvata dal gestore. Non modifica né blocca i prezzi dei preventivi Odoo.')
    closed_message = fields.Text('Messaggio campagna chiusa', required=True, translate=True,
        default='La campagna non è aperta. Puoi continuare a scegliere i prodotti dal catalogo.')
    line_ids = fields.One2many('torrepulia.request.campaign.line', 'campaign_id', string='Prodotti e varianti')
    shop_state_label = fields.Char('Etichetta dei formati in prenotazione', translate=True,
        help="Stato dei formati della campagna nello shop. Vuoto: Raccolto <anno> · in prenotazione.")
    shop_band_title = fields.Char('Titolo della fascia nello shop', translate=True,
        help='Vuoto: Olio nuovo <anno>.')
    shop_band_text = fields.Char('Testo della fascia nello shop', translate=True,
        help='Vuoto: Prenotazioni aperte: lo moliamo entro 8 ore dalla raccolta e te lo spediamo appena è pronto. Paghi alla spedizione.')

    _unique_reference = models.Constraint('UNIQUE(website_id, reference)', 'Il riferimento deve essere univoco per website.')

    @api.constrains('opens_at', 'closes_at', 'website_id', 'line_ids')
    def _check_campaign(self):
        for campaign in self:
            if campaign.opens_at and campaign.closes_at and campaign.opens_at >= campaign.closes_at:
                raise ValidationError(_('La chiusura deve seguire l’apertura.'))
            assigned = self.env['website'].search([('torrepulia_campaign_id', '=', campaign.id)])
            if assigned - campaign.website_id:
                raise ValidationError(_('La campagna predefinita non può essere spostata su un altro website.'))
            campaign.line_ids._check_catalog()

    def _is_open(self):
        self.ensure_one()
        now = fields.Datetime.now()
        return (self.state == 'open' and (not self.opens_at or self.opens_at <= now)
                and (not self.closes_at or now < self.closes_at))


class CampaignLine(models.Model):
    _name = 'torrepulia.request.campaign.line'
    _description = 'Formato della campagna'
    _order = 'sequence, id'
    _check_company_auto = True

    campaign_id = fields.Many2one('torrepulia.request.campaign', required=True, ondelete='cascade')
    website_id = fields.Many2one(related='campaign_id.website_id', store=True)
    company_id = fields.Many2one(related='campaign_id.company_id', store=True)
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one('product.product', string='Prodotto / variante', required=True, ondelete='restrict', check_company=True)
    content = fields.Char('Contenuto della confezione', translate=True,
        help='Descrizione editoriale. Non determina prezzi, unità di misura o attributi.')
    description = fields.Text('Descrizione pratica', translate=True)

    _unique_variant = models.Constraint('UNIQUE(campaign_id, product_id)', 'La variante è già presente nella campagna.')

    @api.constrains('product_id', 'campaign_id')
    def _check_catalog(self):
        for line in self:
            product = line.product_id
            website = line.campaign_id.website_id
            if product and (not product.sale_ok or product.company_id and product.company_id != website.company_id
                            or product.website_id and product.website_id != website):
                raise ValidationError(_('Scegli un prodotto vendibile del website e della sua azienda.'))


class Website(models.Model):
    _inherit = 'website'

    torrepulia_campaign_id = fields.Many2one('torrepulia.request.campaign', string='Campagna stagionale predefinita',
        domain="[('website_id', '=', id)]", check_company=True, copy=False)
    torrepulia_campaign_page_backup = fields.Json(groups='base.group_system', copy=False, readonly=True)

    @api.constrains('torrepulia_campaign_id', 'company_id')
    def _check_selected_campaign(self):
        for website in self:
            if website.torrepulia_campaign_id and website.torrepulia_campaign_id.website_id != website:
                raise ValidationError(_('La campagna deve appartenere a questo website.'))

    def _request_preorder_url(self):
        self.ensure_one()
        if not self._torrepulia_selection_enabled():
            return False
        campaign = self._public_request_campaign()
        return '/prenotailtuoolio' if campaign and campaign._is_open() else False

    def _torrepulia_seasonal_open(self):
        return bool(self._request_preorder_url())

    def _torrepulia_preorder_product_url(self, product):
        """Hybrid mode: products of the open default campaign are reserved, not bought."""
        self.ensure_one()
        if self._torrepulia_request_enabled() or not product or not (url := self._request_preorder_url()):
            return False
        products = self._public_request_campaign().line_ids.product_id
        if product._name == 'product.template':
            return url if product.id in products.product_tmpl_id.ids else False
        return url if product.id in products.ids else False

    def _torrepulia_preorder_season(self):
        """Shop band of the open default campaign, hybrid mode only."""
        self.ensure_one()
        if self._torrepulia_request_enabled() or not (url := self._request_preorder_url()):
            return False
        campaign = self._public_request_campaign()
        year = (campaign.opens_at or fields.Datetime.now()).year
        return {'url': url,
                'label': campaign.shop_state_label or _('Raccolto %s · in prenotazione', year),
                'title': campaign.shop_band_title or _('Olio nuovo %s', year),
                'text': campaign.shop_band_text or _('Prenotazioni aperte: lo moliamo entro 8 ore dalla raccolta e te lo spediamo appena è pronto. Paghi alla spedizione.')}

    def _request_receipt_context(self):
        """Hybrid mode: a request sent while the default campaign is open is a reservation.

        Same facts and defaults as the campaign page, frozen at submission.
        """
        context = super()._request_receipt_context()
        if self._torrepulia_request_enabled() or not self._request_preorder_url():
            return context
        campaign = self._public_request_campaign()
        facts = [(_('Consegna'), campaign.delivery_period),
                 (_('Prezzo'), campaign.price_note or _('Bloccato per tutta la stagione')),
                 (_('Pagamento'), campaign.payment_note or _('Alla spedizione, zero anticipo'))]
        return dict(context, reservation={
            'season': (campaign.opens_at or fields.Datetime.now()).year,
            'facts': [[label, value] for label, value in facts if value]})

    def _public_request_campaign(self, campaign_id=None):
        """Only a website/company scoped editorial projection; no public model ACL.

        The elevated record is never returned to the client, and products must be
        re-read in the visitor environment before rendering any product data.
        """
        self.ensure_one()
        if not self.has_ecommerce_access():
            return self.env['torrepulia.request.campaign']
        selected = campaign_id or self.sudo().torrepulia_campaign_id.id
        if type(selected) is not int or selected <= 0:
            return self.env['torrepulia.request.campaign']
        return self.env['torrepulia.request.campaign'].sudo().search([
            ('id', '=', selected), ('website_id', '=', self.id), ('company_id', '=', self.company_id.id)], limit=1)
