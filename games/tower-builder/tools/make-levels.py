#!/usr/bin/env python3
"""Writes src/levels.js: the ten levels with their suggested builds; each outline is the union of the
build's pieces (wooden supports excluded), so it always fits whole pieces. Needs shapely.
Usage: python3 tools/make-levels.py"""
import json, math, pathlib
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import affinity

HERE = pathlib.Path(__file__).resolve().parent.parent
UP = math.pi / 2

# --- piece shapes (must match PIECE_DEFS in src/index.html; polygons not listed there come from LEVEL_PIECES)
def gable_verts(side):
    b, h, flat = 4.2, 1.1, 0.25  # half the gable: right angle at the inner bottom, a short flat tip for the top slab
    pts = [(-b, 0), (0, 0), (0, h), (-flat, h * (1 - flat / b))]
    if side > 0: pts = [(-x, y) for x, y in reversed(pts)]
    c = Polygon(pts).centroid
    return [[round(x - c.x, 4), round(y - c.y, 4)] for x, y in pts]
LEVEL_PIECES = {"gableL": gable_verts(-1), "gableR": gable_verts(1)}
R_C = 1.95
SHAPES = {
    "block": box(-1, -0.5, 1, 0.5), "square": box(-0.5, -0.5, 0.5, 0.5), "column": box(-0.3, -1.2, 0.3, 1.2),
    "beam": box(-1.6, -0.25, 1.6, 0.25), "capital": box(-0.8, -0.2, 0.8, 0.2),
    "wedge": Polygon([(-0.35, -0.5), (0.35, -0.5), (0.525, 0.5), (-0.525, 0.5)]),
    "centering": Polygon([(R_C * math.cos(math.pi * i / 10), R_C * math.sin(math.pi * i / 10) - 4 * R_C / (3 * math.pi)) for i in range(11)]),
    **{k: Polygon(v) for k, v in LEVEL_PIECES.items()},
}
def placed(d, x, y, a):
    return affinity.translate(affinity.rotate(SHAPES[d], a, origin=(0, 0), use_radians=True), x, y)

# --- helpers for writing builds
def row(mat, x0, n, y, kind="block"):
    w = 1 if kind == "square" else 2
    return [[kind, mat, x0 + w / 2 + w * k, y, 0] for k in range(n)]
def staggered(mat, x0, n, y):  # square, n-1 blocks, square: joints offset from the row below
    return row(mat, x0, 1, y, "square") + row(mat, x0 + 1, n - 1, y) + row(mat, x0 + 1 + 2 * (n - 1), 1, y, "square")
def mirror(lst):
    return lst + [[d, m, -x, y, -a] for d, m, x, y, a in lst]
def arch(cx, sy, support_rows, single=False):
    out = []
    if single: out.append(["block", "wood", cx, sy - 0.5, 0])
    else:
        for r in range(support_rows):
            out += [["block", "wood", cx - 1, sy - support_rows + r + 0.5, 0], ["block", "wood", cx + 1, sy - support_rows + r + 0.5, 0]]
    out.append(["centering", "wood", cx, sy + 4 * 1.95 / (3 * math.pi) + 0.01, 0])
    for i in [0, 8, 1, 7, 2, 6, 3, 5, 4]:
        t = math.radians(10 + 20 * i)
        out.append(["wedge", "stone", cx + 2.51 * math.cos(t), sy + 2.51 * math.sin(t), t - math.pi / 2])
    return out
def arch_hole(cx, sy, base=0, r=2.0):
    pts = [(cx - r, base)] + [(cx + r * math.cos(math.pi - math.pi * i / 10), sy + r * math.sin(math.pi - math.pi * i / 10)) for i in range(11)] + [(cx + r, base)]
    return Polygon(pts)
def acroterion(x, y, w=0.5, h=0.8):  # a palmette-topped ornament standing on a flat place
    return Polygon([(x - w / 2, y), (x + w / 2, y), (x + w * 0.6, y + h * 0.6), (x, y + h), (x - w * 0.6, y + h * 0.6)])
def rect(x0, y0, x1, y1): return box(x0, y0, x1, y1)

COLS6 = [-4.0, -2.4, -0.8, 0.8, 2.4, 4.0]  # capitals 1.6 wide touch each other: -4.8..4.8, the beams' width
def colonnade(y):  # six columns with capitals, three beams
    return [["column", "stone", x, y + 1.2, 0] for x in COLS6] + [["capital", "stone", x, y + 2.6, 0] for x in COLS6] + \
        [["beam", "stone", x, y + 3.05, 0] for x in (-3.2, 0, 3.2)]

L = []
def level(key, nameEl, date, demand, note, sol, load, holes=(), woodRole=None):
    L.append(dict(key=key, nameEl=nameEl, date=date, newDemand=demand, note=note, sol=sol, load=list(load), holes=list(holes), woodRole=woodRole))

level("mastaba", "Μαστάμπα", "c. 3000 BC", "stack a wide, solid mass", "",
      [p for y in (0.5, 1.5, 2.5) for p in row("mudbrick", -4, 4, y)], [rect(-1.6, 3, 1.6, 3.5)])
level("djoser", "Πυραμίδα του Ζοζέρ", "c. 2650 BC", "build tall in steps, top block", "",
      [p for r in range(6) for p in row("stone" if r <= 2 else "mudbrick", -(6 - r), 6 - r, r + 0.5)], [rect(-1, 6, 1, 7)])
level("ziggurat", "Ζιγκουράτ της Ουρ", "c. 2100 BC", "wood courses inside the stone",
      "wood courses stand in for the reed-mat layers of Mesopotamian ziggurats; whether Ur had them: unverified",
      row("stone", -5, 5, 0.5) + row("stone", -5, 5, 1.5) + [["beam", "wood", x, 2.25, 0] for x in (-3.2, 0, 3.2)] +
      row("mudbrick", -4, 4, 3) + [["beam", "wood", x, 3.75, 0] for x in (-1.6, 1.6)] + row("mudbrick", -3, 3, 4.5) + row("mudbrick", -1, 1, 5.5),
      [rect(-1, 6, 1, 7)], woodRole="courses")
level("karnak", "Υπόστυλη αίθουσα του Καρνάκ", "c. 1290-1220 BC", "beams across gaps between columns",
      "cut through the hall on a platform: middle pillars are an upright block and a capital carrying the side beams and the upper columns; side roofs are stone slabs",
      row("stone", -7, 7, 0.5) + mirror([["column", "stone", -5.9, 2.2, 0], ["column", "stone", -4.3, 2.2, 0], ["block", "stone", -1.3, 2.0, UP],
                                          ["capital", "stone", -1.3, 3.2, 0], ["capital", "stone", -5.1, 3.6, 0], ["beam", "stone", -2.7, 3.65, 0],
                                          ["capital", "stone", -1.9, 4.1, 0], ["capital", "stone", -3.5, 4.1, 0], ["column", "stone", -0.8, 4.6, 0]]),
      [rect(-1.6, 5.8, 1.6, 6.3)])
gate = rect(-1, 0, 1, 3)
level("liongate", "Πύλη των Λεόντων", "c. 1250 BC", "overhanging stones held by weight",
      "the lintel and the walls beside the relieving triangle simplified to whole blocks and beams; the lion slab is the load",
      [p for y in (0.5, 1.5, 2.5) for p in row("stone", -5, 2, y) + row("stone", 1, 2, y)] + [["beam", "stone", x, 3.25, 0] for x in (-3.2, 0, 3.2)] +
      [p for y in (4, 5, 6) for p in row("stone", -5, 2, y) + row("stone", 1, 2, y)],
      [Polygon([(-0.9, 3.5), (0.9, 3.5), (0, 4.5)])], [gate])
level("ishtar", "Πύλη της Ιστάρ", "c. 575 BC", "wedge-stone arch on wooden supports",
      "spandrels beside the arch are square blocks; the curved gaps above the arch cannot be filled with straight pieces",
      [p for y in (0.5, 1.5) for p in row("stone", -6, 2, y) + row("stone", 2, 2, y)] +
      [p for y in (2.5, 3.5, 4.5, 5.5, 6.5) for p in (["block", "mudbrick", -5, y, 0], ["block", "mudbrick", 5, y, 0])] +
      arch(0, 2, 2) + [p for y in (2.5, 3.5, 4.5) for p in (["square", "stone", -3.5, y, 0], ["square", "stone", 3.5, y, 0])],
      [rect(-3.8, 5, 3.8, 5.6)], [arch_hole(0, 2)], "support")
P0 = 3
level("parthenon", "Παρθενώνας", "447-432 BC", "columns with capitals, a pediment, acroteria",
      "real front has 8 columns; 6 here to fit; three steps of whole blocks; architrave, frieze and pediment simplified",
      row("stone", -7, 7, 0.5) + row("stone", -6, 6, 1.5) + row("stone", -5, 5, 2.5) + colonnade(P0) +
      [["capital", "stone", x, P0 + 3.5, 0] for x in COLS6] +
      [["gableL", "stone", -4.2 + 0, 0, 0], ["gableR", "stone", 0, 0, 0], ["capital", "stone", 0, 0, 0]],  # placed below
      [], [])
level("mausoleum", "Μαυσωλείο της Αλικαρνασσού", "c. 350 BC", "heavy stepped roof carried on columns",
      "podium, colonnade, stepped pyramid roof, chariot on top, corner ornaments (proportions from reconstructions, which differ)",
      row("stone", -6, 6, 0.5) + staggered("stone", -6, 6, 1.5) + row("stone", -6, 6, 2.5) + colonnade(3) +
      [p for k, n in enumerate((4, 3, 2, 1)) for p in row("stone", -n, n, 6.8 + k)],
      [acroterion(-4.4, 6.3, 0.45), acroterion(4.4, 6.3, 0.45), Polygon([(-0.9, 10.3), (0.9, 10.3), (1.0, 10.8), (0.5, 11.4), (-0.6, 11.4), (-1.0, 10.8)])])
level("pharos", "Φάρος της Αλεξάνδρειας", "c. 280 BC", "very tall, three tiers, strong wind",
      "tier proportions from reconstructions, simplified to whole blocks; top tier is three columns",
      [p for k in range(5) for p in (row("stone", -5, 5, k + 0.5) if k % 2 == 0 else staggered("stone", -5, 5, k + 0.5))] +
      [p for k in range(4) for p in (row("stone", -3, 3, k + 5.5) if k % 2 == 0 else staggered("stone", -3, 3, k + 5.5))] +
      [["column", "stone", x, 10.2, 0] for x in (-0.6, 0, 0.6)] + [["capital", "stone", 0, 11.6, 0]],
      [rect(-0.4, 11.8, 0.4, 13.1)])
V = mirror([["block", "stone", -6.5, 2.0, UP], ["capital", "stone", -6.2, 3.2, 0], ["block", "stone", -6, 3.92, 0], ["column", "stone", -6, 4.72, UP]])
level("valens", "Υδραγωγείο του Ουάλη", "AD 368", "two tiers of arches",
      "real upper arches are smaller; same size here because there is one wedge size",
      [["block", "stone", -6, 0.5, 0], ["block", "stone", 0, 0.5, 0], ["block", "stone", 6, 0.5, 0]] + arch(-3, 1, 1) + arch(3, 1, 1) + V +
      [["capital", "stone", 0, 3.26, 0], ["block", "stone", 0, 3.98, 0], ["capital", "stone", 0, 4.7, 0]] +
      arch(-3, 5.02, 1, True) + arch(3, 5.02, 1, True) + mirror([["block", "stone", -6.5, 6.05, UP]]) +
      [["block", "stone", -6.2, 7.6, 0], ["block", "stone", 6.2, 7.6, 0], ["capital", "stone", 0, 7.28, 0], ["column", "stone", 0, 7.8, UP]],
      [rect(-7, 8, 7, 8.6)], [arch_hole(-3, 1), arch_hole(3, 1), arch_hole(-3, 5, 4), arch_hole(3, 5, 4)], "support")

# Parthenon pediment: the two halves stand on the frieze, the slab on their flat tips, acroteria on the frieze ends and the slab
pth = next(l for l in L if l["key"] == "parthenon")
fr_top = P0 + 3.7
gl, gr = Polygon(LEVEL_PIECES["gableL"]), Polygon(LEVEL_PIECES["gableR"])
pth["sol"][-3] = ["gableL", "stone", round(-gl.bounds[2], 4), round(fr_top - gl.bounds[1], 4), 0]
pth["sol"][-2] = ["gableR", "stone", round(-gr.bounds[0], 4), round(fr_top - gr.bounds[1], 4), 0]
tip = fr_top + gl.bounds[3] - gl.bounds[1]
pth["sol"][-1] = ["capital", "stone", 0, round(tip + 0.2, 4), 0]
pth["load"] = [acroterion(-4.5, fr_top, 0.45), acroterion(4.5, fr_top, 0.45), acroterion(0, tip + 0.4, 0.8, 1.0)]

def parts(geom):
    return [g for g in ([geom] if geom.geom_type == "Polygon" else list(geom.geoms)) if g.area >= 0.05]
def rings(geom, known=None):  # outer rings of the pieces, and the empty places they enclose (openings to keep clear)
    ps = parts(geom)
    filled = unary_union([Polygon(p.exterior) for p in ps])
    empty = filled.difference(geom)
    if known is not None: empty = empty.difference(known)
    empty = empty.buffer(-0.06).buffer(0.06)  # drop seams and slivers along curved edges
    ints = []
    for e in parts(empty):
        assert not list(e.interiors), "an enclosed opening with pieces inside it"
        ints.append(e.exterior)
    return [p.exterior for p in ps], ints
def flat(ring):
    cs = list(ring.coords)[:-1]
    return [round(v, 3) for c in cs for v in c]

def wood_rings(l):  # 'courses' levels: the wood zone is where the build's wooden pieces lie
    if l["woodRole"] != "courses": return []
    u = unary_union([placed(d, x, y, a) for d, m, x, y, a in l["sol"] if m == "wood"])
    return [flat(r) for r in rings(u)[0]]
out = []
for l in L:
    sup = l["woodRole"] == "support"
    shapes = [placed(d, x, y, a) for d, m, x, y, a in l["sol"] if not (sup and m == "wood")]
    u = unary_union([s.buffer(0.03, join_style=2) for s in shapes]).buffer(-0.03, join_style=2)
    holes = list(l["holes"])
    if holes: u = u.difference(unary_union(holes))
    u = u.simplify(0.004)
    ext, ints = rings(u, unary_union(holes) if holes else None)
    out.append(dict(key=l["key"], nameEl=l["nameEl"], date=l["date"], newDemand=l["newDemand"],
                    solid=[flat(r) for r in ext], holes=[flat(h.exterior) for h in holes] + [flat(r) for r in ints],
                    load=[flat(p.exterior) for p in l["load"]], wood=[flat(h.exterior) for h in holes] if sup else wood_rings(l),
                    woodRole=l["woodRole"], note=l["note"],
                    solution=[[d, m, round(x, 4), round(y, 4), round(a, 4)] for d, m, x, y, a in l["sol"]]))
js = ("// Level data, chronological = play order. Generated by tools/make-levels.py; do not edit by hand.\n"
      "// Units metres, x centred, y up from the ground. solid/holes/load/wood: flat [x0,y0,x1,y1,...] rings; outline = solid minus holes.\n"
      "// woodRole: 'support' = temporary wooden supports the player takes out once the arch stands; 'courses' = wood that stays inside the stone.\n"
      "// solution: the suggested build, in building order: [shape, material, x, y, angle]. LEVEL_PIECES: polygon pieces used by levels.\n"
      "const LEVEL_PIECES = " + json.dumps(LEVEL_PIECES) + ";\n"
      "const LEVELS = " + json.dumps(out, ensure_ascii=False) + ";\n")
(HERE / "src" / "levels.js").write_text(js, encoding="utf-8")
for o in out: print(o["key"], len(o["solution"]), "pieces,", len(o["solid"]), "rings,", len(o["holes"]), "holes")
