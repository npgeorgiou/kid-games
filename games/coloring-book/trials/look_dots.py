# His dot-and-line and spiral cases (25 Nov evening), painted through the trial's own stroke code at size L; pictures to the system temp folder.
# dots.png: each brush pressed once (a dot) and one straight line. loads.png: each brush's line (rows) with a third, two thirds and a full bucket (left to right). press.png: the same with a slow, a usual and a fast hand. spiral.png: one long square spiral with the flat brush until it is empty.
import pathlib, tempfile
from PIL import Image
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir())
def poly(ps, d=4):
    o = []
    for (x0, y0), (x1, y1) in zip(ps, ps[1:]):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / d)); o += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    return o + [ps[-1]]
def page(b, strokes):
    q = b.new_page(viewport={'width': 1360, 'height': 800}); errs = []; q.on('pageerror', lambda e: errs.append(str(e)))
    q.goto('file://' + str(HERE / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
    for br, pts, *lv in strokes: q.evaluate("([b,p,l])=>__trial.stroke(2,40,b,p,l)", [br, pts, lv[0] if lv else 3])
    q.wait_for_timeout(200); f = OUT / 'p.png'; q.screenshot(path=str(f), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); q.close()
    if errs: print(errs)
    return Image.open(f).copy()
def sheet(name, strokes):
    with sync_playwright() as p:
        b = p.chromium.launch(); a = page(b, strokes); b.close()
    a.save(OUT / name); print(OUT / name)
BR = ['round', 'flat', 'filbert', 'fan', 'rigger']
sheet('dots.png', [x for k, br in enumerate(BR) for x in ((br, [(110 + k * 190, 130)]), (br, poly([(110 + k * 190, 260), (110 + k * 190, 660)])))])
sheet('loads.png', [(br, poly([(50 + j * 330, 80 + k * 145), (310 + j * 330, 80 + k * 145)]), j + 1) for k, br in enumerate(BR) for j in range(3)])
def timed(pts, v): return [(x, y, k * 4 / v * 1000) for k, (x, y) in enumerate(pts)]  # points 4 px apart, a hand at v px a second
sheet('press.png', [(br, timed(poly([(50 + j * 330, 80 + k * 145), (310 + j * 330, 80 + k * 145)]), v)) for k, br in enumerate(BR) for j, v in enumerate([150, 550, 2500])])
sq = []; m = 60
while m < 330: sq += [(m, m), (1000 - m, m), (1000 - m, 760 - m), (m + 70, 760 - m)]; m += 100
sheet('spiral.png', [('flat', poly(sq))])
