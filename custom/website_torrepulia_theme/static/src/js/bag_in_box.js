import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

let sequence = 0;
// The home links here ("Come funziona"). Odoo's sanitizer strips ids from product descriptions,
// so the first explainer of the page receives the anchor when the page runs.
const ANCHOR = 'come-funziona';
// Read at load: the product page rewrites the URL with the chosen variant and drops the hash.
const requestedAnchor = typeof window !== 'undefined' && window.location.hash === `#${ANCHOR}`;

export class BagInBox extends Interaction {
    static selector = '.tp-site .tp-bib';

    start() {
        const doc = this.el.ownerDocument;
        if (!this.el.id && !doc.getElementById(ANCHOR) && doc.querySelector(BagInBox.selector) === this.el) {
            this.el.id = ANCHOR;
            this.registerCleanup(() => this.el.removeAttribute('id'));
            if (requestedAnchor || doc.defaultView.location.hash === `#${ANCHOR}`) {
                doc.defaultView.requestAnimationFrame(() => this.el.scrollIntoView({ block: 'start' }));
            }
        }
        const button = this.el.querySelector('.tp-bib-hotspot');
        const tooltip = this.el.querySelector('.tp-bib-tooltip');
        if (!button || !tooltip) return;
        const prefix = `tp-bib-${++sequence}`;
        const originals = [];
        const set = (node, name, value) => {
            originals.push([node, name, node.getAttribute(name)]);
            node.setAttribute(name, value);
        };
        // Repeated snippets must not share tooltip IDs.
        set(tooltip, 'id', `${prefix}-tooltip`);
        set(button, 'aria-describedby', tooltip.id);
        set(button, 'aria-controls', tooltip.id);
        let hovered = false;
        let focused = false;
        let pinned = false;
        let dismissed = false;
        const sync = () => {
            const open = !dismissed && (hovered || focused || pinned);
            tooltip.hidden = !open;
            button.setAttribute('aria-expanded', String(open));
            this.el.classList.toggle('is-aroma-active', open);
        };
        this.addListener(button, 'pointerenter', event => {
            if (event.pointerType === 'touch') return;
            hovered = true; dismissed = false; sync();
        });
        this.addListener(button, 'pointerleave', () => { hovered = false; sync(); });
        this.addListener(button, 'focus', () => { focused = true; dismissed = false; sync(); });
        this.addListener(button, 'blur', () => { focused = false; pinned = false; dismissed = false; sync(); });
        this.addListener(button, 'click', () => { pinned = !pinned; dismissed = !pinned; sync(); });
        this.addListener(button, 'keydown', event => {
            if (event.key === 'Escape') { pinned = false; dismissed = true; sync(); }
        });
        this.registerCleanup(() => {
            this.el.classList.remove('is-aroma-active');
            tooltip.hidden = true; button.setAttribute('aria-expanded', 'false');
            for (const [node, name, value] of originals.reverse()) {
                if (value === null) node.removeAttribute(name);
                else node.setAttribute(name, value);
            }
        });
    }
}
registry.category('public.interactions').add('torrepulia.bag_in_box', BagInBox);
