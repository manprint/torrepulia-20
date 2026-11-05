from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import add_analysis_2026, extraction_at_21_everywhere


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Our cold extraction runs at 21 °C, not below 27 °C: pages, guides, product texts, /llms.txt.
    extraction_at_21_everywhere(env)
    # The test report of the 2026 harvest: /l-olio and the formats still on the 2024 card.
    add_analysis_2026(env)
