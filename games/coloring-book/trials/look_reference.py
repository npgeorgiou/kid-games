# His blue reference scene (owner-shots/2026-11-25-acrylic-blue-strokes.jpg) repainted through the trial's own stroke code with one brush; picture beside his, to the system temp folder.
# Usage: look_reference.py <brush> [1]; with 1: impasto, his yellow and blue impasto picture (owner-shots/2026-11-25-impasto-2.jpg) instead.
import math, pathlib, random, sys, tempfile
from PIL import Image
from playwright.sync_api import sync_playwright
HERE = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir()); BRUSH = sys.argv[1]; IMP = len(sys.argv) > 2 and sys.argv[2] == '1'
random.seed(3)
with sync_playwright() as p:
    b = p.chromium.launch(); q = b.new_page(viewport={'width': 1360, 'height': 800}); errs = []; q.on('pageerror', lambda e: errs.append(str(e)))
    q.goto('file://' + str(HERE / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
    if IMP:  # wide wavy diagonal strokes, yellow and blue in turn, each over the wet one before
        for k in range(9):
            c = 5 if k % 2 == 0 else 1; ox = 150 + k * 70
            q.evaluate("([c,s,b,i,p])=>__trial.stroke(c,s,b,i,p)", [c, 40, BRUSH, True, [(ox + i * 5, 620 - i * 4 + 40 * math.sin(i / 14 + k)) for i in range(90)]])
    for k in range(0 if IMP else 46):
        x = random.uniform(130, 870); c = random.choice([0, 0, 1, 1, 1, 1, 2, 2, 2, 3]); s = random.choice([22, 30, 40])
        y0 = random.uniform(60, 200); y1 = random.uniform(450, 700); ph = random.uniform(0, 6); n = int((y1 - y0) / 5)
        q.evaluate("([c,s,b,i,p])=>__trial.stroke(c,s,b,i,p)", [c, s, BRUSH, IMP, [(x + 5 * math.sin(i / 12 + ph), y0 + i * 5) for i in range(n + 1)]])
    q.wait_for_timeout(200); q.screenshot(path=str(OUT / 't.png'), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); b.close()
    if errs: print(errs)
a = Image.open(OUT / 't.png').convert('RGB'); r = Image.open(HERE.parent / 'owner-shots' / ('2026-11-25-impasto-2.jpg' if IMP else '2026-11-25-acrylic-blue-strokes.jpg')).convert('RGB'); r = r.resize((760 * r.width // r.height, 760)).crop((0, 0, 760, 760)) if IMP else r.resize((760, 760))
c = Image.new('RGB', (1760, 760), 'white'); c.paste(a, (0, 0)); c.paste(r, (1000, 0)); c.save(OUT / 'cmp.png')
z = Image.new('RGB', (1200, 450), 'white'); z.paste(a.crop((300, 200, 600, 425)).resize((600, 450)), (0, 0)); z.paste(r.crop((230, 200, 455, 370)).resize((600, 450)), (600, 0)); z.save(OUT / 'zoom.png'); print(OUT / 'cmp.png')
