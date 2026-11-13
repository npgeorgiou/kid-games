#!/usr/bin/env python3
"""Writes src/map-routes.js: ports, boat lines that keep to the sea, and walking paths over land between
ports and sites, all in map-picture pixels (src/art/map.jpg). Needs numpy, scipy, scikit-image, Pillow.
Usage: python3 tools/make-map-routes.py [--preview out.png]"""
import json, sys, pathlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.graph import route_through_array
from skimage.measure import approximate_polygon

HERE = pathlib.Path(__file__).resolve().parent.parent
im = Image.open(HERE / "src" / "art" / "map.jpg").convert("RGB")
a = np.asarray(im).astype(int)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
water = ndimage.binary_closing(ndimage.binary_opening((B > R + 40) & (B > G + 5), iterations=2), iterations=2)
lab, n = ndimage.label(water)
size = ndimage.sum(water, lab, range(1, n + 1))
sea = np.isin(lab, 1 + np.where(size > 20000)[0])   # the seas boats sail
wet = np.isin(lab, 1 + np.where(size > 3000)[0])    # also lakes and the Sea of Marmara: nobody walks there
# the Dardanelles, the Sea of Marmara and the Bosporus, drawn too thin on the picture to be found by colour
STRAITS = [(500, 262), (540, 250), (575, 238), (610, 228), (650, 220), (685, 205), (692, 185), (700, 160), (715, 120)]
img = Image.fromarray(np.uint8(sea) * 255); d = ImageDraw.Draw(img)
d.line(STRAITS, fill=255, width=14)
sea = np.asarray(img) > 0

# Port names as in BUILD.md; positions placed by eye on the picture, then moved to the nearest open water.
PORTS = {
    "athens": (352, 466), "corinth": (298, 446), "crete": (450, 612), "rhodes": (636, 560), "miletus": (572, 488),
    "lycia": (700, 562), "cyprus": (1084, 636), "phoenicia": (1134, 770), "alexandria": (700, 884), "cyrene": (180, 822),
    "redsea": (942, 1052), "blacksea": (1040, 160),
}
SOUTH = (1205, 1400)  # where the Red Sea boat sails to, at the bottom edge of the map
SITES = {"mastaba": (720, 1060), "djoser": (880, 1050), "ziggurat": (1960, 900), "karnak": (830, 1300), "liongate": (200, 530),
         "ishtar": (1720, 770), "parthenon": (340, 425), "mausoleum": (665, 495), "pharos": (700, 900), "valens": (735, 225)}
LINES = [["athens", "crete", "alexandria"], ["corinth", "athens", "rhodes"], ["miletus", "rhodes", "lycia", "cyprus"],
         ["cyprus", "phoenicia", "alexandria"], ["cyrene", "crete", "rhodes"], ["alexandria", "cyrene"], ["blacksea", "athens"],
         ["redsea", "south"], ["lycia", "phoenicia"], ["miletus", "corinth"]]

S = 4  # path grid: one cell = 4 map pixels
def coarse(mask): return mask[: mask.shape[0] // S * S, : mask.shape[1] // S * S].reshape(mask.shape[0] // S, S, -1, S).mean(axis=(1, 3)) > 0.5
seaC = coarse(sea)
distC = ndimage.distance_transform_edt(seaC) * S
boat_cost = np.where(distC < 3, 1e6, 1 + 40 * np.clip((30 - distC) / 30, 0, 1) ** 2)
land = ~coarse(wet | sea)  # the straits too: nobody walks or stands on water
land[[0, -1], :] = False; land[:, [0, -1]] = False
coast = ndimage.distance_transform_edt(land) * S
walk_cost = np.where(land, 1 + 3 * (coast < 8), 1e6)

def snap(p, mask, mind):
    dist = ndimage.distance_transform_edt(mask) * S
    ys, xs = np.nonzero(dist >= mind)
    k = np.argmin((xs * S - p[0]) ** 2 + (ys * S - p[1]) ** 2)
    return (int(xs[k] * S + S // 2), int(ys[k] * S + S // 2))
ports = {k: snap(p, seaC, 8) for k, p in PORTS.items()}
ports["south"] = snap(SOUTH, seaC, 6)
def route(p0, p1, cost, tol=3, keep=None):
    idx, c = route_through_array(cost, (p0[1] // S, p0[0] // S), (p1[1] // S, p1[0] // S), fully_connected=True, geometric=True)
    if c >= 1e6: return None
    pts = np.array([[x * S + S // 2, y * S + S // 2] for y, x in idx], float)
    if keep is None: pts = approximate_polygon(pts, tolerance=tol)
    else:  # fewer corners, but every straight piece stays on `keep` (walks never cut across water)
        def ok(a, b):
            n = int(np.hypot(*(b - a)) // 2) + 2
            return all(keep[int(y) // S, int(x) // S] for x, y in np.linspace(a, b, n))
        out, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = i + 1
            while j + 1 < len(pts) and ok(pts[i], pts[j + 1]) and max(abs((pts[j + 1] - pts[i])[0] * (pts[k] - pts[i])[1] - (pts[j + 1] - pts[i])[1] * (pts[k] - pts[i])[0]) / max(1e-9, np.hypot(*(pts[j + 1] - pts[i]))) for k in range(i + 1, j + 1)) <= tol: j += 1
            out.append(pts[j]); i = j
        pts = np.array(out)
    return [[int(round(x)), int(round(y))] for x, y in pts]

lines = []
for stops in LINES:
    legs = [route(ports[stops[i]], ports[stops[i + 1]], boat_cost) for i in range(len(stops) - 1)]
    assert all(legs), stops
    lines.append({"stops": stops, "legs": legs})
# walking: from each port's shore and each site, to every site reachable over land
shore = {k: snap(p, land, 6) for k, p in ports.items() if k != "south"}
walks = {}
places = {**{"port:" + k: v for k, v in shore.items()}, **{"site:" + k: snap(v, land, 4) for k, v in SITES.items()}}
for f, p0 in places.items():
    for t, p1 in places.items():
        if f == t or not t.startswith("site:") or (t + ">" + f) in walks: continue
        r = route(p0, p1, walk_cost, 10, land)
        if r: walks[f + ">" + t] = r
# land for standing on (no sea, straits or lakes), coarse cells, run lengths row by row starting with water
landC = land.ravel()
edges = np.flatnonzero(np.diff(landC.astype(np.int8))) + 1
runs = np.diff(np.concatenate([[0], edges, [landC.size]])).tolist()
if landC[0]: runs = [0] + runs
js = ("// Map routes, generated by tools/make-map-routes.py from src/art/map.jpg; do not edit by hand. Map-picture pixels.\n"
      "// MAP_PORTS: where boats stop. BOAT_LINES: each boat sails its stops back and forth, legs keep to open water.\n"
      "// MAP_WALKS: 'port:x>site:y' or 'site:x>site:y' paths over land (use reversed for the way back).\n"
      "// MAP_LAND: where people and buildings can stand; cells of s x s pixels, run lengths row by row, water first.\n"
      "const MAP_PORTS = " + json.dumps(ports) + ";\nconst BOAT_LINES = " + json.dumps(lines) + ";\nconst MAP_WALKS = " + json.dumps(walks) +
      ";\nconst MAP_LAND = " + json.dumps({"s": S, "w": int(seaC.shape[1]), "runs": ",".join(map(str, runs))}) + ";\n")
(HERE / "src" / "map-routes.js").write_text(js)
# the picture's land, full size, as a cut-out (water see-through), so animated water can show under it
a = np.where(water | sea, 0, 255).astype(np.uint8)
Image.fromarray(np.dstack([np.zeros_like(a)] * 3 + [a]), "RGBA").save(HERE / "src" / "art" / "map-land.png", optimize=True)
print(len(lines), "boat lines,", len(walks), "walks")
if "--preview" in sys.argv:
    pv = im.copy(); d = ImageDraw.Draw(pv)
    for l in lines:
        for leg in l["legs"]: d.line([tuple(p) for p in leg], fill=(255, 0, 0), width=4)
    for k, w in walks.items():
        if k.startswith("port:"): d.line([tuple(p) for p in w], fill=(255, 255, 0), width=2)
    for k, p in ports.items(): d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=(0, 0, 0))
    pv.resize((1088, 704)).save(sys.argv[sys.argv.index("--preview") + 1])
