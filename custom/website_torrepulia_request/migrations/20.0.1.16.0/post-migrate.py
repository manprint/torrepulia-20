"""Request emails: subject computed per request (reservation or request).

The templates are noupdate: change only a subject still equal to the
shipped one, in every installed language. Edited subjects stay.
"""
from odoo import api, SUPERUSER_ID

SHIPPED = {
    'mail_request_customer': 'Richiesta ricevuta {{ object.request_id.name }}',
    'mail_request_internal': 'Richiesta sito web {{ object.request_id.name }}',
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, shipped in SHIPPED.items():
        template = env.ref('website_torrepulia_request.' + xmlid, raise_if_not_found=False)
        for code, _name in env['res.lang'].get_installed() if template else []:
            localized = template.with_context(lang=code)
            if localized.subject == shipped:
                localized.subject = '{{ object._mail_subject() }}'
