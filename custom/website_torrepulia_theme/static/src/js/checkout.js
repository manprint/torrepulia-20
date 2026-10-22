import { patch } from '@web/core/utils/patch';
import { PortalAdditionalIdentifiers } from '@account/interactions/portal_additional_identifiers';
import { PaymentForm } from '@payment/interactions/payment_form';

// Odoo 20 rebuilds this dropdown on country change with an untranslated label.
patch(PortalAdditionalIdentifiers.prototype, {
    _buildDropdown(metadata) {
        const dropdown = super._buildDropdown(metadata);
        if (this.el.closest('.tp-site')) {
            dropdown.querySelector('button').lastChild.textContent = 'Aggiungi un identificativo fiscale';
        }
        return dropdown;
    },
});

// A bank transfer is paid after the order: confirm it, do not "pay now".
patch(PaymentForm.prototype, {
    _isPayLaterPaymentMethod(paymentMethodCode) {
        return (paymentMethodCode === 'wire_transfer' && Boolean(this.el.closest('.tp-site')))
            || super._isPayLaterPaymentMethod(...arguments);
    },
});
