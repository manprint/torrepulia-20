"""Give every legacy request its own epoch before applying NOT NULL/UNIQUE.

Odoo may evaluate a field default once while initialising an existing column;
a random field default alone is not a per-record migration.
Only new technical metadata on this addon's table is touched.
"""
import re
import secrets


def migrate(cr, version):
    cr.execute('ALTER TABLE torrepulia_request ADD COLUMN IF NOT EXISTS selection_id varchar')
    cr.execute('SELECT id, selection_id FROM torrepulia_request ORDER BY id')
    seen = set()
    for record_id, identity in cr.fetchall():
        if not isinstance(identity, str) or not re.fullmatch(r'[0-9a-f]{32}', identity) or identity in seen:
            identity = secrets.token_hex(16)
            while identity in seen:
                identity = secrets.token_hex(16)
            cr.execute('UPDATE torrepulia_request SET selection_id = %s WHERE id = %s', [identity, record_id])
        seen.add(identity)
