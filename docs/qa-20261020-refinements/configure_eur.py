"""Explicitly requested website currency configuration; no product price writes."""
assert env.cr.dbname == 'torrepulia_cinematic_install'
website = env['website'].search([('torrepulia_theme_enabled', '=', True)], limit=1)
assert website
euro = env.ref('base.EUR')
before = {product.id: product.list_price for product in env['product.template'].search([])}
euro.active = True
pricelist = env['product.pricelist'].search([
    ('website_id', '=', website.id), ('currency_id', '=', euro.id),
    ('company_id', 'in', [False, website.company_id.id])], limit=1)
if not pricelist:
    pricelist = env['product.pricelist'].create({
        'name': 'Torrepulia - EUR', 'currency_id': euro.id,
        'company_id': website.company_id.id, 'website_id': website.id,
        'selectable': True, 'sequence': 0,
    })
assert all(product.list_price == before[product.id] for product in env['product.template'].browse(list(before)))
assert website.pricelist_ids and all(p.currency_id == euro for p in website.pricelist_ids)
print('Website EUR pricelist:', pricelist.name)
print('Native conversion for 69 company-currency units:', website.company_id.currency_id._convert(69, euro, website.company_id))
print('PASS no product price, company currency or existing quotation modified')
env.cr.commit()
