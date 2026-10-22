import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';
import { CinematicCommerce } from '@website_torrepulia_theme/js/cinematic';

patch(CinematicCommerce.prototype, {
    async willStart() {
        if (!this.el.classList.contains('mc-product-formats')) {
            return super.willStart(...arguments);
        }
        let records;
        try { records = JSON.parse(this.el.dataset.productIds || '[]'); } catch { records = []; }
        try {
            this.data = await rpc('/torrepulia/formats', {
                ids: records.map(product => product.id), promoted: false,
                exclude_template_id: Number(this.el.dataset.currentProduct),
            });
        } catch { this.data = null; }
    },
});
