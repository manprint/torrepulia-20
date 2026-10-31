from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Earlier versions created a draft on every page view: the empty ones go now, not over days.
    while env['torrepulia.request'].search_count([('state', '=', 'draft'), ('line_ids', '=', False)]):
        before = env['torrepulia.request'].search_count([('state', '=', 'draft')])
        env['torrepulia.request']._cron_expire_drafts()
        if env['torrepulia.request'].search_count([('state', '=', 'draft')]) == before:
            break
