import json

from odoo.tests import TransactionCase, tagged
from odoo.addons.website_sale.tests.common import MockRequest

from ..controllers.reservation import TorrepuliaReservationForm, reservation_errors


@tagged('post_install', '-at_install')
class TestTorrepuliaReservation(TransactionCase):
    def valid_values(self):
        return {
            'torrepulia_reservation': '2026/2027', 'name': 'Prenotazione olio nuovo 2026/2027',
            'contact_name': 'Reservation QA', 'email_from': 'reservation-qa@local.invalid',
            'phone': '+390000000000', 'delivery_address': 'Torremaggiore 71017',
            'privacy_accepted': 'on', 'bib_filtrato': '1', 'bib_non_filtrato': '0',
            'latta_filtrata': '2', 'latta_non_filtrata': '0',
        }

    def test_reservation_validation(self):
        self.assertFalse(reservation_errors(self.valid_values()))
        for name, invalid in [('email_from', 'invalid'), ('privacy_accepted', ''),
                              ('phone', ''), ('delivery_address', ''), ('contact_name', ''),
                              ('bib_filtrato', '-1'), ('bib_filtrato', '1.5'), ('bib_filtrato', '101')]:
            with self.subTest(name=name, invalid=invalid):
                values = dict(self.valid_values(), **{name: invalid})
                self.assertIn(name, reservation_errors(values))
        values = dict(self.valid_values(), bib_filtrato='0', latta_filtrata='0')
        self.assertIn('bib_filtrato', reservation_errors(values))

    def test_native_crm_storage_and_company(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        values = self.valid_values()
        with MockRequest(self.env(context=dict(self.env.context, lang='en_US')), website=website):
            result = json.loads(TorrepuliaReservationForm()._handle_website_form('crm.lead', **values))
        self.assertIn('id', result, result)
        lead = self.env['crm.lead'].browse(result['id'])
        self.assertEqual(lead.company_id, website.company_id)
        self.assertEqual(lead.contact_name, values['contact_name'])
        self.assertEqual(lead.email_from, values['email_from'])
        self.assertEqual(lead.lang_id.code, 'en_US')
        self.assertIn('bib_filtrato', lead.description)
        self.assertIn('latta_filtrata', lead.description)
        self.assertIn('71017', lead.description)

    def test_invalid_reservation_creates_no_lead(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        before = self.env['crm.lead'].search_count([])
        with MockRequest(self.env, website=website):
            result = json.loads(TorrepuliaReservationForm()._handle_website_form(
                'crm.lead', **dict(self.valid_values(), privacy_accepted='')))
        self.assertIn('privacy_accepted', result['error_fields'])
        self.assertEqual(self.env['crm.lead'].search_count([]), before)

    def test_reservation_subject_also_enforces_validation(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        values = dict(self.valid_values(), privacy_accepted='')
        values.pop('torrepulia_reservation')
        with MockRequest(self.env, website=website):
            result = json.loads(TorrepuliaReservationForm()._handle_website_form('crm.lead', **values))
        self.assertIn('privacy_accepted', result['error_fields'])
