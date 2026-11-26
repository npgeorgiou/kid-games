# His cases painted with a hand's mouse shake (25 Nov 22:01): yellow across a wet dark-blue blob; white and dark strokes over fresh light blue. No zigzags may show. Picture: shake.png in the temp folder.
import pathlib, math, random
from PIL import Image
from playwright.sync_api import sync_playwright
import tempfile
H = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir()); random.seed(5)
def hand(a, b, n=70):
    o = []; w = 0
    for k in range(n + 1):
        w += random.uniform(-1.5, 1.5); w *= 0.9
        x = a[0] + (b[0] - a[0]) * k / n; y = a[1] + (b[1] - a[1]) * k / n; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        o.append((x - dy / L * w * 3 + random.uniform(-1, 1), y + dx / L * w * 3 + random.uniform(-1, 1)))
    return o
def blob(cx, cy, r): return [(cx + r * (t / 160) * math.cos(t * 0.35) + random.uniform(-1, 1), cy + r * (t / 160) * math.sin(t * 0.35)) for t in range(160)]
with sync_playwright() as p:
    b = p.chromium.launch(); shots = []
    for _ in [0]:
        q = b.new_page(viewport={'width': 1360, 'height': 800}); q.goto('file://' + str(H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
        S = lambda c, s, br, pts: q.evaluate("([c,s,b,p])=>__trial.stroke(c,s,b,p)", [c, s, br, pts])
        S(0, 64, 'round', blob(240, 220, 110)); S(5, 40, 'flat', hand((60, 90), (480, 330)))
        for x in range(560, 960, 70): S(2, 40, 'flat', hand((x, 60), (x + 5, 700)))
        S(3, 30, 'round', hand((600, 180), (680, 650))); S(3, 30, 'round', hand((700, 120), (705, 600)))
        S(0, 30, 'round', hand((780, 250), (790, 700))); S(0, 30, 'round', hand((860, 280), (870, 700)))
        q.wait_for_timeout(200); f = str(OUT / 'p.png'); q.screenshot(path=f, clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); shots.append(f)
    b.close()
Image.open(shots[0]).save(OUT / 'shake.png'); print(OUT / 'shake.png')
