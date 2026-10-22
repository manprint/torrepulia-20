"""One-off cleanup of the saved homepage (20.0.3.8.0 migration).

The Builder copy carries literal "&nbsp;" text, a double full stop, the
Builder rotate-in animation on the Regina bottle and h3 value proofs right
under the hero h1. Every language of the stored arch is cleaned; anything
the owner has since rewritten is simply not matched. A disabled copy of each
changed view is kept, like the previous content procedures in tools/.
"""
import json
import re
from datetime import datetime

HOME_KEY = 'website_torrepulia_theme.page_home_view'
REPLACEMENTS = (
    ('e&amp;nbsp;dedizione', 'e dedizione'),
    ('Michele.&amp;nbsp; Siamo', 'Michele. Siamo'),
    ('frante.  Oggi &amp;nbsp;noi', 'frante. Oggi noi'),
    ('tua tavola..', 'tua tavola.'),
    ('>&amp;nbsp;Scopri la storia', '>Scopri la storia'),
    (' o_anim_rotate_in o_animate o_animate_on_scroll', ''),
    (' style="--wanim-intensity: 23; animation-name: dummy;"', ''),
    (' data-scroll-zone-start="0" data-scroll-zone-end="100"', ''),
)
VALUE_PROOFS = re.compile(r'<section[^>]*data-snippet="s_torrepulia_value_proofs".*?</section>', re.S)


def clean_arch(arch):
    for old, new in REPLACEMENTS:
        arch = arch.replace(old, new)
    return VALUE_PROOFS.sub(lambda match: re.sub(r'<(/?)h3\b', r'<\1h2', match.group(0)), arch)


def cleanup_home(env):
    views = env['ir.ui.view'].sudo().with_context(active_test=False).search([('key', '=', HOME_KEY)])
    for view in views:
        # Raw jsonb keeps every stored language, including pending Builder ones.
        env.cr.execute('SELECT arch_db FROM ir_ui_view WHERE id = %s', [view.id])
        stored = env.cr.fetchone()[0] or {}
        cleaned = {lang: clean_arch(arch) for lang, arch in stored.items()}
        if cleaned == stored:
            continue
        view.copy({'name': 'Before editorial cleanup', 'active': False, 'arch_fs': False,
                   'key': 'website_torrepulia_theme.before_editorial_cleanup_%s_%s' % (
                       view.id, datetime.now().strftime('%Y%m%d_%H%M%S'))})
        env.cr.execute('UPDATE ir_ui_view SET arch_db = %s WHERE id = %s', [json.dumps(cleaned), view.id])
    env['ir.ui.view'].invalidate_model(['arch_db'])
    env.transaction.invalidate_ormcache('templates')
