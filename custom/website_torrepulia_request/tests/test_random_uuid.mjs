import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { runInNewContext } from 'node:vm';

const source = await readFile(new URL('../static/src/js/random_uuid.js', import.meta.url), 'utf8');

test('plain HTTP pages get an RFC 4122 identifier from getRandomValues', () => {
    // Insecure context: the browser exposes getRandomValues but not randomUUID.
    const crypto = { getRandomValues: (array) => webcrypto.getRandomValues(array) };
    runInNewContext(source, { globalThis: { crypto }, Uint8Array, Array });
    const ids = new Set(Array.from({ length: 50 }, () => crypto.randomUUID()));
    assert.equal(ids.size, 50);
    for (const id of ids) {
        assert.match(id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
        assert.match(id, /^[A-Za-z0-9_-]{16,64}$/);  // the server's operation_id rule
    }
});

test('a native randomUUID is left untouched', () => {
    const native = () => 'native';
    const crypto = { randomUUID: native, getRandomValues: () => {} };
    runInNewContext(source, { globalThis: { crypto }, Uint8Array, Array });
    assert.equal(crypto.randomUUID, native);
});
