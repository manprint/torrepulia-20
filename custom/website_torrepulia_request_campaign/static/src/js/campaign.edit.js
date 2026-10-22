import { registry } from '@web/core/registry';
import { SeasonalCampaign } from './campaign';

// This runs in the website iframe, where the frontend Interaction is defined.
// Builder options run in the parent web client and must not import it.
const demoMixin = I => class extends I {
    setup() { super.setup(); this.editing = true; }
};
registry.category('public.interactions.edit').add('torrepulia.seasonal.campaign', {
    Interaction: SeasonalCampaign, mixin: demoMixin,
});
