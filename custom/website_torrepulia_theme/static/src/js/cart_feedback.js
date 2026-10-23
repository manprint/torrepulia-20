import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

// Feedback, occasional: the header count beats once when the cart grows.
const EASE_OUT = 'cubic-bezier(.23, 1, .32, 1)';

export class CartCountFeedback extends Interaction {
    static selector = '.tp-site .cart-count';

    setup() {
        this.count = Number(this.el.textContent) || 0;
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const observer = new MutationObserver(() => {
            const count = Number(this.el.textContent) || 0;
            if (count > this.count) {
                this.animation?.cancel();
                // Reduced motion keeps the state change as a colour flash, without movement.
                this.animation = this.el.animate(reduced.matches
                    ? [{ opacity: .4 }, { opacity: 1 }]
                    : [{ transform: 'scale(1)' }, { transform: 'scale(1.3)', offset: .35 }, { transform: 'scale(1)' }],
                { duration: 220, easing: EASE_OUT });
            }
            this.count = count;
        });
        observer.observe(this.el, { childList: true, characterData: true, subtree: true });
        this.registerCleanup(() => { observer.disconnect(); this.animation?.cancel(); });
    }
}

registry.category('public.interactions').add('website_torrepulia_theme.cart_count_feedback', CartCountFeedback);
