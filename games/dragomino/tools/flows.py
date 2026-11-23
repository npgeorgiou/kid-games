# Flow tests: what the owner does, in the running game: real page, real mouse taps and drags on what he sees.
# Each flow starts a game with a set table (?fast: the PC's hand moves without waiting) and prints PASS or FAIL, its name, and what was seen.
# Colours are numbered 0-4 (0 the most common); a tile is [first half, second half]; the board is 20 x 13 squares, the start tiles [0, 1] at (4, 6) and (14, 6).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'coins'}, {'k': 'coins2'}, {'k': 'slot'}, {'k': 'steal'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib
from playwright.sync_api import sync_playwright
GAME = pathlib.Path(__file__).resolve().parent.parent / 'dragomino.html'  # this copy's own build, so old and new code can be tested at once
COIN = {'k': 'coins'}

# SECTION: HELPERS -- the page, a set table, taps and drags on what is drawn, the game's state
def page(b, fast=True):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True)
    q = ctx.new_page(); q.goto(GAME.as_uri() + ('?fast=1' if fast else '')); q.wait_for_function("()=>window.__dg&&__dg.ready", timeout=5000); return q

def table(q, **opts): q.evaluate("(o)=>__dg.restart(o)", opts); time.sleep(0.15)
def st(q): return q.evaluate("()=>__dg.state()")
def tap(q, bid):
    q.wait_for_function("(id)=>__dg.btn(id)", arg=bid, timeout=3000)
    p = q.evaluate("(id)=>__dg.btn(id)", bid); q.mouse.click(p[0], p[1]); time.sleep(0.15)
def waiting(q, kind, who=0):
    q.wait_for_function("([k,w])=>{const s=__dg.state();return s.wait&&s.wait.kind===k&&s.wait.who===w}", arg=[kind, who], timeout=3000)
def path(q, a, b, up=True):  # a finger drag at a real rate
    q.mouse.move(a[0], a[1]); q.mouse.down()
    for k in range(1, 13): q.mouse.move(a[0] + (b[0] - a[0]) * k / 12, a[1] + (b[1] - a[1]) * k / 12); time.sleep(0.02)
    if up: q.mouse.up(); time.sleep(0.15)
def drag_to(q, sp):  # turn the tile in the tray by tapping it, then drag it to the spot {x, y, r}
    while st(q)['wait']['r'] != sp['r']: tap(q, 'tray')
    path(q, q.evaluate("()=>__dg.btn('tray')"), q.evaluate("(s)=>__dg.tileAt(s.x,s.y,s.r)", sp))
def best_spot(q): return max(st(q)['spots'], key=lambda p: p['m'])
def tile_count(q, who): return sum(1 for t in st(q)['tiles'] if t[5] == who)
def report(ok, name, seen): print('%-4s %-40s %s' % ('PASS' if ok else 'FAIL', name, seen))
def get_jar(q, contents, coins=0):  # place a tile with one matching edge, then open the jar it earns
    table(q, bag=[[0, 4]] * 4, coins=[coins, 0], jarQueue=contents + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
def pixel(q, p): return q.evaluate("(p)=>__dg.pixel(p[0],p[1])", p)

# SECTION: FLOWS -- one per owner rule
def f_start(q):  # the same start tile for both, the two most common colours, at the centres of the board's halves; nobody has the token; the kid picks first
    s = st(q); starts = sorted(t[:5] for t in s['tiles'])
    ok = starts == [[4, 6, 0, 0, 1], [14, 6, 0, 0, 1]] and len(s['draft']) == 4 and s['wait'] == {'kind': 'pick', 'who': 0, 'r': 0} and s['first'] is None
    report(ok, 'start: same start tiles, kid first, no token', '%s %d %s %s' % (starts, len(s['draft']), s['wait'], s['first']))

def f_colour_split(q):  # colours are scarce in a fixed ratio: 80 halves, about 24/22/20/18/16%
    s = st(q); report(s['halves'] == [19, 18, 16, 14, 13], 'colours: fixed scarce split', str(s['halves']))

def f_first_round_fits(q):  # in the first round every tile can be placed
    bad = 0
    for seed in range(1, 21):
        table(q, seed=seed); bad += st(q)['fits'].count(False)
    report(bad == 0, 'first round: every tile fits', 'tiles that fit nowhere: %d' % bad)

def f_tap_turns(q):  # tap the tile in the tray to turn it
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); tap(q, 'tray'); r1 = st(q)['wait']['r']; tap(q, 'tray')
    report(r1 == 1 and st(q)['wait']['r'] == 2, 'tray: a tap turns the tile', 'turns %d then %d' % (r1, st(q)['wait']['r']))

def f_drag_place(q):  # drag the tile; it snaps in as one tile; no squares are drawn around the land
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
    marks = q.evaluate("()=>__dg.buttons().filter(b=>b.startsWith('spot')).length")
    drag_to(q, {'x': 3, 'y': 6, 'r': 2}); mine = [t for t in st(q)['tiles'] if t[5] == 0 and t[:5] == [3, 6, 2, 0, 4]]
    report(marks == 0 and len(mine) == 1, 'place: dragged tile snaps in', 'squares %d, placed %s' % (marks, mine))

def f_snap_preview(q):  # before it snaps the place is shown; dropped where it fits nowhere it goes back to the tray
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place')
    tray = q.evaluate("()=>__dg.btn('tray')"); goal = q.evaluate("()=>__dg.tileAt(4,5,0)")
    path(q, tray, [goal[0] + 8, goal[1] + 6], up=False); near = st(q)['snap']
    far = q.evaluate("()=>__dg.tileAt(9,0,0)"); q.mouse.move(far[0], far[1]); time.sleep(0.1); away = st(q)['snap']; q.mouse.up(); time.sleep(0.15)
    s = st(q); ok = near == {'x': 4, 'y': 5, 'r': 0} and away is None and s['wait']['kind'] == 'place' and tile_count(q, 0) == 1
    report(ok, 'snap: place shown, no fit goes back', 'near %s, away %s, wait %s' % (near, away, s['wait']))

def f_needs_match(q):  # a tile with no matching edge can't be placed, can't be picked, and is greyed; nobody can play: turns pass, no tile is thrown
    table(q, bag=[[2, 3]] * 4); q.wait_for_function("()=>__dg.state().over", timeout=5000); s = st(q)
    ok = s['passes'] == [1, 1] and s['left'] == 4 and tile_count(q, 0) == 1
    report(ok, 'match needed: no fit, turns pass', 'passes %s, tiles left %d' % (s['passes'], s['left']))

def f_greyed(q):  # tiles you can't pick are greyed but keep their colour, and can't be tapped
    table(q, bag=[[0, 4], [2, 3], [0, 4], [0, 4]]); s = st(q)
    ok = s['fits'] == [True, False, True, True] and q.evaluate("()=>!__dg.btn('draft-1')") and q.evaluate("()=>!!__dg.btn('draft-0')")
    c = pixel(q, q.evaluate("()=>__dg.draftHalf(1,0)")); grey_purple = c[2] > c[1] + 15  # colour 2 is purple: still purple, greyed
    report(ok and grey_purple, 'greyed: unfit tile not tappable, colour kept', 'fits %s, pixel %s' % (s['fits'], c))

def f_match_other_land(q):  # a matching edge with the PC's land is enough; it earns a jar too
    table(q, bag=[[4, 2]] * 4, tiles=[[9, 3, 0, 2, 2, 1]], jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 7, 'y': 3, 'r': 0}); waiting(q, 'jar'); tap(q, 'jar-0'); s = st(q)
    report(tile_count(q, 0) == 2 and s['players'][0]['coins'] == 1, 'match: PC land counts', 'kid tiles %d coins %d' % (tile_count(q, 0), s['players'][0]['coins']))

def f_jar_per_edge(q):  # one jar per matching edge: one tile can earn several
    table(q, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0})
    waiting(q, 'jar'); j = st(q)['players'][0]['jars']; tap(q, 'jar-0'); tap(q, 'jar-0')
    report(j == 2 and st(q)['players'][0]['coins'] == 2, 'jars: one per matching edge', 'jars %d coins %d' % (j, st(q)['players'][0]['coins']))

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
    for _ in range(40):
        s = st(q)
        if s['phase'] == 'end': break
        w = s['wait']
        if w and w['who'] == 0:
            if w['kind'] == 'pick': tap(q, 'draft-%d' % s['fits'].index(True))
            elif w['kind'] == 'place': drag_to(q, best_spot(q))
            elif w['kind'] == 'jar': tap(q, 'jar-0')
        time.sleep(0.05)
    waiting(q, 'jar'); p = st(q)['players'][0]
    report(p['jars'] == 2 and p['goods'] == [0, 0, 0, 0, 0], 'end: each 3 same leftovers a jar', 'jars %d goods %s' % (p['jars'], p['goods']))

def f_pc_best(q):  # the PC picks and places for the most jars
    table(q, bag=[[0, 0], [0, 1], [0, 4], [0, 4]], first=1, jarQueue=[COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=5000); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] != [14, 6]]
    report(pc == [[0, 1]] and s['players'][1]['coins'] == 2, 'pc: best tile, best place', 'pc tiles %s coins %d' % (pc, s['players'][1]['coins']))

def f_pc_hand(q):  # the PC's moves are slow and done by a moving hand, as if a person did them
    q2 = page(q.context.browser, fast=False)
    q2.evaluate("()=>__dg.restart({bag:[[0,1],[0,0],[0,4],[0,4]],first:1,jarQueue:Array(8).fill({k:'coins'})})")
    t0 = time.time(); xs = set(); dragged = False
    while time.time() - t0 < 20:
        s = st(q2); xs.add(round(s['hand']['x'])); dragged = dragged or s['handDrag']
        if any(t[5] == 1 and t[:2] != [14, 6] for t in s['tiles']): break
        time.sleep(0.05)
    dt = time.time() - t0; q2.context.close()
    report(dt >= 2.5 and len(xs) > 10 and dragged, 'pc: slow, by a moving hand', '%.1fs, hand at %d places, dragged %s' % (dt, len(xs), dragged))

def f_pc_slot(q):  # the PC takes the best expected result on the slot machine too
    q.evaluate("()=>__dg.slotQueue([5,5,1])")  # before the table: the PC moves at once in tests
    table(q, bag=[[0, 4]] * 4, first=1, coins=[0, 5], jarQueue=[{'k': 'slot'}] + [COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=5000); c = st(q)['players'][1]['coins']
    report(c == 7, 'pc: slot machine played for the most', 'pc coins %d' % c)

def f_jar_mix(q):  # half the jars hold 1 coin (a coins jar always holds 1); 2 coins is one of the bonuses
    m = q.evaluate("()=>__dg.sampleJars(4000)")
    ok = set(m) == {'coins', 'coins2', 'slot', 'steal', 'first', 'tile', 'jar', 'set'} and 0.45 < m['coins'] / 4000 < 0.55
    report(ok, 'jars: 1 coin half the time', str(m))

def f_coins2(q):  # the 2 coins bonus
    get_jar(q, [{'k': 'coins2'}]); c = st(q)['players'][0]['coins']
    report(c == 2, 'jar: 2 coins', 'coins %d' % c)

def f_slot_three(q):  # slot machine: pay 1 coin to reroll chosen wheels; 3 the same wins 3
    q.evaluate("()=>__dg.slotQueue([0,0,1,0])"); get_jar(q, [{'k': 'slot'}], coins=3); waiting(q, 'slot')
    tap(q, 'wheel-2'); tap(q, 'reroll'); q.wait_for_function("()=>!__dg.state().slot", timeout=3000); p = st(q)['players'][0]
    report(p['goods'][0] == 4 and p['coins'] == 2, 'slot: reroll costs a coin, 3 same win 3', 'goods %s coins %d' % (p['goods'], p['coins']))

def f_slot_two(q):  # 2 the same win 2; you can stop at any time
    q.evaluate("()=>__dg.slotQueue([5,1,5])"); get_jar(q, [{'k': 'slot'}], coins=0); waiting(q, 'slot')
    tap(q, 'collect'); q.wait_for_function("()=>!__dg.state().slot", timeout=3000); p = st(q)['players'][0]
    report(p['coins'] == 2, 'slot: stop with 2 the same wins 2', 'coins %d' % p['coins'])

def f_steal(q):  # steal a PC tile and place it in your land; a tile with no place for you can't be stolen
    table(q, bag=[[0, 4]] * 4, tiles=[[14, 7, 0, 0, 0, 1], [14, 2, 0, 3, 3, 1]], jarQueue=[{'k': 'steal'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')
    blocked = q.evaluate("()=>!__dg.btn('steal-t2')"); tap(q, 'steal-t1'); waiting(q, 'place'); drag_to(q, best_spot(q)); s = st(q)
    mine = [t[3:5] for t in s['tiles'] if t[5] == 0]; theirs = [t[3:5] for t in s['tiles'] if t[5] == 1]
    report(blocked and [0, 0] in mine and [0, 0] not in theirs, 'steal: tile moves to you, unfit one blocked', 'blocked %s, mine %s, theirs %s' % (blocked, mine, theirs))

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
    kid = pixel(q, q.evaluate("()=>__dg.edge(4,6,3)")); pc = pixel(q, q.evaluate("()=>__dg.edge(14,6,3)")); seam = q.evaluate("()=>__dg.edge(4,6,0)"); mid = pixel(q, [seam[0] - 1, seam[1]])
    ok = kid[1] > kid[0] + 40 and pc[0] > pc[1] + 40 and mid in ([232, 197, 71, 255], [63, 134, 200, 255]) or False
    report(ok, 'borders: green kid, red PC, one rectangle', 'kid %s pc %s seam %s' % (kid, pc, mid))

def f_game_end(q):  # the game ends when the tiles run out; most points wins
    table(q, bag=[[0, 0]] * 4, coins=[20, 2], jarQueue=[COIN] * 20)
    for _ in range(60):
        s = st(q)
        if s['over']: break
        w = s['wait']
        if w and w['who'] == 0:
            if w['kind'] == 'pick': tap(q, 'draft-%d' % s['fits'].index(True))
            elif w['kind'] == 'place': drag_to(q, best_spot(q))
            elif w['kind'] == 'jar': tap(q, 'jar-0')
        time.sleep(0.05)
    s = st(q); report(s['over'] and s['winner'] == 0, 'end: tiles run out, most coins wins', 'winner %s coins %s' % (s['winner'], [p['coins'] for p in s['players']]))

# SECTION: RUN
FLOWS = {n[2:]: f for n, f in list(globals().items()) if n.startswith('f_')}
def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in (names or FLOWS):
            try: q = page(b); FLOWS[n](q); q.context.close()
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0][:120])
        b.close()
