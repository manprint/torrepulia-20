import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { CartService } from '@website_sale/js/cart_service';
import { ProductPage } from '@website_sale/interactions/product_page';

export const requestMode = () => document.body.dataset.tpRequestMode === '1';
let showMessage = () => {};

export function nativeConfiguration(product, info) {
    return {
        product_id: product.productId || info.product_id,
        uom_id: Number.isInteger(product.uomId) ? product.uomId : info.uom_id,
        no_variant_value_ids: product.noVariantAttributeValues || [],
        custom_values: Object.fromEntries((product.productCustomAttributeValues || []).map(value =>
            [String(value.custom_product_template_attribute_value_id), value.custom_value])),
    };
}

if (!CartService.dependencies.includes('torrepulia.request')) {
    CartService.dependencies.push('torrepulia.request');
}
patch(CartService.prototype, {
    setup(env, services) {
        this.requestSelection = services['torrepulia.request'];
        return super.setup(...arguments);
    },
    async add(product, options = {}) {
        if (!requestMode()) {
            return super.add(...arguments);
        }
        try {
            const store = this.requestSelection;
            await store.read();
            const response = await fetch(`/torrepulia/request/product?template_id=${encodeURIComponent(product.productTemplateId)}`,
                { credentials: 'same-origin', cache: 'no-store' });
            const info = await response.json();
            if (!response.ok) {
                throw new Error(info.error);
            }
            if (info.requires_configuration && !options.isConfigured) {
                // No variant is chosen and no quantity added before this explicit step.
                window.location.assign(`${info.url}${info.url.includes('?') ? '&' : '?'}tp_request_qty=${encodeURIComponent(product.quantity ?? 1)}`);
                return 0;
            }
            if (!product.productId && info.requires_configuration) {
                const resolved = await fetch('/torrepulia/request/resolve', {
                    method: 'POST', credentials: 'same-origin', cache: 'no-store',
                    body: new URLSearchParams({ csrf_token: store.csrfToken, payload: JSON.stringify({
                        template_id: product.productTemplateId,
                        ptav_ids: [...(product.ptavs || []), ...(product.noVariantAttributeValues || [])],
                    }) }),
                });
                const result = await resolved.json();
                if (!resolved.ok) {
                    throw new Error(result.error);
                }
                product = { ...product, productId: result.product_id };
            }
            const config = nativeConfiguration(product, info);
            const quantity = product.quantity ?? 1;
            const state = await store.add(config, quantity);
            const line = state.lines.find(row => row.product_id === config.product_id && row.uom_id === config.uom_id);
            showMessage(quantity === 1
                ? _t('Aggiunta 1 confezione di %s.', line?.name || info.name)
                : _t('Aggiunte %s confezioni di %s.', quantity, line?.name || info.name), false, state.addition);
            // The native interaction must not fire cart analytics/wishlist removal.
            return 0;
        } catch (error) {
            showMessage(['network', 'pending'].includes(error.code)
                ? _t('Esito non confermato. Usa Riprova per verificare la stessa aggiunta senza duplicarla.')
                : error.code === 'conflict'
                    ? _t('La selezione è cambiata. Controlla le quantità e riprova.')
                    : error.message || _t('Impossibile aggiungere il prodotto alla richiesta.'), true);
            return 0;
        }
    },
});

function hideStockNotification(parent, combination) {
    // Native stock policy controls the shop. Seasonal preorders use their
    // separate set_configuration path and never this product-page interaction.
    if (combination.tp_request_stock_notice?.preorder_url && combination.is_storable
            && !combination.allow_out_of_stock_order && combination.free_qty < 1) {
        // Avoid a second primary action alongside the seasonal preorder.
        parent.querySelector('#out_of_stock_buttons_wrapper')?.classList.add('d-none');
    }
}

patch(ProductPage.prototype, {
    async _onChangeCombination(event, parent, combination, images) {
        if (!requestMode()) {
            // Standard or hybrid shop: native cart, plus the seasonal link when sold out.
            const result = await super._onChangeCombination(...arguments);
            hideStockNotification(parent, combination);
            return result;
        }
        const input = parent.querySelector('input[name="add_qty"]');
        const desired = input?.value;
        await super._onChangeCombination(...arguments);
        hideStockNotification(parent, combination);
        const limits = this.services['torrepulia.request'].state?.limits;
        if (input) {
            const stockLimited = combination.is_storable && !combination.allow_out_of_stock_order;
            const maximum = Math.min(limits?.max || 1000,
                stockLimited ? Number(input.dataset.max || 1) : Infinity);
            input.dataset.tpRequestStockMax = stockLimited ? String(maximum) : '';
            input.dataset.max = String(maximum);
            input.dataset.min = String(limits?.min || 1);
            input.step = String(limits?.step || 1);
            if (!stockLimited) input.value = desired;
        }
    },
    async _getUnavailableQty(combination) {
        // A legacy ecommerce cart must not reduce availability of the separate request.
        return requestMode() ? 0 : super._getUnavailableQty(...arguments);
    },
});

export class RequestCommerce extends Interaction {
    static selector = '#wrapwrap';
    dynamicContent = {
        '[data-request-clear]': { 't-on-click.prevent': this.clear },
    };

    async start() {
        if (!requestMode()) {
            return;
        }
        this.active = true;
        this.store = this.services['torrepulia.request'];
        for (const group of this.el.querySelectorAll('.tp-catalog-variants')) {
            const name = `tp-variant-${crypto.randomUUID()}`;
            for (const input of group.querySelectorAll('input')) input.name = name;
        }
        this.addListener(this.el, 'click', event => {
            if (event.target.matches('.tp-catalog-variant-input')) {
                const group = event.target.closest('.tp-catalog-variants');
                for (const input of group.querySelectorAll('input')) input.checked = input === event.target;
                const row = group.closest('.tp-request-action-row');
                const soldOut = event.target.dataset.soldOut === '1';
                row.querySelector('.tp-catalog-quantity').hidden = soldOut;
                row.querySelector('[data-tp-request-add-template]').hidden = soldOut;
                for (const message of row.querySelectorAll('[data-stock-variant]')) {
                    message.hidden = !soldOut || message.dataset.stockVariant !== event.target.value;
                }
            }
            const step = event.target.closest('[data-catalog-step]');
            if (step) {
                event.preventDefault();
                if (!this.store.state?.limits) return;
                const input = step.closest('.tp-request-action-row').querySelector('.tp-catalog-quantity-input');
                const { min, max, step: increment } = this.store.state.limits;
                input.value = String(Math.round(Math.min(max, Math.max(min,
                    Number(input.value || min) + Number(step.dataset.catalogStep) * increment)) * 1e9) / 1e9);
                return;
            }
            const button = event.target.closest('[data-tp-request-add-template]');
            if (button) {
                event.preventDefault();
                const input = button.closest('.tp-request-action-row')?.querySelector('.tp-catalog-quantity-input');
                if (input && !input.reportValidity()) return;
                const row = button.closest('.tp-request-action-row');
                const variants = row?.querySelector('.tp-catalog-variants');
                const selected = variants?.querySelector('input:checked');
                if (variants && !selected) { variants.querySelector('input').reportValidity(); return; }
                if (button.disabled) return;
                button.disabled = true;
                this.services.cart.add({ productTemplateId: Number(button.dataset.tpRequestAddTemplate),
                    ...(selected ? { productId: Number(selected.value) } : {}), quantity: input ? Number(input.value) : 1 },
                    { isConfigured: Boolean(selected) }).finally(() => { button.disabled = false; });
            }
        });
        this.createConfirmation();
        this.registerCleanup(this.store.subscribe(state => this.update(state)));
        this.registerCleanup(() => { this.active = false; showMessage = () => {}; });
        await this.store.read().catch(() => showMessage(_t('Impossibile leggere la richiesta. Riprova.'), true));
        const desired = Number(new URLSearchParams(window.location.search).get('tp_request_qty'));
        const limits = this.store.state?.limits;
        const input = this.el.querySelector('.o_wsale_product_page input[name="add_qty"]');
        if (input && limits && Number.isFinite(desired) && desired >= limits.min && desired <= limits.max
                && Math.abs(desired / limits.step - Math.round(desired / limits.step)) < 1e-8) {
            input.value = String(desired);
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    createConfirmation() {
        const doc = this.el.ownerDocument;
        const aside = doc.createElement('aside');
        aside.className = 'tp-request-confirmation';
        aside.setAttribute('role', 'status');
        aside.setAttribute('aria-live', 'polite');
        aside.hidden = true;
        const title = doc.createElement('h2');
        title.textContent = _t('Prodotto aggiunto alla richiesta');
        const message = doc.createElement('p');
        const subtotal = doc.createElement('p'); subtotal.className = 'tp-confirmation-subtotal'; subtotal.hidden = true;
        const note = doc.createElement('p'); note.className = 'tp-confirmation-note';
        note.textContent = _t('(Importo da pagare oggi: 0,00 €; pagamento al momento della spedizione)');
        const actions = doc.createElement('div');
        actions.className = 'tp-request-confirmation-actions';
        const close = doc.createElement('button');
        close.type = 'button'; close.className = 'btn btn-outline-secondary';
        close.textContent = _t('Continua a scegliere');
        const review = doc.createElement('a');
        review.className = 'btn btn-primary'; review.textContent = _t('Vai al riepilogo');
        review.href = document.body.dataset.tpRequestSummaryUrl;
        const retry = doc.createElement('button');
        retry.type = 'button'; retry.className = 'btn btn-outline-secondary'; retry.textContent = _t('Riprova'); retry.hidden = true;
        actions.append(close, review, retry); aside.append(title, message, subtotal, note, actions);
        this.el.append(aside);
        this.addListener(close, 'click', () => { aside.hidden = true; });
        this.addListener(retry, 'click', async () => {
            try {
                const state = await this.store.retryPending();
                showMessage(_t('Richiesta aggiornata. Puoi continuare a scegliere.'), false, state.addition);
            } catch {
                showMessage(_t('Impossibile verificare l’aggiunta. Riprova.'), true);
            }
        });
        showMessage = (text, error, addition) => {
            if (!this.active) return;
            title.textContent = error ? _t('Richiesta da verificare') : _t('✓ AGGIUNTO ALLA RICHIESTA');
            message.textContent = addition ? _t('Hai inserito %s confezioni di: %s', addition.quantity, addition.name) : text;
            subtotal.hidden = !addition?.subtotal_display;
            subtotal.textContent = addition?.subtotal_display ? _t('Subtotale: %s', addition.subtotal_display) : '';
            note.hidden = Boolean(error);
            retry.hidden = !this.store.pending; aside.hidden = false;
        };
        this.registerCleanup(() => aside.remove());
    }

    update(state) {
        if (!this.active) return;
        for (const input of this.el.querySelectorAll('.tp-catalog-quantity-input')) {
            input.min = String(state.limits.min);
            input.max = String(state.limits.max);
            input.step = String(state.limits.step);
        }
        for (const input of this.el.querySelectorAll('.o_wsale_product_page input[name="add_qty"]')) {
            input.dataset.min = String(state.limits.min);
            input.dataset.max = String(Math.min(state.limits.max, Number(input.dataset.tpRequestStockMax || Infinity)));
            input.step = String(state.limits.step);
        }
        for (const link of this.el.querySelectorAll('[data-tp-request-header]')) {
            link.href = state.summary_url;
            const quantity = new Intl.NumberFormat(document.documentElement.lang || 'it').format(state.quantity);
            link.setAttribute('aria-label', state.quantity === 1 ? _t('La tua richiesta, 1 confezione') : _t('La tua richiesta, %s confezioni', quantity));
            link.querySelector('[data-tp-request-header-count]').textContent = quantity;
        }
        if (this.el.querySelector('[data-tp-request-summary]')) {
            this.renderSummary().catch(() => showMessage(_t('Impossibile aggiornare il riepilogo. Riprova.'), true));
        }
    }

    async clear() {
        await this.store.clear().catch(error => showMessage(error.message, true));
    }

    async renderSummary() {
        const ticket = this.summaryTicket = (this.summaryTicket || 0) + 1;
        const response = await fetch('/torrepulia/request/preview', { credentials: 'same-origin', cache: 'no-store' });
        const { state } = await response.json();
        if (!this.active || ticket !== this.summaryTicket || state.revision < this.store.state.revision) return;
        const holder = this.el.querySelector('[data-request-lines]');
        const doc = holder.ownerDocument;
        holder.replaceChildren();
        for (const line of state.lines) {
            const row = doc.createElement('div'); row.className = 'tp-request-line';
            const title = doc.createElement('h2'); title.textContent = line.name;
            const label = doc.createElement('label'); label.textContent = _t('Quantità');
            const input = doc.createElement('input'); input.type = 'number'; input.min = '0';
            input.step = String(state.limits.step); input.max = String(state.limits.max); input.value = String(line.quantity);
            label.append(input);
            input.addEventListener('change', () => this.store.setQuantity(line.key, input.value).catch(error => {
                this.renderSummary(); showMessage(error.message, true);
            }));
            const remove = doc.createElement('button'); remove.type = 'button'; remove.className = 'btn btn-link';
            remove.textContent = _t('Rimuovi'); remove.addEventListener('click', () => this.store.remove(line.key).catch(error => showMessage(error.message, true)));
            row.append(title, label, remove);
            if (line.subtotal_display) {
                const price = doc.createElement('p'); price.textContent = line.subtotal_display; row.append(price);
            }
            if (line.warning) { const warning = doc.createElement('p'); warning.textContent = line.warning; row.append(warning); }
            holder.append(row);
        }
        this.el.querySelector('[data-request-status]').textContent = state.lines.length ? '' : _t('La tua richiesta è vuota. Scegli i prodotti dal catalogo.');
        this.el.querySelector('[data-request-total]').textContent = state.products_total_display || '';
        this.el.querySelector('[data-request-total]').hidden = !state.products_total_display;
        this.el.querySelector('[data-request-price-note]').hidden = !state.show_prices || !state.lines.length;
    }
}
registry.category('public.interactions').add('torrepulia.request.commerce', RequestCommerce);
