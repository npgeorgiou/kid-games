# His wet-paint cases (25 Nov 21:51): a yellow ring grazing a wet blue blob (green only where it touched), green across a wet blue blob (green on top), dark blue over fresh light blue (must show). Picture: wet.png in the temp folder.
import pathlib, math, sys
from PIL import Image
from playwright.sync_api import sync_playwright
import tempfile
H = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir())
def blob(cx, cy, r): return [(cx + r * (t / 160) * math.cos(t * 0.35), cy + r * (t / 160) * math.sin(t * 0.35)) for t in range(160)]
def line(a, b, n=60): return [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]
with sync_playwright() as p:
    b = p.chromium.launch(); shots = []
    for _ in [0]:
        q = b.new_page(viewport={'width': 1360, 'height': 800}); errs = []; q.on('pageerror', lambda e: errs.append(str(e)))
        q.goto('file://' + str(H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
        S = lambda c, s, br, pts: q.evaluate("([c,s,b,p])=>__trial.stroke(c,s,b,p)", [c, s, br, pts])
        S(2, 40, 'round', blob(180, 200, 90))
        ring = [(180 + 128 * math.cos(a / 30), 200 + 128 * math.sin(a / 30)) for a in range(-90, 100)]; S(5, 40, 'flat', ring)   # yellow ring, grazing the blob's edge
        S(1, 40, 'round', blob(560, 200, 90)); S(6, 30, 'round', line((400, 60), (760, 380)))                       # green across wet blue
        for x in range(380, 900, 60): S(2, 40, 'flat', line((x, 440), (x + 10, 740)))                              # fresh light blue
        for x in (420, 560, 700): S(0, 30, 'flat', line((x, 450), (x, 730)))                                        # dark blue over it
        S(0, 30, 'flat', line((80, 450), (80, 730)))                                                                # dark blue on paper
        q.wait_for_timeout(200); f = str(OUT / 'p.png'); q.screenshot(path=f, clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); shots.append(f); print(errs)
    b.close()
Image.open(shots[0]).save(OUT / 'wet.png'); print(OUT / 'wet.png')
