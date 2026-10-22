import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';

export const sameCampaignConfiguration = (line, config) => line.product_id === config.product_id &&
    line.uom_id === config.uom_id && !(line.no_variant_value_ids || []).length &&
    !Object.keys(line.custom_values || {}).length;

export function campaignCounts(state, configurations) {
    const campaign = state.lines.filter(line => configurations.some(config => sameCampaignConfiguration(line, config)))
        .reduce((sum, line) => sum + line.quantity, 0);
    return { campaign, request: state.quantity, other: state.quantity - campaign };
}

export class SeasonalCampaign extends Interaction {
    static selector = '.tp-campaign';
    editing = false;

    async start() {
        this.active = true;
        this.quantityBusy = new Set();
        this.holder = this.el.querySelector('.tp-campaign-content');
        const original = this.holder.innerHTML;
        this.registerCleanup(() => { this.active = false; this.holder.innerHTML = original; });
        if (!this.editing) {
            this.store = this.services['torrepulia.request'];
            this.registerCleanup(this.store.subscribe(state => this.renderState(state)));
            this.addListener(this.el, 'change', event => {
                if (event.target.matches('.tp-campaign-quantity') && event.target.closest('.tp-campaign') === this.el) {
                    this.setCardQuantity(event.target, event.target.value);
                }
            });
        }
        this.addListener(this.el, 'click', event => {
            const step = event.target.closest('[data-campaign-step]');
            if (step && !this.editing && !step.disabled) {
                const input = step.closest('[data-campaign-config]').querySelector('.tp-campaign-quantity');
                const limits = this.store.state.limits;
                const current = Number(input.value), delta = Number(step.dataset.campaignStep);
                const quantity = delta > 0 ? (current ? current + limits.step : limits.min)
                    : current <= limits.min ? 0 : Math.max(limits.min, current - limits.step);
                this.setCardQuantity(input, Math.round(quantity * 1e9) / 1e9);
            }
            if (event.target.closest('[data-campaign-scroll]')) {
                this.holder.scrollIntoView({ block: 'start' });
            }
            if (!this.editing && event.target.closest('[data-campaign-retry]')) {
                this.perform(() => this.store.retryPending());
            }
            if (this.editing && event.target.closest('a, input, [data-campaign-retry]')) event.preventDefault();
        });
        this.addListener(this.el, 'tp-campaign-refresh', () => this.load());
        if (!this.editing) {
            this.addListener(window, 'focus', () => this.load());
            this.addListener(window, 'pageshow', () => this.load());
        }
        this.registerCleanup(() => clearTimeout(this.refreshTimer));
        const observer = new MutationObserver(() => this.load());
        observer.observe(this.el, { attributes: true, attributeFilter: ['data-campaign', 'data-demo-state'] });
        this.registerCleanup(() => observer.disconnect());
        await this.load();
        if (!this.editing) await this.perform(() => this.store.read());
    }

    async load() {
        const generation = this.generation = (this.generation || 0) + 1;
        try {
            const selected = JSON.parse(this.el.dataset.campaign || 'null');
            const params = new URLSearchParams();
            if (selected?.id) params.set('campaign_id', selected.id);
            if (this.editing) params.set('demo', '1');
            const response = await fetch(`/torrepulia/campaign/content?${params}`, { credentials: 'same-origin', cache: 'no-store' });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            if (!this.active || this.generation !== generation) return;
            // Server-rendered QWeb only; visitor strings are never assigned to HTML.
            this.holder.innerHTML = result.html;
            this.open = result.open;
            this.configs = result.configurations || [];
            clearTimeout(this.refreshTimer);
            if (!this.editing && result.refresh_after) {
                this.refreshTimer = setTimeout(() => this.load(), Math.min(result.refresh_after * 1000, 2147483000));
            }
            if (this.editing) {
                const mode = this.el.dataset.demoState || 'zero';
                this.holder.querySelectorAll('.tp-campaign-quantity').forEach((input, index) => {
                    input.value = mode === 'multiple' ? String(index + 1) : mode === 'one' && index === 0 ? '1' : '0';
                    input.disabled = true;
                });
                this.holder.querySelector('[data-campaign-counts]').textContent = _t('Dati dimostrativi isolati dalla richiesta reale.');
            } else if (this.store.state) {
                this.renderState(this.store.state);
            }
        } catch {
            if (this.active && this.generation === generation) {
                this.holder.textContent = _t('Impossibile caricare la campagna. Ricarica la pagina oppure visita il catalogo.');
            }
        }
    }

    configurations() {
        return this.configs || [];
    }

    setCardQuantity(input, quantity) {
        const config = JSON.parse(input.closest('[data-campaign-config]').dataset.campaignConfig);
        const key = `${config.product_id}:${config.uom_id}`;
        if (this.quantityBusy.has(key)) return;
        this.quantityBusy.add(key);
        this.renderState(this.store.state);
        this.perform(async () => {
            try { await this.store.setConfiguration(config, quantity); }
            finally {
                this.quantityBusy.delete(key);
                if (this.active) this.renderState(this.store.state);
            }
        });
    }

    renderState(state) {
        if (!this.active || this.editing || !this.holder.querySelector('[data-campaign-counts]')) return;
        const counts = campaignCounts(state, this.configurations());
        for (const input of this.holder.querySelectorAll('.tp-campaign-quantity')) {
            const config = JSON.parse(input.closest('[data-campaign-config]').dataset.campaignConfig);
            input.value = String(state.lines.find(line => sameCampaignConfiguration(line, config))?.quantity || 0);
            input.max = String(state.limits.max); input.step = String(state.limits.step);
            input.disabled = !state.enabled || !this.open || this.quantityBusy.has(`${config.product_id}:${config.uom_id}`);
            for (const button of input.closest('[data-campaign-config]').querySelectorAll('[data-campaign-step]')) {
                button.disabled = input.disabled || (Number(button.dataset.campaignStep) < 0
                    ? !Number(input.value) : Number(input.value) >= state.limits.max);
            }
        }
        const number = value => new Intl.NumberFormat(document.documentElement.lang || 'it').format(value);
        this.holder.querySelector('[data-campaign-counts]').textContent =
            _t('Formati di questa campagna: %s confezioni. Intera richiesta: %s confezioni.', number(counts.campaign), number(counts.request));
        const other = this.holder.querySelector('[data-campaign-other]');
        other.hidden = counts.other <= 0;
        other.textContent = _t('La richiesta comprende anche %s confezioni di altri prodotti o configurazioni. Le ritrovi nel riepilogo qui sotto.', number(counts.other));
        const warning = state.lines.filter(line => line.warning).map(line => line.warning).join(' ');
        this.message(warning);
    }

    message(text) {
        const message = this.holder.querySelector('[data-campaign-message]');
        if (message) message.textContent = text;
        const retry = this.holder.querySelector('[data-campaign-retry]');
        if (retry) retry.hidden = !this.store?.pending;
    }

    async perform(action) {
        try {
            await action();
        } catch (error) {
            if (!this.active) return;
            if (this.store.state) this.renderState(this.store.state);
            this.message(error.code === 'conflict' ? _t('La selezione è cambiata. Controlla le quantità e riprova.')
                : ['pending', 'network'].includes(error.code) ? _t('Aggiornamento da verificare. Usa Riprova aggiornamento senza reinserire la quantità.')
                    : error.message || _t('Impossibile aggiornare la selezione. Riprova.'));
        }
    }
}
registry.category('public.interactions').add('torrepulia.seasonal.campaign', SeasonalCampaign);
