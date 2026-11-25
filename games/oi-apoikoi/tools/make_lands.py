# Makes the 6 land pictures in art/lands/: each land as its ground (<land>-ground.svg: the square's top diamond and its two front walls of earth)
# and the things standing on it (<land>-things.svg). Flat vector look in isometric view: light from the upper left (top lightest, left wall
# lighter, right wall darker), soft shadows, many small things packed close. Seeded: the same pictures every run. python3 tools/make_lands.py
import math, random, pathlib

S = 256                 # a square's diamond is S wide and S / 2 high
WALL = 52               # the walls' height (about 0.4 of the diamond's height)
OUT = pathlib.Path(__file__).resolve().parent.parent / 'art' / 'lands'


def mix(a, b, k):  # colour between a and b (hex), k from 0 (a) to 1 (b)
    pa, pb = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * k) for x, y in zip(pa, pb))
def dark(c, k): return mix(c, '#1a1208', k)
def light(c, k): return mix(c, '#fffbe8', k)
def f(v): return ('%.1f' % v).rstrip('0').rstrip('.')
def pts(ps): return ' '.join(f(x) + ',' + f(y) for x, y in ps)


class Iso:  # a point on the square (u, v from 0 to 1 across it), z up, on a picture whose diamond's top corner is at (S / 2, oy)
    def __init__(self, oy): self.oy = oy
    def __call__(self, u, v, z=0): return (S / 2 + (u - v) * S / 2, self.oy + (u + v) * S / 4 - z)


def poisson(rng, n, gap, lo=0.08, hi=0.92, tries=4000):  # up to n points on the square, at least gap apart (in u, v), back to front
    got = []
    for _ in range(tries):
        if len(got) >= n: break
        p = (rng.uniform(lo, hi), rng.uniform(lo, hi))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 >= gap * gap for q in got): got.append(p)
    return sorted(got, key=lambda p: p[0] + p[1])


# ---------- the ground: top diamond and walls

def wavy(rng, x0, y0, x1, y1, amp, n=14):  # points from (x0, y0) to (x1, y1) with a little wave
    ph = rng.uniform(0, 6)
    return [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n + (amp * (math.sin(k * 1.7 + ph) + rng.uniform(-0.6, 0.6)) if 0 < k < n else 0)) for k in range(n + 1)]


def wall(rng, side, land):  # one front wall: side 0 the left (lit), 1 the right (shaded); bands from the top: lip, soil, a darker layer, soil, stones
    shade = 0.0 if side == 0 else 0.22
    if side == 0: a, b = (0, S / 4), (S / 2, S / 2)
    else: a, b = (S / 2, S / 2), (S, S / 4)
    at = lambda s, t: (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s + t * WALL)  # s along the top edge, t down the wall
    face = pts([at(0, 0), at(1, 0), at(1, 1), at(0, 1)])
    out = ['<g clip-path="url(#w%d)">' % side, '<polygon points="%s" fill="%s"/>' % (face, dark(land['soil'], shade))]
    def band(t0, t1, col, amp0, amp1):  # a band between two wavy lines across the wall
        top = [at(k / 14, t0 + (amp0 * (math.sin(k * 1.9 + side * 2 + t0 * 9) * 0.5 + rng.uniform(-0.5, 0.5)) / WALL if 0 < k < 14 else 0)) for k in range(15)]
        bot = [at(k / 14, t1 + (amp1 * (math.sin(k * 1.3 + side + t1 * 7) * 0.5 + rng.uniform(-0.5, 0.5)) / WALL if 0 < k < 14 else 0)) for k in reversed(range(15))]
        if t0 <= 0: top = [at(0, -0.05), at(1, -0.05)]
        if t1 >= 1: bot = [at(1, 1.05), at(0, 1.05)]
        out.append('<polygon points="%s" fill="%s"/>' % (pts(top + bot), dark(col, shade)))
    for t0, t1, col in land['layers']: band(t0, t1, col, 5, 5)
    for _ in range(land.get('stones', 9)):  # stones in the earth: a darker oval with a lit top
        s, t, r = rng.uniform(0.05, 0.95), rng.uniform(0.42, 0.9), rng.uniform(2.2, 4.5)
        x, y = at(s, t); c = dark(land['stone'], shade)
        out.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/><ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>' % (f(x), f(y), f(r * 1.3), f(r), c, f(x - r * 0.3), f(y - r * 0.35), f(r * 0.6), f(r * 0.4), light(c, 0.35)))
    lip = land['lip']  # the top lip, hanging over the earth in little drips
    drip = [at(0, -0.02), at(1, -0.02)]
    edge = []
    for k in range(29):
        s = k / 28; t = 0.16 + (0.07 * (1 if k % 2 else -0.3) + rng.uniform(-0.03, 0.06) if 0 < k < 28 else 0)
        edge.append(at(s, t))
    out.append('<polygon points="%s" fill="%s"/>' % (pts(drip + edge[::-1]), dark(lip, shade)))
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.2" opacity="0.5"/>' % (pts(edge), dark(lip, shade + 0.25)))
    hi = [at(s / 10, 0.02) for s in range(11)]  # a lit line just under the top edge
    out.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2" opacity="%s"/>' % (pts(hi), light(lip, 0.5), '0.8' if side == 0 else '0.35'))
    out.append('<polygon points="%s" fill="url(#fade)"/>' % face)  # darker towards the water
    out.append('</g>')
    return out


def ground(land, rng):
    d = Iso(0)
    top = pts([d(0, 0), d(1, 0), d(1, 1), d(0, 1)])
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (S, S // 2 + WALL, S, S // 2 + WALL), '<defs>',
         '<clipPath id="d"><polygon points="%s"/></clipPath>' % top,
         '<clipPath id="w0"><polygon points="%s"/></clipPath>' % pts([(0, S / 4), (S / 2, S / 2), (S / 2, S / 2 + WALL), (0, S / 4 + WALL)]),
         '<clipPath id="w1"><polygon points="%s"/></clipPath>' % pts([(S / 2, S / 2), (S, S / 4), (S, S / 4 + WALL), (S / 2, S / 2 + WALL)]),
         '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0.55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#0b2030" stop-opacity="0.35"/></linearGradient>',
         '<linearGradient id="sun" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.18"/><stop offset="0.6" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.08"/></linearGradient>',
         '</defs>']
    o += wall(rng, 0, land) + wall(rng, 1, land)
    o.append('<polygon points="%s" fill="%s"/>' % (top, land['top']))
    o.append('<g clip-path="url(#d)">')
    for c, n, size in land['patches']:  # patches of other shades: the ground is never one flat colour
        for _ in range(n):
            u, v, r = rng.uniform(-0.1, 1.1), rng.uniform(-0.1, 1.1), rng.uniform(*size)
            x, y = d(u, v); o.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>' % (f(x), f(y), f(r), f(r / 2), c))
    o += land['top_detail'](d, rng)
    o.append('<polygon points="%s" fill="url(#sun)"/>' % top)
    o.append('</g>')
    o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.5" stroke-linejoin="round" opacity="0.7"/>' % (pts([d(0, 1), d(0, 0), d(1, 0)]), light(land['top'], 0.45)))  # lit back edges
    o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.5" stroke-linejoin="round" opacity="0.6"/>' % (pts([d(0, 1), d(1, 1), d(1, 0)]), dark(land['top'], 0.25)))  # the front edges
    o.append('</svg>')
    return '\n'.join(o)


# ---------- things

def shadow(d, u, v, r, k=0.22):
    x, y = d(u, v); return '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#1a2a10" opacity="%s"/>' % (f(x + r * 0.25), f(y + r * 0.08), f(r), f(r * 0.5), k)


def blades(d, rng, n, cols, h=(5, 9), w=1.3):  # little tufts of grass on the top
    o = []
    for _ in range(n):
        u, v = rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95); x, y = d(u, v); c = rng.choice(cols); hh = rng.uniform(*h)
        o.append('<path d="M%s %sl%s %sM%s %sl%s %sM%s %sl%s %s" stroke="%s" stroke-width="%s" stroke-linecap="round" fill="none"/>' % (
            f(x - 2), f(y), f(-1.5), f(-hh * 0.8), f(x), f(y), f(0.3), f(-hh), f(x + 2), f(y), f(1.8), f(-hh * 0.75), c, w))
    return o


def wheat_things(d, rng):
    o = ['<defs>']
    for k in range(4):  # bunches of stalks, each a little different
        g = ['<g id="b%d">' % k]
        for j in range(7):
            a = (j - 3) * 0.13 + rng.uniform(-0.06, 0.06); h = rng.uniform(26, 36); tx, ty = math.sin(a) * h, -math.cos(a) * h
            g.append('<path d="M0 0Q%s %s %s %s" stroke="#c49a3a" stroke-width="1.4" fill="none"/>' % (f(tx * 0.3), f(ty * 0.5), f(tx), f(ty)))
            col = ['#f2cf62', '#e8bb45', '#f7dc7c'][j % 3]
            g.append('<g transform="translate(%s %s) rotate(%s)"><ellipse rx="2.8" ry="7" fill="%s"/><ellipse cx="1" rx="1.4" ry="6" fill="%s"/>'
                     '<path d="M0 -7 0 -12" stroke="%s" stroke-width="0.8"/></g>' % (f(tx), f(ty), f(math.degrees(a)), col, dark(col, 0.18), light(col, 0.3)))
        g.append('</g>'); o += g
    o.append('</defs>')
    for k in range(9):  # rows along the furrows, packed
        for j in range(9):
            u, v = 0.08 + k * 0.105 + rng.uniform(-0.02, 0.02), 0.08 + j * 0.105 + rng.uniform(-0.03, 0.03)
            if rng.random() < 0.06: continue
            x, y = d(u, v); o.append('<ellipse cx="%s" cy="%s" rx="7" ry="3" fill="#6b4a12" opacity="0.18"/>' % (f(x + 2), f(y + 1)))
            o.append('<use href="#b%d" x="%s" y="%s"/>' % (rng.randrange(4), f(x), f(y)))
            if rng.random() < 0.06:  # a poppy among the wheat
                o.append('<path d="M%s %sl0 -22" stroke="#4d7a2a" stroke-width="1.2"/><circle cx="%s" cy="%s" r="3.6" fill="#d8322a"/><circle cx="%s" cy="%s" r="1.8" fill="#f25a48"/><circle cx="%s" cy="%s" r="1" fill="#2a1a10"/>' % (
                    f(x + 4), f(y), f(x + 4), f(y - 23), f(x + 3), f(y - 24), f(x + 4), f(y - 23)))
    return o


def tree(x, y, rng, canopy, r, trunk='#7a4f2a', fruit=None, fruits=0):  # a round tree: trunk, a canopy of overlapping balls (dark, mid, lit), fruit
    o = ['<path d="M%s %s l2 -%s l4 0 l2 %s z" fill="%s"/><path d="M%s %s l2 -%s l2 0 l0 %s z" fill="%s"/>' % (
        f(x - 4), f(y), f(r * 0.9), f(r * 0.9), trunk, f(x), f(y), f(r * 0.9), f(r * 0.9), dark(trunk, 0.3))]
    cy = y - r * 1.55
    for dx, dy, k, c in ((-0.45, 0.15, 0.62, dark(canopy, 0.25)), (0.45, 0.15, 0.62, dark(canopy, 0.3)), (0, 0.25, 0.7, dark(canopy, 0.2)),
                         (-0.25, -0.25, 0.66, canopy), (0.3, -0.2, 0.6, canopy), (0, -0.5, 0.55, light(canopy, 0.12)), (-0.35, -0.45, 0.32, light(canopy, 0.3))):
        o.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (f(x + dx * r), f(cy + dy * r), f(k * r), c))
    for _ in range(fruits):
        a, q = rng.uniform(0, 6.28), rng.uniform(0.2, 0.85); fx, fy = x + math.cos(a) * r * 0.85 * q, cy + math.sin(a) * r * 0.7 * q + r * 0.1
        o.append('<circle cx="%s" cy="%s" r="3.3" fill="%s"/><circle cx="%s" cy="%s" r="1.3" fill="%s"/><path d="M%s %sl0 -2" stroke="%s" stroke-width="1.4"/>' % (
            f(fx), f(fy), fruit, f(fx - 1), f(fy - 1), light(fruit, 0.45), f(fx), f(fy - 3), dark(fruit, 0.35)))
    return o


def pomegranate_things(d, rng):
    o = blades(d, rng, 40, ['#5f9a34', '#7cb342', '#4d8a2a'])
    for _ in range(14):  # small flowers in the grass
        u, v = rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95); x, y = d(u, v)
        o.append('<circle cx="%s" cy="%s" r="1.8" fill="%s"/>' % (f(x), f(y - 1), rng.choice(['#fff6d0', '#f6d84a', '#f08a7a'])))
    for u, v in poisson(rng, 5, 0.36, 0.2, 0.8):
        x, y = d(u, v); r = rng.uniform(19, 23)
        o.append(shadow(d, u, v, r * 1.1))
        o += tree(x, y, rng, '#3f8a2e', r, fruit='#c8202a', fruits=9)
        for _ in range(2):  # fallen fruit
            fx, fy = x + rng.uniform(-16, 16), y + rng.uniform(-3, 5)
            o.append('<circle cx="%s" cy="%s" r="2.6" fill="#b51c26"/>' % (f(fx), f(fy)))
    return o


def vineyard_things(d, rng):
    o = blades(d, rng, 18, ['#6f8f2e', '#86a83a'], (3, 6))
    for k in range(4):  # rows of vines along the square, back to front, on posts and a wire
        v = 0.14 + k * 0.24
        p0, p1 = d(0.08, v), d(0.92, v)
        o.append('<polygon points="%s" fill="#2a1a08" opacity="0.15"/>' % pts([d(0.08, v + 0.03), d(0.92, v + 0.03), d(0.92, v + 0.09), d(0.08, v + 0.09)]))
        for u in (0.08, 0.5, 0.92):  # posts
            x, y = d(u, v); o.append('<path d="M%s %sl0 -22l3 -1l0 22z" fill="#8a6038"/><path d="M%s %sl0 -22l-2 0l0 22z" fill="#a8784a"/>' % (f(x), f(y), f(x), f(y)))
        o.append('<path d="M%s %sL%s %s" stroke="#5a4030" stroke-width="0.8"/>' % (f(p0[0]), f(p0[1] - 18), f(p1[0]), f(p1[1] - 18)))
        for j in range(15):  # the leaves along the wire, in three shades
            u = 0.1 + j * 0.056; x, y = d(u, v); y -= 16 + rng.uniform(-2, 2)
            for dx, dy, rr, c in ((-2, 3, 6.5, '#3e7a24'), (2, 1, 6, '#4f9230'), (-1, -3, 4.5, '#6db040'), (-2.5, -4, 2.2, '#9bd060')):
                o.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (f(x + dx), f(y + dy), f(rr), c))
            if j % 3 != 2:  # grapes hanging under the leaves
                gx, gy = x + rng.uniform(-2, 2), y + 6
                for a, b in ((0, 0), (-2.6, -1), (2.6, -1), (-1.3, 1.8), (1.3, 1.8), (0, 3.6), (-1.3, -2.6), (1.3, -2.6)):
                    o.append('<circle cx="%s" cy="%s" r="2.2" fill="#5b2a7a"/>' % (f(gx + a), f(gy + b)))
                o.append('<circle cx="%s" cy="%s" r="0.9" fill="#b58ad0"/><circle cx="%s" cy="%s" r="0.8" fill="#b58ad0"/>' % (f(gx - 1.6), f(gy - 1.6), f(gx + 1), f(gy + 0.6)))
    return o


def pine(x, y, rng, h):  # a tall dark cypress or a pine of stacked layers
    o = ['<rect x="%s" y="%s" width="4" height="8" fill="#6a4426"/>' % (f(x - 2), f(y - 8))]
    if rng.random() < 0.4:  # cypress: tall, narrow, two-sided
        w = h * 0.22
        o.append('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Z" fill="#245a2a"/>' % (f(x), f(y - h - 6), f(x - w * 1.3), f(y - h * 0.45), f(x - w * 0.5), f(y - 4), f(x), f(y - 2), f(x), f(y - 2)))
        o.append('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Z" fill="#1a4520"/>' % (f(x), f(y - h - 6), f(x + w * 1.3), f(y - h * 0.45), f(x + w * 0.5), f(y - 4), f(x), f(y - 2), f(x), f(y - 2)))
        o.append('<path d="M%s %s Q%s %s %s %s" stroke="#3f7a3a" stroke-width="1.5" fill="none"/>' % (f(x - 1), f(y - h), f(x - w * 0.9), f(y - h * 0.5), f(x - w * 0.6), f(y - 10)))
        return o
    for k in range(4):  # pine: layers, each a triangle with a lit left and a shaded right side
        t = y - 6 - k * h * 0.22; w = h * (0.42 - k * 0.08); top = t - h * 0.36
        o.append('<polygon points="%s" fill="#2f6b2f"/>' % pts([(x - w, t), (x, top), (x, t + 2)]))
        o.append('<polygon points="%s" fill="#1f5126"/>' % pts([(x + w, t), (x, top), (x, t + 2)]))
        o.append('<polyline points="%s" fill="none" stroke="#5a9a48" stroke-width="1.2"/>' % pts([(x - w * 0.8, t - 1), (x - 1, top + 2)]))
    return o


def rock(x, y, r, col='#8f8a80'):  # a faceted stone: lit top, mid front, dark right
    return ['<polygon points="%s" fill="%s"/><polygon points="%s" fill="%s"/><polygon points="%s" fill="%s"/>' % (
        pts([(x - r, y), (x - r * 0.6, y - r * 0.8), (x + r * 0.3, y - r * 0.9), (x + r, y - r * 0.2), (x + r * 0.2, y + r * 0.3)]), dark(col, 0.05),
        pts([(x - r * 0.6, y - r * 0.8), (x + r * 0.3, y - r * 0.9), (x + r * 0.1, y - r * 0.35), (x - r * 0.5, y - r * 0.3)]), light(col, 0.4),
        pts([(x + r * 0.3, y - r * 0.9), (x + r, y - r * 0.2), (x + r * 0.2, y + r * 0.3), (x + r * 0.1, y - r * 0.35)]), dark(col, 0.25))]


def forest_things(d, rng):
    o = blades(d, rng, 30, ['#3e7a2a', '#2f6a24', '#558f34'])
    for u, v in poisson(rng, 4, 0.2):
        x, y = d(u, v); o += rock(x, y, rng.uniform(4, 6), '#8a8478')
    for u, v in poisson(rng, 13, 0.19, 0.1, 0.9):
        x, y = d(u, v); h = rng.uniform(34, 50)
        o.append(shadow(d, u, v, h * 0.32, 0.25)); o += pine(x, y, rng, h)
    return o


def peak(x, y, w, h, rng, col):  # a rocky peak: a lit left face, a shaded right face, ridges, a pale top
    ax, ay = x + rng.uniform(-w * 0.15, w * 0.15), y - h
    mid = (x + w * 0.1, y + w * 0.12)
    o = ['<polygon points="%s" fill="%s"/>' % (pts([(x - w, y), (ax, ay), mid]), light(col, 0.12)),
         '<polygon points="%s" fill="%s"/>' % (pts([(ax, ay), (x + w, y), mid]), dark(col, 0.28))]
    for k in range(3):  # ridges down the lit face
        t = rng.uniform(0.3, 0.8); bx = x - w + (mid[0] - x + w) * rng.uniform(0.2, 0.9)
        o.append('<path d="M%s %sL%s %s" stroke="%s" stroke-width="1.6" fill="none"/>' % (f(ax + (bx - ax) * 0.25), f(ay + h * 0.25 * t), f(bx), f(y + 2), dark(col, 0.12)))
    o.append('<polygon points="%s" fill="#eef0ee"/><polygon points="%s" fill="#c8ccd0"/>' % (
        pts([(ax, ay), (ax - w * 0.28, ay + h * 0.3), (ax - w * 0.1, ay + h * 0.24), (ax, ay + h * 0.32)]),
        pts([(ax, ay), (ax + w * 0.26, ay + h * 0.28), (ax + w * 0.05, ay + h * 0.25), (ax, ay + h * 0.32)])))
    return o


def mountain_things(d, rng):
    o = []
    for u, v, w, h in ((0.3, 0.25, 46, 92), (0.72, 0.42, 38, 70), (0.42, 0.7, 34, 58)):
        x, y = d(u, v); o.append(shadow(d, u, v, w * 0.9, 0.2)); o += peak(x, y, w, h, rng, '#8c8a86')
    for u, v in poisson(rng, 10, 0.12):
        x, y = d(u, v)
        if (x - 128) ** 2 + (y - 192) ** 2 > 0: o += rock(x, y, rng.uniform(3, 6), rng.choice(['#9a958c', '#857f76']))
    for u, v in poisson(rng, 5, 0.2):  # rubies glinting among the stones
        x, y = d(u, v); o.append('<polygon points="%s" fill="#c41e3a"/><polygon points="%s" fill="#ff7a8a"/>' % (
            pts([(x, y - 6), (x + 3.5, y - 2), (x, y + 1), (x - 3.5, y - 2)]), pts([(x, y - 6), (x - 3.5, y - 2), (x - 0.5, y - 2.5)])))
    for _ in range(6):  # small shrubs
        u, v = rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9); x, y = d(u, v)
        o.append('<circle cx="%s" cy="%s" r="3.5" fill="#5a7a3a"/><circle cx="%s" cy="%s" r="2" fill="#7a9a4a"/>' % (f(x), f(y - 2), f(x - 1), f(y - 3)))
    return o


def house(d, u, v, du, dv, h, rng, wallc='#f3ead8', roof='#c2552e'):  # a box with a gabled roof, its ridge along u; door and window on its front faces
    p = lambda a, b, z=0: d(u + a, v + b, z)
    o = ['<polygon points="%s" fill="#1a1a10" opacity="0.18"/>' % pts([p(0, dv + 0.04), p(du + 0.05, dv + 0.04), p(du + 0.05, 0), p(du, 0)])]
    o.append('<polygon points="%s" fill="%s"/>' % (pts([p(0, dv), p(du, dv), p(du, dv, h), p(0, dv, h)]), wallc))  # front (lit)
    rh = h * 0.6
    o.append('<polygon points="%s" fill="%s"/>' % (pts([p(du, dv), p(du, 0), p(du, 0, h), p(du, dv / 2, h + rh), p(du, dv, h)]), dark(wallc, 0.16)))  # gable end (shade)
    o.append('<polygon points="%s" fill="%s"/>' % (pts([p(0, dv, h), p(du, dv, h), p(du, dv / 2, h + rh), p(0, dv / 2, h + rh)]), roof))  # roof facing us
    o.append('<polygon points="%s" fill="%s"/>' % (pts([p(du, dv, h), p(du + 0.012, dv + 0.012, h - 1), p(du + 0.012, dv / 2, h + rh), p(du, dv / 2, h + rh)]), dark(roof, 0.3)))
    for k in range(1, 5):  # tile lines on the roof
        a = du * k / 5; o.append('<path d="M%s %sL%s %s" stroke="%s" stroke-width="0.9"/>' % (*map(f, p(a, dv, h)), *map(f, p(a, dv / 2, h + rh)), dark(roof, 0.2)))
    o.append('<path d="M%s %sL%s %s" stroke="%s" stroke-width="2"/>' % (*map(f, p(0, dv / 2, h + rh)), *map(f, p(du, dv / 2, h + rh)), light(roof, 0.3)))
    dx = du * 0.35; o.append('<polygon points="%s" fill="#6b4226"/>' % pts([p(dx, dv), p(dx + 0.06, dv), p(dx + 0.06, dv, h * 0.55), p(dx, dv, h * 0.55)]))
    wx = du * 0.68; o.append('<polygon points="%s" fill="#3a5a7a"/>' % pts([p(wx, dv, h * 0.45), p(wx + 0.05, dv, h * 0.45), p(wx + 0.05, dv, h * 0.78), p(wx, dv, h * 0.78)]))
    return o


def temple(d, u, v, rng):  # a small temple: a step, columns, a pediment
    p = lambda a, b, z=0: d(u + a, v + b, z)
    du, dv, h = 0.3, 0.2, 22; o = ['<polygon points="%s" fill="#d8d0bc"/>' % pts([p(-0.02, dv + 0.02), p(du + 0.02, dv + 0.02), p(du + 0.02, dv + 0.02, 4), p(-0.02, dv + 0.02, 4)])]
    o.append('<polygon points="%s" fill="#b8ae98"/>' % pts([p(du + 0.02, dv + 0.02), p(du + 0.02, -0.02), p(du + 0.02, -0.02, 4), p(du + 0.02, dv + 0.02, 4)]))
    o.append('<polygon points="%s" fill="#a89e88"/>' % pts([p(0, 0, 4), p(du, 0, 4), p(du, dv, 4), p(0, dv, 4)]))
    for k in range(5):
        x, y = p(du * k / 4, dv, 4); o.append('<rect x="%s" y="%s" width="3.4" height="%s" fill="#f7f2e6"/><rect x="%s" y="%s" width="1.2" height="%s" fill="#cfc6b0"/>' % (f(x - 1.7), f(y - h), h, f(x + 0.5), f(y - h), h))
    for k in range(3):
        x, y = p(du, dv * k / 2, 4); o.append('<rect x="%s" y="%s" width="3" height="%s" fill="#d6ceb8"/>' % (f(x - 1.5), f(y - h), h))
    o.append('<polygon points="%s" fill="#efe8d8"/>' % pts([p(0, dv, 4 + h), p(du, dv, 4 + h), p(du, dv, 8 + h), p(0, dv, 8 + h)]))
    o.append('<polygon points="%s" fill="#c9c0aa"/>' % pts([p(du, dv, 4 + h), p(du, 0, 4 + h), p(du, 0, 8 + h), p(du, dv / 2, 16 + h), p(du, dv, 8 + h)]))
    o.append('<polygon points="%s" fill="#b0482a"/>' % pts([p(0, dv, 8 + h), p(du, dv, 8 + h), p(du, dv / 2, 16 + h), p(0, dv / 2, 16 + h)]))
    return o


def town_things(d, rng):
    o = []
    for k in range(10):  # paving stones of the street
        u, v = rng.uniform(0.15, 0.85), rng.uniform(0.15, 0.85); x, y = d(u, v)
        o.append('<ellipse cx="%s" cy="%s" rx="4" ry="2" fill="#bdb09a" opacity="0.5"/>' % (f(x), f(y)))
    o += temple(d, 0.12, 0.08, rng)
    o += house(d, 0.6, 0.08, 0.26, 0.18, 20, rng)
    x, y = d(0.48, 0.48); o.append(shadow(d, 0.48, 0.48, 12)); o += tree(x, y, rng, '#7a9a4a', 12, trunk='#6a5a40')  # an olive tree in the square
    o += house(d, 0.1, 0.56, 0.24, 0.2, 18, rng, '#f6eedf', '#b9502c')
    o += house(d, 0.62, 0.52, 0.22, 0.16, 24, rng, '#efe0c4', '#c8603a')
    o += house(d, 0.36, 0.74, 0.28, 0.16, 16, rng)
    for u, v in ((0.52, 0.36), (0.3, 0.46)):  # amphorae by the doors
        x, y = d(u, v); o.append('<ellipse cx="%s" cy="%s" rx="3" ry="4.5" fill="#b8622e"/><rect x="%s" y="%s" width="2.4" height="3" fill="#a0522a"/><ellipse cx="%s" cy="%s" rx="1" ry="2" fill="#d88a50"/>' % (
            f(x), f(y - 4), f(x - 1.2), f(y - 11), f(x - 1), f(y - 5)))
    return o


def things(land, rng):
    d = Iso(S / 2)
    body = land['things'](d, rng)
    return '\n'.join(['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 %d %d" width="%d" height="%d">' % (S, S, S, S)] + body + ['</svg>'])


# ---------- the top's own detail (on the ground picture, under the things)

def furrows(col, n=9):
    def draw(d, rng):
        o = []
        for k in range(n):
            u = 0.06 + k * 0.105 + 0.03; a, b = d(u, -0.05), d(u, 1.05)
            o.append('<path d="M%s %sL%s %s" stroke="%s" stroke-width="4" opacity="0.55"/>' % (f(a[0]), f(a[1]), f(b[0]), f(b[1]), col))
        return o
    return draw
def grass_top(d, rng): return blades(d, rng, 50, ['#6aa83a', '#4f8f2c', '#86bf4a'], (3, 5), 1)
def pebbles(col):
    def draw(d, rng):
        o = []
        for _ in range(26):
            u, v, r = rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(1.2, 2.8); x, y = d(u, v)
            o.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>' % (f(x), f(y), f(r * 1.4), f(r * 0.8), col))
        return o
    return draw
def paving(d, rng):
    o = []
    for k in range(1, 8):
        a, b = d(k / 8, 0), d(k / 8, 1); o.append('<path d="M%s %sL%s %s" stroke="#cdbfa4" stroke-width="1"/>' % (f(a[0]), f(a[1]), f(b[0]), f(b[1])))
        a, b = d(0, k / 8), d(1, k / 8); o.append('<path d="M%s %sL%s %s" stroke="#cdbfa4" stroke-width="1"/>' % (f(a[0]), f(a[1]), f(b[0]), f(b[1])))
    return o
def vine_rows(d, rng):
    o = []
    for k in range(4):
        v = 0.14 + k * 0.24; o.append('<polygon points="%s" fill="#8a5a34" opacity="0.5"/>' % pts([d(0.04, v - 0.04), d(0.96, v - 0.04), d(0.96, v + 0.05), d(0.04, v + 0.05)]))
    return o + grass_top(d, rng)[:20]


GRASS_LAYERS = [(0, 0.5, '#a06a3c'), (0.5, 0.68, '#7e4f2c'), (0.68, 1, '#93603a')]
LANDS = {
    'wheat': dict(top='#e2b956', lip='#c99b3c', soil='#a06a3c', stone='#7a6a58', layers=GRASS_LAYERS,
                  patches=[('#d4a84a', 18, (8, 22)), ('#ecc96a', 14, (6, 18))], top_detail=furrows('#b88a35'), things=wheat_things),
    'pomegranate': dict(top='#79b445', lip='#5f9a34', soil='#a06a3c', stone='#7a6a58', layers=GRASS_LAYERS,
                        patches=[('#6aa33c', 22, (8, 24)), ('#8cc455', 16, (6, 18))], top_detail=grass_top, things=pomegranate_things),
    'vineyard': dict(top='#9aa850', lip='#6f9a34', soil='#9a5f38', stone='#7a6a58', layers=[(0, 0.5, '#9a5f38'), (0.5, 0.68, '#7a4428'), (0.68, 1, '#8c5634')],
                     patches=[('#8a9a46', 18, (8, 22)), ('#b0b060', 12, (6, 16))], top_detail=vine_rows, things=vineyard_things),
    'forest': dict(top='#4f8a34', lip='#3f7a2a', soil='#8a5a34', stone='#6e6458', layers=[(0, 0.5, '#8a5a34'), (0.5, 0.68, '#6a4226'), (0.68, 1, '#7c4e2e')],
                   patches=[('#447c2e', 22, (8, 24)), ('#5e9a3e', 14, (6, 18)), ('#6b5a30', 6, (4, 10))], top_detail=grass_top, things=forest_things),
    'mountain': dict(top='#a29c90', lip='#8a8478', soil='#8a8478', stone='#5e5850', stones=12, layers=[(0, 0.4, '#9a948a'), (0.4, 0.58, '#7a746a'), (0.58, 0.78, '#8e887e'), (0.78, 1, '#6e685e')],
                     patches=[('#958f84', 20, (8, 22)), ('#b2ac9f', 14, (6, 18)), ('#8a9a6a', 6, (4, 10))], top_detail=pebbles('#7e786e'), things=mountain_things),
    'town': dict(top='#e3d6ba', lip='#8aa848', soil='#a06a3c', stone='#7a6a58', layers=GRASS_LAYERS,
                 patches=[('#d8caa8', 12, (8, 20))], top_detail=paving, things=town_things),
}

if __name__ == '__main__':
    for name, land in LANDS.items():
        (OUT / (name + '-ground.svg')).write_text(ground(land, random.Random(name + 'g')))
        (OUT / (name + '-things.svg')).write_text(things(land, random.Random(name + 't')))
    print('made', len(LANDS) * 2, 'pictures in', OUT)
