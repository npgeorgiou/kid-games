#!/usr/bin/env python3
# Brush previews (owner 21 Nov: real results, painted as he would, on each canvas): python3 tools/previews.py
# One page: for each canvas, one stroke per brush painted straight through the game's stroke code (no finger-speed waiting),
# the wet paint run dry, each stroke kept as lib/previews/<canvas>.json (JPEG data URLs). Takes about a minute (most of it the watercolour running, on the test browser's slow processor drawing).
import sys, time, json, base64, io, pathlib, subprocess
here = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(here / "tools"))
from flows import page, tap
from playwright.sync_api import sync_playwright
from PIL import Image
subprocess.run([sys.executable, str(here / "build.py")], check=True, stdout=subprocess.DEVNULL)
W, H = 400, 200
with sync_playwright() as p:
    b = p.chromium.launch(); q = page(b, '1600x1000')
    for cv in ('wc', 'smooth', 'cotton'):
        if cv != 'wc': tap(q, 'canvas'); tap(q, 'canvas-' + cv); time.sleep(0.5)
        shapes = q.evaluate("()=>Object.fromEntries(Object.entries(__cb.shapes).map(([t,v])=>[t,v.length]))")
        jobs = [(t, i, 0) for t in ('acrylic', 'water', 'crayon', 'marker', 'simple') for i in range(shapes[t])] + [('simple', i, 1) for i in range(shapes['simple'])]
        for k, (t, i, blur) in enumerate(jobs):
            x, y = (k % 4) * W, (k // 4) * H
            q.evaluate("([t,i,blur,pts])=>{const s=__cb.st;s.tool=t;s.shape[t]=i;s.soft=blur;s.size=1;s.color=6;s.load=3;__cb.paint(pts)}",
                       [t, i, blur, [[x + 60, y + 130], [x + 140, y + 80], [x + 230, y + 110], [x + 340, y + 70]]])
        q.evaluate("()=>{__cb.fast(6); __cb.age(120)}")
        out = {}
        for k, (t, i, blur) in enumerate(jobs):
            x, y = (k % 4) * W, (k // 4) * H
            u = q.evaluate("(a)=>__cb.cell(...a)", [x, y, W, H])
            im = Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGB').resize((W // 2, H // 2), Image.LANCZOS)
            buf = io.BytesIO(); im.save(buf, 'JPEG', quality=82)
            out['%s-%d%s' % (t, i, '-blur' if blur else '')] = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
        (here / "lib" / "previews" / (cv + ".json")).write_text(json.dumps(out)); print(cv, len(out), 'previews')
    b.close()
