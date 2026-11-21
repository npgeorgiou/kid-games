# Flow tests: what the owner does, done the way he does it, in the running game (real frames, real mouse clicks,
# real keys, cues and voice on). Run: python3 tools/harness.py flows [names]. Each flow starts from a fresh page
# with no saved progress. Every flow prints one line: PASS or FAIL, its name, and on failure what was seen.
# Keep each flow short: skip the voice with ESC where waiting adds nothing, poll often, give up fast.
import time
import tempfile; TMP = tempfile.gettempdir()  # the commit gate runs old and new code at once, each with its own TMPDIR

# --------------------------------------------------------------------
# SECTION: HELPERS -- the page, waiting, buttons, the mouse, pile pieces, recording what is said
# --------------------------------------------------------------------
def page(b):
    q = b.new_page(viewport={'width': 1280, 'height': 800})
    q.goto('file://'+TMP+'/tb-real.html')
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

def quiet(q, secs=3):  # whatever the voice is saying is skipped, until it is quiet: on the map with ESC as the child does; in a site
    end = time.time() + secs  # ESC leaves the site (owner 18 Nov), so there the test switches the line off itself
    while time.time() < end and q.evaluate("()=>!!__tb.voice.cur||__tb.voice.queue.length>0"):
        if q.evaluate("()=>__tb.mode==='map'"): q.keyboard.press('Escape')
        else: q.evaluate("()=>{const T=__tb; if(T.voice.cur) T.endLine(T.voice.cur);}")
        time.sleep(0.15)

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

def drag(q, a, b, steps=20, hold=0):  # a real mouse drag, at about the rate a hand moves; hold: seconds kept still at the end (the piece catches up)
    q.mouse.move(a[0], a[1]); q.mouse.down(); time.sleep(0.05)
    for k in range(1, steps + 1): q.mouse.move(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps); time.sleep(0.015)
    if hold: time.sleep(hold)
    q.mouse.up(); time.sleep(0.05)

def pile_piece(q, material):  # the screen point of a resting pile piece of that material
    return q.evaluate("(m)=>{const T=__tb; const b=T.pileBodies().find((x)=>x.pileItem.material===m&&x.getLinearVelocity().length()<0.05); if(!b) return null; const p=b.getPosition(), r=T.pileBinRect; return [r.x+p.x*T.pileScale, r.y+r.h-p.y*T.pileScale];}", material)  # the pile has its own place and scale on the screen

def pile_piece_inside(q, material):  # like pile_piece, but only a piece whose middle lies inside the pile's box (one wedged in its wall cannot be grabbed there)
    return q.evaluate("(m)=>{const T=__tb, r=T.pileBinRect; const pts=T.pileBodies().filter((x)=>x.pileItem.material===m&&x.getLinearVelocity().length()<0.05).map((b)=>{const p=b.getPosition(); return [r.x+p.x*T.pileScale, r.y+r.h-p.y*T.pileScale];}).filter(([x,y])=>x>r.x+10&&x<r.x+r.w-10); return pts[0]||null;}", material)

def later_launch(q):  # not the very first launch (its "press here to start" step lets only the first site be touched)
    q.evaluate("()=>{const m=__tb.cueMem(); m.ever=m.ever||{}; for (const id of ['welcome-first','map-start-step']) m.ever[id]=1; __tb.active.length=0;}")

def record(q):  # from now on: every line said, the music's share while a test runs, and the headpiece's dotted outline drawn while a headpiece is on
    q.evaluate("""()=>{const T=__tb; window.__rec={said:[],duckInTest:[],ghostWithLoad:0}; let ln=null; const g=T.SKIN.loadGhost;
      T.SKIN.loadGhost=function(...a){ if(T.loads.length&&!T.test) __rec.ghostWithLoad++; return g.apply(this,a); };
      const f=()=>{const l=T.voice.cur&&T.voice.cur.n; if(l!==ln){ if(l!=null) __rec.said.push(l); ln=l; } if(T.test) __rec.duckInTest.push(T.musicDuck); requestAnimationFrame(f);}; requestAnimationFrame(f);}""")

def map_point(q, test):  # a screen point on the map where test(mx, my) holds, near the middle of the screen first
    return q.evaluate("""(t)=>{const T=__tb, v=T.mapView(), f=new Function('T','mx','my','return '+t);
      for(let r=0;r<900;r+=5) for(let a=0;a<6.28;a+=Math.min(0.2,4/Math.max(r,1))){const x=640+r*Math.cos(a), y=400+r*Math.sin(a)*0.7, mx=(x-v.ox)/v.k, my=(y-v.oy)/v.k; if(x>40&&x<1100&&y>100&&y<760&&!T.screenButtons().some((b)=>b.rect?(x>b.rect.x-10&&x<b.rect.x+b.rect.w+10&&y>b.rect.y-10&&y<b.rect.y+b.rect.h+10):Math.hypot(x-b.x,y-b.y)<(b.r||b.size||60)+10)&&f(T,mx,my)) return [x,y];} return null;}""", test)

# --------------------------------------------------------------------
# SECTION: SETTINGS AND LAUNCH -- the gear's ticks, the restart, buttons and music
# --------------------------------------------------------------------
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

def button_click_sound(b):
    # owner 18 Nov: "add this to all button clicks, at same volume as the terrain touch effects": the settings gear, its X, a
    # site, then in the site the broom and the map button; each press clicks once, as loud as a tap on the map
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    got = {}
    for bid in ('settings', 'settings-close', 'site:mastaba', 'broom', 'home'):
        time.sleep(0.4); quiet(q); q.evaluate("()=>{__tb.soundLog.length=0}")
        click(q, bid); time.sleep(0.15)
        got[bid] = q.evaluate("()=>__tb.soundLog.filter((x)=>x==='button-click').length")
    vol = q.evaluate("()=>[__tb.SOUNDS['button-click'][0][1], __tb.SOUNDS['map-tap-sand'][0][1]]")
    q.close()
    return all(v == 1 for v in got.values()) and vol[0] == vol[1], dict(clicks=got, gains=vol)

def music_tick(b):
    # owner 18 Nov: "make checkbox option in setting for music (main menu and level)": unticked in the settings box, no music on
    # the map or in a site, and it stays so after the page is opened again; ticked again, the music is back
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'settings'); time.sleep(0.1); click(q, 'music'); click(q, 'settings-close'); time.sleep(0.3)
    r = dict(map_off=q.evaluate("()=>__tb.musicDuck"))
    click(q, 'site:mastaba'); time.sleep(0.4); quiet(q); time.sleep(0.2)
    r['site_off'] = q.evaluate("()=>__tb.musicDuck")
    q.reload(); q.wait_for_function('()=>!!window.__tb'); q.mouse.click(640, 400); quiet(q); time.sleep(0.3)
    r['after_reopen'] = q.evaluate("()=>[__tb.SETTINGS.find((s)=>s.id==='music').on(), __tb.musicDuck]")
    click(q, 'settings'); time.sleep(0.1); click(q, 'music'); click(q, 'settings-close'); time.sleep(0.3)
    r['map_on'] = q.evaluate("()=>__tb.musicDuck")
    q.close()
    return r['map_off'] == 0 and r['site_off'] == 0 and r['after_reopen'] == [False, 0] and r['map_on'] == 1, r

def sidebar_icons_spread(b):
    # owner 18 Nov: "make teh icons at the top of the sidebar spread out, now they are all clustered in teh middle": in a site,
    # the first icon at the sidebar's left edge and the last at its right edge
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    r = q.evaluate("()=>{const T=__tb, L=T.levelSidebar().buttons, x0=T.buildingWidthPx, w=window.innerWidth-x0; return {left_gap:L[0].x-L[0].size/2-x0, right_gap:x0+w-(L[L.length-1].x+L[L.length-1].size/2), n:L.length, size:L[0].size};}")
    q.close()
    return r['n'] > 1 and r['left_gap'] <= 12 and r['right_gap'] <= 12, r

# --------------------------------------------------------------------
# SECTION: CUES -- what is said and when, outside the tutorial
# --------------------------------------------------------------------
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

def home_line_repeat(b):
    # owner 18 Nov: "the press here to go mack to the map cue, plays too often, double its play interval": its wait after it ends
    q = page(b)
    w = q.evaluate("()=>{const c=__tb.CUE_TABLE.cues.find(x=>x.id==='first-win-home'); return c.repeat||5;}")
    q.close()
    return w == 10, dict(repeat_seconds=w)

def esc_leaves_site(b):
    # owner 18 Nov: "an esc in the lvel ... should exit immediatly", then "if an intro is playing the esc stops the intro": a site
    # entered, its intro (picture and line) playing: one ESC skips the intro and stays; the next ESC leaves for the map
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    click(q, 'site:mastaba')
    intro = until(q, "()=>__tb.mode==='build'&&!!__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 4)
    q.keyboard.press('Escape'); time.sleep(0.1)
    first = q.evaluate("()=>({mode:__tb.mode, intro:!!(__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro')})")
    q.keyboard.press('Escape'); time.sleep(0.1)
    second = q.evaluate("()=>__tb.mode")
    q.close()
    return intro and first['mode'] == 'build' and not first['intro'] and second == 'map', dict(intro_playing=intro, after_first_esc=first, after_second_esc=second)

def esc_during_demo(b):
    # owner 18 Nov: "when demo/tutorial is playing an esc should just exit" and "an esc stops the demo sound, but the demo keeps
    # playing ... if they are to stop, they stop together": the second site's demo running, one ESC: on the map, no demo, no
    # demo line; and a demo line cut short stops its demo
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.progress.done.mastaba={pieces:[],loads:[]}; __tb.cueMem().seq['first-site']='done';}")
    click(q, 'site:djoser'); time.sleep(0.3); quiet(q)  # its intro line skipped
    demo = until(q, "()=>!!__tb.demo&&!!__tb.voice.cur&&__tb.voice.cur.demo", 8)
    q.keyboard.press('Escape'); time.sleep(0.1)
    after = q.evaluate("()=>({mode:__tb.mode, demo:!!__tb.demo, line:!!(__tb.voice.cur&&__tb.voice.cur.demo), demoPieces:__tb.pieces.filter(p=>p.demo).length})")
    click(q, 'site:djoser'); time.sleep(0.3); quiet(q)
    again = until(q, "()=>!!__tb.demo&&!!__tb.voice.cur&&__tb.voice.cur.demo", 8)
    q.evaluate("()=>{if(__tb.voice.cur) __tb.cutLine(__tb.voice.cur)}")  # the demo's line cut short however it happens
    cut = q.evaluate("()=>({demo:!!__tb.demo, demoPieces:__tb.pieces.filter(p=>p.demo).length})")
    q.close()
    r = dict(demo_speaking=demo, after_esc=after, demo_again=again, after_line_cut=cut)
    return demo and after['mode'] == 'map' and not after['demo'] and not after['line'] and again and not cut['demo'] and not cut['demoPieces'], r

# --------------------------------------------------------------------
# SECTION: TUTORIAL -- the first site's steps
# --------------------------------------------------------------------
def tutorial_early_brick(b):
    # owner 18 Nov: "at some point, I managed to go out of the tuturial in the 1st lvl, the shovel, the undo, the "button is green
    # now" vue didnt fire, I took some brick before the test said it": the first site, teaching on; at every step the child first
    # takes a mudbrick into the building, then does what the step asks; every step's line must still come
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    record(q)
    click(q, 'site:mastaba')
    until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 2); time.sleep(0.5)
    q.keyboard.press('Escape'); time.sleep(0.05)
    W = q.evaluate("()=>__tb.buildingWidthPx")
    gy = q.evaluate("()=>__tb.worldToScreen(0,0).y")
    last = "()=>{const T=__tb, p=T.pieces.filter((x)=>!x.demo&&x.heldBy==null).pop(); if(!p) return null; const s=T.worldToScreen(p.body.getPosition().x,p.body.getPosition().y); return [s.x,s.y];}"
    n, seen, end = 0, [], time.time() + 95
    def brick():
        nonlocal n
        p = pile_piece(q, 'mudbrick')
        if p: drag(q, p, [W * (0.3 + 0.06 * (n % 6)), gy - 25 - 22 * (n // 6)], hold=0.4); n += 1
    while time.time() < end:
        st = q.evaluate("()=>__tb.cueMem().seq['first-site']")
        if st == 'done': break
        if not seen or seen[-1] != st:
            seen.append(st); q.evaluate("(s)=>__rec.said.push('step '+s)", st); brick()  # a brick taken before the step's line says what to do
        if st == 't-tap3':
            p = q.evaluate(last)
            if p:
                for _ in range(3): q.mouse.click(p[0], p[1]); time.sleep(0.12)
        elif st == 't-dragback':
            p = q.evaluate(last)
            if p: drag(q, p, [W + 60, gy - 120], hold=0.3)
        elif st == 't-shovel': click(q, 'broom')
        elif st == 't-red':  # the test button once the step has said to press it
            if 99 in q.evaluate("()=>__rec.said"): click(q, 'test')
            else: brick()
        elif st == 't-green':  # the building finished with the quick build; the button once the step has said it is green
            if 100 in q.evaluate("()=>__rec.said"): click(q, 'test')
            elif not q.evaluate("()=>__tb.testReady()"):
                q.keyboard.down('Control'); time.sleep(0.1); click(q, 'autobuild'); until(q, "()=>!__tb.auto", 20); q.keyboard.up('Control'); time.sleep(3.2)  # the child's press, not the parent's (WARNINGS: Ctrl latch)
        else: brick()
        time.sleep(0.6)
    r = dict(steps=seen, said=q.evaluate("()=>__rec.said"), step=q.evaluate("()=>__tb.cueMem().seq['first-site']"), pieces=n,
             cues=q.evaluate("()=>({cur:__tb.voice.cur&&__tb.voice.cur.n, queue:__tb.voice.queue.map((x)=>[x.n,x.cue&&x.cue.id,x.fin,x.done]), active:__tb.active.map((x)=>[x.n,x.cue&&x.cue.id,x.seq,x.ended,x.fin,x.done,x.waitEvent]), whens:__tb.whens.length})"))
    q.close()
    return r['step'] == 'done' and all(x in r['said'] for x in (95, 135, 100)), r

def tutorial_no_mudbrick_line(b):
    # owner 21 Nov: "the cue that appears when you touch a mudbrick for the first time ... should NOT be appearing there" (in the
    # first site's teaching): the child takes bricks between the steps, as in tutorial-early-brick; the mudbrick line is not said
    # while the teaching runs, and every step still comes
    ok, r = tutorial_early_brick(b)
    said = r['said'] if isinstance(r, dict) else []
    end = max([i for i, x in enumerate(said) if isinstance(x, str)] + [len(said)])
    return ok and 78 not in said[:end], dict(said=said, step=r.get('step') if isinstance(r, dict) else r)

def tutorial_test_while_step_waits(b, step, at):
    # owner 21 Nov: "at some point the tutorial of 1st level stopped, after [the mudbrick line] was heard ... no 'this is the red
    # button', no 'this is the shovel, the undo', no 'green can be pressed now'": the first site's teaching waits for enough
    # pieces; a line is playing when the child lays the piece that starts the next step (here the first wood: its line), the child
    # builds on and presses the green button before that step's line had its turn; the teaching must go on after the test.
    # The child lays bricks in rows; the at-th piece is the first wood, let go inside the dotted outline, so two lines (the wood's,
    # the dotted outline's) play while the parent's quick build (Ctrl) finishes the building and the green button is pressed
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("(s)=>{__tb.cueMem().seq['first-site']=s}", step)
    record(q)
    click(q, 'site:mastaba')
    until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 2); time.sleep(0.3)
    q.keyboard.press('Escape'); time.sleep(0.3); quiet(q)
    W = q.evaluate("()=>__tb.buildingWidthPx"); gy = q.evaluate("()=>__tb.worldToScreen(0,0).y")
    for n in range(at - 1):
        drag(q, pile_piece(q, 'mudbrick'), [W * (0.3 + 0.06 * (n % 6)), gy - 25 - 22 * (n // 6)], hold=0.4)
    top = q.evaluate("()=>{const T=__tb, w=T.worldToScreen(T.LEVEL_X0, 3.6); return [w.x, w.y];}")
    drag(q, pile_piece(q, 'wood'), top, hold=0.2)
    q.keyboard.down('Control'); time.sleep(0.1); click(q, 'autobuild'); until(q, "()=>!__tb.auto", 20); q.keyboard.up('Control')
    green = until(q, "()=>__tb.testReady()", 4)
    queued = q.evaluate("()=>__tb.voice.queue.map((x)=>x.cue&&x.cue.id)")
    if green: click(q, 'test')
    started = until(q, "()=>!!__tb.test", 2)
    ended = started and until(q, "()=>!__tb.test", 60)
    failed = not q.evaluate("()=>!!__tb.progress.done.mastaba"); in_test = q.evaluate("()=>__rec.said.slice()")
    end = time.time() + 100
    while time.time() < end and q.evaluate("()=>__tb.cueMem().seq['first-site']") != 'done':
        if q.evaluate("()=>__tb.cueMem().seq['first-site']==='t-undo'&&!__tb.voice.cur&&!__tb.test") and pile_piece(q, 'mudbrick'): drag(q, pile_piece(q, 'mudbrick'), [W * 0.5, gy - 200], hold=0.4)  # the child builds on until the undo step comes
        if q.evaluate("()=>__tb.cueMem().seq['first-site']==='t-red'") and 99 in q.evaluate("()=>__rec.said") and q.evaluate("()=>!__tb.test&&!__tb.voice.cur"): click(q, 'test')  # the red-button step, after its line
        if q.evaluate("()=>__tb.cueMem().seq['first-site']==='t-green'") and 100 in q.evaluate("()=>__rec.said") and q.evaluate("()=>__tb.testReady()&&!__tb.test"): click(q, 'test')
        time.sleep(0.5)
    r = dict(green=green, queued_at_green=queued, test_started=started, test_ended=ended, failed=failed, said_by_test_end=in_test, said=q.evaluate("()=>__rec.said"), step=q.evaluate("()=>__tb.cueMem().seq['first-site']"),
             now=q.evaluate("()=>({mode:__tb.mode, pieces:__tb.pieces.length, pile:__tb.pileBodies().map((x)=>x.pileItem.material[0]).join(''), cur:__tb.voice.cur&&__tb.voice.cur.n, queue:__tb.voice.queue.map((x)=>x.n), whens:__tb.whens.length, test:!!__tb.test, fail:!!__tb.failShow})"))
    q.close()
    test_lines = 71 in in_test and (not failed or 105 in in_test)  # the test's own lines still play: the green-button line, and at the first fail its explanation of the red
    return started and test_lines and r['step'] == 'done' and all(n in r['said'] for n in ((99, 135, 100) if step == 't-red' else (135, 100))), r

def tutorial_test_before_red_step(b): return tutorial_test_while_step_waits(b, 't-red', 8)

def tutorial_test_before_undo_step(b): return tutorial_test_while_step_waits(b, 't-undo', 10)

def tutorial_put_right_after_dragback(b):
    # owner 21 Nov: "when it says: you can also drag it, I then drag it, and immediately I take another one and put it in the
    # site, then the tutorial stops"; "the 'put a few more pieces' doesn't play or if it plays then it stops immediately, so there
    # are no instructions really": the line plays in full, and the shovel step comes once he has put a few pieces
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    click(q, 'site:mastaba')
    until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 2); time.sleep(0.3)
    q.keyboard.press('Escape'); time.sleep(0.3)
    W = q.evaluate("()=>__tb.buildingWidthPx"); gy = q.evaluate("()=>__tb.worldToScreen(0,0).y")
    q.evaluate("""()=>{window.__l=[]; let ln=null; const f=()=>{const c=__tb.voice.cur, n=c&&c.n; if(n!==ln){ if(ln!=null) __l[__l.length-1].end=performance.now(); if(n!=null) __l.push({n, t0:performance.now()}); ln=n; } requestAnimationFrame(f);}; requestAnimationFrame(f);}""")
    last = "()=>{const T=__tb, p=T.pieces.filter((x)=>!x.demo&&x.heldBy==null).pop(); if(!p) return null; const s=T.worldToScreen(p.body.getPosition().x,p.body.getPosition().y); return [s.x,s.y];}"
    end = time.time() + 40  # the tutorial from its start, each step done once its line has been said: a piece in, three taps, a piece in
    while time.time() < end and not q.evaluate("()=>__tb.voice.cur&&__tb.voice.cur.n===134"):
        st = q.evaluate("()=>{const c=__tb.voice.cur; return __tb.cueMem().seq['first-site']+'/'+(c?c.n:'')}")
        if st in ('t-drag-1/', 't-drag-2/'): drag(q, pile_piece_inside(q, 'mudbrick'), [W * 0.3, gy - 25], hold=0.4)
        elif st == 't-tap3/':
            p = q.evaluate(last)
            if p:
                for _ in range(3): q.mouse.click(p[0], p[1]); time.sleep(0.12)
        time.sleep(0.3)
    ok = until(q, "()=>__tb.voice.cur&&__tb.voice.cur.n===134", 1)  # "you can also drag it back"
    if ok:
        time.sleep(0.5); p = q.evaluate(last)
        if p: drag(q, p, [W + 60, gy - 120], hold=0.3)  # he drags it back
        drag(q, pile_piece_inside(q, 'mudbrick'), [W * 0.4, gy - 25], hold=0.4)  # and at once puts another one in the site
    heard = until(q, "()=>__l.some((x)=>x.n===138&&x.end)", 15)
    for k in range(1, 4):  # then he goes on putting pieces in, one at a time
        if q.evaluate("()=>__l.some((x)=>x.n===95)"): break
        drag(q, pile_piece_inside(q, 'mudbrick'), [W * (0.4 + 0.12 * k), gy - 25], hold=0.4); time.sleep(1)
    shovel = until(q, "()=>__l.some((x)=>x.n===95)", 10)
    r = q.evaluate("()=>({lines:__l.map((x)=>[x.n, x.end?+((x.end-x.t0)/1000).toFixed(1):null]), len138:__tb.VOICE_SECONDS[138], step:__tb.cueMem().seq['first-site']})")
    q.close()
    full = [d for n, d in r['lines'] if n == 138 and d is not None and d >= r['len138'] - 0.3]
    return ok and heard and bool(full) and shovel, r

def tutorial_piece_in_at_dragback(b, when):
    # owner 21 Nov: "AGAIN I MANAGED TO MAKE YOU SKIP THE TUTORIALS by dragging fast a piece to the site after the line that was
    # asking me to drag it back to the pile": the tutorial from its start, each step done once its line is said; at the drag-back
    # step he takes a new piece from the pile and puts it in the site fast (when: 'during' its line, 'after' it, 'before' it while
    # the line before it plays); every later step's line must still come, in full: drag back, put a few pieces, the shovel
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    click(q, 'site:mastaba')
    until(q, "()=>__tb.voice.cur&&__tb.voice.cur.cue&&__tb.voice.cur.cue.id==='site-intro'", 2); time.sleep(0.3)
    q.keyboard.press('Escape'); time.sleep(0.3)
    W = q.evaluate("()=>__tb.buildingWidthPx"); gy = q.evaluate("()=>__tb.worldToScreen(0,0).y")
    q.evaluate("""()=>{window.__l=[]; let ln=null; const f=()=>{const c=__tb.voice.cur, n=c&&c.n; if(n!==ln){ if(ln!=null) __l[__l.length-1].end=performance.now(); if(n!=null) __l.push({n, t0:performance.now()}); ln=n; } requestAnimationFrame(f);}; requestAnimationFrame(f);}""")
    last = "()=>{const T=__tb, p=T.pieces.filter((x)=>!x.demo&&x.heldBy==null).pop(); if(!p) return null; const s=T.worldToScreen(p.body.getPosition().x,p.body.getPosition().y); return [s.x,s.y];}"
    cur = "()=>{const c=__tb.voice.cur; return __tb.cueMem().seq['first-site']+'/'+(c?c.n:'')}"
    target = {'before': 't-tap3/132', 'during': 't-dragback/134', 'after': 't-dragback/'}[when]
    end, did = time.time() + 40, False
    while time.time() < end and not did:
        st = q.evaluate(cur)
        if st == target or (when == 'before' and st.endswith('/132')) or (when == 'after' and st.startswith('t-dragback/') and q.evaluate("()=>__l.some((x)=>x.n===134&&x.end)") and not q.evaluate("()=>!!__tb.voice.cur")):
            if when == 'during': time.sleep(0.4)
            drag(q, pile_piece_inside(q, 'mudbrick'), [W * 0.6, gy - 25], steps=8, hold=0.1); did = True; break  # fast, into the site
        if st in ('t-drag-1/', 't-drag-2/'): drag(q, pile_piece_inside(q, 'mudbrick'), [W * 0.3, gy - 25], hold=0.4)
        elif st == 't-tap3/':
            p = q.evaluate(last)
            if p:
                for _ in range(3): q.mouse.click(p[0], p[1]); time.sleep(0.12)
        time.sleep(0.1)
    end = time.time() + 45  # then he follows whatever the tutorial says next, once each line is said
    while time.time() < end and not q.evaluate("()=>__l.some((x)=>x.n===95)"):
        st = q.evaluate(cur)
        if st == 't-dragback/' and q.evaluate("()=>__l.filter((x)=>x.n===134&&x.end).length>0"):
            p = q.evaluate(last)
            if p: drag(q, p, [W + 60, gy - 120], hold=0.3)
        elif st.startswith('t-drag-3/') and q.evaluate("()=>__l.some((x)=>x.n===138&&x.end)"): drag(q, pile_piece_inside(q, 'mudbrick'), [W * (0.3 + 0.1 * (int(time.time() * 3) % 5)), gy - 25], hold=0.4)
        elif st in ('t-drag-1/', 't-drag-2/'): drag(q, pile_piece_inside(q, 'mudbrick'), [W * 0.3, gy - 25], hold=0.4)
        time.sleep(0.5)
    r = q.evaluate("()=>({lines:__l.map((x)=>[x.n, x.end?+((x.end-x.t0)/1000).toFixed(1):null]), len:{134:__tb.VOICE_SECONDS[134],138:__tb.VOICE_SECONDS[138]}, step:__tb.cueMem().seq['first-site'], pieces:__tb.pieces.filter((p)=>!p.demo).map((p)=>{const c=p.body.getPosition(); return [+(c.x-__tb.LEVEL_X0).toFixed(1), +c.y.toFixed(1), p.heldBy, !!p.ghost]})})")
    q.close()
    full = lambda n: any(m == n and d is not None and d >= r['len'][str(n)] - 0.3 for m, d in r['lines'])
    return did and full(134) and full(138) and any(m == 95 for m, _ in r['lines']), r

def tutorial_piece_in_before_dragback(b): return tutorial_piece_in_at_dragback(b, 'before')

def tutorial_piece_in_during_dragback(b): return tutorial_piece_in_at_dragback(b, 'during')

def tutorial_piece_in_after_dragback(b): return tutorial_piece_in_at_dragback(b, 'after')

# --------------------------------------------------------------------
# SECTION: THE TEST -- its lines, sounds and red
# --------------------------------------------------------------------
def test_end_sounds(b):
    # owner 17 Nov: "the success (and maybe the failure) audio in the lvls, after the test, are quite delayed": the time
    # from the earthquake's end to the cheer, and to the win line, at normal speed
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{const m=__tb.cueMem(); m.seq['first-site']='done'; m.ever=m.ever||{}; for (const id of ['explain-wind','explain-load','explain-quake']) m.ever[id]=1;}")  # the test's first-time explanations are not what is timed
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
        time.sleep(0.05)
    time.sleep(11)
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
    # owner 18 Nov: "change the test to that the withstood comes first, and the end-level cue follows 1 sec after" (this was: the site's line within 1.3 s of the cheer)
    w = next((k for k, e in enumerate(tl) if e.endswith(' line 104')), None)
    wst = float(tl[w].split()[0]) if w is not None else None
    wend = next((float(e.split()[0]) for e in tl[w + 1:] if ' line ' in e), None) if w is not None else None
    r.update(withstood_after_cheer=(wst - ch) if wst and ch else None, site_line_after_withstood=(wl - wend) if wl and wend else None)
    return bool(ch and quake_end and wl and wst and wend and ch - quake_end <= 0.7 and wst - ch <= 1.3 and 0.8 <= wl - wend <= 1.3), r

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

def test_lines_start_with_parts(b):
    # owner 18 Nov: "the first time the 3 test explanations run, the first one, the wind cue, is playing AFTER the wind has started.
    # the 'lets see, will it stand' cue, that plays when you press the green button, should play first, then the tests start,
    # and for each one of the 3 tests, its voice cue starts with it": the green button pressed, the first test with the teaching on
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.evaluate("""()=>{window.__ev=[]; const T=__tb, t0=performance.now(); let ph=null, ln=null;
      const f=()=>{const t=+((performance.now()-t0)/1000).toFixed(2), p=T.test?T.test.phase:null, l=T.voice.cur?T.voice.cur.n:null;
        if(p!==ph){__ev.push([t,'phase',p]); ph=p;} if(l!==ln){ if(ln!=null) __ev.push([t,'end',ln]); if(l!=null) __ev.push([t,'line',l]); ln=l;} requestAnimationFrame(f);}; requestAnimationFrame(f);}""")
    q.keyboard.down('Control'); time.sleep(0.1); click(q, 'autobuild'); until(q, "()=>!__tb.auto", 30); q.keyboard.up('Control')
    time.sleep(3.2)  # past the Ctrl latch: the green button pressed as the child does, the test at its normal speed
    until(q, "()=>__tb.testReady()", 10); click(q, 'test')
    until(q, "()=>!__tb.test||__tb.test.phase==='pass'||__tb.test.phase==='fail'", 40)
    ev = q.evaluate("()=>__ev")
    q.close()
    at = lambda kind, v: next((e[0] for e in ev if e[1] == kind and e[2] == v), None)
    r = dict(lets_see_ends=at('end', 71), wind=at('phase', 'wind'), wind_line=at('line', 101), load=at('phase', 'load'), load_line=at('line', 102), quake=at('phase', 'quake'), quake_line=at('line', 103))
    ok = r['lets_see_ends'] is not None and r['wind'] is not None and 0 <= r['wind'] - r['lets_see_ends'] <= 0.3  # the wind right after the line, no gap
    for part, line in (('wind', 'wind_line'), ('load', 'load_line'), ('quake', 'quake_line')):
        ok = ok and r[part] is not None and r[line] is not None and abs(r[line] - r[part]) <= 0.25
    if not ok: r['events'] = [e for e in ev if e[1] != 'phase' or e[2] in ('wind', 'load', 'quake', 'voice', 'settle', 'supports')][:30]
    return ok, r

def test_result_line_before_site_line(b):
    # owner 18 Nov: "the after tests cue playes after the in-level finish-level cue. no, first the sucess/failure end-tests cue,
    # then the end-level in-level cue": the first site passed for the first time, teaching on
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{const m=__tb.cueMem(); m.seq['first-site']='done'; m.ever=m.ever||{}; for (const id of ['explain-wind','explain-load','explain-quake']) m.ever[id]=1;}")  # the explanations are not what is checked
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.evaluate("()=>{window.__said=[]; const T=__tb; let ln=null; const f=()=>{const l=T.voice.cur?T.voice.cur.n:null; if(l!==ln){ if(l!=null) __said.push(l); ln=l;} requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    quick_build_and_test(q, hold=True)  # Ctrl held: the fast test
    until(q, "()=>__said.includes(14)&&__said.includes(104)&&__said.includes(106)", 25)
    said = q.evaluate("()=>__said")
    q.close()
    k = lambda n: said.index(n) if n in said else None
    return k(104) is not None and k(14) is not None and k(106) is not None and k(104) < k(14) < k(106), dict(lines_said=said)

def explanations_do_not_pause_test(b):
    # owner 18 Nov: "the 1st time test exmplanations (wind, headpiece, earthequake) freeze the screen with the overlay effect, and
    # pauses. I dont want that. they should play as the tests go": first test with the teaching on, never waiting for a line
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.evaluate("()=>{window.__ex={said:[],paused:0,dark:0}; const T=__tb; const f=()=>{const c=T.voice.cur; if(c&&[101,102,103].includes(c.n)&&!__ex.said.includes(c.n)) __ex.said.push(c.n); if(T.test&&T.test.phase==='cue') __ex.paused++; if(c&&c.attention==='freeze') __ex.dark++; requestAnimationFrame(f);}; requestAnimationFrame(f);}")
    quick_build_and_test(q, hold=False)
    until(q, "()=>!__tb.test||__tb.test.phase==='pass'||__tb.test.phase==='fail'", 40)
    ex = q.evaluate("()=>__ex")
    q.close()
    return len(ex['said']) >= 1 and ex['paused'] == 0 and ex['dark'] == 0, ex

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

def red_during_fail_lines(b):
    # owner 21 Nov: "no red was shown when the wind moved the pieces, just the 'to kokkino deixnei pou xalase' but no red was
    # shown": the first site, its teaching over, a build that fails the test (wooden blocks on top, voices on); while the
    # failure's line and the line saying the red shows where it broke are heard, the red is on the screen
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    q.evaluate("""()=>{const T=__tb; for(const e of [['block','mudbrick',-3,0.5],['block','mudbrick',-1,0.5],['block','mudbrick',1,0.5],['block','mudbrick',3,0.5],['square','mudbrick',-3.5,1.5],['block','mudbrick',-2,1.5],['block','mudbrick',0,1.5],['block','mudbrick',2,1.5],['square','mudbrick',3.5,1.5],['block','wood',-3,2.5],['block','wood',-1,2.5],['block','wood',1,2.5],['block','wood',3,2.5]]) T.spawnPiece(e[0],T.LEVEL_X0+e[2],e[3]+0.002,0,e[1]);}""")
    green = until(q, "()=>__tb.testReady()", 8)
    if green: click(q, 'test')
    seen, end = [], time.time() + 60
    while time.time() < end and (green and (q.evaluate("()=>!!__tb.test") or not seen)):
        st = q.evaluate("()=>{const c=__tb.voice.cur; return c&&c.cue&&c.cue.on&&(c.cue.on==='test-fail'||c.cue.on==='fail-explain')?[c.n, !!__tb.failShow, __tb.test&&__tb.test.phase]:null}")
        if st: seen.append(st)
        time.sleep(0.1)
    lines = sorted(set(x[0] for x in seen)); dark = [x for x in seen if not x[1]]
    r = dict(green=green, lines=lines, without_red=dark[:5], heard=len(seen))
    q.close()
    return green and 105 in lines and not dark, r

# --------------------------------------------------------------------
# SECTION: BUILDING, THE HAND AND THE PILE
# --------------------------------------------------------------------
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

def ishtar_planks(b):
    # owner 18 Nov: "give istar 4 wooden planks instead of 4 std blocks": the wood of its pile, as the game makes it
    q = page(b)
    wood = q.evaluate("""()=>{const L=__tb.LEVELS.find(l=>l.key==='ishtar'), c={}; let pulled=false;
      for(const [d,m] of L.solution){ if(d==='pull'){pulled=true; continue;} if(m==='wood'&&!pulled) c[d]=(c[d]||0)+1; }
      for(const [d,m,n] of L.extra||[]) if(m==='wood') c[d]=(c[d]||0)+n; return c;}""")
    q.close()
    return wood.get('beam') == 4 and not wood.get('block'), dict(wood_in_pile=wood)

def two_finger_turn(b):
    # owner 18 Nov: "2 fingers can be used to carry a block, cause this way a kid can rotate the blocks better": a plank lying
    # on the ground, one finger near each end, the fingers turned a quarter round about each other while lifting: the plank
    # turns with them; one finger let go, the other still carries it
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    st = q.evaluate("""()=>{const T=__tb, s0=T.worldToScreen(0,0).x, s1=T.worldToScreen(1,0).x, p=T.spawnPiece('beam',(350-s0)/(s1-s0),0.3,0,'wood'), hx=T.PIECE_DEFS.beam.hx, c=p.body.getPosition();
      const a=T.worldToScreen(c.x-0.7*hx,c.y), z=T.worldToScreen(c.x+0.7*hx,c.y), m=T.worldToScreen(c.x,c.y); return {a:[a.x,a.y],z:[z.x,z.y],m:[m.x,m.y]};}""")
    time.sleep(0.5)
    s = q.context.new_cdp_session(q)
    q.evaluate("()=>{window.__pev=[]; for(const t of ['pointerdown','pointerup','pointercancel','lostpointercapture']) window.addEventListener(t,(e)=>__pev.push(t+':'+e.pointerId+':'+e.pointerType+':'+Math.round(e.clientX)),true);}")
    def touch(kind, pts):
        s.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in pts]})
    import math
    (ax, ay), (zx, zy), (mx, my) = st['a'], st['z'], st['m']
    r = (zx - ax) / 2
    touch('touchStart', [(1, (ax, ay))]); time.sleep(0.03)
    touch('touchStart', [(1, (ax, ay)), (2, (zx, zy))])
    two = q.evaluate("()=>{const p=__tb.pieces[__tb.pieces.length-1]; return !!(p.heldBy!=null&&p.second&&p.second.grip);}")
    seen = q.evaluate("()=>{const p=__tb.pieces[__tb.pieces.length-1]; return {pointers:__tb.pointers.size, held:p.heldBy, second:!!p.second, n:__tb.pieces.length, def:p.defKey, mode:__tb.mode};}")
    for k in range(1, 41):  # about 0.7 s, a hand's rate; the middle rises 150 px while the fingers turn a quarter round
        th = math.pi / 2 * k / 40; cy = my - 150 * k / 40
        touch('touchMove', [(1, (mx - r * math.cos(th), cy + r * math.sin(th))), (2, (mx + r * math.cos(th), cy - r * math.sin(th)))])
        time.sleep(0.016)
    time.sleep(0.8)
    turned = q.evaluate("()=>__tb.pieces[__tb.pieces.length-1].body.getAngle()")
    touch('touchEnd', [(2, (mx, my - 150 - r))])
    time.sleep(0.05)
    still = q.evaluate("()=>{const p=__tb.pieces[__tb.pieces.length-1]; return p.heldBy!=null&&!p.second&&!!p.grip;}")
    touch('touchEnd', [])
    time.sleep(0.05)
    free = q.evaluate("()=>__tb.pieces[__tb.pieces.length-1].heldBy==null&&__tb.pointers.size===0")
    pev = q.evaluate('()=>__pev')
    q.close()
    r = dict(pev=pev, seen=seen, st=st, two_fingers_hold=two, turned_deg=round(math.degrees(turned)), one_finger_still_holds=still, let_go=free)
    return two and 70 <= abs(math.degrees(turned)) <= 110 and still and free, r

def two_fingers_on_pile_piece(b):
    # owner 18 Nov: "both the block and the block's outline came out of the sidebar": two fingers on one piece in the
    # sidebar, both dragged out into the building: one piece comes out, never two
    q = page(b)
    q.mouse.click(640, 400); quiet(q); untick_all(q)
    click(q, 'site:mastaba'); time.sleep(0.3); quiet(q)
    time.sleep(0.8)
    a = pile_piece(q, 'mudbrick')
    s = q.context.new_cdp_session(q)
    def touch(kind, pts):
        s.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in pts]})
    n0 = q.evaluate("()=>__tb.pieces.length")
    f1, f2 = (a[0] - 4, a[1]), (a[0] + 4, a[1])
    touch('touchStart', [(1, f1)]); time.sleep(0.03)
    touch('touchStart', [(1, f1), (2, f2)])
    held = q.evaluate("()=>__tb.pointers.size")
    for k in range(1, 31):  # both fingers out to the left, into the building, at a hand's rate
        dx = -500 * k / 30
        touch('touchMove', [(1, (f1[0] + dx, f1[1] - 100)), (2, (f2[0] + dx, f2[1] - 100))]); time.sleep(0.016)
    time.sleep(0.5)
    out = q.evaluate("()=>__tb.pieces.length") - n0
    touch('touchEnd', []); time.sleep(1.0)
    st = q.evaluate("()=>({pieces:__tb.pieces.length, ghosts:__tb.pieces.filter(p=>p.ghost).length, pointers:__tb.pointers.size})")
    q.close()
    r = dict(fingers_down=held, pieces_out=out, after=st)
    return out == 1 and st['ghosts'] == 0, r

def pile_piece_not_in_wall(b):
    # owner 21 Nov: "fix the piece stuck issue": a piece dragged from the building back into the pile, fast and low; no piece of
    # the pile stays stuck in the pile's walls (seen at the left wall after a fast drag back). Five tries at different heights.
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.cueMem().seq['first-site']='done'}")
    click(q, 'site:mastaba'); time.sleep(0.4); quiet(q)
    W = q.evaluate("()=>__tb.buildingWidthPx"); gy = q.evaluate("()=>__tb.worldToScreen(0,0).y")
    stuck = []
    for k, (dx, dy) in enumerate([(60, 120), (40, 90), (20, 140), (80, 60), (30, 110)]):
        drag(q, pile_piece_inside(q, 'mudbrick'), [W * 0.3, gy - 25], hold=0.4); time.sleep(0.5)
        pc = q.evaluate("()=>{const T=__tb,p=T.pieces.filter((x)=>!x.demo)[0]; if(!p) return null; const s=T.worldToScreen(p.body.getPosition().x,p.body.getPosition().y);return [s.x,s.y]}")
        if pc: drag(q, pc, [W + dx, gy - dy], steps=10, hold=0.2)
        time.sleep(2)
        out = q.evaluate("""()=>{const T=__tb,r=T.pileBinRect,Wm=r.w/T.pileScale; return T.pileBodies().map((b)=>{let lo=1e9,hi=-1e9; for(let f=b.getFixtureList();f;f=f.getNext()){const bb=f.getAABB(0); lo=Math.min(lo,bb.lowerBound.x); hi=Math.max(hi,bb.upperBound.x);} return [+lo.toFixed(2), +(hi-Wm).toFixed(2)];}).filter(([lo,hi])=>lo<-0.05||hi>0.05);}""")
        if out: stuck.append([k, out])
    until(q, "()=>Math.max(...__tb.pileBodies().map((b)=>b.getLinearVelocity().length()))<0.05", 5); still = q.evaluate("()=>Math.max(...__tb.pileBodies().map((b)=>b.getLinearVelocity().length()))"); moving = q.evaluate("()=>__tb.pileBodies().filter((b)=>b.getLinearVelocity().length()>0.05).map((b)=>{const p=b.getPosition(); return [+p.x.toFixed(2), +p.y.toFixed(2), +b.getLinearVelocity().x.toFixed(3), +b.getLinearVelocity().y.toFixed(3)]})")  # and the pile comes to rest
    q.close()
    return not stuck and still < 0.05, dict(stuck=stuck, pile_speed=still, moving=moving)

# --------------------------------------------------------------------
# SECTION: MAP -- water, stones, sand, boats
# --------------------------------------------------------------------
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

def sand_draw_sound(b):
    # owner 18 Nov: "give sand drawing an appropriate sound, again, same loudness as all terrain sounds"
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    p = map_point(q, "T.sandArea(mx,my)>=0&&[1,2,3,4,5,6].every((k)=>T.sandArea(mx+k*15/T.mapView().k,my)>=0)")
    q.evaluate("()=>{__tb.soundLog.length=0}")
    q.mouse.move(*p); q.mouse.down(); q.mouse.move(p[0] + 90, p[1], steps=6); time.sleep(0.1)
    heard = q.evaluate("()=>__tb.soundLog.includes('map-sand-draw')"); q.mouse.up(); q.close()
    return bool(p and heard), dict(sand_at=p, sand_sound=heard)

def sand_draw_quieter(b):
    # owner 18 Nov: "reduce sand drawing sound 20%" (it was 0.512)
    q = page(b)
    v = q.evaluate("()=>__tb.SOUNDS['map-sand-draw'][0][1]")
    q.close()
    return abs(v - 0.512 * 0.8) < 0.005, dict(volume=v)

def boat_thrown(b):
    # owner 18 Nov: "boats shouldm also be able to be thrown, like stones do, with the similar throwing logic, just not rolling":
    # a boat picked up and flicked: it lands well past where the finger let go, and lies still once landed
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.progress.done.mastaba={pieces:[],loads:[]}}"); until(q, "()=>__tb.boats.length>0", 2)  # a finished site: its boat
    sea = map_point(q, "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+260*Math.cos(k*0.785),my+60*Math.sin(k*0.785))==='water')")
    if not sea: q.close(); return False, 'no open sea'
    q.evaluate("(p)=>{const T=__tb, v=T.mapView(), b=T.boats[0]; b.held=b.back=b.drop=null; b.stuck=true; b.ox=b.oy=b.ovx=b.ovy=0; b.x=(p[0]-v.ox)/v.k; b.y=(p[1]-v.oy)/v.k;}", sea)
    quiet(q); q.evaluate("()=>{__tb.active.length=0}")  # nothing points or holds the screen
    st = q.evaluate("()=>{const T=__tb, b=T.boats[0], p=T.mapView().pt(b.x,b.y); return {i:0, x:p.x, y:p.y};}")
    x, y = st['x'], st['y']
    q.mouse.move(x, y); q.mouse.down()
    st['held'] = q.evaluate("()=>!!__tb.boats[0].held")
    for k in range(1, 13): q.mouse.move(x + 8 * k, y); time.sleep(0.016)
    time.sleep(0.25)  # lifted over its shadow
    q.evaluate("()=>{window.addEventListener('pointerup',()=>{const T=__tb,b=T.boats[0],p=T.mapView().pt(b.x,b.y); window.__let=[p.x,p.y];},{capture:true,once:true});}")  # set before the flick, so nothing runs between it and letting go
    for k in range(1, 7): q.mouse.move(x + 96 + 25 * k, y); time.sleep(0.016)
    q.mouse.up(); time.sleep(0.8)  # let go straight after the flick, as a hand does (where it was is read at the moment of letting go)
    let = q.evaluate("()=>window.__let")
    end = q.evaluate("(i)=>{const T=__tb,b=T.boats[i],p=T.mapView().pt(b.x,b.y); return [p.x,p.y,!!b.drop];}", st['i'])
    time.sleep(0.3)
    end2 = q.evaluate("(i)=>{const T=__tb,b=T.boats[i],p=T.mapView().pt(b.x,b.y); return [p.x,p.y];}", st['i'])
    q.close()
    flew = end[0] - let[0]
    r = dict(start=st, let_go_at=let, landed_at=end[:2], flew_px=round(flew), still_after=round(abs(end2[0] - end[0]), 1))
    return st['held'] and flew > 30 and not end[2], r

def boat_on_boat(b):
    # owner 18 Nov: "make so dropping a boat on another boat makes the same sound that the blocks do on wood-on-wood hit. sound
    # volume should be the same as the stone-on-boat sound": a boat carried over another boat at sea and let go there
    q = page(b)
    q.mouse.click(640, 400); quiet(q); later_launch(q)
    q.evaluate("()=>{__tb.progress.done.mastaba={pieces:[],loads:[]}; __tb.progress.done.ur={pieces:[],loads:[]}}"); until(q, "()=>__tb.boats.length>1", 2)
    sea = map_point(q, "T.groundAt(mx,my)==='water'&&!T.isLand(mx,my)&&[0,1,2,3,4,5,6,7].every((k)=>T.groundAt(mx+260*Math.cos(k*0.785),my+60*Math.sin(k*0.785))==='water')")
    if not sea: q.close(); return False, 'no open sea'
    q.evaluate("(p)=>{const T=__tb, v=T.mapView(); T.boats.slice(0,2).forEach((b,i)=>{b.held=b.back=b.drop=null; b.stuck=true; b.ox=b.oy=b.ovx=b.ovy=0; b.x=(p[0]-v.ox)/v.k+(i?0:-160/v.k); b.y=(p[1]-v.oy)/v.k;});}", sea)
    quiet(q); q.evaluate("()=>{__tb.active.length=0}")
    a = q.evaluate("()=>{const T=__tb, p=T.mapView().pt(T.boats[0].x,T.boats[0].y); return [p.x,p.y];}")
    t = q.evaluate("()=>{const T=__tb, v=T.mapView(), p=v.pt(T.boats[1].x,T.boats[1].y); return [p.x,p.y-T.BOAT_LIFT_H*v.k];}")  # held up, its shadow over the other boat: it falls straight down onto it
    q.mouse.move(*a); q.mouse.down()
    for k in range(1, 21): q.mouse.move(a[0] + (t[0] - a[0]) * k / 20, a[1] + (t[1] - a[1]) * k / 20); time.sleep(0.03)
    time.sleep(0.4); q.evaluate("()=>{__tb.soundLog.length=0}")
    q.mouse.up(); time.sleep(0.6)
    snd = q.evaluate("()=>__tb.soundLog.slice()")
    pos = q.evaluate("()=>__tb.boats.slice(0,2).map((b)=>[Math.round(b.x),Math.round(b.y),b.lift])")
    vol = q.evaluate("()=>[__tb.SOUNDS['map-boat-boat'], __tb.SOUNDS['map-stone-boat'], __tb.SOUNDS['hit-wood-wood']]")
    q.close()
    ok = 'map-boat-boat' in snd and vol[0] and vol[0][0][0] == vol[2][0][0] and vol[0][0][1] == vol[1][0][1]
    return bool(ok), dict(sounds=snd, boats=pos, same_file=vol[0][0][0] == vol[2][0][0], gains=[vol[0][0][1], vol[1][0][1]])

# --------------------------------------------------------------------
# SECTION: RUNNER -- the list of flows and running them
# --------------------------------------------------------------------
FLOWS = {'restart-load-screen': restart_load_screen, 'child-action-cuts-line': child_action_cuts_line, 'ticks-off-lines-play': ticks_off_lines_play, 'test-end-sounds': test_end_sounds, 'first-site-ticks-off': first_site_ticks_off, 'first-site-ticks-on': first_site_ticks_on, 'ticks-off-first-win': ticks_off_first_win, 'red-outside': red_outside, 'map-water': map_water, 'map-stones': map_stones, 'test-fail-sounds': test_fail_sounds, 'red-headpiece-place': red_headpiece_place, 'owner-first-site-build': owner_first_site_build, 'headpiece-in-hand': headpiece_in_hand, 'damaged-voice-once-per-session': damaged_voice_once_per_session, 'sand-draw-sound': sand_draw_sound, 'ishtar-planks': ishtar_planks, 'two-finger-turn': two_finger_turn, 'two-fingers-on-pile-piece': two_fingers_on_pile_piece, 'esc-leaves-site': esc_leaves_site, 'esc-during-demo': esc_during_demo, 'explanations-do-not-pause-test': explanations_do_not_pause_test, 'home-line-repeat': home_line_repeat, 'boat-thrown': boat_thrown, 'sand-draw-quieter': sand_draw_quieter, 'test-lines-start-with-parts': test_lines_start_with_parts, 'test-result-line-before-site-line': test_result_line_before_site_line, 'tutorial-early-brick': tutorial_early_brick, 'tutorial-no-mudbrick-line': tutorial_no_mudbrick_line, 'tutorial-test-before-red-step': tutorial_test_before_red_step, 'tutorial-test-before-undo-step': tutorial_test_before_undo_step, 'red-during-fail-lines': red_during_fail_lines, 'tutorial-put-right-after-dragback': tutorial_put_right_after_dragback, 'pile-piece-not-in-wall': pile_piece_not_in_wall, 'tutorial-piece-in-before-dragback': tutorial_piece_in_before_dragback, 'tutorial-piece-in-during-dragback': tutorial_piece_in_during_dragback, 'tutorial-piece-in-after-dragback': tutorial_piece_in_after_dragback, 'boat-on-boat': boat_on_boat, 'sidebar-icons-spread': sidebar_icons_spread, 'button-click-sound': button_click_sound, 'music-tick': music_tick}  # middle_grab_bump: waits for the owner's answer on the lever

def run(b, names):
    for n, f in FLOWS.items():
        if names and n not in names: continue
        t = time.time()
        try: ok, info = f(b)
        except Exception as e: ok, info = False, 'error ' + str(e)[:300]
        print(('PASS ' if ok else 'FAIL ') + n + ' (%.1f s) ' % (time.time() - t) + ('' if ok else str(info)[:900]))
