# Flow tests: what the owner does, in the running game: real page, real mouse taps and drags on what he sees.
# One browser and one page for the whole run: each flow starts a new game with a set table (fast: the PC's hand moves without waiting)
# and prints PASS or FAIL, [its flow name], what it checks, and what was seen. Waits are on the game's state, never on a fixed sleep.
# Colours are numbered 0-4 (0 the most common); a tile is [first half, second half]; the board is 20 x 13 squares, the start tiles [0, 1] at (4, 6) and (14, 6).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'coins'}, {'k': 'coins2'}, {'k': 'slot'}, {'k': 'steal'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib
from playwright.sync_api import sync_playwright
GAME = next((pathlib.Path(__file__).resolve().parent.parent).glob('*.html'))  # this copy's own built page (whatever its name then), so old and new code can be tested at once
COIN = {'k': 'coins'}
NOW = ['']  # the flow running, for the report lines
WAIT = 1500  # ms: the game answers in a few ms in fast mode, so a flow that waits longer has failed; short waits keep failing runs short

# SECTION: HELPERS -- the page, a set table, taps and drags on what is drawn, the game's state
def settle(q): q.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")  # the game has answered and drawn
def table(q, **opts): opts.setdefault('fast', True); q.evaluate("(o)=>__dg.restart(o)", opts); settle(q)
def st(q): return q.evaluate("()=>__dg.state()")
def tap(q, bid):
    q.wait_for_function("(id)=>__dg.btn(id)", arg=bid, timeout=WAIT)
    p = q.evaluate("(id)=>__dg.btn(id)", bid); q.mouse.click(p[0], p[1]); settle(q)
def waiting(q, kind, who=0):
    q.wait_for_function("([k,w])=>{const s=__dg.state();return s.wait&&s.wait.kind===k&&s.wait.who===w}", arg=[kind, who], timeout=WAIT)
def path(q, a, b, up=True):  # a finger drag: press, move in small steps, let go
    q.mouse.move(a[0], a[1]); q.mouse.down(); q.mouse.move(b[0], b[1], steps=12)
    if up: q.mouse.up(); settle(q)
def held(q): return q.evaluate("()=>__dg.held()")
def drag_to(q, sp):  # turn the tile where it lies by tapping it, then drag it to the spot {x, y, r}
    while st(q)['wait']['r'] != sp['r']: h = held(q); q.mouse.click(h[0], h[1]); settle(q)
    path(q, held(q), q.evaluate("(s)=>__dg.tileAt(s.x,s.y,s.r)", sp))
def best_spot(q): return max(st(q)['spots'], key=lambda p: p['m'])
def tile_count(q, who): return sum(1 for t in st(q)['tiles'] if t[5] == who)
def drawn(q, kind): return [d for d in q.evaluate("()=>__dg.drawn()") if d['k'] == kind]
def report(ok, name, seen): print('%-4s [%s] %-40s %s' % ('PASS' if ok else 'FAIL', NOW[0], name, seen))
def get_jar(q, contents, coins=0, slots=()):  # place a tile with one matching edge, then open the jar it earns
    table(q, bag=[[0, 4]] * 4, coins=[coins, 0], jarQueue=contents + [COIN] * 8, slotQueue=list(slots))
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
def kid_plays(q, until, steps=80):  # the kid takes the first tile that fits, places it where it earns most, opens his jars
    for _ in range(steps):
        s = st(q)
        if until(s): return s
        w = s['wait']
        if w and w['who'] == 0:
            if w['kind'] == 'pick': tap(q, 'draft-%d' % s['fits'].index(True))
            elif w['kind'] == 'place': drag_to(q, best_spot(q))
            elif w['kind'] == 'jar': tap(q, 'jar-0')
        else: settle(q)
    return st(q)

# SECTION: FLOWS -- one per owner rule
def f_start(q):  # the same start tile for both, the two most common colours, at the centres of the board's halves; nobody has the token; the kid picks first
    s = st(q); starts = sorted(t[:5] for t in s['tiles'])
    ok = starts == [[4, 6, 0, 0, 1], [14, 6, 0, 0, 1]] and len(s['draft']) == 4 and s['wait'] == {'kind': 'pick', 'who': 0, 'r': 0} and s['first'] is None
    report(ok, 'start: same start tiles, kid first, no token', '%s %d %s %s' % (starts, len(s['draft']), s['wait'], s['first']))

def f_colour_split(q):  # colours are scarce in a fixed ratio: 80 halves, about 24/22/20/18/16%
    s = st(q); report(s['halves'] == [19, 18, 16, 14, 13], 'colours: fixed scarce split', str(s['halves']))

def f_first_round_fits(q):  # in the first round every tile can be placed by each player
    bad = 0
    for seed in range(1, 21):
        table(q, seed=seed); bad += q.evaluate("()=>__dg.state().draft.length") - sum(st(q)['fits'])
    report(bad == 0, 'first round: every tile fits', 'tiles that fit nowhere: %d' % bad)

def f_tap_turns(q):  # tap the won tile where it lies (in the top row) to turn it
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h = held(q)
    q.mouse.click(h[0], h[1]); settle(q); r1 = st(q)['wait']['r']; q.mouse.click(h[0], h[1]); settle(q)
    report(r1 == 1 and st(q)['wait']['r'] == 2, 'tile: a tap turns it where it lies', 'turns %d then %d' % (r1, st(q)['wait']['r']))

def f_drag_place(q):  # drag the tile from the top row; it snaps in as one tile; no squares are drawn around the land, no tray
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
    ids = q.evaluate("()=>__dg.buttons()"); marks = [b for b in ids if b.startswith('spot') or b == 'tray']
    drag_to(q, {'x': 3, 'y': 6, 'r': 2}); mine = [t for t in st(q)['tiles'] if t[5] == 0 and t[:5] == [3, 6, 2, 0, 4]]
    report(not marks and len(mine) == 1, 'place: dragged tile snaps in', 'extra marks %s, placed %s' % (marks, mine))

def f_drag_leave(q):  # drag, leave it anywhere, turn it there, drag again: it is placed only when it snaps
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
    far = q.evaluate("()=>__dg.tileAt(9,1,0)"); path(q, held(q), far); h1 = held(q); left = h1 is not None and abs(h1[0] - far[0]) < 2 and abs(h1[1] - far[1]) < 2
    q.mouse.click(h1[0], h1[1]); settle(q); turned = st(q)['wait']['r'] == 1
    mid = q.evaluate("()=>__dg.tileAt(9,9,1)"); path(q, held(q), mid); still = st(q)['wait']['kind'] == 'place' and tile_count(q, 0) == 1
    drag_to(q, {'x': 3, 'y': 6, 'r': 2})
    report(left and turned and still and tile_count(q, 0) == 2, 'tile: left anywhere until it snaps', 'left %s turned %s still %s tiles %d' % (left, turned, still, tile_count(q, 0)))

def f_snap_preview(q):  # before it snaps the place is shown; far from any place nothing is shown
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place')
    goal = q.evaluate("()=>__dg.tileAt(4,5,0)"); path(q, held(q), [goal[0] + 8, goal[1] + 6], up=False); near = st(q)['snap']; ghost = len([d for d in drawn(q, 'tile') if d['look'] == 'ghost'])
    far = q.evaluate("()=>__dg.tileAt(9,0,0)"); q.mouse.move(far[0], far[1]); settle(q); away = st(q)['snap']; q.mouse.up(); settle(q)
    ok = near == {'x': 4, 'y': 5, 'r': 0} and ghost == 1 and away is None and st(q)['wait']['kind'] == 'place'
    report(ok, 'snap: place shown before it snaps', 'near %s ghost %d, away %s' % (near, ghost, away))

def f_own_land(q):  # a tile must have a matching edge with your own land; matching only the PC's land is not enough
    table(q, bag=[[2, 4], [0, 4], [0, 4], [0, 4]], tiles=[[9, 3, 0, 2, 2, 1]]); s = st(q)
    report(s['fits'][0] is False and q.evaluate("()=>!__dg.btn('draft-0')"), 'match: must be with your own land', 'fits %s' % s['fits'])

def f_jars_any_land(q):  # matching edges with any land earn jars: one with yours, one with the PC's
    table(q, bag=[[1, 2]] * 4, tiles=[[6, 4, 0, 2, 2, 1]], jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 5, 'y': 5, 'r': 3}); waiting(q, 'jar'); j = st(q)['players'][0]['jars']
    report(j == 2, 'jars: matching edges with any land', 'jars %d' % j)

def f_jar_per_edge(q):  # one jar per matching edge: one tile can earn several
    table(q, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0})
    waiting(q, 'jar'); j = st(q)['players'][0]['jars']; tap(q, 'jar-0'); tap(q, 'jar-0')
    report(j == 2 and st(q)['players'][0]['coins'] == 2, 'jars: one per matching edge', 'jars %d coins %d' % (j, st(q)['players'][0]['coins']))

def f_greyed(q):  # tiles you can't pick are greyed but keep their colour, and can't be tapped
    table(q, bag=[[0, 4], [2, 3], [0, 4], [0, 4]]); s = st(q); d = {x['id']: x for x in drawn(q, 'tile')}
    ok = s['fits'] == [True, False, True, True] and q.evaluate("()=>!__dg.btn('draft-1')") and d['draft-1']['look'] == 'grey' and d['draft-1']['cs'] == [2, 3] and d['draft-0']['look'] is None
    report(ok, 'greyed: unfit tile not tappable, colours kept', 'fits %s, drawn %s' % (s['fits'], d.get('draft-1')))

def f_pass_other_plays(q):  # nothing fits you: your turn passes, clearly, and the PC plays again; no tile is thrown
    table(q, bag=[[3, 4]] * 4 + [[0, 0]] * 4, tiles=[[14, 7, 0, 3, 3, 1]], jarQueue=[COIN] * 20)
    q.wait_for_function("()=>__dg.state().round===2", timeout=WAIT); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1].count([3, 4])
    report(s['passes'][0] >= 1 and pc == 4, 'pass: turn passes, PC plays again', 'kid passes %d, PC took %d' % (s['passes'][0], pc))

def f_end_rule(q):  # the game ends when no tile left can be placed by either player; no tile is thrown
    table(q, bag=[[2, 3]] * 4); q.wait_for_function("()=>__dg.state().over", timeout=WAIT); s = st(q)
    report(s['left'] == 4, 'end: nothing placeable, game over', 'tiles left %d' % s['left'])

def f_goods_at_start(q):  # each square makes 1 good of its colour at the start of the round, the start tile too
    table(q, bag=[[0, 4]] * 4, tiles=[[4, 7, 0, 2, 2, 0]]); g = st(q)['players'][0]['goods']
    report(g == [1, 1, 2, 0, 0], 'goods: 1 per square at round start', str(g))

def f_sets_of_five(q):  # a set is 5 goods, one of each; the PC bids when it pays; a tie goes to the picker; only the winner pays
    kid, pc = [[4, 4, 0, 2, 3, 0], [4, 2, 0, 4, 4, 0]], [[14, 4, 0, 2, 3, 1], [14, 2, 0, 4, 4, 1]]
    table(q, bag=[[0, 1], [0, 0], [0, 0], [0, 0]], tiles=kid + pc)
    tap(q, 'draft-0'); waiting(q, 'bid'); s = st(q); pc_bid = s['players'][1]['bid']
    tap(q, 'bid'); waiting(q, 'place'); s = st(q)
    ok = pc_bid == 1 and s['players'][0]['goods'] == [0, 0, 0, 0, 1] and s['players'][1]['goods'] == [1, 1, 1, 1, 2]
    report(ok, 'bid: sets of 5, tie to picker, winner pays', 'pc bid %d, kid %s, pc %s' % (pc_bid, s['players'][0]['goods'], s['players'][1]['goods']))

def f_leftovers_jar(q):  # at the end of the round each 3 of the same leftover good make a jar; the rest are lost
    table(q, bag=[[0, 0]] * 4, tiles=[[4, 2, 0, 2, 2, 0], [4, 3, 0, 2, 2, 0], [6, 3, 0, 2, 2, 0]], jarQueue=[COIN] * 20)
    kid_plays(q, lambda s: s['phase'] == 'end'); waiting(q, 'jar'); p = st(q)['players'][0]
    report(p['jars'] == 2 and p['goods'] == [0, 0, 0, 0, 0], 'end: each 3 same leftovers a jar', 'jars %d goods %s' % (p['jars'], p['goods']))

def f_pc_best(q):  # the PC picks and places for the most jars
    table(q, bag=[[0, 0], [0, 1], [0, 4], [0, 4]], first=1, jarQueue=[COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] != [14, 6]]
    report(pc == [[0, 1]] and s['players'][1]['coins'] == 2, 'pc: best tile, best place', 'pc tiles %s coins %d' % (pc, s['players'][1]['coins']))

def f_pc_hand(q):  # the PC's moves are slow and done by a moving hand: it points to tap, pinches to drag (a fake clock runs the real timings at once)
    q.clock.pause_at(q.evaluate("()=>Date.now()") + 1000)
    q.evaluate("()=>__dg.restart({fast:false,bag:[[0,1],[0,0],[0,4],[0,4]],first:1,jarQueue:Array(8).fill({k:'coins'})})")
    ms, xs, gs, dragged = 0, set(), set(), False
    while ms < 20000:
        q.clock.run_for(50); ms += 50; s = st(q)
        xs.add(round(s['hand']['x'])); gs.add(s['hand']['g']); dragged = dragged or s['handDrag']
        if any(t[5] == 1 and t[:2] != [14, 6] for t in s['tiles']): break
    q.clock.resume()
    report(ms >= 2500 and len(xs) > 10 and dragged and {'point', 'pinch'} <= gs, 'pc: slow, by a moving hand', '%d ms, hand at %d places, gestures %s' % (ms, len(xs), sorted(gs)))

def f_pc_slot(q):  # the PC takes the best expected result on the slot machine too
    table(q, bag=[[0, 4]] * 4, first=1, coins=[0, 5], jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[5, 5, 1])
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT); c = st(q)['players'][1]['coins']
    report(c == 7, 'pc: slot machine played for the most', 'pc coins %d' % c)

def f_jar_mix(q):  # half the jars hold 1 coin (a coins jar always holds 1); 2 coins is one of the bonuses
    m = q.evaluate("()=>__dg.sampleJars(4000)")
    ok = set(m) == {'coins', 'coins2', 'slot', 'steal', 'first', 'tile', 'jar', 'set'} and 0.45 < m['coins'] / 4000 < 0.55
    report(ok, 'jars: 1 coin half the time', str(m))

def f_coins2(q):  # the 2 coins bonus
    get_jar(q, [{'k': 'coins2'}]); c = st(q)['players'][0]['coins']
    report(c == 2, 'jar: 2 coins', 'coins %d' % c)

def f_slot_three(q):  # slot machine: pay 1 coin to reroll chosen wheels; 3 the same wins 3
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot')
    tap(q, 'wheel-2'); tap(q, 'reroll'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT); p = st(q)['players'][0]
    report(p['goods'][0] == 4 and p['coins'] == 2, 'slot: reroll costs a coin, 3 same win 3', 'goods %s coins %d' % (p['goods'], p['coins']))

def f_slot_two(q):  # 2 the same win 2; you can stop at any time
    get_jar(q, [{'k': 'slot'}], coins=0, slots=[5, 1, 5]); waiting(q, 'slot')
    tap(q, 'collect'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT); p = st(q)['players'][0]
    report(p['coins'] == 2, 'slot: stop with 2 the same wins 2', 'coins %d' % p['coins'])

def f_steal(q):  # steal a PC tile: it is lifted where it lay and you place it; a tile with no place for you can't be stolen
    table(q, bag=[[0, 4]] * 4, tiles=[[14, 7, 0, 0, 0, 1], [14, 2, 0, 3, 3, 1]], jarQueue=[{'k': 'steal'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')
    blocked = q.evaluate("()=>!__dg.btn('steal-t2')"); spot = q.evaluate("()=>__dg.tileAt(14,7,0)"); tap(q, 'steal-t1'); waiting(q, 'place')
    h = held(q); lifted = abs(h[0] - spot[0]) < 2 and abs(h[1] - spot[1]) < 2
    drag_to(q, best_spot(q)); s = st(q); mine = [t[3:5] for t in s['tiles'] if t[5] == 0]; theirs = [t[3:5] for t in s['tiles'] if t[5] == 1]
    report(blocked and lifted and [0, 0] in mine and [0, 0] not in theirs, 'steal: tile moves to you, unfit one blocked', 'blocked %s, lifted there %s, mine %s' % (blocked, lifted, mine))

def f_first_token(q):  # the first-player token comes from a jar
    get_jar(q, [{'k': 'first'}]); report(st(q)['first'] == 0, 'first: token comes to you', 'first %s' % st(q)['first'])

def f_free_tile(q):  # a free extra tile from nowhere, always one that fits, placed at once
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'place'); n0 = tile_count(q, 0); ok = len(st(q)['spots']) > 0; drag_to(q, best_spot(q))
    report(ok and tile_count(q, 0) == n0 + 1, 'tile: free tile fits and is placed', 'tiles %d -> %d' % (n0, tile_count(q, 0)))

def f_another_jar(q):  # another jar, which you open yourself
    get_jar(q, [{'k': 'jar'}, {'k': 'coins2'}]); waiting(q, 'jar'); c0 = st(q)['players'][0]['coins']
    tap(q, 'jar-0'); c1 = st(q)['players'][0]['coins']
    report(c1 == c0 + 2, 'jar: another jar to open', 'coins %d -> %d' % (c0, c1))

def f_free_set(q):  # a free set: one of each of the 5 goods
    get_jar(q, [{'k': 'set'}]); g = st(q)['players'][0]['goods']
    report(g == [2, 2, 1, 1, 1], 'set: one of each good', str(g))

def f_borders(q):  # each player's land has a border all around: green for the kid, red for the PC; a tile is one rectangle, no gap between its halves
    table(q, bag=[[0, 4]] * 4); b = drawn(q, 'border'); kid = sum(1 for x in b if x['o'] == 0); pc = sum(1 for x in b if x['o'] == 1)
    seam = q.evaluate("()=>__dg.edge(4,6,0)"); mid = q.evaluate("(p)=>__dg.pixel(p[0]-1,p[1])", seam)
    ok = kid == 6 and pc == 6 and mid == [232, 197, 71, 255]
    report(ok, 'borders: all around each land, one rectangle', 'kid edges %d, pc edges %d, seam %s' % (kid, pc, mid))

def f_game_end(q):  # the game ends when the tiles run out; most points wins
    table(q, bag=[[0, 0]] * 4, coins=[20, 2], jarQueue=[COIN] * 20)
    s = kid_plays(q, lambda s: s['over'])
    report(s['over'] and s['winner'] == 0, 'end: tiles run out, most coins wins', 'winner %s coins %s' % (s['winner'], [p['coins'] for p in s['players']]))

def f_random_play(q):  # many seeded games with random moves at random moments: every game ends, every placement keeps the rules
    bad = q.evaluate("""async () => {
      const ch = new MessageChannel(), tick = () => new Promise(r => { ch.port1.onmessage = () => r(); ch.port2.postMessage(0); }), errs = [];  // a message, not a timer: timers wait 4 ms each
      for (let seed = 1; seed <= 12; seed++) {
        let rs = seed * 7919; const rand = n => { rs = (rs * 16807) % 2147483647; return rs % n; };
        __dg.restart({ seed, fast: true });
        for (let step = 0; ; step++) {
          for (let k = rand(3); k >= 0; k--) await tick();
          const s = __dg.state(), w = __dg.wait();
          if (s.over) break;
          if (step > 3000) { errs.push('seed ' + seed + ' stuck at ' + JSON.stringify(s.wait)); break; }
          const cells = new Set(); for (const t of s.tiles) for (const [a, b] of [[t[0], t[1]], [t[0] + [1, 0, -1, 0][t[2]], t[1] + [0, 1, 0, -1][t[2]]]]) {
            if (a < 0 || b < 0 || a >= 20 || b >= 13 || cells.has(a + ',' + b)) errs.push('seed ' + seed + ' bad square ' + a + ',' + b); cells.add(a + ',' + b); }
          if (s.players.some(p => p.coins < 0 || p.goods.some(g => g < 0))) errs.push('seed ' + seed + ' below zero');
          if (!w || !w.human) continue;
          if (w.kind === 'pick') { const ok = s.fits.map((f, i) => f ? i : -1).filter(i => i >= 0); if (!ok.length) errs.push('seed ' + seed + ' pick with nothing to pick'); else __dg.answer(ok[rand(ok.length)]); }
          else if (w.kind === 'bid') __dg.answer(rand(2) === 0);
          else if (w.kind === 'place') { if (!w.spots.length) { errs.push('seed ' + seed + ' a tile with no place'); break; } __dg.answer(w.spots[rand(w.spots.length)]); }
          else if (w.kind === 'jar') __dg.answer();
          else if (w.kind === 'steal') __dg.answer(w.ids[rand(w.ids.length)]);
          else if (w.kind === 'slot') __dg.answer('collect');
        }
        if (errs.length > 5) break;
      }
      return errs.slice(0, 5);
    }""")
    report(not bad, 'random play: games end, rules hold', '%s' % (bad or '12 games'))

# SECTION: RUN -- one browser, one page (with a fake clock that runs normally until a flow pauses it), every flow on a new game
FLOWS = {n[2:]: f for n, f in list(globals().items()) if n.startswith('f_')}
def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True); q = ctx.new_page()
        q.clock.install(); q.goto(GAME.as_uri() + '?fast=1')
        try: q.wait_for_function("()=>window.__dg&&__dg.ready", timeout=5000)
        except Exception as e: pass
        for n in (names or FLOWS):
            NOW[0] = n
            try: q.mouse.up(); table(q); FLOWS[n](q)
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0][:120])
        b.close()
