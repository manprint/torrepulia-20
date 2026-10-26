from odoo import api, fields, models
from odoo.tools import format_date, formatLang

# Legal maximum for the extra virgin category (Reg. UE 2022/2104), used to draw
# each value to scale on the product page. Polyphenols and tocopherols have none.
EVO_LIMITS = {'acidity': 0.8, 'peroxides': 20.0, 'k232': 2.5, 'k270': 0.22}


class OilProfile(models.Model):
    _name = 'torrepulia.oil.profile'
    _description = "Carta d'identità dell'olio"
    _order = 'harvest_year desc, id desc'

    name = fields.Char('Nome', required=True, translate=True, help='Per esempio: Raccolto 2024.')
    harvest_year = fields.Integer('Anno del raccolto')
    cultivar = fields.Char('Cultivar', translate=True)
    origin = fields.Char('Uliveti', translate=True)
    harvest_period = fields.Char('Periodo di raccolta', translate=True)
    lab = fields.Char('Laboratorio', help='Chi ha eseguito l\'analisi. Resta interno: il sito scrive "il frantoio".')
    report_date = fields.Date('Data del rapporto di prova')
    report_url = fields.Char('Rapporto di prova (link)', help='Link al rapporto di prova intero, se non si carica il PDF.')
    report_file = fields.Binary('Rapporto di prova (PDF)', attachment=True,
        help='Il rapporto intero, pubblicato sul sito con le analisi. Prevale sul link.')
    report_filename = fields.Char('Nome del file')
    analysis_note = fields.Text("Nota sull'analisi", translate=True,
        help="Come è stata fatta l'analisi, mostrata sotto i valori su /l-olio. "
             'Per esempio: analisi rapida in frantoio, non di un laboratorio accreditato.')
    acidity = fields.Float('Acidità (% acido oleico)', digits=(6, 2))
    peroxides = fields.Float('Perossidi (meq O2/kg)', digits=(6, 2))
    k232 = fields.Float('K232', digits=(6, 2))
    k270 = fields.Float('K270', digits=(6, 2))
    polyphenols = fields.Float('Polifenoli totali (mg/kg)', digits=(8, 0))
    oleic_acid = fields.Float('Acido oleico (%)', digits=(6, 1))
    tocopherols = fields.Float('Tocoferoli totali (mg/kg)', digits=(8, 0))
    product_tmpl_ids = fields.One2many('product.template', 'torrepulia_oil_profile_id', string='Prodotti')

    def _torrepulia_facts(self):
        self.ensure_one()
        return [(label, value) for label, value in (
            ('Cultivar', self.cultivar), ('Uliveti', self.origin), ('Raccolta', self.harvest_period),
        ) if value]

    def _torrepulia_lab_rows(self):
        """Rows of the lab sheet; a value left at zero is not shown."""
        self.ensure_one()

        def number(value, digits):
            return formatLang(self.env, value, digits=digits)

        rows = []
        for key, label, digits, unit, limit_label in (
            ('acidity', 'Acidità', 2, ' %', '0,80 %'),
            ('peroxides', 'Perossidi', 2, ' meq O₂/kg', '20'),
            ('k232', 'K232', 2, '', '2,50'),
            ('k270', 'K270', 2, '', '0,22'),
            ('polyphenols', 'Polifenoli totali', 0, ' mg/kg', 'nessun limite'),
            ('oleic_acid', 'Acido oleico', 1, ' %', '55 - 83 %'),
            ('tocopherols', 'Tocoferoli', 0, ' mg/kg', 'nessun limite'),
        ):
            value = self[key]
            if not value:
                continue
            ratio = min(100, round(value / EVO_LIMITS[key] * 100)) if key in EVO_LIMITS else None
            rows.append({'label': label, 'value': number(value, digits) + unit, 'limit': limit_label, 'ratio': ratio})
        return rows

    def _torrepulia_report_link(self):
        self.ensure_one()
        if self.report_file:
            return '/torrepulia/analisi/%s/rapporto.pdf' % self.id
        return self.report_url or False

    def _torrepulia_value(self, key, digits, unit=''):
        self.ensure_one()
        return formatLang(self.env, self[key], digits=digits) + unit if self[key] else False

    def _torrepulia_report_day(self):
        self.ensure_one()
        return format_date(self.env, self.report_date, date_format='d MMMM y') if self.report_date else False

    @api.model
    def _torrepulia_season(self):
        # The harvest starts in October: from September the season is the new harvest's year.
        today = fields.Date.context_today(self)
        return today.year if today.month >= 9 else today.year - 1

    @api.model
    def _torrepulia_published_analysis(self):
        """Analysis shown on La Peranzana: the latest with values, never older than last season's harvest."""
        for profile in self.sudo().search([('harvest_year', '>=', self._torrepulia_season() - 1)]):
            if profile._torrepulia_lab_rows():
                return profile
        return self.browse()

    def _torrepulia_source(self):
        # The mill may change from one harvest to the next: the site never names it.
        self.ensure_one()
        parts = [self.name]
        if self.report_date:
            parts.append('Rapporto di prova del frantoio del %s' % format_date(
                self.env, self.report_date, date_format='d MMMM y'))
        return '. '.join(parts) + '.'


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    torrepulia_oil_profile_id = fields.Many2one('torrepulia.oil.profile', string="Carta d'identità dell'olio",
        ondelete='set null', help='Analisi e dati di raccolta mostrati sulla scheda prodotto.')

    def _torrepulia_oil_profile(self):
        # Public product pages read the profile; it carries no private data.
        self.ensure_one()
        return self.sudo().torrepulia_oil_profile_id


class Website(models.Model):
    _inherit = 'website'

    torrepulia_shipping_note = fields.Char('Nota spedizione sulla scheda prodotto', translate=True,
        default='Spedizione gratuita da 89 €, altrimenti 9,90 €. Consegna in 24-72 ore lavorative.')

    torrepulia_shop_available_label = fields.Char('Etichetta shop: disponibile', translate=True,
        default='Disponibile subito', help='Stato dei formati acquistabili subito. Vuoto: Disponibile subito.')
    torrepulia_shop_sold_out_label = fields.Char('Etichetta shop: esaurito', translate=True,
        default='Temporaneamente esaurito', help='Stato dei formati esauriti. Vuoto: Temporaneamente esaurito.')

    def _torrepulia_format_preorder(self, product):
        """Preorder destination of a format; the request bridge provides the real one."""
        self.ensure_one()
        return False

    def _torrepulia_preorder_available_from(self, product):
        """First delivery date of a reserved format, else False; the campaign addon provides it."""
        self.ensure_one()
        return False

    # Builder font values pointing at the self-hosted brand fonts: no Google Fonts request.
    TORREPULIA_FONTS = {'font': "'Manrope'", 'headings-font': "'Libre Caslon Display'",
                        'navbar-font': "'Manrope'", 'buttons-font': "'Manrope'"}

    def _torrepulia_use_local_fonts(self):
        for website in self:
            self.env['website.assets'].with_context(website_id=website.id).make_scss_customization(
                '/website/static/src/scss/options/user_values.scss', self.TORREPULIA_FONTS)

    def _torrepulia_shop_rows_enabled(self):
        """The shop lists one format per row; a request-only catalogue keeps the native grid."""
        self.ensure_one()
        return self.torrepulia_theme_enabled

    def _torrepulia_preorder_season(self):
        """Open new-oil season as {'url', 'label', 'title', 'text'}, else False; the campaign addon provides it."""
        self.ensure_one()
        return False
