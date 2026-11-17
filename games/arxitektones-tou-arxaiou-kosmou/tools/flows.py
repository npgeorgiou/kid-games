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

def drag(q, a, b, steps=20):  # a real mouse drag, at about the rate a hand moves
    q.mouse.move(a[0], a[1]); q.mouse.down(); time.sleep(0.05)
    for k in range(1, steps + 1): q.mouse.move(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps); time.sleep(0.015)
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
    q.keyboard.down('Control'); time.sleep(0.1); click(q, 'autobuild'); until(q, "()=>!__tb.auto", 30); q.keyboard.up('Control')
    until(q, "()=>__tb.testReady()", 10); time.sleep(3.3)  # Ctrl let go more than its 3 s latch before: the test at normal speed
    q.evaluate("""()=>{const T=__tb; window.__tl=[]; let ph=null, n=T.soundLog.length, ln=null; const t0=performance.now();
      const f=()=>{const t=((performance.now()-t0)/1000).toFixed(2); const p=T.test?T.test.phase:'none'; if(p!==ph){__tl.push(t+' phase '+p); ph=p;}
        if(T.soundLog.length){for(const x of T.soundLog) if(!x.startsWith('music')) __tl.push(t+' sound '+x); T.soundLog.length=0;} const l=T.voice.cur&&T.voice.cur.n; if(l!==ln){__tl.push(t+' line '+l); ln=l;}
        if(performance.now()-t0<70000) requestAnimationFrame(f);}; requestAnimationFrame(f);}""")
    click(q, 'test')
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

FLOWS = {'restart-load-screen': restart_load_screen, 'child-action-cuts-line': child_action_cuts_line, 'ticks-off-lines-play': ticks_off_lines_play, 'test-end-sounds': test_end_sounds, 'first-site-ticks-off': first_site_ticks_off, 'first-site-ticks-on': first_site_ticks_on}

def run(b, names):
    for n, f in FLOWS.items():
        if names and n not in names: continue
        t = time.time()
        try: ok, info = f(b)
        except Exception as e: ok, info = False, 'error ' + str(e)[:300]
        print(('PASS ' if ok else 'FAIL ') + n + ' (%.1f s) ' % (time.time() - t) + ('' if ok else str(info)[:900]))
