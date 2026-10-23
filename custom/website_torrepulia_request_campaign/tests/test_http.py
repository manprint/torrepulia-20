import json
import secrets
from unittest.mock import patch

from lxml import html

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCampaignHttp(HttpCase):
    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        team = self.env['crm.team'].create({'name': 'Campaign HTTP team', 'company_id': self.website.company_id.id})
        self.website.write({'torrepulia_theme_enabled': True, 'torrepulia_request_team_id': team.id,
            'torrepulia_commercial_mode': 'request', 'torrepulia_request_show_prices': True})
        self.products = self.env['product.product'].create([
            {'name': 'Campaign HTTP filtered', 'is_published': True, 'list_price': 71.25},
            {'name': 'Campaign HTTP second', 'is_published': True, 'list_price': 38.50},
            {'name': 'Catalog outside campaign', 'is_published': True}])
        self.campaign = self.env['torrepulia.request.campaign'].create({
            'name': 'HTTP campaign', 'reference': 'http-test', 'website_id': self.website.id, 'state': 'open',
            'line_ids': [fields.Command.create({'product_id': product.id, 'sequence': index,
                'content': 'Contenuto verificato dal gestore'}) for index, product in enumerate(self.products[:2])]})
        self.website.torrepulia_campaign_id = self.campaign

    def content(self, suffix=''):
        response = self.url_open('/torrepulia/campaign/content' + suffix)
        self.assertEqual(response.status_code, 200, response.text[:200])
        self.assertIn('no-store', response.headers['Cache-Control'])
        return response.json()

    def update(self, operation, product, qty):
        bootstrap = self.url_open('/torrepulia/request/current').json()
        payload = {'operation': operation, 'operation_id': secrets.token_hex(16),
            'selection_id': bootstrap['state']['selection_id'], 'revision': bootstrap['state']['revision'],
            'product_id': product.id, 'quantity': qty}
        response = self.url_open('/torrepulia/request/update', data={
            'csrf_token': bootstrap['csrf_token'], 'payload': json.dumps(payload)})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['state']

    def test_integrated_form_and_required_seasonal_contacts(self):
        result = self.url_open('/torrepulia/request/form?layout=campaign')
        self.assertEqual(result.status_code, 200)
        self.assertIn('private',result.headers['Cache-Control'])
        tree = html.fromstring(result.content)
        form = tree.xpath('//form')[0]
        self.assertEqual(form.get('action'),'/torrepulia/campaign/submit')
        self.assertFalse(form.xpath('.//*[@data-review-lines]'))
        self.assertTrue(form.xpath('.//*[@data-review-compact-lines]'))
        for name in ('phone','delivery_area'):
            self.assertTrue(form.xpath('.//input[@name="%s" and @required]' % name))
        self.assertIn('Riepilogo Prenotazione',result.text)
        state = self.update('set_configuration',self.products[0],2)
        bootstrap=self.url_open('/torrepulia/request/current').json()
        counts={model:self.env[model].search_count([]) for model in ('crm.lead','sale.order','res.partner')}
        payload={'selection_id':state['selection_id'],'revision':state['revision'],
            'operation_id':secrets.token_hex(16),'contact_name':'Seasonal guest',
            'email':'seasonal-summary@example.invalid','privacy_accepted':True,'phone':'','delivery_area':''}
        def send():
            return self.url_open('/torrepulia/campaign/submit',data={
                'csrf_token':bootstrap['csrf_token'],'payload':json.dumps(payload)})
        rejected=send()
        self.assertEqual(rejected.status_code,422)
        self.assertEqual(set(rejected.json()['fields']),{'phone','delivery_area'})
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state']['quantity'],2)
        for model,count in counts.items():self.assertEqual(self.env[model].search_count([]),count)
        payload.update(phone='+1 202-555-0123',delivery_area='Torremaggiore (FG)')
        with patch.object(type(self.env['ir.mail_server']),'send_email',return_value='<seasonal-test@example.invalid>'):
            submitted=send()
            self.assertEqual(submitted.status_code,200,submitted.text)
            self.assertEqual(send().json()['reference'],submitted.json()['reference'])
        self.assertEqual(self.env['crm.lead'].search_count([]),counts['crm.lead']+1)
        self.assertEqual(self.env['sale.order'].search_count([]),counts['sale.order'])
        record=self.env['torrepulia.request'].search([('selection_id','=',state['selection_id'])])
        self.assertIn('Torremaggiore (FG)',record.opportunity_id.description)

    def test_cards_prices_set_quantities_keep_other_products_no_crm(self):
        reference_unit = self.env['product.base.unit'].create({'name': 'L'})
        self.products[0].write({'base_unit_id': reference_unit.id, 'base_unit_count': 5})
        self.website.show_product_reference_price = True
        counts = {model: self.env[model].search_count([]) for model in ('sale.order', 'crm.lead', 'res.partner')}
        content = self.content()
        self.assertTrue(content['open'])
        tree = html.fromstring(content['html'])
        # Facts read the campaign; no certification-like claim, no hard-coded season.
        self.assertEqual(tree.xpath('//dl[@class="tp-campaign-facts"]//dt/text()'), ['Prezzo', 'Pagamento'])
        self.assertIn('Alla spedizione, zero anticipo', tree.text_content())
        self.assertEqual(len(tree.xpath('//section[@class="tp-campaign-steps"]//li')), 3)
        self.assertNotIn('FILIERA PROTETTA', content['html'])
        self.assertNotIn('2026/2027', tree.text_content())
        self.assertNotIn('tp-campaign-assurances', content['html'])
        cards = tree.xpath('//*[@data-campaign-config]')
        self.assertEqual([json.loads(card.get('data-campaign-config'))['product_id'] for card in cards], self.products[:2].ids)
        self.assertEqual(len(tree.xpath('//input[@type="number"]')), 2)
        self.assertFalse(tree.xpath('//input[@type="radio"] | //form'))
        self.assertIn('71.25', content['html'])
        self.assertIn('14.25', content['html'])
        self.assertIn('L</span>', content['html'])
        self.assertNotIn('Completa la tua prenotazione', content['html'])
        self.assertNotIn('data-campaign-review', content['html'])
        self.update('add', self.products[2], 4)
        self.update('add', self.products[0], 2)
        state = self.update('set_configuration', self.products[0], 3)
        self.assertEqual(state['quantity'], 7)
        self.assertEqual(sorted(line['quantity'] for line in state['lines']), [3, 4])
        self.update('set_configuration', self.products[1], 1)
        self.assertEqual(self.url_open('/torrepulia/request/preview').json()['state']['quantity'], 8)
        self.website.torrepulia_request_show_prices = False
        hidden = self.content()['html']
        self.assertNotIn('71.25', hidden)
        self.assertNotIn('71,25', hidden)
        self.assertNotIn('product_price', hidden)
        self.assertNotIn('14.25', hidden)
        for model, count in counts.items():
            self.assertEqual(self.env[model].search_count([]), count, model)
        self.assertEqual(self.products[0].list_price, 71.25)

    def test_closed_isolation_archive_and_public_demo_denied(self):
        self.update('add', self.products[0], 2)
        self.campaign.write({'state': 'closed', 'closed_message': 'Chiusura configurata dal gestore'})
        closed = self.content()
        self.assertFalse(closed['open'])
        self.assertIn('Chiusura configurata dal gestore', closed['html'])
        self.assertNotIn('class="tp-campaign-quantity"', closed['html'])
        self.assertIn(self.products[0].id, [config['product_id'] for config in closed['configurations']])
        self.assertIn('/shop', closed['html'])
        # Closed showcase does not disable normal catalog operations.
        self.assertEqual(self.update('add', self.products[2], 1)['quantity'], 3)
        other = self.env['website'].create({'name': 'Other campaign website', 'company_id': self.website.company_id.id})
        foreign = self.env['torrepulia.request.campaign'].create({'name': 'Private other website title',
            'reference': 'other', 'website_id': other.id, 'introduction': 'Other website editorial'})
        foreign_data = self.content('?campaign_id=%s' % foreign.id)
        self.assertIsNone(foreign_data['campaign_reference'])
        self.assertNotIn('Other website editorial', foreign_data['html'])
        self.assertEqual(self.url_open('/torrepulia/campaign/content?demo=1').status_code, 403)
        self.campaign.state = 'open'
        self.products[0].active = False
        self.assertNotIn('Campaign HTTP filtered', self.content()['html'])
        state = self.url_open('/torrepulia/request/current').json()['state']
        self.assertFalse(next(line for line in state['lines'] if line['product_id'] == self.products[0].id)['available'])

    def test_retired_form_no_lead_and_seasonal_page_has_no_form(self):
        leads = self.env['crm.lead'].search_count([])
        response = self.url_open('/website/form/crm.lead', data={
            'torrepulia_reservation': '2026/2027', 'name': 'Prenotazione olio nuovo 2026/2027',
            'contact_name': 'Campaign Test', 'email_from': 'campaign-test@example.invalid',
            'phone': '0000', 'delivery_address': 'Test', 'privacy_accepted': 'on', 'bib_filtrato': '2'})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn('error', response.json())
        self.assertEqual(self.env['crm.lead'].search_count([]), leads)
        self.website._install_request_campaign_pages()
        page = self.url_open('/prenotailtuoolio')
        self.assertEqual(page.status_code, 200)
        tree = html.fromstring(page.text)
        self.assertTrue(tree.xpath('//section[@data-snippet="s_torrepulia_request_campaign"]'))
        self.assertFalse(tree.xpath('//form[@data-model_name="crm.lead"]'))
        self.assertNotIn('bib_filtrato', page.text)
        self.assertIn('Prenota il tuo olio del nuovo raccolto', page.text)

    def test_editor_preview_is_authenticated_and_has_no_personal_data(self):
        state = self.update('add', self.products[0], 7)
        editor = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Campaign Editor QA', 'login': 'campaign-editor@example.invalid',
            'password': 'CampaignOnlyTestPassword',
            'group_ids': [fields.Command.set(self.env.ref('website.group_website_designer').ids)]})
        self.authenticate(editor.login, 'CampaignOnlyTestPassword')
        before = self.url_open('/torrepulia/request/current').json()['state']
        demo = self.content('?demo=1')
        self.assertIn('Anteprima dimostrativa', demo['html'])
        self.assertNotIn('71.25', demo['html'])
        self.assertNotIn(state['selection_id'], demo['html'])
        tree = html.fromstring(demo['html'])
        self.assertTrue(tree.xpath('//input[@value="0" and @disabled]'))
        self.assertEqual(self.url_open('/torrepulia/request/current').json()['state'], before)
