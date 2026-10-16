"""Helpers for explicit, local-only QA; no production credentials are changed."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT.parents[2] / 'torrepulia-20-local-dev'


def shell(source, database='odoo_dev'):
    assert database in ['odoo_dev','torrepulia_cinematic_install']
    result = subprocess.run([
        'docker', 'compose', 'exec', '-T', 'odoo', 'odoo', 'shell', '-d', database,
        '--db_host=db', '--db_user=odoo', '--db_password=change-me', '--no-http',
        '--log-level=error', '--log-handler=odoo:ERROR', '--dev=',
    ], input=f"assert env.cr.dbname == '{database}'\n" + source, text=True,
       encoding='utf-8', capture_output=True, cwd=STACK)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()
