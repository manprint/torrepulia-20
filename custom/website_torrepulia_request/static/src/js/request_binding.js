import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';

/** Same binding contract for catalog, product, seasonal, header and summary.
 * Configuration lives in markup; visitor state only lives in memory/input.value.
 * Never write personal state into dataset, defaultValue or saved snippet HTML.
 */
export class RequestSelectionBinding extends Interaction {
    static selector = '[data-tp-request]';
    dynamicContent = {
        '[data-tp-request-add]': { 't-on-click.prevent': this.add },
        '[data-tp-request-quantity]': { 't-on-change': this.setQuantity },
        '[data-tp-request-remove]': { 't-on-click.prevent': this.remove },
        '[data-tp-request-clear]': { 't-on-click.prevent': this.clear },
        '[data-tp-request-retry]': { 't-on-click.prevent': this.retry },
    };

    start() {
        this.active = true;
        this.store = this.services['torrepulia.request'];
        this.initial = [...this.el.querySelectorAll('[data-tp-request-count], [data-tp-request-quantity], [data-tp-request-message]')]
            .map(element => ({ element, text: element.textContent, value: element.value }));
        this.registerCleanup(() => {
            this.active = false;
            for (const { element, text, value } of this.initial) {
                element.textContent = text;
                if (value !== undefined) {
                    element.value = value;
                }
            }
        });
        this.registerCleanup(this.store.subscribe(state => this.renderState(state)));
        return this.store.read().catch(() => {
            if (this.active) {
                this.message(_t('Impossibile leggere la selezione. Riprova.'));
            }
        });
    }

    configuration(element) {
        const owner = element.closest('[data-tp-request-config]') || this.el;
        return JSON.parse(owner.dataset.tpRequestConfig || '{}');
    }

    sameConfiguration(line, config) {
        return line.product_id === config.product_id && line.uom_id === (config.uom_id || line.default_uom_id) &&
            JSON.stringify([...line.no_variant_value_ids].sort((a, b) => a - b)) ===
            JSON.stringify([...(config.no_variant_value_ids || [])].sort((a, b) => a - b)) &&
            JSON.stringify(Object.entries(line.custom_values).sort()) ===
            JSON.stringify(Object.entries(config.custom_values || {}).map(([key, value]) =>
                [key, typeof value === 'string' ? value.trim() : value]).sort());
    }

    renderState(state) {
        if (!this.active) {
            return;
        }
        for (const element of this.el.querySelectorAll('[data-tp-request-count]')) {
            element.textContent = String(state.quantity);
        }
        for (const input of this.el.querySelectorAll('[data-tp-request-quantity]')) {
            const config = this.configuration(input);
            const line = state.lines.find(line => input.dataset.tpRequestLine
                ? line.key === input.dataset.tpRequestLine : this.sameConfiguration(line, config));
            input.value = String(line?.quantity || 0);
        }
        for (const link of this.el.querySelectorAll('[data-tp-request-link]')) {
            // URL is website configuration, never a visitor quantity or token.
            link.setAttribute('href', state.summary_url);
        }
        const warnings = state.lines.filter(line => line.warning).map(line => line.warning);
        this.message(warnings.join(' '));
    }

    message(text) {
        for (const node of this.el.querySelectorAll('[data-tp-request-message]')) {
            node.textContent = text;
        }
    }

    async perform(action) {
        try {
            await action();
        } catch (error) {
            if (!this.active) {
                return;
            }
            if (this.store.state) {
                this.renderState(this.store.state);
            }
            this.message(error.code === 'conflict'
                ? _t('La selezione è cambiata in un’altra pagina. Controlla le quantità e riprova.')
                : ['network', 'pending'].includes(error.code)
                    ? _t('Esito non confermato. Usa Riprova per verificare la stessa operazione senza duplicarla.')
                    : error.code === 'invalid' ? error.message : _t('Impossibile aggiornare la selezione. Riprova.'));
        }
    }

    add(event) {
        return this.perform(() => this.store.add(this.configuration(event.currentTarget),
            Number(event.currentTarget.dataset.tpRequestAdd || 1)));
    }

    setQuantity(event) {
        const input = event.currentTarget;
        return this.perform(() => input.dataset.tpRequestLine
            ? this.store.setQuantity(input.dataset.tpRequestLine, input.value)
            : this.store.setConfiguration(this.configuration(input), input.value));
    }

    remove(event) {
        return this.perform(() => this.store.remove(event.currentTarget.dataset.tpRequestRemove));
    }

    clear() {
        return this.perform(() => this.store.clear());
    }

    retry() {
        return this.perform(() => this.store.retryPending());
    }
}

// Deliberately absent from public.interactions.edit: Builder saves configuration,
// never a visitor's selection. Interaction cleanup restores initial placeholders.
registry.category('public.interactions').add('torrepulia.request.selection', RequestSelectionBinding);
