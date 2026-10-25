import { patch } from '@web/core/utils/patch';
import { PortalPrepayment } from '@sale/interactions/portal_prepayment';

// Odoo 20 reads data-is-partially-paid as a string, and "false" is truthy: the payment window
// opened on every visit of the order confirmation, even after the bank transfer was chosen.
patch(PortalPrepayment.prototype, {
    setup() {
        super.setup();
        const params = new URLSearchParams(window.location.search);
        this.showPaymentModal = params.has('payment_amount') || params.has('amount_selection')
            || this.el.dataset.isPartiallyPaid === 'true';
    },
});
