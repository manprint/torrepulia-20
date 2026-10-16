"""Fetch the actual CSS bundle to diagnose compilation, without browser tests."""
import requests
from lxml import html

base = 'http://127.0.0.1:8069'
session = requests.Session()
response = session.get(base + '/web/login', params={'db': 'torrepulia_cinematic_install'}, timeout=60)
response.raise_for_status()
response = session.get(base + '/', timeout=60)
response.raise_for_status()
root = html.fromstring(response.text)
stylesheets = root.xpath('//link[@rel="stylesheet"]/@href')
found = False
for url in stylesheets:
    if '/web/assets/' not in url:
        continue
    css = session.get(base + url if url.startswith('/') else url, timeout=120)
    css.raise_for_status()
    if 'Incompatible units' in css.text or 'style compilation failed' in css.text.lower():
        raise RuntimeError('The served stylesheet still contains a compilation error.')
    if '.mc-home-closing' in css.text:
        found = True
        print('Frontend CSS compiled and served:', css.status_code, len(css.content), 'bytes', url)
if not found:
    raise RuntimeError('The served frontend CSS does not contain the closing-section rules.')
