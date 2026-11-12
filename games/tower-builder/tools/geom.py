"""Small geometry helpers for the level tools (numpy + OpenCV, no shapely): simple polygons and a fine raster
for unions, openings and outlines. Raster cell RES metres; rings come back to within about RES."""
import math
import numpy as np
import cv2

RES = 0.005  # metres per raster cell


class Ring:
    def __init__(self, pts): self.coords = list(pts) + [pts[0]]


class Polygon:
    geom_type = "Polygon"

    def __init__(self, pts=()):
        self.pts = [(float(x), float(y)) for x, y in (pts.coords[:-1] if isinstance(pts, Ring) else pts)]
        self.exterior = Ring(self.pts) if self.pts else None
        self.is_empty = not self.pts

    def _sa(self):
        p = self.pts; n = len(p); a = cx = cy = 0.0
        for i in range(n):
            x0, y0 = p[i]; x1, y1 = p[(i + 1) % n]; c = x0 * y1 - x1 * y0
            a += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
        return a / 2, cx, cy

    @property
    def area(self): return abs(self._sa()[0])

    @property
    def centroid(self):
        a, cx, cy = self._sa()
        class P: pass
        c = P(); c.x = cx / (6 * a); c.y = cy / (6 * a); return c

    @property
    def bounds(self):
        xs = [p[0] for p in self.pts]; ys = [p[1] for p in self.pts]
        return (min(xs), min(ys), max(xs), max(ys))


def box(x0, y0, x1, y1): return Polygon([(x1, y0), (x1, y1), (x0, y1), (x0, y0)])  # shapely's order


class affinity:
    @staticmethod
    def rotate(p, a, origin=(0, 0), use_radians=True):
        c, s = math.cos(a), math.sin(a); ox, oy = origin
        return Polygon([(ox + (x - ox) * c - (y - oy) * s, oy + (x - ox) * s + (y - oy) * c) for x, y in p.pts])

    @staticmethod
    def translate(p, dx, dy): return Polygon([(x + dx, y + dy) for x, y in p.pts])


class Frame:
    """A raster over the polygons' bounds plus a margin."""
    def __init__(self, polys, margin=1.5):
        xs = [x for p in polys for x, _ in p.pts]; ys = [y for p in polys for _, y in p.pts]
        self.x0, self.y1 = math.floor((min(xs) - margin) / RES) * RES, math.ceil((max(ys) + margin) / RES) * RES
        self.w = int((max(xs) + margin - self.x0) / RES) + 1; self.h = int((self.y1 - (min(ys) - margin)) / RES) + 1

    def mask(self, polys):
        m = np.zeros((self.h, self.w), np.uint8)
        for p in polys:
            q = np.array([[(x - self.x0) / RES * 16, (self.y1 - y) / RES * 16] for x, y in p.pts], np.int32)
            cv2.fillPoly(m, [q], 1, lineType=cv2.LINE_8, shift=4)
        return m

    def disk(self, m, r, op):  # dilate / erode / close / open by a disk of r metres
        k = int(round(r / RES)); ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1))
        return cv2.morphologyEx(m, op, ker)

    def keep(self, m, min_area):  # drop pieces smaller than min_area m^2
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        out = np.zeros_like(m)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] * RES * RES >= min_area: out[lab == i] = 1
        return out

    def rings(self, m, outer_only=True):  # outer boundaries (and, if asked, inner ones) as Polygons in metres
        cs, hier = cv2.findContours(m, cv2.RETR_CCOMP if not outer_only else cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        out = []
        for c in cs:
            a = cv2.approxPolyDP(c, 1.5, True)[:, 0, :]
            if len(a) < 3: continue
            out.append(Polygon(_corners([(self.x0 + x * RES, self.y1 - y * RES) for x, y in a])))
        return out


def _corners(pts, d=0.016):
    """Tracing cuts each inner corner by a cell; two vertices closer than d become the corner where their edges meet."""
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if math.dist(a, b) < d:
                p, q = pts[i - 1], pts[(i + 2) % n]
                d1 = (a[0] - p[0], a[1] - p[1]); d2 = (q[0] - b[0], q[1] - b[1]); den = d1[0] * d2[1] - d1[1] * d2[0]
                if abs(den) > 1e-9 * math.hypot(*d1) * math.hypot(*d2) * 1e3:
                    t = ((b[0] - p[0]) * d2[1] - (b[1] - p[1]) * d2[0]) / den
                    c = (p[0] + t * d1[0], p[1] + t * d1[1])
                    if math.dist(c, a) > 3 * d: c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                else: c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                pts = [c if k == i else pts[k] for k in range(n) if k != (i + 1) % n]
                changed = True
                break
    return [(round(x, 3), round(y, 3)) for x, y in pts]
