# The whole-game test (owner 24 Nov): one run that plays the game in its own order, the way the child plays it, on one page:
# the start and the map, the first site with every lesson of its tutorial, the test, the finished site, a damaged site, the
# second site and its demo, the boats and stones on the map, then the restart and the first site again with the ticks off.
# Every owner rule and bug report is a checked step at the place in the game where it happens; each prints PASS or FAIL.
# Only what the child does: taps, drags, two-finger touches and keys on what is drawn, at a hand's rate. Never the Ctrl quick
# build, never the Ctrl fast test, never a line cut off or a state set from inside the game (owner 24 Nov: "NEVER").
# The page is read to find where things are drawn, what is heard and what is shown, never written.
# Run: python3 tools/harness.py flows      (STOP=<step name> ends the run after that step, while working on a step)
import time, math, os
import tempfile; TMP = tempfile.gettempdir()  # the commit gate runs old and new code at once, each with its own TMPDIR

# --------------------------------------------------------------------
# SECTION: HELPERS -- the page, waiting, what is heard and drawn, the mouse and fingers, pile pieces, building by hand
# --------------------------------------------------------------------
def page(b):  # a fresh game: nothing saved
    q = b.new_page(viewport={'width': 1280, 'height': 800})
    q.goto('file://' + TMP + '/tb-real.html')
    q.evaluate("()=>{try{localStorage.clear()}catch(e){}}")
    q.reload(); q.wait_for_function("()=>!!window.__tb")
    listen(q)
    return q

def listen(q):  # from now on, in the page: every line heard (number, start, end), every sound asked for, the test's parts, the music's share in a test, the headpiece's outline drawn while a headpiece is on
    q.evaluate("""()=>{const T=__tb; window.__rec={lines:[],snd:[],ph:[],duck:[],ghost:0};
      const L=T.soundLog, push=L.push; L.push=function(...a){ for(const x of a) __rec.snd.push([T.clock*1000,x]); return push.apply(this,a); };
      const g=T.SKIN.loadGhost; T.SKIN.loadGhost=function(...a){ if(T.loads.length&&!T.test) __rec.ghost++; return g.apply(this,a); };
      let ln=null, ph=null;
      const f=()=>{const t=T.clock*1000, c=T.voice.cur, n=c?c.n:null, p=T.test?T.test.phase:null;
        if(n!==ln){ if(ln!=null) __rec.lines[__rec.lines.length-1][2]=t; if(n!=null) __rec.lines.push([n,t,null]); ln=n; }
        if(p!==ph){ __rec.ph.push([p,t]); ph=p; } if(T.test) __rec.duck.push(T.musicDuck); requestAnimationFrame(f);};
      requestAnimationFrame(f);}""")

def until(q, js, secs, step=0.05):  # wait until js is true in the page; False if it never is within secs
    end = time.time() + secs
    while time.time() < end:
        if q.evaluate(js): return True
        time.sleep(step)
    return False

def mark(q): return q.evaluate("()=>[__rec.lines.length, __rec.snd.length, __rec.ph.length, __rec.duck.length]")
def heard(q, since=None): return q.evaluate("(m)=>__rec.lines.slice(m?m[0]:0)", since)  # [line, start ms, end ms or None]
def said(q, since=None): return [l[0] for l in heard(q, since)]
def sounds(q, since=None): return q.evaluate("(m)=>__rec.snd.slice(m?m[1]:0)", since)  # [ms, name]
def now_ms(q): return q.evaluate("()=>__tb.clock*1000")  # game time
def line_now(q): return q.evaluate("()=>__tb.voice.cur?__tb.voice.cur.n:null")
def hear(q, n, secs, since=None): return until(q, "(m=>__rec.lines.slice(m?m[0]:0).some((l)=>l[0]===%d))(%s)" % (n, 'null' if since is None else list(since)), secs)
def hear_end(q, n, secs, since=None): return until(q, "(m=>__rec.lines.slice(m?m[0]:0).some((l)=>l[0]===%d&&l[2]))(%s)" % (n, 'null' if since is None else list(since)), secs)
def silent(q, secs=8): return until(q, "()=>!__tb.voice.cur&&!__tb.voice.queue.length", secs)  # waits for the voice to finish by itself
def mode(q): return q.evaluate("()=>__tb.mode")
def wait_game(q, secs):  # waits until the game's own time has moved on by secs (the test page runs the game faster than real time)
    c0 = q.evaluate("()=>__tb.clock"); until(q, "()=>__tb.clock>=%f" % (c0 + secs), secs + 1)

def button(q, bid):  # a screen button's middle, by its id, where it is drawn
    return q.evaluate("(id)=>{const b=__tb.screenButtons().find((x)=>x.id===id); if(!b) return null; return b.rect?[b.rect.x+b.rect.w/2,b.rect.y+b.rect.h/2]:[b.x,b.y];}", bid)

def click(q, bid):
    p = button(q, bid)
    if not p: return False
    q.mouse.click(p[0], p[1]); time.sleep(0.05); return True

def drag(q, a, b, steps=20, hold=0):  # a real mouse drag, at about the rate a hand moves; hold: seconds kept still at the end
    q.mouse.move(a[0], a[1]); q.mouse.down(); time.sleep(0.05)
    for k in range(1, steps + 1): q.mouse.move(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps); time.sleep(0.015)
    if hold: time.sleep(hold)
    q.mouse.up(); time.sleep(0.05)

def held_at(q, pt, px=15):  # the held piece hangs still at the hand (a heavy one comes slowly)
    return "(()=>{const b=%s, T=__tb, p=T.pieces.find((x)=>x.heldBy!=null); if(!p) return true; const c=p.body.getPosition(), s=T.worldToScreen(c.x,c.y); return Math.hypot(s.x-b[0],s.y-b[1])<%d&&p.body.getLinearVelocity().length()<0.3;})()" % (list(pt), px)

def carry(q, a, b, hold=0, beside=None):  # a piece picked up, lifted above the building, held still just above b, put down onto b and let go; the mouse jumps, the piece follows at the game's own pace (a heavy one slowly)
    # beside: the level height (metres) of b; then b moves sideways just clear of a piece already lying there, as a hand puts a brick beside its neighbour, not onto it
    q.mouse.move(*a); q.mouse.down()
    for pt in ((a[0], 60), (b[0], 60)): q.mouse.move(*pt, steps=2)
    until(q, held_at(q, (b[0], 60), 20), 3, 0.02)
    if beside is not None:
        dx = q.evaluate("""([y,tx])=>{const T=__tb, box=(p)=>{let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9; for(let f=p.body.getFixtureList();f;f=f.getNext()){const b=f.getAABB(0); x0=Math.min(x0,b.lowerBound.x); x1=Math.max(x1,b.upperBound.x); y0=Math.min(y0,b.lowerBound.y); y1=Math.max(y1,b.upperBound.y);} return [x0,x1,y0,y1];};
          const h=T.pieces.find((p)=>p.heldBy!=null); if(!h) return 0; let hw=0; for(let f=h.body.getFixtureList();f;f=f.getNext()) for(const v of f.getShape().m_vertices||[]) hw=Math.max(hw,Math.abs(v.x));
          const cx=T.LEVEL_X0+tx; let L=-1e9, R=1e9;  // the free gap between its neighbours in that row: it goes in the middle of the gap if the gap is just its size, else just clear of the neighbour it touches
          for(const p of T.pieces){ if(p===h||p.demo) continue; const B=box(p); if(B[3]<y-0.3||B[2]>y+0.3) continue; if((B[0]+B[1])/2<cx) L=Math.max(L,B[1]); else R=Math.min(R,B[0]); }
          let x=cx; if(L>-1e9&&R<1e9&&R-L<2*hw+0.1) x=(L+R)/2; else { if(L>x-hw) x=L+hw+0.005; if(R<x+hw) x=R-hw-0.005; }
          return Math.max(-0.15,Math.min(0.15,x-cx))*(T.worldToScreen(1,0).x-T.worldToScreen(0,0).x);}""", [beside, (b[0] - q.evaluate("()=>__tb.worldToScreen(__tb.LEVEL_X0,0).x")) / q.evaluate("()=>__tb.worldToScreen(1,0).x-__tb.worldToScreen(0,0).x")])
        b = (b[0] + dx, b[1])
    above = (b[0], b[1] - 40)
    q.mouse.move(b[0], 60, steps=2); q.mouse.move(*above, steps=2); until(q, held_at(q, above, 8), 3, 0.02)
    q.mouse.move(*b, steps=15); until(q, held_at(q, b, 6), 2, 0.02); time.sleep(hold); q.mouse.up()

def fingers(q):  # touches as a hand's fingers make them: fingers(q)('touchStart', [(id, (x, y)), ...])
    s = q.context.new_cdp_session(q)
    return lambda kind, pts: s.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in pts]})

def pixel(q, pt):  # the colour drawn at a screen point
    return q.evaluate("(p)=>{const c=document.querySelector('canvas'), d=window.devicePixelRatio||1, v=c.getContext('2d').getImageData(Math.round(p[0]*d),Math.round(p[1]*d),1,1).data; return [v[0],v[1],v[2]];}", pt)

def test_colour(q):  # the test button's colour as drawn, beside its picture
    p = button(q, 'test'); r = q.evaluate("()=>__tb.screenButtons().find((x)=>x.id==='test').r")
    v = pixel(q, [p[0] + r * 0.75, p[1]])
    return 'red' if v[0] > v[1] + 40 else 'green' if v[1] > v[0] + 30 else 'grey' if abs(v[0] - v[1]) < 12 and abs(v[1] - v[2]) < 12 else str(v)

def screen(q, x, y):  # a place in the site (level coordinates, metres) on the screen
    return q.evaluate("([x,y])=>{const w=__tb.worldToScreen(__tb.LEVEL_X0+x,y); return [w.x,w.y];}", [x, y])

def pile_piece(q, material, kind=None, inside=True, flat=False):  # a resting pile piece (its middle inside the pile's box), as the child sees it there; flat: one lying as it will lie in the plan
    return q.evaluate("""([m,k,ins,flat])=>{const T=__tb, r=T.pileBinRect, lies=(b)=>{const a=Math.abs(b.getAngle())%Math.PI; return Math.min(a,Math.PI-a)<0.08;}; const pts=T.pileBodies().filter((x)=>x.pileItem.material===m&&(!k||x.pileItem.defKey===k)&&x.getLinearVelocity().length()<0.05&&(!flat||lies(x))).map((b)=>{const p=b.getPosition(); return [r.x+p.x*T.pileScale, r.y+r.h-p.y*T.pileScale];}).filter((p)=>!ins||(p[0]>r.x+6&&p[0]<r.x+r.w-6&&p[1]>r.y+6&&p[1]<r.y+r.h-6)); return pts.length?pts[0]:null;}""", [material, kind, inside, flat])

def a_pile_piece(q, material, kind=None, secs=4, flat=False):  # waits for one to rest
    end = time.time() + secs
    while time.time() < end:
        p = pile_piece(q, material, kind, flat=flat)
        if p: return p
        time.sleep(0.1)
    return None

def site_pieces(q):  # the child's pieces in the site: [x, y] on the screen, newest last
    return q.evaluate("()=>{const T=__tb; return T.pieces.filter((x)=>!x.demo&&!x.load&&x.heldBy==null).map((p)=>{const c=p.body.getPosition(), s=T.worldToScreen(c.x,c.y); return [s.x,s.y];});}")

def place(q, kind, material, x, y):  # a pile piece of that kind carried to its place in the site (level metres) and let go just above it; if his hand came out empty, he tries again
    count = "()=>__tb.pieces.filter((x)=>!x.demo&&!x.load).length"
    for _ in range(3):
        n0, p = q.evaluate(count), a_pile_piece(q, material, kind, flat=True)
        if not p:  # none lies flat: he takes one and turns it with two fingers
            p = a_pile_piece(q, material, kind, secs=1)
            return bool(p) and place_turned(q, kind, material, x, y, 0, p)
        p = (p[0], p[1] - 8)  # held a little above its middle, so it hangs level, as a hand lifts a brick
        carry(q, p, screen(q, x, y + 0.02), beside=y); until(q, "()=>__tb.pieces.every((p)=>p.body.getLinearVelocity().length()<0.05)", 2, 0.02)
        if q.evaluate(count) > n0: break
    else: return False
    at = q.evaluate("([x,y])=>{const T=__tb, P=T.pieces.filter((p)=>!p.demo&&!p.load&&p.heldBy==null), p=P[P.length-1], c=p.body.getPosition(), s=T.worldToScreen(c.x,c.y); return [Math.hypot(c.x-T.LEVEL_X0-x,c.y-y)+Math.abs(Math.sin(p.body.getAngle())), s.x, s.y];}", [x, y])
    if at[0] < 0.3: return True
    return place_turned(q, kind, material, x, y, 0, at[1:])  # it fell off its place or over: he takes it with two fingers and puts it right

def place_turned(q, kind, material, x, y, ang, p=None, tries=2):  # a piece that lies turned in the plan (or lies turned in the pile): one finger takes it out of the pile and lifts it high above its place, a second finger on it turns it, both lower it onto its place and let go
    p = p or a_pile_piece(q, material, kind, flat=True) or a_pile_piece(q, material, kind, secs=1)
    if not p: return False
    touch, b = fingers(q), screen(q, x, y + 0.03); hi = (b[0], 150)
    touch('touchStart', [(1, p)])
    for k in range(1, 4): touch('touchMove', [(1, (p[0] + (hi[0] - p[0]) * k / 3, p[1] + (hi[1] - p[1]) * k / 3))])
    until(q, held_at(q, hi, 15), 6, 0.02)
    d = q.evaluate("()=>{const T=__tb, h=T.pieces.find((x)=>x.heldBy!=null); let x0=1e9,x1=-1e9; for(let f=h.body.getFixtureList();f;f=f.getNext()){const b=f.getAABB(0); x0=Math.min(x0,b.lowerBound.x); x1=Math.max(x1,b.upperBound.x);} return 0.35*(x1-x0)*(T.worldToScreen(1,0).x-T.worldToScreen(0,0).x);}")
    a0 = q.evaluate("()=>__tb.pieces.find((x)=>x.heldBy!=null).body.getAngle()")
    turn = math.atan2(math.sin(ang - a0), math.cos(ang - a0))  # the shortest way round to the plan's angle
    touch('touchStart', [(1, hi), (2, (hi[0] + d * math.cos(-a0), hi[1] + d * math.sin(-a0)))])
    for k in range(1, 21):
        t = -(a0 + turn * k / 20)
        touch('touchMove', [(1, hi), (2, (hi[0] + d * math.cos(t), hi[1] + d * math.sin(t)))]); time.sleep(0.02)
    until(q, "(()=>{const h=__tb.pieces.find((x)=>x.heldBy!=null); return !h||Math.abs(Math.sin((h.body.getAngle()-(%f))/2))<0.02;})()" % ang, 4, 0.02)
    for k in range(1, 11):
        c = (hi[0], hi[1] + (b[1] - hi[1]) * k / 10)
        touch('touchMove', [(1, c), (2, (c[0] + d * math.cos(-ang), c[1] + d * math.sin(-ang)))]); time.sleep(0.03)
    until(q, held_at(q, b, 6), 4, 0.02)
    touch('touchEnd', []); until(q, "()=>__tb.pieces.every((p)=>p.body.getLinearVelocity().length()<0.05)", 2, 0.02)
    at = q.evaluate("([x,y,a])=>{const T=__tb, P=T.pieces.filter((p)=>!p.demo&&!p.load&&p.heldBy==null), p=P[P.length-1], c=p.body.getPosition(), s=T.worldToScreen(c.x,c.y), d=p.body.getAngle()-a; return [Math.hypot(c.x-T.LEVEL_X0-x,c.y-y)+Math.abs(Math.sin(d)), s.x, s.y];}", [x, y, ang])
    if at[0] > 0.3 and tries: return place_turned(q, kind, material, x, y, ang, at[1:], tries - 1)  # not right: he takes it again and puts it right
    return True

def build(q, plan):  # the child builds piece by piece: plan is [(kind, material, x, y), ...] or with a turn [(kind, material, x, y, angle), ...]
    # each piece a little apart from its neighbours (3% out from the middle of the site), as a hand leaves small gaps, so no piece is pressed onto its neighbour's edge
    return all(place_turned(q, k, m, x * 1.03, y, *a) if a and abs(a[0]) > 0.01 else place(q, k, m, x * 1.03, y) for k, m, x, y, *a in plan)

def suggested(q, key):  # the site's suggested build as the child sees it drawn in the plan
    return [tuple(s) for s in q.evaluate("(k)=>__tb.SOLUTIONS[k]", key)]

def off_plan(q, key):  # what the child sees wrong: places of the plan with no piece on them, and pieces off every place
    return q.evaluate("""(k)=>{const T=__tb, S=T.SOLUTIONS[k], P=T.pieces.filter((p)=>!p.demo&&!p.load).map((p)=>{const c=p.body.getPosition(); return [p.defKey,p.material,+(c.x-T.LEVEL_X0).toFixed(2),+c.y.toFixed(2)];});
      const near=(a,b)=>a[0]===b[0]&&a[1]===b[1]&&Math.hypot(a[2]-b[2],a[3]-b[3])<0.3; return {empty:S.filter((s)=>!P.some((p)=>near(p,s))).map((s)=>s.slice(0,4)), off:P.filter((p)=>!S.some((s)=>near(p,s)))};}""", key)

def map_point(q, test):  # a screen point on the map where test(mx, my) holds, near the middle of the screen first, away from buttons
    return q.evaluate("""(t)=>{const T=__tb, v=T.mapView(), f=new Function('T','mx','my','return '+t);
      for(let r=0;r<900;r+=5) for(let a=0;a<6.28;a+=Math.min(0.2,4/Math.max(r,1))){const x=640+r*Math.cos(a), y=400+r*Math.sin(a)*0.7, mx=(x-v.ox)/v.k, my=(y-v.oy)/v.k; if(x>40&&x<1100&&y>100&&y<760&&!T.screenButtons().some((b)=>b.rect?(x>b.rect.x-10&&x<b.rect.x+b.rect.w+10&&y>b.rect.y-10&&y<b.rect.y+b.rect.h+10):Math.hypot(x-b.x,y-b.y)<(b.r||b.size||60)+10)&&f(T,mx,my)) return [x,y];} return null;}""", test)

def boat_at(q, i):  # where boat i is drawn now
    return q.evaluate("(i)=>{const T=__tb, b=T.boats[i]; if(!b) return null; const p=T.mapView().pt(b.x,b.y); return [p.x,p.y];}", i)

def quick_build(q):  # the parent's quick build: Ctrl held, the quick-build button, let go once it is built (owner 24 Nov: sites after the first are finished with it)
    q.keyboard.down('Control')
    ok = until(q, "()=>{const b=__tb.screenButtons().find((x)=>x.id==='autobuild'); return !!(b&&b.enabled);}", 20) and click(q, 'autobuild')
    built = ok and until(q, "()=>!__tb.auto", 30)
    q.keyboard.up('Control'); return built

def finish_site(q, R, key):  # in a site: the quick build, the green button, the test to its end; then what follows in the site (its line, the grey button) and on the map (its line, a new boat)
    i = q.evaluate("(k)=>__tb.LEVELS.findIndex((L)=>L.key===k)", key); boats = q.evaluate("()=>__tb.boats.length")
    built = quick_build(q); green = built and until(q, "()=>__tb.testReady()", 10)
    m = mark(q)
    if green: click(q, 'test')
    passed = green and until(q, "()=>!!__tb.progress.done[%r]&&!__tb.test" % key, 60)
    line = passed and hear(q, 14 + i, 8, m)  # the site's own line (cues: win-line, byPlace 14..23)
    grey = passed and test_colour(q) == 'grey'
    silent(q, 6); m = mark(q); click(q, 'home'); on_map = until(q, "()=>__tb.mode==='map'", 3)
    map_line = on_map and hear(q, 24 + i, 8, m)  # its line on the map (cues: map-win, byPlace 24..33)
    boat = on_map and until(q, "()=>__tb.boats.length>%d" % boats, 6)
    R.step('site %s: built, green, the test passes, its line, the button grey; on the map its line and a new boat' % key, passed and line and grey and map_line and boat, dict(built=built, green=green, passed=passed, site_line=line, grey=grey, map_line=map_line, new_boat=boat))
    silent(q, 8)

def later_sites(q, R):  # every site after the second, in the game's order
    for key in q.evaluate("()=>__tb.LEVELS.map((L)=>L.key)")[2:]:
        click(q, 'site:' + key); until(q, "()=>__tb.mode==='build'", 3)
        until(q, "()=>!__tb.demo&&!__tb.voice.cur&&!__tb.voice.queue.length", 60)  # its intro and demo watched to the end
        finish_site(q, R, key)

# --------------------------------------------------------------------
# SECTION: THE WHOLE GAME -- its steps, in the game's order
# --------------------------------------------------------------------
class Run:  # one step's result line: PASS or FAIL, the step's name, what was seen when it failed
    def __init__(self): self.n, self.t = 0, time.time()
    def step(self, name, ok, info=''):  # each line ends with the seconds the run took to reach it from the step before
        self.n += 1; t, self.t = self.t, time.time()
        print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' ' + str(info)[:900]) + ' (%.0f s)' % (self.t - t), flush=True)
        if os.environ.get('STOP') == name: raise SystemExit

def start_and_map(q, R):
    q.mouse.click(640, 400); hear(q, 11, 8); silent(q, 15)  # the first touch: the welcome, then "press here to start"
    # owner 18 Nov: "add this to all button clicks, at same volume as the terrain touch effects": the gear and its X
    got = {}
    for bid in ('settings', 'settings-close'):
        m = mark(q); click(q, bid); time.sleep(0.3); got[bid] = [s for _, s in sounds(q, m)].count('button-click')
    gains = q.evaluate("()=>[__tb.SOUNDS['button-click'][0][1], __tb.SOUNDS['map-tap-sand'][0][1]]")
    R.step('map buttons click once, as loud as a tap on the map', all(v == 1 for v in got.values()) and gains[0] == gains[1], dict(clicks=got, gains=gains))
    click(q, 'site:mastaba'); until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 3, 0.01)  # the first launch: only the first site can be touched

def map_taps(q, R):  # the map once a site is finished: the first launch's step no longer holds the screen
    # owner 18 Nov: "give sand drawing an appropriate sound, again, same loudness as all terrain sounds"; "reduce sand drawing sound 20%" (it was 0.512)
    p = map_point(q, "T.sandArea(mx,my)>=0&&[1,2,3,4,5,6].every((k)=>T.sandArea(mx+k*15/T.mapView().k,my)>=0)")
    m = mark(q); q.mouse.move(*p); q.mouse.down(); q.mouse.move(p[0] + 90, p[1], steps=6); time.sleep(0.1); q.mouse.up()
    vol = q.evaluate("()=>__tb.SOUNDS['map-sand-draw'][0][1]")
    R.step('writing in the sand sounds, 20% quieter', 'map-sand-draw' in [s for _, s in sounds(q, m)] and abs(vol - 0.512 * 0.8) < 0.005, dict(volume=vol))
    # owner 17 Nov late: "dont do water particle effects on rivers and small lakes"; "wave circles should stop at land ... with their white thing going at the beach"
    coast = map_point(q, "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&[0,1,2,3,4,5,6,7].some((k)=>T.groundAt(mx+40*Math.cos(k*0.785)/T.mapView().k,my+24*Math.sin(k*0.785)/T.mapView().k)!=='water')")
    river = map_point(q, "T.groundAt(mx,my)==='water'&&T.isLand(mx,my)")
    q.mouse.click(*coast); time.sleep(0.05)
    rings = q.evaluate("()=>__tb.tapBits.filter((t)=>t.kind==='ring').map((t)=>Array.from(t.stop||[]).filter((x)=>isFinite(x)).length)")
    q.mouse.click(*river); time.sleep(0.05)
    drops = q.evaluate("()=>__tb.tapBits.filter((t)=>t.kind==='drop'&&t.t0>performance.now()-60).length")
    R.step('waves stop at the coast; no splash on a river', bool(rings and min(rings) > 0 and drops == 0), dict(rings=rings, drops=drops))

def first_site_lessons(q, R):
    # owner 18 Nov: "if an intro is playing the esc stops the intro": one ESC skips the intro and stays in the site
    q.keyboard.press('Escape'); time.sleep(0.2)
    intro = q.evaluate("()=>!!(__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro')")
    R.step('ESC during the intro skips it and stays', mode(q) == 'build' and not intro, dict(mode=mode(q), intro=intro))
    # owner 18 Nov: "make teh icons at the top of the sidebar spread out": the first icon at the sidebar's left edge, the last at its right
    r = q.evaluate("()=>{const T=__tb, L=T.levelSidebar().buttons, x0=T.buildingWidthPx, w=window.innerWidth-x0; return {left_gap:L[0].x-L[0].size/2-x0, right_gap:x0+w-(L[L.length-1].x+L[L.length-1].size/2), n:L.length};}")
    R.step('sidebar icons spread to its edges', r['n'] > 1 and r['left_gap'] <= 12 and r['right_gap'] <= 12, r)
    # The lessons, each done as the child does once he has heard it. Owner 18 Nov: "I took some brick before the test said it":
    # at every lesson he first takes a mudbrick into the plan. Owner 21 Nov: "the cue that appears when you touch a mudbrick for the
    # first time ... should NOT be appearing there". Owner 21 Nov: "dragging fast a piece to the site after the line that was asking me
    # to drag it back": during "you can also drag it back" he puts a piece in fast, then drags one back and at once puts another in.
    # Owner 21 Nov: "the 'put a few more pieces' doesn't play or if it plays then it stops immediately": it plays in full.
    W = q.evaluate("()=>__tb.buildingWidthPx"); gy = q.evaluate("()=>__tb.worldToScreen(0,0).y")
    n = [0]
    def brick():
        p = a_pile_piece(q, 'mudbrick', secs=1)
        if p: drag(q, p, [W * (0.3 + 0.06 * (n[0] % 6)), gy - 25 - 22 * (n[0] // 6)], hold=0.4); n[0] += 1
    def last(): s = site_pieces(q); return s[-1] if s else None
    def do(k):  # what he does once he has heard line k to its end
        brick()  # a brick taken before he does what the lesson said (taken only where the lesson lets him touch the pile)
        if k == 93: brick()
        elif k == 94:
            p = last()
            if p:
                for _ in range(3): q.mouse.click(p[0], p[1]); time.sleep(0.03)
        elif k == 134:
            p = last()
            if p: drag(q, p, [W + 60, gy - 120], hold=0.3)
            brick()  # and at once another one in
        elif k == 138:
            for _ in range(3): brick()
    m0, acted, fast, end = mark(q), {}, False, time.time() + 120
    while time.time() < end and 95 not in said(q, m0):
        h = heard(q, m0); ended = [l[0] for l in h if l[2]]
        for k in (93, 94, 134, 138):
            while acted.get(k, 0) < ended.count(k): acted[k] = acted.get(k, 0) + 1; do(k)
        if not fast and any(l[0] == 134 and not l[2] for l in h):
            fast = True; p = a_pile_piece(q, 'mudbrick', secs=1)
            if p: drag(q, p, [W * 0.6, gy - 25], steps=8, hold=0.1)  # fast, into the site, during the line
        time.sleep(0.2)
    h = heard(q, m0); lens = q.evaluate("()=>__tb.VOICE_SECONDS")
    full = lambda k: any(l[0] == k and l[2] and (l[2] - l[1]) / 1000 >= lens[str(k)] - 0.1 for l in h)
    R.step('lessons go on whatever bricks he takes early (tap, drag back, a few pieces, the shovel)', all(full(k) for k in (94, 134, 138)) and 95 in [l[0] for l in h], dict(said=[l[0] for l in h]))
    R.step('no first-mudbrick line during the lessons', 78 not in [l[0] for l in h], dict(said=[l[0] for l in h]))
    hear_end(q, 95, 8, m0); click(q, 'broom')  # "press the shovel"
    hear_end(q, 98, 15, m0)  # "now build, fill the whole plan"

def first_site_build_and_test(q, R):
    # the child builds the plan as drawn, piece by piece; the lessons on the way: the red button (at eight pieces), the undo (at ten)
    plan = suggested(q, 'mastaba'); m0 = mark(q)
    # owner 23 Nov: "the 'this space is for the headpiece, leave it empty' ... play only at the first tutorial level": a piece put
    # into the dotted outline here says it; he takes it out again
    dots = q.evaluate("()=>{const T=__tb, r=T.grid.load[0], cx=r.reduce((a,p)=>a+p[0],0)/r.length, cy=r.reduce((a,p)=>a+p[1],0)/r.length, s=T.worldToScreen(cx,cy); return [s.x,s.y];}")
    W = q.evaluate("()=>__tb.buildingWidthPx")
    def lay_one(k):  # a mudbrick laid into the plan by hand, row by row, where the child drops it
        p = a_pile_piece(q, 'mudbrick')
        if p: carry(q, p, screen(q, -3 + 2 * (k % 4), 0.55 + (k // 4)))
    k = 0
    while k < 12 and not hear(q, 99, 0.6, m0): lay_one(k); k += 1  # he lays pieces until the red-button lesson comes (at eight in the building)
    red = hear_end(q, 99, 10, m0)  # "this is the test button; while it is red the building is not ready; press it and see what is not"
    m = mark(q); click(q, 'test'); time.sleep(0.4)
    shown = q.evaluate("()=>!!__tb.failShow")
    R.step('red button lesson: pressed, the red shows what is missing', red and shown, dict(heard_99=red, red_shown=shown, said=said(q, m0)))
    carry(q, a_pile_piece(q, 'mudbrick'), dots); dotline = hear(q, 137, 5, m)
    silent(q); p = site_pieces(q)[-1]; drag(q, p, [W + 60, p[1] - 120], hold=0.3)  # taken out again, back to the pile
    R.step('the dotted outline line at the first site', dotline, dict(said=said(q, m)))
    while k < 13 and not hear(q, 135, 0.6, m0): lay_one(k); k += 1  # and on until the undo lesson (at ten)
    undo = hear(q, 135, 10, m0)
    built = quick_build(q)  # the rest with the quick build (owner 24 Nov)
    green = until(q, "()=>__tb.testReady()", 10); grn = hear_end(q, 100, 20, m0)
    R.step('undo lesson, then the button turns green and says so', undo and green and grn, dict(said=said(q, m0), built=built, colour=test_colour(q)))
    # owner 18 Nov: "the 'lets see, will it stand' cue ... should play first, then the tests start, and for each one of the 3 tests,
    # its voice cue starts with it"; "the 1st time test explanations ... freeze the screen ... I dont want that"; owner 17 Nov late:
    # "when the tests are playing, the music should fade off"; owner 17 Nov: "the success ... audio in the lvls, after the test, are
    # quite delayed"; owner 18 Nov: "the withstood comes first, and the end-level cue follows 1 sec after"; "first the sucess/failure
    # end-tests cue, then the end-level in-level cue"
    m = mark(q); m_pre = [m[0] - 3] + m[1:]; click(q, 'test')
    until(q, "()=>!!__tb.progress.done.mastaba||(__tb.test&&__tb.test.phase==='fail')", 90); hear(q, 106, 20, m)
    ev = q.evaluate("(m)=>({lines:__rec.lines.slice(m[0]), ph:__rec.ph.slice(m[2]), duck:__rec.duck.slice(m[3]), snd:__rec.snd.slice(m[1]), paused:__rec.ph.slice(m[2]).some((p)=>p[0]==='cue')})", m)
    L = lambda n: next((l for l in ev['lines'] if l[0] == n), None)
    P = lambda n: next((p[1] for p in ev['ph'] if p[0] == n), None)
    ok = L(71) and L(71)[2] and P('wind') is not None and P('wind') >= L(71)[2] and P('wind') - max(L(71)[2], P('settle') + 1200) <= 300  # the wind after the line, and once the pieces have settled (PHASE_TIME.settle, 1.2 s)
    for part, n in (('wind', 101), ('load', 102), ('quake', 103)): ok = ok and P(part) is not None and L(n) and abs(L(n)[1] - P(part)) <= 250
    R.step('"let\'s see" first, then each part of the test with its own line', bool(ok), dict(before=heard(q, m_pre)[:4], lines=ev['lines'][:6], ph=ev['ph'][:6], pressed_at=m))
    R.step('the explanations never pause the test', not ev['paused'] and bool(L(101)), dict(phases=[p[0] for p in ev['ph']]))
    R.step('music off while the test runs', bool(ev['duck']) and ev['duck'][-1] == 0, dict(duck=sorted(set(ev['duck']))[:4]))
    cheer = next((t for t, s in ev['snd'] if s == 'cheer'), None)
    quake_end = next((t for k, (p, t) in enumerate(ev['ph']) if p == 'settle' and any(x[0] == 'quake' for x in ev['ph'][:k])), None)
    w, s14 = L(104), L(14)
    pass_end = next((ev['ph'][k + 1][1] for k, (p, t) in enumerate(ev['ph'][:-1]) if p == 'pass'), None)  # "it withstood" is done when its line and the celebration are done
    told = w and w[2] and pass_end and max(w[2], pass_end)
    R.step('cheer at the end of the earthquake, "it withstood" next, the site line 1 s after it', bool(cheer and quake_end and w and told and s14 and cheer - quake_end <= 700 and w[1] - max([cheer] + [l[2] for l in ev['lines'] if l[2] and l[2] <= w[1]]) <= 1300 and 800 <= s14[1] - told <= 1300),
           dict(cheer_after_quake=cheer and quake_end and cheer - quake_end, withstood_after_cheer=w and cheer and w[1] - cheer, site_line_after_told=s14 and told and s14[1] - told))
    order = [l[0] for l in ev['lines']]; k = lambda n: order.index(n) if n in order else None
    R.step('the test result line before the site line, then "back to the map"', None not in (k(104), k(14), k(106)) and k(104) < k(14) < k(106), dict(order=order))
    R.step('the headpiece outline stays drawn while the headpiece is on', q.evaluate("()=>__rec.ghost") > 0, '')
    # owner 18 Nov: "the press here to go mack to the map cue, plays too often, double its play interval": 10 s after it ends
    hear_end(q, 106, 10, m); e1 = q.evaluate("()=>__rec.lines.filter((x)=>x[0]===106)[0][2]")
    gap = (q.evaluate("()=>__rec.lines.filter((x)=>x[0]===106)[1][1]") - e1) / 1000 if until(q, "()=>__rec.lines.filter((x)=>x[0]===106).length>=2", 16) else None
    R.step('"back to the map" repeats 10 s after it ends', gap is not None and 9.5 <= gap <= 11, dict(gap_s=gap))

def finished_site(q, R):
    # owner 23 Nov: "when a level is successfully passed, the TEST button should become grey, unless the kid presses the shovel, or
    # moves an item. the same should be when reentering a finished level"
    seen = dict(after_pass=test_colour(q))
    silent(q, 15); click(q, 'home'); until(q, "()=>__tb.mode==='map'", 3); time.sleep(0.5)
    click(q, 'site:mastaba'); until(q, "()=>__tb.mode==='build'&&__tb.loads.length===1", 5); wait_game(q, 1.5)
    seen['back_at_the_finished_site'] = test_colour(q)
    click(q, 'test'); time.sleep(0.3); seen['grey_pressed_starts_test'] = q.evaluate("()=>!!__tb.test")
    R.step('test button grey after a pass and at the finished site, where pressing it starts nothing', seen['after_pass'] == 'grey' and seen['back_at_the_finished_site'] == 'grey' and not seen['grey_pressed_starts_test'], seen)
    # owner 18 Nov: "when you go to a finished site, make it possible to grab and move headpiece as any other block ... the weight
    # of stone ... max the weight of 2x std stone blocks ... triple clicking it makes it disappear"; it knocks as stone when it lands
    st = q.evaluate("()=>{const T=__tb, l=T.loads[0], c=l.body.getPosition(), s=T.worldToScreen(c.x,c.y); return {x:s.x,y:s.y,cy:c.y,blocks:T.inBlocks(l.body,'stone')};}")
    m = mark(q); q.mouse.move(st['x'], st['y']); q.mouse.down(); q.mouse.move(st['x'] + 10, st['y'] - 120, steps=10)
    until(q, "()=>__tb.loads[0].body.getPosition().y-%f>0.5" % st['cy'], 4); lifted = q.evaluate("()=>__tb.loads[0].body.getPosition().y") - st['cy']; q.mouse.up(); wait_game(q, 1.0)
    knock = [s for _, s in sounds(q, m) if s.startswith('hit-') and 'stone' in s]
    c = q.evaluate("()=>{const T=__tb, c=T.loads[0].body.getPosition(), s=T.worldToScreen(c.x,c.y); return [s.x,s.y];}")
    for _ in range(3): q.mouse.click(c[0], c[1]); time.sleep(0.03)
    gone = until(q, "()=>__tb.loads.length===0", 1)
    R.step('the headpiece can be carried (at most two stone blocks heavy), knocks as stone, three taps take it away', st['blocks'] <= 2.001 and lifted > 0.5 and bool(knock) and gone, dict(blocks=st['blocks'], lifted=lifted, knock=knock, gone=gone))

def damaged_site(q, R):
    # owner 18 Nov: "the voice cues for next site - damaged site must play sound not every time they trigger (only the visual plays
    # every time), the sound must play the first time they happen per site, and of course refreshing the page counts"
    silent(q, 8); click(q, 'home'); until(q, "()=>__tb.mode==='map'", 3)
    m = mark(q); first = hear(q, 39, 15, m); silent(q, 10)
    m = mark(q); wait_game(q, 21); again = 39 in said(q, m)
    # owner 18 Nov: "make checkbox option in setting for music": unticked, no music on the map, and it stays so after the page is opened again
    click(q, 'settings'); time.sleep(0.1); click(q, 'music'); click(q, 'settings-close'); time.sleep(0.3)
    off_map = q.evaluate("()=>__tb.musicDuck")
    q.reload(); q.wait_for_function("()=>!!window.__tb"); listen(q); q.mouse.click(640, 400)  # the page opened again; listening from before the first touch
    after_refresh = hear(q, 39, 15)
    reopened = q.evaluate("()=>[__tb.SETTINGS.find((s)=>s.id==='music').on(), __tb.musicDuck]")
    R.step('the damaged-site line once per session, again after a refresh', first and not again and after_refresh, dict(first=first, again=again, after_refresh=after_refresh))
    silent(q, 10)
    return off_map, reopened

def music_back(q, R, off_map, reopened):
    click(q, 'site:mastaba'); until(q, "()=>__tb.mode==='build'", 3); time.sleep(0.5)
    off_site = q.evaluate("()=>__tb.musicDuck")
    silent(q, 8); click(q, 'home'); until(q, "()=>__tb.mode==='map'", 3); time.sleep(0.3)
    click(q, 'settings'); time.sleep(0.1); click(q, 'music'); click(q, 'settings-close'); time.sleep(0.3)
    on = q.evaluate("()=>__tb.musicDuck")
    click(q, 'site:mastaba'); until(q, "()=>__tb.mode==='build'", 3); time.sleep(0.5)
    R.step('music tick: off on the map and in a site, still off after reopening, back when ticked', off_map == 0 and off_site == 0 and reopened == [False, 0] and on == 1, dict(map=off_map, site=off_site, reopened=reopened, on=on))

def failing_test(q, R):
    # the damaged first site rebuilt with wooden blocks on top: owner 18 Nov: "is there a test for the failure too?": the failure's
    # sound at the moment it fails; owner 21 Nov: "no red was shown when the wind moved the pieces, just the 'to kokkino deixnei pou
    # xalase'": while the failure's lines are heard, the red is on the screen. Then the wood swapped for mudbricks again: it passes.
    quick_build(q)  # the site rebuilt with the quick build, then its top row of mudbricks swapped for wooden blocks by hand
    W = q.evaluate("()=>__tb.buildingWidthPx")
    for _ in range(4):  # three quick taps on each top mudbrick send it back to the pile
        ps = site_pieces(q); ytop = min(p[1] for p in ps); top = min((p for p in ps if p[1] < ytop + 10), key=lambda p: p[0])
        for _ in range(3): q.mouse.click(*top); time.sleep(0.03)
        time.sleep(0.3)
    plan = suggested(q, 'mastaba'); build(q, [(k, 'wood', x, y) for k, _, x, y, *_ in plan if y > 2])
    green = until(q, "()=>__tb.testReady()", 10)
    m = mark(q)
    if green: click(q, 'test')
    seen, end = [], time.time() + 60
    while time.time() < end and green and (q.evaluate("()=>!!__tb.test") or not seen):
        s = q.evaluate("()=>{const c=__tb.voice.cur; return c&&c.cue&&(c.cue.on==='test-fail'||c.cue.on==='fail-explain')?[c.n, !!__tb.failShow]:null}")
        if s: seen.append(s)
        time.sleep(0.1)
    f = q.evaluate("(m)=>{const p=__rec.ph.slice(m[2]).find((x)=>x[0]==='fail'); return p?p[1]:null}", m)
    snd = next((t for t, s in sounds(q, m) if s == 'fail'), None)
    R.step('the failure sound when the building fails', f is not None and snd is not None and abs(snd - f) <= 100, dict(green=green, colour=test_colour(q), fail_at=f, sound_at=snd, pieces=q.evaluate("()=>__tb.pieces.map((p)=>{const c=p.body.getPosition(); return [p.defKey,p.material[0], +(c.x-__tb.LEVEL_X0).toFixed(2), +c.y.toFixed(2)]})")))
    R.step('the red shows while the failure lines are heard', green and 105 in [x[0] for x in seen] and all(x[1] for x in seen), dict(lines=sorted(set(x[0] for x in seen)), dark=[x for x in seen if not x[1]][:3]))
    silent(q, 15); quick_build(q)
    ok = until(q, "()=>__tb.testReady()", 10)
    if ok: click(q, 'test'); until(q, "()=>!!__tb.progress.done.mastaba&&!__tb.progress.done.mastaba.broken&&!__tb.test", 90)
    silent(q, 15); click(q, 'home'); until(q, "()=>__tb.mode==='map'", 3); time.sleep(0.5)

def second_site(q, R):
    # owner 17 Nov: "I click a site I should go, and the line doesnt play because the restart warning plays. New rule: every
    # interaction that is the result of my action stops the previous visual/audio cue and starts the new one"
    # the restart pressed once: its warning speaks; the child presses the second site: its intro at once, the warning's glow gone
    click(q, 'restart'); warn = hear(q, 91, 2)
    m = mark(q); click(q, 'site:djoser'); intro = until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 1)
    glow = q.evaluate("()=>__tb.active.filter((a)=>(a.targets||[]).some((t)=>t.btn==='restart')).length")
    R.step('a child action cuts the line before it (restart warning, then a site)', warn and intro and glow == 0, dict(warning=warn, intro=intro, glows=glow))
    # owner 18 Nov: "an esc in the lvel ... should exit immediatly"; "if an intro is playing the esc stops the intro"; "when demo/
    # tutorial is playing an esc should just exit"; "an esc stops the demo sound, but the demo keeps playing ... if they are to stop,
    # they stop together"
    q.keyboard.press('Escape'); time.sleep(0.2); stayed = mode(q) == 'build'
    demo = until(q, "()=>!!__tb.demo&&!!__tb.voice.cur&&__tb.voice.cur.demo", 10)
    q.keyboard.press('Escape'); time.sleep(0.2)
    after = q.evaluate("()=>({mode:__tb.mode, demo:!!__tb.demo, line:!!(__tb.voice.cur&&__tb.voice.cur.demo), demoPieces:__tb.pieces.filter(p=>p.demo).length})")
    R.step('ESC skips the intro, then ESC during the demo leaves: demo and its line gone', stayed and demo and after['mode'] == 'map' and not after['demo'] and not after['line'], dict(intro=intro, stayed=stayed, demo=demo, after=after))
    click(q, 'site:djoser'); until(q, "()=>__tb.mode==='build'", 3)
    until(q, "()=>!__tb.demo&&!__tb.voice.cur&&!__tb.voice.queue.length", 180)  # he watches the demo to its end
    # the dotted outline line is not said at the second site
    dots = q.evaluate("()=>{const T=__tb, r=T.grid.load[0], cx=r.reduce((a,p)=>a+p[0],0)/r.length, cy=r.reduce((a,p)=>a+p[1],0)/r.length, s=T.worldToScreen(cx,cy); return [s.x,s.y];}")
    m = mark(q); carry(q, a_pile_piece(q, 'stone') or a_pile_piece(q, 'mudbrick'), dots); wait_game(q, 3)
    R.step('no dotted outline line at the second site', 137 not in said(q, m), dict(said=said(q, m)))
    click(q, 'broom'); time.sleep(0.5)
    finish_site(q, R, 'djoser')

def map_boats_and_stones(q, R):
    until(q, "()=>__tb.boats.length>1&&__tb.boats.every((b)=>!b.back)", 20)
    sea_far = "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+260*Math.cos(k*0.785),my+60*Math.sin(k*0.785))==='water')"
    # owner 18 Nov: "boats shouldm also be able to be thrown, like stones do ... just not rolling": picked up and flicked, it lands past where the finger let go
    a = boat_at(q, 0); q.mouse.move(*a); q.mouse.down(); held = q.evaluate("()=>!!__tb.boats[0].held")
    for k in range(1, 13): q.mouse.move(a[0] + 8 * k, a[1]); time.sleep(0.016)
    time.sleep(0.25)
    q.evaluate("()=>{window.addEventListener('pointerup',()=>{const T=__tb,b=T.boats[0],p=T.mapView().pt(b.x,b.y); window.__let=[p.x,p.y];},{capture:true,once:true});}")
    for k in range(1, 7): q.mouse.move(a[0] + 96 + 25 * k, a[1]); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.8)
    let = q.evaluate("()=>window.__let"); end = q.evaluate("()=>{const T=__tb,b=T.boats[0],p=T.mapView().pt(b.x,b.y); return [p.x,p.y,!!b.drop];}")
    R.step('a boat flicked flies on past the finger', held and end[0] - let[0] > 30 and not end[2], dict(held=held, flew=end[0] - let[0]))
    # owner 18 Nov: "dropping a boat on another boat makes the same sound that the blocks do on wood-on-wood hit ... volume ... same as the stone-on-boat sound"
    until(q, "()=>__tb.boats.every((b)=>!b.held&&!b.drop)", 5)
    a, t = boat_at(q, 0), q.evaluate("()=>{const T=__tb, v=T.mapView(), p=v.pt(T.boats[1].x,T.boats[1].y); return [p.x,p.y-T.BOAT_LIFT_H*v.k];}")
    q.mouse.move(*a); q.mouse.down()
    for k in range(1, 21): q.mouse.move(a[0] + (t[0] - a[0]) * k / 20, a[1] + (t[1] - a[1]) * k / 20); time.sleep(0.03)
    for _ in range(8):  # the other boat sails on: his hand follows it until the boat in his hand hangs over it
        t = q.evaluate("()=>{const T=__tb, v=T.mapView(), p=v.pt(T.boats[1].x,T.boats[1].y); return [p.x,p.y-T.BOAT_LIFT_H*v.k];}"); q.mouse.move(*t, steps=2); time.sleep(0.03)
    m = mark(q); q.mouse.up(); time.sleep(0.6)
    vol = q.evaluate("()=>[__tb.SOUNDS['map-boat-boat'], __tb.SOUNDS['map-stone-boat'], __tb.SOUNDS['hit-wood-wood']]")
    R.step('a boat dropped on a boat knocks as wood on wood, as loud as stone on a boat', 'map-boat-boat' in [s for _, s in sounds(q, m)] and vol[0][0][0] == vol[2][0][0] and vol[0][0][1] == vol[1][0][1], dict(sounds=[s for _, s in sounds(q, m)]))
    # owner 23 Nov: "The borders of the land, the edges, are considered navigable by boats. change that.": carried onto the land at the map's left edge
    until(q, "()=>__tb.boats.every((b)=>!b.held&&!b.drop)", 5)
    edge = q.evaluate("()=>{const T=__tb, v=T.mapView(); for(let y=760;y>100;y-=10){const my=(y-v.oy)/v.k; if(T.isLand(6,my)&&T.isLand(6,my+T.BOAT_LIFT_H)) return [Math.max(0.5,v.ox+1*v.k),y-T.BOAT_LIFT_H*v.k];} return null;}")  # the finger above the land at the map's left edge: a held boat hangs below the finger
    until(q, "()=>__tb.boats.some((b)=>__tb.crewOf(b))", 20)  # a boat with its travellers aboard (an empty boat stays where it is left)
    i = q.evaluate("()=>__tb.boats.findIndex((b)=>__tb.crewOf(b))")
    a = boat_at(q, i); q.mouse.move(*a); q.mouse.down()
    for k in range(1, 31): q.mouse.move(a[0] + (edge[0] - a[0]) * k / 30, a[1] + (edge[1] - a[1]) * k / 30); time.sleep(0.02)
    time.sleep(0.4); q.mouse.up(); until(q, "()=>!!__tb.boats[%d].back" % i, 3)
    st = q.evaluate("(i)=>{const T=__tb, b=T.boats[i], W=b.back;  /* its way back starts with its travellers carrying it: it lies on land */ const sail=W?W.runs.filter((r)=>r.mode==='sail').flatMap((r)=>r.pts):[]; return {first_run:W&&W.runs[0].mode, on_edge:sail.filter(([x,y])=>x<8||y<8||x>2168||y>1400).length};}", i)
    R.step('a boat left on the land by the map edge never sails along the edge', st['first_run'] == 'carry' and st['on_edge'] == 0, st)
    # owner 17 Nov late: "grab stones from the mountain and drop them on the sea (many small splashes) or on the land (they stay there
    # ... and disappear after 1 min ...), they can pile up, or collide with the boats"; owner 18 Nov: "stones stand on water a bit and
    # then sink ... just sink"; "five stones into the water sound like one tap"; "the thrown stones slide too much on land"; "remove
    # the rolling sounds"
    rock = map_point(q, "T.groundAt(mx,my)==='rock'")
    land = map_point(q, "['green','sand'].includes(T.groundAt(mx,my))&&T.sandArea(mx,my)<0&&!T.boats.some((b)=>Math.hypot(b.x-mx,b.y-my)<80)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+70*Math.cos(k*0.785),my+70*Math.sin(k*0.785))!=='water')")
    sea = map_point(q, "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&!T.boats.some((b)=>Math.hypot(b.x-mx,b.y-my)<120)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+90*Math.cos(k*0.785),my+90*Math.sin(k*0.785))==='water')")
    rest = "()=>__tb.mapStones.every((s)=>!s.held&&!s.vz&&!s.vx&&!s.vy)"
    drag(q, rock, land, hold=0.3); time.sleep(0.15); five = until(q, "()=>__tb.mapStones.length===5", 1) and until(q, rest, 2)
    t_first = q.evaluate("()=>__tb.clock")
    drag(q, rock, land, hold=0.3); time.sleep(0.15); piled = until(q, rest, 2) and q.evaluate("()=>__tb.mapStones.length===10&&__tb.mapStones.some((s)=>s.z>__tb.STONE*0.9)")
    R.step('stones from the mountain stay on land and pile up', five and piled, dict(stones=q.evaluate("()=>__tb.mapStones.length")))
    q.evaluate("()=>{window.__wet=0; const touch=new Map(); const end=__tb.clock+10; const f=()=>{ const now=__tb.clock*1000; for(const s of __tb.mapStones) if(!s.held&&s.z<1&&!s.on&&__tb.groundAt(s.x,s.y)==='water'&&!touch.has(s)) touch.set(s,now); for(const [s,t0] of touch) if(__tb.mapStones.includes(s)) __wet=Math.max(__wet,(now-t0)/1000); if(now<end*1000) requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    m = mark(q); drag(q, rock, sea, hold=0.3); wait_game(q, 1.2)
    splashes = [s for _, s in sounds(q, m)].count('map-tap-water')
    R.step('stones into the sea sink at once with one splash sound', q.evaluate("()=>window.__wet") < 0.05 and splashes == 1 and q.evaluate("()=>__tb.mapStones.length") == 10, dict(on_water=q.evaluate("()=>window.__wet"), splashes=splashes))
    # thrown on dry land: they land beyond where the finger let go, roll a little, one knock each
    flat = map_point(q, "Array.from({length:60},(_,k)=>k).every((k)=>{const v=T.mapView(), x=mx+k*5/v.k; return [-20,0,20].every((dy)=>['green','sand'].includes(T.groundAt(x,my+dy/v.k)))&&T.sandArea(x,my)<0&&!T.mapStones.some((s)=>Math.hypot(s.x-x,s.y-my)<40);})")
    n0 = q.evaluate("()=>__tb.mapStones.length")
    q.mouse.move(*rock); q.mouse.down(); time.sleep(0.05)
    for k in range(1, 21): q.mouse.move(rock[0] + (flat[0] - rock[0]) * k / 20, rock[1] + (flat[1] - rock[1]) * k / 20); time.sleep(0.016)
    time.sleep(0.4); m = mark(q)
    q.mouse.move(flat[0] + 120, flat[1], steps=4); q.mouse.up(); until(q, rest, 3)
    thrown = q.evaluate("([p,n0])=>{const T=__tb, v=T.mapView(), mx=(p[0]-v.ox)/v.k, S=T.mapStones.slice(n0); return S.length?S.reduce((a,s)=>a+s.x,0)/S.length-mx:null;}", [[flat[0] + 120, flat[1]], n0])
    rocks = [s for _, s in sounds(q, m)].count('map-tap-rock')
    R.step('stones thrown land beyond the finger, one knock each', thrown is not None and thrown > 30 and rocks <= 5, dict(thrown=thrown, knocks=rocks))
    # onto a boat at sea: a knock, they bounce off and sink, and the boat's people groan
    until(q, "()=>__tb.boats.every((b)=>!b.held&&!b.drop)", 10)
    until(q, "()=>__tb.boats.some((b)=>__tb.crewOf(b)&&!b.held&&!b.back&&__tb.groundAt(b.x,b.y)==='water'&&!__tb.isLand(b.x,b.y))", 30)  # a boat at sea with its travellers aboard
    b = q.evaluate("()=>__tb.boats.findIndex((b)=>__tb.crewOf(b)&&!b.held&&!b.back&&__tb.groundAt(b.x,b.y)==='water'&&!__tb.isLand(b.x,b.y))")
    m = mark(q); q.mouse.move(*rock); q.mouse.down(); time.sleep(0.05)
    for _ in range(10): q.mouse.move(*boat_at(q, b), steps=2); time.sleep(0.03)  # his hand follows the sailing boat
    q.mouse.up()
    hits = until(q, "(m=>__rec.snd.slice(m[1]).some((s)=>s[1]==='map-stone-boat'))(%s)" % list(m), 3)
    R.step('stones dropped on a boat knock, bounce off and sink; its people groan', hits and 'boat-left-on-land' in [s for _, s in sounds(q, m)] and [s for _, s in sounds(q, m)].count('map-stone-boat') <= 2, dict(sounds=sorted(set(s for _, s in sounds(q, m)))))
    return t_first

def stones_gone(q, R, t_first):
    # stones age only while the map is shown: after a minute of map time the first stones are gone, and the stones lying on them fall
    click(q, 'home') if mode(q) == 'build' else None; until(q, "()=>__tb.mode==='map'", 3)
    gone = until(q, "()=>__tb.mapStones.length>0&&__tb.mapStones.every((s)=>s.z<=0.01||s.held)", 40)
    R.step('stones on land disappear after a minute; one on top falls when the one under it goes', gone, dict(stones=q.evaluate("()=>__tb.mapStones.map((s)=>+s.z.toFixed(2))")))

def restart_and_ticks_off(q, R):
    # owner 17 Nov: the restart button shows the load screen again, so the player sees the game start over
    click(q, 'restart'); time.sleep(0.3); click(q, 'restart')
    shown = until(q, "()=>!!document.getElementById('load-screen')", 1); gone = shown and until(q, "()=>!document.getElementById('load-screen')", 4)
    R.step('restart: the load screen, and the game from the start', shown and gone and not q.evaluate("()=>__tb.progress.done.mastaba"), dict(shown=shown, gone=gone))
    q.mouse.click(640, 400); hear(q, 11, 8); silent(q, 15)
    # owner 17 Nov: "I refresh everything, have teaching and all cues and videos disabled, I go in first lvl ... I click the green
    # button, the 'lets see if it will stand' cue plays, but no test starts": every tick off in the gear's box
    click(q, 'settings'); time.sleep(0.1)
    for rid in q.evaluate("()=>__tb.screenButtons().filter((b)=>b.rect).map((b)=>b.id)"):
        if q.evaluate("(id)=>{const r=__tb.SETTINGS.find((s)=>s.id===id); return r?r.on():false}", rid): click(q, rid)
    ticks = q.evaluate("()=>__tb.SETTINGS.map((s)=>s.on())"); click(q, 'settings-close')
    click(q, 'site:mastaba'); until(q, "()=>__tb.mode==='build'", 3); silent(q, 10)
    # owner 17 Nov: "a lot of cues dont play when I have teaching clicked off": the first pick-up of a mudbrick and the red button
    # still speak. Owner 17 Nov late: "all the part of that mudbrick that is outside the design should be red": the first mudbrick is
    # laid across the plan's right edge, and the red button shows its outside part red
    edge = q.evaluate("()=>{const T=__tb; let x=-1e9; for(const r of T.grid.solid) for(const [a,b] of r) if(b<0.5) x=Math.max(x,a); const t=T.worldToScreen(x,0.6); return [t.x,t.y,x];}")
    m = mark(q); drag(q, a_pile_piece(q, 'mudbrick'), edge[:2]); pick = hear(q, 78, 2, m)
    until(q, "()=>__tb.pieces.length===1&&__tb.pieces[0].body.getLinearVelocity().length()<0.02", 4); silent(q, 6)
    box = q.evaluate("""(ex)=>{const T=__tb, p=T.pieces[0]; let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9; for(let f=p.body.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); x0=Math.min(x0,bb.lowerBound.x); x1=Math.max(x1,bb.upperBound.x); y0=Math.min(y0,bb.lowerBound.y); y1=Math.max(y1,bb.upperBound.y);}
      const a=T.worldToScreen((ex+x1)/2,(y0+y1)/2); return {out:[a.x,a.y], outW:x1-ex, inW:ex-x0};}""", edge[2])
    before = pixel(q, box['out']); m = mark(q); click(q, 'test'); red70 = hear(q, 70, 1, m)
    after = max(v[0] - v[1] for v in (pixel(q, box['out']) for _ in range(12) if time.sleep(0.04) is None))
    R.step('ticks off: the first mudbrick and the red button still speak', not any(ticks) and pick and red70, dict(ticks=ticks, mudbrick_line=pick, red_line=red70))
    R.step('the part of a piece outside the plan turns red', box['outW'] > 0.2 and box['inW'] > 0.2 and after - (before[0] - before[1]) > 12, dict(box=box, before=before, after=after))
    silent(q, 6); click(q, 'broom'); wait_game(q, 1.5)

def hand_and_pile(q, R):
    W = q.evaluate("()=>__tb.buildingWidthPx"); gy = q.evaluate("()=>__tb.worldToScreen(0,0).y"); touch = fingers(q)
    # owner 18 Nov: "both the block and the block's outline came out of the sidebar": two fingers on one pile piece, dragged out together
    a = a_pile_piece(q, 'mudbrick'); n0 = q.evaluate("()=>__tb.pieces.length")
    f1, f2 = (a[0] - 4, a[1]), (a[0] + 4, a[1])
    touch('touchStart', [(1, f1)]); time.sleep(0.03); touch('touchStart', [(1, f1), (2, f2)])
    for k in range(1, 31): touch('touchMove', [(1, (f1[0] - 500 * k / 30, f1[1] - 100)), (2, (f2[0] - 500 * k / 30, f2[1] - 100))]); time.sleep(0.016)
    time.sleep(0.5); out = q.evaluate("()=>__tb.pieces.length") - n0
    touch('touchEnd', []); wait_game(q, 1.0); ghosts = q.evaluate("()=>__tb.pieces.filter(p=>p.ghost).length")
    R.step('two fingers on a pile piece bring out one piece', out == 1 and ghosts == 0, dict(out=out, ghosts=ghosts))
    # owner 18 Nov: "2 fingers can be used to carry a block, cause this way a kid can rotate the blocks better": a wooden block laid on
    # the ground, one finger near each end, turned a quarter round while lifting; one finger let go, the other still carries it
    drag(q, a_pile_piece(q, 'wood'), (350, gy - 20), hold=0.3); wait_game(q, 1.0)
    st = q.evaluate("""()=>{const T=__tb, p=T.pieces[T.pieces.length-1], c=p.body.getPosition(); let x0=1e9,x1=-1e9; for(let f=p.body.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); x0=Math.min(x0,bb.lowerBound.x); x1=Math.max(x1,bb.upperBound.x);} const hx=(x1-x0)/2;
      const a=T.worldToScreen(c.x-0.7*hx,c.y), z=T.worldToScreen(c.x+0.7*hx,c.y), m=T.worldToScreen(c.x,c.y); return {a:[a.x,a.y],z:[z.x,z.y],m:[m.x,m.y]};}""")
    (ax, ay), (zx, zy), (mx, my) = st['a'], st['z'], st['m']; r = (zx - ax) / 2
    touch('touchStart', [(1, (ax, ay))]); time.sleep(0.03); touch('touchStart', [(1, (ax, ay)), (2, (zx, zy))])
    two = q.evaluate("()=>{const p=__tb.pieces[__tb.pieces.length-1]; return !!(p.heldBy!=null&&p.second&&p.second.grip);}")
    for k in range(1, 41):
        th = math.pi / 2 * k / 40; cy = my - 150 * k / 40
        touch('touchMove', [(1, (mx - r * math.cos(th), cy + r * math.sin(th))), (2, (mx + r * math.cos(th), cy - r * math.sin(th)))]); time.sleep(0.016)
    time.sleep(0.8); turned = math.degrees(q.evaluate("()=>__tb.pieces[__tb.pieces.length-1].body.getAngle()"))
    touch('touchEnd', [(2, (mx, my - 150 - r))]); time.sleep(0.05)
    still = q.evaluate("()=>{const p=__tb.pieces[__tb.pieces.length-1]; return p.heldBy!=null&&!p.second&&!!p.grip;}")
    touch('touchEnd', []); time.sleep(0.5)
    R.step('two fingers turn a piece; one finger let go, the other still carries it', two and 70 <= abs(turned) <= 110 and still, dict(two=two, turned=round(turned), still=still))
    # owner 21 Nov: "fix the piece stuck issue": a piece dragged back into the pile fast and low, five times; no pile piece stays in its walls
    click(q, 'broom'); wait_game(q, 1.5); stuck = []
    for k, (dx, dy) in enumerate([(60, 120), (40, 90), (20, 140), (80, 60), (30, 110)]):
        drag(q, a_pile_piece(q, 'mudbrick'), [W * 0.3, gy - 25], hold=0.4); time.sleep(0.5)
        pc = site_pieces(q)
        if pc: drag(q, pc[-1], [W + dx, gy - dy], steps=10, hold=0.2)
        wait_game(q, 2)
        out = q.evaluate("""()=>{const T=__tb,r=T.pileBinRect,Wm=r.w/T.pileScale; return T.pileBodies().map((b)=>{let lo=1e9,hi=-1e9; for(let f=b.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); lo=Math.min(lo,bb.lowerBound.x); hi=Math.max(hi,bb.upperBound.x);} return [+lo.toFixed(2), +(hi-Wm).toFixed(2)];}).filter(([lo,hi])=>lo<-0.05||hi>0.05);}""")
        if out: stuck.append([k, out])
    rests = until(q, "()=>Math.max(...__tb.pileBodies().map((b)=>b.getLinearVelocity().length()))<0.05", 5)
    R.step('no pile piece stays stuck in the pile walls after fast drags back', not stuck and rests, dict(stuck=stuck))

def first_site_ticks_off(q, R):
    # owner 18 Nov, his screenshot (2026-11-18-first-site-too-strict.png): bottom row four mudbricks, middle row a small square, three
    # mudbricks, a small square, top row three mudbricks, a narrow gap, and the last mudbrick sticking out past the plan's right edge
    # by about a quarter of its length: the button must turn green
    click(q, 'broom'); wait_game(q, 1.5)
    X = q.evaluate("()=>__tb.LEVEL_X0")
    his = [('block', 'mudbrick', x - X, 0.5) for x in (17, 19, 21, 23)] + [('square', 'mudbrick', 16.5 - X, 1.5)] + [('block', 'mudbrick', x - X, 1.5) for x in (18, 20, 22)] + [('square', 'mudbrick', 23.5 - X, 1.5)] + [('block', 'mudbrick', x - X, 2.5) for x in (17, 19, 21, 23.53)]
    build(q, his); green = until(q, "()=>__tb.testReady()", 6)
    R.step("the owner's first-site build turns the button green", green, dict(colour=test_colour(q), pieces=q.evaluate("()=>__tb.pieces.map((p)=>[p.defKey[0],p.material[0],+(p.body.getPosition().x-__tb.LEVEL_X0).toFixed(2),+p.body.getPosition().y.toFixed(2),+p.body.getAngle().toFixed(2)])")))
    # owner 18 Nov: "if a piece is on the headpiece place ... only its part that is inside the headpiece outline should be red": a
    # wooden block on top across the dots, the red button
    tgt = q.evaluate("()=>{const s=__tb.worldToScreen(18.6,3.6); return [s.x,s.y];}")
    carry(q, a_pile_piece(q, 'wood'), tgt, hold=0.6); wait_game(q, 1.5)
    pts = q.evaluate("""()=>{const T=__tb; const p=T.pieces[T.pieces.length-1]; let x0=1e9,x1=-1e9; for(let f=p.body.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); x0=Math.min(x0,bb.lowerBound.x); x1=Math.max(x1,bb.upperBound.x);}
      const on=T.worldToScreen((Math.max(x0,18.4)+Math.min(x1,21.6))/2,3.25), off=x1<21.2?T.worldToScreen((x1+21.6)/2,3.25):T.worldToScreen((18.4+x0)/2,3.25); return {on:[on.x,on.y], off:[off.x,off.y]};}""")
    rb = lambda pt: (lambda v: v[0] - v[2])(pixel(q, pt))
    b_on, b_off = rb(pts['on']), rb(pts['off'])
    click(q, 'test'); zone = until(q, "()=>!!(__tb.failShow&&__tb.failShow.loadZone)", 2, 0.005)
    seen_on, seen_off = [], []  # the red flashes: the most red seen at each point over a moment
    for _ in range(12): seen_on.append(rb(pts['on'])); seen_off.append(rb(pts['off'])); time.sleep(0.02)
    a_on, a_off = max(seen_on), max(seen_off)
    R.step('only the part of a piece inside the headpiece outline turns red', zone and a_on - b_on > 12 and abs(a_off - b_off) < 8, dict(on=(b_on, a_on), off=(b_off, a_off)))
    # the wood taken off again; owner 17 Nov late: "i had teaching turned off, but the 'click here to go back to the map' and 'well
    # done, your monument withstood the tests' cues played"; the test runs with every tick off
    wait_game(q, 1); p = site_pieces(q)[-1]; drag(q, p, [q.evaluate("()=>__tb.buildingWidthPx") + 60, p[1] - 120], hold=0.3)
    green = until(q, "()=>__tb.testReady()", 8); m = mark(q)
    if green: click(q, 'test')
    started = until(q, "()=>!!__tb.test", 3); passed = until(q, "()=>!!__tb.progress.done.mastaba&&!__tb.test", 90); wait_game(q, 4); silent(q, 10)
    s = said(q, m)
    R.step('ticks off: the test runs and passes, without "it withstood" or "back to the map"', green and started and passed and 104 not in s and 106 not in s, dict(green=green, started=started, passed=passed, said=s))
    # owner 23 Nov: the test button grey after the pass "unless the kid presses the shovel, or moves an item"
    seen = dict(after_pass=test_colour(q))
    ps = site_pieces(q); ytop = min(p[1] for p in ps); top = min((p for p in ps if p[1] < ytop + 10), key=lambda p: p[0])
    drag(q, top, (top[0], top[1] - 4), steps=4, hold=0.3); wait_game(q, 1.5); seen['after_moving_a_piece'] = test_colour(q)
    click(q, 'broom'); wait_game(q, 1.5); seen['after_shovel'] = test_colour(q)
    R.step('test button grey after a pass, green once a piece moves, red after the shovel', seen == dict(after_pass='grey', after_moving_a_piece='green', after_shovel='red'), seen)

def data_rules(q, R):
    # owner 18 Nov: "give istar 4 wooden planks instead of 4 std blocks": the wood of its pile, as the game makes it (its site is not yet reached by this run)
    wood = q.evaluate("""()=>{const L=__tb.LEVELS.find(l=>l.key==='ishtar'), c={}; let pulled=false;
      for(const [d,m] of L.solution){ if(d==='pull'){pulled=true; continue;} if(m==='wood'&&!pulled) c[d]=(c[d]||0)+1; }
      for(const [d,m,n] of L.extra||[]) if(m==='wood') c[d]=(c[d]||0)+n; return c;}""")
    R.step('Ishtar gate: four wooden planks', wood.get('beam') == 4 and not wood.get('block'), wood)

def whole_game(b):
    q, R = page(b), Run()
    try:
        start_and_map(q, R)
        first_site_lessons(q, R)
        first_site_build_and_test(q, R)
        finished_site(q, R)
        off_map, reopened = damaged_site(q, R)
        music_back(q, R, off_map, reopened)
        failing_test(q, R)
        map_taps(q, R)
        second_site(q, R)
        t_first = map_boats_and_stones(q, R)
        later_sites(q, R)
        stones_gone(q, R, t_first)
        restart_and_ticks_off(q, R)
        hand_and_pile(q, R)
        first_site_ticks_off(q, R)
        data_rules(q, R)
    except SystemExit: pass
    except Exception as e: R.step('the run went on to the end', False, 'error: ' + str(e).splitlines()[0][:300])
    q.close()

# --------------------------------------------------------------------
# SECTION: RUNNER
# --------------------------------------------------------------------
FLOWS = {'whole-game': whole_game}
def run(b, names):
    t = time.time()
    for n in (names or FLOWS): FLOWS[n](b)
    print('whole run %.0f s' % (time.time() - t))
