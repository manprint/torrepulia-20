"""Validate module syntax, declared files and portable static XML references."""
import ast
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
from lxml import etree

ROOT=Path(__file__).resolve().parents[1]
manifest=ast.literal_eval((ROOT/'__manifest__.py').read_text(encoding='utf-8'))
errors=[]
python_files=[p for p in ROOT.rglob('*.py') if '__pycache__' not in p.parts]
for path in python_files:
    ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
xml_files=list((ROOT/'views').rglob('*.xml'))+list((ROOT/'data').rglob('*.xml'))+list((ROOT/'static/src/xml').rglob('*.xml'))
checked=set()
for path in xml_files:
    document=etree.parse(str(path))
    for element in document.iter():
        for name in ['src','href','poster','srcset']:
            value=element.get(name) or ''
            urls=[part.strip().rsplit(' ',1)[0] for part in value.split(',')] if name=='srcset' else [value]
            for url in urls:
                prefix='/website_torrepulia_theme/'
                if not url.startswith(prefix):continue
                relative=unquote(urlsplit(url).path[len(prefix):])
                checked.add(relative)
                if not (ROOT/relative).is_file():errors.append({'source':str(path.relative_to(ROOT)),'missing':relative})
for name in manifest['data']:
    if not (ROOT/name).is_file():errors.append({'manifest_data_missing':name})
for paths in manifest['assets'].values():
    for name in paths:
        prefix='website_torrepulia_theme/'
        if isinstance(name,str) and name.startswith(prefix):
            relative=name[len(prefix):]
            if not list(ROOT.glob(relative)):errors.append({'manifest_asset_missing':relative})
result={'version':manifest['version'],'python_files':len(python_files),'xml_files':len(xml_files),
        'static_references':len(checked),'errors':errors}
(ROOT/'docs/qa-final/source-release-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
assert not errors,errors
