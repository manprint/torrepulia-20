from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestFooter(HttpCase):
    def test_footer_reads_company_data_and_active_payments(self):
        website = self.env['website'].search([], limit=1)
        website.torrepulia_theme_enabled = True
        website.company_id.write({
            'name': 'Azienda agricola di prova', 'vat': 'IT00722360716',
            'email': 'prova@example.com', 'phone': '+39 000 000 0000',
            'social_instagram': 'https://www.instagram.com/prova', 'social_facebook': False,
        })
        providers = website._torrepulia_footer_payments()
        page = self.url_open('/shop').text
        self.assertIn('P. IVA 00722360716', page)
        self.assertIn('Azienda agricola di prova', page)
        self.assertIn('mailto:prova@example.com', page)
        self.assertIn('https://www.instagram.com/prova', page)
        self.assertNotIn('>Facebook<', page)
        self.assertIn('Termini di vendita', page)
        self.assertIn('Spedizione e pagamento', page)
        for name in providers:
            self.assertIn(name.lower(), page.lower())
