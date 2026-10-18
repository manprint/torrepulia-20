import json
import re

from odoo import tools
from odoo.http import request
from odoo.addons.website_crm.controllers.website_form import WebsiteForm


QUANTITIES = ('bib_filtrato', 'bib_non_filtrato', 'latta_filtrata', 'latta_non_filtrata')


def reservation_errors(values):
    errors = [name for name in ('contact_name', 'email_from', 'phone', 'delivery_address')
              if not str(values.get(name, '')).strip()]
    if values.get('email_from') and not tools.email_normalize(values['email_from']):
        errors.append('email_from')
    if values.get('privacy_accepted') not in ('on', 'true', '1'):
        errors.append('privacy_accepted')
    quantities = []
    for name in QUANTITIES:
        value = str(values.get(name, '0'))
        if not re.fullmatch(r'[0-9]{1,3}', value) or not 0 <= int(value) <= 100:
            errors.append(name)
        else:
            quantities.append(int(value))
    if not errors and not any(quantities):
        errors.append(QUANTITIES[0])
    return errors


class TorrepuliaReservationForm(WebsiteForm):
    def _handle_website_form(self, model_name, **kwargs):
        if (model_name == 'crm.lead' and request.env.website.torrepulia_theme_enabled
                and (kwargs.get('torrepulia_reservation') == '2026/2027'
                     or kwargs.get('name') == 'Prenotazione olio nuovo 2026/2027')):
            if errors := reservation_errors(kwargs):
                return json.dumps({'error_fields': errors})
        # Native website_form retains CAPTCHA, model permissions, visitor,
        # company/language attribution and storage of custom reservation fields.
        return super()._handle_website_form(model_name, **kwargs)
