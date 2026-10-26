import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

// Conversions for GA4 (Odoo's gtag) and the Meta Pixel, both loaded only after consent: sent
// once per reference in the tab, a reload of the page does not count again. Without consent
// nothing is sent or stored, not even the marker.
function consented() {
    const match = document.cookie.match(/(?:^|; )website_cookies_bar=([^;]*)/);
    try {
        return Boolean(match && JSON.parse(decodeURIComponent(match[1])).optional);
    } catch {
        return false;
    }
}

function once(key) {
    if (!consented()) return false;
    try {
        if (sessionStorage.getItem(key)) return false;
        sessionStorage.setItem(key, '1');
    } catch {
        // Storage blocked: send anyway, the page is reached once after the submission.
    }
    return true;
}

export class ReservationLead extends Interaction {
    static selector = '.tp-site [data-tp-conversion="lead"]';

    start() {
        const { tpReference: reference, tpLeadSource: source } = this.el.dataset;
        if (!reference || !once(`tp-lead-${reference}`)) return;
        window.gtag?.('event', 'generate_lead', { lead_source: source });
        window.fbq?.('track', 'Lead', { content_category: source });
    }
}

// GA4 already receives "purchase" from Odoo's own tracking; the Pixel gets it here.
export class MetaPurchase extends Interaction {
    static selector = '.tp-site div[name="order_confirmation"]';

    start() {
        let info;
        try {
            info = JSON.parse(this.el.dataset.orderTrackingInfo || '{}');
        } catch {
            return;
        }
        if (!window.fbq || !info.transaction_id || !once(`tp-purchase-${info.transaction_id}`)) return;
        window.fbq('track', 'Purchase', { value: info.value, currency: info.currency });
    }
}

registry.category('public.interactions')
    .add('website_torrepulia_theme.reservation_lead', ReservationLead)
    .add('website_torrepulia_theme.meta_purchase', MetaPurchase);
