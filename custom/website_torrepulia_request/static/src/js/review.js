import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { ReCaptcha } from '@google_recaptcha/js/recaptcha';
import { RecaptchaForm } from '@google_recaptcha/interactions/recaptcha_form';

// Keep the native Turnstile data-captcha interaction, when installed. This
// particular form obtains native reCAPTCHA tokens in its AJAX submit handler;
// native form.submit() would bypass the protected JSON submission protocol.
patch(RecaptchaForm.prototype, {
    onSubmit(event) {
        if (this.el.matches('[data-tp-review-form]')) return;
        return super.onSubmit(...arguments);
    },
});

export class ReviewSubmissionError extends Error {
    constructor(code, message, fields = []) { super(message); this.code = code; this.fields = fields; }
}

export class SubmissionAttempt {
    constructor({ transport, makeId = () => crypto.randomUUID() }) {
        this.transport = transport; this.makeId = makeId;
        this.pending = null; this.busy = false;
    }

    async submit(state, contact, tokens = {}) {
        if (this.busy) throw new ReviewSubmissionError('busy', 'busy');
        this.busy = true;
        try {
            if (!this.pending) this.pending = { ...contact, operation_id: this.makeId(),
                selection_id: state.selection_id, revision: state.revision };
            const response = await this.transport(this.pending, tokens);
            if (response.ok !== true) {
                this.pending = null;
                throw new ReviewSubmissionError('invalid', response.message || _t('Verifica i dati e riprova.'), response.fields || []);
            }
            this.pending = null;
            return response;
        } catch (error) {
            if (error instanceof ReviewSubmissionError) throw error;
            throw new ReviewSubmissionError('uncertain', _t('Esito dell’invio non confermato. Usa Riprova invio per verificare la stessa richiesta senza duplicarla.'));
        } finally {
            this.busy = false;
        }
    }
}

export function renderCompactLines(holder, state) {
    const doc = holder.ownerDocument;
    holder.replaceChildren();
    const quantity = value => new Intl.NumberFormat(doc.documentElement.lang || 'it').format(value);
    for (const line of state.lines) {
        const row = doc.createElement('div'); row.className = 'tp-review-summary-line';
        const description = doc.createElement('div');
        const title = doc.createElement('p'); title.className = 'tp-review-summary-name';
        title.textContent = _t('%s × %s', line.name, quantity(line.quantity));
        description.append(title);
        for (const detail of [...(line.attributes || []), ...(line.custom_text || [])]) {
            // The variant name already carries its values ("Latta 5 LT (Filtrato)").
            if (line.name.includes(detail.split(': ').pop())) continue;
            const text = doc.createElement('p'); text.className = 'tp-review-summary-detail';
            text.textContent = detail; description.append(text);
        }
        if (line.warning) {
            const warning = doc.createElement('p'); warning.className = 'tp-review-warning';
            warning.textContent = line.warning; description.append(warning);
        }
        if (line.available === false) {
            // No counter on the page for an archived or changed product: removing it here is the only way on.
            const remove = doc.createElement('button'); remove.type = 'button';
            remove.className = 'tp-review-summary-remove'; remove.textContent = _t('Rimuovi');
            remove.dataset.reviewRemove = line.key;
            remove.setAttribute('aria-label', _t('Rimuovi %s', line.name));
            description.append(remove);
        }
        row.append(description);
        if (state.show_prices && line.subtotal_display) {
            const subtotal = doc.createElement('span'); subtotal.className = 'tp-review-summary-subtotal';
            subtotal.textContent = line.subtotal_display; row.append(subtotal);
        }
        holder.append(row);
    }
}

export class RequestReview extends Interaction {
    static selector = '[data-tp-review]';
    dynamicContent = { '[data-tp-review-form]': { 't-on-submit.prevent': this.submit } };

    async start() {
        this.active = true;
        const original = this.el.innerHTML;
        this.registerCleanup(() => {
            this.active = false;
            if (this.el.hasAttribute('data-review-lazy')) this.el.innerHTML = original;
        });
        if (this.el.hasAttribute('data-review-lazy')) {
            const response = await fetch(this.el.closest('.tp-campaign') ? '/torrepulia/request/form?layout=campaign' : '/torrepulia/request/form', { credentials: 'same-origin', cache: 'no-store' });
            if (!response.ok) { this.el.textContent = _t('Apri La tua richiesta per proseguire.'); return; }
            const html = await response.text();
            if (!this.active) return;
            this.el.innerHTML = html;
        }
        this.store = this.services['torrepulia.request'];
        this.form = this.el.querySelector('[data-tp-review-form]');
        this.recaptcha = new ReCaptcha();
        this.dirtyInputs = new Map();
        this.attempt = new SubmissionAttempt({ transport: async (payload, tokens) => {
            const response = await fetch(this.form.getAttribute('action') || '/torrepulia/request/submit', { method: 'POST',
                credentials: 'same-origin', cache: 'no-store',
                body: new URLSearchParams({ csrf_token: this.store.csrfToken, payload: JSON.stringify(payload), ...tokens }) });
            if (response.status >= 500 || !response.headers.get('content-type')?.includes('application/json')) throw new Error('transport');
            return response.json();
        } });
        this.registerCleanup(() => { this.active = false; this.attempt.pending = null; });
        this.registerCleanup(this.store.subscribe(() => this.refresh().catch(error => this.error(error.message))));
        this.addListener(this.el, 'input', event => {
            if (event.target.matches('[data-review-key]')) this.dirtyInputs.set(event.target.dataset.reviewKey, event.target.value);
        });
        this.addListener(this.el, 'change', event => {
            if (event.target.matches('[data-review-key]')) {
                const input = event.target;
                this.dirtyInputs.delete(input.dataset.reviewKey);
                this.change(() => this.store.setQuantity(input.dataset.reviewKey, input.value));
            }
        });
        this.addListener(this.el, 'click', event => {
            const step = event.target.closest('[data-review-step]');
            if (step && !step.disabled) {
                const input = step.closest('.tp-review-controls').querySelector('[data-review-key]');
                const current = Number(input.value), limits = this.store.state.limits;
                const quantity = Number(step.dataset.reviewStep) > 0 ? (current ? current + limits.step : limits.min)
                    : current <= limits.min ? 0 : Math.max(limits.min, current - limits.step);
                this.change(() => this.store.setQuantity(input.dataset.reviewKey, Math.round(quantity * 1e9) / 1e9));
            }
            const remove = event.target.closest('[data-review-remove]');
            if (remove) this.change(() => this.store.remove(remove.dataset.reviewRemove));
            if (event.target.closest('[data-review-retry]')) this.change(() => this.store.retryPending());
        });
        await this.store.read().catch(() => this.error(_t('Impossibile leggere la richiesta. Ricarica la pagina per riprovare.')));
    }

    async change(action) {
        if (this.busy || this.changing) return;
        this.changing = true;
        this.setBusy(Boolean(this.busy));
        try { await action(); }
        catch (error) {
            await this.refresh().catch(() => {});
            this.error(['pending', 'network'].includes(error.code)
                ? _t('Aggiornamento da verificare. Usa Riprova aggiornamento prima di inviare.')
                : error.code === 'conflict' ? _t('La selezione è cambiata. Controlla le quantità e riprova.') : error.message);
        } finally {
            this.changing = false;
            if (this.active) this.setBusy(Boolean(this.busy));
        }
    }

    async refresh() {
        if (this.completed) return;
        const ticket = this.reviewTicket = (this.reviewTicket || 0) + 1;
        const response = await fetch('/torrepulia/request/preview', { credentials: 'same-origin', cache: 'no-store' });
        if (!response.ok) throw new Error(_t('Impossibile aggiornare il riepilogo. Ricarica la pagina.'));
        const { state } = await response.json();
        if (!this.active || this.completed || ticket !== this.reviewTicket ||
                state.selection_id !== this.store.state?.selection_id || state.revision < this.store.state.revision) return;
        this.viewState = state;
        this.el.querySelector('[data-review-status]').textContent = '';
        const empty = !state.lines.length;
        this.el.querySelector('[data-review-empty]').hidden = !empty;
        this.el.querySelector('[data-review-content]').hidden = empty;
        this.form.hidden = empty && !this.attempt.pending;
        this.renderLines(state);
        const total = this.el.querySelector('[data-review-sum]');
        const compact = this.form.dataset.reviewCompact === '1';
        total.hidden = compact || !state.products_total_display;
        total.textContent = state.products_total_display ? _t('Totale prodotti: %s', state.products_total_display) : '';
        const liters = this.el.querySelector('[data-review-liters]');
        liters.hidden = compact || !state.liters_display;
        if (compact) this.el.querySelector('[data-review-pay-today]').textContent = state.show_prices
            ? _t('Totale da pagare oggi: 0,00 €') : _t('Nessun pagamento richiesto oggi.');
        liters.textContent = state.liters_display ? _t('Contenuto complessivo della richiesta: %s', state.liters_display) : '';
        this.el.querySelector('[data-review-delivery-note]').hidden = empty;
        if (compact) this.renderTotals(state, empty);
        this.el.querySelector('[data-review-retry]').hidden = !this.store.pending;
        this.setBusy(Boolean(this.busy));
    }

    // Reservation summary: products, shipping (or how far it is from free) and the expected total.
    renderTotals(state, empty) {
        const totals = this.el.querySelector('[data-review-totals]');
        if (!totals) return;
        totals.hidden = empty || !state.products_total_display;
        if (totals.hidden) return;
        const set = (selector, value) => { totals.querySelector(selector).textContent = value || ''; };
        set('[data-review-products]', state.products_total_display);
        set('[data-review-shipping]', state.shipping_display);
        set('[data-review-estimated]', state.estimated_total_display);
        totals.querySelector('[data-review-shipping-row]').hidden = !state.shipping_display;
        totals.querySelector('[data-review-estimated-row]').hidden = !state.estimated_total_display;
        const free = totals.querySelector('[data-review-free-shipping]');
        free.hidden = !state.free_shipping_gap_display;
        set('[data-review-free-gap]', state.free_shipping_gap_display
            ? _t('Ti mancano %s per la spedizione gratuita.', state.free_shipping_gap_display) : '');
        totals.querySelector('[data-review-free-bar]').style.width = `${state.free_shipping_progress || 0}%`;
        // The shop's shipping sentence would repeat the figures above.
        const note = this.el.querySelector('[data-review-delivery-note]');
        if (note && state.shipping_display) note.hidden = true;
    }

    renderLines(state) {
        if (this.form.dataset.reviewCompact === '1') {
            renderCompactLines(this.el.querySelector('[data-review-compact-lines]'), state);
            return;
        }
        const holder = this.el.querySelector('[data-review-lines]');
        const doc = holder.ownerDocument;
        const focused = doc.activeElement?.dataset.reviewKey;
        holder.replaceChildren();
        const text = (tag, value, className) => {
            const node = doc.createElement(tag); node.textContent = value;
            if (className) node.className = className;
            return node;
        };
        for (const line of state.lines) {
            const row = doc.createElement('article'); row.className = 'tp-review-line';
            if (line.thumbnail) {
                const image = doc.createElement('img'); image.src = line.thumbnail; image.alt = '';
                image.width = 96; image.height = 96; row.append(image);
            }
            const details = doc.createElement('div'); details.className = 'tp-review-details';
            details.append(text('h2', line.name.replace(/\bLT\b/gi, 'L')));
            for (const value of [...(line.attributes || []), ...(line.custom_text || [])]) details.append(text('p', value));
            if (line.liters_display) details.append(text('p', _t('Contenuto complessivo: %s', line.liters_display)));
            if (line.warning) details.append(text('p', line.warning, 'tp-review-warning'));
            const controls = doc.createElement('div'); controls.className = 'tp-review-controls';
            const label = text('label', _t('Quantità di %s', line.name));
            const input = doc.createElement('input'); input.type = 'number'; input.min = '0';
            input.max = String(state.limits.max); input.step = String(state.limits.step);
            input.value = this.dirtyInputs.get(line.key) ?? String(line.quantity);
            input.dataset.reviewKey = line.key; input.disabled = Boolean(this.busy);
            input.setAttribute('aria-label', _t('Quantità di %s', line.name));
            const stepper = doc.createElement('div'); stepper.className = 'tp-review-stepper';
            const makeStep = (delta, name) => {
                const button = text('button', delta < 0 ? '−' : '+'); button.type = 'button';
                button.dataset.reviewStep = String(delta);
                button.setAttribute('aria-label', _t('%s quantità di %s', name, line.name));
                button.disabled = Boolean(this.busy) || (delta > 0 && line.quantity >= state.limits.max);
                return button;
            };
            stepper.append(makeStep(-1, _t('Riduci')), input, makeStep(1, _t('Aumenta')));
            label.append(stepper);
            const remove = text('button', _t('Rimuovi'), 'btn btn-link'); remove.type = 'button';
            remove.dataset.reviewRemove = line.key; remove.disabled = Boolean(this.busy);
            controls.append(label, remove);
            if (line.price_display) details.append(text('p', _t('Prezzo unitario: %s', line.price_display), 'product_price'));
            if (line.subtotal_display) controls.append(text('p', _t('Subtotale: %s', line.subtotal_display), 'product_price'));
            details.append(controls); row.append(details); holder.append(row);
            if (focused === line.key) input.focus({ preventScroll: true });
        }
    }

    setBusy(busy) {
        this.busy = busy;
        this.form.setAttribute('aria-busy', String(busy));
        this.form.querySelector('[data-review-fields]').disabled = busy || Boolean(this.attempt.pending) || !this.viewState?.can_submit;
        const button = this.form.querySelector('button[type="submit"]');
        button.disabled = busy || Boolean(this.changing) || (!this.attempt.pending && !this.viewState?.can_submit) || Boolean(this.store.pending);
        button.textContent = busy ? _t('Invio in corso…') : this.attempt.pending ? _t('Riprova invio') : _t('Conferma la mia prenotazione');
        this.form.querySelector('[data-review-sending]').hidden = !busy;
        this.form.elements.namedItem('privacy_accepted').disabled = busy || Boolean(this.attempt.pending) || !this.viewState?.can_submit;
        for (const input of this.el.querySelectorAll('[data-review-key], [data-review-remove], [data-review-step]')) input.disabled = busy || Boolean(this.changing);
    }

    error(message, fields = []) {
        if (!this.active) return;
        const alert = this.el.querySelector('[data-review-error]');
        alert.textContent = message || _t('Invio non riuscito. Riprova.'); alert.hidden = false;
        for (const input of this.form.querySelectorAll('[aria-invalid]')) input.removeAttribute('aria-invalid');
        let first;
        for (const name of fields) {
            const input = this.form.elements.namedItem(name);
            if (input) { input.setAttribute('aria-invalid', 'true'); first ||= input; }
        }
        (first || alert).focus();
    }

    async submit(event) {
        event.preventDefault();
        if (this.busy) return;
        if (this.form.querySelector('.cf_form_disabled')) {
            this.error(_t('Completa la verifica di sicurezza prima di inviare.')); return;
        }
        if (!this.attempt.pending && !this.form.reportValidity()) return;
        const contact = Object.fromEntries(['contact_name', 'email', 'phone', 'notes', 'delivery_area'].map(name => [name, this.form.elements.namedItem(name)?.value || '']));
        // The reservation form asks for the shipping address; the request form does not have these fields.
        for (const name of ['street', 'zip', 'city', 'state_code']) {
            const input = this.form.elements.namedItem(name);
            if (input) contact[name] = input.value || '';
        };
        contact.privacy_accepted = this.form.elements.namedItem('privacy_accepted').checked;
        this.setBusy(true);
        this.el.querySelector('[data-review-error]').hidden = true;
        let success = false;
        try {
            await this.store.read(); // drains queued quantity edits before taking the revision
            if (this.store.pending) throw new ReviewSubmissionError('pending', _t('Verifica prima l’aggiornamento delle quantità.'));
            await this.recaptcha.loadLibs();
            const token = await this.recaptcha.getToken('website_form');
            if (token.error) throw new ReviewSubmissionError('captcha', token.error);
            const tokens = {};
            if (token.token) tokens.recaptcha_token_response = token.token;
            const turnstile = this.form.elements.namedItem('turnstile_captcha')?.value;
            if (turnstile) tokens.turnstile_captcha = turnstile;
            const result = await this.attempt.submit(this.store.state, contact, tokens);
            success = true;
            this.completed = true;
            this.reviewTicket = (this.reviewTicket || 0) + 1;
            if (this.active) window.location.assign(result.success_url);
        } catch (error) {
            this.setBusy(false);
            this.error(error.message, error.fields);
            const widget = this.form.querySelector('.s_turnstile_container');
            if (widget && window.turnstile?.reset) window.turnstile.reset(widget);
        } finally {
            if (!success && this.active) this.setBusy(false);
        }
    }
}
registry.category('public.interactions').add('torrepulia.request.review', RequestReview);
