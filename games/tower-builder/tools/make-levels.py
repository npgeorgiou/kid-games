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
def centred(pts):
    c = Polygon(pts).centroid
    return [[round(x - c.x, 4), round(y - c.y, 4)] for x, y in pts]
def gable_verts(side):
    b, h = 4.5, 1.0  # half the gable: right angle at the inner bottom; a square stone fills the middle between the halves
    pts = [(-b, 0), (0, 0), (0, h)]
    if side > 0: pts = [(-x, y) for x, y in reversed(pts)]
    return centred(pts)
TRI = 1.5  # triangle (new): right-angled, both short sides 1.5; fills the corner between an arch and the wall beside it
LEVEL_PIECES = {"gableL": gable_verts(-1), "gableR": gable_verts(1), "tri": centred([(0, 0), (TRI, 0), (0, TRI)])}
R_C = 1.95
SHAPES = {
    "block": box(-1, -0.5, 1, 0.5), "square": box(-0.5, -0.5, 0.5, 0.5), "column": box(-0.3, -1.2, 0.3, 1.2),
    "beam": box(-1.6, -0.25, 1.6, 0.25), "capital": box(-0.8, -0.2, 0.8, 0.2), "abacus": box(-0.5, -0.15, 0.5, 0.15),
    "wedge": Polygon([(-0.35, -0.5), (0.35, -0.5), (0.525, 0.5), (-0.525, 0.5)]),
    "centering": Polygon([(R_C * math.cos(math.pi * i / 10), R_C * math.sin(math.pi * i / 10) - 4 * R_C / (3 * math.pi)) for i in range(11)]),
    **{k: Polygon(v) for k, v in LEVEL_PIECES.items()},
}
# a triangle with its right angle at corner (cx, cy), the short sides along the wall and the top,
# the long side facing down towards (sx, sy) = -1/+1: the arch below and to that side
def tri_at(cx, cy, sx, mat="stone"):
    # rest shape has the right angle at the bottom left; turned -90 deg it sits at the top left, 180 deg at the top right
    a = -UP if sx > 0 else math.pi
    sh = affinity.rotate(SHAPES["tri"], a, origin=(0, 0), use_radians=True)
    corner = (sh.bounds[0], sh.bounds[3]) if sx > 0 else (sh.bounds[2], sh.bounds[3])
    return ["tri", mat, round(cx - corner[0], 4), round(cy - corner[1], 4), round(a, 4)]
def tri_rest(cx, cy, right_angle_at, mat):  # lying on a short side, right angle at the bottom 'left' or 'right' corner (cx, cy)
    a = 0 if right_angle_at == "left" else UP
    sh = affinity.rotate(SHAPES["tri"], a, origin=(0, 0), use_radians=True)
    bx = sh.bounds[0] if right_angle_at == "left" else sh.bounds[2]
    return ["tri", mat, round(cx - bx, 4), round(cy - sh.bounds[1], 4), round(a, 4)]
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
level("djoser", "Πυραμίδα του Ζοζέρ", "c. 2650 BC", "build tall in steps; the sixth step goes on last", "six steps; the load is the top step",
      [p for r in range(5) for p in row("stone" if r <= 2 else "mudbrick", -(6 - r), 6 - r, r + 0.5)], [rect(-1, 5, 1, 6)])
level("ziggurat", "Ζιγκουράτ της Ουρ", "c. 2100 BC", "three terraces with reed-mat courses, a stairway, the temple on top",
      "Britannica: mudbrick core strengthened with reed matting, three tiers, staircases, temple of Nanna on top (not preserved); wood courses stand for the reed mats; the stairway is one triangle",
      row("stone", -5, 5, 0.5) + [["beam", "wood", x, 1.25, 0] for x in (-3.2, 0, 3.2)] + [tri_rest(-5, 0, "right", "stone")] +
      row("mudbrick", -4, 4, 2.0) + row("mudbrick", -4, 4, 3.0) + [["beam", "wood", x, 3.75, 0] for x in (-1.6, 1.6)] + row("mudbrick", -2, 2, 4.5),
      [rect(-1.5, 5, 1.5, 6.0)], woodRole="courses")
level("karnak", "Υπόστυλη αίθουσα του Καρνάκ", "c. 1290-1220 BC", "beams across gaps between columns",
      "cut through the hall on a platform: middle pillars are an upright block and a capital carrying the side beams and the upper columns; side roofs are stone slabs",
      row("stone", -7, 7, 0.5) + mirror([["column", "stone", -5.9, 2.2, 0], ["column", "stone", -4.3, 2.2, 0], ["block", "stone", -1.3, 2.0, UP],
                                          ["capital", "stone", -1.3, 3.2, 0], ["capital", "stone", -5.1, 3.6, 0], ["beam", "stone", -2.7, 3.65, 0],
                                          ["capital", "stone", -1.9, 4.1, 0], ["capital", "stone", -3.5, 4.1, 0], ["column", "stone", -0.8, 4.6, 0]]),
      [rect(-1.6, 5.8, 1.6, 6.3)])
gate = rect(-1.5, 0, 1.5, 2)
level("liongate", "Πύλη των Λεόντων", "c. 1250 BC", "two upright jambs carry the great lintel",
      "two monolith jambs capped by a huge lintel (4.5 x 2.0 x 0.8 m); the lintel is the load, lowered between the walls onto the jambs; the relieving triangle above it cannot be built before it, so the slot above stays open",
      [p for y in (0.5, 1.5, 2.5, 3.5) for p in row("stone", -6.5, 2, y) + row("stone", 2.5, 2, y)] + [["block", "stone", -2.0, 1.0, UP], ["block", "stone", 2.0, 1.0, UP]],
      [rect(-2.25, 2.02, 2.25, 2.82)], [gate])
level("ishtar", "Πύλη της Ιστάρ", "c. 575 BC", "wedge-stone arch on wooden supports",
      "spandrels beside the arch are square blocks and two triangles; small curved slivers along the arch cannot be filled",
      [p for y in (0.5, 1.5) for p in row("stone", -6, 2, y) + row("stone", 2, 2, y)] +
      [p for y in (2.5, 3.5, 4.5, 5.5, 6.5) for p in (["block", "mudbrick", -5, y, 0], ["block", "mudbrick", 5, y, 0])] +
      arch(0, 2, 2) + [p for y in (2.5, 3.5, 4.5) for p in (["square", "stone", -3.5, y, 0], ["square", "stone", 3.5, y, 0])] +
      [tri_at(-3, 5, 1), tri_at(3, 5, -1)],
      [rect(-3.8, 5, 3.8, 5.6)], [arch_hole(0, 2)], "support")
P0 = 3
COLS8 = [-5.6, -4.0, -2.4, -0.8, 0.8, 2.4, 4.0, 5.6]  # eight columns; the architrave stones span one gap each
level("parthenon", "Παρθενώνας", "447-432 BC", "eight columns, a pediment, acroteria",
      "eight columns on the front as on the real temple; three steps; small square tops (abacus) leave gaps between the columns; architrave one stone per gap; pediment halves either side of a square",
      row("stone", -8, 8, 0.5) + row("stone", -7, 7, 1.5) + staggered("stone", -6, 6, 2.5) +
      [["column", "stone", x, P0 + 1.2, 0] for x in COLS8] + [["abacus", "stone", x, P0 + 2.55, 0] for x in COLS8] +
      [["capital", "stone", x, P0 + 2.9, 0] for x in (-4.8, -3.2, -1.6, 0, 1.6, 3.2, 4.8)] +
      [["capital", "stone", x, P0 + 3.3, 0] for x in (-4.8, -3.2, -1.6, 0, 1.6, 3.2, 4.8)] +
      [["gableL", "stone", 0, 0, 0], ["gableR", "stone", 0, 0, 0], ["square", "stone", 0, 0, 0]],  # placed below
      [], [])
DOOR = rect(-1.4, 0, 1.4, 2)
level("mausoleum", "Μαυσωλείο της Αλικαρνασσού", "c. 350 BC", "a door through the podium; the stepped roof on the colonnade",
      "Pliny: podium, 36 columns (pteron), pyramid of 24 steps, four-horse chariot on top; lions stood at the base of the pyramid (livius.org); a door into the podium (tomb chamber) with a beam lintel",
      mirror([["block", "stone", -5.4, 0.5, 0], ["block", "stone", -3.4, 0.5, 0], ["square", "stone", -1.9, 0.5, 0],
              ["square", "stone", -5.9, 1.5, 0], ["block", "stone", -4.4, 1.5, 0], ["block", "stone", -2.4, 1.5, 0], ["capital", "stone", -5.6, 2.2, 0]]) +
      [["beam", "stone", x, 2.25, 0] for x in (-3.2, 0, 3.2)] + colonnade(2.5) +
      [p for k, n in enumerate((4, 3, 2, 1)) for p in row("stone", -n, n, 6.3 + k)],
      [Polygon([(-4.8, 5.8), (-4.05, 5.8), (-4.05, 6.25), (-4.3, 6.55), (-4.8, 6.35)]), Polygon([(4.8, 5.8), (4.05, 5.8), (4.05, 6.25), (4.3, 6.55), (4.8, 6.35)]),
       Polygon([(-0.9, 9.8), (0.9, 9.8), (1.0, 10.3), (0.5, 10.9), (-0.6, 10.9), (-1.0, 10.3)])], [DOOR])
WIN = lambda y, w=1: rect(-w, y, w, y + 1)
def win_row(n, y):  # a full course with a window two wide in its middle
    half = [["block", "stone", -1 - 2 * k - 1, y, 0] for k in range(n // 2)]
    return mirror(half)
level("pharos", "Φάρος της Αλεξάνδρειας", "c. 280 BC", "three tiers with windows, statues on the corners, a statue on top",
      "three tapering tiers: square, octagonal, round (here a ring of three columns); windows over the inner ramp; Roman coins show Tritons on the corners and a statue (Zeus or Poseidon) on top",
      row("stone", -5, 5, 0.5) + win_row(4, 1.5) + staggered("stone", -5, 5, 2.5) + win_row(4, 3.5) + staggered("stone", -5, 5, 4.5) +
      row("stone", -3, 3, 5.5) + win_row(2, 6.5) + staggered("stone", -3, 3, 7.5) + row("stone", -3, 3, 8.5) +
      [["column", "stone", x, 10.2, 0] for x in (-0.6, 0, 0.6)] + [["capital", "stone", 0, 11.6, 0]],
      [rect(-0.4, 11.8, 0.4, 13.1), acroterion(-4.4, 5, 0.5, 0.9), acroterion(4.4, 5, 0.5, 0.9)], [WIN(1), WIN(3), WIN(6)])
def tier(sy):  # two arches springing at sy, square piers at the ends, a triangle in each corner beside an arch
    return [p for k in range(3) for p in (["square", "stone", -6.5, sy + 0.5 + k, 0], ["square", "stone", 6.5, sy + 0.5 + k, 0])] + \
        [tri_at(-6, sy + 3, 1), tri_at(0, sy + 3, -1), tri_at(0, sy + 3, 1), tri_at(6, sy + 3, -1)]
UPPER = 5.02
level("valens", "Υδραγωγείο του Ουάλη", "AD 368", "two tiers of arches",
      "real upper arches are smaller; same size here because there is one wedge size; a full course between the tiers",
      [["block", "stone", -6, 0.5, 0], ["block", "stone", 0, 0.5, 0], ["block", "stone", 6, 0.5, 0]] + arch(-3, 1, 1) + arch(3, 1, 1) + tier(1) +
      row("stone", -7, 7, UPPER - 0.5) + arch(-3, UPPER, 0) + arch(3, UPPER, 0) + tier(UPPER),
      [rect(-7, UPPER + 3.05, 7, UPPER + 3.65)], [arch_hole(-3, 1), arch_hole(3, 1), arch_hole(-3, UPPER, UPPER), arch_hole(3, UPPER, UPPER)], "support")

# Parthenon pediment: the two halves stand on the frieze either side of a square stone; acroteria on the frieze ends and on the square
pth = next(l for l in L if l["key"] == "parthenon")
fr_top = P0 + 3.5
gl, gr = Polygon(LEVEL_PIECES["gableL"]), Polygon(LEVEL_PIECES["gableR"])
pth["sol"][-3] = ["gableL", "stone", round(-0.5 - gl.bounds[2], 4), round(fr_top - gl.bounds[1], 4), 0]
pth["sol"][-2] = ["gableR", "stone", round(0.5 - gr.bounds[0], 4), round(fr_top - gr.bounds[1], 4), 0]
pth["sol"][-1] = ["square", "stone", 0, fr_top + 0.5, 0]
pth["load"] = [acroterion(-5.3, fr_top, 0.45), acroterion(5.3, fr_top, 0.45), acroterion(0, fr_top + 1.0, 0.8, 1.0)]

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
    # closed over gaps narrower than 0.7 m (pockets and slivers no piece can fill are part of the
    # outline, not lace-like openings); real openings come from the level's holes
    u = unary_union([s.buffer(0.35, join_style=2, mitre_limit=10) for s in shapes]).buffer(-0.35, join_style=2, mitre_limit=10)
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
