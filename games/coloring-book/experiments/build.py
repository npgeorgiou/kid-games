#!/usr/bin/env python3
"""Build src/brushes.html into one self-contained brushes.html (the tuning page): inlines src/brush-core.js,
each family's Krita presets (krita/presets/) and its Krita reference picture (references/krita/)."""
import base64, json, pathlib
here = pathlib.Path(__file__).resolve().parent
FAMILIES = [  # the families built so far, in the README's order; row: where that preset's strip starts in the picture (x, y), 880x150
    ('Eraser', 'a-erasers.png', [('Eraser_Circle', 'a)_Eraser_Circle', (10, 10)), ('Eraser_Small', 'a)_Eraser_Small', (10, 180)), ('Eraser_Soft', 'a)_Eraser_Soft', (10, 350))]),
]
fams = [{'name': name, 'picture': 'data:image/png;base64,' + base64.b64encode((here / 'references' / 'krita' / pic).read_bytes()).decode(),
         'presets': [{'id': pid, 'file': fn, 'text': (here / 'krita' / 'presets' / (fn + '.txt')).read_text(encoding='utf-8'), 'row': list(row)} for pid, fn, row in presets]}
        for name, pic, presets in FAMILIES]
out = (here / 'src' / 'brushes.html').read_text(encoding='utf-8')
out = out.replace('/*%BRUSH_CORE%*/', (here / 'src' / 'brush-core.js').read_text(encoding='utf-8')).replace('/*%FAMILIES%*/[]', json.dumps(fams))
(here / 'brushes.html').write_text(out, encoding='utf-8')
print('wrote brushes.html', len(out), 'bytes')
