import json
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged

from ..models.editorial_pages import add_review_privacy


@tagged('post_install', '-at_install')
class TestReviewRequest(TransactionCase):
    """The review request leaves a few days after the oil, once per order."""

    def setUp(self):
        super().setUp()
        # Odoo's cron commits its progress: not inside a test transaction (as in website_sale's tests).
        progress = patch.object(self.env.registry['ir.cron'], '_commit_progress', return_value=float('inf'))
        progress.start()
        self.addCleanup(progress.stop)
        self.website = self.env['website'].search([], limit=1)
        self.website.write({
            'torrepulia_theme_enabled': True, 'send_order_rating_emails': True, 'rating_email_delay': 7,
            'rating_email_template_id': self.env.ref('website_torrepulia_theme.mail_order_review').id,
            'torrepulia_google_review_url': 'https://g.page/r/torrepulia/review'})
        self.partner = self.env['res.partner'].create({'name': 'Maria Rossi', 'email': 'maria@example.invalid'})
        self.product = self.env['product.product'].create({
            'name': 'Latta di prova', 'type': 'consu', 'list_price': 69, 'is_published': True, 'website_id': self.website.id})

    def shipped_order(self, days_ago, website=None):
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id, 'website_id': (website or self.website).id,
            'order_line': [fields.Command.create({'product_id': self.product.id, 'product_uom_qty': 1})]})
        order.action_confirm()
        for picking in order.picking_ids:
            for move in picking.move_ids:
                move.write({'quantity': move.product_uom_qty, 'picked': True})
            picking._action_done()
            picking.date_done = fields.Datetime.now() - timedelta(days=days_ago)
        return order

    def sent(self, order):
        # Only the review request: confirming the order sends its own email.
        return self.env['mail.mail'].search_count([('model', '=', 'sale.order'), ('res_id', '=', order.id),
                                                   ('subject', 'ilike', 'Com%è La Regina')])

    def test_days_run_from_the_shipment_once(self):
        tasted, travelling = self.shipped_order(8), self.shipped_order(2)
        # Confirmed long ago (bank transfer, reservation): the order date does not count.
        tasted.date_order = travelling.date_order = fields.Datetime.now() - timedelta(days=30)
        self.env['sale.order']._cron_send_order_rating_emails()
        self.assertEqual(self.sent(tasted), 1)
        self.assertTrue(tasted.torrepulia_review_sent)
        self.assertEqual(self.sent(travelling), 0)
        self.env['sale.order']._cron_send_order_rating_emails()  # Never twice.
        self.assertEqual(self.sent(tasted), 1)
        mail = self.env['mail.mail'].search([('model', '=', 'sale.order'), ('res_id', '=', tasted.id),
                                             ('subject', 'ilike', 'Com%è La Regina')])
        self.assertEqual(mail.subject, "Com'è La Regina? Raccontacelo in un minuto")
        self.assertIn('https://g.page/r/torrepulia/review', mail.body_html)
        self.assertIn('Com&#8217;è La Regina, Maria?', mail.body_html.replace('’', '&#8217;'))
        self.assertIn('Ti scriviamo una sola volta', mail.body_html)

    def test_an_order_not_fully_shipped_waits(self):
        order = self.shipped_order(10)
        order.order_line[0].product_uom_qty = 2  # One more pack: a second delivery, still to leave.
        self.assertTrue(order.picking_ids.filtered(lambda picking: picking.state != 'done'))
        self.env['sale.order']._cron_send_order_rating_emails()
        self.assertEqual(self.sent(order), 0)

    def test_other_websites_keep_odoo_timing(self):
        other = self.env['website'].create({'name': 'Altro sito', 'send_order_rating_emails': True, 'rating_email_delay': 0})
        self.assertFalse(other.torrepulia_theme_enabled)
        order = self.shipped_order(0, website=other)
        self.env['sale.order']._cron_send_order_rating_emails()
        self.assertTrue(order.is_rating_email_sent)
        self.assertFalse(order.torrepulia_review_sent)

    def test_privacy_policy_tells_about_the_review_request_once(self):
        view = self.env['ir.ui.view'].create({'name': 'Privacy', 'type': 'qweb', 'arch': '<t t-name="privacy"><p>x</p></t>',
                                              'key': 'website_torrepulia_theme.test_review_privacy'})
        saved = ('<t t-name="privacy"><section class="tp-section tp-legal"><div class="container tp-reading">'
                 '<h3>Avviso di disponibilità</h3><p>Avviso.</p><h3>Statistiche e marketing</h3><p>GA4.</p></div></section></t>')
        self.env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps({'en_US': saved}), view.id])
        page = self.env['website.page'].search([('url', '=', '/privacy-policy')], limit=1)
        if page:
            page.view_id = view
        else:
            self.env['website.page'].create({'url': '/privacy-policy', 'view_id': view.id, 'website_id': self.website.id})
        add_review_privacy(self.env)
        add_review_privacy(self.env)
        self.env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        arch = self.env.cr.fetchone()[0]['en_US']
        self.assertEqual(arch.count('Richiesta di recensione'), 1)
        self.assertLess(arch.index('Richiesta di recensione'), arch.index('Statistiche e marketing'))
        self.assertGreater(arch.index('Richiesta di recensione'), arch.index('Avviso.'))
