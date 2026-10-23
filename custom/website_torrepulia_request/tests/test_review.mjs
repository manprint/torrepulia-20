import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';

const source = (await readFile(new URL('../static/src/js/review.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '').replace(/export /g, '');
const storeSource = await readFile(new URL('../static/src/js/request_store.js', import.meta.url), 'utf8');
const { RequestSelectionStore } = await import(`data:text/javascript;base64,${Buffer.from(storeSource).toString('base64')}`);

function fixture() {
    class RecaptchaForm { onSubmit() { return 'native'; } }
    const redirects = [];
    function patch(target, extension) {
        const parent = Object.create(Object.getPrototypeOf(target));
        Object.defineProperties(parent, Object.getOwnPropertyDescriptors(target));
        Object.setPrototypeOf(extension, parent);
        Object.defineProperties(target, Object.getOwnPropertyDescriptors(extension));
    }
    const context = { Interaction: class {}, RecaptchaForm, patch,
        ReCaptcha: class {}, registry: { category: () => ({ add() {} }) },
        _t: (text, ...args) => text.replace(/%s/g, () => args.shift()),
        window: { location: { assign: url => redirects.push(url) } } };
    runInNewContext(source + '\nglobalThis.exports = { SubmissionAttempt, RequestReview, renderCompactLines };', context);
    return { ...context.exports, RecaptchaForm, redirects };
}
const state = { selection_id: 'draft-a', revision: 3 };
const contact = { contact_name: 'Test', email: 'test@example.invalid', phone: '', notes: 'Keep my data', privacy_accepted: true };

test('review quantity change blocks repeated controls until authoritative response arrives', async () => {
    const { RequestReview } = fixture();
    const ui = new RequestReview(); ui.active = true;
    const busyStates = []; let release; let writes = 0;
    ui.setBusy = () => busyStates.push(Boolean(ui.changing));
    const pending = ui.change(() => { writes++; return new Promise(resolve => { release = resolve; }); });
    await ui.change(() => { writes++; });
    assert.equal(writes, 1);
    assert.equal(ui.changing, true);
    release(); await pending;
    assert.deepEqual(busyStates, [true, false]);
});

test('uncertain response retries the same submission even after shared selection rotates', async () => {
    const { SubmissionAttempt } = fixture();
    const bodies = [];
    let calls = 0, leads = 0;
    const attempt = new SubmissionAttempt({ makeId: () => 'same-operation', transport: async body => {
        bodies.push(structuredClone(body));
        if (calls++ === 0) { leads++; throw new Error('Response lost after commit'); }
        return { ok: true, reference: 'R-TEST', replayed: true, success_url: '/la-tua-richiesta/conferma' };
    } });
    await assert.rejects(attempt.submit(state, contact), error => error.code === 'uncertain');
    assert.ok(attempt.pending);
    const result = await attempt.submit({ selection_id: 'new-draft', revision: 0 }, { ...contact, notes: 'Different draft' });
    assert.equal(result.replayed, true);
    assert.deepEqual(bodies[1], bodies[0]);
    assert.equal(leads, 1);
    assert.equal(attempt.pending, null);
});

test('in-flight second submit cannot send a second network request', async () => {
    const { SubmissionAttempt } = fixture();
    let complete, calls = 0;
    const attempt = new SubmissionAttempt({ makeId: () => 'only-operation', transport: () => {
        calls++; return new Promise(resolve => { complete = resolve; });
    } });
    const first = attempt.submit(state, contact);
    await assert.rejects(attempt.submit(state, contact), error => error.code === 'busy');
    assert.equal(calls, 1);
    complete({ ok: true, reference: 'R-TEST' }); await first;
});

test('known validation failure allows correction without retaining stale contact payload', async () => {
    const { SubmissionAttempt } = fixture();
    const bodies = []; let id = 0;
    const attempt = new SubmissionAttempt({ makeId: () => `operation-${++id}`, transport: async body => {
        bodies.push(structuredClone(body));
        return bodies.length === 1 ? { ok: false, fields: ['email'], message: 'Email non valida' }
            : { ok: true, reference: 'R-TEST' };
    } });
    await assert.rejects(attempt.submit(state, contact), error => error.code === 'invalid' && error.fields[0] === 'email');
    assert.equal(attempt.pending, null);
    await attempt.submit(state, { ...contact, email: 'corrected@example.invalid' });
    assert.notEqual(bodies[1].operation_id, bodies[0].operation_id);
    assert.equal(bodies[1].email, 'corrected@example.invalid');
});

test('AJAX review form bypasses only the native synchronous recaptcha submission', () => {
    const { RecaptchaForm } = fixture();
    const normal = new RecaptchaForm(); normal.el = { matches: () => false };
    assert.equal(normal.onSubmit({}), 'native');
    const review = new RecaptchaForm(); review.el = { matches: () => true };
    assert.equal(review.onSubmit({}), undefined);
});

function uiFixture(transport) {
    const f = fixture();
    const values = Object.fromEntries(Object.entries(contact).map(([name, value]) => [name, { value, checked: value === true }]));
    const errors = [], busy = [];
    const ui = { active: true, busy: false, store: { state, read: async () => state,
        afterSubmission: async () => {} },
        recaptcha: { loadLibs: async () => {}, getToken: async () => ({}) },
        form: { elements: { namedItem: name => values[name] }, reportValidity: () => true,
            querySelector: () => null },
        el: { querySelector: () => ({ hidden: true }) },
        attempt: new f.SubmissionAttempt({ makeId: () => 'test-operation', transport }),
        setBusy(value) { this.busy = value; busy.push(value); },
        error(message, fields) { errors.push({ message, fields }); } };
    return { ...f, ui, values, errors, busy };
}

test('failed submit retains every contact value and never navigates to success', async () => {
    const f = uiFixture(async () => ({ ok: false, message: 'Verifica email', fields: ['email'] }));
    await f.RequestReview.prototype.submit.call(f.ui, { preventDefault() {} });
    assert.equal(f.values.email.value, contact.email);
    assert.equal(f.values.notes.value, contact.notes);
    assert.equal(f.values.privacy_accepted.checked, true);
    assert.equal(f.redirects.length, 0);
    assert.equal(f.ui.busy, false);
    assert.equal(f.errors[0].fields[0], 'email');
});

test('confirmed submission navigates immediately without publishing an empty draft first', async () => {
    const f = uiFixture(async () => ({ ok: true, reference: 'R-TEST', success_url: '/la-tua-richiesta/conferma' }));
    let refreshed = false;
    f.ui.store.afterSubmission = async () => { refreshed = true; };
    await f.RequestReview.prototype.submit.call(f.ui, { preventDefault() {} });
    assert.equal(refreshed, false);
    assert.equal(f.ui.completed, true);
    assert.deepEqual(f.redirects, ['/la-tua-richiesta/conferma']);
    assert.equal(f.errors.length, 0);
});

test('completed review ignores selection refresh while confirmation is loading', async () => {
    const f = uiFixture(async () => ({ ok: true }));
    f.ui.completed = true;
    await f.RequestReview.prototype.refresh.call(f.ui);
    assert.equal(f.redirects.length, 0);
    assert.equal(f.errors.length, 0);
});

test('submission refresh publishes authoritative fresh quantity to header and other tabs', async () => {
    let changed = 0;
    const store = new RequestSelectionStore({ onChanged: () => changed++, transport: async () => ({
        state: { website_id: 1, enabled: true, selection_id: 'fresh-draft', revision: 0, quantity: 0, lines: [] },
        csrf_token: 'fresh-test' }) });
    const quantities = [];
    store.subscribe(state => quantities.push(state.quantity));
    await store.afterSubmission();
    assert.equal(store.state.quantity, 0);
    assert.deepEqual(quantities, [0]);
    assert.equal(changed, 1);
});

test('seasonal summary renders all server lines once without another quantity editor', () => {
    const { renderCompactLines } = fixture();
    class Element {
        constructor(tag) { this.tag=tag; this.children=[]; }
        append(...nodes) { this.children.push(...nodes); }
        replaceChildren() { this.children=[]; }
    }
    const doc = {documentElement:{lang:'it'}, createElement:tag=>new Element(tag)};
    const holder = new Element('div'); holder.ownerDocument=doc;
    const state = {show_prices:true,lines:[
        {name:'Latta 5 LT',quantity:2,subtotal_display:'138,00 €'},
        {name:'Bottiglie fuori campagna',quantity:3,subtotal_display:'207,00 €',custom_text:['Etichetta personalizzata']}]};
    renderCompactLines(holder,state);
    assert.equal(holder.children.length,2);
    assert.equal(holder.children[0].children[0].children[0].textContent,'Latta 5 LT × 2');
    assert.equal(holder.children[0].children[1].textContent,'138,00 €');
    const flatten = node=>[node,...node.children.flatMap(flatten)];
    assert.ok(flatten(holder).every(node=>!['img','input','button'].includes(node.tag)));
    state.lines[0].quantity=3;
    renderCompactLines(holder,state);
    assert.equal(holder.children.length,2);
    assert.equal(holder.children[0].children[0].children[0].textContent,'Latta 5 LT × 3');
    state.show_prices=false;
    renderCompactLines(holder,state);
    assert.equal(holder.children[0].children.length,1);
    assert.ok(!flatten(holder).some(node=>String(node.textContent).includes('€')));
});

test('compact summary lets the visitor remove a line that is no longer available', () => {
    const { renderCompactLines } = fixture();
    class Element {
        constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {}; }
        append(...nodes) { this.children.push(...nodes); }
        replaceChildren() { this.children = []; }
        setAttribute(name, value) { this.attributes[name] = value; }
    }
    const doc = { documentElement: { lang: 'it' }, createElement: tag => new Element(tag) };
    const holder = new Element('div'); holder.ownerDocument = doc;
    renderCompactLines(holder, { show_prices: true, lines: [
        { key: 'old', name: 'Latta 5 LT', quantity: 1, available: false, warning: 'Prodotto archiviato.' },
        { key: 'new', name: 'Latta 5 LT (Filtrato)', quantity: 2, available: true, subtotal_display: '138,00 €' }] });
    const flatten = node => [node, ...node.children.flatMap(flatten)];
    const buttons = flatten(holder).filter(node => node.tag === 'button');
    assert.equal(buttons.length, 1);
    assert.equal(buttons[0].dataset.reviewRemove, 'old');
    assert.equal(buttons[0].attributes['aria-label'], 'Rimuovi Latta 5 LT');
});
