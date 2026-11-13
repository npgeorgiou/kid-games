#!/usr/bin/env python3
"""Writes src/levels.js: the ten levels with their suggested builds. Each outline is the shape of the building
(owner, 12 Nov): the outer edge of the build (wooden supports excluded) drawn solid, minus only the openings the level
declares on purpose (doors, arches, spaces between columns, shafts). Needs numpy and OpenCV (tools/geom.py).
Usage: python3 tools/make-levels.py"""
import json, math, pathlib
import sys, cv2
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from geom import Polygon, box, affinity, Frame

HERE = pathlib.Path(__file__).resolve().parent.parent
RES_SEAM = 0.006  # gaps this narrow between touching pieces are seams, closed
NOTCH = 0.3  # a notch in the building's edge narrower than 2 x NOTCH is inside its shape
DIP = 0.12  # so is a dip in the edge shallower than this, however wide (beside the arch tops)
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
    "beam": box(-1.6, -0.25, 1.6, 0.25), "capital": box(-0.8, -0.2, 0.8, 0.2), "abacus": box(-0.4, -0.2, 0.4, 0.2),
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
s = [p for r in range(5) for p in row("stone" if r < 2 else "mudbrick", -(6 - r), 6 - r, r + 0.5)]  # owner (13 Nov): two stone layers, three mudbrick
level("djoser", "Πυραμίδα του Ζοζέρ", "c. 2650 BC", "build tall in steps; the sixth step goes on last", "six steps (Djoser's pyramid has six); the load is the top step",
      s, [rect(-1, 5, 1, 6)],
      wrong=[W("mudbrick at the bottom, stone on top", "material", [[e[0], "mudbrick" if e[3] < 1 else "stone", e[2], e[3], e[4]] for e in s]),
             W("a top-step block more than half off the step below", "build", moved(s, lambda e: near(e[2], 1) and near(e[3], 4.5), dx=2.2))])
# 3 Ziggurat of Ur
s = (row("stone", -5, 5, 0.5) + [["beam", "wood", x, 1.25, 0] for x in (-3.2, 0, 3.2)] + [tri_rest(-5, 0, "right", "stone")] +
     row("stone", -4, 4, 2.0) + row("mudbrick", -4, 4, 3.0) + [["beam", "wood", x, 3.75, 0] for x in (-1.6, 1.6)] + row("mudbrick", -2, 2, 4.5))
level("ziggurat", "Ζιγκουράτ της Ουρ", "c. 2100 BC", "three terraces with reed-mat courses, a stairway, the temple on top",
      "Britannica: mudbrick core strengthened with reed matting, three tiers, staircases, temple of Nanna on top (not preserved); wood courses stand for the reed mats; the stairway is one triangle",
      s, [rect(-1.5, 5, 1.5, 6.0)], woodRole="courses",
      wrong=[W("mudbrick in the base, stone in the top terrace", "material", [[e[0], "mudbrick" if near(e[3], 0.5) and e[0] == "block" else "stone" if near(e[3], 4.5) else e[1], e[2], e[3], e[4]] for e in s]),
             W("a top-terrace block more than half off the terrace below", "build", moved(s, lambda e: near(e[2], 1) and near(e[3], 4.5), dx=3.2))])
# 4 Lion Gate (owner, 13 Nov: before Karnak, it is easier): the lion triangle (headpiece) is lowered onto the lintel between the stepped-in stones
gate = rect(-1, 0, 1, 2)
s = (mirror([["block", "stone", -5, 0.5, 0], ["block", "stone", -3, 0.5, 0], ["square", "stone", -5.5, 1.5, 0], ["block", "stone", -4, 1.5, 0], ["square", "stone", -2.5, 1.5, 0],
             ["block", "stone", -1.5, 1.0, UP]]) +
     [["beam", "stone", x, 2.25, 0] for x in (-3.2, 0, 3.2)] +
     mirror([["block", "stone", -4.0, 3.0, 0], ["square", "stone", -2.0, 3.0, 0]]) +  # owner (13 Nov): back to the lower version
     mirror([["beam", "wood", -2.75, 4.1, UP]]))  # flagpoles held between two stones
level("liongate", "Πύλη των Λεόντων", "c. 1250 BC", "jambs, a stone lintel, flagpoles held between stones, and the lion triangle lowered onto the lintel",
      "two monolith jambs and a great lintel (4.5 x 2.0 x 0.8 m, about 20 t); the lion relief, a triangle, stands on the lintel in the relieving triangle (Wikipedia); "
      "the real corbelled courses close over the relief, which a slab lowered from above cannot pass, so the relief stands free on the lintel; the flagpoles are the owner's addition (no source found for them)",
      s, [Polygon([(-1.45, 2.52), (1.45, 2.52), (0, 5.1)])], [gate],
      wrong=[W("mudbrick jambs", "material", recolour(s, lambda e: e[0] == "block" and e[4] != 0, "mudbrick")),
             W("wooden planks as the lintel over the door", "material", recolour(s, lambda e: e[0] == "beam" and e[1] == "stone", "wood")),
             W("mudbrick for the jambs and the lower walls", "material", recolour(s, lambda e: e[0] in ("block", "square") and e[3] < 2, "mudbrick")),
             W("one jamb left out", "build", without(s, lambda e: e[0] == "block" and e[4] != 0 and e[2] < 0))])
# 5 Karnak (owner, 13 Nov: after the Lion Gate, which is easier): four identical columns (two outer, two middle), every pillar topped by a capital of two small stacked blocks;
# the side beams rest on the outer and middle capitals; the taller middle nave stands on square pillars over the beam ends
def cap(x, y): return [["abacus", "stone", x, y + 0.2, 0], ["abacus", "stone", x, y + 0.6, 0]]
s = row("stone", -5, 5, 0.5) + mirror([["column", "stone", -3.7, 2.2, 0], *cap(-3.7, 3.4), ["column", "stone", -1.3, 2.2, 0], *cap(-1.3, 3.4),
                                        ["beam", "stone", -2.5, 4.45, 0], ["square", "stone", -1.3, 5.2, 0], *cap(-1.3, 5.7)])
level("karnak", "Υπόστυλη αίθουσα του Καρνάκ", "c. 1290-1220 BC", "beams across gaps between columns",
      "cut through the hall on a platform: four columns with capitals carry the side beams; the middle nave is taller, on square pillars with capitals over the beam ends (University of Memphis: central nave taller)",
      s, [rect(-1.6, 6.5, 1.6, 7.0)], [rect(-3.4, 1, -1.6, 4.2), rect(1.6, 1, 3.4, 4.2)],  # the aisles between the columns, up to the beams
      wrong=[W("mudbrick pillars under the middle roof", "material", recolour(s, lambda e: e[0] == "square", "mudbrick")),
             W("mudbrick capitals", "material", recolour(s, lambda e: e[0] == "abacus", "mudbrick")),
             W("a mudbrick platform", "material", recolour(s, lambda e: e[0] == "block", "mudbrick")),
             W("wooden planks as the side beams", "material", recolour(s, lambda e: e[0] == "beam", "wood")),
             W("mudbrick middle columns", "material", recolour(s, lambda e: e[0] == "column" and abs(e[2]) < 2, "mudbrick")),
             W("a middle column too far in for the beam", "build", moved(s, lambda e: near(e[2], -1.3) and e[3] < 4.3, dx=1.0))])
# 6 Ishtar Gate
s = ([p for y in (0.5, 1.5) for p in row("stone", -6, 2, y) + row("stone", 2, 2, y)] +
     [p for y in (2.5, 3.5, 4.5, 5.5, 6.5) for p in (["block", "stone" if y < 4 else "mudbrick", -(ARCH_X + 2), y, 0], ["block", "stone" if y < 4 else "mudbrick", ARCH_X + 2, y, 0])] +
     arch(0, 2, 2) + [p for y in (2.5, 3.5, 4.5) for p in (["square", "stone", -(ARCH_X + 0.5), y, 0], ["square", "stone", ARCH_X + 0.5, y, 0])] +
     [tri_at(-ARCH_X, 5, 1, kind="trib"), tri_at(ARCH_X, 5, -1, kind="trib")])
ish = s
level("ishtar", "Πύλη της Ιστάρ", "c. 575 BC", "a stone arch on a wooden form",
      "nine wedges on a wooden form, the arch top exactly 3 m above its feet; big triangles in the corners rest on the arch, flush with its top; roof of cedar (worldhistory.org)",
      s, [rect(-3.8, 5, 3.8, 5.6), rect(-6.05, 7, -4.05, 7.6), rect(4.05, 7, 6.05, 7.6)], [arch_hole(0, 2, 0)], "support",  # owner: a headpiece as thick as the roof on each tower
      wrong=[W("mudbrick under the arch's feet", "material", recolour(s, lambda e: e[3] < 2 and e[1] == "stone" and abs(abs(e[2]) - 3) < 0.01, "mudbrick")),
             W("mudbrick towers all the way down", "material", recolour(s, lambda e: e[0] == "block" and e[3] > 2 and abs(abs(e[2]) - (ARCH_X + 2)) < 0.01, "mudbrick")),
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
      [rect(a + 0.5, P0, b - 0.5, P0 + DR + 0.4) for a, b in zip(COLS, COLS[1:])],  # between the columns, up to the architrave
      wrong=[W("mudbrick in the top step", "material", recolour(s, lambda e: near(e[3], P0 - 0.5), "mudbrick")),
             W("drums stacked off line", "build", moved(s, lambda e: e[0] == "square" and near(e[3], P0 + 1.5) and near(e[2], 3.0), dx=0.6)),
             W("an end column too far out for the architrave", "build", moved(s, lambda e: e[0] in ("square", "capital") and near(e[2], 5.0) and e[3] > P0, dx=1.0))])
# 8 Mausoleum: solid core, columns, the walkway ceiling beams reach out from the core further than they hold alone:
# wooden posts hold them while the roof steps go on, then come out
s = (row("stone", -6, 6, 0.5) +
     [["square", "stone", 0, 2.5, 0], ["square", "stone", 0, 3.5, 0], ["capital", "stone", 0, 4.2, 0]] +  # owner: the middle column half as wide (one square), its capital wider than it, like the side columns
     [p for x in (-5.0, 5.0) for p in (["square", "stone", x, 2.5, 0], ["square", "stone", x, 3.5, 0], ["capital", "stone", x, 4.2, 0])] +
     [["column", "wood", x, 3.2, 0] for x in (-2.6, 2.6)] +   # temporary posts
     [["beam", "stone", x, 4.65, 0] for x in (-4.8, -1.6, 1.6, 4.8)] +   # owner: the lintels meet, no gap between them
     [p for k in range(5) for p in row("stone", -(5 - k), 5 - k, 5.4 + k)] +   # owner: the roof a square narrower (on each side, so its joints still overlap)
     [t for k in range(1, 4) for t in (tri_rest(5 - k, 4.9 + k, "left", "stone"), tri_rest(-(5 - k), 4.9 + k, "right", "stone"))])  # roof sloped by triangles; owner: the top two removed
s = [e if e[3] < 1 else [e[0], e[1], e[2], round(e[3] - 1, 4), e[4]] for e in s]  # one podium course
maus = s
level("mausoleum", "Μαυσωλείο της Αλικαρνασσού", "c. 350 BC", "beams reaching out from the core, held on wooden posts until the roof weighs them down; a sloped roof",
      "Pliny: podium, 36 columns, a pyramid of 24 steps, a four-horse chariot on top (corroborated by excavation, worldhistory.org); a solid core behind the columns carried the roof (Wikipedia); ceiling beams of the walkway were found (AJA). Cut through: core in the middle, a column each side; the wooden posts are the game's way of building it",
      s, [Polygon([(-0.9, 8.9), (0.9, 8.9), (1.0, 9.4), (0.5, 10.0), (-0.6, 10.0), (-1.0, 9.4)]), acroterion(-5.95, 3.9, 0.45), acroterion(5.95, 3.9, 0.45)],
      [rect(-4.5, 1, -0.5, 3.4), rect(0.5, 1, 4.5, 3.4)], "support",  # the walkways between the columns and the core; the acroteria stay on the lintel ends, moved in with them
      wrong=[W("mudbrick in the middle column", "material", recolour(s, lambda e: e[0] == "square" and near(e[2], 0) and 1 < e[3] < 3, "mudbrick")),
             W("mudbrick side columns", "material", recolour(s, lambda e: e[0] == "square" and abs(e[2]) > 4 and e[3] < 3, "mudbrick")),
             W("one column left out", "build", without(s, lambda e: e[0] in ("square", "capital") and near(e[2], -5.0) and e[3] < 3.5))])  # posts pulled early no longer fails: the lintels now meet and hold each other
# 9 Lighthouse: tall hollow lowest tier, two thin walls round a shaft tied by wooden beams, a stone cap, a narrower tier, a round top, statue and Tritons
def pharos(tied=True, cap="stone"):
    out = []
    for k in range(7):  # lowest tier: walls of blocks round the shaft; every other course two wooden beams tie them
        y = k + 0.5
        if k % 2 == 1:
            out += ([["beam", "wood", 0, k + 0.25, 0], ["beam", "wood", 0, k + 0.75, 0]] if tied else [["square", "stone", -1.1, y, 0], ["square", "stone", 1.1, y, 0]]) + \
                   [["square", "stone", -2.1, y, 0], ["square", "stone", 2.1, y, 0]]
        else:
            out += [["block", "stone", -1.6, y, 0], ["block", "stone", 1.6, y, 0]]
    y = 7.0  # second tier: hollow too, walls one square thick, tied by one wooden beam between courses
    for part in ("w", "t", "w", "t", "w"):
        if part == "t": out.append(["beam", "wood", 0, y + 0.25, 0]); y += 0.5
        else: out += [["square", "stone", -1.1, y + 0.5, 0], ["square", "stone", 1.1, y + 0.5, 0]]; y += 1
    out += [["block", cap, 0, y + 0.5, 0]]  # a stone over the shaft (owner: the top square removed)
    return out
s = pha = pharos()
level("pharos", "Φάρος της Αλεξάνδρειας", "c. 280 BC", "a tall hollow tower: two walls tied by wooden beams, a narrower hollow tier, a round top",
      "square, octagonal and round tiers (Wikipedia); a spiral ramp inside the lowest tier and a shaft in the upper ones (Balawi via Wikipedia; mfn.li); statue on top and Tritons on the corners (Roman coins). Walls laced with timber are an old Greek technique; for the Pharos the sources name lead between the base blocks",
      s, [rect(-1, 12, 1, 13), acroterion(-2.1, 7, 0.4, 0.8), acroterion(2.1, 7, 0.4, 0.8)],  # owner: the top headpiece as big as a block lying down
      [rect(-0.6, k, 0.6, k + 1) for k in (0, 2, 4)] + [rect(-0.6, 6, 0.6, 7)] + [rect(-0.6, 7, 0.6, 8), rect(-0.6, 8.5, 0.6, 9.5), rect(-0.6, 10, 0.6, 11)],
      wrong=[W("mudbrick at the base", "material", recolour(s, lambda e: e[0] == "block" and e[3] < 2, "mudbrick")),
             W("mudbrick ties instead of wood", "material", recolour(s, lambda e: e[0] == "beam", "mudbrick")),
             W("mudbrick walls in the upper tier", "material", recolour(s, lambda e: e[0] == "square" and e[3] > 7, "mudbrick")),
             W("a mudbrick stone over the shaft", "material", pharos(cap="mudbrick")),
             W("no wooden ties (the walls stacked straight up)", "build", pharos(tied=False)),
             W("the upper tier set off centre", "build", moved(s, lambda e: e[3] > 7, dx=1.0))])
# 10 Valens: two forms for four arches, moved from the lower to the upper arches
VX = ARCH_X  # arch centres; neighbouring arches touch at their feet
def tier(sy):  # side walls a square wide, a big triangle in each corner beside the arches, flush with their tops
    return [p for k in range(3) for p in (["square", "stone", -(2 * VX + 0.5), sy + 0.5 + k, 0], ["square", "stone", 2 * VX + 0.5, sy + 0.5 + k, 0])] + \
        [tri_at(-2 * VX, sy + 3, 1, kind="trib"), tri_at(0, sy + 3, -1, kind="trib"), tri_at(0, sy + 3, 1, kind="trib"), tri_at(2 * VX, sy + 3, -1, kind="trib")]
UPPER = 5.0
lower = [["block", "stone", -2 * VX, 0.5, 0], ["block", "stone", 0, 0.5, 0], ["block", "stone", 2 * VX, 0.5, 0]] + arch(-VX, 1, 0, single=True) + arch(VX, 1, 0, single=True) + tier(1) + \
    row("stone", -7, 7, UPPER - 0.5)
s = lower + [PULL] + arch(-VX, UPPER, 0) + arch(VX, UPPER, 0) + tier(UPPER)
level("valens", "Υδραγωγείο του Ουάλη", "AD 368", "two tiers of arches, two forms moved from arch to arch",
      "real upper arches are smaller; same size here because there is one wedge size; three piers under the lower arches and a full course between the tiers",
      s, [rect(-(2 * VX + 1), UPPER + 3, 2 * VX + 1, UPPER + 3.6)], [arch_hole(-VX, 1, 0), arch_hole(VX, 1, 0), arch_hole(-VX, UPPER), arch_hole(VX, UPPER)], "support",
      wrong=[W("mudbrick piers", "material", recolour(s, lambda e: e[0] == "block" and near(e[3], 0.5), "mudbrick")),
             W("a form pulled out before the last wedge", "build", (lambda i: s[:i] + [PULL] + s[i:])(max(k for k, e in enumerate(lower) if e[0] == "wedge")))])

def flat(ring):
    cs = list(ring.coords)[:-1]
    return [round(v, 3) for c in cs for v in c]

out = []
for l in L:
    sup = l["woodRole"] == "support"
    shapes = [placed(d, x, y, a) for d, m, x, y, a in l["sol"] if d != "pull" and not (sup and m == "wood")]
    holes = list(l["holes"])
    F = Frame(shapes + holes)
    # the outline is the shape of the building: its outer edge drawn solid (seams, slivers, enclosed gaps and narrow
    # notches inside it), minus only the openings the level declares; openings that touch are one opening
    u = F.disk(F.mask(shapes), RES_SEAM, cv2.MORPH_CLOSE)
    hm = F.mask(holes)
    sil = F.square(u | hm, NOTCH, cv2.MORPH_CLOSE)
    for kw, kh in ((3.0, 0.02), (0.02, 3.0)):  # shallow dips along flat edges: filled where the gap left is thinner than DIP
        k = (max(1, int(kw / 0.005)) | 1, max(1, int(kh / 0.005)) | 1)
        add = cv2.morphologyEx(sil, cv2.MORPH_CLOSE, np.ones((k[1], k[0]), np.uint8)) & (1 - sil)
        n, lab, st, _ = cv2.connectedComponentsWithStats(add, connectivity=8)
        for c in range(1, n):
            if min(st[c, cv2.CC_STAT_WIDTH], st[c, cv2.CC_STAT_HEIGHT]) * 0.005 <= DIP: sil[lab == c] = 1
    sil = F.mask(F.rings(sil))
    opening = F.keep(F.disk(hm & (1 - u), RES_SEAM, cv2.MORPH_CLOSE), 0.05)  # a declared opening less what the build's pieces fill
    ext, ints = F.rings(sil), F.rings(opening)
    wedges = [placed(d, x, y, a) for d, m, x, y, a in l["sol"] if d == "wedge"]  # the wedges get thin guide lines
    wood = []
    if sup: wood = ints  # temporary supports stand in the openings (as drawn, less what the build's pieces fill)
    elif l["woodRole"] == "courses":  # the wood zone is where the build's wooden pieces lie
        wood = F.rings(F.disk(F.mask([placed(d, x, y, a) for d, m, x, y, a in l["sol"] if d != "pull" and m == "wood"]), RES_SEAM, cv2.MORPH_CLOSE))
    out.append(dict(key=l["key"], nameEl=l["nameEl"], date=l["date"], newDemand=l["newDemand"],
                    solid=[flat(r.exterior) for r in ext], holes=[flat(r.exterior) for r in ints],
                    load=[flat(p.exterior) for p in l["load"]], wood=[flat(h.exterior) for h in wood],
                    woodRole=l["woodRole"], note=l["note"],
                    guides=[flat(w.exterior) for w in wedges],
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
    for w in l["wrong"]:  # levels.md: the pieces each wrong choice puts in place of the right ones, on top of the build
        right = {(e[0], round(e[2], 3), round(e[3], 3)): e[1] for e in l["sol"] if e[0] != "pull"}
        swap = Counter((e[0], e[1]) for e in w["sol"] if e[0] != "pull" and right.get((e[0], round(e[2], 3), round(e[3], 3)), e[1]) != e[1])
        ex |= swap + ((stock(w["sol"]) - base) - swap)
    o["extra"] = [[d, m, n] for (d, m), n in sorted(ex.items())]
js = js[:js.index("const LEVELS = ")] + "const LEVELS = " + json.dumps(out, ensure_ascii=False) + ";\n"
(HERE / "src" / "levels.js").write_text(js, encoding="utf-8")
tests = {l["key"]: [dict(name=w["name"], kind=w["kind"], sol=[r4(e) for e in w["sol"]]) for w in l["wrong"]] for l in L}
(HERE / "tools" / "level-tests.json").write_text(json.dumps(tests, ensure_ascii=False), encoding="utf-8")
for o in out: print(o["key"], len(o["solution"]), "pieces,", len(o["solid"]), "rings,", len(o["holes"]), "holes")
