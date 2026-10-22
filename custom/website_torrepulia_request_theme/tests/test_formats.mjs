import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';
const source = (await readFile(new URL('../static/src/js/formats.js', import.meta.url), 'utf8'))
    .replace(/^import .*;\r?\n/gm, '');
function fixture(detail) {
    const calls=[];
    class CinematicCommerce { async willStart() { calls.push('native'); } }
    function patch(target, extension) {
        const parent=Object.create(Object.getPrototypeOf(target));
        Object.defineProperties(parent,Object.getOwnPropertyDescriptors(target));
        Object.setPrototypeOf(extension,parent);
        Object.defineProperties(target,Object.getOwnPropertyDescriptors(extension));
    }
    runInNewContext(source, { patch, CinematicCommerce, rpc:async (path,params)=>{calls.push(params);return {html:'QA'};} });
    const widget=new CinematicCommerce();
    widget.el={classList:{contains:()=>detail},dataset:{currentProduct:'42',productIds:'[{"id":42},{"id":43}]'}};
    return {widget,calls};
}
test('product detail excludes its current template in the server request', async()=>{
    const {widget,calls}=fixture(true);await widget.willStart();
    assert.equal(calls[0].exclude_template_id,42);
    assert.equal(calls[0].ids.join(','),'42,43');
    assert.equal(widget.data.html,'QA');
});
test('homepage and Builder format snippets retain native loading',async()=>{
    const {widget,calls}=fixture(false);await widget.willStart();assert.equal(calls[0],'native');
});
