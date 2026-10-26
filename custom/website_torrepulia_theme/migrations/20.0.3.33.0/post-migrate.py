from odoo import api, SUPERUSER_ID

from odoo.addons.website_torrepulia_theme.models.editorial_pages import recopy_privacy_policy, retext_refund_clause


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Refund on withdrawal as article 56 of the Codice del Consumo requires it.
    retext_refund_clause(env)
    # The privacy policy of what the site really processes, in place of the generic template.
    recopy_privacy_policy(env)
