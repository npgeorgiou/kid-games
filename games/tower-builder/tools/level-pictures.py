#!/usr/bin/env python3
"""One picture of all ten levels, top to bottom: left the outline the player gets (orange = the headpiece lowered
in the test), right the suggested build. Reads src/levels.js. Needs Pillow, numpy and OpenCV (tools/geom.py).
Usage: python3 tools/level-pictures.py  ->  levels.png"""
import json, math, pathlib
from PIL import Image, ImageDraw, ImageFont
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from geom import Polygon, affinity

HERE = pathlib.Path(__file__).resolve().parent.parent
js = (HERE / "src" / "levels.js").read_text(encoding="utf-8")
PIECES = json.loads(js[js.index("const LEVEL_PIECES = ") + 21:js.index(";\n", js.index("const LEVEL_PIECES = "))])
LEVELS = json.loads(js[js.index("const LEVELS = ") + 15:js.rindex(";")])
R_C = 1.95
SHAPES = {
    "block": [(-1, -.5), (1, -.5), (1, .5), (-1, .5)], "square": [(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)],
    "column": [(-.3, -1.2), (.3, -1.2), (.3, 1.2), (-.3, 1.2)], "beam": [(-1.6, -.25), (1.6, -.25), (1.6, .25), (-1.6, .25)],
    "capital": [(-.8, -.2), (.8, -.2), (.8, .2), (-.8, .2)], "abacus": [(-.4, -.2), (.4, -.2), (.4, .2), (-.4, .2)], "wedge": [(-.35, -.5), (.35, -.5), (.525, .5), (-.525, .5)],
    "centering": [(R_C * math.cos(math.pi * i / 10), R_C * math.sin(math.pi * i / 10) - 4 * R_C / (3 * math.pi)) for i in range(11)],
    **{k: [tuple(v) for v in vs] for k, vs in PIECES.items()},
}
FILL = {"stone": (170, 170, 168), "mudbrick": (196, 150, 98), "wood": (150, 100, 55)}
PX, PAD, LABEL = 26, 30, 64
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
except OSError:
    font = small = ImageFont.load_default()

def ring(flat): return [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
def bounds(L):
    xs, ys = [], []
    for r in L["solid"] + L["load"]:
        for x, y in ring(r): xs.append(x); ys.append(y)
    return min(xs) - 0.5, max(xs) + 0.5, max(ys) + 0.4
W_M = max(max(abs(bounds(L)[0]), abs(bounds(L)[1])) for L in LEVELS) * 2
colW = int(W_M * PX) + 2 * PAD
rows = [int(bounds(L)[2] * PX) + PAD + LABEL for L in LEVELS]
img = Image.new("RGB", (2 * colW, sum(rows) + PAD), (250, 249, 245))
d = ImageDraw.Draw(img, "RGBA")
y0 = 0
for n, (L, h) in enumerate(zip(LEVELS, rows)):
    top = bounds(L)[2]
    base = y0 + LABEL + int(top * PX)
    def P(x, y, ox): return (ox + colW / 2 + x * PX, base - y * PX)
    d.line([(0, y0), (2 * colW, y0)], fill=(200, 196, 188), width=2)
    sup = L["woodRole"] == "support"
    d.text((PAD, y0 + 10), "%d  %s  (%s)" % (n + 1, L["key"].capitalize(), L["date"]), font=font, fill=(40, 40, 40))
    d.text((PAD, y0 + 38), L["newDemand"], font=small, fill=(90, 90, 90))
    for ox, title in ((0, "outline"), (colW, "suggested build")):
        d.text((ox + colW - PAD - 150, y0 + 14), title, font=small, fill=(120, 120, 120))
        d.line([P(-W_M / 2, 0, ox), P(W_M / 2, 0, ox)], fill=(120, 110, 95), width=3)
    # left: the outline (solid minus openings), wood zones, the headpiece
    for r in L["solid"]: d.polygon([P(x, y, 0) for x, y in ring(r)], fill=(214, 224, 236), outline=(70, 100, 140))
    for r in L["holes"]: d.polygon([P(x, y, 0) for x, y in ring(r)], fill=(250, 249, 245), outline=(70, 100, 140))
    for r in L.get("guides", []): d.polygon([P(x, y, 0) for x, y in ring(r)], outline=(70, 100, 140))
    if L["woodRole"] == "courses":
        for r in L["wood"]: d.polygon([P(x, y, 0) for x, y in ring(r)], fill=(150, 100, 55, 90))
    # right: the build; temporary wood see-through, forms used twice (after a 'pull') drawn at both places
    pulled = False
    for e in L["solution"]:
        k, m, x, y, a = e
        if k == "pull": pulled = True; continue
        poly = affinity.translate(affinity.rotate(Polygon(SHAPES[k]), a, origin=(0, 0), use_radians=True), x, y)
        temp = sup and m == "wood"
        col = FILL[m] + ((110,) if temp else (255,))
        d.polygon([P(px, py, colW) for px, py in poly.exterior.coords], fill=col, outline=(60, 60, 60, 160 if temp else 255))
    for ox in (0, colW):
        for r in L["load"]: d.polygon([P(x, y, ox) for x, y in ring(r)], fill=(240, 140, 40), outline=(160, 80, 10))
    y0 += h
d.line([(colW, 0), (colW, img.height)], fill=(200, 196, 188), width=2)
out = HERE / "levels.png"
img.save(out)
print(out, img.size)
