"""Writes krita/picture-palettes.txt: for each preset, the colours of its strip in Krita's picture (references/krita/), the paper's colour first.
The brushes page paints with these, so a stroke can be set beside its picture in the picture's own colours. Run after a picture or a family changes."""
import ast, pathlib
from PIL import Image
here = pathlib.Path(__file__).resolve().parent.parent
FAMILIES = eval(compile(ast.Expression(next(n.value for n in ast.parse((here / "build.py").read_text()).body if isinstance(n, ast.Assign) and n.targets[0].id == "FAMILIES")), "build.py", "eval"))  # the list as build.py writes it (it has sums in it)

def palette(pixels, most=10, apart=48):  # the commonest colours, each at least `apart` from the ones kept (a strip's paper first: it covers most)
    count = {}
    for r, g, b in pixels: k = (r >> 3, g >> 3, b >> 3); count[k] = count.get(k, 0) + 1
    kept = []
    for (r, g, b), n in sorted(count.items(), key=lambda kv: -kv[1]):
        c = (r * 8 + 4, g * 8 + 4, b * 8 + 4)
        if n * 2000 < len(pixels): break  # under half a per mille of the strip: stray edge pixels
        if all(sum((a - b) ** 2 for a, b in zip(c, k)) ** 0.5 >= apart for k in kept): kept.append(c)
        if len(kept) == most: break
    return kept

lines = ['# Each preset\'s colours in its strip of Krita\'s picture, the paper first (made by tools/picture_palettes.py).']
for name, pic, zoom, files, (x0, y0), step in FAMILIES:
    im = Image.open(here / 'references' / 'krita' / pic).convert('RGB')
    for k, fn in enumerate(files):
        top = round(y0 + k * step); strip = im.crop((round(x0 + step), top, im.width, min(im.height, round(top + step))))  # right of the icon square that starts each strip
        lines.append('%s = %s' % (fn, ' '.join('#%02x%02x%02x' % c for c in palette(list(strip.getdata())))))
(here / 'krita' / 'picture-palettes.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(len(lines) - 1, 'presets')
