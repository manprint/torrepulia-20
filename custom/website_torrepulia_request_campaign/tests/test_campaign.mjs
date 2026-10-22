import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const source = (await readFile(new URL('../static/src/js/campaign.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');
const editorSource = (await readFile(new URL('../static/src/js/campaign_options.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');
const iframeSource = (await readFile(new URL('../static/src/js/campaign.edit.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');
const storeSource = await readFile(new URL('../../website_torrepulia_request/static/src/js/request_store.js', import.meta.url), 'utf8');
const { RequestSelectionStore } = await import(`data:text/javascript;base64,${Buffer.from(storeSource).toString('base64')}`);

function fixture(fetch) {
    const context = { Interaction: class {}, registry: { category: () => ({ add() {} }) }, URLSearchParams,
        document: { documentElement: { lang: 'it' } },
        _t: (text, ...values) => text.replace(/%s/g, () => values.shift()), fetch, clearTimeout, setTimeout };
    runInNewContext(source + '\n globalThis.exports = { campaignCounts, campaignAmount, sameCampaignConfiguration, SeasonalCampaign };', context);
    return context.exports;
}

const line = (product_id, quantity, extra = {}) => ({ product_id, quantity, uom_id: 1,
    no_variant_value_ids: [], custom_values: {}, ...extra });
const configs = [{ product_id: 1, uom_id: 1 }, { product_id: 2, uom_id: 1 }];

test('seasonal stepper sets the total and ignores another click while the same row is pending', async () => {
    const { SeasonalCampaign } = fixture();
    const ui = new SeasonalCampaign();
    ui.active = true; ui.quantityBusy = new Set();
    const calls = []; let finish;
    ui.store = { state: {}, setConfiguration: (config, quantity) => {
        calls.push([config.product_id, quantity]);
        return new Promise(resolve => { finish = resolve; });
    } };
    ui.renderState = () => {};
    let pending;
    ui.perform = action => { pending = action(); };
    const input = { closest: () => ({ dataset: { campaignConfig: JSON.stringify(configs[0]) } }) };
    ui.setCardQuantity(input, 3);
    ui.setCardQuantity(input, 4);
    assert.deepEqual(calls, [[1, 3]]);
    assert.equal(ui.quantityBusy.size, 1);
    finish(); await pending;
    assert.equal(ui.quantityBusy.size, 0);
});

test('zero, one, multiple and outside products have distinct campaign/request counts', () => {
    const { campaignCounts } = fixture();
    for (const [lines, expected] of [
        [[], [0, 0, 0]], [[line(1, 1)], [1, 1, 0]],
        [[line(1, 3), line(2, 2), line(99, 4)], [5, 9, 4]],
    ]) {
        const state = { lines, quantity: lines.reduce((sum, row) => sum + row.quantity, 0) };
        const result = campaignCounts(state, configs);
        assert.deepEqual([result.campaign, result.request, result.other], expected);
    }
});

test('fixed summary amount covers the page counters and hides when a price is missing', () => {
    const { campaignAmount } = fixture();
    const state = { lines: [line(1, 2), line(2, 1), line(99, 5)], quantity: 8 };
    assert.equal(campaignAmount(state, [{ config: configs[0], price: 69 }, { config: configs[1], price: 13.8 }]), 151.8);
    assert.equal(campaignAmount({ lines: [], quantity: 0 }, [{ config: configs[0], price: 69 }]), 0);
    assert.equal(campaignAmount(state, [{ config: configs[0], price: 69 }, { config: configs[1], price: null }]), null);
});

test('variant, UoM and custom configurations never silently share a quantity control', () => {
    const { sameCampaignConfiguration, campaignCounts } = fixture();
    assert.equal(sameCampaignConfiguration(line(2, 1), configs[0]), false);
    assert.equal(sameCampaignConfiguration(line(1, 1, { uom_id: 2 }), configs[0]), false);
    assert.equal(sameCampaignConfiguration(line(1, 1, { no_variant_value_ids: [7] }), configs[0]), false);
    assert.equal(sameCampaignConfiguration(line(1, 1, { custom_values: { 7: 'Custom text' } }), configs[0]), false);
    const result = campaignCounts({ lines: [line(1, 2), line(2, 3)], quantity: 5 }, configs);
    assert.equal(result.campaign, 5);
});

test('catalog add two then seasonal set three preserves four outside campaign', async () => {
    const { campaignCounts } = fixture();
    let state = { website_id: 1, enabled: true, selection_id: null, revision: 0, quantity: 0, lines: [] };
    const store = new RequestSelectionStore({ makeId: () => String(Math.random()), transport: async (kind, payload) => {
        if (kind === 'read') return { ok: true, state: structuredClone(state), csrf_token: 'test' };
        const rows = structuredClone(state.lines);
        let row = rows.find(row => row.product_id === payload.product_id);
        if (!row) { row = line(payload.product_id, 0); rows.push(row); }
        row.quantity = payload.operation === 'add' ? row.quantity + Number(payload.quantity) : Number(payload.quantity);
        state = { ...state, selection_id: 'test', revision: state.revision + 1,
            lines: rows, quantity: rows.reduce((sum, row) => sum + row.quantity, 0) };
        return { ok: true, state: structuredClone(state) };
    } });
    await store.add({ product_id: 99, uom_id: 1 }, 4);
    await store.add(configs[0], 2);
    await store.setConfiguration(configs[0], 3);
    const result = campaignCounts(store.state, configs);
    assert.deepEqual([result.campaign, result.request, result.other], [3, 7, 4]);
    await store.setConfiguration(configs[1], 2);
    assert.equal(store.state.quantity, 9);
});

test('out-of-order campaign fetch cannot overwrite newer selected campaign', async () => {
    let resolveOld;
    const { SeasonalCampaign } = fixture(url => url.includes('campaign_id=1')
        ? new Promise(resolve => { resolveOld = resolve; })
        : Promise.resolve({ ok: true, json: async () => ({ html: 'NEW', open: true, configurations: [] }) }));
    const ui = new SeasonalCampaign(); ui.active = true;
    ui.el = { dataset: { campaign: '{"id":1}' } }; ui.holder = { innerHTML: 'ORIGINAL' }; ui.store = { state: null };
    const old = ui.load();
    ui.el.dataset.campaign = '{"id":2}'; await ui.load();
    resolveOld({ ok: true, json: async () => ({ html: 'OLD', open: true }) }); await old;
    assert.equal(ui.holder.innerHTML, 'NEW');
});

test('Builder demo hydration never accesses real request service and generates no IDs', async () => {
    const { SeasonalCampaign } = fixture(async () => ({ ok: true, json: async () => ({ html: 'DEMO', open: true }) }));
    const ui = new SeasonalCampaign(); ui.active = true; ui.editing = true;
    ui.store = new Proxy({}, { get() { throw new Error('Real service accessed by preview'); } });
    const inputs = [{ value: '0' }, { value: '0' }]; const status = {};
    ui.el = { dataset: { demoState: 'multiple' } };
    ui.holder = { innerHTML: '', querySelectorAll: () => inputs, querySelector: () => status };
    await ui.load();
    assert.deepEqual(inputs.map(input => input.value), ['1', '2']);
    assert.ok(inputs.every(input => input.disabled));
    assert.ok(inputs.every(input => !Object.hasOwn(input, 'id')));
    ui.el.dataset.demoState = 'one'; await ui.load();
    assert.deepEqual(inputs.map(input => input.value), ['1', '0']);
    ui.el.dataset.demoState = 'zero'; await ui.load();
    assert.deepEqual(inputs.map(input => input.value), ['0', '0']);
});

test('campaign management opens effective default form and ignores close after snippet removal', async () => {
    const context = { BaseOptionComponent: class {}, Plugin: class {},
        registry: { category: () => ({ add() {} }) } };
    runInNewContext(editorSource + '\n globalThis.Option = SeasonalCampaignOption;', context);
    const element = { dataset: {}, isConnected: true, events: [], dispatchEvent(event) { this.events.push(event.type); } };
    let opened;
    context.browser = { open: (...args) => { opened = args; } };
    const option = new context.Option();
    option.env = { getEditingElement: () => element };
    option.window = { CustomEvent: class { constructor(type) { this.type = type; } } };
    option.services = { website: { currentWebsiteId: 7 },
        orm: { async read(model, ids, fields) {
            assert.equal(model, 'website'); assert.equal(ids[0], 7); assert.equal(fields[0], 'torrepulia_campaign_id');
            return [{ torrepulia_campaign_id: [9, 'Configured default'] }];
        } }, action: { async doAction(value, callbacks) { action = value; options = callbacks; } } };
    await option.manage();
    assert.deepEqual(opened, ['/odoo/action-website_torrepulia_request_campaign.action_campaigns/9', '_blank', 'noopener']);
    assert.deepEqual(element.events, []);
});

test('iframe edit registration enables isolated preview before frontend interaction starts', () => {
    class FrontendInteraction { setup() { this.setupCalled = true; } }
    let registered;
    const context = { SeasonalCampaign: FrontendInteraction,
        registry: { category(name) {
            assert.equal(name, 'public.interactions.edit');
            return { add(key, value) { registered = value; } };
        } } };
    runInNewContext(iframeSource, context);
    const Preview = registered.mixin(registered.Interaction);
    const preview = new Preview();
    preview.setup();
    assert.equal(preview.setupCalled, true);
    assert.equal(preview.editing, true);
});

test('save cleaner removes runtime products/prices/counts for moved or duplicated snippets', () => {
    const contexts = [];
    // The parent editor has no frontend SeasonalCampaign module. Loading the
    // options there must work without registering iframe interactions.
    const context = { BaseOptionComponent: class {}, Plugin: class {},
        registry: { category: () => ({ add() {} }) } };
    runInNewContext(editorSource + '\n globalThis.clean = cleanCampaigns;', context);
    function snippet() {
        const holder = { children: ['PERSONAL PRICE AND QUANTITY'], replaceChildren(child) { this.children = [child]; } };
        const review = { children: ['PERSONAL CONTACT AND PRIVACY'], replaceChildren(child) { this.children = [child]; } };
        return { querySelector: selector => selector === '.tp-campaign-content' ? holder : review, holder, review };
    }
    const a = snippet(), b = snippet();
    const root = { querySelectorAll: () => [a, b], matches: () => false,
        ownerDocument: { createElement: tag => ({ tag }) } };
    assert.equal(context.clean(root), root);
    context.clean(root);
    for (const el of [a, b]) {
        assert.equal(el.holder.children.length, 1);
        assert.equal(el.holder.children[0].textContent, 'Caricamento della campagna…');
        assert.equal(el.review.children.length, 1);
        assert.match(el.review.children[0].textContent, /Nessun dato personale/);
    }
    const single = { ...a, matches: () => true, querySelectorAll: () => [], ownerDocument: root.ownerDocument };
    context.clean(single);
    assert.equal(single.holder.children.length, 1);
});
