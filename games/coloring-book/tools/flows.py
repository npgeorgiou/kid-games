# Flow tests: what the owner does, in the running game: real page, real mouse drags at a real rate, real touches.
# Each flow starts from a fresh page with no saved pictures and prints PASS or FAIL, its name, and what was seen.
import time, json
from playwright.sync_api import sync_playwright

def page(b):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True)
    q = ctx.new_page(); q.goto('file:///tmp/cb.html')
    q.evaluate("()=>new Promise(r=>{const d=indexedDB.deleteDatabase('coloring-book'); d.onsuccess=d.onerror=d.onblocked=()=>r()})")
    q.reload(); q.wait_for_function("()=>window.__cb&&__cb.ready"); return q

def tap(q, bid):
    p = q.evaluate("(id)=>__cb.btn(id)", bid); q.mouse.click(p[0], p[1]); time.sleep(0.05)

def drag(q, pts, step=6):  # paper points; moves at about 60 per second like a finger
    s = [q.evaluate("([x,y])=>__cb.screenOf(x,y)", p) for p in pts]
    q.mouse.move(*s[0]); q.mouse.down()
    for (x0, y0), (x1, y1) in zip(s, s[1:]):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step))
        for i in range(1, n + 1): q.mouse.move(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1)

def shown(q, x, y): return q.evaluate("([x,y])=>__cb.shown(x,y)", [x, y])
def lum(c): return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
def report(ok, name, seen): print('%-4s %-48s %s' % ('PASS' if ok else 'FAIL', name, seen))

def f_oil_mix(q):
    tap(q, 'tool-oil'); tap(q, 'size-2'); tap(q, 'color-4'); drag(q, [(200, 300), (700, 300)])
    tap(q, 'color-7'); drag(q, [(450, 120), (450, 520)])
    mid, before, after = shown(q, 450, 300), shown(q, 450, 160), shown(q, 450, 380)
    gr = lambda c: c[1] - c[2]
    report(mid[1] > mid[0] and mid[1] > mid[2] and gr(after) > gr(before) + 15, 'oil: blue over yellow is green and carried on',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_oil_thick_dry(q):
    tap(q, 'tool-oil'); tap(q, 'size-1'); tap(q, 'color-2'); drag(q, [(100, 500), (1500, 500)])
    h = q.evaluate("()=>{const T=__cb,a=[150,700,1400].map(x=>{let s=0;for(let j=-10;j<=10;j++)s+=T.Ht[(500+j)*T.CW+x];return +(s/21).toFixed(3)});return a}")
    prof = [round(lum(shown(q, 700, 500 + j))) for j in range(-14, 15, 2)]
    spread = max(prof[2:-2]) - min(prof[2:-2])
    report(h[0] > 0.08 and h[2] < h[0] * 0.8 and spread > 12, 'oil: thick, streaky, runs dry', 'thickness start/mid/end %s, brightness across %s' % (h, prof))

def f_water(q):
    tap(q, 'tool-water'); tap(q, 'size-1'); tap(q, 'color-7'); drag(q, [(300, 400), (900, 400)])
    time.sleep(1.6)
    wet = q.evaluate("()=>__cb.water.active")
    prof = [round(lum(shown(q, 600, 400 + j))) for j in range(0, 40, 2)]
    paper = round(lum(shown(q, 600, 600))); centre = prof[0]; darkest = min(prof)
    tap(q, 'color-7'); drag(q, [(300, 400), (900, 400)]); time.sleep(1.6)
    twice = round(lum(shown(q, 600, 400)))
    report(not wet and centre < paper - 30 and darkest < centre - 4 and prof.index(darkest) > 3 and twice < centre - 15,
           'watercolour: dries, darker rim, layers darken', 'paper %d, centre %d, across %s, second layer %d' % (paper, centre, prof, twice))

def f_crayon(q):
    tap(q, 'tool-crayon'); tap(q, 'size-2'); tap(q, 'color-2'); drag(q, [(300, 300), (900, 300)])
    r = q.evaluate("()=>{let n=0,p=0;for(let x=400;x<800;x+=3)for(let y=296;y<=304;y++){const c=__cb.shown(x,y);n++;if(c[1]>200)p++;}return p/n}")
    report(0.1 < r < 0.6, 'crayon: specks of paper stay', 'paper share in the stroke %.2f' % r)

def f_soft(q):
    tap(q, 'tool-simple'); tap(q, 'size-2'); tap(q, 'color-1')
    def edge(y):
        prof = [lum(shown(q, 600, y + j)) for j in range(0, 60)]
        lo, hi = min(prof), max(prof)
        return sum(1 for v in prof if lo + 0.1 * (hi - lo) < v < lo + 0.9 * (hi - lo))
    tap(q, 'soft-0'); drag(q, [(300, 250), (900, 250)]); tap(q, 'soft-2'); drag(q, [(300, 600), (900, 600)])
    hard, soft = edge(250), edge(600)
    report(hard <= 4 and soft >= hard + 10, 'simple brush: softness changes the edge', 'edge width sharp %d, fuzzy %d' % (hard, soft))

def f_undo(q):
    tap(q, 'tool-oil'); tap(q, 'color-2'); drag(q, [(200, 200), (600, 300)])
    before = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    tap(q, 'color-7'); drag(q, [(300, 100), (300, 500)]); tap(q, 'undo')
    after = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    time.sleep(0.1); look = shown(q, 300, 450)
    report(abs(before - after) < 1e-3 and lum(look) > 200, 'undo takes back the last stroke exactly', 'difference %.6f, where it was %s' % (before - after, look))

def f_two_fingers(q):
    tap(q, 'tool-simple'); tap(q, 'color-1')
    cdp = q.context.new_cdp_session(q)
    a = [q.evaluate("([x,y])=>__cb.screenOf(x,y)", p) for p in [(300, 300), (800, 700)]]
    t = lambda typ, pts: cdp.send('Input.dispatchTouchEvent', {'type': typ, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in pts]})
    t('touchStart', [(0, a[0])]); time.sleep(0.03)
    t('touchStart', [(0, a[0]), (1, a[1])])
    for k in range(1, 20):
        t('touchMove', [(0, (a[0][0] + k * 8, a[0][1])), (1, (a[1][0] + k * 8, a[1][1]))]); time.sleep(0.016)
    t('touchEnd', []); time.sleep(0.15)
    first, second = shown(q, 350, 300), shown(q, 850, 700)
    report(lum(first) < 80 and lum(second) > 200, 'touch: first finger paints, second does nothing', 'under first %s, under second %s' % (first, second))

def f_stickers(q):
    tap(q, 'tool-sticker'); p = q.evaluate("()=>__cb.btn('sticker-star')"); s = q.evaluate("()=>__cb.screenOf(800,500)")
    q.mouse.move(*p); q.mouse.down()
    for i in range(1, 21): q.mouse.move(p[0] + (s[0] - p[0]) * i / 20, p[1] + (s[1] - p[1]) * i / 20); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1); placed = q.evaluate("()=>__cb.stickers.map(s=>[s.kind,Math.round(s.x),Math.round(s.y)])")
    drag(q, [(800, 500), (800, 1100)]); gone = q.evaluate("()=>__cb.stickers.length")
    report(len(placed) == 1 and abs(placed[0][1] - 800) < 5 and gone == 0, 'stickers: drag on, drag off', 'placed %s, after dragging off %d' % (placed, gone))

def f_gallery(q):
    tap(q, 'tool-oil'); tap(q, 'color-5'); drag(q, [(200, 500), (1400, 500)])
    painted = shown(q, 400, 500); tap(q, 'new'); time.sleep(0.5)
    blank = shown(q, 400, 500); n = q.evaluate("()=>__cb.count()")
    tap(q, 'gallery'); time.sleep(0.4)
    cards = q.evaluate("()=>[...document.querySelectorAll('#gal .card')].map(c=>{const r=c.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2,c.classList.contains('cur')]})")
    old = [c for c in cards if not c[2]]
    if old: q.mouse.click(old[0][0], old[0][1]); time.sleep(0.6)
    back = shown(q, 400, 500)
    q.reload(); q.wait_for_function("()=>__cb.ready"); time.sleep(0.2); reopened = shown(q, 400, 500)
    close = lambda a, b: max(abs(x - y) for x, y in zip(a, b)) <= 6
    report(n >= 1 and lum(blank) > 200 and old and close(back, painted) and close(reopened, painted), 'gallery: new keeps the old, open it again',
           'painted %s, new page %s, kept %d, opened again %s, after reload %s' % (painted, blank, n, back, reopened))

def f_speed(q):  # what he would feel: time spent painting per frame with the biggest oil brush moving fast
    tap(q, 'tool-oil'); tap(q, 'size-2'); tap(q, 'color-3')
    q.evaluate("()=>{window.__ft=[];let l=performance.now();const f=(t)=>{__ft.push(t-l);l=t;if(__ft.length<400)requestAnimationFrame(f)};requestAnimationFrame(f)}")
    drag(q, [(100, 200), (1500, 300), (100, 400), (1500, 500), (100, 600)], step=25)
    ft = q.evaluate("()=>__ft.slice(5).sort((a,b)=>a-b)"); p95 = ft[int(len(ft) * 0.95)]
    report(p95 < 34, 'speed: big oil brush, fast strokes (this machine)', '95%% of frames under %.0f ms' % p95)

FLOWS = {'oil_mix': f_oil_mix, 'oil_thick_dry': f_oil_thick_dry, 'water': f_water, 'crayon': f_crayon, 'soft': f_soft, 'undo': f_undo,
         'two_fingers': f_two_fingers, 'stickers': f_stickers, 'gallery': f_gallery, 'speed': f_speed}

def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in (names or FLOWS):
            q = page(b)
            try: FLOWS[n](q)
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0])
            q.context.close()
        b.close()
