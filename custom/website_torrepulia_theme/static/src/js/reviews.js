import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

// The product reviews (portal chatter) render in a shadow root: its host gets the class that the
// theme rules loaded inside it read (scss/reviews_chatter.scss), on the Torrepulia site only.
export class ReviewsChatterHost extends Interaction {
    static selector = '.tp-site .o_portal_chatter';

    start() {
        const mark = () => {
            const host = this.el.querySelector('#chatterRoot');
            host?.classList.add('tp-chatter');
            return Boolean(host);
        };
        if (mark()) return;
        const observer = new MutationObserver(() => { if (mark()) observer.disconnect(); });
        observer.observe(this.el, { childList: true, subtree: true });
        this.registerCleanup(() => observer.disconnect());
    }
}

registry.category('public.interactions').add('website_torrepulia_theme.reviews_chatter_host', ReviewsChatterHost);
