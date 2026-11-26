# Every acrylic reference picture of his (owner-shots/2026-11-25-acrylic-*) beside the trial painting a similar scene; one sheet to the system temp folder (refs.png).
# Strokes carry times: a hand at an even pace that flicks off at the end.
import pathlib, math, random
from PIL import Image
from playwright.sync_api import sync_playwright
import tempfile
H = pathlib.Path(__file__).resolve().parent; R = H.parent / 'owner-shots'; OUT = pathlib.Path(tempfile.gettempdir()); random.seed(2)
def hand(pts, n=4):
    o = []
    for a, b in zip(pts, pts[1:]):
        L = max(1, int(math.hypot(b[0]-a[0], b[1]-a[1]) / n)); o += [(a[0]+(b[0]-a[0])*k/L + random.uniform(-.7,.7), a[1]+(b[1]-a[1])*k/L + random.uniform(-.7,.7)) for k in range(L)]
    o = o + [pts[-1]]; ms = 0; r = []
    for k, (x, y) in enumerate(o):
        f = k / max(1, len(o) - 1); ms += 8 if f < 0.75 else 8 - 6.5 * (f - 0.75) / 0.25; r.append((x, y, ms))  # a hand slows nothing, then flicks off at the end
    return r
def curve(cx, cy, r, a0, a1, n=None):
    n = n or max(8, int(abs(a1 - a0) * r / 4))
    return [(cx + r*math.cos(a0+(a1-a0)*k/n), cy + r*math.sin(a0+(a1-a0)*k/n)) for k in range(n+1)]
scenes = {
 'acrylic-1': [(1,'round',40,hand([(80,120),(300,90)])),(2,'filbert',40,curve(500,180,70,2.5,5.5)),(5,'flat',40,hand([(650,90),(900,120)])),(0,'round',40,curve(820,320,60,0,4)),(5,'flat',64,hand([(80,330),(260,360)])),(2,'round',40,curve(420,420,70,3,6.5)),(1,'filbert',40,hand([(120,600),(380,560)])),(5,'round',30,hand([(600,500),(640,700)])),(0,'round',64,hand([(800,560),(900,600)])),(3,'flat',22,hand([(100,112),(290,96)]),2),(1,'round',30,curve(420,420,60,3.2,6.2),2),(3,'filbert',22,hand([(820,560),(890,590)]),1),(2,'flat',30,hand([(700,95),(860,112)]),2)],
 'acrylic-2': [(c,'flat',40,hand([(80,520-k*50),(940,260-k*50)])) for k,c in enumerate([2,2,6,5,5,4])],
 'acrylic-4': [(c,'flat',64,hand([(100,70+k*85),(500,62+k*85),(900,75+k*85),(500,100+k*85),(110,95+k*85),(500,92+k*85),(900,105+k*85)])) for k,c in enumerate([0,0,1,1,2,2,3,3])],  # as he paints a gradient: each band brushed back and forth into the wet band above
# blue-strokes: his picture's paint is about a quarter white or pale, measured: the colours are chosen in about those shares
 'acrylic-blue-strokes': [(random.choice([0,0,1,1,1,2,2,3,3,3]),'flat',random.choice([22,30,40]),hand([(x,random.uniform(60,200)),(x+random.uniform(-15,15),random.uniform(450,700))])) for x in [random.uniform(130,870) for _ in range(46)]],
}
TUNE = {}  # numbers of the trial's paint (its P) to try instead of its own, for tune.py
def palette(name, k=4):  # his picture's own paint colours, dark to light (k-means in Lab over the paint), for the scenes that use them
    import numpy as np
    from skimage import color
    from scipy.cluster.vq import kmeans2
    a = np.asarray(ref(name).resize((200, 200))) / 255.0; lab = color.rgb2lab(a).reshape(-1, 3); bg = np.median(lab[:400], 0); px = lab[np.sqrt(((lab - bg) ** 2).sum(1)) > 10]
    c, lab_k = kmeans2(px, k, seed=1, minit='++'); ch = np.hypot(px[:, 1], px[:, 2])  # each colour from the more colourful half of its group (plain averages come out dull: WARNINGS)
    c = np.array([px[(lab_k == j) & (ch >= np.median(ch[lab_k == j]))].mean(0) for j in range(k)]); c = c[np.argsort(c[:, 0])]
    return [[int(v) for v in (np.clip(color.lab2rgb(c[None, j:j + 1])[0, 0], 0, 1) * 255)] for j in range(k)]
OWN = ('acrylic-4', 'acrylic-blue-strokes')  # scenes painted in his picture's own colours (palette): the colour numbers there are places in it
def paint():  # every scene painted by the trial, full size: {name: picture}
    pics = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, strokes in scenes.items():
            q = b.new_page(viewport={'width': 1360, 'height': 800}); q.goto('file://' + str(H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
            if TUNE: q.evaluate("(t)=>Object.assign(__trial.P, t)", TUNE)
            pal = palette(name) if name in OWN else None
            for c, br, s, pts, *lv in strokes: c = pal[c] if pal else c; q.evaluate("([c,s,b,p,l])=>__trial.stroke(c,s,b,p,l)", [c, s, br, pts, lv[0] if lv else 3])
            q.wait_for_timeout(150); q.screenshot(path=str(OUT / 's.png'), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); q.close()
            pics[name] = Image.open(str(OUT / 's.png')).convert('RGB')
        b.close()
    return pics
PAINT_ONLY = {'acrylic-2': (0, 0.7, 0.55, 1)}  # the part of his picture with paint only (acrylic-2 also shows the brush), as shares of its width and height
def ref(name):
    im = Image.open(next(R.glob(f'2026-11-25-{name}.*'))).convert('RGB'); x0, y0, x1, y1 = PAINT_ONLY.get(name, (0, 0, 1, 1))
    return im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
if __name__ == '__main__':
    out = []
    for name, im in paint().items():
        a = im.resize((500, 380)); r = ref(name); r = r.resize((int(380 * r.width / r.height), 380))
        c = Image.new('RGB', (510 + r.width, 380), 'white'); c.paste(a, (0, 0)); c.paste(r, (510, 0)); out.append(c)
    W = max(c.width for c in out); s = Image.new('RGB', (W, 380 * len(out) + 6 * len(out)), 'white')
    for k, c in enumerate(out): s.paste(c, (0, k * 386))
    s.save(OUT / 'refs.png'); print(OUT / 'refs.png')
