#!/usr/bin/env python3
"""Build src/brushes.html into one self-contained brushes.html (the brushes page): inlines src/brush-core.js,
each family's Krita presets (krita/presets/) and its Krita reference picture (references/krita/)."""
import base64, gzip, json, pathlib, re, struct
here = pathlib.Path(__file__).resolve().parent
FAMILIES = [  # the families built so far, in the README's order: name, Krita's picture, its zoom to Krita's scale, the presets in the picture's order,
    # where the first preset's strip starts (x, y) and the step down to the next one, all in the picture's own pixels
    ('Eraser', 'a-erasers.png', 1, ['a)_Eraser_Circle', 'a)_Eraser_Small', 'a)_Eraser_Soft'], (10, 10), 170),
    ('Markers', 'e-markers.png', 1, ['e)_Marker_Chisel_Smooth', 'e)_Marker_Details', 'e)_Marker_Dry'], (10, 10), 170),
    ('Pencils', 'c-pencils.png', 1, ['c)_Pencil-1_Hard', 'c)_Pencil-2', 'c)_Pencil-3_Large_4B', 'c)_Pencil-4_Soft', 'c)_Pencil-5_Tilted', 'c)_Pencil-6_Quick_Shade'], (10, 10), 165),
    ('Chalk, Pastel, Charcoal', 'h-chalk-pastel-charcoal.png', 1, ['h)_Chalk_Details', 'h)_Chalk_Grainy', 'h)_Chalk_Soft', 'h)_Charcoal_pencil_large', 'h)_Charcoal_Pencil_Medium', 'h)_Charcoal_Pencil_Thin'], (10, 10), 165),
    ('Dry Painting', 'f-dry-painting.png', 1, ['f)_Bristles-1_Details', 'f)_Bristles-2_Flat_Rough', 'f)_Bristles-3_Large_Smooth', 'f)_Bristles-4_Glaze', 'f)_Bristles-5_Flat', 'f)_Charcoal_Rock_Soft', 'f)_Dry_Roller'], (8, 6), 141.5),
    ('Dry Textured', 'g-dry-painting-textured.png', 1, ['g)_Dry_Bristles_Eroded', 'g)_Dry_Bristles', 'g)_Dry_Brushing', 'g)_Dry_Textured_Creases'], (10, 10), 170),
    ('Stamps', 'z-stamps.png', 900 / 403, ['z)_Stamp_Bokeh', 'z)_Stamp_Floor', 'z)_Stamp_Grass', 'z)_Stamp_Grass_Patch', 'z)_Stamp_Hearts', 'z)_Stamp_Herbals', 'z)_Stamp_Leaves',
        'z)_Stamp_Mountains_Distant', 'z)_Stamp_Shoujo_Bubbles', 'z)_Stamp_Sparkles', 'z)_Stamp_Stylised_Tree', 'z)_Stamp_Vegetal', 'z)_Stamp_Water'], (4, 4), 992 / 13),
    ('Wet painting', 'i-wet-painting.png', 1, ['i)_Wet_Bristles', 'i)_Wet_Bristles_Rough', 'i)_Wet_Circle', 'i)_Wet_Knife', 'i)_Wet_Paint_Details', 'i)_Wet_Paint', 'i)_Wet_Smear', 'i)_Wet_Textured_Soft'], (8, 6), 1264 / 8),
    ('Watercolors', 'j-watercolors.png', 1, ['j)_Watercolor_Fringe', 'j)_Watercolor_Texture', 'j)_Waterpaint_Hard_Edges', 'j)_Waterpaint_Soft_Edges'], (10, 10), 170),
]
MIME = {'.png': 'image/png', '.svg': 'image/svg+xml'}
def data_url(f):  # GIMP brushes are raw pixels: gzipped (the page unzips them)
    raw = f.read_bytes() if f.suffix in MIME else gzip.compress(f.read_bytes(), 9)
    return 'data:%s;base64,%s' % (MIME.get(f.suffix, 'application/gzip'), base64.b64encode(raw).decode())
fams = [{'name': name, 'zoom': zoom, 'width': struct.unpack('>I', (here / 'references' / 'krita' / pic).read_bytes()[16:20])[0], 'picture': 'data:image/png;base64,' + base64.b64encode((here / 'references' / 'krita' / pic).read_bytes()).decode(),
         'presets': [{'id': fn[3:], 'file': fn, 'text': (here / 'krita' / 'presets' / (fn + '.txt')).read_text(encoding='utf-8'), 'row': [x0 * zoom, (y0 + k * step) * zoom]} for k, fn in enumerate(files)]}
        for name, pic, zoom, files, (x0, y0), step in FAMILIES]
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
