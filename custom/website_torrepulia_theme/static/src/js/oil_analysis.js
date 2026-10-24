import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

// La Peranzana shows the analysis of the latest harvest profile: the backend is the only source.
export class OilAnalysis extends Interaction {
    static selector = '.tp-analysis';

    async willStart() {
        try {
            const response = await this.waitFor(fetch('/torrepulia/analisi', { headers: { Accept: 'application/json' } }));
            this.html = response.ok ? (await this.waitFor(response.json())).html : null;
        } catch {
            this.html = null;
        }
    }

    start() {
        const holder = this.el.querySelector('.tp-analysis-content');
        if (!holder || !this.html) return;
        const original = holder.innerHTML;
        holder.innerHTML = this.html;
        this.registerCleanup(() => { holder.innerHTML = original; });
    }
}
registry.category('public.interactions').add('torrepulia.oil_analysis', OilAnalysis);
