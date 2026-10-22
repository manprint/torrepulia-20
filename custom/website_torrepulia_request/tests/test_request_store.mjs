import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../static/src/js/request_store.js', import.meta.url), 'utf8');
const { RequestSelectionStore } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

function fixture() {
    let state = { website_id: 9, enabled: true, selection_id: null, revision: 0, quantity: 0, lines: [] };
    const operations = new Set();
    const calls = [];
    let failResponses = 0;
    let reads = 0;
    const storageValues = new Map();
    const storage = { setItem: (k, v) => storageValues.set(k, v),
        getItem: k => storageValues.get(k), removeItem: k => storageValues.delete(k) };
    const transport = async (kind, body) => {
        if (kind === 'read') {
            reads++;
            return { ok: true, csrf_token: 'test-csrf', state: structuredClone(state) };
        }
        calls.push(structuredClone(body));
        if (!operations.has(body.operation_id)) {
            if (body.revision !== state.revision || body.selection_id !== state.selection_id) {
                return { ok: false, code: 'conflict', state: structuredClone(state) };
            }
            operations.add(body.operation_id);
            state = { ...state, selection_id: 'test-selection', revision: state.revision + 1,
                quantity: body.operation === 'add' ? state.quantity + Number(body.quantity)
                    : body.operation === 'set' || body.operation === 'set_configuration' ? Number(body.quantity) : 0 };
        }
        if (failResponses > 0) {
            failResponses--;
            throw new Error('Committed but response lost');
        }
        return { ok: true, state: structuredClone(state) };
    };
    let next = 0;
    const create = () => new RequestSelectionStore({ transport, storage, makeId: () => `operation-${++next}` });
    return { create, calls, storageValues, fail: n => { failResponses = n; },
        current: () => state, reads: () => reads,
        remote: quantity => { state = { ...state, revision: state.revision + 1, quantity }; } };
}

test('catalog increments, seasonal sets, every subscribed surface gets server totals', async () => {
    const f = fixture();
    const store = f.create();
    const catalog = [], seasonal = [], header = [], summary = [];
    for (const values of [catalog, seasonal, header, summary]) {
        store.subscribe(state => values.push(state.quantity));
    }
    await store.add({ product_id: 1 }, 2);
    await store.setConfiguration({ product_id: 1 }, 3);
    for (const values of [catalog, seasonal, header, summary]) {
        assert.deepEqual(values, [0, 2, 3]);
    }
    assert.equal(f.current().quantity, 3);
    assert.throws(() => { store.state.quantity = 100; }, TypeError);
});

test('simultaneous local edits serialize using the latest server revision', async () => {
    const f = fixture();
    const store = f.create();
    await Promise.all([store.add({ product_id: 1 }, 2), store.add({ product_id: 1 }, 3)]);
    assert.equal(store.state.quantity, 5);
    assert.deepEqual(f.calls.map(c => c.revision), [0, 1]);
});

test('many widgets starting on the same catalog share one bootstrap read', async () => {
    const f = fixture();
    const store = f.create();
    await Promise.all(Array.from({ length: 50 }, () => store.read()));
    assert.equal(f.reads(), 1);
    await store.read();
    assert.equal(f.reads(), 2);
});

test('lost response retries exactly the same increment identifier', async () => {
    const f = fixture();
    f.fail(1);
    const store = f.create();
    await store.add({ product_id: 1 }, 2);
    assert.equal(store.state.quantity, 2);
    assert.equal(f.calls[0].operation_id, f.calls[1].operation_id);
    assert.deepEqual(f.calls[0], f.calls[1]);
});

test('ambiguous operation survives navigation and blocks accidental new increments', async () => {
    const f = fixture();
    f.fail(2);
    const oldPage = f.create();
    await assert.rejects(oldPage.add({ product_id: 1 }, 2), e => e.code === 'network');
    await assert.rejects(oldPage.add({ product_id: 1 }, 2), e => e.code === 'pending');
    const newPage = f.create();
    await newPage.retryPending();
    assert.equal(newPage.state.quantity, 2);
    assert.equal(f.calls[2].operation_id, f.calls[0].operation_id);
    assert.equal(f.storageValues.size, 0);
});

test('cross-tab conflict refreshes authoritative state without overwriting it', async () => {
    const f = fixture();
    const store = f.create();
    await store.add({ product_id: 1 }, 2);
    f.remote(7);
    await assert.rejects(store.setQuantity('key', 3), e => e.code === 'conflict');
    assert.equal(store.state.quantity, 7);
    assert.equal(f.current().quantity, 7);
    await store.setQuantity('key', 3);
    assert.equal(store.state.quantity, 3);
});

test('delayed responses cannot roll back revision or selection epoch', async () => {
    const f = fixture();
    const store = f.create();
    await store.add({ product_id: 1 }, 2);
    const first = structuredClone(store.state);
    await store.setQuantity('key', 3);
    assert.equal(store._accept(first, 99), false);
    assert.equal(store.state.quantity, 3);
    const newEpoch = { ...first, selection_id: 'new-selection', revision: 0, quantity: 0 };
    assert.equal(store._accept(newEpoch, 100), true);
    assert.equal(store._accept(first, 98), false);
    assert.equal(store.state.selection_id, 'new-selection');
});

test('returning to a page rereads the server and one broken subscriber is isolated', async () => {
    const f = fixture();
    const store = f.create();
    store.subscribe(() => { throw new Error('broken widget'); });
    const values = [];
    store.subscribe(state => values.push(state.quantity));
    await store.read();
    f.remote(6);
    await store.read();
    assert.deepEqual(values, [0, 6]);
});

test('binding hydrates only runtime properties and restores Builder placeholders', async () => {
    let bindingSource = await readFile(new URL('../static/src/js/request_binding.js', import.meta.url), 'utf8');
    bindingSource = bindingSource.replace(/^import .*;\n/gm, '');
    const shim = `class Interaction { cleanups = []; services = {}; registerCleanup(fn) { this.cleanups.push(fn); } }
        const registry = { category: () => ({ add() {} }) }; const _t = text => text;\n`;
    const { RequestSelectionBinding } = await import(`data:text/javascript;base64,${Buffer.from(shim + bindingSource).toString('base64')}`);
    const owner = { dataset: { tpRequestConfig: '{"product_id":1,"uom_id":1}' } };
    const count = { textContent: '0' };
    const message = { textContent: '' };
    const input = { textContent: '', value: '0', defaultValue: '0', dataset: {}, closest: () => owner };
    const serialized = () => `<input value="${input.defaultValue}"><span>${count.textContent}</span><p>${message.textContent}</p>`;
    const before = serialized();
    const binding = new RequestSelectionBinding();
    binding.el = { querySelectorAll: selector => selector.includes(',') ? [count, message, input]
        : selector === '[data-tp-request-count]' ? [count]
            : selector === '[data-tp-request-quantity]' ? [input]
                : selector === '[data-tp-request-message]' ? [message] : [] };
    const configBefore = owner.dataset.tpRequestConfig;
    const state = { quantity: 3, lines: [{ key: 'a', product_id: 1, uom_id: 1, quantity: 3,
        no_variant_value_ids: [], custom_values: {}, available: true }], summary_url: '/request' };
    binding.services['torrepulia.request'] = { subscribe: fn => { fn(state); return () => {}; }, read: async () => state };
    await binding.start();
    assert.equal(input.value, '3');
    assert.equal(input.defaultValue, '0');
    assert.equal(owner.dataset.tpRequestConfig, configBefore);
    binding.cleanups.reverse().forEach(fn => fn());
    assert.equal(serialized(), before);
});
