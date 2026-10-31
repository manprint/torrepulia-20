import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

/**
 * Website forms say "a person opened this page" a few seconds after it opens. Spam bots post
 * the form directly or fill it in an instant: without the field the server creates no lead.
 * The field exists only while the page runs, so the Builder never saves it.
 */
export class FormGuard extends Interaction {
    static selector = '.s_website_form form, form.s_website_form';
    start() {
        const field = document.createElement('input');
        Object.assign(field, { type: 'hidden', name: 'tp_human', value: '' });
        this.insert(field, this.el);
        this.waitForTimeout(() => { field.value = '1'; }, 3000);
    }
}

registry.category('public.interactions').add('torrepulia.form_guard', FormGuard);
