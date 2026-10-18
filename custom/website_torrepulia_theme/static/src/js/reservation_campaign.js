import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';
import { ProductPage } from '@website_sale/interactions/product_page';

class ReservationQuantity extends Interaction {
    static selector = '.tp-reservation-configurator form';
    dynamicContent = {
        '.css_quantity > button': { 't-on-click.prevent': this.incOrDecQuantity },
        '.tp-reservation-quantity input': { 't-on-input': this.validateSelection, 't-on-change': this.validateSelection },
    };
    start() {
        this.validateSelection();
        this.registerCleanup(() => this.el.querySelectorAll('.tp-reservation-quantity input').forEach(input => input.setCustomValidity('')));
    }
    incOrDecQuantity(ev) {
        ProductPage.prototype.incOrDecQuantity.call(this, ev);
        this.validateSelection();
    }
    _updateMinusButtonTitle(input) {
        ProductPage.prototype._updateMinusButtonTitle.call(this, input);
    }
    validateSelection() {
        const inputs = [...this.el.querySelectorAll('.tp-reservation-quantity input')];
        inputs[0]?.setCustomValidity(inputs.some(input => Number(input.value) > 0)
            ? '' : _t('Scegli almeno una confezione per inviare la prenotazione.'));
    }
}
registry.category('public.interactions').add('torrepulia.reservation.quantity', ReservationQuantity);
