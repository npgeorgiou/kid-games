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

def hold(q, bid, sec):
    p = q.evaluate("(id)=>__cb.btn(id)", bid); q.mouse.move(p[0], p[1]); q.mouse.down(); time.sleep(sec); q.mouse.up(); time.sleep(0.05)

def drag(q, pts, step=6):  # paper points; moves at about 60 per second like a finger
    s = [q.evaluate("([x,y])=>__cb.screenOf(x,y)", p) for p in pts]
    q.mouse.move(*s[0]); q.mouse.down()
    for (x0, y0), (x1, y1) in zip(s, s[1:]):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step))
        for i in range(1, n + 1): q.mouse.move(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1)

def shown(q, x, y): return q.evaluate("([x,y])=>__cb.shown(x,y)", [x, y])
def row(q, y): return q.evaluate("(y)=>{const o=[];for(let x=320;x<1080;x+=4)o.push(__cb.shown(x,y));return o}", y)
def lum(c): return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
def report(ok, name, seen): print('%-4s %-48s %s' % ('PASS' if ok else 'FAIL', name, seen))

def f_oil_mix(q):
    tap(q, 'tool-oil'); tap(q, 'size-2'); hold(q, 'color-4', 1.1); drag(q, [(200, 300), (700, 300)])
    hold(q, 'color-7', 1.1); drag(q, [(450, 120), (450, 520)])
    mid, before, after = shown(q, 450, 300), shown(q, 450, 160), shown(q, 450, 380)
    gr = lambda c: c[1] - c[2]
    report(mid[1] > mid[0] and mid[1] > mid[2] and gr(after) > gr(before) + 15, 'oil: blue over yellow is green and carried on',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_oil_thick_dry(q):
    tap(q, 'tool-oil'); tap(q, 'size-1'); hold(q, 'color-2', 1.1); drag(q, [(100, 500), (1500, 500)])
    h = q.evaluate("()=>{const T=__cb,a=[150,700,1400].map(x=>{let s=0;for(let j=-10;j<=10;j++)s+=T.Ht[(500+j)*T.CW+x];return +(s/21).toFixed(3)});return a}")
    prof = [round(lum(shown(q, 700, 500 + j))) for j in range(-14, 15, 2)]
    spread = max(prof[2:-2]) - min(prof[2:-2])
    report(h[0] > 0.08 and h[2] < h[0] * 0.8 and spread > 12, 'oil: thick, streaky, runs dry', 'thickness start/mid/end %s, brightness across %s' % (h, prof))

def wait_dry(q, most=60):  # watercolour stays wet a few seconds (owner 21 Nov: wet and dry); wait until it is dry
    t = time.time()
    while q.evaluate("()=>__cb.water.active") and time.time() - t < most: time.sleep(0.2)
    return round(time.time() - t, 1)

def f_water(q):
    tap(q, 'tool-water'); tap(q, 'size-1'); hold(q, 'color-7', 1.1); drag(q, [(300, 400), (900, 400)])
    wait_dry(q)
    wet = q.evaluate("()=>__cb.water.active")
    prof = [round(lum(shown(q, 600, 400 + j))) for j in range(0, 40, 2)]
    paper = round(lum(shown(q, 600, 600))); centre = prof[0]; darkest = min(prof)
    hold(q, 'color-7', 1.1); drag(q, [(300, 400), (900, 400)]); wait_dry(q)
    twice = round(lum(shown(q, 600, 400)))
    report(not wet and centre < paper - 30 and darkest < centre - 4 and prof.index(darkest) > 3 and twice < centre - 15,
           'watercolour: dries, darker rim, layers darken', 'paper %d, centre %d, across %s, second layer %d' % (paper, centre, prof, twice))

def f_crayon(q):
    tap(q, 'tool-crayon'); tap(q, 'size-2'); hold(q, 'color-2', 1.1); drag(q, [(300, 300), (900, 300)])
    r = q.evaluate("()=>{let n=0,p=0;for(let x=400;x<800;x+=3)for(let y=296;y<=304;y++){const c=__cb.shown(x,y);n++;if(c[1]>200)p++;}return p/n}")
    report(0.1 < r < 0.6, 'crayon: specks of paper stay', 'paper share in the stroke %.2f' % r)

def f_soft(q):
    tap(q, 'tool-simple'); tap(q, 'size-3'); hold(q, 'color-1', 1.1)  # owner 21 Nov: 5 sizes; size-3 (48) is nearest the old biggest (36)
    def edge(y):
        prof = [lum(shown(q, 600, y + j)) for j in range(0, 60)]
        lo, hi = min(prof), max(prof)
        return sum(1 for v in prof if lo + 0.1 * (hi - lo) < v < lo + 0.9 * (hi - lo))
    tap(q, 'soft-0'); drag(q, [(300, 250), (900, 250)]); tap(q, 'soft-2'); drag(q, [(300, 600), (900, 600)])
    hard, soft = edge(250), edge(600)
    report(hard <= 4 and soft >= hard + 10, 'simple brush: softness changes the edge', 'edge width sharp %d, fuzzy %d' % (hard, soft))

def f_undo(q):
    tap(q, 'tool-oil'); hold(q, 'color-2', 1.1); drag(q, [(200, 200), (600, 300)])
    before = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    hold(q, 'color-7', 1.1); drag(q, [(300, 100), (300, 500)]); tap(q, 'undo')
    after = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    time.sleep(0.1); look = shown(q, 300, 450)
    report(abs(before - after) < 1e-3 and lum(look) > 200, 'undo takes back the last stroke exactly', 'difference %.6f, where it was %s' % (before - after, look))

def f_two_fingers(q):
    tap(q, 'tool-simple'); hold(q, 'color-1', 1.1)
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
    tap(q, 'tool-oil'); hold(q, 'color-5', 1.1); drag(q, [(200, 500), (1400, 500)])
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
    tap(q, 'tool-oil'); tap(q, 'size-2'); hold(q, 'color-3', 1.1)
    q.evaluate("()=>{window.__ft=[];let l=performance.now();const f=(t)=>{__ft.push(t-l);l=t;if(__ft.length<400)requestAnimationFrame(f)};requestAnimationFrame(f)}")
    drag(q, [(100, 200), (1500, 300), (100, 400), (1500, 500), (100, 600)], step=25)
    ft = q.evaluate("()=>__ft.slice(5).sort((a,b)=>a-b)"); p95 = ft[int(len(ft) * 0.95)]
    report(p95 < 34, 'speed: big oil brush, fast strokes (this machine)', '95%% of frames under %.0f ms' % p95)

def f_ctrl_z(q):  # owner 21 Nov: Ctrl+Z takes back; Ctrl+X does not
    tap(q, 'tool-oil'); hold(q, 'color-2', 1.1); drag(q, [(200, 300), (900, 300)]); painted = shown(q, 500, 300)
    q.keyboard.press('Control+x'); time.sleep(0.1); after_x = shown(q, 500, 300)
    q.keyboard.press('Control+z'); time.sleep(0.1); look = shown(q, 500, 300)
    report(lum(painted) < 150 and after_x == painted and lum(look) > 200, 'Ctrl+Z takes back the last stroke, Ctrl+X does nothing', 'painted %s, after Ctrl+X %s, after Ctrl+Z %s' % (painted, after_x, look))

def f_load(q):  # owner 21 Nov: a longer hold on a colour takes more paint, one more dot each half second
    tap(q, 'tool-oil'); levels = []
    for sec in (0.1, 0.6, 1.1): hold(q, 'color-7', sec); levels.append(q.evaluate("()=>__cb.st.load"))
    hold(q, 'color-7', 0.1); drag(q, [(200, 300), (1400, 300)]); little = [lum(c) for c in row(q, 300)]
    hold(q, 'color-7', 1.1); drag(q, [(200, 600), (1400, 600)]); full = [lum(c) for c in row(q, 600)]
    paper = lambda r: sum(1 for v in r if v > 200)
    report(levels == [1, 2, 3] and paper(little) > paper(full) + 10, 'holding a colour longer takes more paint',
           'dots after 0.1/0.6/1.1 s %s, paper showing along the stroke with little paint %d, with full %d' % (levels, paper(little), paper(full)))

def f_delete(q):  # owner 21 Nov: delete the open picture, so a child cannot do it by accident (as the architects game's restart)
    tap(q, 'tool-oil'); hold(q, 'color-2', 1.1); drag(q, [(200, 300), (900, 300)]); q.evaluate("()=>__cb.save()"); time.sleep(0.3)
    n0 = q.evaluate("()=>__cb.count()"); tap(q, 'delete'); time.sleep(0.3); n1 = q.evaluate("()=>__cb.count()"); still = shown(q, 500, 300)
    time.sleep(6.3); tap(q, 'delete'); time.sleep(0.3); n2 = q.evaluate("()=>__cb.count()")
    tap(q, 'delete'); time.sleep(0.1); tap(q, 'delete'); time.sleep(0.6); n3 = q.evaluate("()=>__cb.count()"); look = shown(q, 500, 300)
    report(n0 == 1 and n1 == 1 and lum(still) < 150 and n2 == 1 and n3 == 0 and lum(look) > 200, 'delete: one press only warns, a second press soon after deletes',
           'pictures before %d, after one press %d, after a press 6 s later %d, after two quick presses %d, page now %s' % (n0, n1, n2, n3, look))

def f_acrylic(q):  # acrylic dries fast: soon after, the brush no longer smears it
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); hold(q, 'color-4', 1.1); drag(q, [(200, 300), (700, 300)])
    q.evaluate("()=>__cb.age(30)"); hold(q, 'color-7', 1.1); drag(q, [(450, 120), (450, 520)]); after = shown(q, 450, 380)
    tap(q, 'tool-oil'); hold(q, 'color-4', 1.1); drag(q, [(800, 300), (1300, 300)])
    q.evaluate("()=>__cb.age(30)"); hold(q, 'color-7', 1.1); drag(q, [(1050, 120), (1050, 520)]); oil_after = shown(q, 1050, 380)
    gr = lambda c: c[1] - c[2]
    report(gr(oil_after) > gr(after) + 15, 'acrylic dries faster than oil', 'blue after crossing 30 s old acrylic %s, 30 s old oil %s' % (after, oil_after))

def f_shapes(q):  # owner 21 Nov: brush shapes; a flat brush makes a mark as wide as the brush with straight sides
    tap(q, 'tool-simple'); tap(q, 'size-3'); hold(q, 'color-1', 1.1); tap(q, 'shape-0'); drag(q, [(300, 200), (300, 200.5)])
    tap(q, 'shape-1'); drag(q, [(700, 200), (700, 200.5)])
    w = lambda x: sum(1 for dy in range(-60, 61, 2) if lum(shown(q, x + dy, 200)) < 120)
    h = lambda x: sum(1 for dy in range(-60, 61, 2) if lum(shown(q, x, 200 + dy)) < 120)
    report(abs(w(300) - h(300)) <= 2 and h(700) > 2 * w(700), 'brush shapes: round dab is round, flat dab is a bar across the stroke',
           'round %dx%d, flat %dx%d (across x along, 2 px steps)' % (h(300), w(300), h(700), w(700)))

def f_canvas(q):  # owner 21 Nov: other canvases; linen shows a woven surface
    tap(q, 'canvas'); tap(q, 'canvas-linen'); time.sleep(0.5)
    r = [lum(shown(q, 400 + x, 400)) for x in range(0, 40)]
    report(q.evaluate("()=>__cb.st.canvas") == 'linen' and max(r) - min(r) > 6, 'canvas: picking linen gives a new page on linen', 'canvas %s, light across 40 px %d..%d' % (q.evaluate("()=>__cb.st.canvas"), min(r), max(r)))

def f_oil_dry(q):  # owner 21 Nov (plan): wet paint mixes, dry paint stays put; new paint sits on top of dry paint
    tap(q, 'tool-oil'); tap(q, 'size-2'); hold(q, 'color-4', 1.1); drag(q, [(200, 300), (700, 300)])
    q.evaluate("()=>__cb.age(300)")  # five minutes pass
    hold(q, 'color-7', 1.1); drag(q, [(450, 120), (450, 520)])
    mid, before, after = shown(q, 450, 300), shown(q, 450, 160), shown(q, 450, 380)
    gr = lambda c: c[1] - c[2]
    report(mid[2] > mid[1] and abs(gr(after) - gr(before)) < 10, 'oil: dry paint is not smeared, new paint covers it',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_flat(q):  # with the paper flat the paint does not run down
    tap(q, 'tool-water'); tap(q, 'size-2'); hold(q, 'color-7', 1.1)
    drag(q, [(300, 300), (1100, 300)]); drag(q, [(300, 310), (1100, 310)]); took = wait_dry(q, 30)
    paper = min(lum(c) for c in row(q, 800)); below = min(lum(c) for c in row(q, 400))
    report(below > paper - 8, 'flat paper: paint stays where it was put', 'darkest paper %d, darkest 60 below %d, waited %ss' % (paper, below, took))

FLOWS = {'oil_mix': f_oil_mix, 'oil_thick_dry': f_oil_thick_dry, 'water': f_water, 'crayon': f_crayon, 'soft': f_soft, 'undo': f_undo,
         'two_fingers': f_two_fingers, 'stickers': f_stickers, 'gallery': f_gallery, 'speed': f_speed,
         'ctrl_z': f_ctrl_z, 'oil_dry': f_oil_dry, 'flat': f_flat,
         'load': f_load, 'delete': f_delete, 'acrylic': f_acrylic, 'shapes': f_shapes, 'canvas': f_canvas}

def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in (names or FLOWS):
            q = page(b)
            try: FLOWS[n](q)
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0])
            q.context.close()
        b.close()
