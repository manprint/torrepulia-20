from datetime import date

from odoo import api, SUPERUSER_ID

# Owner-supplied test report: Frantoio Sacco Oliveti, 19 November 2024.
HARVEST_2024 = {
    'name': 'Raccolto 2024', 'harvest_year': 2024, 'cultivar': 'Peranzana, 100%',
    'origin': 'Alto Tavoliere, Torremaggiore', 'harvest_period': 'Ottobre e novembre',
    'lab': 'Frantoio Sacco Oliveti, Torremaggiore', 'report_date': date(2024, 11, 19),
    'acidity': 0.17, 'peroxides': 4.91, 'k232': 1.87, 'k270': 0.12,
    'polyphenols': 588.98, 'oleic_acid': 70.23, 'tocopherols': 243.55,
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    profiles = env['torrepulia.oil.profile']
    profile = profiles.search([('harvest_year', '=', 2024)], limit=1) or profiles.create(HARVEST_2024)
    env['product.template'].with_context(active_test=False).search([
        ('torrepulia_format_name', '!=', False), ('torrepulia_oil_profile_id', '=', False),
    ]).torrepulia_oil_profile_id = profile
