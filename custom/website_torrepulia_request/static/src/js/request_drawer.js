import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';

export class RequestDrawer extends Interaction {
    static selector = '#wrapwrap';

    start() {
        if (document.body.dataset.tpRequestMode !== '1') return;
        this.active = true;
        this.store = this.services['torrepulia.request'];
        const doc = this.el.ownerDocument;
        this.node = (tag, text, cls) => {
            const el = doc.createElement(tag);
            if (text) el.textContent = text;
            if (cls) el.className = cls;
            return el;
        };
        const dialog = this.dialog = this.node('dialog', '', 'tp-request-drawer');
        dialog.id = `tp-request-drawer-${crypto.randomUUID()}`;
        const header = this.node('div', '', 'tp-drawer-heading');
        const title = this.node('h2', _t('La tua richiesta'));
        title.id = `${dialog.id}-title`;
        dialog.setAttribute('aria-labelledby', title.id);
        const close = this.node('button', '×', 'tp-drawer-close');
        close.type = 'button'; close.setAttribute('aria-label', _t('Chiudi la tua richiesta'));
        header.append(title, close);
        this.content = this.node('div', '', 'tp-drawer-content');
        this.content.setAttribute('aria-live', 'polite');
        const footer = this.node('div', '', 'tp-drawer-footer');
        this.total = this.node('p', '', 'tp-drawer-total');
        this.total.hidden = true;
        this.review = this.node('a', _t('VAI AL RIEPILOGO'), 'btn btn-primary');
        this.review.href = document.body.dataset.tpRequestSummaryUrl;
        footer.append(this.total, this.review);
        dialog.append(header, this.content, footer);
        this.el.append(dialog);
        const anchors = [...this.el.querySelectorAll('[data-tp-request-header]')];
        for (const anchor of anchors) {
            anchor.setAttribute('aria-haspopup', 'dialog');
            anchor.setAttribute('aria-controls', dialog.id);
            anchor.setAttribute('aria-expanded', 'false');
        }
        this.addListener(this.el, 'click', event => {
            const anchor = event.target.closest('[data-tp-request-header]');
            if (!anchor || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button) return;
            event.preventDefault();
            this.trigger = anchor;
            this.content.textContent = _t('Caricamento della richiesta…');
            this.total.hidden = true;
            dialog.showModal();
            document.body.classList.add('tp-request-drawer-open');
            anchor.setAttribute('aria-expanded', 'true');
            close.focus();
            this.read();
        });
        this.addListener(close, 'click', () => dialog.close());
        this.addListener(dialog, 'keydown', event => {
            if (event.key !== 'Tab') return;
            const controls = [...dialog.querySelectorAll('button:not([disabled]), a[href]')]
                .filter(el => el.getClientRects().length);
            const first = controls[0], last = controls.at(-1);
            if (event.shiftKey && doc.activeElement === first) {
                event.preventDefault(); last.focus();
            } else if (!event.shiftKey && doc.activeElement === last) {
                event.preventDefault(); first.focus();
            }
        });
        this.addListener(dialog, 'click', event => {
            const rect = dialog.getBoundingClientRect();
            if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right ||
                    event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
        });
        this.addListener(dialog, 'close', () => {
            this.ticket = (this.ticket || 0) + 1;
            document.body.classList.remove('tp-request-drawer-open');
            this.trigger?.setAttribute('aria-expanded', 'false');
            if (this.active && this.trigger?.isConnected) this.trigger.focus();
        });
        this.registerCleanup(this.store.subscribe(() => {
            if (dialog.open) this.refresh().catch(() => this.failed());
        }));
        this.registerCleanup(() => {
            this.active = false;
            dialog.close(); dialog.remove();
            document.body.classList.remove('tp-request-drawer-open');
            for (const anchor of anchors) {
                for (const key of ['aria-haspopup', 'aria-controls', 'aria-expanded']) anchor.removeAttribute(key);
            }
        });
    }

    async read() {
        try { await this.store.read(); }
        catch { this.failed(); }
    }

    failed() {
        if (!this.active || !this.dialog.open) return;
        this.content.replaceChildren(this.node('p', _t('Impossibile aggiornare la richiesta. Riprova oppure apri il riepilogo.')));
        this.total.hidden = true;
        const retry = this.node('button', _t('Riprova'), 'btn btn-outline-primary');
        retry.type = 'button'; retry.addEventListener('click', () => this.read());
        this.content.append(retry);
    }

    async refresh() {
        const ticket = this.ticket = (this.ticket || 0) + 1;
        let state;
        try {
            const response = await fetch('/torrepulia/request/preview', { credentials: 'same-origin', cache: 'no-store' });
            if (!response.ok) throw new Error('preview');
            state = (await response.json()).state;
        } catch {
            if (ticket === this.ticket) this.failed();
            return;
        }
        if (!this.active || !this.dialog.open || ticket !== this.ticket ||
                state.selection_id !== this.store.state?.selection_id || state.revision < this.store.state.revision) return;
        this.content.replaceChildren();
        this.review.href = state.summary_url;
        if (!state.lines.length) {
            this.content.append(this.node('p', _t('La tua richiesta è ancora vuota')));
            const shop = this.node('a', _t('Scopri i nostri prodotti'), 'btn btn-link');
            shop.href = '/shop'; this.content.append(shop);
        }
        for (const line of state.lines) {
            const row = this.node('article', '', 'tp-drawer-line');
            if (line.thumbnail) {
                const image = this.node('img'); image.src = line.thumbnail; image.alt = '';
                image.width = 64; image.height = 80; row.append(image);
            }
            const details = this.node('div');
            details.append(this.node('h3', line.name.replace(/\bLT\b/gi, 'L')));
            for (const value of [...(line.attributes || []), ...(line.custom_text || [])]) details.append(this.node('p', value));
            details.append(this.node('p', _t('Quantità: %s', line.quantity)));
            if (line.subtotal_display) details.append(this.node('p', _t('Subtotale: %s', line.subtotal_display)));
            if (line.warning) details.append(this.node('p', line.warning, 'tp-drawer-warning'));
            row.append(details); this.content.append(row);
        }
        this.total.hidden = !state.products_total_display;
        this.total.textContent = state.products_total_display ? _t('Totale prodotti: %s', state.products_total_display) : '';
        if (state.products_total_display) this.total.append(this.node('small', _t('Spese di spedizione da definire.')));
    }
}
registry.category('public.interactions').add('torrepulia.request.drawer', RequestDrawer);
