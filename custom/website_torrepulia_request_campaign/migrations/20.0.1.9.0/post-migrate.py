"""Reservation flow: the oil is paid on the order confirmation, before it leaves.

Texts saved on the campaigns that still say "paid on shipping" give way to the
new defaults (an empty field uses them); any other wording stays.
"""
from odoo import api, SUPERUSER_ID

PAID_ON_SHIPPING = {
    'payment_note': ('nessun anticipo, paghi alla spedizione', 'alla spedizione, zero anticipo'),
    'shop_band_text': ('prenotazioni aperte: lo moliamo entro 8 ore dalla raccolta e te lo spediamo appena è pronto. paghi alla spedizione.',
                       'prenotazioni aperte. lo moliamo e lo spediamo entro 48 ore, paghi alla spedizione.'),
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for campaign in env['torrepulia.request.campaign'].search([]):
        for code, _name in env['res.lang'].get_installed():
            localized = campaign.with_context(lang=code)
            for field, old in PAID_ON_SHIPPING.items():
                if (localized[field] or '').strip().lower() in old:
                    localized[field] = False
