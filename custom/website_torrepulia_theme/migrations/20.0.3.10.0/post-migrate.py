from odoo import api, SUPERUSER_ID

# Approved Phase 2 direction: one sentence per format on the shop rows.
AUDIENCE = {
    'bottles': "Per la tavola di ogni giorno e per chi vuole regalare La Regina.",
    'tin': "La scorta di famiglia. La latta protegge l'olio dalla luce per tutta la stagione.",
    'box': "Per chi usa molto olio a crudo. La sacca si comprime mentre si svuota e l'aria non entra.",
}


def audience_key(product):
    name = '%s %s' % (product.torrepulia_format_name or '', product.name or '')
    name = name.lower()
    if 'bag' in name:
        return 'box'
    if 'latt' in name:
        return 'tin'
    if 'bottigl' in name or product.torrepulia_unit_count in (2, 6):
        return 'bottles'
    return None


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    products = env['product.template'].with_context(active_test=False).search([
        ('torrepulia_format_name', '!=', False), ('torrepulia_shop_audience', '=', False)])
    for product in products:
        if key := audience_key(product):
            product.torrepulia_shop_audience = AUDIENCE[key]
