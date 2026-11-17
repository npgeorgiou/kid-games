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

FLOWS = {'first-site-ticks-off': first_site_ticks_off, 'first-site-ticks-on': first_site_ticks_on}

def run(b, names):
    for n, f in FLOWS.items():
        if names and n not in names: continue
        t = time.time()
        try: ok, info = f(b)
        except Exception as e: ok, info = False, 'error ' + str(e)[:300]
        print(('PASS ' if ok else 'FAIL ') + n + ' (%.1f s) ' % (time.time() - t) + ('' if ok else str(info)[:900]))
