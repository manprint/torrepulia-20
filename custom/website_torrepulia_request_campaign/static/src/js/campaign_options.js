import { BaseOptionComponent } from '@html_builder/core/base_option_component';
import { Plugin } from '@html_editor/plugin';
import { registry } from '@web/core/registry';
import { browser } from '@web/core/browser/browser';

export class SeasonalCampaignOption extends BaseOptionComponent {
    static id = 'torrepulia_campaign_option';
    static template = 'website_torrepulia_request_campaign.CampaignOption';

    get websiteId() {
        return this.services.website.currentWebsiteId;
    }

    async manage() {
        const element = this.env.getEditingElement();
        const campaign = JSON.parse(element.dataset.campaign || 'null');
        let campaignId = campaign?.id;
        if (!campaignId) {
            const [website] = await this.services.orm.read('website', [this.websiteId], ['torrepulia_campaign_id']);
            campaignId = website.torrepulia_campaign_id?.[0];
        }
        // Keep backend navigation separate and preserve unsaved Builder edits.
        const url = '/odoo/action-website_torrepulia_request_campaign.action_campaigns' +
            (campaignId ? `/${campaignId}` : '');
        return browser.open(url, '_blank', 'noopener');
    }

    refresh() {
        this.env.getEditingElement().dispatchEvent(new CustomEvent('tp-campaign-refresh'));
    }
}
registry.category('website-options').add(SeasonalCampaignOption.id, SeasonalCampaignOption);

export function cleanCampaigns(root) {
    const snippets = [...root.querySelectorAll('.tp-campaign')];
    if (root.matches?.('.tp-campaign')) snippets.unshift(root);
    for (const snippet of snippets) {
        const holder = snippet.querySelector('.tp-campaign-content');
        if (holder) {
            const placeholder = root.ownerDocument.createElement('p');
            placeholder.textContent = 'Caricamento della campagna…';
            holder.replaceChildren(placeholder);
        }
        const review = snippet.querySelector('.tp-campaign-review');
        if (review) {
            const placeholder = root.ownerDocument.createElement('p');
            placeholder.textContent = 'Il modulo e il riepilogo della richiesta vengono caricati durante la visita. Nessun dato personale viene salvato nella pagina.';
            review.replaceChildren(placeholder);
        }
    }
    return root;
}

export class CampaignSavePlugin extends Plugin {
    static id = 'torrepuliaCampaignSave';
    resources = { clean_for_save_processors: cleanCampaigns };
}
registry.category('website-plugins').add(CampaignSavePlugin.id, CampaignSavePlugin);

