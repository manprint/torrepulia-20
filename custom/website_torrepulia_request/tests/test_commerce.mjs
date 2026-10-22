import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const source = (await readFile(new URL('../static/src/js/commerce.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');

function fixture() {
    const calls = [], redirects = [];
    class CartService {
        static dependencies = ['notification'];
        setup() { return 'native-setup'; }
        async add(product, options) { calls.push({ native: true, product, options }); return 9; }
    }
    const dependencyReference = CartService.dependencies;
    class ProductPage {
        async _onChangeCombination(event, parent, combination) {
            calls.push({ nativeCombination: combination });
            const input = parent.querySelector('input[name="add_qty"]');
            input.value = '0'; input.dataset.max = '0';
        }
    }
    const document = { body: { dataset: { tpRequestMode: '1' } } };
    const info = { name: 'La Regina', product_id: 42, uom_id: 1, url: '/shop/configure', requires_configuration: false };
    const store = { read: async () => {}, csrfToken: 'test',
        state: { limits: { min: 1, max: 50, step: 1 } },
        add: async (config, qty) => { calls.push({ config, qty }); return {
            addition: { name: 'La Regina — 5 L', quantity: qty, subtotal_display: '207,00 €' },
            lines: [{ product_id: config.product_id, uom_id: config.uom_id, name: 'La Regina — 5 L' }] }; } };
    function patch(target, extension) {
        const parent = Object.create(Object.getPrototypeOf(target));
        Object.defineProperties(parent, Object.getOwnPropertyDescriptors(target));
        Object.setPrototypeOf(extension, parent);
        Object.defineProperties(target, Object.getOwnPropertyDescriptors(extension));
    }
    const context = { document, window: { location: { assign: url => redirects.push(url) } },
        fetch: async path => ({ ok: true, json: async () => path.includes('/resolve') ? { product_id: 99 } : info }),
        CartService, ProductPage, Interaction: class {}, patch, URLSearchParams,
        registry: { category: () => ({ add() {} }) }, _t: (text, ...args) => text.replace(/%s/g, () => args.shift()) };
    runInNewContext(source + '\n globalThis.testExports = { nativeConfiguration, RequestCommerce };', context);
    const cart = new CartService(); cart.setup({}, { 'torrepulia.request': store });
    return { cart, calls, redirects, info, document, store, ProductPage, dependencyReference,
        exports: context.testExports };
}

test('native mode delegates original add and retains dependency array reference', async () => {
    const f = fixture();
    assert.ok(f.dependencyReference.includes('torrepulia.request'));
    f.document.body.dataset.tpRequestMode = '0';
    assert.equal(await f.cart.add({ productId: 42 }, { isBuyNow: true }), 9);
    assert.equal(f.calls[0].native, true);
});

test('simple buy-now increments request quantity without redirect or cart analytics', async () => {
    const f = fixture();
    assert.equal(await f.cart.add({ productTemplateId: 7, quantity: 2 }, { isBuyNow: true }), 0);
    assert.equal(f.calls.length, 1);
    assert.equal(f.calls[0].qty, 2);
    assert.equal(f.calls[0].config.product_id, 42);
    assert.equal(f.redirects.length, 0);
});

test('configurable tile requires explicit product page without arbitrary addition', async () => {
    const f = fixture(); f.info.requires_configuration = true;
    await f.cart.add({ productTemplateId: 7, quantity: 2 });
    assert.deepEqual(f.redirects, ['/shop/configure?tp_request_qty=2']);
    assert.equal(f.calls.length, 0);
});

test('configured product preserves actual variant, UoM, no-variant values and custom text', async () => {
    const f = fixture(); f.info.requires_configuration = true;
    await f.cart.add({ productTemplateId: 7, productId: 88, quantity: 3, uomId: 5,
        noVariantAttributeValues: [12], productCustomAttributeValues: [
            { custom_product_template_attribute_value_id: 12, custom_value: 'Client inscription' }] }, { isConfigured: true });
    const { config, qty } = f.calls[0];
    assert.equal(config.product_id, 88); assert.equal(config.uom_id, 5); assert.equal(qty, 3);
    assert.equal(config.no_variant_value_ids[0], 12);
    assert.equal(config.custom_values['12'], 'Client inscription');
    assert.equal(f.redirects.length, 0);
});

test('explicit dynamic combination resolves native variant before adding', async () => {
    const f = fixture(); f.info.requires_configuration = true;
    await f.cart.add({ productTemplateId: 7, quantity: 2, ptavs: [1, 2] }, { isConfigured: true });
    assert.equal(f.calls[0].config.product_id, 99);
    assert.equal(f.calls[0].qty, 2);
});

test('stock-zero combination preserves native hiding and quantity bound', async () => {
    const f = fixture();
    const input = { value: '3', dataset: {} };
    const parent = { querySelector: () => input };
    const page = new f.ProductPage(); page.services = { 'torrepulia.request': f.store };
    page._toggleDisable = () => { throw new Error('must not re-enable native stock controls'); };
    await page._onChangeCombination({}, parent,
        { is_storable: true, is_combination_possible: true, free_qty: 0, allow_out_of_stock_order: false });
    assert.equal(input.value, '0'); assert.equal(input.dataset.max, '0');
    assert.equal(input.dataset.tpRequestStockMax, '0');
});

test('sell when exhausted retains selected quantity and request limits', async () => {
    const f = fixture();
    const input = { value: '3', dataset: {} };
    const page = new f.ProductPage(); page.services = { 'torrepulia.request': f.store };
    await page._onChangeCombination({}, { querySelector: () => input },
        { is_storable: true, free_qty: 0, allow_out_of_stock_order: true });
    assert.equal(input.value, '3'); assert.equal(input.dataset.max, '50');
    assert.equal(await page._getUnavailableQty({ cart_qty: 12 }), 0);
});

test('confirmation gives product and added quantity, continue closes and review uses central URL', async () => {
    const f = fixture();
    class Element {
        constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.attributes = {}; }
        append(...children) { this.children.push(...children); }
        setAttribute(key, value) { this.attributes[key] = value; }
    }
    const doc = { createElement: tag => new Element(tag) };
    const root = new Element('main'); root.ownerDocument = doc;
    f.document.body.dataset.tpRequestSummaryUrl = '/review-configured';
    const ui = new f.exports.RequestCommerce();
    ui.el = root; ui.active = true; ui.store = f.store;
    ui.addListener = (el, type, fn) => { el.listeners[type] = fn; };
    ui.registerCleanup = () => {};
    ui.createConfirmation();
    await f.cart.add({ productTemplateId: 7, quantity: 2 });
    const aside = root.children[0];
    assert.equal(aside.hidden, false);
    assert.match(aside.children[1].textContent, /Hai inserito 2 confezioni di: La Regina — 5 L/);
    assert.equal(aside.children[0].textContent, '✓ AGGIUNTO ALLA RICHIESTA');
    assert.equal(aside.children[2].textContent, 'Subtotale: 207,00 €');
    assert.equal(aside.children[2].hidden, false);
    const [close, review] = aside.children[4].children;
    assert.equal(close.textContent, 'Continua a scegliere');
    assert.equal(review.textContent, 'VAI AL RIEPILOGO'); assert.equal(review.href, '/review-configured');
    close.listeners.click(); assert.equal(aside.hidden, true);
    f.store.add = async () => ({ addition: { quantity: 1, name: 'Prezzi riservati' }, lines: [] });
    await f.cart.add({ productTemplateId: 7, quantity: 1 });
    assert.equal(aside.children[2].hidden, true);
    assert.equal(aside.children[2].textContent, '');
    assert.equal(f.redirects.length, 0);
});

test('switching real variants hides only exhausted variant action and shows its message', async () => {
    const f = fixture();
    const quantity = {}, button = {}, message = { dataset: { stockVariant: '88' }, hidden: true };
    const row = { querySelector: selector => selector === '.tp-catalog-quantity' ? quantity : button,
        querySelectorAll: () => [message] };
    let radios;
    const group = { querySelectorAll: () => radios, closest: () => row };
    const radio = (value, soldOut) => ({ value, dataset: { soldOut }, matches: () => true,
        closest: selector => selector === '.tp-catalog-variants' ? group : null });
    radios = [radio('88', '1'), radio('89', '0')];
    f.store.subscribe = () => () => {};
    const ui = new f.exports.RequestCommerce();
    ui.services = { 'torrepulia.request': f.store };
    ui.el = { querySelectorAll: () => [], querySelector: () => null };
    let click;
    ui.addListener = (el, type, callback) => { click = callback; };
    ui.registerCleanup = () => {}; ui.createConfirmation = () => {};
    await ui.start();
    click({ target: radios[0] });
    assert.equal(button.hidden, true); assert.equal(quantity.hidden, true);
    assert.equal(message.hidden, false); assert.equal(radios[0].checked, true);
    click({ target: radios[1] });
    assert.equal(button.hidden, false); assert.equal(quantity.hidden, false);
    assert.equal(message.hidden, true); assert.equal(radios[0].checked, false);
    assert.equal(f.calls.length, 0);
});
