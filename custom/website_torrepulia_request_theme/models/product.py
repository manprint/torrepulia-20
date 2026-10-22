from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    torrepulia_web_title = fields.Char('Titolo della scheda Torrepulia', translate=True, default='La Regina',
        help="Lasciare vuoto per usare il nome del prodotto.")
    torrepulia_sensory_profile = fields.Html('Il Profilo Sensoriale', translate=True)
    torrepulia_food_pairings = fields.Html('Abbinamenti in Cucina', translate=True)
    torrepulia_shipping_storage = fields.Html('Spedizione e Conservazione', translate=True)


class Website(models.Model):
    _inherit = 'website'

    def _cinematic_products(self, ids=None):
        products = super()._cinematic_products(ids)
        excluded = self.env.context.get('torrepulia_exclude_template_id')
        return products.filtered(lambda product: product.id != excluded) if excluded else products

    def _torrepulia_format_preorder(self, product):
        return self._torrepulia_preorder_product_url(product)

    def _torrepulia_shop_rows_enabled(self):
        # A request-only catalogue keeps the native tiles with their request controls.
        return super()._torrepulia_shop_rows_enabled() and not self._torrepulia_request_enabled()
