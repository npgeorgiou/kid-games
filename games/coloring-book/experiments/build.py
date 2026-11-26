#!/usr/bin/env python3
"""Build src/brushes.html into one self-contained brushes.html (the tuning page): inlines src/brush-core.js,
each family's Krita presets (krita/presets/) and its Krita reference picture (references/krita/)."""
import base64, json, pathlib, re
here = pathlib.Path(__file__).resolve().parent
FAMILIES = [  # the families built so far, in the README's order; row: where that preset's strip starts in the picture (x, y), 880x150
    ('Eraser', 'a-erasers.png', [('Eraser_Circle', 'a)_Eraser_Circle', (10, 10)), ('Eraser_Small', 'a)_Eraser_Small', (10, 180)), ('Eraser_Soft', 'a)_Eraser_Soft', (10, 350))]),
    ('Markers', 'e-markers.png', [('Marker_Chisel_Smooth', 'e)_Marker_Chisel_Smooth', (10, 10)), ('Marker_Details', 'e)_Marker_Details', (10, 180)), ('Marker_Dry', 'e)_Marker_Dry', (10, 350))]),
]
MIME = {'.png': 'image/png', '.svg': 'image/svg+xml'}
def data_url(f): return 'data:%s;base64,%s' % (MIME.get(f.suffix, 'application/octet-stream'), base64.b64encode(f.read_bytes()).decode())
fams = [{'name': name, 'picture': 'data:image/png;base64,' + base64.b64encode((here / 'references' / 'krita' / pic).read_bytes()).decode(),
         'presets': [{'id': pid, 'file': fn, 'text': (here / 'krita' / 'presets' / (fn + '.txt')).read_text(encoding='utf-8'), 'row': list(row)} for pid, fn, row in presets]}
        for name, pic, presets in FAMILIES]
assets = {}  # every tip and texture the presets name
for fam in fams:
    for p in fam['presets']:
        for name in re.findall(r'filename="([^"]+)"', p['text']) + re.findall(r'^Texture/Pattern/Name = (.+)$', p['text'], re.M):
            f = here / 'krita' / ('patterns' if name in re.findall(r'^Texture/Pattern/Name = (.+)$', p['text'], re.M) else 'tips') / name
            assets[name] = data_url(f)
out = (here / 'src' / 'brushes.html').read_text(encoding='utf-8')
out = out.replace('/*%BRUSH_CORE%*/', (here / 'src' / 'brush-core.js').read_text(encoding='utf-8')).replace('/*%FAMILIES%*/[]', json.dumps(fams)).replace('/*%ASSETS%*/{}', json.dumps(assets))
(here / 'brushes.html').write_text(out, encoding='utf-8')
print('wrote brushes.html', len(out), 'bytes')
