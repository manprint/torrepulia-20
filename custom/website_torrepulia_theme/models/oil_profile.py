from odoo import fields, models
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
    lab = fields.Char('Laboratorio', help='Chi ha eseguito l\'analisi, per esempio il frantoio.')
    report_date = fields.Date('Data del rapporto di prova')
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

    def _torrepulia_source(self):
        self.ensure_one()
        parts = [self.name]
        if self.lab:
            parts.append(self.lab)
        if self.report_date:
            parts.append('Rapporto del %s' % format_date(self.env, self.report_date, date_format='d MMMM y'))
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

    def _torrepulia_shop_rows_enabled(self):
        """The shop lists one format per row; a request-only catalogue keeps the native grid."""
        self.ensure_one()
        return self.torrepulia_theme_enabled

    def _torrepulia_preorder_season(self):
        """Open new-oil season as {'url', 'label', 'title', 'text'}, else False; the campaign addon provides it."""
        self.ensure_one()
        return False
