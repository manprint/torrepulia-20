"""Conservative reference inventory: runtime views, source and generated asset families."""
import ast
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'qa-final'
manifest = ast.literal_eval((ROOT / '__manifest__.py').read_text(encoding='utf-8'))
runtime = [json.loads(path.read_text(encoding='utf-8')) for path in OUT.glob('runtime-*.json')]
if len(runtime) < 2:
    raise RuntimeError('Refresh both database inventories with inventory_runtime.py before planning asset cleanup.')
production = []
for folder in ['models', 'controllers', 'views', 'data', 'static/src/js', 'static/src/scss', 'static/src/xml']:
    production.extend(path for path in (ROOT / folder).rglob('*') if path.is_file() and path.suffix in ['.py','.xml','.js','.scss','.csv'])
production += [ROOT / '__manifest__.py']
texts = '\n'.join(path.read_text(encoding='utf-8') for path in production)
texts += '\n' + json.dumps(runtime, ensure_ascii=False)
texts = unquote(texts)
unused = []
retained = []
for path in (ROOT / 'static').rglob('*'):
    if not path.is_file() or path.suffix.lower() not in ['.webp','.png','.jpg','.jpeg','.svg','.mp4','.webm','.ttf','.woff','.woff2']:
        continue
    relative = path.relative_to(ROOT).as_posix()
    dynamic = False
    if '/cinematic/campaign/' in relative:
        dynamic = bool(re.match(r'(hero|family|olive|land|still-life|bottle|box|duetto|tin)-(\d+|desktop|mobile)', path.name))
    if '/cinematic/images/' in relative:
        dynamic = bool(re.match(r'(uliveto-hero|harvest|culinary-campaign|family-archive|family-today|territory)-\d+\.webp', path.name))
    used = path.name in texts or relative in texts or dynamic
    (retained if used else unused).append({'path':relative,'bytes':path.stat().st_size,'reason':'source/runtime or generated family' if used else 'no source/runtime reference'})

keepers = {'local_qa.py','diagnose_builder.py','final_home_qa.py','hero_layout_qa.py','about_editorial.py','about_editorial_qa.py','roots_closing.py','roots_closing_qa.py','closing_blend_qa.py','header_media_qa.py','oil_editorial.py','oil_editorial_qa.py','inventory_runtime.py','inspect_compiled_css.py','plan_module_cleanup.py','final_builder_qa.py','archive_module_cleanup.ps1'}
keepers.update({'oil_production.py','oil_production_qa.py','prepare_production_media.py','oil_closing.py','release_check.py','release_browser_qa.py'})
keepers.add('regina_cta.py')
tools = [{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'reason':'retired one-time migration/generation or superseded fixture'}
    for p in (ROOT/'tools').glob('*') if p.is_file() and p.name not in keepers]
historical = [p for p in (ROOT/'docs').glob('*') if p.is_file() and p.suffix in ['.xml','.json']]
for directory in [ROOT/'docs'/'qa',ROOT/'docs'/'cinematic']:
    if directory.exists():historical.extend(p for p in directory.rglob('*') if p.is_file())
historical.extend((OUT).glob('*.png'))
historical.extend((OUT).glob('runtime-*.json'))
historical.extend((OUT).glob('axe-*.min.js'))
docs=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'reason':'historical evidence or intermediate owner snapshot; archived outside runtime module'} for p in historical]
report = {'unused_assets':unused,'retained_assets':retained,'retired_tools':tools,'historical_docs':docs,
    'active_bag_views':[(v['key'],v['active']) for data in runtime for v in data['views'] if 'tp-bib-blueprint' in v['arch']],
    'totals':{'unused_assets':len(unused),'asset_bytes':sum(p['bytes'] for p in unused),'retired_tools':len(tools),'tool_bytes':sum(p['bytes'] for p in tools),'historical_docs':len(docs),'historical_bytes':sum(p['bytes'] for p in docs)}}
(OUT/'cleanup-plan.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report['totals']))
for item in unused:
    print('UNUSED',item['path'],item['bytes'])
print('SVG RUNTIME VIEWS',report['active_bag_views'])
