# Flow tests: what the owner does, done the way he does it, in the running game (real frames, real mouse clicks,
# real keys, cues and voice on). Run: python3 tools/harness.py flows [names]. Each flow starts from a fresh page
# with no saved progress. Every flow prints one line: PASS or FAIL, its name, and on failure what was seen.
# Keep each flow short: skip the voice with ESC where waiting adds nothing, poll often, give up fast.
import time

def page(b):
    q = b.new_page(viewport={'width': 1280, 'height': 800})
    q.goto('file:///tmp/tb-real.html')
    q.evaluate("()=>{try{localStorage.clear()}catch(e){}}")
    q.reload()
    q.wait_for_function("()=>!!window.__tb")
    return q

def until(q, js, secs, step=0.05):  # wait until js is true in the page; False if it never is within secs
    end = time.time() + secs
    while time.time() < end:
        if q.evaluate(js): return True
        time.sleep(step)
    return False

def button(q, bid):  # a screen button's middle, by its id
    return q.evaluate("(id)=>{const b=__tb.screenButtons().find((x)=>x.id===id); if(!b) return null; return b.rect?[b.rect.x+b.rect.w/2,b.rect.y+b.rect.h/2]:[b.x,b.y];}", bid)

def click(q, bid):
    p = button(q, bid)
    if not p: return False
    q.mouse.click(p[0], p[1]); time.sleep(0.05); return True

def quiet(q, secs=3):  # the child skips whatever the voice is saying (ESC), until it is quiet
    end = time.time() + secs
    while time.time() < end and q.evaluate("()=>!!__tb.voice.cur||__tb.voice.queue.length>0"):
        q.keyboard.press('Escape'); time.sleep(0.15)

def untick_all(q):  # the gear, every tick off, close
    click(q, 'settings'); time.sleep(0.1)
    for rid in q.evaluate("()=>__tb.screenButtons().filter((b)=>b.rect).map((b)=>b.id)"):
        if q.evaluate("(id)=>{const r=__tb.SETTINGS.find((s)=>s.id===id); return r?r.on():false}", rid): click(q, rid)
    click(q, 'settings-close')

def quick_build_and_test(q, hold=False):  # Ctrl held: the quick build; let go (or keep holding); then the green button, as soon as it is green
    q.keyboard.down('Control'); time.sleep(0.1)
    ok = until(q, "()=>{const b=__tb.screenButtons().find((x)=>x.id==='autobuild'); return !!(b&&b.enabled);}", 60) and click(q, 'autobuild')
    built = ok and until(q, "()=>!__tb.auto", 30)
    if not hold: q.keyboard.up('Control')
    green = built and until(q, "()=>__tb.testReady()", 10)
    if green: click(q, 'test')
    started = green and until(q, "()=>!!__tb.test", 3)
    moving = started and until(q, "()=>!!__tb.progress.done.mastaba||(__tb.test&&__tb.test.phase==='fail')", 60) # the test runs to its end: passed (the site is finished) or failed
    if hold: q.keyboard.up('Control')
    return dict(autobuild_button=ok, built=built, green=green, test_started=started, test_running=moving,
                state=q.evaluate("()=>({done:!!__tb.progress.done.mastaba, test:__tb.test&&{phase:__tb.test.phase,t:__tb.test.t}, line:__tb.voice.cur&&__tb.voice.cur.n, holding:__tb.attention(), mode:__tb.mode})"))

def first_site_ticks_off(b):
    # owner 17 Nov: "I refresh everything, have teaching and all cues and videos disabled, I go in first lvl, I fast
    # build with ctrl, and then I click the green button, the 'lets see if it will stand' cue plays, but no test starts"
    q = page(b)
    q.mouse.click(640, 400); quiet(q)  # first touch (sound allowed), welcome skipped
    untick_all(q)
    ticks = q.evaluate("()=>__tb.SETTINGS.map((s)=>s.on())")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    r = quick_build_and_test(q, hold=True); r['ticks'] = ticks
    q.close()
    return r['test_running'] and not any(ticks), r

def first_site_ticks_on(b):
    # the same with the ticks on, teaching finished (the parent's quick build and test still work)
    q = page(b)
    q.mouse.click(640, 400); quiet(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    r = quick_build_and_test(q, hold=True)
    q.close()
    return r['test_running'], r

def drag(q, a, b, steps=20, hold=0):  # a real mouse drag, at about the rate a hand moves; hold: seconds kept still at the end (the piece catches up)
    q.mouse.move(a[0], a[1]); q.mouse.down(); time.sleep(0.05)
    for k in range(1, steps + 1): q.mouse.move(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps); time.sleep(0.015)
    if hold: time.sleep(hold)
    q.mouse.up(); time.sleep(0.05)

def pile_piece(q, material):  # the screen point of a resting pile piece of that material
    return q.evaluate("(m)=>{const T=__tb; const b=T.pileBodies().find((x)=>x.pileItem.material===m&&x.getLinearVelocity().length()<0.05); if(!b) return null; const p=b.getPosition(), r=T.pileBinRect; return [r.x+p.x*T.pileScale, r.y+r.h-p.y*T.pileScale];}", material)  # the pile has its own place and scale on the screen

def later_launch(q):  # not the very first launch (its "press here to start" step lets only the first site be touched)
    q.evaluate("()=>{const m=__tb.cueMem(); m.ever=m.ever||{}; for (const id of ['welcome-first','map-start-step']) m.ever[id]=1; __tb.active.length=0;}")

def restart_load_screen(b):
    # owner 17 Nov: the restart button shows the load screen again, so the player sees the game start over
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.progress.done.mastaba={pieces:[],loads:[]}}")
    click(q, 'restart'); time.sleep(0.3); click(q, 'restart')
    shown = until(q, "()=>!!document.getElementById('load-screen')", 1)
    gone = shown and until(q, "()=>!document.getElementById('load-screen')", 4)
    r = dict(load_screen_shown=shown, then_gone=gone, progress_erased=q.evaluate("()=>!__tb.progress.done.mastaba"), mode=q.evaluate("()=>__tb.mode"))
    q.close()
    return shown and gone and r['progress_erased'], r

def child_action_cuts_line(b):
    # owner 17 Nov: "I click a site I should go, and the line doesnt play because the restart warning plays. New rule:
    # every interaction that is the result of my action stops the previous visual/audio cue and starts the new one"
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    click(q, 'restart'); playing91 = until(q, "()=>__tb.voice.cur&&__tb.voice.cur.n===91", 1)
    click(q, 'site:mastaba')
    intro = until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 0.5)
    r = dict(restart_line_playing=playing91, intro_at_once=intro, line=q.evaluate("()=>__tb.voice.cur&&__tb.voice.cur.n"), glows=q.evaluate("()=>__tb.active.filter((a)=>(a.targets||[]).some((t)=>t.btn==='restart')).length"))
    q.close()
    return playing91 and intro and r['glows'] == 0, r

def ticks_off_lines_play(b):
    # owner 17 Nov: "a lot of cues dont play when I have teaching clicked off. teaching is only the 1st lvl tutorials, and
    # the first time I explain the tests": with both ticks off, the first pick-up of a mudbrick and the red button still speak
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q, 5)
    p = pile_piece(q, 'mudbrick'); drag(q, p, (300, 400)); pick = until(q, "()=>__tb.voice.cur&&__tb.voice.cur.n===78", 1)
    quiet(q); click(q, 'test'); red = until(q, "()=>__tb.voice.cur&&__tb.voice.cur.n===70", 1)
    r = dict(first_mudbrick_line=pick, red_button_line=red, said=q.evaluate("()=>__tb.soundLog.slice(-5)"))
    q.close()
    return pick and red, r

def test_end_sounds(b):
    # owner 17 Nov: "the success (and maybe the failure) audio in the lvls, after the test, are quite delayed": the time
    # from the earthquake's end to the cheer, and to the win line, at normal speed
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.keyboard.down('Control'); time.sleep(0.1); click(q, 'autobuild'); until(q, "()=>!__tb.auto", 30)
    until(q, "()=>__tb.testReady()", 10)  # Ctrl still held: the test runs fast until the earthquake, which runs at normal speed (what is timed)
    q.evaluate("()=>{const f=()=>{const t=__tb.test; if(t&&t.phase==='quake') t.fast=false; requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    q.evaluate("""()=>{const T=__tb; window.__tl=[]; let ph=null, n=T.soundLog.length, ln=null; const t0=performance.now();
      const f=()=>{const t=((performance.now()-t0)/1000).toFixed(2); const p=T.test?T.test.phase:'none'; if(p!==ph){__tl.push(t+' phase '+p); ph=p;}
        if(T.soundLog.length){for(const x of T.soundLog) if(!x.startsWith('music')) __tl.push(t+' sound '+x); T.soundLog.length=0;} const l=T.voice.cur&&T.voice.cur.n; if(l!==ln){__tl.push(t+' line '+l); ln=l;}
        if(performance.now()-t0<70000) requestAnimationFrame(f);}; requestAnimationFrame(f);}""")
    click(q, 'test'); q.keyboard.up('Control')
    end = time.time() + 60
    while time.time() < end and not q.evaluate("()=>!!__tb.progress.done.mastaba||(__tb.test&&__tb.test.phase==='fail')"):
        if q.evaluate("()=>[101,102,103].includes(__tb.voice.cur&&__tb.voice.cur.n)"): q.keyboard.press('Escape')  # the test's explanations skipped, as a parent would
        time.sleep(0.05)
    time.sleep(7)
    tl = q.evaluate("()=>__tl")
    q.close()
    def at(word):
        for e in tl:
            if word in e: return float(e.split()[0])
    ch = at('sound cheer')
    quake_end = next((float(e.split()[0]) for k, e in enumerate(tl) if 'phase settle' in e and any('phase quake' in x for x in tl[:k])), None)
    tl = [e for e in tl if 'hit-' not in e and 'drag-' not in e and 'map-tap' not in e]
    r = dict(timeline=tl[-14:], cheer_after_quake=(ch - quake_end) if ch and quake_end else None)
    wl = next((float(e.split()[0]) for e in tl if e.endswith(' line 14')), None)
    r['win_line_after_quake'] = (wl - quake_end) if wl and quake_end else None
    return bool(ch and quake_end and wl and ch - quake_end <= 0.7 and wl - ch <= 1.3), r

def record(q):  # from now on: every line said, the music's share while a test runs, and the headpiece's dotted outline drawn while a headpiece is on
    q.evaluate("""()=>{const T=__tb; window.__rec={said:[],duckInTest:[],ghostWithLoad:0}; let ln=null; const g=T.SKIN.loadGhost;
      T.SKIN.loadGhost=function(...a){ if(T.loads.length&&!T.test) __rec.ghostWithLoad++; return g.apply(this,a); };
      const f=()=>{const l=T.voice.cur&&T.voice.cur.n; if(l!==ln){ if(l!=null) __rec.said.push(l); ln=l; } if(T.test) __rec.duckInTest.push(T.musicDuck); requestAnimationFrame(f);}; requestAnimationFrame(f);}""")

def ticks_off_first_win(b):
    # owner 17 Nov late: "i had teaching turned off, but the 'click here to go back to the map' and 'well done, your monument
    # withstood the tests' cues played"; "when the tests are playing, the music should fade off"; "the headpiece outline
    # shouldn't disappear when the headpiece comes down": both ticks off, first site, Ctrl quick build, green button, the test passes
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    record(q)
    r = quick_build_and_test(q, hold=True)
    until(q, "()=>!__tb.test", 15); time.sleep(1); until(q, "()=>!__tb.voice.cur&&!__tb.voice.queue.length", 20); time.sleep(2)  # the win line and whatever follows it
    rec = q.evaluate("()=>__rec"); q.close()
    r.update(said=rec['said'], music_in_test=sorted(set(rec['duckInTest']))[:4], outline_drawn_with_headpiece=rec['ghostWithLoad'])
    ok = r['state']['done'] and 104 not in rec['said'] and 106 not in rec['said'] and rec['duckInTest'] and rec['duckInTest'][-1] == 0 and rec['ghostWithLoad'] > 0
    return ok, r

def red_outside(b):
    # owner 17 Nov late: "show with red areas that are NOT filled while they should, and areas that ARE filled while they
    # shouldn't ... all the part of that mudbrick that is outside the design should be red"; "we work with straight lines":
    # a mudbrick laid on the ground across the plan's right edge, the red button: the part outside the plan turns red
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    edge = q.evaluate("()=>{const T=__tb; let x=-1e9; for(const r of T.grid.solid) for(const [a,b] of r) if(b<0.5) x=Math.max(x,a); const s=T.worldToScreen(x,0.35), t=T.worldToScreen(x+0.45,0.6); return [s.x,s.y,x,t.x,t.y];}")
    drag(q, pile_piece(q, 'mudbrick'), (edge[3], edge[4]))
    until(q, "()=>__tb.pieces.length===1&&__tb.pieces[0].body.getLinearVelocity().length()<0.02&&Math.abs(__tb.pieces[0].body.getAngularVelocity())<0.02", 4)
    box = q.evaluate("""(ex)=>{const T=__tb, p=T.pieces[0]; let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9; for(let f=p.body.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); x0=Math.min(x0,bb.lowerBound.x); x1=Math.max(x1,bb.upperBound.x); y0=Math.min(y0,bb.lowerBound.y); y1=Math.max(y1,bb.upperBound.y);}
      const a=T.worldToScreen((ex+x1)/2,(y0+y1)/2), c=T.worldToScreen((x0+ex)/2,(y0+y1)/2); return {out:[a.x,a.y], outW:(x1-ex), inW:(ex-x0)};}""", edge[2])
    px = lambda pt: q.evaluate("(p)=>{const c=document.querySelector('canvas'), d=window.devicePixelRatio||1, v=c.getContext('2d').getImageData(Math.round(p[0]*d),Math.round(p[1]*d),1,1).data; return v[0]-v[1];}", pt)
    before = px(box['out'])
    click(q, 'test'); time.sleep(0.05)
    after = max(px(box['out']) for _ in range(12) if time.sleep(0.04) is None)
    r = dict(piece_outside_m=round(box['outW'], 2), inside_m=round(box['inW'], 2), red_before=before, red_after=after, fail=q.evaluate("()=>__tb.failShow&&{unfilled:__tb.failShow.unfilled,n:(__tb.failShow.counted||[]).length}"))
    q.close()
    return box['outW'] > 0.2 and box['inW'] > 0.2 and after - before > 12, r

def map_point(q, test):  # a screen point on the map where test(mx, my) holds, near the middle of the screen first
    return q.evaluate("""(t)=>{const T=__tb, v=T.mapView(), f=new Function('T','mx','my','return '+t);
      for(let r=0;r<900;r+=5) for(let a=0;a<6.28;a+=Math.min(0.2,4/Math.max(r,1))){const x=640+r*Math.cos(a), y=400+r*Math.sin(a)*0.7, mx=(x-v.ox)/v.k, my=(y-v.oy)/v.k; if(x>40&&x<1100&&y>100&&y<760&&!T.screenButtons().some((b)=>b.rect?(x>b.rect.x-10&&x<b.rect.x+b.rect.w+10&&y>b.rect.y-10&&y<b.rect.y+b.rect.h+10):Math.hypot(x-b.x,y-b.y)<(b.r||b.size||60)+10)&&f(T,mx,my)) return [x,y];} return null;}""", test)

def map_water(b):
    # owner 17 Nov late: "dont do water particle effects on rivers and small lakes"; "wave circles should stop at land, not
    # continue on land, but ... stop there with their white thing going at the beach": a tap on the sea by a coast, a tap on a river
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    coast = map_point(q, "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&[0,1,2,3,4,5,6,7].some((k)=>T.groundAt(mx+40*Math.cos(k*0.785)/v.k,my+24*Math.sin(k*0.785)/v.k)!=='water')".replace('v.k','T.mapView().k'))
    river = map_point(q, "T.groundAt(mx,my)==='water'&&T.isLand(mx,my)")
    q.evaluate("()=>{__tb.tapBits.length=0}"); q.mouse.click(*coast); time.sleep(0.05)
    rings = q.evaluate("()=>__tb.tapBits.filter((t)=>t.kind==='ring').map((t)=>Array.from(t.stop||[]).filter((x)=>isFinite(x)).length)")
    q.evaluate("()=>{__tb.tapBits.length=0}"); q.mouse.click(*river); time.sleep(0.05)
    drops = q.evaluate("()=>__tb.tapBits.filter((t)=>t.kind==='drop').length")
    r = dict(coast=coast, river=river, ring_dirs_stopped_by_land=rings, drops_on_river=drops)
    q.close()
    return bool(coast and river and rings and min(rings) > 0 and drops == 0), r

def map_stones(b):
    # owner 17 Nov late: "grab stones from the mountain and drop them on the sea (many small splashes) or on the land (they stay
    # there, 3d small cubes, and disappear after 1 min ...), they can pile up, or collide with the boats"
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.progress.done.mastaba={pieces:[],loads:[]}}"); until(q, "()=>__tb.boats.length>0", 2)  # a finished site: its boat sails
    rock = map_point(q, "T.groundAt(mx,my)==='rock'")
    land = map_point(q, "['green','sand'].includes(T.groundAt(mx,my))&&T.sandArea(mx,my)<0&&!T.boats.some((b)=>Math.hypot(b.x-mx,b.y-my)<80)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+70*Math.cos(k*0.785),my+70*Math.sin(k*0.785))!=='water')")
    sea = map_point(q, "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&!T.boats.some((b)=>Math.hypot(b.x-mx,b.y-my)<80)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+90*Math.cos(k*0.785),my+90*Math.sin(k*0.785))==='water')")  # open sea: what bounces off a boat lands in water
    n = lambda: q.evaluate("()=>__tb.mapStones.length")
    rest = "()=>__tb.mapStones.every((s)=>!s.held&&!s.vz&&!s.vx&&!s.vy)"
    drag(q, rock, land, hold=0.3); time.sleep(0.15); five = until(q, "()=>__tb.mapStones.length===5", 1) and until(q, rest, 2)
    held_gone = five and q.evaluate("()=>__tb.mapStones.filter((s)=>s.z===0).length>=4")
    drag(q, rock, land, hold=0.3); time.sleep(0.15); piled = until(q, rest, 2) and q.evaluate("()=>__tb.mapStones.length===10&&__tb.mapStones.some((s)=>s.z>__tb.STONE*0.9)")
    q.evaluate("()=>{__tb.tapBits.length=0}")
    q.evaluate("()=>{window.__wet=0; const touch=new Map(); const end=performance.now()+2500; const f=()=>{ const now=performance.now(); for(const s of __tb.mapStones) if(!s.held&&s.z<1&&!s.on&&__tb.groundAt(s.x,s.y)==='water'&&!touch.has(s)) touch.set(s,now); for(const [s,t0] of touch) if(__tb.mapStones.includes(s)) __wet=Math.max(__wet,(now-t0)/1000); if(now<end) requestAnimationFrame(f);}; requestAnimationFrame(f);}")  # owner 18 Nov: "stones stand on water a bit and then sink ... just sink"
    q.evaluate("()=>{__tb.soundLog.length=0}")
    drag(q, rock, sea, hold=0.3); time.sleep(0.15); sank = until(q, "()=>__tb.mapStones.length===10&&__tb.tapBits.filter((t)=>t.kind==='ring').length>=4", 2)
    time.sleep(1.0); on_water_left = q.evaluate("()=>window.__wet")
    splashes = q.evaluate("()=>__tb.soundLog.filter((x)=>x==='map-tap-water').length")  # owner 18 Nov: five stones into the water sound like one tap on the water
    q.evaluate("()=>{const T=__tb; T.mapStones.splice(0,T.mapStones.length);}")
    drag(q, rock, land, hold=0.3); time.sleep(0.15); until(q, rest, 2)
    q.evaluate("()=>{const T=__tb, b=T.mapStones.find((s)=>s.z===0), t=T.mapStones.find((s)=>s.on===b); for(const s of T.mapStones) if(s!==b&&s!==t) s.age=0; if(t){b.age=59.95;} window.__top=t;}")
    fell = until(q, "()=>!window.__top||(__tb.mapStones.includes(window.__top)&&window.__top.z===0)", 2)
    # thrown: a quick drag let go while moving: the stones land on beyond where the finger let go
    q.evaluate("()=>{__tb.mapStones.splice(0)}")
    # owner 18 Nov: "they do a sudden drop-and-slide motion, its not smooth": one stone's speed over the ground, frame by frame, from the throw to rest
    flat = map_point(q, "Array.from({length:60},(_,k)=>k).every((k)=>{const v=T.mapView(), x=mx+k*5/v.k; return [-20,0,20].every((dy)=>['green','sand'].includes(T.groundAt(x,my+dy/v.k)))&&T.sandArea(x,my)<0;})")  # dry land, no river, for 300 px to the right
    q.evaluate("()=>{window.__slide=0; window.__sp=[]; window.__slideEnd=performance.now()+9000; const seen=new Map(); let one=null, last=null; const f=()=>{for(const s of __tb.mapStones){ if(s.held||s.z>0.01){seen.delete(s);continue;} if(!seen.has(s)) seen.set(s,[s.x,s.y]); const [x,y]=seen.get(s); __slide=Math.max(__slide,Math.hypot(s.x-x,s.y-y)); } if(!one) one=__tb.mapStones.find(s=>!s.held&&s.vz!==undefined&&(s.vx||s.vy)); if(one){ if(one.roll&&!window.__inroll){ window.__tips=(window.__tips||0)+1; } window.__inroll=!!one.roll; if(one.roll) window.__rolled=true; if(one.z>0.01||one.held) window.__land=null; else if(!window.__land) window.__land=[one.x,one.y]; if(window.__land) window.__gs=Math.hypot(one.x-__land[0],one.y-__land[1]); } if(performance.now()<window.__slideEnd) requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    q.mouse.move(*rock); q.mouse.down(); time.sleep(0.05)
    for k in range(1, 21): q.mouse.move(rock[0] + (flat[0] - rock[0]) * k / 20, rock[1] + (flat[1] - rock[1]) * k / 20); time.sleep(0.016)
    time.sleep(0.4); q.evaluate("()=>{__tb.soundLog.length=0; window.__rockTaps=0; const end=performance.now()+3500; let n=0; const f=()=>{ const L=__tb.soundLog; if(L.length<n) n=0; for(;n<L.length;n++) if(L[n]==='map-tap-rock') __rockTaps++; if(performance.now()<end) requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    q.mouse.move(flat[0] + 120, flat[1], steps=4); q.mouse.up()  # a throw to the right: the browser here sends a move about every 55 ms, so 30 px a move is about 550 px a second
    far_end = (flat[0] + 120, flat[1])
    until(q, rest, 3)
    slide = q.evaluate("()=>window.__gs||0")  # owner 18 Nov: "the thrown stones slide too much on land": at most about their own size
    rolled = q.evaluate("()=>!!window.__rolled")  # owner 18 Nov: "make stones not slide but ... roll like cubes roll"
    tips = q.evaluate("()=>window.__tips||0")  # owner 18 Nov: "even when I throw with force they don't roll a lot"
    rock_taps = q.evaluate("()=>window.__rockTaps")  # owner 18 Nov: "remove the rolling sounds": one landing knock per stone, nothing while tipping
    thrown = q.evaluate("(p)=>{const T=__tb, v=T.mapView(), mx=(p[0]-v.ox)/v.k; if(!T.mapStones.length) return null; return T.mapStones.reduce((a,s)=>a+s.x,0)/T.mapStones.length - mx;}", far_end)
    # onto a boat on the water: a knock, they bounce off and sink, and the boat's people groan
    q.evaluate("()=>{__tb.mapStones.splice(0); __tb.soundLog.length=0;}")
    q.evaluate("(p)=>{const T=__tb, v=T.mapView(), b=T.boats[0]; b.held=b.back=b.drop=null; b.stuck=true; b.ox=b.oy=b.ovx=b.ovy=0; b.x=(p[0]-v.ox)/v.k; b.y=(p[1]-v.oy)/v.k+30*0.866;}", sea)
    drag(q, rock, sea, hold=0.3); time.sleep(0.05)  # held still over the boat, then let go
    bounced = until(q, "()=>__tb.soundLog.includes('map-stone-boat')", 3) and until(q, "()=>__tb.mapStones.length===0", 5)
    groan = q.evaluate("()=>__tb.soundLog.includes('boat-left-on-land')")
    knocks = q.evaluate("()=>__tb.soundLog.filter((x)=>x==='map-stone-boat').length")  # five stones landing together: one knock
    q.evaluate("()=>{__tb.mapStones.push({x:0,y:0,z:0,vz:0,vx:0,vy:0,rise:1,held:null,on:null,age:0,yaw:0,grey:140})}")
    q.evaluate("(p)=>{const T=__tb, v=T.mapView(), b=T.boats[0], s=T.mapStones[0], mx=(p[0]-v.ox)/v.k, my=(p[1]-v.oy)/v.k; b.held=b.back=b.drop=null; b.stuck=true; b.ox=b.oy=b.ovx=b.ovy=0; b.x=mx; b.y=my; s.x=mx+2; s.y=my;}", land); time.sleep(0.2)
    pushed = q.evaluate("()=>{const T=__tb, b=T.boats[0], s=T.mapStones[0]; return !!s && Math.hypot(s.x-b.x,s.y-b.y)>=56*0.35+6-0.5;}")
    r = dict(rock=rock, land=land, sea=sea, five_land_and_stay=held_gone, piles=piled, sinks_with_splashes=sank, seconds_on_the_water=round(on_water_left, 2), splash_sounds=splashes, top_falls_when_bottom_goes=fell, thrown_beyond_px=thrown, moved_after_landing_px=round(slide, 1), tipped_over=rolled, tips=tips, rock_sounds=rock_taps, boat_knock_and_sink=bounced, boat_groans=groan, knocks=knocks, boat_pushes=pushed, stones=n())
    q.close()
    return bool(rock and land and sea and held_gone and piled and sank and fell and thrown and thrown > 30 and rock_taps <= 5 and on_water_left < 0.05 and splashes == 1 and bounced and groan and knocks <= 2 and pushed), r

def test_fail_sounds(b):
    # owner 18 Nov: "is there a test for the failure too?": a building that does not hold (one mudbrick, the test forced with
    # Ctrl); the failure's sound at the moment it fails, at normal speed
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    drag(q, pile_piece(q, 'mudbrick'), (400, 500)); time.sleep(0.8)
    q.evaluate("""()=>{const T=__tb; window.__tl=[]; let ph=null; const t0=performance.now(); T.soundLog.length=0;
      const f=()=>{const t=(performance.now()-t0)/1000; if(T.test) T.test.fast=false; const p=T.test?T.test.phase:'none'; if(p!==ph){__tl.push([t,'phase',p]); ph=p;}
        for(const x of T.soundLog) if(!x.startsWith('music')&&!x.startsWith('hit-')&&!x.startsWith('drag-')) __tl.push([t,'sound',x]); T.soundLog.length=0; if(t<30) requestAnimationFrame(f);}; requestAnimationFrame(f);}""")
    q.keyboard.down('Control'); time.sleep(0.1); click(q, 'test'); q.keyboard.up('Control')
    until(q, "()=>__tb.test&&__tb.test.phase==='fail'", 20); time.sleep(0.5)
    tl = q.evaluate("()=>__tl"); q.close()
    f = next((e[0] for e in tl if e[1] == 'phase' and e[2] == 'fail'), None); snd = next((e[0] for e in tl if e[1] == 'sound' and e[2] == 'fail'), None)
    r = dict(timeline=[(round(e[0], 2), e[1], e[2]) for e in tl][-8:], sound_after_fail=round(snd - f, 3) if f is not None and snd is not None else None)
    return f is not None and snd is not None and abs(snd - f) <= 0.1, r

def red_headpiece_place(b):
    # owner 18 Nov: "if a piece is on the headpiece place, all of it turns red, but ... only its part that is inside the
    # headpiece outline should be red": the first site quick-built, a wooden block put on top across the dots, the red button
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.keyboard.down('Control'); time.sleep(0.1); click(q, 'autobuild'); until(q, "()=>!__tb.auto", 30); q.keyboard.up('Control'); time.sleep(3.3)
    tgt = q.evaluate("()=>{const s=__tb.worldToScreen(18.6,3.6); return [s.x,s.y];}")
    a0 = pile_piece(q, 'wood'); up = (a0[0], tgt[1] - 60)  # lifted up first, then over the building, as a hand does
    q.mouse.move(*a0); q.mouse.down(); time.sleep(0.05)
    for (x0, y0), (x1, y1) in ((a0, up), (up, tgt)):
        for k in range(1, 31): q.mouse.move(x0 + (x1 - x0) * k / 30, y0 + (y1 - y0) * k / 30); time.sleep(0.015)
        time.sleep(0.6)
    q.mouse.up(); time.sleep(1.5)
    pts = q.evaluate("""()=>{const T=__tb; const p=T.pieces[T.pieces.length-1]; let x0=1e9,x1=-1e9; for(let f=p.body.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); x0=Math.min(x0,bb.lowerBound.x); x1=Math.max(x1,bb.upperBound.x);}
      const on=T.worldToScreen((Math.max(x0,18.4)+Math.min(x1,21.6))/2,3.25), off=x1<21.2?T.worldToScreen((x1+21.6)/2,3.25):T.worldToScreen((18.4+x0)/2,3.25); return {on:[on.x,on.y], off:[off.x,off.y], x0, x1};}""")
    px = lambda pt: q.evaluate("(p)=>{const c=document.querySelector('canvas'), d=window.devicePixelRatio||1, v=c.getContext('2d').getImageData(Math.round(p[0]*d),Math.round(p[1]*d),1,1).data; return v[0]-v[2];}", pt)
    b_on, b_off = px(pts['on']), px(pts['off'])
    click(q, 'test'); time.sleep(0.05); until(q, "()=>Math.sin(performance.now()/120)>0.9", 1, 0.005)
    a_on, a_off = px(pts['on']), px(pts['off'])
    r = dict(piece_x=(round(pts['x0'], 2), round(pts['x1'], 2)), on_piece=(b_on, a_on), dots_beside_piece=(b_off, a_off), zone=q.evaluate("()=>!!(__tb.failShow&&__tb.failShow.loadZone)"))
    q.close()
    return r['zone'] and a_on - b_on > 12 and abs(a_off - b_off) < 8, r

def owner_first_site_build(b):
    # owner 18 Nov, his screenshot (2026-11-18-first-site-too-strict.png): first site, bottom row four mudbricks, middle row a
    # small square, three mudbricks, a small square, top row three mudbricks, a narrow gap, and the last mudbrick sticking out
    # past the plan's right edge by about a quarter of its length: the button must turn green
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.evaluate("""()=>{const T=__tb; const put=(d,x,y)=>T.spawnPiece(d,x,y+0.002,0,'mudbrick');
      for(const x of [17,19,21,23]) put('block',x,0.5); put('square',16.5,1.5); for(const x of [18,20,22]) put('block',x,1.5); put('square',23.5,1.5);
      for(const x of [17,19,21]) put('block',x,2.5); put('block',23.53,2.5);}""")
    green = until(q, "()=>__tb.testReady()", 6)
    r = dict(green=green, check=q.evaluate("()=>{const c=__tb.runCheck(); return {fill:+c.fill.toFixed(3), out:+c.out.toFixed(3), far:c.far};}"))
    q.close()
    return green, r

def headpiece_in_hand(b):
    # owner 18 Nov: "when you go to a finished site, make it possible to grab and move headpiece as any other block ... the
    # weight of stone ... max the weight of 2x std stone blocks ... triple clicking it makes it disappear"
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    r = quick_build_and_test(q, hold=True)
    until(q, "()=>!__tb.test", 10); quiet(q); click(q, 'home'); until(q, "()=>__tb.mode==='map'", 3); time.sleep(0.3); quiet(q)
    click(q, 'site:mastaba'); until(q, "()=>__tb.mode==='build'&&__tb.loads.length===1", 3); time.sleep(1); quiet(q)
    st = q.evaluate("""()=>{const T=__tb, l=T.loads[0], c=l.body.getPosition(), s=T.worldToScreen(c.x,c.y); return {x:s.x,y:s.y,cy:c.y,blocks:T.inBlocks(l.body,'stone')};}""")
    q.evaluate("()=>{__tb.soundLog.length=0}")
    drag(q, (st['x'], st['y']), (st['x'] + 10, st['y'] - 120), steps=30)
    time.sleep(0.1); lifted = q.evaluate("()=>__tb.loads[0].body.getPosition().y") - st['cy']
    time.sleep(1.5)
    knock = q.evaluate("()=>__tb.soundLog.filter((x)=>x.startsWith('hit-')&&x.includes('stone'))")  # owner 18 Nov: it sounds as stone when it lands
    c = q.evaluate("()=>{const T=__tb, l=T.loads[0], c=l.body.getPosition(), s=T.worldToScreen(c.x,c.y); return [s.x,s.y];}")
    for _ in range(3): q.mouse.click(c[0], c[1]); time.sleep(0.08)
    gone = until(q, "()=>__tb.loads.length===0", 1)
    r = dict(mass_in_blocks=round(st['blocks'], 2), lifted_m=round(lifted, 2), stone_sound_on_landing=knock, gone_after_three_taps=gone)
    q.close()
    return r['mass_in_blocks'] <= 2.001 and lifted > 0.5 and bool(knock) and gone, r

def damaged_voice_once_per_session(b):
    # owner 18 Nov: "the voice cues for next site - damaged site must play sound not every time they trigger (only the visual
    # plays every time), the sound must play the first time they happen per site, and of course refreshing the page counts"
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.progress.done.mastaba={pieces:[],loads:[],broken:true}; localStorage.setItem('tower-builder-progress-v1', JSON.stringify(__tb.progress));}")
    record(q)
    first = until(q, "()=>__rec.said.includes(39)", 12)
    time.sleep(0.2); until(q, "()=>!__tb.voice.cur", 8); q.evaluate("()=>{__rec.said.length=0}")
    t0 = q.evaluate("()=>__tb.flashes.length"); again = until(q, "()=>__rec.said.includes(39)", 21)
    q.reload(); q.wait_for_function("()=>!!window.__tb"); record(q); q.mouse.click(640, 400)  # listening from before the first touch
    after_refresh = until(q, "()=>__rec.said.includes(39)", 12)
    r = dict(said_first=first, said_again_same_session=again, said_after_refresh=after_refresh)
    q.close()
    return first and not again and after_refresh, r

def middle_grab_bump(b):
    # owner 18 Nov: "when I hold a piece from the middle, then it does not rotate when hitting other pieces. middle grab means
    # stability": a stone block lying on the ground, grabbed in its middle, lifted and pushed with its lower edge into the top
    # corner of a stack of three stone blocks
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.evaluate("()=>{const T=__tb; T.clearAllPieces(); for(let k=0;k<3;k++) T.spawnPiece('block',20.5,0.502+k,0,'stone'); window.__mv=T.spawnPiece('block',14,0.502,0,'stone');}")
    time.sleep(0.6); quiet(q)
    a, up, tgt = q.evaluate("()=>{const T=__tb, s=(x,y)=>{const p=T.worldToScreen(x,y); return [p.x,p.y];}; return [s(14,0.5), s(14,3.25), s(19.3,3.25)];}")
    q.mouse.move(*a); q.mouse.down(); time.sleep(0.05)
    if not q.evaluate("()=>window.__mv.heldBy!=null"): q.close(); return False, dict(probe="the press did not take the block")
    q.evaluate("()=>{window.__bump={turn:0,touched:false}; const f=()=>{const b=window.__mv.body; __bump.turn=Math.max(__bump.turn,Math.abs(b.getAngle())); for(let c=b.getContactList();c;c=c.next) if(c.contact.isTouching()&&c.other.piece) __bump.touched=true; if(window.__mv.heldBy!=null) requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    for (x0, y0), (x1, y1), n in ((a, up, 20), (up, tgt, 40)):
        for k in range(1, n + 1): q.mouse.move(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n); time.sleep(0.016)
    time.sleep(1.0)
    bump = q.evaluate("()=>__bump"); touched, turn = bump['touched'], bump['turn']
    r = dict(touching_the_stack=touched, most_turn_rad=round(turn, 3), pieces=q.evaluate("()=>__tb.pieces.map(x=>x.body.getPosition().x.toFixed(2)+','+x.body.getPosition().y.toFixed(2)+'@'+x.body.getAngle().toFixed(2)).join(' ')"))
    q.mouse.up(); q.close()
    return touched and turn < 0.05, r

def sand_draw_sound(b):
    # owner 18 Nov: "give sand drawing an appropriate sound, again, same loudness as all terrain sounds"
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    p = map_point(q, "T.sandArea(mx,my)>=0&&[1,2,3,4,5,6].every((k)=>T.sandArea(mx+k*15/T.mapView().k,my)>=0)")
    q.evaluate("()=>{__tb.soundLog.length=0}")
    q.mouse.move(*p); q.mouse.down(); q.mouse.move(p[0] + 90, p[1], steps=6); time.sleep(0.1)
    heard = q.evaluate("()=>__tb.soundLog.includes('map-sand-draw')"); q.mouse.up(); q.close()
    return bool(p and heard), dict(sand_at=p, sand_sound=heard)

def ishtar_planks(b):
    # owner 18 Nov: "give istar 4 wooden planks instead of 4 std blocks": the wood of its pile, as the game makes it
    q = page(b)
    wood = q.evaluate("""()=>{const L=__tb.LEVELS.find(l=>l.key==='ishtar'), c={}; let pulled=false;
      for(const [d,m] of L.solution){ if(d==='pull'){pulled=true; continue;} if(m==='wood'&&!pulled) c[d]=(c[d]||0)+1; }
      for(const [d,m,n] of L.extra||[]) if(m==='wood') c[d]=(c[d]||0)+n; return c;}""")
    q.close()
    return wood.get('beam') == 4 and not wood.get('block'), dict(wood_in_pile=wood)

FLOWS = {'restart-load-screen': restart_load_screen, 'child-action-cuts-line': child_action_cuts_line, 'ticks-off-lines-play': ticks_off_lines_play, 'test-end-sounds': test_end_sounds, 'first-site-ticks-off': first_site_ticks_off, 'first-site-ticks-on': first_site_ticks_on, 'ticks-off-first-win': ticks_off_first_win, 'red-outside': red_outside, 'map-water': map_water, 'map-stones': map_stones, 'test-fail-sounds': test_fail_sounds, 'red-headpiece-place': red_headpiece_place, 'owner-first-site-build': owner_first_site_build, 'headpiece-in-hand': headpiece_in_hand, 'damaged-voice-once-per-session': damaged_voice_once_per_session, 'sand-draw-sound': sand_draw_sound, 'ishtar-planks': ishtar_planks}  # middle_grab_bump: waits for the owner's answer on the lever (BUILD.md update 83)

def run(b, names):
    for n, f in FLOWS.items():
        if names and n not in names: continue
        t = time.time()
        try: ok, info = f(b)
        except Exception as e: ok, info = False, 'error ' + str(e)[:300]
        print(('PASS ' if ok else 'FAIL ') + n + ' (%.1f s) ' % (time.time() - t) + ('' if ok else str(info)[:900]))
