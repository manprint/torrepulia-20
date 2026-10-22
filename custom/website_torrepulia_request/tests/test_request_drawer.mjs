import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const source = (await readFile(new URL('../static/src/js/request_drawer.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');

function fixture(fetch) {
    const document = { body: { dataset: { tpRequestMode: '0' } } };
    const context = { Interaction: class {}, registry: { category: () => ({ add() {} }) }, document, fetch,
        _t: (text, ...args) => text.replace(/%s/g, () => args.shift()) };
    runInNewContext(source + '\nglobalThis.Drawer = RequestDrawer;', context);
    const ui = new context.Drawer();
    ui.active = true; ui.dialog = { open: true };
    ui.store = { state: { selection_id: 'visitor-a', revision: 4 } };
    ui.node = (tag, text) => ({ tag, textContent: text || '', children: [], append(...nodes) { this.children.push(...nodes); } });
    ui.content = { children: [], replaceChildren(...nodes) { this.children = nodes; }, append(...nodes) { this.children.push(...nodes); } };
    ui.total = ui.node('p'); ui.review = {};
    return { ui, document };
}

test('standard website leaves native header behaviour untouched', () => {
    const { ui } = fixture();
    ui.start();
    assert.equal(ui.services, undefined);
});

test('drawer ignores a delayed preview after closure and after a selection change', async () => {
    let release;
    const { ui } = fixture(() => new Promise(resolve => { release = resolve; }));
    const pending = ui.refresh();
    ui.dialog.open = false;
    release({ ok: true, json: async () => ({ state: { selection_id: 'visitor-a', revision: 4, lines: [] } }) });
    await pending;
    assert.equal(ui.content.children.length, 0);
    ui.dialog.open = true;
    const switched = ui.refresh();
    ui.store.state.selection_id = 'new-draft';
    release({ ok: true, json: async () => ({ state: { selection_id: 'visitor-a', revision: 4, lines: [] } }) });
    await switched;
    assert.equal(ui.content.children.length, 0);
});

test('drawer renders authoritative quantities, central URL and no hidden price placeholders', async () => {
    const state = { selection_id: 'visitor-a', revision: 4, summary_url: '/riepilogo-configurato',
        lines: [{ name: 'Latta 5 LT', quantity: 3, attributes: ['Filtrato'] }] };
    const { ui } = fixture(async () => ({ ok: true, json: async () => ({ state }) }));
    await ui.refresh();
    assert.equal(ui.review.href, '/riepilogo-configurato');
    assert.equal(ui.total.hidden, true);
    const details = ui.content.children[0].children[0];
    assert.deepEqual(details.children.map(node => node.textContent), ['Latta 5 L', 'Filtrato', 'Quantità: 3']);
});

test('late failed preview cannot replace a more recent successful view', async () => {
    const releases = [];
    const { ui } = fixture(() => new Promise(resolve => releases.push(resolve)));
    let failures = 0; ui.failed = () => { failures++; };
    const old = ui.refresh(), current = ui.refresh();
    releases[1]({ ok: true, json: async () => ({ state: {
        selection_id: 'visitor-a', revision: 4, summary_url: '/current', lines: [] } }) });
    await current;
    releases[0]({ ok: false }); await old;
    assert.equal(failures, 0);
    assert.equal(ui.review.href, '/current');
});
