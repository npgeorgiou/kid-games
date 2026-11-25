# Every acrylic and impasto reference picture of his (owner-shots/2026-11-25-acrylic-1,2,4 and impasto-1,3) beside the trial painting a similar scene; one sheet to the system temp folder (refs.png).
# Blue strokes and impasto-2 are in look_reference.py. Strokes carry times: a hand at an even pace that flicks off at the end.
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
 'acrylic-1': (False, [(1,'round',40,hand([(80,120),(300,90)])),(2,'filbert',40,curve(500,180,70,2.5,5.5)),(5,'flat',40,hand([(650,90),(900,120)])),(0,'round',40,curve(820,320,60,0,4)),(5,'flat',64,hand([(80,330),(260,360)])),(2,'round',40,curve(420,420,70,3,6.5)),(1,'filbert',40,hand([(120,600),(380,560)])),(5,'round',30,hand([(600,500),(640,700)])),(0,'round',64,hand([(800,560),(900,600)]))]),
 'acrylic-2': (False, [(c,'flat',40,hand([(80,520-k*50),(940,260-k*50)])) for k,c in enumerate([2,2,6,5,5,4])]),
 'acrylic-4': (False, [(c,'flat',64,hand([(100,80+k*80),(900,90+k*80)])) for k,c in enumerate([0,0,1,1,2,2,3,3])]),
 'impasto-1': (True, [(random.choice([1,2,3,5,6,0]),'flat',random.choice([22,40]),hand([(x,y),(x+random.uniform(60,140),y+random.uniform(-25,25))])) for x,y in [(random.uniform(40,880),random.uniform(40,720)) for _ in range(70)]]),
 'impasto-3': (True, [(random.choice([4,5,5,2,6,3]),'flat',40,hand([(x,y),(x,y+70)])) for x in range(60,960,75) for y in range(40,700,85)]),
}
out = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (imp, strokes) in scenes.items():
        q = b.new_page(viewport={'width': 1360, 'height': 800}); q.goto('file://' + str(H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready')
        for c, br, s, pts in strokes: q.evaluate("([c,s,b,i,p])=>__trial.stroke(c,s,b,i,p)", [c, s, br, imp, pts])
        q.wait_for_timeout(150); q.screenshot(path=str(OUT / 's.png'), clip={'x': 12, 'y': 12, 'width': 1000, 'height': 760}); q.close()
        a = Image.open(str(OUT / 's.png')).convert('RGB').resize((500, 380)); r = Image.open(next(R.glob(f'2026-11-25-{name}.*'))).convert('RGB'); r = r.resize((int(380 * r.width / r.height), 380))
        c = Image.new('RGB', (510 + r.width, 380), 'white'); c.paste(a, (0, 0)); c.paste(r, (510, 0)); out.append(c)
    b.close()
W = max(c.width for c in out); s = Image.new('RGB', (W, 380 * len(out) + 6 * len(out)), 'white')
for k, c in enumerate(out): s.paste(c, (0, k * 386))
s.save(OUT / 'refs.png'); print(OUT / 'refs.png')
