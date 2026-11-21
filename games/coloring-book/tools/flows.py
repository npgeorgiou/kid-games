# Flow tests: what the owner does, in the running game: real page, real mouse drags at a real rate, real touches.
# Colours are picked by their place in the Basic palette: 0 white, 1 black, 2 red, 3 orange, 4 yellow, 5 green, 6 blue, 7 purple, 8 pink, 9 brown (owner 21 Nov: every palette 10 colours).
# Each flow starts from a fresh page with no saved pictures and prints PASS or FAIL, its name, and what was seen.
import time, json
from playwright.sync_api import sync_playwright

def page(b):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True)
    q = ctx.new_page(); q.goto('file:///tmp/cb.html')
    q.evaluate("()=>new Promise(r=>{const d=indexedDB.deleteDatabase('coloring-book'); d.onsuccess=d.onerror=d.onblocked=()=>r()})")
    q.reload(); q.wait_for_function("()=>window.__cb&&__cb.ready"); return q

def tap(q, bid):
    opener = {'size': 'size', 'shape': 'brush', 'blur': 'brush'}.get(bid.split('-')[0])  # owner 21 Nov: sizes and brushes are chosen in a popup
    if opener: p = q.evaluate("(id)=>__cb.btn(id)", opener); q.mouse.click(p[0], p[1]); time.sleep(0.1)
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
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); hold(q, 'color-4', 1.6); drag(q, [(200, 300), (700, 300)])
    hold(q, 'color-6', 1.6); drag(q, [(450, 120), (450, 520)])
    mid, before, after = shown(q, 450, 300), shown(q, 450, 160), shown(q, 450, 380)
    gr = lambda c: c[1] - c[2]
    report(mid[1] > mid[0] and mid[1] > mid[2] and gr(after) > gr(before) + 15, 'oil: blue over yellow is green and carried on',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_oil_thick_dry(q):
    tap(q, 'tool-acrylic'); tap(q, 'size-1'); hold(q, 'color-2', 1.6); drag(q, [(100, 500), (1500, 500)])
    h = q.evaluate("()=>{const T=__cb,a=[150,700,1400].map(x=>{let s=0;for(let j=-10;j<=10;j++)s+=T.Ht[(500+j)*T.CW+x];return +(s/21).toFixed(3)});return a}")
    prof = [round(lum(shown(q, 700, 500 + j))) for j in range(-14, 15, 2)]
    spread = max(prof[2:-2]) - min(prof[2:-2])
    report(h[0] > 0.08 and h[2] < h[0] * 0.8 and spread > 12, 'oil: thick, streaky, runs dry', 'thickness start/mid/end %s, brightness across %s' % (h, prof))

def wait_dry(q, most=60):  # watercolour stays wet a few seconds (owner 21 Nov: wet and dry); wait until it is dry
    t = time.time()
    while q.evaluate("()=>__cb.water.active") and time.time() - t < most: time.sleep(0.2)
    return round(time.time() - t, 1)

def f_water(q):
    tap(q, 'tool-water'); tap(q, 'size-1'); hold(q, 'color-6', 1.6); drag(q, [(300, 400), (900, 400)])
    wait_dry(q)
    wet = q.evaluate("()=>__cb.water.active")
    prof = [round(lum(shown(q, 600, 400 + j))) for j in range(0, 40, 2)]
    paper = round(lum(shown(q, 600, 600))); centre = prof[0]; darkest = min(prof)
    hold(q, 'color-6', 1.6); drag(q, [(300, 400), (900, 400)]); wait_dry(q)
    twice = round(lum(shown(q, 600, 400)))
    report(not wet and centre < paper - 30 and darkest < centre - 4 and prof.index(darkest) > 3 and twice < centre - 15,
           'watercolour: dries, darker rim, layers darken', 'paper %d, centre %d, across %s, second layer %d' % (paper, centre, prof, twice))

def f_crayon(q):
    tap(q, 'tool-crayon'); tap(q, 'size-2'); hold(q, 'color-2', 1.6); drag(q, [(300, 300), (900, 300)])
    r = q.evaluate("()=>{let n=0,p=0;for(let x=400;x<800;x+=3)for(let y=296;y<=304;y++){const c=__cb.shown(x,y);n++;if(c[1]>200)p++;}return p/n}")
    report(0.1 < r < 0.6, 'crayon: specks of paper stay', 'paper share in the stroke %.2f' % r)

def f_soft(q):
    tap(q, 'tool-simple'); tap(q, 'size-3'); hold(q, 'color-1', 1.6)  # owner 21 Nov: 5 sizes; size-3 (48) is nearest the old biggest (36)
    def edge(y):
        prof = [lum(shown(q, 600, y + j)) for j in range(0, 60)]
        lo, hi = min(prof), max(prof)
        return sum(1 for v in prof if lo + 0.1 * (hi - lo) < v < lo + 0.9 * (hi - lo))
    tap(q, 'shape-0'); drag(q, [(300, 250), (900, 250)]); tap(q, 'blur-0'); drag(q, [(300, 600), (900, 600)])  # owner 21 Nov: the blurred brushes are a second row
    hard, soft = edge(250), edge(600)
    report(hard <= 4 and soft >= hard + 10, 'simple brush: softness changes the edge', 'edge width sharp %d, fuzzy %d' % (hard, soft))

def f_undo(q):
    tap(q, 'tool-acrylic'); hold(q, 'color-2', 1.6); drag(q, [(200, 200), (600, 300)])
    before = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    hold(q, 'color-6', 1.6); drag(q, [(300, 100), (300, 500)]); tap(q, 'undo')
    after = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    time.sleep(0.1); look = shown(q, 300, 450)
    report(abs(before - after) < 1e-3 and lum(look) > 200, 'undo takes back the last stroke exactly', 'difference %.6f, where it was %s' % (before - after, look))

def f_two_fingers(q):
    tap(q, 'tool-simple'); hold(q, 'color-1', 1.6)
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
    tap(q, 'tool-acrylic'); hold(q, 'color-5', 1.6); drag(q, [(200, 500), (1400, 500)])
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
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); hold(q, 'color-3', 1.6)
    q.evaluate("()=>{window.__ft=[];let l=performance.now();const f=(t)=>{__ft.push(t-l);l=t;if(__ft.length<400)requestAnimationFrame(f)};requestAnimationFrame(f)}")
    drag(q, [(100, 200), (1500, 300), (100, 400), (1500, 500), (100, 600)], step=25)
    ft = q.evaluate("()=>__ft.slice(5).sort((a,b)=>a-b)"); p95 = ft[int(len(ft) * 0.95)]
    report(p95 < 34, 'speed: big oil brush, fast strokes (this machine)', '95%% of frames under %.0f ms' % p95)

def f_ctrl_z(q):  # owner 21 Nov: Ctrl+Z takes back; Ctrl+X does not
    tap(q, 'tool-acrylic'); hold(q, 'color-2', 1.6); drag(q, [(200, 300), (900, 300)]); painted = shown(q, 500, 300)
    q.keyboard.press('Control+x'); time.sleep(0.1); after_x = shown(q, 500, 300)
    q.keyboard.press('Control+z'); time.sleep(0.1); look = shown(q, 500, 300)
    report(lum(painted) < 150 and after_x == painted and lum(look) > 200, 'Ctrl+Z takes back the last stroke, Ctrl+X does nothing', 'painted %s, after Ctrl+X %s, after Ctrl+Z %s' % (painted, after_x, look))

def f_load(q):  # owner 21 Nov: a tap gives a full brush; holding goes round a third, two thirds, full, a third...; a third looks washed out from the start
    tap(q, 'tool-acrylic'); levels = []
    for sec in (0.05, 0.6, 1.1, 1.6, 2.1): hold(q, 'color-6', sec); levels.append(q.evaluate("()=>__cb.st.load"))
    hold(q, 'color-6', 0.6); drag(q, [(200, 300), (1400, 300)])
    hold(q, 'color-6', 0.05); drag(q, [(200, 600), (1400, 600)])
    little, full = lum(shown(q, 300, 300)), lum(shown(q, 300, 600))
    report(levels == [3, 1, 2, 3, 1] and little > full + 30, 'paint amount: a tap is full, holding goes round; little paint is washed out',
           'after a tap, then holding 0.6, 1.1, 1.6, 2.1 s: %s; brightness near the start with a third %d, full %d' % (levels, little, full))

def f_fixed_angle(q):  # owner 21 Nov: the flat brush does not turn by itself
    tap(q, 'tool-marker'); tap(q, 'shape-1'); tap(q, 'size-3'); hold(q, 'color-1', 0.05)
    drag(q, [(200, 300), (800, 300)]); drag(q, [(1200, 150), (1200, 750)])
    across_h = sum(1 for dy in range(-60, 61, 2) if lum(shown(q, 500, 300 + dy)) < 120) * 2
    across_v = sum(1 for dx in range(-60, 61, 2) if lum(shown(q, 1200 + dx, 450)) < 120) * 2
    report(abs(across_h - across_v) <= 6 and across_h < 85, 'flat brush keeps its angle whichever way it moves', 'stroke width moving across %d px, moving down %d px (brush 96 px)' % (across_h, across_v))

def f_marker_ends(q):  # owner 21 Nov: big marker brushes must not leave blurry ends
    tap(q, 'tool-marker'); tap(q, 'size-4'); hold(q, 'color-1', 0.05); drag(q, [(300, 400), (900, 400)])
    prof = [lum(shown(q, 900 + dx, 400)) for dx in range(40, 110)]
    soft = sum(1 for v in prof if 60 < v < 200)
    report(soft <= 4, 'marker: crisp end at the biggest size', 'pixels of soft edge at the end %d' % soft)

def f_guide_place(q):  # owner 21 Nov: the guide picture sits exactly on the paper
    r = q.evaluate("""()=>{const g=document.getElementById('guide'),p=document.getElementById('paper');g.classList.remove('hide');const a=g.getBoundingClientRect(),b=p.getBoundingClientRect();g.classList.add('hide');return [a.left-b.left,a.top-b.top,a.width-b.width,a.height-b.height]}""")
    report(all(abs(v) < 1 for v in r), 'guide picture lies exactly on the paper', 'offset and size difference %s' % r)

def f_esc(q):  # owner 21 Nov: Esc leaves other views
    tap(q, 'gallery'); time.sleep(0.4); shown_gal = q.evaluate("()=>!document.getElementById('gal').classList.contains('hide')")
    q.keyboard.press('Escape'); time.sleep(0.2); gone = q.evaluate("()=>document.getElementById('gal').classList.contains('hide')")
    report(shown_gal and gone, 'Esc closes the gallery', 'gallery open %s, closed after Esc %s' % (shown_gal, gone))

def f_guide_menu(q):  # owner 21 Nov: the guide picture can be changed without a new page
    pt = q.evaluate("()=>__cb.btn('guide')")
    with q.expect_file_chooser(timeout=8000) as fc: q.mouse.move(*pt); q.mouse.down(); q.mouse.up()
    fc.value.set_files('owner-shots/2026-11-21-guide-yellow-building.jpg'); time.sleep(2)
    tap(q, 'guide'); time.sleep(0.2); opts = [q.evaluate("(i)=>!!__cb.btn(i)", i) for i in ('guide-pick', 'guide-show', 'guide-remove')]
    tap(q, 'guide-remove'); time.sleep(0.2); gone = q.evaluate("()=>document.getElementById('guide').classList.contains('hide')")
    report(all(opts) and gone, 'guide picture: change, show or hide, remove', 'choices shown %s, removed %s' % (opts, gone))

def f_undo_all(q):  # owner 21 Nov: undo goes all the way back
    tap(q, 'tool-simple'); tap(q, 'size-4'); hold(q, 'color-1', 1.6); n = 24
    for k in range(n): drag(q, [(100, 60 + k * 37), (1500, 80 + k * 37)], step=40)
    dark = lum(shown(q, 800, 70))
    for k in range(n): q.keyboard.press('Control+z'); time.sleep(0.15)
    time.sleep(1.0); look = [lum(shown(q, 800, 70 + k * 37)) for k in range(0, n, 4)]
    report(dark < 80 and min(look) > 200, 'undo goes all the way back to the empty page', 'painted %d, after %d undos %s' % (dark, n, look))

def f_marker(q):  # owner 21 Nov: a marker; its ink is see-through, so crossing lines get darker
    tap(q, 'tool-marker'); tap(q, 'size-2'); hold(q, 'color-6', 1.6); drag(q, [(200, 300), (900, 300)]); drag(q, [(550, 100), (550, 500)])
    one, two = shown(q, 300, 300), shown(q, 550, 300)
    report(lum(two) < lum(one) - 15, 'marker: crossing lines get darker', 'one line %s, crossing %s' % (one, two))

def f_delete(q):  # owner 21 Nov: delete the open picture, so a child cannot do it by accident (as the architects game's restart)
    tap(q, 'tool-acrylic'); hold(q, 'color-2', 1.6); drag(q, [(200, 300), (900, 300)]); q.evaluate("()=>__cb.save()"); time.sleep(0.3)
    n0 = q.evaluate("()=>__cb.count()"); tap(q, 'delete'); time.sleep(0.3); n1 = q.evaluate("()=>__cb.count()"); still = shown(q, 500, 300)
    time.sleep(6.3); tap(q, 'delete'); time.sleep(0.3); n2 = q.evaluate("()=>__cb.count()")
    tap(q, 'delete'); time.sleep(0.1); tap(q, 'delete'); time.sleep(0.6); n3 = q.evaluate("()=>__cb.count()"); look = shown(q, 500, 300)
    report(n0 == 1 and n1 == 1 and lum(still) < 150 and n2 == 1 and n3 == 0 and lum(look) > 200, 'delete: one press only warns, a second press soon after deletes',
           'pictures before %d, after one press %d, after a press 6 s later %d, after two quick presses %d, page now %s' % (n0, n1, n2, n3, look))

def f_delete_elsewhere(q):  # owner 21 Nov: after the first delete press, touching anywhere else takes the warning back
    tap(q, 'tool-acrylic'); hold(q, 'color-2', 1.6); drag(q, [(200, 300), (900, 300)]); q.evaluate("()=>__cb.save()"); time.sleep(0.3)
    tap(q, 'delete'); q.mouse.click(4, 4); time.sleep(0.1); tap(q, 'delete'); time.sleep(0.6); n = q.evaluate("()=>__cb.count()")
    report(n == 1, 'delete: a touch elsewhere takes the warning back', 'pictures after press, touch elsewhere, press: %d' % n)

def f_shapes(q):  # owner 21 Nov: brush shapes; a flat brush is a bar, held at one diagonal angle (it does not turn with the stroke)
    tap(q, 'tool-marker'); tap(q, 'size-3'); hold(q, 'color-1', 1.6); tap(q, 'shape-0'); drag(q, [(300, 200), (300, 200.5)])
    tap(q, 'shape-1'); drag(q, [(700, 200), (700, 200.5)])
    line = lambda x, dx, dy: sum(1 for k in range(-60, 61, 2) if lum(shown(q, x + k * dx, 200 + k * dy)) < 120)
    rnd, bar, across = (line(300, 1, 0), line(300, 0, 1)), line(700, 0.707, -0.707), line(700, 0.707, 0.707)
    report(abs(rnd[0] - rnd[1]) <= 2 and bar > 2 * across, 'brush shapes: round dab is round, flat dab is a diagonal bar',
           'round %dx%d, flat along the diagonal %d, across it %d (2 px steps)' % (rnd[0], rnd[1], bar, across))

def f_canvas(q):  # owner 21 Nov: other canvases; the cotton canvas shows a woven surface (owner 21 Nov 17:26: linen removed)
    tap(q, 'canvas'); tap(q, 'canvas-cotton'); time.sleep(0.5)
    r = [lum(shown(q, 400 + x, 400)) for x in range(0, 40)]
    report(q.evaluate("()=>__cb.st.canvas") == 'cotton' and max(r) - min(r) > 6, 'canvas: picking cotton gives a new page on cotton', 'canvas %s, light across 40 px %d..%d' % (q.evaluate("()=>__cb.st.canvas"), min(r), max(r)))

def f_oil_dry(q):  # owner 21 Nov (plan): wet paint mixes, dry paint stays put; new paint sits on top of dry paint
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); hold(q, 'color-4', 1.6); drag(q, [(200, 300), (700, 300)])
    q.evaluate("()=>__cb.age(300)")  # five minutes pass
    hold(q, 'color-6', 1.6); drag(q, [(450, 120), (450, 520)])
    mid, before, after = shown(q, 450, 300), shown(q, 450, 160), shown(q, 450, 380)
    gr = lambda c: c[1] - c[2]
    report(mid[2] > mid[1] and abs(gr(after) - gr(before)) < 10, 'oil: dry paint is not smeared, new paint covers it',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_flat(q):  # with the paper flat the paint does not run down
    tap(q, 'tool-water'); tap(q, 'size-2'); hold(q, 'color-6', 1.6)
    drag(q, [(300, 300), (1100, 300)]); drag(q, [(300, 310), (1100, 310)]); took = wait_dry(q, 30)
    paper = min(lum(c) for c in row(q, 800)); below = min(lum(c) for c in row(q, 400))
    report(below > paper - 8, 'flat paper: paint stays where it was put', 'darkest paper %d, darkest 60 below %d, waited %ss' % (paper, below, took))

FLOWS = {'oil_mix': f_oil_mix, 'oil_thick_dry': f_oil_thick_dry, 'water': f_water, 'crayon': f_crayon, 'soft': f_soft, 'undo': f_undo,
         'two_fingers': f_two_fingers, 'stickers': f_stickers, 'gallery': f_gallery, 'speed': f_speed,
         'ctrl_z': f_ctrl_z, 'oil_dry': f_oil_dry, 'flat': f_flat,
         'load': f_load, 'esc': f_esc, 'guide_menu': f_guide_menu, 'fixed_angle': f_fixed_angle, 'marker_ends': f_marker_ends, 'guide_place': f_guide_place, 'undo_all': f_undo_all, 'marker': f_marker, 'delete': f_delete, 'delete_elsewhere': f_delete_elsewhere, 'shapes': f_shapes, 'canvas': f_canvas}

def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in (names or FLOWS):
            q = page(b)
            try: FLOWS[n](q)
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0])
            q.context.close()
        b.close()

def f_crayon_levels(q):  # owner 21 Nov: the bucket levels are how hard the crayon presses; the lighter ones must still paint clearly
    tap(q, 'tool-crayon'); tap(q, 'size-2'); out = []
    for lv, y in ((1, 250), (2, 450), (3, 650)):
        hold(q, 'color-6', 0.6 + 0.5 * (lv - 1)) if lv < 3 else tap(q, 'color-6')
        drag(q, [(300, y), (900, y)])
        out.append(q.evaluate("(y)=>{let n=0,p=0;for(let x=400;x<800;x+=3)for(let k=y-4;k<=y+4;k++){const c=__cb.shown(x,k);n++;if(c[0]>200)p++;}return 1-p/n}", y))
    report(0.3 < out[0] < out[1] < out[2], 'crayon: a third, two thirds, full press cover more and more', 'covered %s' % ['%.2f' % v for v in out])

def f_crayon_blend(q):  # owner 21 Nov: crayons blend: a second colour pressed over the first mixes with it
    tap(q, 'tool-crayon'); tap(q, 'size-2'); tap(q, 'color-4'); drag(q, [(300, 300), (900, 300)])
    a = q.evaluate("()=>__cb.shown(600,300)"); tap(q, 'color-6'); drag(q, [(300, 300), (900, 300)])
    b = q.evaluate("()=>{const s=[0,0,0];let n=0;for(let x=500;x<700;x+=2){const c=__cb.shown(x,300);if(c[0]<235){s[0]+=c[0];s[1]+=c[1];s[2]+=c[2];n++;}}return s.map(v=>v/n)}")
    report(b[1] > b[2] and b[0] < 200, 'crayon: blue over yellow blends green', 'yellow %s, both %s' % (a, [round(v) for v in b]))
FLOWS.update({'crayon_levels': f_crayon_levels, 'crayon_blend': f_crayon_blend})

def f_water_speed(q):  # owner 21 Nov: watercolour laggy, more so with more paint on the page: frame time follows the wet paint, not the box around it
    tap(q, 'tool-water'); tap(q, 'size-2'); tap(q, 'color-6')
    ft = "()=>new Promise(res=>{const o=[];let l=performance.now();const f=(t)=>{o.push(t-l);l=t;if(o.length<12)requestAnimationFrame(f);else res(o.slice(2).sort((a,b)=>a-b)[5])};requestAnimationFrame(f)})"
    drag(q, [(150, 150), (400, 150)], step=30); one = q.evaluate(ft)
    drag(q, [(1200, 850), (1450, 850)], step=30); two = q.evaluate(ft)
    report(two < one * 2.6, 'watercolour: two far wet spots cost about twice one', 'frame %.0f ms with one, %.0f ms with two (this machine)' % (one, two))
FLOWS['water_speed'] = f_water_speed

def f_crayon_back_forth(q):  # owner 21 Nov 17:26: going back and forth over the same line keeps adding colour all along it, not only at its ends (papers 1 and 3)
    tap(q, 'tool-crayon'); tap(q, 'size-2'); tap(q, 'color-6')
    pts = [(300, 400), (900, 400)] * 3
    drag(q, pts[:2]); one = q.evaluate("()=>{let n=0,p=0;for(let x=500;x<700;x+=3)for(let y=396;y<=404;y++){n++;if(__cb.shown(x,y)[0]>200)p++;}return 1-p/n}")
    drag(q, pts)
    more = q.evaluate("()=>{let n=0,p=0;for(let x=500;x<700;x+=3)for(let y=396;y<=404;y++){n++;if(__cb.shown(x,y)[0]>200)p++;}return 1-p/n}")
    report(more > one + 0.08, 'crayon: back and forth adds colour in the middle', 'covered in the middle: one pass %.2f, then four more %.2f' % (one, more))

def f_crayon_bend(q):  # owner 21 Nov 17:26: a bend does not paint thicker than the straight part
    tap(q, 'tool-crayon'); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-6')
    drag(q, [(300, 300), (700, 300), (700, 700)])
    cov = "([x0,y0,x1,y1])=>{let n=0,p=0;for(let x=x0;x<x1;x+=2)for(let y=y0;y<y1;y+=2){n++;if(__cb.shown(x,y)[0]>200)p++;}return 1-p/n}"
    straight = q.evaluate(cov, [450, 290, 550, 310]); corner = q.evaluate(cov, [670, 290, 690, 310])
    report(corner < straight + 0.12, 'crayon: the bend is not denser than the straight part', 'covered straight %.2f, inside the bend %.2f' % (straight, corner))
FLOWS.update({'crayon_back_forth': f_crayon_back_forth, 'crayon_bend': f_crayon_bend})

def f_picker(q):  # owner 21 Nov 17:26: a colour picker next to the palette: tap it, tap the painting, paint with that colour
    tap(q, 'tool-simple'); tap(q, 'size-2'); tap(q, 'color-2'); drag(q, [(300, 300), (600, 300)])
    tap(q, 'color-6'); tap(q, 'pick'); s = q.evaluate("([x,y])=>__cb.screenOf(x,y)", [450, 300]); q.mouse.click(*s); time.sleep(0.1)
    drag(q, [(300, 600), (600, 600)]); a, b = shown(q, 450, 300), shown(q, 450, 600)
    report(max(abs(a[i] - b[i]) for i in range(3)) < 12, 'colour picker: the picked red paints red', 'picked from %s, painted %s' % (a, b))

def f_keep_amount(q):  # owner 21 Nov 17:26: with a paint amount chosen, choosing another colour keeps it
    hold(q, 'color-2', 0.6); lv = q.evaluate("()=>__cb.st.load"); tap(q, 'color-6')
    report(lv == 1 and q.evaluate("()=>__cb.st.load") == 1, 'another colour keeps the paint amount', 'a third chosen (%s), after another colour %s' % (lv, q.evaluate("()=>__cb.st.load")))

def f_simple_over(q):  # owner 21 Nov 17:26: the simple brush lays its colour over what is there by opacity; a soft edge never lightens the colour under it
    tap(q, 'tool-simple'); tap(q, 'size-3'); tap(q, 'color-6'); drag(q, [(200, 400), (1000, 400)])
    under = shown(q, 600, 400); tap(q, 'blur-0'); tap(q, 'color-4'); drag(q, [(600, 100), (600, 700)])
    edge = [shown(q, 600 + dx, 400) for dx in range(30, 80, 5)]
    report(all(lum(e) >= lum(under) - 6 and e[2] <= under[2] + 6 for e in edge), 'simple brush: a soft yellow edge over blue only adds yellow', 'blue %s, across the edge %s' % (under, edge[::3]))
FLOWS.update({'picker': f_picker, 'keep_amount': f_keep_amount, 'simple_over': f_simple_over})

def f_water_no_hitch(q):  # owner 21 Nov 18:29: after a few strokes on dry paper, new strokes lag and show late: no frame may hang while he paints on (the undo room filling up)
    tap(q, 'tool-simple'); tap(q, 'size-4'); tap(q, 'color-6')
    for y in (100, 300, 500, 700, 900): drag(q, [(50, y), (1550, y)], step=80)
    for c in ('color-2', 'color-4'):
        tap(q, c)
        for y in (100, 300, 500, 700, 900): drag(q, [(50, y), (1550, y)], step=80)
    time.sleep(2); tap(q, 'tool-water'); tap(q, 'size-3'); free = q.evaluate("()=>__cb.freeTiles")  # a moment of rest, as between his strokes
    q.evaluate("()=>{window.__gaps=[];let l=performance.now();const f=(t)=>{__gaps.push(t-l);l=t;if(__gaps.length<40)requestAnimationFrame(f)};requestAnimationFrame(f)}")
    drag(q, [(400, 200), (1200, 200)], step=30); time.sleep(1)
    g = sorted(q.evaluate("()=>__gaps.slice(2)")); med = g[len(g) // 2]
    report(g[-1] < 3 * med + 50 and free >= 400, 'painting never waits for undo room: a whole page is free before a stroke', 'longest frame %.0f ms, usual %.0f ms (this machine), free undo room before %s' % (g[-1], med, free))
FLOWS['water_no_hitch'] = f_water_no_hitch

def f_simple_soft_keeps(q):  # owner 21 Nov 18:29: the soft simple brush damages lines it painted before; a new soft line only adds colour, never takes any away
    tap(q, 'tool-simple'); tap(q, 'blur-0'); tap(q, 'size-3'); tap(q, 'color-6')
    drag(q, [(200, 300), (1000, 300)])
    ys = range(240, 365, 5); before = [lum(shown(q, 700, y)) for y in ys]
    drag(q, [(200, 380), (1000, 380)]); drag(q, [(200, 250), (1000, 250)])
    after = [lum(shown(q, 700, y)) for y in ys]
    lost = [(y, round(b), round(a)) for y, b, a in zip(ys, before, after) if a > b + 4]
    report(not lost, 'simple soft brush: new lines never take colour away from old ones', 'places that got lighter (y, before, after) %s' % lost[:4])
FLOWS['simple_soft_keeps'] = f_simple_soft_keeps

def f_picker_shows(q):  # owner 21 Nov 18:29: the colour picker has its own pointer, and beside it a big swatch of the colour it would pick there
    tap(q, 'tool-simple'); tap(q, 'size-3'); tap(q, 'color-2'); drag(q, [(300, 300), (700, 300)])
    brush = q.evaluate("()=>document.getElementById('paper').style.cursor")
    tap(q, 'pick'); s = q.evaluate("([x,y])=>__cb.screenOf(x,y)", [500, 300]); q.mouse.move(*s); time.sleep(0.2)
    own = q.evaluate("()=>document.getElementById('paper').style.cursor")
    sw = q.evaluate("()=>{const e=document.getElementById('pickpeek');if(!e||e.classList.contains('hide'))return null;const r=e.getBoundingClientRect();return [r.width,getComputedStyle(e).backgroundColor]}")
    report(own != brush and sw is not None and sw[0] >= 60 and 'rgb(2' in sw[1], 'colour picker: own pointer and a big swatch of the colour under it', 'pointer changed %s, swatch %s' % (own != brush, sw))
FLOWS['picker_shows'] = f_picker_shows

def f_mop(q):  # owner 21 Nov 18:29: the mop (3rd watercolour brush) is wetter and softer than the round brush
    tap(q, 'tool-water'); tap(q, 'size-2'); tap(q, 'color-6')
    tap(q, 'shape-0'); drag(q, [(300, 300), (900, 300)], step=20)
    tap(q, 'shape-2'); drag(q, [(300, 650), (900, 650)], step=20)
    q.evaluate("()=>__cb.fast(8)")
    def prof(y0): return [lum(c) for c in q.evaluate("(y0)=>{const o=[];for(let y=y0-110;y<=y0+110;y+=2)o.push(__cb.shown(600,y));return o}", y0)]
    def shape(p):  # width of the mark, and of its edges (where it is between a fifth and three quarters of its darkest)
        paper = sorted(p[:15] + p[-15:])[15]; d = [paper - v for v in p]; top = max(d)
        return sum(2 for v in d if v > 0.2 * top), sum(2 for v in d if 0.2 * top < v < 0.75 * top)
    (wr, er), (wm, em) = shape(prof(300)), shape(prof(650))
    report(wm > wr * 1.2 and em > er * 1.5, 'mop: wetter (spreads wider) and softer (gentler edge) than round', 'width round %d mop %d, edge round %d mop %d' % (wr, wm, er, em))
FLOWS['mop'] = f_mop

def f_marker_real(q):  # owner 21 Nov 18:29: he does not see a marker's crossings get darker or its edge darker; any colour, the size he starts with
    out = []
    for col in ('color-4', 'color-2', 'color-5'):
        q.reload(); q.wait_for_function("()=>window.__cb&&__cb.ready")
        tap(q, 'tool-marker'); tap(q, col); drag(q, [(200, 300), (900, 300)]); drag(q, [(550, 100), (550, 500)])
        r = q.evaluate("()=>__cb.st.size") ; R = [8, 16, 28, 48, 80][r]
        one, two = shown(q, 300, 300), shown(q, 550, 300)
        prof = [shown(q, 300, 300 + dy) for dy in range(0, R + 1)]
        darkest_edge = min(prof[int(R * 0.6):], key=sum); centre = prof[0]  # darker: less light in all three colours together
        out.append((col, one, two, centre, darkest_edge, sum(one) - sum(two), sum(centre) - sum(darkest_edge)))
    ok = all(c[5] > 0.06 * sum(c[1]) and c[6] > 0.04 * sum(c[3]) for c in out)  # noticed as a share of how light the line is
    report(ok, 'marker: crossings clearly darker and the edge darker, in every colour', '; '.join('%s crossing -%.0f edge -%.0f' % (c[0], c[5], c[6]) for c in out))
FLOWS['marker_real'] = f_marker_real

def f_palettes(q):  # owner 21 Nov 18:29: column 1 like his Fiery Red Sunset (dark to light across neighbouring colours), column 2 varied full palettes (pastel, dark, faded, fuller), column 3 two families in one run; 10 each, no two alike; the popup uses most of the screen
    tap(q, 'palette'); time.sleep(0.3)
    cols = q.evaluate("()=>[...document.querySelectorAll('.palcol')].filter(c=>c.closest('.palcols')).map(c=>[...c.querySelectorAll('.pal')].map(p=>[...p.querySelectorAll('u')].map(u=>getComputedStyle(u).backgroundColor.match(/\\d+/g).map(Number))))")
    box = q.evaluate("()=>{const r=document.querySelector('.popbox').getBoundingClientRect();return [r.width/innerWidth,r.height/innerHeight]}")
    import colorsys
    def L(c): return colorsys.rgb_to_hls(*[v / 255 for v in c])[1] * 100
    def far(a, b): return sum(sum(abs(x - y) for x, y in zip(p, r)) for p, r in zip(a, b)) / 30
    fiery = [[3, 7, 30], [55, 6, 23], [106, 4, 15], [157, 2, 8], [208, 0, 0], [220, 47, 2], [232, 93, 4], [244, 140, 6], [250, 163, 7], [255, 186, 8]]
    same = [(c, i, j) for c, col in enumerate(cols) for i in range(len(col)) for j in range(i + 1, len(col)) if far(col[i], col[j]) < 25]
    c1_range = all(max(L(x) for x in p) - min(L(x) for x in p) > 35 for p in cols[0]) if cols else False  # his example runs 45 from darkest to lightest
    means = [sum(L(x) for x in p) / 10 for p in cols[1]] if len(cols) > 1 else []
    ok = (len(cols) == 3 and all(len(c) == 10 and all(len(p) == 10 for p in c) for c in cols) and fiery in cols[0] and not same and c1_range
          and min(means) < 45 and max(means) > 78 and box[0] > 0.8 and box[1] > 0.75)
    report(ok, 'palettes: three columns of 10, Fiery Red Sunset in the first, none alike, light and dark in the second, popup most of the screen',
           'columns %s, Fiery in 1st %s, alike %s, column 1 dark to light %s, column 2 lightness %s..%s, popup %.0f%% x %.0f%%' % ([len(c) for c in cols], bool(cols) and fiery in cols[0], same[:3], c1_range, round(min(means or [0])), round(max(means or [0])), box[0] * 100, box[1] * 100))
FLOWS['palettes'] = f_palettes

def f_acrylic_scrub(q):  # owner 21 Nov 18:29: a 3rd acrylic brush like the Brusheezy acrylic packs (broad scrubbed strokes breaking into dry streaks), clearly unlike the flat
    n = q.evaluate("()=>__cb.shapes.acrylic.length")
    if n < 4: report(False, 'acrylic: a scrubby 3rd brush unlike the flat', 'only %d acrylic brushes' % n); return
    tap(q, 'tool-acrylic'); tap(q, 'size-3'); tap(q, 'color-6')
    tap(q, 'shape-1'); drag(q, [(200, 300), (1100, 300)])
    tap(q, 'shape-2'); drag(q, [(200, 650), (1100, 650)])
    def paper_share(y0): return q.evaluate("(y0)=>{let n=0,p=0;for(let x=400;x<900;x+=4)for(let y=y0-30;y<=y0+30;y+=3){n++;const c=__cb.shown(x,y);if(c[0]>150&&c[1]>150)p++;}return p/n}", y0)
    flat, scrub = paper_share(300), paper_share(650)
    report(scrub > flat + 0.12 and scrub < 0.7, 'acrylic: a scrubby 3rd brush unlike the flat', 'paper showing through: flat %.2f, scrub %.2f' % (flat, scrub))
FLOWS['acrylic_scrub'] = f_acrylic_scrub

def f_pastel_smear(q):  # owner 21 Nov 18:29: the crayon is an oil pastel: passing over pastel smears it, carrying its colour along past where it was
    tap(q, 'tool-crayon'); tap(q, 'shape-0'); tap(q, 'size-3'); tap(q, 'color-4')
    drag(q, [(300, 300), (500, 300), (300, 340), (500, 340)])
    tap(q, 'color-6'); drag(q, [(400, 320), (900, 320)])
    avg = "([x0,x1])=>{const s=[0,0,0];let n=0;for(let x=x0;x<x1;x+=3)for(let y=305;y<=335;y+=3){const c=__cb.shown(x,y);if(c[0]+c[1]+c[2]<600){s[0]+=c[0];s[1]+=c[1];s[2]+=c[2];n++;}}return s.map(v=>Math.round(v/Math.max(1,n)))}"
    near = q.evaluate(avg, [515, 585]); far = q.evaluate(avg, [800, 880])
    report(near[1] - near[2] > far[1] - far[2] + 25, 'oil pastel: dragging through yellow carries yellow along (greener just after it)', 'just past the yellow %s, far from it %s' % (near, far))
FLOWS['pastel_smear'] = f_pastel_smear
