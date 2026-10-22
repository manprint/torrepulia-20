"""Odoo 20 autonomous checkout boundary, separate from commercial quotations."""
from werkzeug.exceptions import abort

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain
from odoo.http import request
from odoo.tools import SQL, split_every


# Canonical matched routes, not the visitor's query string or language prefix.
# Audited against the installed website_sale and website_sale_stock controllers.
CHECKOUT_ROUTES = (
    '/shop/cart', '/shop/checkout', '/shop/address', '/shop/extra_info',
    '/shop/payment', '/shop/confirmation', '/shop/express_checkout', '/shop/express',
    '/shop/update_address', '/shop/delivery_methods', '/shop/set_delivery_method',
    '/shop/get_delivery_rate', '/shop/print', '/website_sale/set_delivery_date',
    '/website_sale_stock/set_pickup_location', '/website/form/shop.sale.order',
    '/my/orders/reorder', '/shop/claimreward', '/wallet/top_up', '/coupon',
)


def checkout_route(path):
    return any(path == prefix or path.startswith(prefix + '/') for prefix in CHECKOUT_ROUTES)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)
        if not checkout_route(rule.rule) or not request.env.website._torrepulia_request_enabled():
            return
        message = _('Il sito raccoglie richieste di preventivo. Il carrello e il checkout online sono sospesi.')
        if rule.endpoint.routing['type'] == 'jsonrpc':
            raise ValidationError(message)
        url = request.env.website._torrepulia_request_url()
        if request.httprequest.method in ('GET', 'HEAD'):
            response = request.redirect(url, code=303)
        else:
            response = request.make_json_response({'error': message, 'redirectUrl': url}, status=409)
        response.headers['Cache-Control'] = 'private, no-store'
        abort(response)


class Website(models.Model):
    _inherit = 'website'

    torrepulia_open_cart_count = fields.Integer('Carrelli e-commerce aperti', compute='_compute_open_carts',
        groups='base.group_system,sales_team.group_sale_manager')

    def _get_and_cache_current_cart(self):
        self.ensure_one()
        if self._torrepulia_request_enabled():
            # Do not resurrect, reprice, assign or reset a previous cart during
            # a GET/login. Preserve the original server session pointer for rollback.
            return self.env['sale.order'].browse()
        return super()._get_and_cache_current_cart()

    def _torrepulia_open_cart_domain(self):
        self.ensure_one()
        return [('website_id', '=', self.id), ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'sent']), ('order_line', '!=', False),
                ('torrepulia_request_id', '=', False)]

    @api.depends('company_id', 'torrepulia_commercial_mode')
    def _compute_open_carts(self):
        authorized = (self.env.user.has_group('base.group_system')
                      or self.env.user.has_group('sales_team.group_sale_manager'))
        for site in self:
            # Narrow aggregate only; no cart/customer details are elevated.
            site.torrepulia_open_cart_count = (
                self.env['sale.order'].sudo().search_count(site._torrepulia_open_cart_domain())
                if authorized and site.company_id in self.env.companies else 0)

    def action_torrepulia_open_carts(self):
        self.ensure_one()
        self.check_access('read')
        if (not self.env.user.has_group('sales_team.group_sale_manager')
                or self.company_id not in self.env.companies):
            raise AccessError(_('Solo il responsabile commerciale può consultare i carrelli del sito.'))
        return {'type': 'ir.actions.act_window', 'name': _('Carrelli e-commerce aperti'),
                'res_model': 'sale.order', 'view_mode': 'list,form',
                'domain': self._torrepulia_open_cart_domain()}

    @api.model
    def _cron_send_abandoned_cart_email(self):
        # Native Odoo 20 algorithm with one extra website-domain condition.
        # Filtering AFTER _filter_can_send... would incorrectly mark suspended
        # carts as already mailed. Exclude them before grouping instead.
        sites = Domain([('send_abandoned_cart_followup', '=', True),
                        ('cart_recovery_mail_template_id', '!=', False),
                        ('torrepulia_commercial_mode', '!=', 'request')])
        groups = self.env['sale.order']._read_group(
            Domain([('is_abandoned_cart', '=', True), ('website_id', 'in', sites),
                    ('cart_recovery_email_sent', '=', False)]) & Domain.custom(
                to_sql=lambda table: SQL('%s >= %s', table.date_order,
                    table._join('website_id').send_abandoned_cart_email_activation_time)),
            groupby=['website_id'], aggregates=['id:recordset', 'id:count'])
        if not groups:
            return
        self.env['ir.cron']._commit_progress(remaining=sum(count for _site, _cart, count in groups))
        for _site, cart_group, _count in groups:
            allowed = cart_group._filter_can_send_abandoned_cart_followup().filtered('partner_id.email')
            failed = cart_group - allowed
            failed.write({'cart_recovery_email_sent': True})
            self.env['ir.cron']._commit_progress(len(failed))
            for batch in split_every(10, allowed.ids, self.env['sale.order'].browse):
                batch._cart_recovery_email_send()
                self.env['ir.cron']._commit_progress(len(batch))


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    torrepulia_open_cart_count = fields.Integer(related='website_id.torrepulia_open_cart_count')

    def action_torrepulia_open_carts(self):
        self.ensure_one()
        return self.website_id.action_torrepulia_open_carts()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _torrepulia_suspended_catalog_carts(self):
        # Native eCommerce provenance is stored by Odoo, not an HTTP flag.
        # Issue 7 creates backend quotations with assigned_website_id and no
        # eCommerce website_id. The structured request link is server validated.
        return self.filtered(lambda order: order.state in ('draft', 'sent') and order.website_id
            and order.website_id._torrepulia_request_enabled() and not order.torrepulia_request_id)

    def _torrepulia_check_cart_checkout(self):
        if self._torrepulia_suspended_catalog_carts():
            raise ValidationError(_('Il checkout del carrello è sospeso. Rivolgiti al commerciale per un preventivo.'))

    def _cart_add(self, *args, **kwargs):
        self._torrepulia_check_cart_checkout()
        return super()._cart_add(*args, **kwargs)

    def _cart_update_line_quantity(self, *args, **kwargs):
        self._torrepulia_check_cart_checkout()
        return super()._cart_update_line_quantity(*args, **kwargs)

    def _validate_order(self):
        self._torrepulia_check_cart_checkout()
        return super()._validate_order()

    def action_recovery_email_send(self):
        self._torrepulia_check_cart_checkout()
        return super().action_recovery_email_send()

    def _cart_recovery_email_send(self):
        allowed = self - self._torrepulia_suspended_catalog_carts()
        if allowed:
            return super(SaleOrder, allowed)._cart_recovery_email_send()


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model_create_multi
    def create(self, vals_list):
        # Isolate the postcondition even if an internal caller catches the
        # validation error: no orphan transaction may remain in that transaction.
        with self.env.cr.savepoint():
            transactions = super().create(vals_list)
            # Native controllers already verify document tokens and construct
            # links; check the actual order before any charge/processing call.
            transactions.sale_order_ids._torrepulia_check_cart_checkout()
        return transactions
