from markupsafe import Markup

from odoo import _, fields, models
from odoo.tools.misc import format_amount

# 25/10: the product pages still described the oil of before the owner's words ("fruttato
# medio", "oliva appena colta", grass and wheat). Only a text with one of these changes.
OLD_SENSORY_MARKS = ('appena colta', 'grano', 'erba', 'Fruttato Medio', 'fruttato medio ', 'fruttato medio.')
PRODUCT_SENSORY = Markup('<p>Un fruttato medio-intenso, elegante e armonico. Al naso arriva prima il verde del pomodoro '
                         'e del carciofo, poi la mandorla fresca. In bocca &#232; morbido e rotondo: amaro e piccante '
                         'delicati e ben bilanciati, finale pulito.</p>')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    torrepulia_web_title = fields.Char('Titolo della scheda Torrepulia', translate=True, default='La Regina',
        help="Lasciare vuoto per usare il nome del prodotto.")
    torrepulia_denomination = fields.Char('Denominazione', translate=True, default='Olio extravergine di oliva Peranzana',
        help="Sottotitolo della scheda, prima del contenuto. Vuoto: solo formato e contenuto.")
    torrepulia_sensory_profile = fields.Html('Profilo sensoriale', translate=True)
    torrepulia_food_pairings = fields.Html('Abbinamenti in cucina', translate=True)
    torrepulia_shipping_storage = fields.Html('Spedizione e conservazione', translate=True)

    def _torrepulia_retext_sensory(self):
        """Sensory profile in the words of 25/10, in every language; the old text stays in the chatter."""
        for code, _name in self.env['res.lang'].get_installed():
            for template in self.with_context(lang=code).search([('torrepulia_sensory_profile', '!=', False)]):
                current = template.torrepulia_sensory_profile or ''
                if not any(mark in current for mark in OLD_SENSORY_MARKS):
                    continue
                template.message_post(body=Markup('Profilo sensoriale (%s) prima del testo del 25/10:<br/>%s') % (code, current),
                                      subtype_xmlid='mail.mt_note')
                template.torrepulia_sensory_profile = PRODUCT_SENSORY


class Website(models.Model):
    _inherit = 'website'

    def _cinematic_products(self, ids=None):
        products = super()._cinematic_products(ids)
        excluded = self.env.context.get('torrepulia_exclude_template_id')
        return products.filtered(lambda product: product.id != excluded) if excluded else products

    def _torrepulia_format_preorder(self, product):
        return self._torrepulia_preorder_product_url(product)

    def _request_review_shipping(self, products_total, currency):
        # The review counts shipping as the checkout does: same carrier, free over the same threshold.
        shipping = super()._request_review_shipping(products_total, currency)
        carrier = self._torrepulia_shipping_carrier() if self.torrepulia_theme_enabled else False
        if not carrier:
            return shipping
        free = bool(carrier.free_over and products_total >= carrier.amount)
        cost = 0 if free else carrier.fixed_price
        shipping.update({
            'shipping_display': _('Gratuita') if free else format_amount(self.env, cost, currency),
            'estimated_total_display': format_amount(self.env, products_total + cost, currency),
        })
        if carrier.free_over and not free and carrier.amount > 0:
            shipping.update({
                'free_shipping_gap_display': format_amount(self.env, carrier.amount - products_total, currency),
                'free_shipping_progress': min(round(products_total / carrier.amount * 100), 100),
            })
        return shipping

    def _torrepulia_shop_rows_enabled(self):
        # A request-only catalogue keeps the native tiles with their request controls.
        return super()._torrepulia_shop_rows_enabled() and not self._torrepulia_request_enabled()
