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
# pediment (four stones): each half is an inner part (4 m) and an outer tip (3 m); the inner parts meet in the middle with a
# flat top 0.8 wide where the middle acroterion stands; the ends stop 1 m short of the frieze ends, where the corner
# acroteria stand level. Absolute shapes (right half; left is the mirror):
GH, GE = 1.33, 4.0  # pediment: two stones, each half 4 m long and 1.33 m high with a flat top 0.4 m wide at the middle
GABLE_ABS = {"gableR": [(0, 0), (GE, 0), (0.4, GH), (0, GH)]}
GABLE_ABS["gableL"] = [(-x, y) for x, y in reversed(GABLE_ABS["gableR"])]
TRI = 1.0  # small triangle (half a square): the ziggurat stairway and the mausoleum roof
# big triangle: fills the corner beside an arch. With its right angle at the corner (top of the arch, side of the wall
# beside it) its long side rests on the arch's outer corner at 40 degrees, so it sits exactly flush with the arch top
ARCH_X = round(3 / math.cos(math.radians(10)), 4)   # half-width of an arch at its feet: 3.0462
TRIB = round(ARCH_X + 3 - ARCH_X * (math.cos(math.radians(40)) + math.sin(math.radians(40))), 4)  # 1.7545
LEVEL_PIECES = {**{k: centred(v) for k, v in GABLE_ABS.items()}, "tri": centred([(0, 0), (TRI, 0), (0, TRI)]),
                "trib": centred([(0, 0), (TRIB, 0), (0, TRIB)])}
WT = math.tan(math.radians(10))  # 9 wedges, 20 degrees each; faces 2.0 and 3.0 m from the centre, so the arch top is exactly 3 m above its springing
WEDGE = [(-2 * WT, -0.5), (2 * WT, -0.5), (3 * WT, 0.5), (-3 * WT, 0.5)]
R_C = 2.0  # arch form: the wedges' inner faces lie 2.0 m from the centre
SHAPES = {
    "block": box(-1, -0.5, 1, 0.5), "square": box(-0.5, -0.5, 0.5, 0.5), "column": box(-0.3, -1.2, 0.3, 1.2),
    "beam": box(-1.6, -0.25, 1.6, 0.25), "capital": box(-0.8, -0.2, 0.8, 0.2),
    "wedge": Polygon(WEDGE),
    **{k: Polygon(v) for k, v in LEVEL_PIECES.items()},
}
# a triangle with its right angle at corner (cx, cy), the short sides along the wall and the top,
# the long side facing down towards (sx, sy) = -1/+1: the arch below and to that side
def tri_at(cx, cy, sx, mat="stone", kind="tri"):
    # rest shape has the right angle at the bottom left; turned -90 deg it sits at the top left, 180 deg at the top right
    a = -UP if sx > 0 else math.pi
    sh = affinity.rotate(SHAPES[kind], a, origin=(0, 0), use_radians=True)
    corner = (sh.bounds[0], sh.bounds[3]) if sx > 0 else (sh.bounds[2], sh.bounds[3])
    return [kind, mat, round(cx - corner[0], 4), round(cy - corner[1], 4), round(a, 4)]
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
    out.append(["centering", "wood", cx, round(sy + 4 * R_C / (3 * math.pi), 4), 0])
    for i in [0, 8, 1, 7, 2, 6, 3, 5, 4]:
        t = math.radians(10 + 20 * i)
        out.append(["wedge", "stone", round(cx + 2.5 * math.cos(t), 4), round(sy + 2.5 * math.sin(t), 4), round(t - math.pi / 2, 4)])
    return out
def arch_hole(cx, sy, base=None):  # the opening under an arch: the form's half circle, down to base
    base = sy if base is None else base
    return Polygon([(cx - 2, base)] + [(cx + 2 * math.cos(math.pi * (1 - i / 32)), sy + 2 * math.sin(math.pi * (1 - i / 32))) for i in range(33)] + [(cx + 2, base)])

    return Polygon(pts)
def acroterion(x, y, w=0.5, h=0.8):  # a palmette-topped ornament standing on a flat place
    return Polygon([(x - w / 2, y), (x + w / 2, y), (x + w * 0.6, y + h * 0.6), (x, y + h), (x - w * 0.6, y + h * 0.6)])
def rect(x0, y0, x1, y1): return box(x0, y0, x1, y1)

COLS6 = [-4.0, -2.4, -0.8, 0.8, 2.4, 4.0]  # capitals 1.6 wide touch each other: -4.8..4.8, the beams' width
def colonnade(y):  # six columns with capitals, three beams
    return [["column", "stone", x, y + 1.2, 0] for x in COLS6] + [["capital", "stone", x, y + 2.6, 0] for x in COLS6] + \
        [["beam", "stone", x, y + 3.05, 0] for x in (-3.2, 0, 3.2)]

L = []
def level(key, nameEl, date, demand, note, sol, load, holes=(), woodRole=None, wrong=()):
    L.append(dict(key=key, nameEl=nameEl, date=date, newDemand=demand, note=note, sol=sol, load=list(load), holes=list(holes), woodRole=woodRole, wrong=list(wrong)))
PULL = ["pull", "", 0, 0, 0]  # quick build: take every temporary wooden support out now (put back in the pile)

# --- wrong choices: each is the suggested build with one change; tools/harness.py spec checks that each one falls
def recolour(sol, pred, m):
    return [[e[0], m, e[2], e[3], e[4]] if e[0] != "pull" and pred(e) else e for e in sol]
def moved(sol, pred, dx=0, dy=0):
    return [[e[0], e[1], e[2] + dx, e[3] + dy, e[4]] if e[0] != "pull" and pred(e) else e for e in sol]
def without(sol, pred):
    return [e for e in sol if e[0] == "pull" or not pred(e)]
def W(name, kind, sol): return dict(name=name, kind=kind, sol=sol)
near = lambda a, b: abs(a - b) < 1e-3

# 1 Mastaba
s = row("mudbrick", -4, 4, 0.5) + staggered("mudbrick", -4, 4, 1.5) + row("mudbrick", -4, 4, 2.5)  # joints staggered
level("mastaba", "Μαστάμπα", "c. 3000 BC", "stack a wide, solid mass", "", s, [rect(-1.6, 3, 1.6, 3.5)],
      wrong=[W("wooden blocks in the top row", "material", recolour(s, lambda e: near(e[3], 2.5), "wood")),
             W("the middle of the top row left open under the roof", "build", without(s, lambda e: abs(e[2]) < 1.5 and near(e[3], 2.5)))])
# 2 Djoser: five steps built, the sixth step is the load
s = [p for r in range(5) for p in row("stone" if r <= 2 else "mudbrick", -(6 - r), 6 - r, r + 0.5)]
level("djoser", "Πυραμίδα του Ζοζέρ", "c. 2650 BC", "build tall in steps; the sixth step goes on last", "six steps (Djoser's pyramid has six); the load is the top step",
      s, [rect(-1, 5, 1, 6)],
      wrong=[W("mudbrick at the bottom, stone on top", "material", [[e[0], "mudbrick" if e[3] <= 1.5 else "stone" if e[3] >= 3.5 else e[1], e[2], e[3], e[4]] for e in s]),
             W("a top-step block more than half off the step below", "build", moved(s, lambda e: near(e[2], 1) and near(e[3], 4.5), dx=2.2))])
# 3 Ziggurat of Ur
s = (row("stone", -5, 5, 0.5) + [["beam", "wood", x, 1.25, 0] for x in (-3.2, 0, 3.2)] + [tri_rest(-5, 0, "right", "stone")] +
     row("mudbrick", -4, 4, 2.0) + row("mudbrick", -4, 4, 3.0) + [["beam", "wood", x, 3.75, 0] for x in (-1.6, 1.6)] + row("mudbrick", -2, 2, 4.5))
level("ziggurat", "Ζιγκουράτ της Ουρ", "c. 2100 BC", "three terraces with reed-mat courses, a stairway, the temple on top",
      "Britannica: mudbrick core strengthened with reed matting, three tiers, staircases, temple of Nanna on top (not preserved); wood courses stand for the reed mats; the stairway is one triangle",
      s, [rect(-1.5, 5, 1.5, 6.0)], woodRole="courses",
      wrong=[W("mudbrick in the base, stone in the top terrace", "material", [[e[0], "mudbrick" if near(e[3], 0.5) and e[0] == "block" else "stone" if near(e[3], 4.5) else e[1], e[2], e[3], e[4]] for e in s]),
             W("a top-terrace block more than half off the terrace below", "build", moved(s, lambda e: near(e[2], 1) and near(e[3], 4.5), dx=3.2))])
# 4 Karnak
s = row("stone", -7, 7, 0.5) + mirror([["column", "stone", -5.9, 2.2, 0], ["column", "stone", -4.3, 2.2, 0], ["block", "stone", -1.3, 2.0, UP],
                                        ["capital", "stone", -1.3, 3.2, 0], ["capital", "stone", -5.1, 3.6, 0], ["beam", "stone", -2.7, 3.65, 0],
                                        ["capital", "stone", -1.9, 4.1, 0], ["capital", "stone", -3.5, 4.1, 0], ["column", "stone", -0.8, 4.6, 0]])
level("karnak", "Υπόστυλη αίθουσα του Καρνάκ", "c. 1290-1220 BC", "beams across gaps between columns",
      "cut through the hall on a platform: middle pillars are an upright block and a capital carrying the side beams and the upper columns; side roofs are stone slabs; the central nave is taller (University of Memphis)",
      s, [rect(-1.6, 5.8, 1.6, 6.3)],
      wrong=[W("mudbrick pillars", "material", recolour(s, lambda e: e[0] == "block" and e[4] != 0, "mudbrick")),
             W("wooden upper pillars", "material", recolour(s, lambda e: e[0] == "column" and abs(e[2]) < 1, "wood")),
             W("a middle pillar too far out for the beam", "build", moved(s, lambda e: near(e[2], -1.3) and e[3] < 3.5, dx=1.0))])
# 5 Lion Gate: the lion triangle (headpiece) is lowered onto the lintel between the stepped-in stones
gate = rect(-1, 0, 1, 2)
s = (mirror([["block", "stone", -5, 0.5, 0], ["block", "stone", -3, 0.5, 0], ["square", "stone", -5.5, 1.5, 0], ["block", "stone", -4, 1.5, 0], ["square", "stone", -2.5, 1.5, 0],
             ["block", "stone", -1.5, 1.0, UP]]) +
     [["beam", "stone", x, 2.25, 0] for x in (-3.2, 0, 3.2)] +
     mirror([["block", "stone", -4.0, 3.0, 0], ["square", "stone", -2.0, 3.0, 0]]) + mirror([["beam", "wood", -2.75, 4.1, UP]]))  # flagpoles held between two stones
level("liongate", "Πύλη των Λεόντων", "c. 1250 BC", "jambs, a stone lintel, flagpoles held between stones, and the lion triangle lowered onto the lintel",
      "two monolith jambs and a great lintel (4.5 x 2.0 x 0.8 m, about 20 t); the lion relief, a triangle, stands on the lintel in the relieving triangle (Wikipedia); "
      "the real corbelled courses close over the relief, which a slab lowered from above cannot pass, so the relief stands free on the lintel; the flagpoles are the owner's addition (no source found for them)",
      s, [Polygon([(-1.45, 2.52), (1.45, 2.52), (0, 5.1)])], [gate],
      wrong=[W("mudbrick jambs", "material", recolour(s, lambda e: e[0] == "block" and e[4] != 0, "mudbrick")),
             W("flagpoles standing on top of the stones, not between them", "build", moved(s, lambda e: e[1] == "wood", dx=0, dy=1.0))])
# 6 Ishtar Gate
s = ([p for y in (0.5, 1.5) for p in row("stone", -6, 2, y) + row("stone", 2, 2, y)] +
     [p for y in (2.5, 3.5, 4.5, 5.5) for p in (["block", "mudbrick", -(ARCH_X + 2), y, 0], ["block", "mudbrick", ARCH_X + 2, y, 0])] +
     arch(0, 2, 2) + [p for y in (2.5, 3.5, 4.5) for p in (["square", "stone", -(ARCH_X + 0.5), y, 0], ["square", "stone", ARCH_X + 0.5, y, 0])] +
     [tri_at(-ARCH_X, 5, 1, kind="trib"), tri_at(ARCH_X, 5, -1, kind="trib")])
ish = s
level("ishtar", "Πύλη της Ιστάρ", "c. 575 BC", "a stone arch on a wooden form",
      "nine wedges on a wooden form, the arch top exactly 3 m above its feet; big triangles in the corners rest on the arch, flush with its top; roof of cedar (worldhistory.org)",
      s, [rect(-3.8, 5, 3.8, 5.6)], [arch_hole(0, 2, 0)], "support",
      wrong=[W("mudbrick under the arch's feet", "material", recolour(s, lambda e: e[3] < 2 and e[1] == "stone" and abs(abs(e[2]) - 3) < 0.01, "mudbrick")),
             W("the form pulled out before the keystone", "build", (lambda i: s[:i] + [PULL] + s[i:])(max(k for k, e in enumerate(s) if e[0] == "wedge")))])
# 7 Parthenon: six columns of square drums 2 m apart with capitals, an architrave of blocks, a pediment of two stones;
# the three acroteria are the load
P0, DR = 2, 3  # top of the steps; drums per column
COLS = [-5.0, -3.0, -1.0, 1.0, 3.0, 5.0]
s = (row("stone", -7, 7, 0.5) + staggered("stone", -6, 6, 1.5) +
     [["square", "stone", x, P0 + 0.5 + k, 0] for x in COLS for k in range(DR)] + [["capital", "stone", x, P0 + DR + 0.2, 0] for x in COLS] +
     [["block", "stone", x, P0 + DR + 0.9, 0] for x in (-4, -2, 0, 2, 4)])
fr_top = P0 + DR + 1.4  # top of the architrave: the pediment stands on it
s += [[k, "stone", round(Polygon(GABLE_ABS[k]).centroid.x, 4), round(fr_top + Polygon(GABLE_ABS[k]).centroid.y, 4), 0] for k in ("gableL", "gableR")]
level("parthenon", "Παρθενώνας", "447-432 BC", "columns built drum by drum, architrave, pediment, acroteria",
      "the real front has eight columns (octastyle) built of drums, about 1.25 column widths apart; six here, one width apart; two steps and no frieze; the pediment stops 1 m short of each end so the corner acroteria stand level; the three acroteria are the load",
      s, [acroterion(-4.5, fr_top, 0.45), acroterion(4.5, fr_top, 0.45), acroterion(0, fr_top + GH, 0.8, 1.0)],
      wrong=[W("mudbrick in the top step", "material", recolour(s, lambda e: near(e[3], P0 - 0.5), "mudbrick")),
             W("drums stacked off line", "build", moved(s, lambda e: e[0] == "square" and near(e[3], P0 + 1.5) and near(e[2], 3.0), dx=0.6)),
             W("an end column too far out for the architrave", "build", moved(s, lambda e: e[0] in ("square", "capital") and near(e[2], 5.0) and e[3] > P0, dx=1.0))])
# 8 Mausoleum: solid core, columns, the walkway ceiling beams reach out from the core further than they hold alone:
# wooden posts hold them while the roof steps go on, then come out
s = (row("stone", -6, 6, 0.5) +
     [["block", "stone", 0, 2.5, 0], ["block", "stone", 0, 3.5, 0], ["capital", "stone", 0, 4.2, 0]] +
     [p for x in (-5.0, 5.0) for p in (["square", "stone", x, 2.5, 0], ["square", "stone", x, 3.5, 0], ["capital", "stone", x, 4.2, 0])] +
     [["column", "wood", x, 3.2, 0] for x in (-2.6, 2.6)] +   # temporary posts
     [["beam", "stone", x, 4.65, 0] for x in (-5.4, -1.6, 1.6, 5.4)] +
     [p for k in range(5) for p in row("stone", -(6 - k), 6 - k, 5.4 + k)] +
     [t for k in range(1, 5) for t in (tri_rest(6 - k, 4.9 + k, "left", "stone"), tri_rest(-(6 - k), 4.9 + k, "right", "stone"))])  # roof sloped by triangles
s = [e if e[3] < 1 else [e[0], e[1], e[2], round(e[3] - 1, 4), e[4]] for e in s]  # one podium course
maus = s
level("mausoleum", "Μαυσωλείο της Αλικαρνασσού", "c. 350 BC", "beams reaching out from the core, held on wooden posts until the roof weighs them down; a sloped roof",
      "Pliny: podium, 36 columns, a pyramid of 24 steps, a four-horse chariot on top (corroborated by excavation, worldhistory.org); a solid core behind the columns carried the roof (Wikipedia); ceiling beams of the walkway were found (AJA). Cut through: core in the middle, a column each side; the wooden posts are the game's way of building it",
      s, [Polygon([(-0.9, 8.9), (0.9, 8.9), (1.0, 9.4), (0.5, 10.0), (-0.6, 10.0), (-1.0, 9.4)]), acroterion(-6.5, 3.9, 0.45), acroterion(6.5, 3.9, 0.45)], [], "support",
      wrong=[W("mudbrick in the core", "material", recolour(s, lambda e: e[0] == "block" and near(e[2], 0) and 1 < e[3] < 3, "mudbrick")),
             W("no wooden posts", "build", without(s, lambda e: e[1] == "wood")),
             W("posts pulled out before the roof steps are on", "build", (lambda i: s[:i] + [PULL] + s[i:])(next(k for k, e in enumerate(s) if e[3] > 4)))])
# 9 Lighthouse: tall hollow lowest tier, two thin walls round a shaft tied by wooden beams, a stone cap, a narrower tier, a round top, statue and Tritons
def pharos(tied=True, cap="stone"):
    out = []
    for k in range(10):  # lowest tier: walls of blocks round the shaft; every other course two wooden beams tie them
        y = k + 0.5
        if k % 2 == 1 and k < 9:
            out += ([["beam", "wood", 0, k + 0.25, 0], ["beam", "wood", 0, k + 0.75, 0]] if tied else [["square", "stone", -1.1, y, 0], ["square", "stone", 1.1, y, 0]]) + \
                   [["square", "stone", -2.1, y, 0], ["square", "stone", 2.1, y, 0]]
        else:
            out += [["block", "stone", -1.6, y, 0], ["block", "stone", 1.6, y, 0]]
    y = 10.0  # second tier: hollow too, walls one square thick, tied by one wooden beam between courses
    for part in ("w", "t", "w", "t", "w"):
        if part == "t": out.append(["beam", "wood", 0, y + 0.25, 0]); y += 0.5
        else: out += [["square", "stone", -1.1, y + 0.5, 0], ["square", "stone", 1.1, y + 0.5, 0]]; y += 1
    out += [["block", cap, 0, y + 0.5, 0], ["square", "stone", 0, y + 1.5, 0]]  # the round top: a stone over the shaft, a drum
    return out
s = pha = pharos()
level("pharos", "Φάρος της Αλεξάνδρειας", "c. 280 BC", "a tall hollow tower: two walls tied by wooden beams, a narrower hollow tier, a round top",
      "square, octagonal and round tiers (Wikipedia); a spiral ramp inside the lowest tier and a shaft in the upper ones (Balawi via Wikipedia; mfn.li); statue on top and Tritons on the corners (Roman coins). Walls laced with timber are an old Greek technique; for the Pharos the sources name lead between the base blocks",
      s, [rect(-0.4, 16.1, 0.4, 17.4), acroterion(-2.1, 10, 0.4, 0.8), acroterion(2.1, 10, 0.4, 0.8)],
      [rect(-0.6, k, 0.6, k + 1) for k in (0, 2, 4, 6)] + [rect(-0.6, 8, 0.6, 10)] + [rect(-0.6, 10, 0.6, 11), rect(-0.6, 11.5, 0.6, 12.5), rect(-0.6, 13, 0.6, 14)],
      wrong=[W("mudbrick at the base", "material", recolour(s, lambda e: e[0] == "block" and e[3] < 2, "mudbrick")),
             W("no wooden ties (the walls stacked straight up)", "build", pharos(tied=False)),
             W("the upper tier set off centre", "build", moved(s, lambda e: e[3] > 10, dx=1.0))])
# 10 Valens: two forms for four arches, moved from the lower to the upper arches
VX = ARCH_X  # arch centres; neighbouring arches touch at their feet
def tier(sy, wide=False):  # side walls: blocks (2 m) in the lower tier, which takes the arches' push, squares above
    if wide: walls = [p for k in range(3) for p in (["block", "stone", -(2 * VX + 1), sy + 0.5 + k, 0], ["block", "stone", 2 * VX + 1, sy + 0.5 + k, 0])]
    else: walls = [p for k in range(3) for p in (["square", "stone", -(2 * VX + 0.5), sy + 0.5 + k, 0], ["square", "stone", 2 * VX + 0.5, sy + 0.5 + k, 0])]
    return walls + \
        [tri_at(-2 * VX, sy + 3, 1, kind="trib"), tri_at(0, sy + 3, -1, kind="trib"), tri_at(0, sy + 3, 1, kind="trib"), tri_at(2 * VX, sy + 3, -1, kind="trib")]
UPPER = 3.0
lower = arch(-VX, 0, 0) + arch(VX, 0, 0) + tier(0, wide=True)  # the lower arches stand on the ground, their forms too (pile size)
s = lower + [PULL] + arch(-VX, UPPER, 0) + arch(VX, UPPER, 0) + tier(UPPER)
level("valens", "Υδραγωγείο του Ουάλη", "AD 368", "two tiers of arches, two forms moved from arch to arch",
      "real upper arches are smaller; same size here because there is one wedge size; the upper arches stand on the lower tier, whose top is flat",
      s, [rect(-(2 * VX + 1), UPPER + 3, 2 * VX + 1, UPPER + 3.6)], [arch_hole(-VX, 0), arch_hole(VX, 0), arch_hole(-VX, UPPER), arch_hole(VX, UPPER)], "support",
      wrong=[W("mudbrick at the foot of the side walls", "material", recolour(s, lambda e: e[0] == "block" and near(e[3], 0.5), "mudbrick")),
             W("a form pulled out before the last wedge", "build", (lambda i: s[:i] + [PULL] + s[i:])(max(k for k, e in enumerate(lower) if e[0] == "wedge")))])

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
    u = unary_union([placed(d, x, y, a) for d, m, x, y, a in l["sol"] if d != "pull" and m == "wood"])
    return [flat(r) for r in rings(u)[0]]
out = []
for l in L:
    sup = l["woodRole"] == "support"
    shapes = [placed(d, x, y, a) for d, m, x, y, a in l["sol"] if d != "pull" and not (sup and m == "wood")]
    # closed over gaps narrower than 0.7 m (pockets and slivers no piece can fill are part of the
    # outline, not lace-like openings); real openings come from the level's holes
    u = unary_union([s.buffer(0.003, join_style=2, mitre_limit=10) for s in shapes]).buffer(-0.003, join_style=2, mitre_limit=10)  # exactly the build
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
r4 = lambda e: [e[0], e[1], round(e[2], 4), round(e[3], 4), round(e[4], 4)]
from collections import Counter
def stock(sol):  # pile items: the build's pieces; wooden pieces after a 'pull' step are the same supports used again
    out, pulled = [], False
    for e in sol:
        if e[0] == "pull": pulled = True; continue
        if pulled and e[1] == "wood": continue
        out.append((e[0], e[1]))
    return Counter(out)
for l, o in zip(L, out):
    base, ex = stock(l["sol"]), Counter()
    for w in l["wrong"]:
        if w["kind"] == "material": ex |= stock(w["sol"]) - base
    o["extra"] = [[d, m, n] for (d, m), n in sorted(ex.items())]
js = js[:js.index("const LEVELS = ")] + "const LEVELS = " + json.dumps(out, ensure_ascii=False) + ";\n"
(HERE / "src" / "levels.js").write_text(js, encoding="utf-8")
tests = {l["key"]: [dict(name=w["name"], kind=w["kind"], sol=[r4(e) for e in w["sol"]]) for w in l["wrong"]] for l in L}
(HERE / "tools" / "level-tests.json").write_text(json.dumps(tests, ensure_ascii=False), encoding="utf-8")
for o in out: print(o["key"], len(o["solution"]), "pieces,", len(o["solid"]), "rings,", len(o["holes"]), "holes")
