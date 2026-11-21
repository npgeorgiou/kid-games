#!/usr/bin/env python3
# Brush previews (owner 21 Nov: real results, painted as he would, on each canvas): python3 tools/previews.py
# python3 tools/previews.py wc  -- one canvas; with no name it runs every canvas at once, in parallel (owner 21 Nov: be faster)
# Paints one stroke per brush on a fresh page for every canvas, lets it dry, and keeps each stroke as lib/previews/<canvas>.json (JPEG data URLs).
import sys, time, json, base64, io, pathlib, subprocess, shutil
here = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(here / "tools"))
from flows import page, tap, drag
from playwright.sync_api import sync_playwright
from PIL import Image
ALL = ('wc', 'smooth', 'cotton')
if len(sys.argv) < 2:
    subprocess.run([sys.executable, str(here / "build.py")], check=True, stdout=subprocess.DEVNULL); shutil.copy(here / "coloring-book.html", "/tmp/cb.html")
    for pr in [subprocess.Popen([sys.executable, __file__, cv]) for cv in ALL]: pr.wait()
    sys.exit()
CW, CH, W, H = 1600, 1000, 400, 200
with sync_playwright() as p:
    b = p.chromium.launch()
    for cv in sys.argv[1:]:
        q = page(b)
        if cv != 'wc': tap(q, 'canvas'); tap(q, 'canvas-' + cv); time.sleep(0.5)
        shapes = q.evaluate("()=>Object.fromEntries(Object.entries(__cb.shapes).map(([t,v])=>[t,v.length]))")
        jobs = [(t, i, 0) for t in ('acrylic', 'water', 'crayon', 'marker', 'simple') for i in range(shapes[t])] + [('simple', i, 1) for i in range(shapes['simple'])]
        cells = {}
        for k, (t, i, blur) in enumerate(jobs):
            x, y = (k % 4) * W, (k // 4) * H
            tap(q, 'tool-' + t); tap(q, 'size-1'); tap(q, ('blur-' if blur else 'shape-') + str(i)); tap(q, 'color-6')
            drag(q, [(x + 60, y + 130), (x + 140, y + 80), (x + 230, y + 110), (x + 340, y + 70)])
            cells[k] = (t, i, blur, x, y)
            if t == 'water': q.evaluate("()=>__cb.fast(20)")
        q.evaluate("()=>{__cb.fast(40); __cb.age(120)}"); time.sleep(1)
        out = {}
        for k, (t, i, blur, x, y) in cells.items():
            u = q.evaluate("(a)=>__cb.cell(...a)", [x, y, W, H])
            im = Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGB').resize((W // 2, H // 2), Image.LANCZOS)
            buf = io.BytesIO(); im.save(buf, 'JPEG', quality=82)
            out['%s-%d%s' % (t, i, '-blur' if blur else '')] = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
        (here / "lib" / "previews" / (cv + ".json")).write_text(json.dumps(out))
        print(cv, len(out), 'previews')
        q.context.close()
    b.close()
