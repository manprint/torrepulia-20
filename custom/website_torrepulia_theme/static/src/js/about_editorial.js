import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

export class AboutEditorial extends Interaction {
    static selector = '.tp-site .tp-about-generations';

    start() {
        const reduced = matchMedia('(prefers-reduced-motion: reduce)');
        const articles = [...this.el.querySelectorAll('.tp-about-grid > article')];
        if (reduced.matches || !('IntersectionObserver' in window) ||
            this.el.closest('[contenteditable="true"], .o_editable') || !articles.length) return;

        const pending = new Set(articles);
        const observer = new IntersectionObserver(entries => {
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                entry.target.classList.add('is-editorial-visible');
                pending.delete(entry.target);
                observer.unobserve(entry.target);
            }
            if (!pending.size) observer.disconnect();
        }, { threshold: .08, rootMargin: '0px 0px -24px 0px' });

        // Content is visible without JS; hiding is only a progressive enhancement.
        this.el.classList.add('has-editorial-reveal');
        for (const article of articles) observer.observe(article);
        this.addListener(reduced, 'change', () => {
            if (!reduced.matches) return;
            observer.disconnect();
            this.el.classList.remove('has-editorial-reveal');
        });
        this.registerCleanup(() => {
            observer.disconnect();
            this.el.classList.remove('has-editorial-reveal');
            for (const article of articles) article.classList.remove('is-editorial-visible');
        });
    }
}

registry.category('public.interactions').add('torrepulia.about_editorial', AboutEditorial);
