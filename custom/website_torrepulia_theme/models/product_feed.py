"""The Google Merchant Center feed of Odoo (/gmc.xml) for the Torrepulia site.

Same facts as the product markup (models/seo.py): reserved formats are preorders with their
first delivery date, the brand is the website, and a product without a sales description
gets the same fallback description as its page.
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

from odoo import models

from .seo import _product_description

ROME = ZoneInfo('Europe/Rome')


class ProductFeed(models.Model):
    _inherit = 'product.feed'

    def _prepare_gmc_items(self):
        items = super()._prepare_gmc_items()
        if self.website_id.torrepulia_theme_enabled:
            for product, item in items.items():
                if not item.get('description'):
                    item['description'] = _product_description(product.product_tmpl_id)
        return items

    def _prepare_gmc_stock_info(self, product):
        info = super()._prepare_gmc_stock_info(product)
        website = self.website_id
        if website.torrepulia_theme_enabled and website._torrepulia_format_preorder(product):
            # Odoo says out_of_stock for a format of the open campaign: it is reserved, not sold out.
            info['availability'] = 'preorder'
        return info

    def _prepare_gmc_additional_info(self, product):
        info = super()._prepare_gmc_additional_info(product)
        website = self.website_id
        if not website.torrepulia_theme_enabled:
            return info
        direct = [pair for pair in info['gmc_direct_attributes'] if pair[0] not in ('brand', 'availability_date')]
        direct.append(('brand', website.name))
        # Required by Merchant Center for a preorder: the first delivery day, Italian time.
        if website._torrepulia_format_preorder(product) and (day := website._torrepulia_preorder_available_from(product)):
            direct.append(('availability_date', datetime.combine(day, time(), ROME).strftime('%Y-%m-%dT%H:%M%z')))
        info['gmc_direct_attributes'] = direct
        return info
