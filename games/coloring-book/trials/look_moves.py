# His 26 Nov wet-paint cases, with every brush (one column each), a steady and a shaking hand: bands that start on wet paint (no arcs where they start),
# an orange swirl scribbled over wet red and yellow (it must move and mix them), long diagonal bands laid over each other (no zigzags or scallops).
# Usage: look_moves.py [shake]; picture: moves.png in the system temp folder.
import math, pathlib, random, sys, tempfile
from PIL import Image
from playwright.sync_api import sync_playwright
H = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir()); SHAKE = 'shake' in sys.argv[1:]; random.seed(5)
BRUSHES = ['round', 'flat', 'filbert', 'fan', 'rigger']
def hand(pts, step=4):  # a hand at an even 500 px a second; a shaking hand wobbles a few px
    o = []; ms = 0
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(b[0]-a[0], b[1]-a[1]) / step))
        for k in range(n):
            j = random.uniform(-3, 3) if SHAKE else 0
            o.append((a[0]+(b[0]-a[0])*k/n + j, a[1]+(b[1]-a[1])*k/n + j, ms)); ms += step / 0.5
    return o + [(pts[-1][0], pts[-1][1], ms)]
def swirl(cx, cy, r, turns):
    n = int(turns * 40); return [(cx + r*(0.6 + 0.4*math.sin(k*0.13))*math.cos(k*2*math.pi/40), cy + r*0.8*(0.6 + 0.4*math.sin(k*0.13))*math.sin(k*2*math.pi/40)) for k in range(n)]
def scene(q, br, x0):  # a column 190 px wide
    S = lambda c, s, pts: q.evaluate("([c,s,b,p])=>__trial.stroke(c,s,b,p)", [c, s, br, pts])
    sz = 8 if br == 'rigger' else 22; w = 10 if br == 'rigger' else 40
    for k, c in enumerate([4, 5, 6]): S(c, sz, hand([(x0 + 10 + k*30, 40 + k*w*0.8), (x0 + 180, 40 + k*w*0.8)]))           # bands, each starting on the last one's wet paint
    S(4, sz, hand([(x0 + 10, 230), (x0 + 180, 230)])); S(5, sz, hand([(x0 + 10, 230 + w), (x0 + 180, 230 + w)]))         # wet red and yellow
    S(4, sz, hand(swirl(x0 + 95, 250, 55, 4))[::1]); S(5, sz, hand(swirl(x0 + 95, 250, 40, 3)))                         # scribbled over them, round and round
    for k, c in enumerate([4, 5, 5, 6]): S(c, sz, hand([(x0 + 10, 560 + k*w*0.5), (x0 + 180, 420 + k*w*0.5)]))        # long diagonal bands over each other
with sync_playwright() as p:
    b = p.chromium.launch(); q = b.new_page(viewport={'width': 1360, 'height': 800}); errs = []; q.on('pageerror', lambda e: errs.append(str(e)))
    q.goto('file://' + str(H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
    for k, br in enumerate(BRUSHES): scene(q, br, k * 198)
    q.wait_for_timeout(200); f = OUT / ('moves-shake.png' if SHAKE else 'moves.png'); q.screenshot(path=str(f), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 700}); b.close()
    print(errs or f)
