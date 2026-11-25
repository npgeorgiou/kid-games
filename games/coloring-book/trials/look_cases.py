# His cases (25 Nov), painted straight through the trial's own stroke code with one brush; picture to the system temp folder.
# Usage: look_cases.py <brush> ; cases: one long spiral until the brush is empty, straight lines and curves, yellow and blue zigzags with a stroke through both,
# yellow scribbled into a wet blue blob, strokes over dry (left) and over wet (right) paint, wet-into-wet bands dark to light.
import math, pathlib, sys, tempfile
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir()); BRUSH = sys.argv[1]
def line(a, b):
    n = max(1, int(math.hypot(b[0]-a[0], b[1]-a[1]) / 4)); return [(a[0]+(b[0]-a[0])*i/n, a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
def poly(ps):
    o = []
    for a, b in zip(ps, ps[1:]): o += line(a, b)[:-1]
    return o + [ps[-1]]
def zig(x0, x1, y0, y1, n): return poly([(x0+(x1-x0)*k/n, y0 if k % 2 == 0 else y1) for k in range(n+1)])
def scene(q):
    S = lambda c, s, pts: q.evaluate("([c,s,b,p])=>__trial.stroke(c,s,b,p)", [c, s, BRUSH, pts])
    W = lambda sec: q.evaluate("(s)=>__trial.wait(s)", sec)
    sz = 22
    sp = []; a = 0.0; r = 150.0
    while r > 15: sp.append((170 + r*math.cos(a), 170 + r*math.sin(a))); a += 0.05; r -= 0.45
    S(6, sz, sp)                                                          # spiral until empty
    S(4, sz, line((360, 40), (640, 40))); S(4, sz, line((370, 80), (370, 300))); S(4, sz, line((420, 300), (640, 90)))
    S(4, sz, [(430 + 90*math.cos(t/30*math.pi), 200 + 50*math.sin(t/30*math.pi)) for t in range(0, 50)])  # curve
    S(4, sz, [(470 + k*3, 120 + 40*math.sin(k/9)) for k in range(55)])     # wave
    S(5, sz, zig(690, 860, 30, 300, 6)); S(1, sz, zig(800, 980, 30, 300, 6)); S(1, int(sz*1.3), line((690, 270), (980, 60)))  # zigzags, a stroke through both
    bl = [(160 + 110*math.cos(t*0.21)*(0.4 + 0.6*abs(math.sin(t*0.05))), 560 + 90*math.sin(t*0.27)) for t in range(160)]
    S(1, 40, bl); S(5, sz, [(160 + 70*math.cos(t*0.33), 560 + 55*math.sin(t*0.41)) for t in range(200)])  # yellow scribbled into the wet blue blob
    for x in (370, 420, 470): S(2 if x == 420 else 1, sz, line((x, 380), (x, 740)))
    W(60)
    for x in (540, 590, 640): S(2 if x == 590 else 1, sz, line((x, 380), (x, 740)))  # the right group is wet, the left one dry
    S(0, sz, line((350, 470), (660, 470))); S(3, sz, line((350, 620), (660, 640)))
    for k, c in enumerate([0, 0, 1, 1, 2, 2, 3, 3]): S(c, sz, zig(700, 980, 390 + k*44, 400 + k*44, 1) + zig(980, 700, 405 + k*44, 415 + k*44, 1))  # wet bands, dark to light
    W(1)
with sync_playwright() as p:
    b = p.chromium.launch(); q = b.new_page(viewport={'width': 1360, 'height': 800}); errs = []; q.on('pageerror', lambda e: errs.append(str(e)))
    q.goto('file://' + str(HERE / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready'); scene(q); q.wait_for_timeout(200)
    f = OUT / f'cases-{BRUSH}.png'; q.screenshot(path=str(f), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); b.close()
    print(errs or f)
