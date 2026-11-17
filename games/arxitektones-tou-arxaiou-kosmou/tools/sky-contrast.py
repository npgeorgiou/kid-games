#!/usr/bin/env python3
"""How well each site's building stands out from each day sky, measured on the real game picture.

For every site: the quick build, drawn under each candidate sky, with textures on and off. Sky pixels are the ones that
change when the sky changes; the building is what stays and touches the ground. Along the building's edge, each sky pixel
is compared with the nearest building pixel a few pixels inside the edge (past the dark outline of the pieces), with
CIEDE2000, the colour difference that matches what people see (the older CIE76 overrates differences in blues and violets).
Score = the average along the whole edge. Usage: python3 tools/sky-contrast.py   (run tools/harness.py once first: it writes /tmp/tb.html)
"""
import io, json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.color import rgb2lab, deltaE_ciede2000
from playwright.sync_api import sync_playwright

CANDIDATES = ["air", "aug", "bah", "day", "dro", "ken", "sno", "ora", "sen"]

def shot(pg, w, h):
    return np.asarray(Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": 0, "width": w, "height": h}))).convert("RGB")).astype(float)

res = {}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 800}); pg.goto("file:///tmp/tb.html"); pg.wait_for_timeout(1500)
    keys = pg.evaluate("()=>__tb.LEVELS.map(L=>L.key)")
    for i, k in enumerate(keys):
        pg.evaluate("""(i)=>{const T=__tb;T.progress.done={};T.cueReset();T.cueMem().seq['first-site']='done';T.cueMem().ever['welcome-first']=1;
          T.startLevel(i);T.onEnterSite(i);T.newScene();T.render();T.setTab(true);T.startAutoBuild();for(let k=0;k<1500;k++)T.stepPhysics(1/60,8);T.setTab(false);T.newScene();}""", i)
        w, gy = pg.evaluate("()=>[Math.floor(__tb.buildingWidthPx), Math.floor(__tb.worldToScreen(__tb.LEVEL_X0,0).y)]")
        for tex in (False, True):
            pg.evaluate("(t)=>__tb.setTextures(t)", tex)
            imgs = {}
            for s in CANDIDATES + ["mon"]:
                pg.evaluate("(s)=>{__tb.setSky(s);__tb.render();}", s); imgs[s] = shot(pg, w, gy)
            same = np.all(np.abs(imgs["mon"] - imgs["air"]) < 3, axis=2)  # unchanged by the sky: the building (and buttons)
            lab, n = ndimage.label(same); bottom = set(lab[-2][lab[-2] > 0])
            build = np.isin(lab, list(bottom))  # what touches the ground
            inside = ndimage.binary_erosion(build, iterations=4)
            sky = ~same
            ring = sky & (ndimage.distance_transform_edt(~build) <= 5)
            _, (iy, ix) = ndimage.distance_transform_edt(~inside, return_indices=True)
            ry, rx = np.nonzero(ring)
            for s in CANDIDATES:
                a = rgb2lab((imgs[s][ry, rx] / 255.0)[None])[0]; c = rgb2lab((imgs[s][iy[ry, rx], ix[ry, rx]] / 255.0)[None])[0]
                d = deltaE_ciede2000(a, c)
                res.setdefault(k, {}).setdefault(s, []).append(float(d.mean()))
    b.close()
score = {k: {s: sum(v) / len(v) for s, v in d.items()} for k, d in res.items()}
print("site       " + " ".join(s.rjust(5) for s in CANDIDATES))
for k, d in score.items(): print(k.ljust(10) + " " + " ".join("%5.1f" % d[s] for s in CANDIDATES))
json.dump(score, open("/tmp/sky-contrast.json", "w"))
