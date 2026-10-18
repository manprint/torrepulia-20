import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';

// Native Bootstrap collapse remains the owner of state and aria-expanded.
export class TorrepuliaNavigation extends Interaction {
    static selector = '.tp-cinematic .mc-chrome';
    start() {
        const toggle = this.el.querySelector('.menu-toggle');
        const menu = this.el.querySelector('#mc-mobile-menu');
        const close = (restoreFocus = false) => {
            if (!menu.classList.contains('show')) return;
            if (restoreFocus) toggle.focus();
            toggle.click();
        };
        this.addListener(menu, 'shown.bs.collapse', () => {
            toggle.setAttribute('aria-label', _t('Chiudi il menu'));
            menu.querySelector('a, summary')?.focus();
        });
        this.addListener(menu, 'hidden.bs.collapse', () => toggle.setAttribute('aria-label', _t('Apri il menu')));
        this.addListener(this.el, 'keydown', ev => {
            if (ev.key === 'Escape') { close(true); ev.preventDefault(); }
        });
        this.addListener(document, 'click', ev => { if (!this.el.contains(ev.target)) close(menu.contains(document.activeElement)); });
        this.addListener(menu, 'click', ev => { if (ev.target.closest('a')) close(true); });
        this.addListener(menu, 'focusout', ev => { if (ev.relatedTarget && !this.el.contains(ev.relatedTarget)) close(); });
        this.addListener(window, 'resize', () => {
            if (getComputedStyle(toggle).display === 'none') {
                close(false);
                if (menu.contains(document.activeElement)) this.el.querySelector('.desktop-nav a')?.focus();
            }
        });
    }
}
registry.category('public.interactions').add('torrepulia.navigation', TorrepuliaNavigation);
