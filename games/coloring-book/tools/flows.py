# Flow tests: what the owner does, in the running game: real page, real mouse drags at a real rate, real touches.
# Each flow runs on a small test paper (?paper=WxH, owner 21 Nov: tests run in seconds) that holds just the part of the full 1600x1000 paper it uses:
# PAPER names the size and where that part starts (ox, oy), and the page gives it that part's canvas grain; flows keep full-paper coordinates and the helpers shift them. Speed and undo-room flows keep the full paper.
# Colours are picked by their place in the Basic palette: 0 white, 1 black, 2 red, 3 orange, 4 yellow, 5 green, 6 blue, 7 purple, 8 pink, 9 brown (owner 21 Nov: every palette 10 colours).
# Each flow starts from a fresh page with no saved pictures and prints PASS or FAIL, its name, and what was seen.
import time, json, pathlib, math
from playwright.sync_api import sync_playwright
GAME = pathlib.Path(__file__).resolve().parent.parent / 'coloring-book.html'  # this copy's own build, so old and new code can be tested at once

# SECTION: HELPERS -- the page on its test paper, taps, holds, drags at a finger's speed, what the paper shows
def page(b, paper='400x250', off=(0, 0)):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True)
    q = ctx.new_page(); q.ox, q.oy = off; q.goto(GAME.as_uri() + '?paper=%s@%d,%d' % (paper, *off))
    q.evaluate("()=>new Promise(r=>{const d=indexedDB.deleteDatabase('coloring-book'); d.onsuccess=d.onerror=d.onblocked=()=>r()})")
    reload(q); return q

def reload(q):  # S(x, y): what the paper shows at a full-paper point, for checks written inside the page
    q.reload(); q.wait_for_function("()=>window.__cb&&__cb.ready"); q.evaluate("([ox,oy])=>{window.S=(x,y)=>__cb.shown(x-ox,y-oy)}", [q.ox, q.oy])

def scr(q, x, y): return q.evaluate("([x,y])=>__cb.screenOf(x,y)", [x - q.ox, y - q.oy])

def tap(q, bid):
    opener = {'size': 'size', 'shape': 'brush', 'blur': 'brush', 'splash': 'brush', 'lift': 'brush'}.get(bid.split('-')[0])  # owner 21 Nov: sizes and brushes are chosen in a popup
    if opener: p = q.evaluate("(id)=>__cb.btn(id)", opener); q.mouse.click(p[0], p[1]); time.sleep(0.1)
    p = q.evaluate("(id)=>__cb.btn(id)", bid); q.mouse.click(p[0], p[1]); time.sleep(0.05)

def hold(q, bid, sec):
    p = q.evaluate("(id)=>__cb.btn(id)", bid); q.mouse.move(p[0], p[1]); q.mouse.down(); time.sleep(sec); q.mouse.up(); time.sleep(0.05)

def drag(q, pts, step=9, per_move=False):  # paper points at a finger's speed: step paper pixels per 16 ms (9: about 550 a second, as on his screen); the pointer is where the finger
    s = [scr(q, *p) for p in pts]                                       # would be by now, so a slow test machine sends fewer moves but the stroke takes the real time.
    if per_move: return drag_moves(q, s, pts, step)                     # per_move: one move of step pixels after another, so each frame paints what one of his frames would (frame-time checks)
    q.mouse.move(*s[0]); q.mouse.down()
    for (x0, y0), (x1, y1), (a, c), (d, e) in zip(s, s[1:], pts, pts[1:]):
        t0, n = time.time(), max(abs(d - a), abs(e - c)) / step * 0.016  # seconds this part takes
        while True:
            f = min(1, (time.time() - t0) / n) if n > 0 else 1
            q.mouse.move(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)
            if f >= 1: break
            time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1)

def drag_moves(q, s, pts, step):
    q.mouse.move(*s[0]); q.mouse.down()
    for (x0, y0), (x1, y1), (a, c), (d, e) in zip(s, s[1:], pts, pts[1:]):
        n = max(1, int(max(abs(d - a), abs(e - c)) / step))
        for i in range(1, n + 1): q.mouse.move(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1)

def shown(q, x, y): return q.evaluate("([x,y])=>__cb.shown(x,y)", [x - q.ox, y - q.oy])
def row(q, y): return q.evaluate("(y)=>{const o=[];for(let x=320;x<1080;x+=4)o.push(S(x,y));return o}", y)
def across(q, x, y, half=20): return q.evaluate("([x,y,h])=>{const s=[0,0,0];for(let i=-h;i<=h;i+=2){const c=S(x+i,y);s[0]+=c[0];s[1]+=c[1];s[2]+=c[2]}return s.map(v=>Math.round(v/(h+1)))}", [x, y, half])
def lum(c): return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
def report(ok, name, seen): print('%-4s %-48s %s' % ('PASS' if ok else 'FAIL', name, seen))

# SECTION: FLOWS -- one per owner rule, in the order he gave them
def f_oil_mix(q):
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); tap(q, 'color-4'); drag(q, [(200, 300), (700, 300)])
    tap(q, 'color-6'); drag(q, [(450, 120), (450, 520)])
    mid, before, after = across(q, 450, 300), across(q, 450, 160), across(q, 450, 380)  # each brush stroke's bristles are new, so a streak can sit on any one pixel: the colour across the stroke
    gr = lambda c: c[1] - c[2]
    report(mid[1] > mid[0] and mid[1] > mid[2] and gr(after) > gr(before) + 15, 'oil: blue over yellow is green and carried on',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_oil_thick_dry(q):
    tap(q, 'tool-acrylic'); tap(q, 'size-1'); tap(q, 'color-2'); drag(q, [(100, 500), (1500, 500)])
    h = q.evaluate("()=>{const T=__cb,a=[150,700,1400].map(x=>{let s=0;for(let j=-10;j<=10;j++)s+=T.Ht[(500-%d+j)*T.CW+x-%d];return +(s/21).toFixed(3)});return a}" % (q.oy, q.ox))
    prof = [round(lum(shown(q, 700, 500 + j))) for j in range(-14, 15, 2)]
    spread = max(prof[2:-2]) - min(prof[2:-2])
    report(h[0] > 0.08 and h[2] < h[0] * 0.8 and spread > 12, 'oil: thick, streaky, runs dry', 'thickness start/mid/end %s, brightness across %s' % (h, prof))

def wait_dry(q, most=60):  # watercolour stays wet a few seconds (owner 21 Nov: wet and dry); wait until it is dry
    t = time.time()
    while q.evaluate("()=>__cb.water.active") and time.time() - t < most: time.sleep(0.2)
    return round(time.time() - t, 1)

def f_water(q):
    tap(q, 'tool-water'); tap(q, 'size-1'); tap(q, 'color-6'); drag(q, [(450, 400), (750, 400)])
    wait_dry(q)
    wet = q.evaluate("()=>__cb.water.active")
    prof = [round(lum(shown(q, 600, 400 + j))) for j in range(0, 40, 2)]
    paper = round(lum(shown(q, 600, 600))); centre = prof[0]; darkest = min(prof)
    tap(q, 'color-6'); drag(q, [(450, 400), (750, 400)]); wait_dry(q)
    twice = round(lum(shown(q, 600, 400)))
    report(not wet and centre < paper - 30 and darkest < centre - 4 and prof.index(darkest) > 3 and twice < centre - 15,
           'watercolour: dries, darker rim, layers darken', 'paper %d, centre %d, across %s, second layer %d' % (paper, centre, prof, twice))

def f_crayon(q):
    tap(q, 'tool-crayon'); tap(q, 'size-2'); tap(q, 'color-2'); drag(q, [(300, 300), (900, 300)])
    r = q.evaluate("()=>{let n=0,p=0;for(let x=400;x<800;x+=3)for(let y=296;y<=304;y++){const c=S(x,y);n++;if(c[1]>200)p++;}return p/n}")
    report(0.1 < r < 0.6, 'crayon: specks of paper stay', 'paper share in the stroke %.2f' % r)

def f_soft(q):
    tap(q, 'tool-simple'); tap(q, 'size-3'); tap(q, 'color-1')  # owner 21 Nov: 5 sizes; size-3 (48) is nearest the old biggest (36)
    def edge(y):
        prof = [lum(shown(q, 600, y + j)) for j in range(0, 60)]
        lo, hi = min(prof), max(prof)
        return sum(1 for v in prof if lo + 0.1 * (hi - lo) < v < lo + 0.9 * (hi - lo))
    tap(q, 'shape-0'); drag(q, [(300, 250), (900, 250)]); tap(q, 'blur-0'); drag(q, [(300, 600), (900, 600)])  # owner 21 Nov: the blurred brushes are a second row
    hard, soft = edge(250), edge(600)
    report(hard <= 4 and soft >= hard + 10, 'simple brush: softness changes the edge', 'edge width sharp %d, fuzzy %d' % (hard, soft))

def f_undo(q):
    tap(q, 'tool-acrylic'); tap(q, 'color-2'); drag(q, [(200, 200), (600, 300)])
    before = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    tap(q, 'color-6'); drag(q, [(300, 100), (300, 500)]); tap(q, 'undo')
    after = q.evaluate("()=>{let s=0;for(let i=0;i<__cb.A.length;i+=7)s+=__cb.A[i]+__cb.Ht[i/3|0];return s}")
    time.sleep(0.1); look = shown(q, 300, 450)
    report(abs(before - after) < 1e-3 and lum(look) > 200, 'undo takes back the last stroke exactly', 'difference %.6f, where it was %s' % (before - after, look))

def f_two_fingers(q):
    tap(q, 'tool-simple'); tap(q, 'color-1')
    cdp = q.context.new_cdp_session(q)
    a = [(300, 300), (800, 700)]  # the fingers' paper points; each move is 8 screen pixels at his paper's scale (about 12 paper pixels)
    t = lambda typ, pts: cdp.send('Input.dispatchTouchEvent', {'type': typ, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in pts]})
    t('touchStart', [(0, scr(q, *a[0]))]); time.sleep(0.03)
    t('touchStart', [(0, scr(q, *a[0])), (1, scr(q, *a[1]))])
    for k in range(1, 20):
        t('touchMove', [(i, scr(q, a[i][0] + k * 11.8, a[i][1])) for i in (0, 1)]); time.sleep(0.016)
    t('touchEnd', []); time.sleep(0.15)
    first, second = shown(q, 350, 300), shown(q, 850, 700)
    report(lum(first) < 80 and lum(second) > 200, 'touch: first finger paints, second does nothing', 'under first %s, under second %s' % (first, second))

def f_stickers(q):
    tap(q, 'tool-sticker'); p = q.evaluate("()=>__cb.btn('sticker-star')"); s = scr(q, 800, 500)
    q.mouse.move(*p); q.mouse.down()
    for i in range(1, 21): q.mouse.move(p[0] + (s[0] - p[0]) * i / 20, p[1] + (s[1] - p[1]) * i / 20); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1); placed = q.evaluate("()=>__cb.stickers.map(s=>[s.kind,Math.round(s.x),Math.round(s.y)])")
    drag(q, [(800, 500), (800, 650)]); gone = q.evaluate("()=>__cb.stickers.length")
    report(len(placed) == 1 and abs(placed[0][1] + q.ox - 800) < 5 and gone == 0, 'stickers: drag on, drag off', 'placed %s, after dragging off %d' % (placed, gone))

def f_gallery(q):
    tap(q, 'tool-acrylic'); tap(q, 'color-5'); drag(q, [(200, 500), (450, 500)])
    painted = shown(q, 400, 500); tap(q, 'new'); time.sleep(0.5)
    blank = shown(q, 400, 500); n = q.evaluate("()=>__cb.count()")
    tap(q, 'gallery'); time.sleep(0.4)
    cards = q.evaluate("()=>[...document.querySelectorAll('#gal .card')].map(c=>{const r=c.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2,c.classList.contains('cur')]})")
    old = [c for c in cards if not c[2]]
    if old: q.mouse.click(old[0][0], old[0][1]); time.sleep(0.6)
    back = shown(q, 400, 500)
    reload(q); time.sleep(0.2); reopened = shown(q, 400, 500)
    close = lambda a, b: max(abs(x - y) for x, y in zip(a, b)) <= 6
    report(n >= 1 and lum(blank) > 200 and old and close(back, painted) and close(reopened, painted), 'gallery: new keeps the old, open it again',
           'painted %s, new page %s, kept %d, opened again %s, after reload %s' % (painted, blank, n, back, reopened))

def f_speed(q):  # what he would feel: time spent painting per frame with the biggest oil brush moving fast
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); tap(q, 'color-3')
    q.evaluate("()=>{window.__ft=[];let l=performance.now();const f=(t)=>{__ft.push(t-l);l=t;if(__ft.length<400)requestAnimationFrame(f)};requestAnimationFrame(f)}")
    drag(q, [(100, 200), (1500, 300), (100, 400), (1500, 500), (100, 600)], step=37, per_move=True)
    ft = q.evaluate("()=>__ft.slice(5).sort((a,b)=>a-b)"); p95 = ft[int(len(ft) * 0.95)]
    report(p95 < 34, 'speed: big oil brush, fast strokes (this machine)', '95%% of frames under %.0f ms' % p95)

def f_ctrl_z(q):  # owner 21 Nov: Ctrl+Z takes back; Ctrl+X does not
    tap(q, 'tool-acrylic'); tap(q, 'color-2'); drag(q, [(200, 300), (900, 300)]); painted = shown(q, 500, 300)
    q.keyboard.press('Control+x'); time.sleep(0.1); after_x = shown(q, 500, 300)
    q.keyboard.press('Control+z'); time.sleep(0.1); look = shown(q, 500, 300)
    report(lum(painted) < 150 and after_x == painted and lum(look) > 200, 'Ctrl+Z takes back the last stroke, Ctrl+X does nothing', 'painted %s, after Ctrl+X %s, after Ctrl+Z %s' % (painted, after_x, look))

def f_load(q):  # owner 21 Nov: a tap gives a full brush; holding goes round a third, two thirds, full, a third...; a third looks washed out from the start
    tap(q, 'tool-acrylic'); levels = []
    for sec in (0.05, 0.6, 1.1, 1.6, 2.1): hold(q, 'color-6', sec); levels.append(q.evaluate("()=>__cb.st.load"))
    hold(q, 'color-6', 0.6); drag(q, [(200, 300), (500, 300)])
    hold(q, 'color-6', 0.05); drag(q, [(200, 600), (500, 600)])
    little, full = lum(shown(q, 300, 300)), lum(shown(q, 300, 600))
    report(levels == [3, 1, 2, 3, 1] and little > full + 30, 'paint amount: a tap is full, holding goes round; little paint is washed out',
           'after a tap, then holding 0.6, 1.1, 1.6, 2.1 s: %s; brightness near the start with a third %d, full %d' % (levels, little, full))

def f_fixed_angle(q):  # owner 21 Nov: the flat brush does not turn by itself
    tap(q, 'tool-marker'); tap(q, 'shape-1'); tap(q, 'size-3'); hold(q, 'color-1', 0.05)
    drag(q, [(200, 300), (800, 300)]); drag(q, [(950, 250), (950, 650)])
    across_h = sum(1 for dy in range(-60, 61, 2) if lum(shown(q, 500, 300 + dy)) < 120) * 2
    across_v = sum(1 for dx in range(-60, 61, 2) if lum(shown(q, 950 + dx, 450)) < 120) * 2
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

def f_undo_all(q):  # owner 21 Nov: undo goes all the way back (24 big strokes over a 640x384 paper: more changed tiles than the undo room on the graphics card holds, so old steps come back from memory)
    tap(q, 'tool-simple'); tap(q, 'size-4'); tap(q, 'color-1'); n = 24
    for k in range(n): drag(q, [(20, 40 + k * 13), (620, 60 + k * 13), (20, 80 + k * 13)], step=20)  # quick (1250 px/s) but below lifting off (owner 23 Nov: a flick lifts the brush)
    dark = lum(shown(q, 320, 50))
    for k in range(n): q.keyboard.press('Control+z'); time.sleep(0.15)
    time.sleep(1.0); look = [lum(shown(q, 320, 50 + k * 13)) for k in range(0, n, 4)]
    report(dark < 80 and min(look) > 200, 'undo goes all the way back to the empty page', 'painted %d, after %d undos %s' % (dark, n, look))

def f_marker(q):  # owner 21 Nov: a marker; its ink is see-through, so crossing lines get darker
    tap(q, 'tool-marker'); tap(q, 'size-2'); tap(q, 'color-6'); drag(q, [(200, 300), (900, 300)]); drag(q, [(550, 200), (550, 400)])
    one, two = shown(q, 300, 300), shown(q, 550, 300)
    report(lum(two) < lum(one) - 15, 'marker: crossing lines get darker', 'one line %s, crossing %s' % (one, two))

def f_delete(q):  # owner 21 Nov: delete the open picture, so a child cannot do it by accident (as the architects game's restart)
    tap(q, 'tool-acrylic'); tap(q, 'color-2'); drag(q, [(200, 300), (900, 300)]); q.evaluate("()=>__cb.save()"); time.sleep(0.3)
    n0 = q.evaluate("()=>__cb.count()"); tap(q, 'delete'); time.sleep(0.3); n1 = q.evaluate("()=>__cb.count()"); still = shown(q, 500, 300)
    time.sleep(6.3); tap(q, 'delete'); time.sleep(0.3); n2 = q.evaluate("()=>__cb.count()")
    tap(q, 'delete'); time.sleep(0.1); tap(q, 'delete'); time.sleep(0.6); n3 = q.evaluate("()=>__cb.count()"); look = shown(q, 500, 300)
    report(n0 == 1 and n1 == 1 and lum(still) < 150 and n2 == 1 and n3 == 0 and lum(look) > 200, 'delete: one press only warns, a second press soon after deletes',
           'pictures before %d, after one press %d, after a press 6 s later %d, after two quick presses %d, page now %s' % (n0, n1, n2, n3, look))

def f_delete_elsewhere(q):  # owner 21 Nov: after the first delete press, touching anywhere else takes the warning back
    tap(q, 'tool-acrylic'); tap(q, 'color-2'); drag(q, [(200, 300), (900, 300)]); q.evaluate("()=>__cb.save()"); time.sleep(0.3)
    tap(q, 'delete'); q.mouse.click(4, 4); time.sleep(0.1); tap(q, 'delete'); time.sleep(0.6); n = q.evaluate("()=>__cb.count()")
    report(n == 1, 'delete: a touch elsewhere takes the warning back', 'pictures after press, touch elsewhere, press: %d' % n)

def f_shapes(q):  # owner 21 Nov: brush shapes; a flat brush is a bar, held at one diagonal angle (it does not turn with the stroke)
    tap(q, 'tool-marker'); tap(q, 'size-3'); tap(q, 'color-1'); tap(q, 'shape-0'); drag(q, [(300, 200), (300, 200.5)])
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
    tap(q, 'tool-acrylic'); tap(q, 'size-2'); tap(q, 'color-4'); drag(q, [(200, 300), (700, 300)])
    q.evaluate("()=>__cb.age(300)")  # five minutes pass
    tap(q, 'color-6'); drag(q, [(450, 120), (450, 520)])
    mid, before, after = across(q, 450, 300), across(q, 450, 160), across(q, 450, 380)  # each brush stroke's bristles are new, so a streak can sit on any one pixel: the colour across the stroke
    gr = lambda c: c[1] - c[2]
    report(mid[2] > mid[1] and abs(gr(after) - gr(before)) < 10, 'oil: dry paint is not smeared, new paint covers it',
           'crossing %s, blue before %s, blue after %s' % (mid, before, after))

def f_flat(q):  # with the paper flat the paint does not run down
    tap(q, 'tool-water'); tap(q, 'size-2'); tap(q, 'color-6')
    drag(q, [(450, 300), (750, 300)]); drag(q, [(450, 310), (750, 310)]); took = wait_dry(q, 30)
    paper = min(lum(c) for c in row(q, 520)); below = min(lum(c) for c in row(q, 400))
    report(below > paper - 8, 'flat paper: paint stays where it was put', 'darkest paper %d, darkest 60 below %d, waited %ss' % (paper, below, took))

FLOWS = {'oil_mix': f_oil_mix, 'oil_thick_dry': f_oil_thick_dry, 'water': f_water, 'crayon': f_crayon, 'soft': f_soft, 'undo': f_undo,
         'two_fingers': f_two_fingers, 'stickers': f_stickers, 'gallery': f_gallery, 'speed': f_speed,
         'ctrl_z': f_ctrl_z, 'oil_dry': f_oil_dry, 'flat': f_flat,
         'load': f_load, 'esc': f_esc, 'guide_menu': f_guide_menu, 'fixed_angle': f_fixed_angle, 'marker_ends': f_marker_ends, 'guide_place': f_guide_place, 'undo_all': f_undo_all, 'marker': f_marker, 'delete': f_delete, 'delete_elsewhere': f_delete_elsewhere, 'shapes': f_shapes, 'canvas': f_canvas}

# SECTION: PAPERS AND RUN -- each flow's test paper, the test-paper flow, the runner
PAPER = {  # flow: (test paper, where it starts on the full paper); not named: 400x250 from the top left
    'oil_mix': ('600x500', (150, 70)), 'oil_dry': ('600x500', (150, 70)), 'oil_thick_dry': ('1500x120', (50, 440)), 'water': ('720x300', (240, 330)),
    'crayon': ('680x120', (260, 240)), 'soft': ('700x500', (250, 180)), 'undo': ('520x500', (140, 50)), 'two_fingers': ('820x500', (250, 250)),
    'stickers': ('400x250', (600, 375)), 'gallery': ('400x250', (100, 375)), 'speed': ('1600x1000', (0, 0)), 'ctrl_z': ('800x120', (150, 240)),
    'load': ('400x420', (150, 240)), 'fixed_angle': ('880x530', (140, 185)), 'marker_ends': ('830x200', (210, 300)), 'undo_all': ('640x384', (0, 0)),
    'marker': ('800x300', (150, 150)), 'marker_real': ('800x300', (150, 150)), 'delete': ('800x250', (150, 175)), 'delete_elsewhere': ('800x250', (150, 175)),
    'shapes': ('600x200', (200, 100)), 'canvas': ('400x250', (200, 250)), 'flat': ('900x300', (250, 240)), 'crayon_levels': ('680x300', (260, 200)),
    'crayon_blend': ('680x120', (260, 240)), 'water_speed': ('1600x1000', (0, 0)), 'crayon_back_forth': ('680x120', (260, 340)), 'crayon_bend': ('500x300', (250, 250)),
    'picker': ('400x300', (250, 250)), 'simple_over': ('700x400', (250, 200)), 'water_no_hitch': ('1600x1000', (0, 0)), 'simple_soft_keeps': ('600x260', (350, 185)),
    'picker_shows': ('500x200', (250, 200)), 'mop': ('680x500', (260, 180)), 'acrylic_scrub': ('1000x280', (150, 235)), 'pastel_smear': ('700x160', (250, 240)), 'simple_self_cross': ('600x350', (250, 150))}

def f_test_paper(q):  # owner 21 Nov: tests on a smaller paper: the page takes its size from the address, and a stroke lands where it is drawn
    tap(q, 'tool-simple'); tap(q, 'color-1'); drag(q, [(100, 125), (300, 125)])
    size, on, off = q.evaluate("()=>[__cb.CW,__cb.CH]"), lum(shown(q, 200, 125)), lum(shown(q, 200, 40))
    report(size == [400, 250] and on < 80 and off > 200, 'test paper: 400x250 from the address, strokes land where drawn', 'paper %s, on the stroke %d, beside it %d' % (size, on, off))
FLOWS['test_paper'] = f_test_paper

def glide(q, at, L, v0, v1, v2=None):  # a stroke along a path: at(d) is the paper point d pixels along it, L its length; speed goes evenly (in time) from v0 to v1, then to v2 over the second half if given.
    cdp = q.context.new_cdp_session(q); t0 = time.time(); d, t, n = 0.0, 0.0, 0  # moves 16 ms apart with their own times, as his screen sends them
    def v(d): return v0 + (v1 - v0) * min(1, d / (L if v2 is None else L / 2)) if v2 is None or d < L / 2 else v1 + (v2 - v1) * (d - L / 2) / (L / 2)
    def ev(typ, t, d, extra={}):
        X, Y = scr(q, *at(d)); cdp.send('Input.dispatchMouseEvent', dict({'type': typ, 'x': X, 'y': Y, 'button': 'left', 'buttons': 1, 'timestamp': t0 + t}, **extra))
    ev('mousePressed', 0, 0, {'clickCount': 1})
    while d < L: d = min(L, d + v(d) * 0.016); t += 0.016; ev('mouseMoved', t, d)
    ev('mouseReleased', t, d, {'clickCount': 1}); cdp.detach(); time.sleep(0.15)

def f_lift_control(q):  # owner 23 Nov 22:37, point 1: once off the paper the brush stays off until a new touch; the biggest brush's tail has no sudden size changes; speeding up round a circle thins it evenly to the end, as on a line
    import math
    tap(q, 'tool-acrylic'); tap(q, 'shape-0'); tap(q, 'size-4'); tap(q, 'color-1'); tap(q, 'lift'); bad = []  # lifting is a switch, off at the start (owner 24 Nov)
    glide(q, lambda d: (100 + d, 150), 1450, 550, 5500, 300)  # speeds up to a flick, then slows down while still pressed (owner 24 Nov: lifting is slower, so a faster flick to go off)
    ws = [width_across(q, x, 150, 0, 1, 110) for x in range(110, 1500, 4)]
    off = next((j for j in range(len(ws)) if j > 10 and max(ws[j:j + 6]) == 0), len(ws))
    back = sum(1 for w in ws[off:] if w > 0); grows = [j for j in range(8, off) if ws[j] > max(ws[j - 8:j]) + 4]
    if back or grows: bad.append('biggest: back on the paper %d places, widens %d times in the tail' % (back, len(grows)))
    tap(q, 'size-2'); tap(q, 'color-1'); R, L = 200, 2 * math.pi * 200
    glide(q, lambda d: (800 + R * math.cos(d / R), 700 + R * math.sin(d / R)), L * 0.97, 700, 4200)  # one turn, speeding up evenly (owner 24 Nov: lifting starts at 2000)
    glide(q, lambda d: (150 + d, 330), L * 0.97, 700, 4200)  # the same on a line
    def circ(f): a = f * 0.97 * 2 * math.pi; return max(width_across(q, 800 + R * math.cos(a + e), 700 + R * math.sin(a + e), math.cos(a + e), math.sin(a + e), 45) for e in (-0.02, 0, 0.02))
    def line(f): x = 150 + f * L * 0.97; return max(width_across(q, x + e, 330, 0, 1, 45) for e in (-4, 0, 4))
    c, l = [circ(f) for f in (0.1, 0.5, 0.9)], [line(f) for f in (0.1, 0.5, 0.9)]
    if not (c[0] > c[2] * 1.25 and c[2] > 0): bad.append('circle does not thin evenly to its end %s' % c)
    if any(abs(a - b) > 0.25 * max(a, b, 1) for a, b in zip(c, l)): bad.append('circle %s and line %s differ' % (c, l))
    report(not bad, 'lifting: stays off, smooth tail, thins on circles as on lines', '; '.join(bad) or 'circle %s line %s' % (c, l))
FLOWS['lift_control'] = f_lift_control
PAPER['lift_control'] = ('1600x1000', (0, 0))

def f_pal_keep_colours(q):  # owner 23 Nov 22:37, point 2: no palette colour disappears; a palette's own near-white or near-black is its white or black bucket
    bad = []
    for name in ('Basic', 'Scandi Brick and Slate', 'Earth, Sage and Sky', 'Red', 'Standard rainbow'):
        i = q.evaluate("(n)=>__cb.palIndex(n)", name); own = q.evaluate("(i)=>__cb.pal(i).map(c=>c.map(v=>Math.round(v*255)))", i)
        tap(q, 'palette'); time.sleep(0.3); tap(q, 'pal-%d' % i); time.sleep(0.1); got = []
        for c in pots_shown(q): tap(q, c); got.append(q.evaluate("()=>__cb.color()"))
        lost = [c for c in own if c not in got]
        if lost or lum(got[0]) < 235 or lum(got[1]) > 25: bad.append('%s: lost %s, first two %s %s' % (name, lost, got[0], got[1]))
    report(not bad, 'buckets: every palette colour shown, white and black first', '; '.join(bad))
FLOWS['pal_keep_colours'] = f_pal_keep_colours

def f_pot_ring_inside(q):  # owner 23 Nov 22:37, point 3: the chosen bucket's ring never goes off the screen at the bottom or under the paper at the top
    bad = []
    for w, h in ((1280, 800), (1920, 1080), (1366, 768)):
        q.set_viewport_size({'width': w, 'height': h}); time.sleep(0.3)
        for c in pots_shown(q):
            tap(q, c); time.sleep(0.25)
            r = q.evaluate("()=>{const e=document.querySelector('#bottom .pot.on'),k=e.getBoundingClientRect(),s=getComputedStyle(e),sc=k.width/e.offsetWidth,o=(parseFloat(s.outlineOffset)+parseFloat(s.outlineWidth))*sc,p=document.getElementById('paper').getBoundingClientRect();return [k.top-o,k.bottom+o,p.bottom,innerHeight]}")
            if r[1] > r[3] or r[0] < r[2]: bad.append('%dx%d %s: ring %d..%d, paper ends %d, screen ends %d' % (w, h, c, r[0], r[1], r[2], r[3]))
    report(not bad, 'buckets: chosen ring stays between the paper and the screen edge', '%d wrong: %s' % (len(bad), bad[:3]))
FLOWS['pot_ring_inside'] = f_pot_ring_inside

def f_spray_speed(q):  # owner 23 Nov 22:37, point 4: a faster spray stroke leaves its drops further apart; spraying in place makes no ring at the edge
    tap(q, 'tool-spray'); tap(q, 'shape-0'); tap(q, 'size-3'); tap(q, 'color-1')
    def cover(y): return sum(width_across(q, x, y, 0, 1, 60) for x in range(200, 700, 5))
    jerk(q, 100, 800, 80, 300); jerk(q, 100, 800, 230, 1200); slow, fast = cover(80), cover(230)
    x, y = scr(q, 400, 420); q.mouse.move(x, y); q.mouse.down(); time.sleep(1.5); q.mouse.up(); time.sleep(0.1)
    import math
    pts = q.evaluate("()=>{const o=[];for(let dy=-60;dy<=60;dy++)for(let dx=-60;dx<=60;dx++){const c=S(400+dx,420+dy);o.push(0.3*c[0]+0.59*c[1]+0.11*c[2]<150?1:0)}return o}")
    def share(r0, r1):
        v = [pts[(dy + 60) * 121 + dx + 60] for dy in range(-60, 61) for dx in range(-60, 61) if r0 <= math.hypot(dx, dy) < r1]; return sum(v) / len(v)
    inner, edge = share(40, 45), share(46, 51)  # the size has radius 48: just inside it, and at it
    report(fast < slow * 0.4 and edge < inner * 0.8, 'spray: faster is sparser, no ring when held still', 'paint along slow %d, fast %d; held: %.2f inside, %.2f at the edge' % (slow, fast, inner, edge))
FLOWS['spray_speed'] = f_spray_speed
PAPER['spray_speed'] = ('900x500', (0, 0))

def f_shapes_close(q):  # owner 23 Nov 22:37, point 5: shapes as the Squares Brush (av01d fabric-brushes): each shape touches the next, along the whole stroke
    tap(q, 'tool-shapes'); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-1'); out = []
    for k, v in enumerate((400, 900)):
        y = 80 + k * 160; jerk(q, 60, 820, y, v)
        line = q.evaluate("(y)=>{const o=[];for(let x=120;x<760;x++){const c=S(x,y);o.push(0.3*c[0]+0.59*c[1]+0.11*c[2]<235?1:0)}return o}", y)
        out.append(round(sum(line) / len(line), 2))
    report(min(out) >= 0.9, 'shapes: each touches the next', 'share of the stroke line covered at 400 and 900 px/s: %s' % out)
FLOWS['shapes_close'] = f_shapes_close
PAPER['shapes_close'] = ('900x400', (0, 0))

def f_ink_splash_drawing(q):  # owner 23 Nov 22:37, point 6: ink as in the fabric-brushes page: a solid body, and splashes while it still paints, not only as it lifts off
    tap(q, 'tool-ink'); tap(q, 'shape-0'); tap(q, 'size-3'); tap(q, 'color-1'); tap(q, 'splash-2')
    jerk(q, 60, 840, 120, 600); body = q.evaluate("()=>{let n=0,k=0;for(let x=150;x<750;x+=3)for(let dy=-12;dy<=12;dy+=3){const c=S(x,120+dy);k++;if(0.3*c[0]+0.59*c[1]+0.11*c[2]<150)n++}return n/k}")
    jerk(q, 60, 840, 330, 1200)  # quick, still on the paper
    still = width_across(q, 700, 330, 0, 1, 40) > 0
    spl = q.evaluate("()=>{let n=0;for(let x=100;x<800;x+=3)for(const dy of [-80,-65,65,80]){const c=S(x,330+dy);if(0.3*c[0]+0.59*c[1]+0.11*c[2]<150)n++}return n}")
    report(body >= 0.85 and still and spl >= 3, 'ink: solid body, splashes while still painting', 'body %.2f covered, still painting %s, splash spots %d' % (body, still, spl))
FLOWS['ink_splash_drawing'] = f_ink_splash_drawing
PAPER['ink_splash_drawing'] = ('900x480', (0, 0))

def f_cursor_turns(q):  # owner 23 Nov 22:37, point 7: going round in circles, the pointer (the brush shown at the pointer) turns with the brush
    import math
    tap(q, 'tool-acrylic')
    for b in ('brush', 'turn'): p = q.evaluate("(id)=>__cb.btn(id)", b); q.mouse.click(p[0], p[1]); time.sleep(0.15)
    tap(q, 'shape-1'); tap(q, 'size-3'); tap(q, 'color-1')
    cdp = q.context.new_cdp_session(q); t0 = time.time(); seen = set()
    def ev(typ, t, a, extra={}):
        X, Y = scr(q, 450 + 150 * math.cos(a), 300 + 150 * math.sin(a)); cdp.send('Input.dispatchMouseEvent', dict({'type': typ, 'x': X, 'y': Y, 'button': 'left', 'buttons': 1, 'timestamp': t0 + t}, **extra))
    ev('mousePressed', 0, 0, {'clickCount': 1}); t = 0
    for i in range(1, 61):
        t += 0.016; ev('mouseMoved', t, i / 60 * 2 * math.pi)
        if i % 15 == 0: seen.add(q.evaluate("()=>document.getElementById('paper').style.cursor.slice(0,200)"))
    ev('mouseReleased', t, 2 * math.pi, {'clickCount': 1}); cdp.detach()
    report(len(seen) >= 3, 'pointer turns with the brush going round', '%d different pointers in 4 quarter turns' % len(seen))
FLOWS['cursor_turns'] = f_cursor_turns
PAPER['cursor_turns'] = ('900x600', (0, 0))

def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in (names or FLOWS):
            q = page(b, *PAPER.get(n, ('400x250', (0, 0)))); t0 = time.time()
            try: FLOWS[n](q)
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0])
            q.context.close(); print('TIME %-44s %.1f s' % (n, time.time() - t0))  # every flow timed (a slow test is fixed first)
        b.close()

# SECTION: LATER FLOWS -- owner rules from 21 Nov afternoon on
def f_crayon_levels(q):  # owner 21 Nov: the bucket levels are how hard the crayon presses; the lighter ones must still paint clearly
    tap(q, 'tool-crayon'); tap(q, 'size-2'); out = []
    for lv, y in ((1, 250), (2, 350), (3, 450)):
        hold(q, 'color-6', 0.6 + 0.5 * (lv - 1)) if lv < 3 else tap(q, 'color-6')
        drag(q, [(300, y), (900, y)])
        out.append(q.evaluate("(y)=>{let n=0,p=0;for(let x=400;x<800;x+=3)for(let k=y-4;k<=y+4;k++){const c=S(x,k);n++;if(c[0]>200)p++;}return 1-p/n}", y))
    report(0.3 < out[0] < out[1] < out[2], 'crayon: a third, two thirds, full press cover more and more', 'covered %s' % ['%.2f' % v for v in out])

def f_crayon_blend(q):  # owner 21 Nov: crayons blend: a second colour pressed over the first mixes with it
    tap(q, 'tool-crayon'); tap(q, 'size-2'); tap(q, 'color-4'); drag(q, [(300, 300), (900, 300)])
    a = q.evaluate("()=>S(600,300)"); tap(q, 'color-6'); drag(q, [(300, 300), (900, 300)])
    b = q.evaluate("()=>{const s=[0,0,0];let n=0;for(let x=500;x<700;x+=2){const c=S(x,300);if(c[0]<235){s[0]+=c[0];s[1]+=c[1];s[2]+=c[2];n++;}}return s.map(v=>v/n)}")
    report(b[1] > b[2] and b[0] < 200, 'crayon: blue over yellow blends green', 'yellow %s, both %s' % (a, [round(v) for v in b]))
FLOWS.update({'crayon_levels': f_crayon_levels, 'crayon_blend': f_crayon_blend})

def f_water_speed(q):  # owner 21 Nov: watercolour laggy, more so with more paint on the page: frame time follows the wet paint, not the box around it
    tap(q, 'tool-water'); tap(q, 'size-2'); tap(q, 'color-6')
    ft = "()=>new Promise(res=>{const o=[];let l=performance.now();const f=(t)=>{o.push(t-l);l=t;if(o.length<12)requestAnimationFrame(f);else res(o.slice(2).sort((a,b)=>a-b)[5])};requestAnimationFrame(f)})"
    drag(q, [(150, 150), (400, 150)], step=44, per_move=True); one = q.evaluate(ft)
    drag(q, [(1200, 850), (1450, 850)], step=44, per_move=True); two = q.evaluate(ft)
    report(two < one * 2.6, 'watercolour: two far wet spots cost about twice one', 'frame %.0f ms with one, %.0f ms with two (this machine)' % (one, two))
FLOWS['water_speed'] = f_water_speed

def f_crayon_back_forth(q):  # owner 21 Nov 17:26: going back and forth over the same line keeps adding colour all along it, not only at its ends (papers 1 and 3)
    tap(q, 'tool-crayon'); tap(q, 'size-2'); tap(q, 'color-6')
    pts = [(300, 400), (900, 400)] * 3
    drag(q, pts[:2]); one = q.evaluate("()=>{let n=0,p=0;for(let x=500;x<700;x+=3)for(let y=396;y<=404;y++){n++;if(S(x,y)[0]>200)p++;}return 1-p/n}")
    drag(q, pts)
    more = q.evaluate("()=>{let n=0,p=0;for(let x=500;x<700;x+=3)for(let y=396;y<=404;y++){n++;if(S(x,y)[0]>200)p++;}return 1-p/n}")
    report(more > one + 0.08, 'crayon: back and forth adds colour in the middle', 'covered in the middle: one pass %.2f, then four more %.2f' % (one, more))

def f_crayon_bend(q):  # owner 21 Nov 17:26: a bend does not paint thicker than the straight part
    tap(q, 'tool-crayon'); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-6')
    drag(q, [(300, 300), (700, 300), (700, 500)])
    cov = "([x0,y0,x1,y1])=>{let n=0,p=0;for(let x=x0;x<x1;x+=2)for(let y=y0;y<y1;y+=2){n++;if(S(x,y)[0]>200)p++;}return 1-p/n}"
    straight = q.evaluate(cov, [450, 290, 550, 310]); corner = q.evaluate(cov, [670, 290, 690, 310])
    report(corner < straight + 0.12, 'crayon: the bend is not denser than the straight part', 'covered straight %.2f, inside the bend %.2f' % (straight, corner))
FLOWS.update({'crayon_back_forth': f_crayon_back_forth, 'crayon_bend': f_crayon_bend})

def f_picker(q):  # owner 21 Nov 17:26: a colour picker next to the palette: tap it, tap the painting, paint with that colour
    tap(q, 'tool-simple'); tap(q, 'size-2'); tap(q, 'color-2'); drag(q, [(300, 300), (600, 300)])
    tap(q, 'color-6'); tap(q, 'pick'); s = scr(q, 450, 300); q.mouse.click(*s); time.sleep(0.1)
    drag(q, [(300, 450), (600, 450)]); a, b = shown(q, 450, 300), shown(q, 450, 450)
    report(max(abs(a[i] - b[i]) for i in range(3)) < 12, 'colour picker: the picked red paints red', 'picked from %s, painted %s' % (a, b))

def f_keep_amount(q):  # owner 21 Nov 17:26: with a paint amount chosen, choosing another colour keeps it
    hold(q, 'color-2', 0.6); lv = q.evaluate("()=>__cb.st.load"); tap(q, 'color-6')
    report(lv == 1 and q.evaluate("()=>__cb.st.load") == 1, 'another colour keeps the paint amount', 'a third chosen (%s), after another colour %s' % (lv, q.evaluate("()=>__cb.st.load")))

def f_simple_over(q):  # owner 21 Nov 17:26: the simple brush lays its colour over what is there by opacity; a soft edge never lightens the colour under it
    tap(q, 'tool-simple'); tap(q, 'size-3'); tap(q, 'color-6'); drag(q, [(300, 400), (900, 400)])
    dxs = range(30, 80, 5); unders = [shown(q, 600 + dx, 400) for dx in dxs]; under = unders[0]  # the blue at each place before the yellow (the blue line varies a little with the finger's speed)
    tap(q, 'blur-0'); tap(q, 'color-4'); drag(q, [(600, 250), (600, 550)])
    edge = [shown(q, 600 + dx, 400) for dx in dxs]
    report(all(lum(e) >= lum(u) - 6 and e[2] <= u[2] + 6 for e, u in zip(edge, unders)), 'simple brush: a soft yellow edge over blue only adds yellow', 'blue %s, across the edge %s' % (under, edge[::3]))
FLOWS.update({'picker': f_picker, 'keep_amount': f_keep_amount, 'simple_over': f_simple_over})

def f_water_no_hitch(q):  # owner 21 Nov 18:29: after a few strokes on dry paper, new strokes lag and show late: no frame may hang while he paints on (the undo room filling up)
    tap(q, 'tool-simple'); tap(q, 'size-4'); tap(q, 'color-6')
    for y in (100, 300, 500, 700, 900): drag(q, [(50, y), (1550, y)], step=118, per_move=True)
    for c in ('color-2', 'color-4'):
        tap(q, c)
        for y in (100, 300, 500, 700, 900): drag(q, [(50, y), (1550, y)], step=118, per_move=True)
    time.sleep(2); tap(q, 'tool-water'); tap(q, 'size-3'); free = q.evaluate("()=>__cb.freeTiles")  # a moment of rest, as between his strokes
    q.evaluate("()=>{window.__gaps=[];let l=performance.now();const f=(t)=>{__gaps.push(t-l);l=t;if(__gaps.length<40)requestAnimationFrame(f)};requestAnimationFrame(f)}")
    drag(q, [(400, 200), (1200, 200)], step=44, per_move=True); time.sleep(1)
    g = sorted(q.evaluate("()=>__gaps.slice(2)")); med = g[len(g) // 2]
    report(g[-1] < 3 * med + 50 and free >= 400, 'painting never waits for undo room: a whole page is free before a stroke', 'longest frame %.0f ms, usual %.0f ms (this machine), free undo room before %s' % (g[-1], med, free))
FLOWS['water_no_hitch'] = f_water_no_hitch

def f_simple_soft_keeps(q):  # owner 21 Nov 18:29: the soft simple brush damages lines it painted before; a new soft line only adds colour, never takes any away
    tap(q, 'tool-simple'); tap(q, 'blur-0'); tap(q, 'size-3'); tap(q, 'color-6')
    drag(q, [(400, 300), (900, 300)])
    ys = range(240, 365, 5); before = [lum(shown(q, 700, y)) for y in ys]
    drag(q, [(400, 380), (900, 380)]); drag(q, [(400, 250), (900, 250)])
    after = [lum(shown(q, 700, y)) for y in ys]
    lost = [(y, round(b), round(a)) for y, b, a in zip(ys, before, after) if a > b + 4]
    report(not lost, 'simple soft brush: new lines never take colour away from old ones', 'places that got lighter (y, before, after) %s' % lost[:4])
FLOWS['simple_soft_keeps'] = f_simple_soft_keeps

def f_picker_shows(q):  # owner 21 Nov 18:29: the colour picker has its own pointer, and beside it a big swatch of the colour it would pick there
    tap(q, 'tool-simple'); tap(q, 'size-3'); tap(q, 'color-2'); drag(q, [(300, 300), (700, 300)])
    brush = q.evaluate("()=>document.getElementById('paper').style.cursor")
    tap(q, 'pick'); s = scr(q, 500, 300); q.mouse.move(*s); time.sleep(0.2)
    own = q.evaluate("()=>document.getElementById('paper').style.cursor")
    sw = q.evaluate("()=>{const e=document.getElementById('pickpeek');if(!e||e.classList.contains('hide'))return null;const r=e.getBoundingClientRect();return [r.width,getComputedStyle(e).backgroundColor]}")
    report(own != brush and sw is not None and sw[0] >= 60 and 'rgb(2' in sw[1], 'colour picker: own pointer and a big swatch of the colour under it', 'pointer changed %s, swatch %s' % (own != brush, sw))
FLOWS['picker_shows'] = f_picker_shows

def f_mop(q):  # owner 21 Nov 18:29: the mop (3rd watercolour brush) is wetter and softer than the round brush
    tap(q, 'tool-water'); tap(q, 'size-2'); tap(q, 'color-6')
    tap(q, 'shape-0'); drag(q, [(450, 300), (750, 300)], step=30)
    tap(q, 'shape-2'); drag(q, [(450, 560), (750, 560)], step=30)
    q.evaluate("()=>__cb.fast(8)")
    def prof(y0): return [lum(c) for c in q.evaluate("(y0)=>{const o=[];for(let y=y0-110;y<=y0+110;y+=2)o.push(S(600,y));return o}", y0)]
    def shape(p):  # width of the mark, and of its edges (where it is between a fifth and three quarters of its darkest)
        paper = sorted(p[:15] + p[-15:])[15]; d = [paper - v for v in p]; top = max(d)
        return sum(2 for v in d if v > 0.2 * top), sum(2 for v in d if 0.2 * top < v < 0.75 * top)
    (wr, er), (wm, em) = shape(prof(300)), shape(prof(560))
    report(wm > wr * 1.2 and em > er * 1.5, 'mop: wetter (spreads wider) and softer (gentler edge) than round', 'width round %d mop %d, edge round %d mop %d' % (wr, wm, er, em))
FLOWS['mop'] = f_mop

def f_marker_real(q):  # owner 21 Nov 18:29: he does not see a marker's crossings get darker or its edge darker; any colour, the size he starts with
    out = []
    for col in ('color-4', 'color-2', 'color-5'):
        reload(q)
        tap(q, 'tool-marker'); tap(q, col); drag(q, [(200, 300), (900, 300)]); drag(q, [(550, 200), (550, 400)])
        r = q.evaluate("()=>__cb.st.size") ; R = [8, 16, 28, 48, 80][r]
        one, two = shown(q, 300, 300), shown(q, 550, 300)
        prof = [shown(q, 300, 300 + dy) for dy in range(0, R + 1)]
        darkest_edge = min(prof[int(R * 0.6):], key=sum); centre = prof[0]  # darker: less light in all three colours together
        out.append((col, one, two, centre, darkest_edge, sum(one) - sum(two), sum(centre) - sum(darkest_edge)))
    ok = all(c[5] > 0.06 * sum(c[1]) and c[6] > 0.04 * sum(c[3]) for c in out)  # noticed as a share of how light the line is
    report(ok, 'marker: crossings clearly darker and the edge darker, in every colour', '; '.join('%s crossing -%.0f edge -%.0f' % (c[0], c[5], c[6]) for c in out))
FLOWS['marker_real'] = f_marker_real

def f_palettes(q):  # owner 22 Nov 00:21, changed by him 23 Nov 10:27 and 22:37: four columns of 12; column 1 his monochromes with Payne's grey (his hex) between Blue and Purple, then a grey scale
    # in the same steps; column 2 the 5 rainbows, then extras; no row above the columns (Basic is one of the extras); the popup most of the screen
    import csv
    def his(name): return [[[int(h[k:k + 2], 16) for k in (1, 3, 5)] for h in r[1:11]] for r in list(csv.reader(open(GAME.parent / 'lib' / 'owner-palettes' / name)))[1:] if r and "Payne" not in r[0]]
    mono, rainbow = his('monochromatic.csv'), his('rainbow.csv')
    payne = [[int(h[k:k + 2], 16) for k in (1, 3, 5)] for h in "#15283C,#253A4E,#364C62,#495F75,#5D728A,#70879F,#859CB4,#9AB2CA,#AFC7E1,#C5DDF8".split(',')]
    tap(q, 'palette'); time.sleep(0.3); cols = pal_dom(q)
    c = [[p['cols'] for p in col] for col in cols]
    grey = c[0][11] if len(c[0]) > 11 else []
    grey_ok = len(grey) == 10 and all(max(g) - min(g) <= 2 for g in grey) and all(grey[i][0] < grey[i + 1][0] for i in range(9))
    above = q.evaluate("()=>document.querySelectorAll('.palpic .pal').length")
    box = q.evaluate("()=>{const r=document.querySelector('.popbox').getBoundingClientRect();return [r.width/innerWidth,r.height/innerHeight]}")
    ok = [len(x) for x in c] == [12] * 4 and c[0][:7] + c[0][8:11] == mono and c[0][7] == payne and grey_ok  # owner 23 Nov 22:37: Payne's grey between Blue and Purple and c[1][:5] == rainbow and above == 0 and box[0] > 0.8 and box[1] > 0.75
    report(ok, 'palettes: four columns of 12, monochromes then Payne\'s grey and a grey scale, nothing above',
           'columns %s, monochromes his %s, Payne %s, grey scale %s, rainbows %s, above %d, popup %.0f%% x %.0f%%' % ([len(x) for x in c], c[0][:7] + c[0][8:11] == mono, len(c[0]) > 7 and c[0][7] == payne, grey_ok, c[1][:5] == rainbow, above, box[0] * 100, box[1] * 100))
FLOWS['palettes'] = f_palettes

def f_acrylic_scrub(q):  # owner 21 Nov 18:29: a 3rd acrylic brush like the Brusheezy acrylic packs (broad scrubbed strokes breaking into dry streaks), clearly unlike the flat
    n = q.evaluate("()=>__cb.shapes.acrylic.length")
    if n < 4: report(False, 'acrylic: a scrubby 3rd brush unlike the flat', 'only %d acrylic brushes' % n); return
    tap(q, 'tool-acrylic'); tap(q, 'size-3'); tap(q, 'color-6')
    tap(q, 'shape-1'); drag(q, [(200, 300), (1100, 300)])
    tap(q, 'shape-2'); drag(q, [(200, 450), (1100, 450)])
    def paper_share(y0): return q.evaluate("(y0)=>{let n=0,p=0;for(let x=400;x<900;x+=4)for(let y=y0-30;y<=y0+30;y+=3){n++;const c=S(x,y);if(c[0]>150&&c[1]>150)p++;}return p/n}", y0)
    flat, scrub = paper_share(300), paper_share(450)
    report(scrub > flat + 0.12 and scrub < 0.7, 'acrylic: a scrubby 3rd brush unlike the flat', 'paper showing through: flat %.2f, scrub %.2f' % (flat, scrub))
FLOWS['acrylic_scrub'] = f_acrylic_scrub

def f_pastel_smear(q):  # owner 21 Nov 18:29: the crayon is an oil pastel: passing over pastel smears it, carrying its colour along past where it was
    tap(q, 'tool-crayon'); tap(q, 'shape-0'); tap(q, 'size-3'); tap(q, 'color-4')
    drag(q, [(300, 300), (500, 300), (300, 340), (500, 340)])
    tap(q, 'color-6'); drag(q, [(400, 320), (900, 320)])
    avg = "([x0,x1])=>{const s=[0,0,0];let n=0;for(let x=x0;x<x1;x+=3)for(let y=305;y<=335;y+=3){const c=S(x,y);if(c[0]+c[1]+c[2]<600){s[0]+=c[0];s[1]+=c[1];s[2]+=c[2];n++;}}return s.map(v=>Math.round(v/Math.max(1,n)))}"
    near = q.evaluate(avg, [515, 585]); far = q.evaluate(avg, [800, 880])
    report(near[1] - near[2] > far[1] - far[2] + 25, 'oil pastel: dragging through yellow carries yellow along (greener just after it)', 'just past the yellow %s, far from it %s' % (near, far))
FLOWS['pastel_smear'] = f_pastel_smear

def pal_dom(q):  # the popup's columns as they are drawn: per column, per palette, its colours (r,g,b) and its box
    return q.evaluate("()=>[...document.querySelectorAll('.palcols .palcol')].map(c=>[...c.querySelectorAll('.pal')].map(p=>{const r=p.getBoundingClientRect();return {cols:[...p.querySelectorAll('u')].map(u=>getComputedStyle(u).backgroundColor.match(/\\d+/g).map(Number)),box:[r.left,r.top,r.right,r.bottom]}}))")

def f_pal_dividers(q):  # owner 23 Nov: a vertical divider between column 1 (monochromes) and column 2; a horizontal one in column 2 after its 5 rainbows
    tap(q, 'palette'); time.sleep(0.3); cols = pal_dom(q)
    lines = q.evaluate("()=>[...document.querySelectorAll('.paldiv')].map(d=>{const r=d.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]})")
    c1r, c2l = max(p['box'][2] for p in cols[0]), min(p['box'][0] for p in cols[1])
    vert = [l for l in lines if l[3] - l[1] > 5 * (l[2] - l[0]) and c1r <= l[0] and l[2] <= c2l]
    r5, r6 = cols[1][4]['box'], cols[1][5]['box']
    horiz = [l for l in lines if l[2] - l[0] > 5 * (l[3] - l[1]) and r5[3] <= l[1] and l[3] <= r6[1] and l[0] < r5[2] and l[2] > r5[0]]
    report(len(vert) == 1 and len(horiz) == 1, 'palettes: divider after column 1, divider after the 5 rainbows', 'vertical %d, horizontal %d' % (len(vert), len(horiz)))

GROUPS = ['progression', 'two', 'three', 'many']  # the extras' groups, in the order shown (owner 24 Nov 08:50: by hue the way he sees it: one smooth progression, two hues, three, many)
def pal_groups():  # each extra palette's group, by its first colour, from lib/palettes/palettes.txt (shown to him as stripes, 24 Nov)
    out = {}
    for l in (pathlib.Path(__file__).parent.parent / 'lib' / 'palettes' / 'palettes.txt').read_text().splitlines():
        f = [t.strip() for t in l[2:].split('|')] if l[:1] in '234' else []
        if len(f) == 3: out[f[1].split()[0]] = f[2]
    return out

def f_pal_order(q):  # owner 23 Nov 22:37, 24 Nov 08:50 (replacing hues by slices of the colour wheel): the extras (after the rainbows, down column 2, then 3, then 4): one smooth progression, two hues, three, many; Basic is one of them;
    tap(q, 'palette'); time.sleep(0.3); cols = pal_dom(q)  # the green-red Red, Yellow and Green replaces Coral, Citrus and Olive; every row level across the columns
    ex = cols[1][5:] + cols[2] + cols[3]; hexes = ['%02X%02X%02X' % tuple(p['cols'][0]) for p in ex]; g = pal_groups(); h = [GROUPS.index(g[x]) if g.get(x) in GROUPS else -1 for x in hexes]
    back = [(i + 1, h[i], h[i + 1]) for i in range(len(h) - 1) if h[i + 1] < h[i]]
    tops = [[round(p['box'][1]) for p in col] for col in cols]; level = all(abs(tops[k][r] - tops[0][r]) <= 1 for k in range(1, len(tops)) for r in range(min(map(len, tops))))
    ok = len(ex) == 31 and not back and -1 not in h and sorted(set(h)) == [0, 1, 2, 3] and 'F7F7F2' in hexes and 'A50026' in hexes and 'EB5E28' not in hexes and level
    report(ok, 'palettes: extras progression, two, three, many hues; Basic among them, rows level', 'extras %d, a busier group before a simpler one (place, group, next) %s, Basic %s, red-yellow-green %s, coral gone %s, rows level %s'
           % (len(ex), back[:3], 'F7F7F2' in hexes, 'A50026' in hexes, 'EB5E28' not in hexes, level))

def f_pal_picture_only(q):  # owner 23 Nov: a guide picture gives only its own palette, no closest saved palette
    pt = q.evaluate("()=>__cb.btn('guide')")
    with q.expect_file_chooser(timeout=8000) as fc: q.mouse.move(*pt); q.mouse.down(); q.mouse.up()
    fc.value.set_files('owner-shots/2026-11-21-guide-yellow-building.jpg'); time.sleep(2)
    tap(q, 'palette'); time.sleep(0.3); n = q.evaluate("()=>document.querySelectorAll('.palpicg .pal').length")
    report(n == 1, 'palettes: one palette from the guide picture', 'picture palettes %d' % n)

def f_pal_stripes(q):  # owner 23 Nov: each palette one long bar of stripes, palettes closer together and bigger, the popup bigger
    tap(q, 'palette'); time.sleep(0.3); cols = pal_dom(q)
    gaps = q.evaluate("()=>{let m=0;for(const p of document.querySelectorAll('.palcols .pal')){const u=[...p.querySelectorAll('u')].map(e=>e.getBoundingClientRect());for(let i=1;i<u.length;i++)m=Math.max(m,u[i].left-u[i-1].right)}return m}")
    b = cols[1][0]['box']; w, h = b[2] - b[0], b[3] - b[1]; between = cols[1][2]['box'][1] - cols[1][1]['box'][3]
    box = q.evaluate("()=>{const r=document.querySelector('.popbox').getBoundingClientRect();return [r.width/innerWidth,r.height/innerHeight]}")
    report(gaps < 0.5 and w > 3 * h and between < 0.3 * h and box[0] > 0.9 and box[1] > 0.82, 'palettes: stripes on one bar, close together, popup bigger',
           'gap between stripes %.1f, bar %dx%d, space between bars %d, popup %.0f%% x %.0f%%' % (gaps, w, h, between, box[0] * 100, box[1] * 100))

def f_canvas_bigger(q):  # owner 23 Nov: a bigger paper: smaller buckets and gaps; nothing covers the paper
    p = q.evaluate("()=>{const r=document.getElementById('paper').getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]}")
    over = q.evaluate("([l,t,r,b])=>[...document.querySelectorAll('.bar .btn')].filter(e=>!e.classList.contains('hide')).filter(e=>{const k=e.getBoundingClientRect();return k.left<r&&k.right>l&&k.top<b&&k.bottom>t}).length", p)
    report(p[2] - p[0] >= 1111 and over == 0, 'screen: the paper at least 2.5% wider than before (1084 on 1280x800), nothing over it', 'paper %dx%d, buttons over it %d' % (p[2] - p[0], p[3] - p[1], over))

def pots_shown(q): return q.evaluate("()=>[...document.querySelectorAll('#bottom .pot')].filter(e=>!e.classList.contains('hide')).map(e=>e.dataset.id)")
def f_pots_bw(q):  # owner 23 Nov: white and black buckets always in the bottom bar, unless the palette has them (then 10 buckets, else up to 12)
    basic = len(pots_shown(q))
    tap(q, 'palette'); time.sleep(0.3); p = q.evaluate("()=>{const e=document.querySelectorAll('.palcols .palcol')[1].querySelector('.pal').getBoundingClientRect();return [e.left+e.width/2,e.top+e.height/2]}")
    q.mouse.click(*p); time.sleep(0.3); ids = pots_shown(q)
    tap(q, ids[1]); last = q.evaluate("()=>__cb.color()"); tap(q, ids[0]); before = q.evaluate("()=>__cb.color()")  # owner 23 Nov 10:27: they are the first two
    report(basic == 10 and len(ids) == 12 and lum(last) < 25 and lum(before) > 235, 'buckets: white and black added to a palette without them',
           'Basic %d buckets, a rainbow %d, the first two %s %s' % (basic, len(ids), before, last))

def contrast(a, b):  # WCAG contrast ratio of two colours (r, g, b 0-255)
    def L(c): c = [v / 255 for v in c]; c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]; return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    x, y = sorted([L(a), L(b)]); return (y + 0.05) / (x + 0.05)

def f_pot_selected(q):  # owner 23 Nov 10:27 (point 28, replacing "raised"): the chosen bucket is not raised; buckets a bit bigger; the chosen one ringed in a colour that stands out on the brown
    tap(q, 'color-3'); time.sleep(0.2)
    r = q.evaluate("()=>[...document.querySelectorAll('#bottom .pot')].map(e=>{const k=e.getBoundingClientRect(),s=getComputedStyle(e);return [e.classList.contains('on'),k.top+k.height/2,k.height,s.outlineColor.match(/\\d+/g).map(Number),parseFloat(s.outlineWidth),s.outlineStyle]})")
    bar = q.evaluate("()=>getComputedStyle(document.body).backgroundColor.match(/\\d+/g).map(Number)"); b = q.evaluate("()=>parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--b'))")
    on = [x for x in r if x[0]][0]; others = [x for x in r if not x[0]]
    flat = all(abs(x[1] - on[1]) <= 1 for x in others); c = contrast(on[3], bar)  # centres level: not raised
    report(flat and on[2] >= 0.95 * b and on[5] == 'solid' and on[4] >= 4 and c >= 4.5, 'buckets: chosen one level with the rest, bigger, ringed to stand out on the brown',
           'level %s, bucket %d px (tool button %d), ring %s %.0fpx, contrast with the brown %.1f' % (flat, on[2], b, on[3], on[4], c))

def f_pot_on_top(q):  # owner 23 Nov 20:18: the chosen bucket a tiny bit bigger than the others, and its ring overlaps them, never hidden under them
    tap(q, 'color-3'); time.sleep(0.3)
    r = q.evaluate("()=>[...document.querySelectorAll('#bottom .pot')].map(e=>{const k=e.getBoundingClientRect();return [e.classList.contains('on'),k.left,k.right,k.top,k.bottom]})")
    on = [x for x in r if x[0]][0]; other = [x for x in r if not x[0]][0]
    from PIL import Image; import io
    im = Image.open(io.BytesIO(q.screenshot())).convert('RGB'); my = int((on[3] + on[4]) / 2)
    ring = [im.getpixel((int(on[2]) + dx, my)) for dx in range(1, 12)]  # just right of the chosen bucket, towards its neighbour
    shows = sum(1 for c in ring if min(c) > 225)
    bigger = (on[4] - on[3]) / (other[4] - other[3])
    report(1.04 <= bigger <= 1.15 and shows >= 3, 'buckets: chosen one a little bigger, its ring on top of the neighbours', 'size %.2f of the others, ring pixels showing %d' % (bigger, shows))
FLOWS['pot_on_top'] = f_pot_on_top

def f_pots_bw_first(q):  # owner 23 Nov 10:27, point 29: white and black are always the first two buckets, even when the palette has them in another place
    out = []
    for name in ('Basic', 'Standard rainbow', 'Scandi Brick and Slate', 'Teal, Sand and Ember'):
        i = q.evaluate("(n)=>__cb.palIndex(n)", name); tap(q, 'palette'); time.sleep(0.3); tap(q, 'pal-%d' % i); time.sleep(0.1)
        cols = q.evaluate("()=>[...document.querySelectorAll('#bottom .pot')].filter(e=>!e.classList.contains('hide')).map(e=>e.dataset.id)")
        tap(q, cols[0]); w = q.evaluate("()=>__cb.color()"); tap(q, cols[1]); k = q.evaluate("()=>__cb.color()")
        rest = []
        for c in cols[2:]: tap(q, c); rest.append(q.evaluate("()=>__cb.color()"))
        near = [c for c in rest if min(c) > 225 or max(c) < 30]
        out.append((name, lum(w) > 235 and lum(k) < 25 and not near))
    report(all(o for _, o in out), 'buckets: white then black first, never again further on', '%s' % out)
FLOWS.update({'pots_bw_first': f_pots_bw_first})

def f_gallery_guide_hidden(q):  # owner 23 Nov: opening a kept picture that has a guide picture keeps the guide, hidden (the eye shows it)
    pt = q.evaluate("()=>__cb.btn('guide')")
    with q.expect_file_chooser(timeout=8000) as fc: q.mouse.move(*pt); q.mouse.down(); q.mouse.up()
    fc.value.set_files('owner-shots/2026-11-21-guide-yellow-building.jpg'); time.sleep(2)
    tap(q, 'tool-simple'); drag(q, [(50, 100), (300, 100)]); tap(q, 'new'); time.sleep(0.5)
    tap(q, 'gallery'); time.sleep(0.4)
    cards = q.evaluate("()=>[...document.querySelectorAll('#gal .card')].map(c=>{const r=c.getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2,c.classList.contains('cur')]})")
    old = [c for c in cards if not c[2]]; q.mouse.click(old[0][0], old[0][1]); time.sleep(0.8)
    hidden = q.evaluate("()=>document.getElementById('guide').classList.contains('hide')")
    tap(q, 'guide'); time.sleep(0.2); tap(q, 'guide-show'); time.sleep(0.2)
    shows = q.evaluate("()=>!document.getElementById('guide').classList.contains('hide')")
    report(hidden and shows, 'gallery: a kept picture opens with its guide picture hidden, the eye shows it', 'hidden on open %s, shown after the eye %s' % (hidden, shows))
FLOWS.update({'pal_dividers': f_pal_dividers, 'pal_order': f_pal_order, 'pal_picture_only': f_pal_picture_only, 'pal_stripes': f_pal_stripes, 'canvas_bigger': f_canvas_bigger,
              'pots_bw': f_pots_bw, 'pot_selected': f_pot_selected, 'gallery_guide_hidden': f_gallery_guide_hidden})

def drag_screen(q, s, step=9):  # screen points, at a finger's speed (step screen pixels per 16 ms)
    q.mouse.move(*s[0]); q.mouse.down()
    for (x0, y0), (x1, y1) in zip(s, s[1:]):
        n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) / step))
        for i in range(1, n + 1): q.mouse.move(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.1)

def f_start_outside(q):  # owner 23 Nov: a stroke can start beside the paper and come in, painting from the edge on
    tap(q, 'tool-simple'); tap(q, 'color-6')
    top = q.evaluate("()=>document.getElementById('paper').getBoundingClientRect().top"); x, _ = scr(q, 200, 0); _, y1 = scr(q, 200, 150)
    drag_screen(q, [(x, top - 5), (x, y1)])
    ys = [2, 20, 60, 120]; got = [round(lum(shown(q, 200, y))) for y in ys]
    report(all(v < 120 for v in got), 'stroke started above the paper paints from its edge in', 'brightness down the line at %s: %s' % (ys, got))

def widths_along(q, xs, y, half=30, dark=150, dxs=(0,)):  # width_across at every x of a row, in one call (one call per place made a row take seconds); each the widest of the dxs beside it
    return q.evaluate("([xs,y,h,k,ds])=>xs.map(x=>Math.max(...ds.map(d=>{let n=0;for(let i=-h;i<=h;i++){const c=S(x+d,y+i);if(0.3*c[0]+0.59*c[1]+0.11*c[2]<k)n++}return n})))", [list(xs), y, half, dark, list(dxs)])

def width_across(q, cx, cy, ux, uy, half=60, dark=150):  # painted pixels (darker than dark) along the line through (cx, cy) in direction (ux, uy)
    return q.evaluate("([cx,cy,ux,uy,h,k])=>{let n=0;for(let i=-h;i<=h;i++){const c=S(cx+ux*i,cy+uy*i);if(0.3*c[0]+0.59*c[1]+0.11*c[2]<k)n++}return n}", [cx, cy, ux, uy, half, dark])

def f_turn(q):  # owner 23 Nov: a switch in the brush popup: brushes turn with the stroke; off, a flat brush stays at its one angle (owner 21 Nov)
    tap(q, 'tool-marker'); tap(q, 'shape-1'); tap(q, 'size-3'); tap(q, 'color-6')
    def pair(x0):  # strokes down-right and up-right; widths across each
        drag(q, [(x0, 30), (x0 + 80, 110)]); drag(q, [(x0, 220), (x0 + 80, 140)])
        return width_across(q, x0 + 40, 70, 0.7071, -0.7071, 90), width_across(q, x0 + 40, 180, 0.7071, 0.7071, 90)
    fixed = pair(40); tap(q, 'brush'); time.sleep(0.1); tap(q, 'turn'); turned = pair(240)
    rf, rt = max(fixed) / max(1, min(fixed)), max(turned) / max(1, min(turned))
    report(rf > 1.5 and rt < 1.2, 'brush turns with the stroke when switched on', 'widths of the two directions: one angle %s, turning %s' % (fixed, turned))

def f_speed_pressure(q):  # owner 23 Nov: with a finger or the mouse, a slower stroke presses harder (a fast one is lighter and narrower)
    tap(q, 'tool-simple'); tap(q, 'size-3'); tap(q, 'color-6')
    drag(q, [(40, 70), (360, 70)], step=400, per_move=True); drag(q, [(40, 180), (360, 180)], step=2, per_move=True)  # one move after another: the slow test browser spaces them out
    fast, slow = [round(lum(across(q, 300, y, 6))) for y in (70, 180)]
    report(slow < fast - 8, 'slower strokes press harder', 'brightness in the middle of the line: fast %d, slow %d' % (fast, slow))
FLOWS.update({'start_outside': f_start_outside, 'turn': f_turn, 'speed_pressure': f_speed_pressure})

def f_new_tools(q):  # owner 23 Nov: new drawing tools: spray, shapes, ink, pencil; each paints where it is drawn
    got = {}
    for k, t in enumerate(('spray', 'shapes', 'ink', 'pencil')):
        tap(q, 'tool-' + t); tap(q, 'size-2'); tap(q, 'color-6'); y = 35 + 60 * k
        drag(q, [(40, y), (360, y)]); got[t] = round(lum(across(q, 200, y, 10)))
    report(all(v < (238 if t == 'spray' else 200) for t, v in got.items()), 'new drawing tools paint', 'brightness on each stroke %s' % got)  # spray: loose drops, as far apart at every size (owner 24 Nov), so a small size is light

def f_shapes_vary(q):  # owner 23 Nov: shape stamps along the stroke, each a slightly different colour from the chosen one
    tap(q, 'tool-shapes'); tap(q, 'shape-1'); tap(q, 'size-2'); tap(q, 'color-2'); drag(q, [(30, 125), (370, 125)])
    cols = q.evaluate("()=>{const o=[];for(let x=30;x<370;x+=2){const c=S(x,125);if(c[0]>120&&c[1]<120)o.push(c)}return o}")
    reds = sorted(set(c[0] for c in cols)); spread = (reds[-1] - reds[0]) if reds else 0
    report(len(cols) > 40 and spread >= 12, 'shapes: stamps vary a little in colour', 'red stamp pixels %d, red channel from %s to %s' % (len(cols), reds[:1], reds[-1:]))

def f_pencil_grain(q):  # owner 23 Nov: a drawing pencil: colour only on the paper's raised grain, so paper shows through; harder (fuller bucket) is darker
    tap(q, 'tool-pencil'); tap(q, 'shape-1'); tap(q, 'size-3'); tap(q, 'color-6'); hold(q, 'color-6', 0.6)
    drag(q, [(30, 70), (370, 70)]); tap(q, 'color-6'); drag(q, [(30, 180), (370, 180)])
    def light(y): return q.evaluate("(y)=>{let n=0,t=0;for(let x=60;x<340;x+=2)for(let j=-4;j<=4;j+=2){const c=S(x,y+j);t++;if(0.3*c[0]+0.59*c[1]+0.11*c[2]>200)n++}return n/t}", y)
    soft, hard = light(70), light(180)
    report(0.15 < soft < 0.9 and hard < soft - 0.1, 'pencil: paper shows through, pressing harder covers more', 'paper showing: light %.0f%%, hard %.0f%%' % (soft * 100, hard * 100))

def f_ink_speed(q):  # owner 23 Nov: an ink pen: a slow line is wider than a fast one
    tap(q, 'tool-ink'); tap(q, 'size-3'); tap(q, 'color-1')
    drag(q, [(40, 70), (360, 70)], step=400, per_move=True); drag(q, [(40, 180), (360, 180)], step=2, per_move=True)
    fast, slow = width_across(q, 300, 70, 0, 1, 50), width_across(q, 300, 180, 0, 1, 50)
    report(slow > fast * 1.5, 'ink: slow lines wider than fast', 'width fast %d, slow %d' % (fast, slow))
FLOWS.update({'new_tools': f_new_tools, 'shapes_vary': f_shapes_vary, 'pencil_grain': f_pencil_grain, 'ink_speed': f_ink_speed})

def f_simple_self_cross(q):  # owner 23 Nov 10:27, point 1: simple tool, blurry brush, ONE stroke that crosses itself: the crossing must not spoil the line (no X-shaped crease where it crosses)
    tap(q, 'tool-simple'); tap(q, 'blur-0'); tap(q, 'size-3'); tap(q, 'color-2')
    drag(q, [(500, 450), (500, 200), (800, 200), (800, 300), (300, 300)])  # one stroke: up, right, down, then back left across its own start
    paper, full = lum(shown(q, 650, 400)), lum(shown(q, 380, 300))
    def cov(x, y): return (paper - lum(shown(q, x, y))) / max(1, paper - full)
    rows = []
    for o in range(8, 40, 2):
        line = (cov(380, 300 + o) + cov(380, 300 - o) + cov(500 + o, 400) + cov(500 - o, 400)) / 4  # the line alone, o pixels from its middle
        corner = min(cov(500 + sx * o, 300 + sy * o) for sx in (-1, 1) for sy in (-1, 1))            # the crossing's corners, o pixels from the middle both ways
        if 0.25 < line < 0.7: rows.append((o, round(line, 2), round(corner, 2)))
    ok = rows and all(c >= l + l * (1 - l) / 3 for _, l, c in rows)  # a crease: the corner no darker than the line; round: at least a third of what a second line adds there
    report(ok, 'simple soft brush: a stroke crossing itself has round corners', '(offset, line, corner) %s' % ([r for r in rows if r[2] < r[1] + r[1] * (1 - r[1]) / 3][:4] or rows[:3]))
FLOWS['simple_self_cross'] = f_simple_self_cross

def f_turn_every(q):  # owner 23 Nov 10:27, point 15: he cannot make the turn switch work: switched on, every drawing tool's flat brush turns with the stroke, so a line is as wide going down-right as up-right
    tools = [('acrylic', 1), ('water', 1), ('crayon', 1), ('marker', 1), ('simple', 1), ('ink', 1), ('pencil', 2)]
    tap(q, 'tool-marker'); tap(q, 'brush'); time.sleep(0.1); tap(q, 'turn')  # his steps: open the brush popup, press the turn switch
    out, bad = [], []
    for i, (t, sh) in enumerate(tools):
        x0, y0 = 60 + (i % 4) * 380, 60 + (i // 4) * 420
        tap(q, 'tool-' + t); tap(q, 'shape-%d' % sh); tap(q, 'size-2'); tap(q, 'color-1')
        drag(q, [(x0, y0), (x0 + 200, y0 + 200)]); drag(q, [(x0, y0 + 360), (x0 + 200, y0 + 160)])
        if t == 'water': wait_dry(q)
        a, b = width_across(q, x0 + 100, y0 + 100, 0.7071, -0.7071, 60), width_across(q, x0 + 100, y0 + 260, 0.7071, 0.7071, 60)
        out.append('%s %d/%d' % (t, a, b))
        if not (a > 2 and b > 2 and max(a, b) / min(a, b) < 1.3): bad.append(t)
    report(not bad and q.evaluate("()=>__cb.st.turn"), 'turn switch: every flat brush turns with the stroke', 'not turning: %s; widths down-right/up-right: %s' % (bad, ', '.join(out)))
FLOWS['turn_every'] = f_turn_every
PAPER['turn_every'] = ('1600x1000', (0, 0))

def flick(q, x0, x1, y, v0=550, v1=4000):  # a quick flick: starts at his usual speed (paper pixels a second), speeds up evenly, and leaves the screen still moving fast.
    L = x1 - x0; a = (v1 * v1 - v0 * v0) / (2 * L); T = (v1 - v0) / a     # Moves 16 ms apart, as his screen sends them, each stamped with its own time: the page
    cdp = q.context.new_cdp_session(q); t0 = time.time()                   # reads the speed from those times, so a slow test browser draws the same stroke he would.
    def ev(typ, t, extra={}):
        x, yy = scr(q, x0 + v0 * t + a * t * t / 2, y)
        cdp.send('Input.dispatchMouseEvent', dict({'type': typ, 'x': x, 'y': yy, 'button': 'left', 'buttons': 1, 'timestamp': t0 + t}, **extra))
    ev('mousePressed', 0, {'clickCount': 1}); t = 0.016
    while t < T: ev('mouseMoved', t); t += 0.016
    ev('mouseReleased', t - 0.016, {'clickCount': 1}); cdp.detach(); time.sleep(0.1)

def f_flick_lifts(q):  # owner 23 Nov 10:27, point 16: speed works like lifting the brush: a quick flick starts at normal width and thins until it disappears, for every drawing tool
    tools = ['acrylic', 'water', 'crayon', 'marker', 'simple', 'spray', 'shapes', 'ink', 'pencil']
    out, bad = [], []; tap(q, 'lift')  # lifting is a switch, off at the start (owner 24 Nov)
    for i, t in enumerate(tools):
        y = 60 + i * 105
        tap(q, 'tool-' + t); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-1')
        flick(q, 100, 1500, y, v1=4500)  # 550 px/s at 100, 2000 at 430, 3200 at 800, 4500 at 1500 (owner 24 Nov: lifting starts later and is slower, so a flick runs longer)
        if t == 'water': wait_dry(q)
        def w(x): return max(width_across(q, x + dx, y, 0, 1, 45) for dx in (-6, -3, 0, 3, 6)) if t != 'spray' else sum(width_across(q, x + dx, y, 0, 1, 45) for dx in range(-20, 21, 2))  # spray is loose drops: all its paint across a band
        start, mid, end = w(130), w(1000), w(1450)  # owner 23 Nov 20:18: lifting starts once the hand is fast and takes a few centimetres (24 Nov: more of them)
        out.append('%s %d>%d>%d' % (t, start, mid, end))
        if not (start >= 6 and mid < start * 0.8 and end == 0): bad.append(t)
    report(not bad, 'a quick flick thins out and disappears, every drawing tool', 'wrong: %s; widths start>middle>end: %s' % (bad, ', '.join(out)))
FLOWS['flick_lifts'] = f_flick_lifts
PAPER['flick_lifts'] = ('1600x1000', (0, 0))

def jerk(q, x0, x1, y, v):  # a jerk: from rest straight to speed v (paper pixels a second), moves 16 ms apart with their own times, let go while moving
    cdp = q.context.new_cdp_session(q); t0 = time.time()
    def ev(typ, t, x, extra={}):
        X, Y = scr(q, x, y); cdp.send('Input.dispatchMouseEvent', dict({'type': typ, 'x': X, 'y': Y, 'button': 'left', 'buttons': 1, 'timestamp': t0 + t}, **extra))
    ev('mousePressed', 0, x0, {'clickCount': 1}); t = 0.016
    while x0 + v * t < x1: ev('mouseMoved', t, x0 + v * t); t += 0.016
    ev('mouseReleased', t - 0.016, x0 + v * (t - 0.016), {'clickCount': 1}); cdp.detach(); time.sleep(0.15)

def f_jerk_tail(q):  # owner 23 Nov 20:18: a jerk lifts the brush fast and leaves a smoothly thinned line (no beads, no rings); a smaller jerk leaves a longer line
    out, bad = [], []; tap(q, 'lift')  # lifting is a switch, off at the start (owner 24 Nov)
    for i, t in enumerate(['acrylic', 'water', 'crayon', 'marker', 'simple', 'ink', 'pencil']):
        tap(q, 'tool-' + t); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-1')
        if t == 'ink': tap(q, 'splash-0')  # its splash drops would land on the next rows
        lens = []
        for k, v in enumerate((3600, 3000)):  # a hand finishing a line fast: about 1 m/s, a smaller jerk about 85 cm/s (his screen about 36 px a cm; owner 24 Nov: below 55 cm/s it no longer lifts)
            y = 70 + i * 130 + k * 60
            jerk(q, 100, 1500, y, v)
            if t == 'water': wait_dry(q)
            ws = widths_along(q, range(110, 1500, 4), y, 30, 215 if t == 'pencil' else 150, (-4, 0, 4))  # a fast pencil line is light grey (about 145), not dark; the widest of three beside each place (the pastel's lumps and grain)
            end = max([j for j, w in enumerate(ws) if w > 0] or [0])
            gaps = [j for j in range(1, int(end * 0.9)) if max(ws[j - 1:j + 2]) == 0]  # a stretch with nothing, before the tip (grain alone leaves no 12 px hole)
            grows = [j for j in range(8, end) if ws[j] > max(ws[j - 8:j]) + 3]
            lens.append(end * 4)
            if gaps or grows or end * 4 > 1300: bad.append('%s %d: gaps %d, widens %d, length %d' % (t, v, len(gaps), len(grows), end * 4))
        if not lens[0] < lens[1]: bad.append('%s: bigger jerk not shorter %s' % (t, lens))
        out.append('%s %s' % (t, lens))
    report(not bad, 'a jerk leaves a smooth thinning tail, shorter for a bigger jerk', '%s; tail lengths %s' % (bad[:4], ', '.join(out)))
FLOWS['jerk_tail'] = f_jerk_tail
PAPER['jerk_tail'] = ('1600x1000', (0, 0))

def f_previews_drawn(q):  # owner 23 Nov 20:18: some brush pictures in the brush popup are black boxes: every brush picture, on every canvas, shows paper with a stroke on it
    bad = q.evaluate("""async()=>{const out=[];for(const [cv,m] of Object.entries(__cb.previews))for(const [k,src] of Object.entries(m)){
      const im=new Image();im.src=src;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const x=c.getContext('2d');x.drawImage(im,0,0);
      const d=x.getImageData(0,0,c.width,c.height).data;let lo=255,hi=0,sum=0;for(let i=0;i<d.length;i+=4){const l=(d[i]+d[i+1]+d[i+2])/3;lo=Math.min(lo,l);hi=Math.max(hi,l);sum+=l}
      const mean=sum/(d.length/4);if(mean<150||hi-lo<60)out.push(cv+':'+k)}return out}""")
    report(not bad, 'brush pictures: paper with a stroke, none black or empty', 'bad: %d %s' % (len(bad), bad[:8]))
FLOWS['previews_drawn'] = f_previews_drawn

LOOKS = GAME.parent / 'tools' / 'looks'  # one saved picture per brush: how its normal stroke looked when the owner last saw it
def brush_jobs(q):
    n = q.evaluate("()=>Object.fromEntries(Object.entries(__cb.shapes).map(([t,v])=>[t,v.length]))")
    return [(t, i) for t in ('acrylic', 'water', 'crayon', 'marker', 'simple', 'spray', 'shapes', 'ink', 'pencil') for i in range(n[t])]
def brush_strokes(q):  # every drawing tool and brush, one stroke each at his usual speed, run dry; returns {name: picture}
    from PIL import Image; import io
    jobs = brush_jobs(q); out = {}
    for k, (t, i) in enumerate(jobs):
        x, y = 30 + (k % 4) * 400, 60 + (k // 4) * 125
        tap(q, 'tool-' + t); tap(q, 'shape-%d' % i); tap(q, 'size-1'); tap(q, 'color-6'); jerk(q, x, x + 330, y, 550)
    wait_dry(q)
    for k, (t, i) in enumerate(jobs):
        x, y = 10 + (k % 4) * 400, (k // 4) * 125; a, b = scr(q, x, y), scr(q, x + 380, y + 120)
        out['%s-%d' % (t, i)] = Image.open(io.BytesIO(q.screenshot(clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]}))).convert('L')
    return out

def f_brush_looks(q):  # owner 23 Nov 20:11: a change must not alter how any brush looks unless that brush was meant to change: every brush's normal stroke matches its saved picture
    from PIL import ImageChops, ImageStat
    pics = brush_strokes(q); bad = []
    for k, im in pics.items():
        f = LOOKS / (k + '.png')
        if not f.exists(): bad.append(k + ' (no saved picture)'); continue
        from PIL import Image; ref = Image.open(f).convert('L').resize(im.size)
        from PIL import ImageFilter; blur = ImageFilter.GaussianBlur(4)  # spray and grain are random dot by dot: compare the look, not each dot
        d = ImageStat.Stat(ImageChops.difference(im.filter(blur), ref.filter(blur))).mean[0]
        if d > (8 if k.startswith(('spray', 'ink')) else 4): bad.append('%s %.1f' % (k, d))  # spray's drops and ink's hairs fall at random
    report(not bad, 'every brush looks as saved (tools/looks.py saves them after he approves a look)', 'changed: %s' % bad[:8])
FLOWS['brush_looks'] = f_brush_looks
PAPER['brush_looks'] = ('1600x1000', (0, 0))

def f_spray_real(q):  # owner 23 Nov 10:27, point 3: spray must work like other painting software's spray (airbrush): droplets scattered at random, of different sizes,
    tap(q, 'tool-spray'); tap(q, 'shape-0'); tap(q, 'size-3'); tap(q, 'color-1')  # thickest in the middle and thinning out, and building up while held still
    from PIL import Image; import io
    def cov(cx, cy, r0, r1):  # share of paper darkened between two distances from a point
        a, b = scr(q, cx - 70, cy - 70), scr(q, cx + 70, cy + 70); im = Image.open(io.BytesIO(q.screenshot(clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]}))).convert('L')
        sx = im.width / 140; n = k = 0
        for y in range(im.height):
            for x in range(im.width):
                d = math.hypot(x / sx - 70, y / sx - 70)
                if r0 <= d < r1: n += 1; k += im.getpixel((x, y)) < 150
        return k / max(1, n)
    x, y = scr(q, 400, 300); q.mouse.move(x, y); q.mouse.down(); time.sleep(0.25); early = cov(400, 300, 0, 15); time.sleep(1.0); late = cov(400, 300, 0, 15); q.mouse.up()
    mid, outer = cov(400, 300, 15, 30), cov(400, 300, 40, 55)
    a, b = scr(q, 600, 250), scr(q, 640, 350)  # droplets of different sizes: a short stroke, its dark spots measured one by one
    drag(q, [(620, 230), (620, 370)], step=30)
    im = Image.open(io.BytesIO(q.screenshot(clip={'x': a[0], 'y': a[1], 'width': b[0] - a[0], 'height': b[1] - a[1]}))).convert('L')
    px = im.load(); seen = set(); sizes = []
    for yy in range(im.height):
        for xx in range(im.width):
            if px[xx, yy] < 150 and (xx, yy) not in seen:
                st_, n = [(xx, yy)], 0; seen.add((xx, yy))
                while st_:
                    u, v = st_.pop(); n += 1
                    for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        w = (u + du, v + dv)
                        if 0 <= w[0] < im.width and 0 <= w[1] < im.height and w not in seen and px[w] < 150: seen.add(w); st_.append(w)
                sizes.append(n)
    sizes = [s for s in sizes if s < 60] or [0]; m = sum(sizes) / len(sizes); sd = (sum((s - m) ** 2 for s in sizes) / len(sizes)) ** 0.5
    ok = late > early * 1.3 and early > 0.02 and mid < late and outer < mid * 0.7 and len(sizes) > 10 and sd / max(m, 1e-6) > 0.5
    report(ok, 'spray: random droplets of many sizes, thinning outwards, building up while held', 'held 0.25 s %.2f, 1.25 s %.2f; middle ring %.2f, outer %.2f; droplets %d, size spread %.2f' % (early, late, mid, outer, len(sizes), sd / max(m, 1e-6)))
FLOWS['spray_real'] = f_spray_real
PAPER['spray_real'] = ('500x300', (250, 150))

def f_shapes_speed(q):  # owner 23 Nov 10:27, point 4: shapes work like the Squares Brush (av01d fabric-brushes): moving speed sets the size, faster is bigger, turned with the motion
    tap(q, 'tool-shapes'); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-1')
    jerk(q, 30, 370, 60, 200); jerk(q, 30, 370, 180, 900)
    def size(y): return sum(width_across(q, x, y, 0, 1, 55) for x in range(80, 330, 5)) / 50
    slow, fast = size(60), size(180)
    report(fast > slow * 1.6 and slow > 3, 'shapes: faster is bigger', 'average size slow %.0f, fast %.0f' % (slow, fast))
FLOWS['shapes_speed'] = f_shapes_speed

def f_ink_strands(q):  # owner 23 Nov 10:27, point 5: ink like the av01d fabric-brushes ink: a fast stroke throws splash drops; how many is a setting (none, few, some, many)
    tap(q, 'tool-ink'); tap(q, 'shape-0'); tap(q, 'size-3'); tap(q, 'color-1')
    def splashes(y0):  # dark spots well away from the stroke's middle line
        return q.evaluate("(y0)=>{let n=0;for(let x=60;x<540;x+=3)for(const dy of [-55,-45,45,55]){const c=S(x,y0+dy);if(0.3*c[0]+0.59*c[1]+0.11*c[2]<150)n++}return n}", y0)
    tap(q, 'splash-0'); jerk(q, 40, 560, 80, 2600); none = splashes(80)
    tap(q, 'splash-1'); jerk(q, 40, 560, 220, 2600); few = splashes(220)
    tap(q, 'splash-3'); jerk(q, 40, 560, 360, 2600); many = splashes(360)
    report(none == 0 and many >= 4 and many > few, 'ink: fast strokes splash, as many as the setting says', 'splash spots with none %d, few %d, many %d' % (none, few, many))
FLOWS['ink_strands'] = f_ink_strands
PAPER['ink_strands'] = ('600x450', (0, 0))

def f_lift_switch(q):  # owner 24 Nov 08:50, point 2: a switch in the brush popup, whether speed lifts the brush; off at the start
    tap(q, 'tool-acrylic'); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-1')
    def ends(y): return [max(width_across(q, x + dx, y, 0, 1, 45) for dx in (-6, 0, 6)) for x in (130, 1450)]
    flick(q, 100, 1500, y=120, v1=4500); off = ends(120)
    tap(q, 'lift'); flick(q, 100, 1500, y=300, v1=4500); on = ends(300)
    ok = off[1] >= off[0] * 0.6 and on[1] == 0 and on[0] > 0  # off: only narrower from speed's lighter press
    report(ok, 'lift switch: off at start, a flick stays on the paper; on, it lifts off', 'widths start, end: off %s, on %s' % (off, on))
FLOWS['lift_switch'] = f_lift_switch
PAPER['lift_switch'] = ('1600x450', (0, 0))

def f_long_lift(q):  # owner 24 Nov 08:50, point 1: he cannot make long lifts, the lift happens too fast (and too early, point 5): a fast hand (about 85 cm/s) thins over a long stretch; a quickish one (50 cm/s) stays down
    tap(q, 'tool-acrylic'); tap(q, 'shape-0'); tap(q, 'size-2'); tap(q, 'color-1'); tap(q, 'lift')
    def w(x, y): return max(width_across(q, x + dx, y, 0, 1, 45) for dx in (-6, 0, 6))
    jerk(q, 100, 1500, 150, 3000); fast = [w(x, 150) for x in (150, 600)]; end = max([x for x in range(150, 1500, 10) if w(x, 150) > 0] or [0])
    jerk(q, 100, 1500, 350, 1800); calm = [w(x, 350) for x in (150, 1300)]
    ok = 0 < fast[1] < fast[0] * 0.85 and end > 900 and calm[1] >= calm[0] * 0.8
    report(ok, 'long lift: a fast hand thins over a long stretch, a quickish one stays down', 'fast: widths %s, last paint at %d; 50 cm/s: widths %s' % (fast, end, calm))
FLOWS['long_lift'] = f_long_lift
PAPER['long_lift'] = ('1600x500', (0, 0))

def f_spray_sizes(q):  # owner 24 Nov 08:50, point 4: smaller spray sizes put the drops closer together: every size sprays its drops equally far apart
    tap(q, 'tool-spray'); tap(q, 'shape-0'); tap(q, 'color-1'); out = []
    for i, (x0, R) in enumerate(((60, 8), (130, 16), (230, 28), (380, 48))):
        tap(q, 'size-%d' % i); tap(q, 'color-1'); r = int(R * 0.7); got = []
        for y0 in (60, 150, 240):  # three puffs of 0.3 s each, averaged (a small size gets only a drop or two a puff)
            x, y = scr(q, x0, y0); q.mouse.move(x, y); q.mouse.down(); time.sleep(0.3); q.mouse.up(); time.sleep(0.1)
            got.append(q.evaluate("([x0,y0,r])=>{let n=0,k=0;for(let dy=-r;dy<=r;dy++)for(let dx=-r;dx<=r;dx++){if(dx*dx+dy*dy>r*r)continue;k++;const c=S(x0+dx,y0+dy);if(0.3*c[0]+0.59*c[1]+0.11*c[2]<200)n++}return n/k}", [x0, y0, r]))
        out.append(sum(got) / 3)
    report(max(out) < min(out) * 1.6 and min(out) > 0, 'spray: drops as far apart at every size', 'share of the middle painted, small to big %s' % ['%.2f' % v for v in out])
FLOWS['spray_sizes'] = f_spray_sizes
PAPER['spray_sizes'] = ('500x300', (0, 0))

def f_shapes_tap_start(q):  # owner 24 Nov 08:50, point 5: a single tap makes a tiny shape, not the size his usual speed makes; he cannot start a shapes line small (what he did there is unknown: here a slow start)
    tap(q, 'tool-shapes'); tap(q, 'shape-0'); tap(q, 'size-1'); tap(q, 'color-1')
    def wd(x, y): return max(width_across(q, x + dx, y, 0, 1, 30, 200) for dx in range(-12, 13, 3))  # within the paper (past its edge reads black)
    jerk(q, 40, 360, 50, 550); usual = wd(200, 50)
    x, y = scr(q, 100, 125); q.mouse.click(x, y); time.sleep(0.1); dot = wd(100, 125)
    glide(q, lambda d: (40 + d, 200), 320, 120, 900); start, later = wd(55, 200), wd(330, 200)
    ok = dot >= usual * 0.7 and 0 < start < later * 0.5
    report(ok, 'shapes: a tap is the usual size; a slow start is small', 'across: usual speed %d, tap %d; slow start %d, fast later %d' % (usual, dot, start, later))
FLOWS['shapes_tap_start'] = f_shapes_tap_start

def f_shapes_brushes(q):  # owner 24 Nov 08:50, point 5: the brush pictures all show a dot, not the shape; a normal star and heart, and grass
    tap(q, 'tool-shapes'); tap(q, 'brush'); time.sleep(0.15)
    sig = q.evaluate("""()=>[...document.querySelectorAll('[data-id^="shape-"]')].map(b=>{const c=b.querySelector('canvas'),g=c.getContext('2d'),w=c.width,h=c.height,d=g.getImageData(0,0,w*0.48|0,h*0.48|0).data,W=w*0.48|0,H=h*0.48|0;let s='';
        for(let j=0;j<8;j++)for(let i=0;i<8;i++){const x=(i+0.5)*W/8|0,y=(j+0.5)*H/8|0,k=(y*W+x)*4;s+=d[k+3]>128&&d[k]<120?'1':'0'}return s})""")
    ids = q.evaluate("()=>__cb.shapes.shapes.map(s=>s.id)")
    ok = ids == ['square', 'circle', 'triangle', 'star', 'heart', 'grass'] and len(sig) == 6 and len(set(sig)) == 6
    report(ok, 'shapes: brushes square, circle, triangle, star, heart, grass, each pictured as its shape', 'brushes %s, different pictures %d of %d' % (ids, len(set(sig)), len(sig)))
FLOWS['shapes_brushes'] = f_shapes_brushes
