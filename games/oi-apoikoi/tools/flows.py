# Flow tests: what the owner does, in the running game: real page, real mouse taps and drags on what he sees.
# One browser and one page for the whole run: each flow starts a new game with a set table (fast: the PC's hand moves without waiting)
# and prints PASS or FAIL, [its flow name], what it checks, and what was seen. Waits are on the game's state, never on a fixed sleep.
# Colours are numbered 0-5 (0 and 1 the most common); a tile is [first half, second half]; the board is 16 x 16 squares, the start tiles [0, 1] at (4, 10) turned 0 (the kid's) and (11, 5) turned 2 (the PC's: the kid's turned half a turn).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'empty'}, {'k': 'coins'}, {'k': 'coins2'}, {'k': 'slot'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib, datetime, math
from playwright.sync_api import sync_playwright
GAME = next((pathlib.Path(__file__).resolve().parent.parent).glob('*.html'))  # this copy's own built page (whatever its name then), so old and new code can be tested at once
COIN = {'k': 'coins'}
NOW = ['']  # the flow running, for the report lines
EDGE_GOODS = 1200  # ms: longer than the goods of a placed tile take to fly out of their edges
WAIT = 1500  # ms: the game answers in a few ms in fast mode, so a flow that waits longer has failed; short waits keep failing runs short

# SECTION: HELPERS -- the page, a set table, taps and drags on what is drawn, the game's state
def settle(q): q.evaluate("()=>__dg.render()")  # the game answers a tap at once; draw it now, so what is on screen (and its buttons) is current
def table(q, **opts):  # a new game on a set table (goods=[kid's, PC's]: the goods each player has saved)
    opts.setdefault('fast', True); opts.setdefault('seed', 1)  # always seeded: a flow never depends on luck
    if opts['fast']: pause_clock(q)  # a fast game needs no time to pass; a running clock draws 60 frames a second for nothing
    q.evaluate("(o)=>__dg.restart(o)", opts); settle(q)
    if not opts['fast']: run_until(q, "()=>!!__dg.state().wait")  # through the round's morning light, to the first pick
def skip(q, ms):  # jump the paused fake clock on (each due timer fires once, no frame in between): for waits whose middle nobody looks at
    q.clock.fast_forward(ms); settle(q)
def run_until(q, cond, limit=4000):  # jump the paused fake clock on in short steps (no frames between: they cost about half a real second per fake second) until the game is in the state asked
    for _ in range(limit // 100):
        if q.evaluate(cond): break
        skip(q, 100)
    settle(q)
def st(q): return q.evaluate("()=>__dg.state()")
def tap(q, bid):
    q.wait_for_function("(id)=>__dg.btn(id)", arg=bid, timeout=WAIT, polling=5)
    p = q.evaluate("(id)=>__dg.btn(id)", bid); q.mouse.click(p[0], p[1]); settle(q)
def waiting(q, kind, who=0):
    q.wait_for_function("([k,w])=>{const s=__dg.state();return s.wait&&s.wait.kind===k&&s.wait.who===w}", arg=[kind, who], timeout=WAIT, polling=5)
def path(q, a, b, up=True):  # a finger drag: press, move in small steps, let go
    q.mouse.move(a[0], a[1]); q.mouse.down(); q.mouse.move(b[0], b[1], steps=6)
    if up: q.mouse.up()
    settle(q)
def pause_clock(q):  # stop the page's fake clock a second ahead; run_for then moves it on (a date, not a number: a number after an earlier pause is refused)
    q.clock.pause_at(datetime.datetime.fromtimestamp(q.evaluate("()=>Date.now()") / 1000 + 1))
def held(q): return q.evaluate("()=>__dg.held()")
def drag_to(q, sp):  # turn the tile where it lies by tapping it, then drag it to the spot {x, y, r}
    while st(q)['wait']['r'] != sp['r']: h = held(q); q.mouse.click(h[0], h[1]); settle(q)
    path(q, held(q), q.evaluate("(s)=>__dg.tileAt(s.x,s.y,s.r)", sp))
def best_spot(q): return max(st(q)['spots'], key=lambda p: p['m'])
def tile_count(q, who): return sum(1 for t in st(q)['tiles'] if t[5] == who)
def drawn(q, kind): return q.evaluate("(k)=>__dg.drawn().filter(d=>d.k===k)", kind)  # filtered in the page: the whole list is long
def stock_edge(q): return max(x['x'] + x['r'] for x in drawn(q, 'place') if x['o'] == 0)  # the kid's materials end here: a good flying from further right comes from the board
def report(ok, name, seen): print('%-4s [%s] %-40s %s' % ('PASS' if ok else 'FAIL', NOW[0], name, seen))
def diamond(q):  # the board's diamond as drawn: its centre and half sizes
    b = drawn(q, 'boardarea')[0]; return b['x'] + b['w'] / 2, b['y'] + b['h'] / 2, b['w'] / 2, b['h'] / 2
def off_board(dm, x, y, r):  # a round thing at (x, y) clears the board's diamond by its radius
    cx, cy, a, c = dm; return (abs(x - cx) * c + abs(y - cy) * a - a * c) / (a * a + c * c) ** 0.5 >= r - 0.5
def min_gap(items):  # the smallest gap between any two round things
    return min((((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2) ** 0.5 - a['r'] - b['r'] for i, a in enumerate(items) for b in items[i + 1:]), default=99)
FACES = [['coin', 'jar', 'set', 'blank']] * 3  # a slot machine's faces, wheel by wheel: 2 coins, 2 jars, 2 of each material, a blank (owner 25 Nov)
K3 = [[3, 0, 0, 0, 0, 0], [0] * 6]  # the kid has 3 goods of colour 0: a [0, 4] tile left of the start tile lights 2 more, and the 5 make a jar
def get_jar(q, contents, coins=0, slots=(), faces=FACES):  # place a tile with one connection: its jar; open it (slots: the face each spin lands on)
    table(q, bag=[[0, 4]] * 4, coins=[coins, 0], jarQueue=contents + [COIN] * 8, slotQueue=list(slots), slotFaces=faces)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
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
def f_colour_split(q):  # owner 25 Nov (prototype): 6 colours (the 6th teal), 28 tiles: halves 10, 10, 9, 9, 9, 9; each colour has its row in his area
    s = st(q); rows = sorted({d['c'] for d in drawn(q, 'place') if d['o'] == 0})
    report(s['halves'] == [10, 10, 9, 9, 9, 9] and s['left'] == 28 and rows == list(range(6)), 'colours: 6, 28 tiles, halves 10/10/9/9/9/9', '%s, %d tiles, goods rows %s' % (s['halves'], s['left'], rows))
def f_first_round_fits(q):  # owner 24 Nov: of the first round's 4 tiles, 2 surely fit (one for each player); the other 2 are truly random
    fits, unfit_seen, places = [], 0, set()
    for seed in range(1, 41):
        table(q, seed=seed); f = st(q)['fits']; fits.append(sum(f)); unfit_seen += f.count(False); places.add(tuple(k for k, v in enumerate(f) if v))
    ok = min(fits) >= 2 and unfit_seen > 0 and len(places) > 1
    report(ok, 'first round: 2 surely fit, 2 random', 'fewest fitting %d, tiles that fit nowhere in 40 games %d, fitting tiles in %d different places' % (min(fits), unfit_seen, len(places)))

def f_tap_turns(q):  # tap the won tile where it lies (in the top row) to turn it
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h = held(q)
    q.mouse.click(h[0], h[1]); settle(q); r1 = st(q)['wait']['r']; q.mouse.click(h[0], h[1]); settle(q)
    report(r1 == 1 and st(q)['wait']['r'] == 2, 'tile: a tap turns it where it lies', 'turns %d then %d' % (r1, st(q)['wait']['r']))

def f_drag_place(q):  # drag the tile from the top row; it snaps in as one tile; no squares are drawn around the land, no tray
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
    ids = q.evaluate("()=>__dg.buttons()"); marks = [b for b in ids if b.startswith('spot') or b == 'tray']
    drag_to(q, {'x': 3, 'y': 10, 'r': 2}); mine = [t for t in st(q)['tiles'] if t[5] == 0 and t[:5] == [3, 10, 2, 0, 4]]
    report(not marks and len(mine) == 1, 'place: dragged tile snaps in', 'extra marks %s, placed %s' % (marks, mine))

def f_drag_from_pile(q):  # owner 24 Nov: no tap first: press a tile in the pile and drag it straight to its place; a plain tap still just takes it, unturned
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8)
    path(q, q.evaluate("()=>__dg.btn('draft-0')"), q.evaluate("()=>__dg.tileAt(4,9,0)"))
    placed = [4, 9, 0, 0, 4] in [t[:5] for t in st(q)['tiles'] if t[5] == 0]
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); w = st(q)['wait']
    report(placed and (w['kind'], w['who'], w['r']) == ('place', 0, 0), 'pile: drag straight from the pile', 'placed %s; after a tap %s' % (placed, w))

def f_carried_tilts(q):  # owner 24 Nov ("rethink all UI": pieces do not feel physical): a carried tile tilts toward where it is going, and straightens when it stops
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h = held(q)
    tilt = lambda: drawn(q, 'heldmark')[0]['tilt']
    q.mouse.move(h[0], h[1]); q.mouse.down(); q.mouse.move(h[0] + 200, h[1] + 120, steps=6); settle(q); right = tilt()
    pause_clock(q); skip(q, 500); still = tilt(); q.clock.resume()
    q.mouse.move(h[0] - 100, h[1] + 120, steps=6); settle(q); left = tilt(); q.mouse.up(); settle(q)
    ok = right >= 4 and abs(still) < 0.5 and left <= -4
    report(ok, 'carried tile tilts with the drag', 'moving right %.1f deg, standing still %.1f deg, moving left %.1f deg' % (right, still, left))

def f_tile_bounces(q):  # owner 24 Nov ("rethink all UI": pieces do not feel physical): a tile that lands on the board bounces a little (lands big, squashes, settles), quickly
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    scale = lambda: [x['scale'] for x in drawn(q, 'bounce')]
    seen = [scale()]
    for _ in range(4): skip(q, 70); seen.append(scale())
    skip(q, 200); after = scale(); q.clock.resume()
    flat = [v[0] if v else 1 for v in seen]
    ok = flat[0] > 1.04 and min(flat) < 0.99 and not after
    report(ok, 'a landing tile bounces', 'size every 70 ms %s, then %s' % ([round(v, 3) for v in flat], after or 'still'))

def f_board_tap(q):  # owner 24 Nov ("rethink all UI": the board does not answer a tap): a tap on the board's land puffs dust where it lands, with a soft knock, and changes nothing
    table(q, bag=[[0, 4]] * 4); before = st(q); t = before['tiles'][0]; p = q.evaluate("([x,y])=>__dg.square(x,y)", t[:2])  # owner 27 Nov: a tap on the water splashes (f_water_tap); on land it still puffs dust
    q.mouse.click(p[0], p[1]); settle(q); after = st(q)
    dust = [x for x in drawn(q, 'speck') if abs(x['x'] - p[0]) < 30 and abs(x['y'] - p[1]) < 30]; h = q.evaluate("()=>__dg.sounds()")
    ok = len(dust) >= 6 and 'board' in h and after['wait'] == before['wait'] and after['tiles'] == before['tiles']
    report(ok, 'a tap on the board answers', '%d dust specks at the tap, sounds %s, nothing else changed %s' % (len(dust), h, after['wait'] == before['wait']))

def f_drag_leave(q):  # drag, leave it anywhere, turn it there, drag again: it is placed only when it snaps
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
    far = q.evaluate("()=>__dg.tileAt(9,1,0)"); path(q, held(q), far); h1 = held(q); left = h1 is not None and abs(h1[0] - far[0]) < 2 and abs(h1[1] - far[1]) < 2
    q.mouse.click(h1[0], h1[1]); settle(q); turned = st(q)['wait']['r'] == 1
    mid = q.evaluate("()=>__dg.tileAt(9,9,1)"); path(q, held(q), mid); still = st(q)['wait']['kind'] == 'place' and tile_count(q, 0) == 1
    drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    report(left and turned and still and tile_count(q, 0) == 2, 'tile: left anywhere until it snaps', 'left %s turned %s still %s tiles %d' % (left, turned, still, tile_count(q, 0)))

def f_snap_preview(q):  # before it snaps the place is shown; far from any place nothing is shown
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place')
    goal = q.evaluate("()=>__dg.tileAt(4,9,0)"); path(q, held(q), [goal[0] + 8, goal[1] + 6], up=False); near = st(q)['snap']; ghost = len([d for d in drawn(q, 'tile') if d['look'] == 'ghost'])
    far = q.evaluate("()=>__dg.tileAt(9,0,0)"); q.mouse.move(far[0], far[1]); settle(q); away = st(q)['snap']; q.mouse.up(); settle(q)
    ok = near == {'x': 4, 'y': 9, 'r': 0} and ghost == 1 and away is None and st(q)['wait']['kind'] == 'place'
    report(ok, 'snap: place shown before it snaps', 'near %s ghost %d, away %s' % (near, ghost, away))

def f_own_land(q):  # a tile must have a matching edge with your own land; matching only the PC's land is not enough
    table(q, bag=[[2, 4], [0, 4], [0, 4], [0, 4]], tiles=[[9, 3, 0, 2, 2, 1]]); s = st(q)
    report(s['fits'][0] is False and q.evaluate("()=>!__dg.btn('draft-0')"), 'match: must be with your own land', 'fits %s' % s['fits'])

def f_pile_no_frames(q):  # owner 24 Nov: no outline around the pile's tiles
    table(q, bag=[[0, 4]] * 4); c = q.evaluate("()=>__dg.btn('draft-0')"); hw = (q.evaluate("()=>__dg.btnBox('draft-0')")['w'] - 24) / 3; m = drawn(q, 'market')[0]
    hh = hw / 3 ** 0.5; beside = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [c[0] - 1.5 * hw - 6, c[1] - hh / 2])  # just left of the tile's left corner (its walls hang below it): the market tray's own colour, not a frame
    tray = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [m['x'] + 12, m['y'] + m['h'] - 12])  # the tray, away from the tile
    report(beside == tray, 'pile: tiles have no outline', 'beside the tile %s, the tray %s' % (beside, tray))

def f_pile_fits(q):  # owner 24 Nov ("rethink all UI"): the pile ran off the top of the screen; a full pile stays on screen; owner 25 Nov: the pile holds every tile, a layer each
    table(q); pile = drawn(q, 'pile')[0]; ds = drawn(q, 'tile')[0]['h']; T = drawn(q, 'market')[0]; s = st(q); in_pile = s['left'] - sum(1 for t in s['draft'] if t)
    top, bottom = pile['y'] - ds / 2, pile['bottom']
    ok = pile['layers'] == in_pile and top >= 4 and bottom <= T['y'] + T['h'] and pile['step'] >= 1  # every layer still its own line
    report(ok, 'pile: every tile a layer, on screen', '%d layers for %d tiles, %.1f px apart, from %.0f to %.0f px (screen top 0, market bottom %.0f)' % (pile['layers'], in_pile, pile['step'], top, bottom, T['y'] + T['h']))

def f_deal(q):  # owner 25 Nov (prototype): the 4 market tiles are dealt one by one from the pile
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1}); counts, ms = [], 0
    while ms < 4000 and not st(q)['wait']:
        skip(q, 50); ms += 50; n = sum(1 for t in st(q)['draft'] if t); f = [x for x in drawn(q, 'flight') if x['look'] == 'tile']
        if not counts or counts[-1][0] != n: counts.append((n, len(f)))
    h = q.evaluate("()=>__dg.sounds()"); q.clock.resume()
    ok = [n for n, _ in counts] == [0, 1, 2, 3, 4] and all(f <= 1 for _, f in counts) and h.count('deal') == 4
    report(ok, 'market: dealt one by one', 'market tiles seen %s (tiles flying at once %s), deal sounds %d' % ([n for n, _ in counts], [f for _, f in counts], h.count('deal')))
def f_round_start_no_goods(q):  # owner 24 Nov: land does not make goods each round, a tile's halves make none; goods left carry over to the next round; a round starts with morning light
    table(q, bag=[[2, 2], [2, 2], [3, 3], [3, 3], [2, 2]], tiles=[[4, 11, 0, 2, 2, 0]], goods=[[0, 0, 0, 0, 0, 1], [0] * 6], jarQueue=[COIN] * 8)  # only the kid can place: the PC passes; [3, 3] fits nobody; his 1 teal good is never touched
    s = kid_plays(q, lambda s: s['round'] == 2 and s['wait'] and s['wait']['kind'] == 'pick'); h = q.evaluate("()=>__dg.sounds()"); g = s['players'][0]['goods']
    ok = s['round'] == 2 and sum(g) > 0 and sum(g) + 5 * h.count('made') == h.count('edge') + 1 and g[5] == 1 and 'dissolve' not in h and h.count('dawn') == 2
    report(ok, 'round: no goods from land, goods carry over', 'round %d, goods %s, jars made %d, goods from edges %d, lost %s, morning lights %d' % (s['round'], g, h.count('made'), h.count('edge'), 'dissolve' in h, h.count('dawn')))

def f_connections(q):  # owner 25 Nov (prototype): each connection (matching edge, with any land) gives a jar, dropping from the top of the screen; it also lights the connected land
    # of that colour, both players', spreading out from it; each lit square gives one material; 5 of a colour make a jar at once
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, tiles=[[4, 11, 0, 0, 0, 0], [6, 11, 0, 0, 0, 1]], jarQueue=[COIN] * 8)  # his [0, 0] under the start tile, the PC's [0, 0] beside it
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})  # the 0 half meets the start tile's 0: one connection
    land = [(3, 10), (4, 10), (4, 11), (5, 11), (6, 11), (7, 11)]; at = {tuple(round(v) for v in q.evaluate("([x,y])=>__dg.square(x,y)", sq)): sq for sq in land}
    order, drops, glows, ms = [], 0, 0, 0
    while ms < 6000:
        skip(q, 50); ms += 50; d = drawn(q, 'flight'); glows = max(glows, len(drawn(q, 'edgeglow')))
        order += [at[(round(x['fx']), round(x['fy']))] for x in d if x['look'] == 'good' and (round(x['fx']), round(x['fy'])) in at and at[(round(x['fx']), round(x['fy']))] not in order]
        drops = max(drops, sum(1 for x in d if x['look'] == 'jar' and x['fy'] < 0))
        w = st(q)['wait']
        if w and w['kind'] == 'jar': break
    p = st(q)['players'][0]; q.clock.resume()
    ok = glows == 1 and order == land and p['goods'][0] == 1 and p['jars'] == 2 and drops >= 1
    report(ok, 'connections: a jar each; the connected land lights up', 'edges glowing %d; materials from %s; goods %s; jars %d; jars dropping from the top at once %d' % (glows, order, p['goods'], p['jars'], drops))
def f_five_make_jar(q):  # owner 24 Nov: 5 goods of one colour become a jar at once (not at the round's end) and it is opened at once; the jar comes to its place first, then the goods fly into it on curves, one by one
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=K3, jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); P = stock_edge(q); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); drops, intos, ms = [], [], 0
    while ms < 4000:
        skip(q, 50); ms += 50; d = q.evaluate("()=>__dg.drawn().filter(d=>d.k==='flight')")
        drops += [(ms, x) for x in d if x['look'] == 'jar']; intos += [(ms, x) for x in d if x['look'] == 'good' and x['fx'] < P]  # goods leaving the stockpile
        w = st(q)['wait']
        if w and w['kind'] == 'jar': break
    s = st(q); jar = [x for x in drawn(q, 'jar') if x['o'] == 0]; left = [x for x in drawn(q, 'good') if x['o'] == 0]; tap(q, 'jar-0')
    run_until(q, "()=>__dg.state().players[0].coins===1"); coins = st(q)['players'][0]['coins']; q.clock.resume()
    into = [(m, x) for m, x in intos if any(abs(x['tx'] - j['x']) < 5 for j in jar)]; targets = {round(x['tx']) for _, x in into}  # the 2 lit goods make 5: they fly into one jar (the connection's jar is the other)
    first = bool(drops) and bool(into) and into[0][0] > drops[-1][0]  # the jar is in its place before any good flies into it
    ok = bool(drops) and drops[0][1]['fy'] < 0 and len(jar) == 2 and len(targets) == 1 and first and len({(round(x['fx']), round(x['fy'])) for _, x in into}) == 5 and any(x['y'] < min(x['fy'], x['ty']) - 10 for _, x in into) \
        and not left and s['round'] == 1 and s['phase'] == 'round' and s['wait']['who'] == 0 and coins == 1
    report(ok, 'jars: 5 of a colour make a jar at once, opened at once', 'jar from the top %s, in place first %s, goods into it from %d places, goods left %d, round %d %s, opened for a coin %s' % (bool(drops) and drops[0][1]['fy'] < 0, first, len({(round(x['fx']), round(x['fy'])) for _, x in into}), len(left), s['round'], s['phase'], coins == 1))

def f_no_bidding(q):  # owner 24 Nov: no bidding (too slow: every pick triggered it): the player whose turn it is takes the tile he picks
    kid, pc = [[4, 8, 0, 2, 3, 0], [4, 6, 0, 4, 4, 0]], [[12, 4, 0, 2, 3, 1], [12, 2, 0, 4, 4, 1]]
    table(q, bag=[[0, 1], [0, 0], [0, 0], [0, 0]], tiles=kid + pc, goods=[[1] * 6, [1] * 5]); tap(q, 'draft-0'); w = st(q)['wait']; s = st(q)
    ok = w['kind'] == 'place' and w['who'] == 0 and s['players'][1]['goods'] == [1] * 5 and not drawn(q, 'bidcard') and 'bid' not in q.evaluate("()=>__dg.sounds()")
    report(ok, 'pick: the tile is yours, no bid', 'after the pick: %s, PC goods %s, bid card %s' % (w, s['players'][1]['goods'], bool(drawn(q, 'bidcard'))))

def f_material_lines(q):  # owner 25 Nov (prototype): materials come in a line per colour, so a colour never waits for another's jar; a full row's jar drops while its 5th flies; lit squares light 120 ms apart
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, goods=[[4, 0, 0, 0, 0, 0], [0] * 6], jarQueue=[COIN] * 8); gap = q.evaluate("()=>__dg.gaps().lit")
    tap(q, 'draft-0'); waiting(q, 'place'); P = stock_edge(q); drag_to(q, {'x': 4, 'y': 11, 'r': 0})  # 2 connections: colour 0 lights 2 squares (4 + 2: a jar), colour 1 lights 2
    starts, ms, drops = {}, 0, []  # drops: each jar dropping from the top, and whether a colour 0 good was flying from the board when it set off
    while ms < 3000:
        skip(q, 20); ms += 20; d = drawn(q, 'flight'); board = [x for x in d if x['look'] == 'good' and x['fx'] > P]
        for x in board: starts.setdefault((round(x['fx']), round(x['fy'])), (ms, x['c']))
        for x in d:
            if x['look'] == 'jar' and x['fy'] < 0 and round(x['tx']) not in [t for t, _ in drops]: drops.append((round(x['tx']), any(g['c'] == 0 for g in board)))
        w = st(q)['wait']
        if w and w['kind'] == 'jar': break
    q.clock.resume(); order = sorted(starts.values()); c0 = [t for t, c in order if c == 0]; c1 = [t for t, c in order if c == 1]
    while_flying = [f for _, f in drops]  # 2 connections' jars and the full row's jar
    ok = len(c0) == 2 and len(c1) == 2 and c1[0] < c0[1] and abs((c1[1] - c1[0]) - gap) <= 40 and while_flying == [True] * 3
    report(ok, 'materials: a line per colour; the jar drops while the 5th flies; lit squares apart', 'colour 0 goods leave at %s ms, colour 1 at %s ms (lit gap %d); full row\'s jar dropping while its 5th flies %s' % (c0, c1, gap, while_flying))

def f_row_never_overflows(q):  # owner 24 Nov: a row never needs more than 5 places: a tile giving 2 goods to a row of 4 fills it, the 5 fly into a jar, and the 6th good takes the first place
    pause_clock(q); table(q, fast=False, bag=[[0, 0]] * 4, tiles=[[4, 11, 0, 0, 0, 0]], goods=[[4, 0, 0, 0, 0, 0], [0] * 6], jarQueue=[COIN] * 8)
    xs = sorted(x['x'] for x in drawn(q, 'place') if x['o'] == 0 and x['c'] == 0); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 1}); most, targets, ms = 0, set(), 0  # 2 connections lighting 5 squares of colour 0: 4 + 5 goods
    while ms < 5000:
        skip(q, 50); ms += 50; most = max(most, sum(1 for x in drawn(q, 'good') if x['o'] == 0 and x['c'] == 0))
        targets |= {round(x['tx']) for x in drawn(q, 'flight') if x['look'] == 'good' and x['fx'] > xs[-1] + 40}  # goods flying from the board to the stockpile
        w = st(q)['wait']
        if w and w['kind'] == 'jar': break
    g = st(q)['players'][0]; q.clock.resume()
    ok = most <= 5 and targets <= {round(v) for v in xs} and g['goods'][0] == 4 and g['jars'] == 3  # 2 connection jars and 1 of 5 goods
    report(ok, 'stockpile: a full row becomes a jar before the next good', 'most goods in the row %d, goods flew to places %s (row %s), left %d, jars %d' % (most, sorted(targets), [round(v) for v in xs], g['goods'][0], g['jars']))

def away_and_back(q, k):  # carry the tile in hand onto the board, leave it, then carry it back to its market place
    path(q, held(q), [640, 600]); path(q, held(q), q.evaluate("(k)=>__dg.slot(k)", k))
def f_put_back(q):  # owner 24 Nov: a picked tile can be put back on its market place and another picked
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); away_and_back(q, 0); waiting(q, 'pick'); s = st(q)
    ok = s['draft'][0] == [0, 4] and s['players'][0]['got'] == 0 and q.evaluate("()=>!!__dg.btn('draft-1')")
    report(ok, 'put back: returns to the market', 'back on its place %s, tiles taken %d' % (s['draft'][0], s['players'][0]['got']))

def f_sounds(q):  # owner 24 Nov: "add some sounds, it's hard to follow what happens": each thing that happens has its sound, in the order it happens
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot'); tap(q, 'wheel-0'); tap(q, 'wheel-1'); tap(q, 'lever')
    q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); a = [n for n in q.evaluate("()=>__dg.sounds()") if n not in ('dawn', 'deal', 'turn', 'into')]  # the morning, the deal, the turn sound and the goods going into a jar have their own flows
    want = ['pick', 'snap', 'edge', 'edge', 'jar', 'roll', 'roll', 'roll', 'spin', 'stop', 'stop', 'stop', 'clamp', 'clamp', 'roll', 'spin', 'stop', 'win']  # each wheel ticks as it rolls (owner 24 Nov)
    ok = a[:len(want)] == want
    report(ok, 'sounds: one for each thing, in order', 'slot jar: %s, heard %s' % (a[:len(want)], sorted(set(a))))

def f_sound_kinds(q):  # owner 24 Nov: "a weird blip when I tap a piece"; "jars must make a breaking sound": a tap knocks like wood, a jar breaks like clay, a coin clinks; no beeps anywhere
    get_jar(q, [COIN]); settle(q); h = [k for n, k in zip(q.evaluate("()=>__dg.sounds()"), q.evaluate("()=>__dg.heardKinds()")) if n not in ('dawn', 'deal', 'turn', 'into', 'made')]  # the morning, the deal, the turn sound and the jar being made have their own flows
    ok = h[:6] == ['knock', 'knock', 'chime', 'chime', 'break', 'clink']  # tap, snap, a material out of each of the 2 lit squares, the jar opened, its coin
    ok = ok and set(q.evaluate("()=>__dg.soundKinds()")) <= {'break', 'chime', 'clink', 'knock', 'whoosh'}
    report(ok, 'sounds: wood tap, clay break, coin clink', 'heard %s; kinds in the game %s' % (h[:6], q.evaluate("()=>__dg.soundKinds()")))

def f_many_jars_rows(q):  # owner 24 Nov: "when a lot of jars exist, make more rows, 6 jars per row; don't reduce their size"
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); one = drawn(q, 'jar')[0]['size']  # one jar alone: its size
    table(q, bag=[[0, 1]] * 4, jarQueue=[{'k': 'slot'}] + [COIN] * 20, slotQueue=[0, 0, 0], slotFaces=[['jar', 'coin', 'set', 'blank']] * 3)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'jar'); jars = drawn(q, 'jar')  # 2 jars; the first's slot machine shows three jars: 6 more
    rows = {}; [rows.setdefault(j['row'], []).append(j) for j in jars]
    W, H = q.evaluate("()=>[innerWidth, innerHeight]")
    ok = len(jars) == 7 and max(len(r) for r in rows.values()) == 6 and all(abs(j['size'] - one) < 0.5 for j in jars) and all(0 < j['y'] - j['size'] / 2 and j['y'] + j['size'] / 2 < H for j in jars)
    report(ok, 'jars: 6 to a row, more rows, same size', '%d jars in rows of %s, sizes %s (one alone %.0f)' % (len(jars), [len(r) for r in rows.values()], sorted({round(j['size']) for j in jars}), one))

def f_many_coins(q):  # owner 24 Nov: "make sure more coins than you predicted can fit"; coins easy to count and apart; owner 25 Nov (design 3): rows of at most 8 from the bottom of
    # his bottom triangle; past what it holds at full size (160 found by the main game) they shrink but stay apart, clear of the board and of his materials
    out = {}; W, H = q.evaluate("()=>[innerWidth, innerHeight]")
    for n in (12, 160):
        table(q, bag=[[0, 4]] * 4, coins=[n, 0], goods=[[4] * 6, [0] * 6]); dm = diamond(q); c = [x for x in drawn(q, 'coin') if x['o'] == 0]; pl = [x for x in drawn(q, 'place') if x['o'] == 0]
        inside = all(x['x'] - x['r'] > 0 and x['x'] < W / 2 and x['y'] + x['r'] < H and off_board(dm, x['x'], x['y'], x['r']) for x in c)
        rows = sorted({round(x['y']) for x in c}, reverse=True); per = [sum(1 for x in c if round(x['y']) == y) for y in rows]
        out[n] = (len(c) == n and inside and min_gap(c) >= 1 and min_gap(c + pl) >= 1 and max(per) <= 8 and all(a >= b for a, b in zip(per, per[1:])), len(c), inside, round(min_gap(c), 1), per[:4], round(c[0]['r'], 1), round(pl[0]['r'], 1))
    report(all(v[0] for v in out.values()) and out[12][-1] == out[12][-2] > out[160][-2], 'coins: all fit, apart, rows of at most 8', str(out))  # a few coins at full size (a material's), many smaller

def f_jars_apart(q):  # owner 24 Nov: "jar circles are touching": every jar stands apart, with a clear gap; owner 25 Nov: no glow
    table(q, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); waiting(q, 'jar'); settle(q)
    jars = sorted((d['x'], d['size'] / 2) for d in drawn(q, 'jar')); gaps = [b[0] - a[0] - a[1] - b[1] for a, b in zip(jars, jars[1:])]; glows = drawn(q, 'jarglow')
    ok = len(jars) == 2 and min(gaps) >= 12 and not glows
    report(ok, 'jars: apart, with a gap between them, no glow', 'gaps between jars %s px, glows %d' % ([round(g) for g in gaps], len(glows)))

def f_jar_lines(q):  # owner 25 Nov (prototype): jars stand in lines of up to 6, each line centred on its jars; a broken jar leaves its place empty;
    # a new jar takes the first free place and the others slide to keep the line centred
    W = q.evaluate("()=>innerWidth"); centred = lambda xs: abs((min(xs) + max(xs)) / 2 - W / 2) < 1
    def two_jars(first):  # a tile meeting 2 edges: 2 jars; the first one opened holds first
        table(q, bag=[[0, 1]] * 4, jarQueue=[{'k': first}] + [COIN] * 20, slotQueue=[0, 0, 0], slotFaces=[['jar', 'coin', 'set', 'blank']] * 3)
        tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); waiting(q, 'jar'); settle(q); return sorted((d['x'], d['slot']) for d in drawn(q, 'jar'))
    two = two_jars('empty'); tap(q, 'jar-0'); waiting(q, 'jar'); settle(q); left = [(d['x'], d['slot']) for d in drawn(q, 'jar')]
    two_jars('slot'); tap(q, 'jar-0'); waiting(q, 'jar'); settle(q); jars = drawn(q, 'jar'); row0 = sorted((d['x'], d['slot']) for d in jars if d['row'] == 0)
    waited = next(x for x, k in row0 if k == 1)
    ok = [k for _, k in two] == [0, 1] and centred([x for x, _ in two]) and left == [two[1]] and [k for _, k in row0] == list(range(6)) and centred([x for x, _ in row0]) \
        and len(jars) == 7 and abs(waited - two[1][0]) > 1
    report(ok, 'jars: lines of 6, centred; broken leaves its place; new takes the first free one', 'two jars %s; after breaking the first %s; with 6 more, row 0 %s, %d jars' % ([(round(x), k) for x, k in two], [(round(x), k) for x, k in left], [(round(x), k) for x, k in row0], len(jars)))
def f_round_end_shown(q):  # owner 24 Nov: the round's end is its own moment, seen and heard, before anything else happens in it; "the sunset is weird": evening falls (sky darkens from the top, a moon and stars), the board stays in view; leftover market tiles fly back to the pile
    pause_clock(q); table(q, fast=False, bag=[[2, 2], [3, 3]], tiles=[[4, 11, 0, 2, 2, 0], [4, 12, 0, 2, 2, 0]], jarQueue=[COIN] * 8)  # [3, 3] fits nobody: both pass, it is left in the market
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 13, 'r': 0})
    for _ in range(4):  # his jars (a connection's, and one of 5 lit goods)
        run_until(q, "()=>{const s=__dg.state();return s.phase==='end'||(s.wait&&s.wait.kind==='jar')}", 8000); w = st(q)['wait']
        if not (w and w['kind'] == 'jar'): break
        tap(q, 'jar-0')
    for _ in range(80):
        if st(q)['phase'] == 'end': break
        skip(q, 200)
    pile = drawn(q, 'pile')[0]; back, shown, moon, ms, light = [], [], False, 0, True
    while ms < 6000 and not st(q)['over']:
        skip(q, 100); ms += 100; d = q.evaluate("()=>__dg.drawn()")
        tiles = [x for x in d if x['k'] == 'flight' and x['look'] == 'tile']; back += [(ms, x) for x in tiles]
        dusk = [x for x in d if x['k'] == 'dusk']
        if dusk and not st(q)['over']: shown.append(ms); light = light and dusk[0]['a'] <= 0.5 and not [x for x in d if x['k'] == 'shade']
        moon = moon or bool([x for x in d if x['k'] == 'moon' and x['shape'] == 'crescent'])
    q.clock.resume(); h = q.evaluate("()=>__dg.sounds()")
    returned = bool(back) and abs(back[0][1]['tx'] - pile['x']) < 5 and bool(shown) and min(shown) > back[-1][0]  # back in the pile before evening falls
    ok = returned and len(shown) >= 10 and moon and light and 'roundend' in h
    report(ok, 'end: tiles back to the pile, evening falls, its own moment', 'leftover tile flew back to the pile %s; evening shown %d00 ms, moon %s, board in view %s, sound %s' % (returned, len(shown), moon, light, 'roundend' in h))

def f_turn_shown(q):  # owner 24 Nov: "make it obvious who plays; now there is no difference between me and the opponent playing": the player whose turn it is has his area lit, the other's is dimmed; a sound when the turn passes; no sign flies from face to face (owner 24 Nov: "weird")
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); settle(q)
    lit = lambda: {d['o']: d['lit'] for d in drawn(q, 'panel')}
    mine = lit(); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.state().turn===1"); pcs = lit(); w = st(q)['wait']; h = q.evaluate("()=>__dg.sounds()")
    faces = {x['o']: x for x in drawn(q, 'avatar')}; light = [x for x in drawn(q, 'flight') if x['look'] == 'turnlight']; market = drawn(q, 'market')
    bigger = faces[1]['lit'] and not faces[0]['lit'] and market and market[0]['o'] == 1; q.clock.resume()  # owner 27 Nov: the stickers never change size; his turn is his sticker's glow
    ok = mine == {0: True, 1: False} and pcs == {0: False, 1: True} and 'turn' in h and not light and bigger
    report(ok, 'turn: lit, no sign flying, his sticker glows, the market his colour', 'kid playing %s; PC playing %s (wait %s); turn sound %s; a sign flying face to face %s; PC sticker glows and market his %s' % (mine, pcs, w, 'turn' in h, bool(light), bool(bigger)))

def f_end_screen(q):  # owner 25 Nov (prototype): the end: a smaller box over the board; each player's coins fly into his pile, both piles the same coin size, rows of 10;
    # a star over the taller pile; a green play button that works
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[3, 3]] * 4, 'coins': [23, 7]}); flew, ms = False, 0  # no tile fits anyone: the game ends at once
    while ms < 4000 and not st(q)['over']:
        skip(q, 100); ms += 100; box = drawn(q, 'endbox'); flew = flew or any(box and box[0]['x'] < f['tx'] < box[0]['x'] + box[0]['w'] for f in drawn(q, 'flight') if f['look'] == 'coin')
    skip(q, 100); box, board = drawn(q, 'endbox'), drawn(q, 'boardarea')[0]; piles = {o: [c for c in drawn(q, 'endcoin') if c['o'] == o] for o in (0, 1)}; star = drawn(q, 'winner'); panel = drawn(q, 'coin')
    inside = bool(box) and board['x'] <= box[0]['x'] and box[0]['x'] + box[0]['w'] <= board['x'] + board['w'] and board['y'] <= box[0]['y'] and box[0]['y'] + box[0]['h'] <= board['y'] + board['h']
    rows = {o: sorted(sum(1 for c in v if abs(c['y'] - y) < 1) for y in {c['y'] for c in v}) for o, v in piles.items()}; sizes = {c['r'] for v in piles.values() for c in v}
    above = bool(star) and star[0]['o'] == 0 and star[0]['y'] < min(c['y'] for c in piles[0])
    q.clock.resume(); tap(q, 'again'); s = st(q); again = s['round'] == 1 and [p['coins'] for p in s['players']] == [0, 0] and s['wait'] and s['wait']['kind'] == 'pick'
    ok = flew and inside and [len(piles[0]), len(piles[1])] == [23, 7] and not panel and rows == {0: [3, 10, 10], 1: [7]} and len(sizes) == 1 and above and again
    report(ok, 'end: a box over the board, two piles, a star, play again', 'coins flew %s; box over the board %s; piles %s in rows %s, coin sizes %s; star over the taller %s; play button works %s' % (flew, inside, [len(piles[0]), len(piles[1])], rows, sizes, above, again))

def f_again_same_animals(q):  # owner 27 Nov: play again keeps the same two animals
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[3, 3]] * 4, 'coins': [3, 1]}); run_until(q, "()=>__dg.state().over", 4000)
    pets = lambda: [d['pic'].split('/')[1].split('-')[0] for d in sorted(drawn(q, 'avatar'), key=lambda d: d['o'])]
    before = pets(); q.clock.resume(); tap(q, 'again'); after = pets()
    report(after == before, 'play again: the same two animals', 'before %s, after play again %s' % (before, after))
def f_pc_best(q):  # the PC picks and places for the most jars (2 connections)
    table(q, bag=[[0, 0], [0, 1], [0, 4], [0, 4]], first=1, jarQueue=[COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] != [11, 5]]
    report(pc == [[0, 1]] and s['players'][1]['goods'] == [2, 2, 0, 0, 0, 0], 'pc: best tile, best place', 'pc tiles %s goods %s' % (pc, s['players'][1]['goods']))

def f_pc_hand(q):  # the PC's moves are slow and done by a moving hand: it points to tap, grabs to drag, showing the pointing hand for both (owner 24 Nov) (a fake clock runs the real timings at once);
    # a new game started while that hand still carries a tile: the old move never touches the new game
    pause_clock(q)
    q.evaluate("()=>__dg.restart({fast:false,bag:[[0,1],[0,0],[0,4],[0,4]],first:1,jarQueue:Array(8).fill({k:'coins'})})")
    ms, xs, gs, dragged, drag_pics = 0, set(), set(), False, set()
    while ms < 20000:
        q.clock.run_for(200); ms += 200; s = st(q)
        xs.add(round(s['hand']['x'])); gs.add(s['hand']['g']); dragged = dragged or s['handDrag']
        if s['handDrag']: settle(q); drag_pics |= {d['pic'] for d in drawn(q, 'hand')}
        if ms >= 2500 and dragged and {'point', 'grab'} <= gs: break  # slow enough, and seen pointing, grabbing and dragging
    slow = ms >= 2500 and len(xs) > 10 and dragged and {'point', 'grab'} <= gs and drag_pics == {'backhand_index_pointing_up'}
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h0 = held(q)
    q.clock.run_for(1800); settle(q); h1 = held(q); q.clock.resume()  # longer than the rest of the PC's drag
    report(slow and h0 == h1, 'pc: slow, by a moving hand; a new game is left alone', '%d ms, hand at %d places, gestures %s, pictures while dragging %s; new game tile %s then %s' % (ms, len(xs), sorted(gs), sorted(drag_pics), h0, h1))

def f_pc_most_jars(q):  # owner (design): the PC does what is best for this turn; owner 25 Nov rules: a move is worth the jars it makes now, its connections' and those of
    # 5 materials; here [1, 1] and [0, 3] both connect once, but [0, 3] lights 6 colour-0 squares onto his 4: 2 more jars
    table(q, bag=[[1, 1], [0, 3], [3, 3], [3, 3]], first=1, tiles=[[11, 4, 3, 0, 0, 1], [10, 4, 3, 0, 0, 1]], goods=[[0] * 6, [4, 0, 0, 0, 0, 0]], jarQueue=[COIN] * 12)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] not in ([11, 5], [11, 4], [10, 4])]; opened = sum(s['players'][1]['opened'].values())
    report(pc == [[0, 3]] and opened == 3, 'pc: the move that makes the most jars', 'pc placed %s, jars %d' % (pc, opened))

def f_pc_slot(q):  # the PC takes the best expected result on the slot machine too (here: two coins showing, chasing the third is worth it: it keeps both, pays 1 and wins 6)
    table(q, bag=[[0, 4]] * 4, first=1, coins=[0, 5], jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 0, 1, 0], slotFaces=FACES)  # coin, coin, jar; the respin of the third wheel lands on coin
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); c = st(q)['players'][1]['coins']
    report(c == 5 - 1 + 6, 'pc: slot machine played for the most', 'pc coins %d (5, paid 1 to chase the third coin, won 3 faces of 2 coins)' % c)
def f_jar_mix(q):  # owner 25 Nov, per 100 jars: "1 coin about 45%, Empty about 10%, 2 coins about 10%, One of each material about 10%, Another jar about 8%, First player about 8%, Slot machine about 5%, Tile about 4%"; no stealing
    table(q, bag=[[0, 4]] * 4, seed=11)  # seeded: an unseeded sample missed the 1.5% band about once in 15 runs
    n = 8000; m = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)
    want = {'empty': 10, 'coins': 45, 'coins2': 10, 'tile': 4, 'slot': 5, 'first': 8, 'jar': 8, 'set': 10}
    ok = set(m) == set(want) and all(abs(100 * m[k] / n - v) < 1.5 for k, v in want.items())  # the shares are per 100 jars
    report(ok, 'jars: the owner\'s mix, no stealing', ', '.join('%s %.1f%%' % (k, 100 * m.get(k, 0) / n) for k in sorted(set(want) | set(m))))
def f_empty_jar(q):  # owner 24 Nov: some jars hold nothing: it breaks, shows it is empty, and nothing is gained
    get_jar(q, [{'k': 'empty'}])
    waiting(q, 'pick'); p = st(q)['players'][0]
    report(p['coins'] == 0 and p['jars'] == 0 and 'jar' in q.evaluate("()=>__dg.sounds()"), 'jars: an empty jar gives nothing', 'coins %d jars %d' % (p['coins'], p['jars']))

def f_jar_breaks(q):  # owner 24 Nov: "jars should visually break and the revealed bonus comes from inside them"; "the you play first should fly to its place"; a coin flies to his coins
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[COIN, {'k': 'first'}] + [COIN] * 8)  # the tile meets 2 edges: 2 jars
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000)
    def watch(btn, until):  # tap a jar, then watch the screen until the reward has landed
        at = q.evaluate("(b)=>__dg.btn(b)", btn); tap(q, btn); seen, ms = [], 0
        while ms < 3000:
            skip(q, 50); ms += 50; d = q.evaluate("()=>__dg.drawn().filter(d=>d.k==='flight'||d.k==='speck')"); s = st(q); seen.append((d, s))
            if until(s): break
        return at, seen
    at1, seen1 = watch('jar-1', lambda s: s['players'][0]['coins'] == 1)
    at0, seen0 = watch('jar-0', lambda s: s['first'] == 0)
    def flights(seen, look): return [x for d, _ in seen for x in d if x['k'] == 'flight' and x['look'] == look]
    near = lambda a, b, r=12: abs(a[0] - b[0]) < r and abs(a[1] - b[1]) < r
    specks = [(x['x'], x['y']) for d, _ in seen1 for x in d if x['k'] == 'speck']
    broke = bool(specks) and all(near(p, at1, 40) for p in specks)
    out = flights(seen1, 'shown'); came_out = bool(out) and near((out[0]['fx'], out[0]['fy']), at1)
    coin = flights(seen1, 'coin'); P = drawn(q, 'panel')[0]['w']; coin_flew = bool(coin) and coin[0]['tx'] < P and all(s['players'][0]['coins'] == 0 for d, s in seen1 if any(x['k'] == 'flight' and x['look'] == 'coin' for x in d))
    star = flights(seen0, 'bee'); token = drawn(q, 'token'); star_flew = bool(star) and bool(token) and near((star[-1]['tx'], star[-1]['ty']), (token[0]['x'], token[0]['y'])) and all(s['first'] is None for d, s in seen0 if any(x['k'] == 'flight' and x['look'] == 'bee' for x in d))
    q.clock.resume()
    report(broke and came_out and coin_flew and star_flew, 'jars: break where tapped, the bonus comes out, rewards fly to their place', 'broke where tapped %s, bonus out of it %s, coin flew to his coins %s, star flew to its place %s' % (broke, came_out, coin_flew, star_flew))

def f_jars_at_once(q):  # owner 25 Nov (prototype): jars break at once, as fast as he taps; each prize (a picture) pops up above its own jar, stays a moment, then flies to its place;
    # only the slot machine and a tile to place wait (for the other prizes to land, then for him)
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[COIN, {'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 1, 3], slotFaces=FACES)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000)  # 2 connections: 2 jars
    jars = sorted((d['x'], d['y'], d['size']) for d in drawn(q, 'jar')); tap(q, 'jar-0'); again = (st(q)['wait'] or {}).get('kind') == 'jar'; tap(q, 'jar-0'); left = st(q)['players'][0]['jars']
    run_until(q, "()=>{const d=__dg.drawn();return d.filter(x=>x.k==='shown').length===2&&!d.some(x=>x.k==='flight'&&x.look==='shown')}", 2000); cards = sorted((d['x'], d['y']) for d in drawn(q, 'shown'))
    above = len(cards) == 2 and all(abs(c[0] - j[0]) < 5 and c[1] < j[1] - j[2] / 2 for c, j in zip(cards, jars))  # risen out of it, above it
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='slot'}", 8000); coins = st(q)['players'][0]['coins']; tap(q, 'tray'); q.clock.resume()
    ok = again and left == 0 and above and coins == 1
    report(ok, 'jars: break at once; prize above its jar; the slot machine waits', 'next tap taken at once %s, jars left %d, prizes above their jars %s (%s over %s), coin landed before the machine %s' % (again, left, above, [(round(x), round(y)) for x, y in cards], [(round(x), round(y)) for x, y, _ in jars], coins == 1))

def f_jars_step_aside(q):  # owner 24 Nov: "the extra tile bonus makes the jars I was opening disappear; it should temporarily fly them to some free area"
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[{'k': 'tile'}] + [COIN] * 8)  # 2 jars; the first holds a tile
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000); tap(q, 'jar-1')
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='place'}", 3000); q.clock.run_for(600); settle(q)
    T = q.evaluate("()=>innerHeight*0.16"); away = [j for j in drawn(q, 'jar') if j['o'] == 0]
    aside = len(away) == 1 and away[0]['y'] < T + 20
    drag_to(q, best_spot(q)); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000); back = [j for j in drawn(q, 'jar') if j['o'] == 0 and not j.get('new')]; q.clock.resume()
    ok = aside and len(back) == 1 and back[0]['y'] > T + 100
    report(ok, 'jars: step aside during a bonus tile, then come back', 'waiting jar seen aside while placing %s (%s), back in the row after %s' % (aside, [(round(j['x']), round(j['y'])) for j in away], [(round(j['x']), round(j['y'])) for j in back]))

def f_jar_picture(q):  # owner 25 Nov (prototype): what a jar held is a picture, no words (the 24 Nov labels are gone); an empty jar shows an X
    pause_clock(q); table(q, bag=[[0, 4]] * 4, fast=False, jarQueue=[{'k': 'empty'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='shown')", 3000); shown = [d['j'] for d in drawn(q, 'shown')]; texts = [d['text'] for d in drawn(q, 'label')]; x = len(drawn(q, 'nothing')); q.clock.resume()
    report(shown == ['empty'] and not texts and x == 1, 'jars: a picture, no words; empty is an X', 'shown %s, words %s, X drawn %d' % (shown, texts, x))

def f_pass_sound(q):  # owner 25 Nov (prototype): a skipped turn is only its sound: nothing covers the screen
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[3, 3]] * 4, 'tiles': [[11, 4, 0, 3, 3, 1]]}); covered, ms = 0, 0  # only the PC's land takes [3, 3]: his turn passes
    while ms < 3000 and not st(q)['passes'][0]:
        skip(q, 100); ms += 100
    for _ in range(5): skip(q, 100); covered += len(drawn(q, 'shade'))
    h = q.evaluate("()=>__dg.sounds()"); q.clock.resume()
    report(st(q)['passes'][0] >= 1 and 'pass' in h and covered == 0, 'pass: only its sound', 'passes %s, pass sound %s, screen covered in %d pictures' % (st(q)['passes'], 'pass' in h, covered))
def f_coins2(q):  # the 2 coins bonus
    get_jar(q, [{'k': 'coins2'}]); c = st(q)['players'][0]['coins']
    report(c == 2, 'jar: 2 coins', 'coins %d' % c)

def f_slot_rolls(q):  # owner 24 Nov: the wheels roll fast, then slow down and stop one after another (first, second, third), ticking as they pass and knocking as they stop;
    # owner 25 Nov: rolling wheels stop by their order among the rolling ones (one wheel spun alone stops when the first did); the tray shows the prize only after they stop
    pause_clock(q)
    table(q, bag=[[0, 4]] * 4, fast=False, coins=[3, 0], jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 0, 1, 0], slotFaces=FACES)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    def watch(wheels):  # game time from now until each of these wheels stops; the prize in the tray while any rolls
        stops, start, ms, at, early = {k: None for k in wheels}, None, 0, [], []  # times from the first frame any wheel rolls
        while ms < 5000 and None in stops.values():
            skip(q, 100); ms += 100
            ws = {d['n']: d for d in drawn(q, 'wheel')}
            if 0 in wheels and ws and ws[0]['rolling']: at.append(ws[0]['at'])
            if any(w['rolling'] for w in ws.values()): early += [d['faces'] for d in drawn(q, 'pic') if d['for'] == 'tray' and d['faces']]
            if start is None and any(w['rolling'] for w in ws.values()): start = ms
            for k in wheels:
                if k in ws and not ws[k]['rolling'] and stops[k] is None and start is not None: stops[k] = ms - start
        return [stops[k] for k in wheels], at, early
    stops, at, early = watch([0, 1, 2]); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='slot'}")
    tap(q, 'wheel-0'); tap(q, 'wheel-1'); tap(q, 'lever'); alone, _, early2 = watch([2]); settle(q); after = [d['faces'] for d in drawn(q, 'pic') if d['for'] == 'tray']
    q.clock.resume(); h = q.evaluate("()=>__dg.sounds()")
    steps = [b - a for a, b in zip(at, at[1:])]; slows = len(steps) >= 4 and steps[0] > 3 * steps[-1] > 0
    ok = None not in stops and stops[0] < stops[1] < stops[2] and stops[0] >= 500 and slows and h.count('roll') == 4 and h.count('stop') == 4 and alone[0] is not None and abs(alone[0] - stops[0]) <= 100 \
        and not early and not early2 and after == [['coin'] * 3]
    report(ok, 'slot: wheels roll, slow down, stop one by one; prize after', 'stops at %s ms, one wheel alone at %s; first wheel moves %s per 100 ms; roll sounds %d, stop sounds %d; prize while rolling %s, after %s' % (stops, alone, [round(x, 1) for x in steps], h.count('roll'), h.count('stop'), early + early2, after))
def f_slot_says_price(q):  # owner 24 Nov: "I can't even see what I pay", and then "no text; the slot machine should have none": price, prize and coins are pictures; owner 25 Nov: a blank face is an X
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 1, 3]); waiting(q, 'slot'); settle(q)
    pics = {d['for']: d for d in drawn(q, 'pic')}; texts = drawn(q, 'label'); blank = [f for f in drawn(q, 'drumface') if f['n'] == 2]
    ok = not texts and pics.get('lever', {}).get('coins') == 1 and pics.get('tray', {}).get('faces') == [] and pics.get('coins', {}).get('n') == 3 and [f['f'] for f in blank] == ['blank'] and drawn(q, 'nothing')
    report(ok, 'slot: price, prize and coins as pictures, no text', 'texts %s, pictures %s, third wheel %s, X drawn %d' % ([t['text'] for t in texts], pics, [f['f'] for f in blank], len(drawn(q, 'nothing'))))
def f_slot_three(q):  # owner 24 Nov: keep wheels, pull the lever to pay 1 coin and spin the others; owner 25 Nov: three of a kind wins what you see: 3 faces of 2 coins
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot')
    tap(q, 'wheel-0'); tap(q, 'wheel-1'); tap(q, 'lever'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); p = st(q)['players'][0]
    report(p['coins'] == 3 - 1 + 6, 'slot: respin costs a coin, three of a kind wins what you see', 'coins %d (3, paid 1, three faces of 2 coins)' % p['coins'])
def f_slot_two(q):  # owner 25 Nov (prototype): only three of a kind wins; you can stop at any time, and anything else gives nothing
    get_jar(q, [{'k': 'slot'}], coins=0, slots=[0, 2, 3]); waiting(q, 'slot'); g0 = st(q)['players'][0]['goods']
    tap(q, 'tray'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); p = st(q)['players'][0]
    report(p['coins'] == 0 and p['goods'] == g0 and p['jars'] == 0, 'slot: only three of a kind wins', 'coins %d, goods %s (before %s), jars %d' % (p['coins'], p['goods'], g0, p['jars']))
def f_slot_drums(q):  # owner 24 Nov (said twice): each wheel a shaded drum showing only the face it lands on, the wheels apart; tap a wheel to keep it (a clamp drops on it), tap again to free it;
    # a lever on the machine's side pays a coin and spins the others; tap the tray under the wheels to take the prizes; no circular arrow
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 1, 3]); waiting(q, 'slot'); settle(q)
    ws = sorted(drawn(q, 'wheel'), key=lambda d: d['n']); faces = [sum(1 for f in drawn(q, 'drumface') if f['n'] == k) for k in range(3)]
    apart = min(b['x'] - a['x'] - a['w'] for a, b in zip(ws, ws[1:])); boxes = {b: q.evaluate("(b)=>__dg.btnBox(b)", b) for b in ('lever', 'tray')}
    under = boxes['tray'] and boxes['tray']['y'] > max(w['y'] + w['h'] for w in ws); side = boxes['lever'] and boxes['lever']['x'] > max(w['x'] + w['w'] for w in ws)
    tap(q, 'wheel-1'); kept = st(q)['slot']['kept']; clamps = [c['n'] for c in drawn(q, 'clamp')]; tap(q, 'wheel-1'); freed = st(q)['slot']['kept']
    ok = len(ws) == 3 and all(w['shaded'] for w in ws) and faces == [1, 1, 1] and apart >= 24 and all(b and b['w'] >= 75 and b['h'] >= 75 for b in boxes.values()) and under and side \
        and kept == [False, True, False] and clamps == [1] and freed == [False] * 3 and not drawn(q, 'roundarrow')
    report(ok, 'slot: drums, clamps, a lever and a tray', 'wheels %d shaded %s, faces showing %s, %d px apart; lever %s at the side %s, tray %s under the wheels %s; kept %s with clamps %s, freed %s; circular arrow %s' % (len(ws), all(w['shaded'] for w in ws), faces, apart, boxes['lever'], side, boxes['tray'], under, kept, clamps, freed, bool(drawn(q, 'roundarrow'))))

def f_slot_faces(q):  # owner 25 Nov (prototype): each wheel has the same 4 faces, 2 coins, 2 jars, 2 of each material and a blank, each wheel in its own order
    seen, same = set(), True
    for seed in range(1, 13):  # the first spin is set to show three different places, so the machine waits for him (three of a kind ends it at once)
        table(q, seed=seed, bag=[[0, 4]] * 4, jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 1, 2]); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
        if not st(q)['slot']: continue
        f = st(q)['slot']['faces']; seen.add(tuple(map(tuple, f))); same = same and all(sorted(w) == ['blank', 'coin', 'jar', 'set'] for w in f)
    report(len(seen) > 6 and same, 'slot: the same 4 faces on every wheel, own order', '%d different machines in 12, every wheel coin, jar, materials, blank %s' % (len(seen), same))
def f_first_token(q):  # the first-player token comes from a jar
    get_jar(q, [{'k': 'first'}]); report(st(q)['first'] == 0, 'first: token comes to you', 'first %s' % st(q)['first'])

def inside_poly(pts, x, y):
    o = False
    for k, (ax, ay) in enumerate(pts):
        bx, by = pts[(k + 1) % len(pts)]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay): o = not o
    return o
def side_gap(pts, x, y):  # the shortest distance from (x, y) to the shape's sides
    def d(a, b): vx, vy = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((x - a[0]) * vx + (y - a[1]) * vy) / ((vx * vx + vy * vy) or 1))); return math.hypot(a[0] + t * vx - x, a[1] + t * vy - y)
    return min(d(pts[k], pts[(k + 1) % len(pts)]) for k in range(len(pts)))
def f_stickers(q):  # owner 27 Nov: "avatars for the 2 players ... like stickers ... the expressions should start from normal and react to the various game events; the active player should have a red/green glow"; "the avatars should react to the opponent's events too"
    pic = lambda o: [x['pic'] for x in drawn(q, 'avatar') if x['o'] == o][0]
    table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'empty'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); av = {x['o']: x for x in drawn(q, 'avatar')}
    animals = [av[i]['pic'].split('/')[1].rsplit('-', 1)[0] for i in (0, 1)]
    start = all(av[i]['pic'].startswith('avatars/') and av[i]['pic'].endswith('-neutral') for i in (0, 1)) and animals[0] != animals[1] and av[0]['lit'] and not av[1]['lit']
    drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); joined = pic(0)
    tap(q, 'jar-0'); run_until(q, "()=>__dg.drawn().some(d=>d.k==='avatar'&&d.o===0&&d.pic.endsWith('-sad'))", 4000); empty, other = pic(0), pic(1); q.clock.resume()
    table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'set'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); tap(q, 'jar-0'); run_until(q, "()=>__dg.sounds().includes('reveal')", 4000); settle(q); shown = pic(0); q.clock.resume()
    report(start and joined.endswith('-happy') and empty.endswith('-sad') and other.endswith('-happy') and shown.endswith('-happy'), 'stickers: two animals, neutral first, his turn glows, faces follow what happens, the other reacts too',
           'animals %s, start %s, after a connection %s, an empty jar %s (the other %s), a jar of materials %s' % (animals, start, joined, empty, other, shown))
def f_bee_corner(q):  # owner 27 Nov: "replace the star (who goes first next round) with a bee icon, that you will put in this corner" (his face stone's corner by the pool)
    get_jar(q, [{'k': 'first'}]); t = drawn(q, 'token'); face = [a for a in drawn(q, 'area') if a['o'] == 0 and a['kind'] == 'face'][0]['pts']
    b = t[0] if t else None; corner = face[1]
    ok = bool(b) and inside_poly(face, b['x'], b['y']) and side_gap(face, b['x'], b['y']) >= b['r'] and min(range(len(face)), key=lambda k: math.hypot(face[k][0] - b['x'], face[k][1] - b['y'])) == 1
    report(ok, 'bee: the first-player bee in his face stone\'s corner by the pool', 'bee %s, corner %s' % (b and (round(b['x']), round(b['y'])), [round(v) for v in corner]))
def f_ruby_leader(q):  # owner 27 Nov: "divide it in half, and the half of the winning player gets a ruby on top"
    res = {}
    for coins in ([3, 1], [1, 4], [2, 2]):
        table(q, coins=coins); r = drawn(q, 'ruby'); W = q.evaluate("()=>innerWidth"); res[tuple(coins)] = r[0] if r else None
    a, b, c = res[(3, 1)], res[(1, 4)], res[(2, 2)]
    ok = a and a['o'] == 0 and a['x'] + a['r'] <= W / 2 and b and b['o'] == 1 and b['x'] - b['r'] >= W / 2 and c is None
    report(bool(ok), 'ruby: on the half of the player with the most coins, none when level', 'kid ahead %s, PC ahead %s, level %s' % (a and (a['o'], round(a['x'])), b and (b['o'], round(b['x'])), c))
def f_ruby_centred(q):  # owner 27 Nov: the ruby at the centre of the triangle formed by the pool's bottom edge, the top of his coin stacks and his materials' side, the same on both sides
    seen = {}
    for o, coins in ((0, [3, 1]), (1, [1, 3])):
        table(q, coins=coins); r = [d for d in drawn(q, 'ruby') if d['o'] == o]; pts = [p for d in drawn(q, 'area') if d['o'] == o and d['kind'] == 'coins' for p in d['pts']]
        A = min(pts, key=lambda p: p[1]); C = max((p for p in pts if p[1] < max(y for _, y in pts) - 1), key=lambda p: p[1]); B = [A[0], C[1]]
        m = [(A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3]; seen[o] = (r and (round(r[0]['x']), round(r[0]['y'])), (round(m[0]), round(m[1])))
    ok = all(v[0] and abs(v[0][0] - v[1][0]) <= 2 and abs(v[0][1] - v[1][1]) <= 2 for v in seen.values())
    report(ok, 'ruby: at the centre of its triangle', 'per player (ruby, the triangle\'s centre) %s' % seen)
def f_extra_glow(q):  # owner 27 Nov: "the extra tile should have something like golden glow and sparkling small stars too, to draw attention to it"
    table(q, bag=[[0, 4]] * 4, jarQueue=[{'k': 'tile'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); market = drawn(q, 'extraglow')
    drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
    for _ in range(40):
        s = st(q)
        if s['wait'] and s['wait']['kind'] == 'place' and s['fromNowhere']: break
        skip(q, 300)
    g, h = drawn(q, 'extraglow'), held(q)
    report(not market and bool(g) and abs(g[0]['x'] - h[0]) < 2 and abs(g[0]['y'] - h[1]) < 2, 'extra tile: a golden glow and stars, a market tile none', 'market tile glow %s, extra tile glow %s at %s' % (bool(market), bool(g), h))

def f_sticker_box(q):  # owner 27 Nov: "make the avatars bigger and contain them in this box" (his red box on the face stone, beside the extra tile's place)
    table(q); tap(q, 'draft-0'); waiting(q, 'place'); ok, seen = True, []
    for i in (0, 1):
        a0 = [x for x in drawn(q, 'avatar') if x['o'] == i][0]; a, s = a0['box'], a0['shown']; face = [x for x in drawn(q, 'area') if x['o'] == i and x['kind'] == 'face'][0]['pts']
        corners = [(s['x'] + dx * s['w'] / 2, s['y'] + dy * s['h'] / 2) for dx in (-1, 1) for dy in (-1, 1)]
        within = all(a['x'] - 0.5 <= x <= a['x'] + a['w'] + 0.5 and a['y'] - 0.5 <= y <= a['y'] + a['h'] + 0.5 for x, y in corners) and all(inside_poly(face, x, y) for x, y in corners)
        big = max(s['w'] / a['w'], s['h'] / a['h']) > 0.99  # owner 27 Nov: always the biggest size, his turn or not
        ok = ok and within and big; seen.append((i, round(s['w']), round(s['h']), within, big))
    report(ok, 'stickers: as big as their box, inside it, on the face stone', seen)
def f_sticker_poke(q):  # owner 27 Nov: "make clicking the avatar make it take the happy stance for a fraction of a second"
    table(q, fast=False); tap(q, 'avatar-0'); now = [x['pic'] for x in drawn(q, 'avatar') if x['o'] == 0][0]; heard = q.evaluate("()=>__dg.sounds()")
    skip(q, 1000); later = [x['pic'] for x in drawn(q, 'avatar') if x['o'] == 0][0]; q.clock.resume()
    report(now.endswith('-happy') and later.endswith('-neutral') and 'poke' in heard, 'sticker: a tap makes it happy for a moment, with a sound', 'tapped %s, a second later %s, sound %s' % (now, later, 'poke' in heard))
def f_water_tap(q):  # owner 27 Nov: "make the click on the water make the splash sound and the splash animation, the architects game has them"
    table(q, fast=False); c = q.evaluate("()=>__dg.square(8, 8)"); q.mouse.click(c[0], c[1]); skip(q, 200)
    rings, drops, heard = [x for x in drawn(q, 'splashring') if x.get('round')], drawn(q, 'drops'), q.evaluate("()=>__dg.sounds()"); q.clock.resume()
    report(bool(rings) and 'watertap' in heard, 'water: a tap splashes, rings and drops, with the architects game\'s water sound', 'rings %d, sound %s' % (len(rings), 'watertap' in heard))
def f_ruby_moves(q):  # owner 27 Nov: "when it's equal coins dissolve it in many particles, dissolve it, and the opposite when it appears again or for the first time; add proper sound hooks"
    table(q, coins=[1, 0]); a, h = drawn(q, 'ruby'), q.evaluate("()=>__dg.sounds()"); table(q, coins=[0, 2]); b = drawn(q, 'ruby')
    report(bool(a) and a[0]['o'] == 0 and bool(b) and b[0]['o'] == 1, 'ruby: on the leader\'s half', 'kid ahead %s, PC ahead %s' % (a and a[0]['o'], b and b[0]['o']))
    table(q, fast=False, coins=[1, 0], bag=[[0, 4]] * 4, jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 1, 2], slotFaces=FACES); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); tap(q, 'jar-0'); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='slot'}", 8000); tap(q, 'lever')
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='slot'}", 8000); tap(q, 'tray'); run_until(q, "()=>__dg.sounds().includes('rubyout')", 8000); skip(q, 2000)
    gone, h = drawn(q, 'ruby'), q.evaluate("()=>__dg.sounds()"); q.clock.resume()
    report(not gone and 'rubyout' in h, 'ruby: dissolves when the coins are level, with its sound', 'ruby %s, sound %s' % (gone, 'rubyout' in h))
    table(q, fast=False, coins=[1, 1], bag=[[0, 4]] * 4, jarQueue=[COIN] * 9); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); tap(q, 'jar-0')
    states = []
    for _ in range(80):
        skip(q, 50); r = drawn(q, 'ruby'); states.append(r[0] if r else None)
        if r and r[0].get('whole'): break
    formed = any(x and x.get('fading') == 'in' and not x['whole'] for x in states) and bool(states[-1]) and states[-1]['whole']; h = q.evaluate("()=>__dg.sounds()"); q.clock.resume()
    report(formed and 'rubyin' in h, 'ruby: forms from its bits, with its sound, when a player takes the lead', '%d steps of 50 ms, formed %s, sound %s' % (len(states), formed, 'rubyin' in h))
def f_ruby_flies(q):  # owner 27 Nov: "the ruby changed places by moving ... slow, faster, slow"; "move the ruby in this area" (his bottom stone beside his materials, under the pool)
    table(q, fast=False, coins=[1, 2], bag=[[0, 4]] * 4, jarQueue=[{'k': 'coins2'}] + [COIN] * 8); start = drawn(q, 'ruby')
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); tap(q, 'jar-0')
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='ruby'&&d.moving)", 8000); xs = []
    for _ in range(60):
        r = drawn(q, 'ruby')[0]; xs.append(r['x'])
        if not r.get('moving'): break
        skip(q, 40)
    q.clock.resume(); steps = [abs(b - a) for a, b in zip(xs, xs[1:])]; n = len(steps); W = q.evaluate("()=>innerWidth")
    eased = n >= 6 and max(steps[n // 3: 2 * n // 3]) > 2 * max(steps[0], steps[-1])
    report(bool(start) and start[0]['o'] == 1 and start[0]['x'] > W / 2 and xs[-1] < W / 2 and eased, 'ruby: flies from player to player, slow, fast, slow', 'from %s to %s in %d steps, first %.0f, middle %.0f, last %.0f px' % (start and round(start[0]['x']), round(xs[-1]), n, steps[0] if steps else 0, max(steps[n // 3: 2 * n // 3]) if n >= 3 else 0, steps[-1] if steps else 0))
def f_pile_turn(q):  # owner 27 Nov: "rotate deck the other way so it is like the first 2 drawn slots"
    table(q); tap(q, 'draft-0'); waiting(q, 'place'); pile = drawn(q, 'pile')[0]; tiles = drawn(q, 'tile')
    at = lambda k: q.evaluate("(k)=>__dg.slot(k)", k); turns = [[t['r'] for t in tiles if t.get('x') is not None and abs(t['x'] - at(k)[0]) < 2 and abs(t['y'] - at(k)[1]) < 2] for k in (1,)]
    report(bool(turns[0]) and all(r == pile['turn'] for r in turns[0]), 'pile: turned as the market\'s first two tiles', 'pile %s, second market tile %s' % (pile['turn'], turns))

def f_tile_excites(q):  # owner 27 Nov: an extra tile from a jar makes him excited (it made him happy)
    pause_clock(q); table(q, bag=[[0, 4]] * 4, fast=False, jarQueue=[{'k': 'tile'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.sounds().some(x=>(x.n||x)==='reveal')", 3000); settle(q); face = [d['pic'] for d in drawn(q, 'avatar') if d['o'] == 0]; q.clock.resume()
    report(bool(face) and face[0].endswith('-excited'), 'faces: an extra tile makes him excited', 'his face %s' % face)
def f_free_tile(q):  # owner 25 Nov (prototype): a jar's free tile is a random tile, no wild tile; its colours are not shown until it lies beside the market; it always fits; it is his ("marked as yours", 24 Nov)
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'tile'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='flight'&&d.look==='tile')", 3000); flying = [d['cs'] for d in drawn(q, 'tile') if d['id'] is None]
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='place'}", 3000); h = held(q); m = drawn(q, 'market')[0]; shown = [d['cs'] for d in drawn(q, 'tile') if d['id'] == 'held']
    mark = [x['o'] for x in drawn(q, 'heldmark')]; fits = len(st(q)['spots']) > 0; q.clock.resume(); n0 = tile_count(q, 0); drag_to(q, best_spot(q))
    ok = flying == [None] and len(shown) == 1 and shown[0] and len(shown[0]) == 2 and m['x'] + m['w'] < h[0] and mark == [0] and fits and tile_count(q, 0) == n0 + 1
    report(ok, 'tile: random, colours hidden until beside the market, fits', 'flying %s, beside the market %s with colours %s, his %s, fits %s, placed %s' % (flying, m['x'] + m['w'] < h[0], shown, mark, fits, tile_count(q, 0) == n0 + 1))

def f_screen_sizes(q):  # owner 25 Nov (design 3, the new look): the board is sea, 16 x 16 squares seen in true isometric view (a diamond 1.73 times as wide as high), as tall as the screen
    # under the market band allows; a tile the same size everywhere; tiles he can't take: a light grey wash, their pictures clear (owner 25 Nov, prototype)
    table(q, bag=[[0, 3], [3, 3], [0, 4], [0, 4]]); H = q.evaluate("()=>innerHeight"); b = drawn(q, 'boardarea')[0]; band = drawn(q, 'band')[0]
    a, c = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hw, hh = c[0] - a[0], c[1] - a[1]
    t = {d['id']: d for d in drawn(q, 'tile') if d['id'] in ('draft-0', 'draft-1')}
    half = lambda k: q.evaluate("([k,dx,dy])=>{const [x,y]=__dg.slot(k); return __dg.pixel(x+dx,y+dy)}", [k, hw / 2, hh / 2 + hh * 0.6])[:3]  # the second half's front, where its ground shows
    taken, grey = half(0), half(1)  # the same land picture ([0, 3] and [3, 3]): one as it is, one greyed
    clear = grey != taken and all(abs(x - y) <= 40 for x, y in zip(grey, taken))
    shape = b['cols'] == b['rows'] == 16 and abs(b['w'] / b['h'] - 3 ** 0.5) < 0.01 and abs(hw / hh - 3 ** 0.5) < 0.01 and abs(b['w'] - 32 * hw) < 1
    tall = band['y'] == 0 and abs(b['y'] - (band['y'] + band['h'])) <= 1 and H - 16 <= b['y'] + b['h'] <= H
    one = abs(t['draft-0']['w'] - 3 * hw) < 1 and abs(t['draft-0']['h'] - 3 * hh) < 1
    ok = shape and tall and one and t['draft-1']['look'] == 'grey' and t['draft-0']['look'] is None and clear
    report(ok, 'screen: sea diamond, as tall as allowed, one tile size, light grey', 'board %s squares, %.0f x %.0f px (%.2f), top %.0f under a band of %.0f, bottom %.0f of %d; square %.1f x %.1f; market tile %.0f x %.0f; greyed %s vs %s' % (
        (b['cols'], b['rows']), b['w'], b['h'], b['w'] / b['h'], b['y'], band['h'], b['y'] + b['h'], H, hw, hh, t['draft-0']['w'], t['draft-0']['h'], grey, taken))
def f_land_pictures(q):  # owner 25 Nov (design 3, the new look): each land is a picture in the same isometric view (wheat field, pomegranate orchard, vineyard, forest, mountain, town);
    # land exists only where tiles are placed, the rest is sea from his water pack; each land's material is its own picture (grain, pomegranates, grapes, timber, rubies, little statues)
    table(q, bag=[[0, 4]] * 4, tiles=[[4, 11, 0, 2, 3, 0], [4, 12, 0, 4, 5, 0]], goods=[[1] * 6, [0] * 6])
    lands, mats = ['wheat', 'pomegranate', 'vineyard', 'forest', 'mountain', 'town'], ['grain', 'pomegranate', 'grapes', 'timber', 'ruby', 'statue']
    sq = drawn(q, 'square'); g = [x for x in drawn(q, 'good') if x['o'] == 0]; sea = drawn(q, 'sea')
    pics = all(x['pic'] == 'lands/' + lands[x['c']] and x['ready'] for x in sq) and {x['c'] for x in sq} == set(range(6))
    goods = sorted((x['c'], x['pic']) for x in g) == [(c, 'materials/' + m) for c, m in enumerate(mats)] and all(x['ready'] for x in g)
    px = lambda x, y: q.evaluate("([x,y])=>{const p=__dg.square(x,y); return __dg.pixel(p[0],p[1]+3)}", [x, y])[:3]
    wet = lambda c: c[2] > c[0] + 30  # the sea is blue; every land picture is warmer
    land_px, sea_px = [px(x, y) for x, y in ((4, 11), (5, 12), (4, 10))], [px(x, y) for x, y in ((8, 8), (1, 1), (14, 14))]
    ok = pics and goods and bool(sea) and sea[0]['ready'] and not any(wet(c) for c in land_px) and all(wet(c) for c in sea_px)
    report(ok, 'look: land pictures on a sea, material pictures', 'squares %s, materials %s, sea %s, land pixels %s, sea pixels %s' % (
        sorted({(x['c'], x['pic'], x['ready']) for x in sq}), sorted((x['c'], x['pic']) for x in g), sea, land_px, sea_px))
def f_player_areas(q):  # owner 25 Nov (design 3, the new look): each player's area is the two triangles beside the board on his side, joined at the board's side corner (green left, red right);
    # owner 25 Nov: the 4 central tips (each triangle's thin end at the screen's middle) are grey and hold nothing, each cut where it is 3 material places thick;
    # materials 1.5 times their old size (12.4 px on this screen), a row of 5 per colour from the top, beside the screen edge (owner 25 Nov: rows, not columns); his face beside them;
    # coins fill the bottom triangle in rows from the bottom up, each as long as the triangle is wide there, at most 8 a row; owner 24 Nov: everything spaced apart, no jar outlines; the pile a stack of tiles
    table(q, bag=[[0, 4]] * 12, goods=[[4, 4, 4, 2, 1, 0], [1, 1, 0, 0, 0, 0]], coins=[20, 3]); W, H = q.evaluate("()=>[innerWidth, innerHeight]"); dm = diamond(q); band = drawn(q, 'band')[0]
    d = q.evaluate("()=>__dg.drawn()"); of = lambda k, o: [x for x in d if x['k'] == k and x.get('o') == o]; pile = [x for x in d if x['k'] == 'pile']
    side = lambda o, x: x < W / 2 if o == 0 else x > W / 2; out = {}
    for o in (0, 1):
        face, places, goods, coins = of('avatar', o)[0], of('place', o), of('good', o), of('coin', o)
        rws = {c: {round(x['y']) for x in places if x['c'] == c} for c in range(6)}
        column = all(len(v) == 1 for v in rws.values()) and len({min(v) for v in rws.values()}) == 6 and all(len({round(x['x']) for x in places if x['c'] == c}) == 5 for c in range(6))
        near_edge = (min(x['x'] - x['r'] for x in places) if o == 0 else W - max(x['x'] + x['r'] for x in places)) <= 24
        from_top = min(x['y'] - x['r'] for x in places) - (band['y'] + band['h']) <= 16
        inner = max(places, key=lambda x: abs(x['x'] - (0 if o == 0 else W)) + x['y'])  # the bottom row's inner place, nearest the board
        big = min(x['r'] for x in places) >= 1.5 * 12.4 - 0.2 or not off_board(dm, inner['x'], inner['y'], inner['r'] + 4)  # owner 25 Nov: rows: as big as fits above the board
        on_place = len(goods) == sum(st(q)['players'][o]['goods']) and all(any(abs(g['x'] - x['x']) < 1 and abs(g['y'] - x['y']) < 1 and g['c'] == x['c'] for x in places) for g in goods)
        tips, rp = of('tip', o), min(abs(a['x'] - b['x']) for a in places for b in places if a['c'] == b['c'] and a is not b)
        def tip_ok(t):  # touches the middle line; its side away from the middle is 3 material places long; grey where drawn
            far = max(abs(x - W / 2) for x, _ in t['pts']); side_ys = [y for x, y in t['pts'] if abs(abs(x - W / 2) - far) < 0.5]
            mx, my = sum(x for x, _ in t['pts']) / len(t['pts']), sum(y for _, y in t['pts']) / len(t['pts']); px = q.evaluate("([x,y])=>__dg.pixel(x,y)", [mx, my])[:3]
            return min(abs(x - W / 2) for x, _ in t['pts']) < 0.5 and abs(max(side_ys) - min(side_ys) - 3 * rp) < 1 and max(px) - min(px) <= 6 and 90 < px[0] < 220
        def inside(t, x, y, r):  # a round thing reaches into the tip (convex, points in order)
            p = t['pts']; edges = list(zip(p, p[1:] + p[:1])); sgn = lambda a, b: (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
            def dist(a, b):  # from (x, y) to the segment a-b
                dx, dy = b[0] - a[0], b[1] - a[1]; u = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / max(1e-9, dx * dx + dy * dy)))
                return ((x - a[0] - u * dx) ** 2 + (y - a[1] - u * dy) ** 2) ** 0.5
            ins = all(sgn(a, b) >= 0 for a, b in edges) or all(sgn(a, b) <= 0 for a, b in edges)
            return ins or min(dist(a, b) for a, b in edges) < r
        things = places + coins + [face] + of('token', o)
        corner = side(o, face['x']) and len(tips) == 2 and all(tip_ok(t) for t in tips) and not any(inside(t, x['x'], x['y'], x['r']) for t in tips for x in things)
        rows = sorted({round(c['y']) for c in coins}, reverse=True); per = [sorted(c['x'] for c in coins if round(c['y']) == y) for y in rows]
        step = min((b - a for r in per for a, b in zip(r, r[1:])), default=0); r0 = coins[0]['r'] if coins else 0
        nxt = lambda r: (r[-1] + step) if o == 0 else (r[0] - step)
        full = all(len(r) == 8 or not off_board(dm, nxt(r), y, r0) or any(inside(t, nxt(r), y, r0) for t in tips) for r, y in zip(per[:-1], rows))  # a row short of 8 meets the board or a tip
        coins_ok = bool(coins) and max(len(r) for r in per) <= 8 and all(len(a) >= len(b) for a, b in zip(per, per[1:])) and H - max(c['y'] + c['r'] for c in coins) <= 24 and full
        clear = all(off_board(dm, x['x'], x['y'], x['r']) and side(o, x['x']) for x in places + coins + [face])
        apart = min_gap(places + coins + [face]) >= 3
        out[o] = dict(column=column, edge=near_edge, top=from_top, big=big, on_place=on_place, corner=corner, coins=coins_ok, off_board=clear, apart=apart, rows=[len(r) for r in per])
    ok = all(all(v for k, v in x.items() if k != 'rows') for x in out.values()) and not [x for x in d if x['k'] == 'jargroup'] and len(pile) == 1 and pile[0]['layers'] == 8
    report(ok, 'areas: grey empty tips, material rows, coin rows', '%s, pile %s' % (out, pile))
def f_no_sets(q):  # owner 25 Nov (prototype): no wild tiles, no sets to tap: one of each colour lights nothing; only the market's tiles can be tapped
    table(q, bag=[[0, 4]] * 4, goods=[[2] * 6, [0] * 6]); b = q.evaluate("()=>__dg.buttons()"); marks = drawn(q, 'setrow') + drawn(q, 'setsign')
    b = [x for x in b if not x.startswith('avatar-')]  # owner 27 Nov: the stickers answer a tap
    report(sorted(b) == ['draft-%d' % k for k in range(4)] and not marks, 'no sets, no wild tile', 'buttons %s, set marks %d' % (b, len(marks)))
def f_another_jar(q):  # another jar, which you open yourself
    get_jar(q, [{'k': 'jar'}, {'k': 'coins2'}]); waiting(q, 'jar'); c0 = st(q)['players'][0]['coins']
    tap(q, 'jar-0'); c1 = st(q)['players'][0]['coins']
    report(c1 == c0 + 2, 'jar: another jar to open', 'coins %d -> %d' % (c0, c1))

def f_free_set(q):  # a free set: one of each of the 5 goods (on top of the placed tile's own 2, owner 24 Nov)
    get_jar(q, [{'k': 'set'}]); g = st(q)['players'][0]['goods']
    report(g == [3, 1, 1, 1, 1, 1], 'set: one of each good', str(g))

def f_sticker_glow(q):  # owner 27 Nov: the turn's sticker glow: less neon ("radioactive"), a slower pulse, a more solid core, a little bigger; later: bigger again, and more vivid, just not neon; then: still faded, dull: more vivid
    pause_clock(q); table(q, fast=False); seen = []
    for _ in range(60): skip(q, 100); settle(q); g = [d for d in drawn(q, 'glow') if d['o'] == 0]; seen.append(g[0] if g else None)
    q.clock.resume(); a = [x['a'] for x in seen if x]
    peaks = [k for k in range(1, len(a) - 1) if a[k] >= a[k - 1] and a[k] > a[k + 1]]; period = (peaks[1] - peaks[0]) * 100 if len(peaks) > 1 else 6000
    def sat(col): r, g_, b = (int(col[k:k + 2], 16) / 255 for k in (1, 3, 5)); mx, mn = max(r, g_, b), min(r, g_, b); return (mx - mn) / (1 - abs(mx + mn - 1)) if mx != mn else 0
    light = lambda col: (max(int(col[k:k + 2], 16) for k in (1, 3, 5)) + min(int(col[k:k + 2], 16) for k in (1, 3, 5))) / 510
    x = next((x for x in seen if x), {'col': '#000000', 'core': 0, 'g': 0, 'ui': 1})
    ok = all(seen) and period >= 3000 and 0.84 <= sat(x['col']) <= 0.95 and light(x['col']) <= 0.55 and x['core'] >= 0.25 * x['g'] and x['g'] >= 30 * x['ui']
    report(ok, 'faces: the turn glow is vivid not neon, slow, solid, bigger', 'pulse every %d ms, colour %s (saturation %.2f, lightness %.2f), solid core %.1f of a glow %.1f (%.1f at a 1080 screen)' % (period, x['col'], sat(x['col']), light(x['col']), x['core'], x['g'], x['g'] / x['ui']))
def f_stockpile(q):  # owner 27 Nov: materials stockpile: the side places' gaps to the screen edge and to the stone's edge are equal, on both sides; the grapes and stone columns swapped
    # (wheat, sheep, stone, forest, grapes, town); later: both players' columns in the same order from left to right, not mirrored; the statue icon 7.5% wider than the others, filling its place like them
    table(q); settle(q); flat = {d['o']: d for d in drawn(q, 'goodsflat')}; pl = drawn(q, 'place'); icons = drawn(q, 'icon'); seen = {}
    for o in (0, 1):
        mine = [d for d in pl if d['o'] == o]; lo = min(d['x'] - d['r'] for d in mine); hi = max(d['x'] + d['r'] for d in mine); f = flat.get(o, {'x0': 0, 'x1': 0})
        order = [c for c, _ in sorted({d['c']: d['x'] for d in mine}.items(), key=lambda kv: kv[1])]
        w = {d['c']: d['w'] for d in icons if d['o'] == o}
        seen[o] = (round(lo - f['x0']), round(f['x1'] - hi), order, round(w.get(5, 0) / w.get(0, 1), 3))
    ok = all(abs(v[0] - v[1]) <= 1 and v[0] > 0 and v[2] == [0, 1, 4, 3, 2, 5] and abs(v[3] - 1.075) < 0.005 for v in seen.values())
    report(ok, 'materials: even gaps, grapes and stone swapped, same order both sides, statue wider', 'per player (gap at the left, gap at the right, columns from left to right, statue icon to others) %s' % seen)
def f_buttons_press(q):  # owner 27 Nov: the buttons (3D stones) are tappable with a pressed state: pressed, a button loses its shadow and goes down; let go, it comes back up
    table(q); seen = {}
    for kind in ('gear', 'exit'):
        b = [d for d in drawn(q, 'button') if d['kind'] == kind][0]; q.mouse.move(b['x'], b['y']); q.mouse.down(); settle(q)
        d = [d for d in drawn(q, 'button') if d['kind'] == kind][0]; q.mouse.up(); settle(q); u = [d for d in drawn(q, 'button') if d['kind'] == kind][0]
        seen[kind] = (b['shadow'], round(d['y'] - b['y'], 1), d['shadow'], round(u['y'] - b['y'], 1), u['shadow'])
    ok = all(v[0] and v[1] > 2 and not v[2] and v[3] == 0 and v[4] for v in seen.values())
    report(ok, 'buttons: pressed, a button goes down and loses its shadow', 'per button (shadow up, how far down when pressed, shadow pressed, after letting go, shadow) %s' % seen)
def f_pool_walls(q):  # owner 27 Nov: the pool's walls lower: from the water to their top as high as a tile's ground (shows over the water)
    table(q); settle(q); w = drawn(q, 'poolwall'); g = {round(d['shows'], 1) for d in drawn(q, 'square')}
    ok = bool(w) and len(g) == 1 and abs(w[0]['h'] - g.pop()) < 0.5 if w and g else False
    report(ok, 'pool: walls as high as a tile\'s ground', 'wall %s, tile ground over the water %s' % ([round(d['h'], 1) for d in w], sorted({round(d['shows'], 1) for d in drawn(q, 'square')})))
def f_stickers_face(q):  # owner 27 Nov: the two animals face each other; later: the left player's sticker is the picture as on the sheet, the right player's is mirrored, in every face
    seen = {}
    for a, b in (('cat', 'dog'), ('frog', 'cat'), ('bunny', 'chick'), ('hamster', 'frog')):
        table(q, animals=[a, b]); settle(q); s = {d['o']: d.get('mirrored') for d in drawn(q, 'avatar')}; seen[a + '/' + b] = (s.get(0), s.get(1))
    report(all(v == (False, True) for v in seen.values()), 'faces: left sticker as on the sheet, right one mirrored', 'per pair (left mirrored, right mirrored) %s' % seen)
def f_sticker_rests(q):  # owner 27 Nov: resting, a sticker stretches a little up and down, its feet still: only the part above them moves
    pause_clock(q); table(q, fast=False); seen = []
    for _ in range(30): skip(q, 100); settle(q); d = [d['shown'] for d in drawn(q, 'avatar') if d['o'] == 1 and d['pic'].endswith('-neutral')]; seen.append(d[0] if d else None)
    q.clock.resume(); hs = [x['h'] for x in seen if x]; feet = [x['y'] + x['h'] / 2 for x in seen if x]
    ok = len(hs) == len(seen) and (max(hs) - min(hs)) / max(hs) >= 0.02 and max(feet) - min(feet) < 0.5
    report(ok, 'faces: resting, the sticker stretches, feet still', 'heights %.1f to %.1f, feet moved %.2f px, resting frames %d of %d' % (min(hs or [0]), max(hs or [0]), (max(feet) - min(feet)) if feet else -1, len(hs), len(seen)))
def f_button_hole_bevel(q):  # owner 27 Nov: a pressed button's top is level with its slab, so its bevel lies below the slab's surface, like a hole's: lit the other way round
    # (up: its left bevel lit by the sun at the top left, its right one dark; pressed: its left bevel dark, its right one lit)
    table(q); look = "([x,y])=>{const c=document.getElementById('under'),d=c.width/innerWidth,p=c.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;return p[0]+p[1]+p[2]}"
    def sides():
        b = [d for d in drawn(q, 'button') if d['kind'] == 'gear'][0]; e = b['edge'] - 3 * b['ui']
        return q.evaluate(look, [b['x'] - e, b['y']]) - q.evaluate(look, [b['x'] + e, b['y']])
    up = sides(); b = [d for d in drawn(q, 'button') if d['kind'] == 'gear'][0]; q.mouse.move(b['x'], b['y']); q.mouse.down(); settle(q); down = sides(); q.mouse.up(); settle(q)
    report(up > 30 and down < -30, 'buttons: pressed, the bevel is lit like a hole\'s', 'left bevel minus right bevel (brightness): up %d, pressed %d' % (up, down))
def f_button_groove(q):  # owner 27 Nov: a pressed button looked like one stone with the slab: a groove runs round it, as if it is slotted into the slab
    table(q); look = "([x,y])=>{const c=document.getElementById('under'),d=c.width/innerWidth,p=c.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;return p[0]+p[1]+p[2]}"
    b = [d for d in drawn(q, 'button') if d['kind'] == 'gear'][0]; q.mouse.move(b['x'], b['y']); q.mouse.down(); settle(q); b = [d for d in drawn(q, 'button') if d['kind'] == 'gear'][0]; u = b['ui']; seen = {}
    for name, (dx, dy) in {'left': (-1, 0), 'right': (1, 0), 'top': (0, -1), 'bottom': (0, 1)}.items():
        at = lambda k: [b['x'] + dx * (b['edge'] + k * u), b['y'] + dy * (b['edge'] + k * u)]
        seen[name] = (q.evaluate(look, at(1)), q.evaluate(look, at(14)))
    q.mouse.up(); settle(q)
    report(all(g < s - 60 for g, s in seen.values()), 'buttons: pressed, a groove round it in the slab', 'per side (groove, slab beyond it) %s' % seen)
def f_starts_face(q):  # owner 25 Nov: the start tiles face each other: the PC's is the kid's turned half a turn around the board's centre (each colour on its turned square)
    table(q, bag=[[3, 3]] * 4); D = [[1, 0], [0, 1], [-1, 0], [0, -1]]
    sq = lambda t: {(t[0], t[1]): t[3], (t[0] + D[t[2]][0], t[1] + D[t[2]][1]): t[4]}
    kid, pc = [sq(t) for o in (0, 1) for t in st(q)['tiles'] if t[5] == o]
    turned = {(15 - x, 15 - y): c for (x, y), c in kid.items()}
    report(pc == turned, 'starts: the tiles face each other', 'kid %s, pc %s' % (kid, pc))
def f_scales(q):  # owner 25 Nov: "make sure your ui is adoptable to all laptop and pc screen sizes": what has its own size (faces, the hand, the slot machine) grows with the board, and stays on screen
    seen, small_hh = [], 0
    for w, h in ((1366, 768), (1920, 1080), (2560, 1440)):
        q.set_viewport_size({'width': w, 'height': h}); get_jar(q, [{'k': 'slot'}], coins=3); waiting(q, 'slot'); settle(q)
        a, c = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hh = c[1] - a[1]
        face = [x for x in drawn(q, 'avatar') if x['o'] == 0][0]; m = drawn(q, 'machine')[0]; hand = drawn(q, 'hand')[0]; lever = q.evaluate("()=>__dg.btn('lever')")
        inside = m['x'] >= 0 and m['y'] >= 0 and m['x'] + m['w'] <= w and m['y'] + m['h'] <= h and m['x'] <= lever[0] <= m['x'] + m['w'] * 1.3 and m['y'] <= lever[1] <= m['y'] + m['h']
        fills = round(max(face['shown']['w'] / face['box']['w'], face['shown']['h'] / face['box']['h']), 2)  # owner 27 Nov: the sticker is as big as its box on the face stone, whatever the screen
        seen.append((fills, round(m['w'] / hh, 2), round(hand['z'] / hh, 2), inside)); small_hh = small_hh if seen[1:] else hh
    q.set_viewport_size({'width': 1280, 'height': 800})
    same = all(abs(x[k] - seen[1][k]) <= 0.02 * seen[1][k] for x in seen[1:] for k in (1, 2)) and abs(seen[0][2] - seen[1][2]) <= 0.02 * seen[1][2] and all(x[0] >= 0.99 for x in seen)
    small = seen[0][1] * small_hh >= 540 - 1  # on a small screen the machine keeps its made size (its buttons stay big enough to touch), as long as it fits
    report(same and small and all(x[3] for x in seen), 'scales: sizes grow with the screen, on screen', 'per size (the sticker filling its box, machine width and hand in half-square heights, on screen) %s' % seen)
def f_thick_land(q):  # owner 25 Nov: land squares are blocks with some thickness: walls of earth under the top's front edges, the sea below them
    table(q, bag=[[0, 4]] * 4); a, c = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hh = c[1] - a[1]
    x, y = q.evaluate("()=>__dg.square(5,10)"); px = lambda dy: q.evaluate("([x,y])=>__dg.pixel(x,y)", [x, y + hh + dy * hh])[:3]  # under the start tile's front corner
    wet = lambda p: p[2] > p[0] + 30; wall, sea = px(0.4), px(1.3)
    report(not wet(wall) and wet(sea), 'land: blocks with walls over the sea', 'under the front corner: %s at 0.4 of a half square, %s at 1.3' % (wall, sea))
def f_moving_water(q):  # owner 25 Nov: the water moves (ripples drift over it, foam around the land); the land stays still (test pages keep the water still unless asked: it costs the run)
    pause_clock(q); table(q, fast=False, stillWater=False, bag=[[0, 4]] * 4); spot = q.evaluate("()=>__dg.square(8,2)"); land = q.evaluate("()=>__dg.square(4,10)")
    look = lambda: [q.evaluate("([x,y])=>__dg.pixel(x,y)", [p[0] + dx, p[1] + dy])[:3] for p in (spot, land) for dx in (-9, -3, 3, 9) for dy in (-4, 4)]
    a = look(); skip(q, 1500); b = look(); q.clock.resume()
    moved = sum(1 for k in range(8) if a[k] != b[k]); still = all(a[k] == b[k] for k in range(8, 16))
    report(moved >= 4 and still and drawn(q, 'foam'), 'water: it moves, the land does not', 'sea pixels changed %d of 8, land unchanged %s, foam %s' % (moved, still, bool(drawn(q, 'foam'))))
def f_borders(q):  # each player's land has a border all around: green for the kid, red for the PC; a tile's two halves meet with no gap (no sea between them)
    table(q, bag=[[0, 4]] * 4); b = drawn(q, 'border'); kid = sum(1 for x in b if x['o'] == 0); pc = sum(1 for x in b if x['o'] == 1)
    seam = q.evaluate("()=>__dg.edge(4,10,0)"); mid = q.evaluate("(p)=>__dg.pixel(p[0],p[1]+4)", seam)[:3]
    ok = kid == 6 and pc == 6 and not mid[2] > mid[0] + 30
    report(ok, 'borders: all around each land, halves joined', 'kid edges %d, pc edges %d, seam %s' % (kid, pc, mid))
MAIN_SEED, MAIN_JARS = 3, ['coins', 'empty', 'slot', 'first', 'jar', 'tile', 'coins2', 'set']  # the main game's fixed pile (made by this seed) and the jar contents queued, in order
def f_main_game(q):  # owner 24 Nov: one main test plays a whole game with a fixed pile and fixed jar contents, so every situation happens in order; at each situation it checks that situation's rules, and after every move what he sees adds up
    out = q.evaluate("""async ([seed, kinds]) => {
      const cv = document.querySelector('canvas'), errs = [], did = {}, err = m => errs.push(m);
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { if (!p) { err('nothing to tap at ' + JSON.stringify(__dg.state().wait)); return; } __dg.render(); ev('pointerdown', p); ev('pointerup', p); await tick(); };
      const drag = async (a, b) => { if (!a || !b) { err('nothing to drag at ' + JSON.stringify(__dg.state().wait)); return; } __dg.render(); ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = kind => __dg.drawn().filter(d => d.k === kind), btn = id => { __dg.render(); return __dg.btn(id); };  // buttons are where the last picture put them: draw first
      const sum = a => a.reduce((x, y) => x + y, 0), DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
      const lit = starts => { const sq2 = seen('square'), on = (x, y) => sq2.find(d => d.x === x && d.y === y), done = new Set(), todo = starts.slice(); while (todo.length) { const [x, y] = todo.shift(), a = on(x, y); if (!a || done.has(x + ',' + y)) continue; done.add(x + ',' + y); [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const b = on(x + dx, y + dy); if (b && b.c === a.c) todo.push([x + dx, y + dy]); }); } return done.size; };  // the squares the connections light, on the board shown (owner 25 Nov)
      __dg.restart({ seed, fast: true, jarQueue: kinds.map(k => ({ k })), slotQueue: [0, 0, 1, 0] }); await tick();
      { const s = __dg.state(), starts = s.tiles.map(t => t.slice(0, 5).join()).sort();  // the start: the same start tile for both, the two most common colours, at the centres of the board's halves; nobody has the token; the kid picks first
        if (starts.join('|') !== '11,5,2,0,1|4,10,0,0,1' || s.draft.length !== 4 || !s.wait || s.wait.kind !== 'pick' || s.wait.who !== 0 || s.first !== null) err('start: ' + JSON.stringify([starts, s.wait, s.first])); }
      let putBack = false, picked = -1, prev = __dg.state(), afterPass = 0; const total = prev.left;  // every tile of the pile
      for (let step = 0; ; step++) {
        await tick(); const s = __dg.state(), w = s.wait; __dg.render();
        if (step > 4000 || errs.length > 5) { err('stuck at ' + JSON.stringify(w)); break; }
        for (const o of [0, 1]) if (seen('coin').filter(d => d.o === o).length + seen('endcoin').filter(d => d.o === o).length !== s.players[o].coins) err('round ' + s.round + ': coins shown for ' + o + ' differ');  // in his area, or at the end in his pile
        if (s.over) {  // the end: no tile left can be placed by either player (none thrown); most coins wins, his star shown
          const [a, b] = s.players.map(p => p.coins), win = a > b ? 0 : b > a ? 1 : -1, star = seen('winner');
          if (s.leftFits) err('end: a tile left still fits');
          if (s.winner !== win || (win >= 0 && (star.length !== 1 || star[0].o !== win))) err('end: winner ' + s.winner + ' for coins ' + [a, b]);
          did.end = true; break;
        }
        if (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left !== total) err('a tile was thrown away: board, hand and left make ' + (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left));  // no tile is ever thrown: not when he passes, not at the round's end (the tile in hand counts)
        for (const o of [0, 1]) for (let c = 0; c < 6; c++) if (seen('good').filter(d => d.o === o && d.c === c).length !== s.players[o].goods[c]) err('round ' + s.round + ': goods shown differ for ' + o);
        if (__dg.sounds().includes('dissolve')) err('round ' + s.round + ': goods were lost');  // goods carry over between rounds (owner 24 Nov)
        if (s.passes[0] > prev.passes[0]) { did.pass = true; afterPass = prev.round === s.round && s.phase === 'round' ? { round: s.round, got: prev.players[1].got, passes: prev.passes[1] } : 0; }  // a pass seen across a round's end is not checked: the new round may start with him  // nothing fits him: his turn passes, no tile is thrown
        if (afterPass && w && w.who === 0 && w.kind === 'pick') { const a = afterPass; afterPass = 0; if (a.round === s.round && s.players[1].got === a.got && s.passes[1] === a.passes) err('pass: the PC did not play again ' + JSON.stringify({ a, got: s.players[1].got, passes: s.passes, round: s.round, draft: s.draft, fits1: s.draft.map(t => !!t) })); }  // and the PC plays again (it took a tile, or it passed too)
        prev = s;
        if (!w || w.who !== 0) continue;
        if (w.kind === 'pick') {
          if (s.players.some(p => p.goods.some(g => g >= 5))) err('round ' + s.round + ': 5 of a colour not made into a jar');  // at once (owner 24 Nov)
          s.fits.forEach((f, k) => { if (f || !s.draft[k]) return; const d = seen('tile').find(t => t.id === 'draft-' + k);  // a tile he can't pick: greyed, its colours kept, not tappable
            did.unusable = true;
            if (!d || d.look !== 'grey' || d.cs.join() !== s.draft[k].join() || __dg.btn('draft-' + k)) err('greyed: tile ' + k + ' ' + JSON.stringify(d)); });
          const k = s.fits.indexOf(true); picked = k; await tap(btn('draft-' + k));
          if (!putBack && s.round >= 2 && __dg.state().wait && __dg.state().wait.kind === 'place') { await drag(__dg.held(), [innerWidth - 60, 400]); await drag(__dg.held(), __dg.slot(k)); putBack = did.putBack = __dg.state().draft[k] !== null && __dg.state().wait.kind === 'pick'; }
        }
        else if (w.kind === 'place') {
          if (picked < 0) did.bonusTile = true; picked = -1;
          const sp = s.spots.reduce((a, b) => b.m > a.m ? b : a);
          while (__dg.state().wait.r !== sp.r) { await tap(__dg.held()); __dg.render(); }
          const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), held = sp.cs, d = DIRS[sp.r];  // the colours it gets there (a wild tile takes its neighbours')  // matching edges with any land, counted on the board shown
          let edges = 0; const starts = []; [[sp.x, sp.y], [sp.x + d[0], sp.y + d[1]]].forEach(([x, y], h) => DIRS.forEach(([dx, dy]) => { const n = at(x + dx, y + dy); if (n && n.c === held[h]) { edges++; starts.push([x, y], [x + dx, y + dy]); } }));
          const g0 = sum(s.players[0].goods);
          await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)); __dg.render();
          const t = __dg.state(), g = seen('good').filter(d => d.o === 0).length, five = t.players[0].jars - s.players[0].jars - edges, n = lit(starts);  // his new jars wait for his taps: a jar per connection, a material per lit square, each 5 of a colour a jar at once
          if (five < 0 || g + 5 * five !== g0 + n || t.players[0].goods.some(x => x >= 5)) err('round ' + s.round + ': ' + edges + ' connections lighting ' + n + ' squares, goods ' + g0 + ' -> ' + g + ' and ' + (five + edges) + ' jars');
        }
        else if (w.kind === 'jar') { const n = s.players[0].jars; await tap(btn('jar-0')); if (__dg.state().players[0].jars >= n) did.moreJars = true; }  // a jar that brings another jar, or goods that make one
        else if (w.kind === 'slot') { did.slot = true; if (s.players[0].coins && !did.reroll) { did.reroll = true; await tap(btn('wheel-0')); await tap(btn('wheel-1')); await tap(btn('lever')); } else await tap(btn('tray')); }  // once: keep two wheels and pull the lever
      }
      return { errs: errs.slice(0, 5), did, left: __dg.state().queued };
    }""", [MAIN_SEED, MAIN_JARS])
    want = ['unusable', 'pass', 'putBack', 'bonusTile', 'slot', 'reroll', 'moreJars', 'end']
    missing = [k for k in want if not out['did'].get(k)]
    report(not out['errs'] and not missing and out['left'] == 0, 'main game: every situation, what he sees adds up', 'missing %s, errors %s, jar contents left %s' % (missing, out['errs'], out['left']))

def f_simulation(q):  # owner 25 Nov (task list): a simulation tool plays seeded games through the screen and reports jars, coins and bonus shares per player
    import sim; r = sim.play(q, [1])[0]
    shares = all(sum(p['opened'].values()) == p['jars'] for p in r['players'])
    ok = r['over'] and shares and [p['coins'] for p in r['players']] == r['shown'] and all(p['jars'] > 0 for p in r['players'])
    report(ok, 'simulation: jars, coins and bonus shares per player', '%s' % r)

def f_random_play(q):  # seeded games played through the screen (taps and drags on what is drawn, at random moments); after every move, what he can see holds:
    # a placement gives a jar per connection and a material per square it lights, on the board shown; each 5 of a colour a jar at once
    bad = q.evaluate("""async () => {
      const cv = document.querySelector('canvas'), ch = new MessageChannel(), errs = [];
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };  // let the game's answers run (they are promise steps in fast mode); no timer, no message: those wait for the browser
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { ev('pointerdown', p); ev('pointerup', p); await tick(); };  // the game answers after the event: wait for it
      const drag = async (a, b) => { ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = kind => __dg.drawn().filter(d => d.k === kind);
      const lit = starts => { const sq2 = seen('square'), on = (x, y) => sq2.find(d => d.x === x && d.y === y), done = new Set(), todo = starts.slice(); while (todo.length) { const [x, y] = todo.shift(), a = on(x, y); if (!a || done.has(x + ',' + y)) continue; done.add(x + ',' + y); [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const b = on(x + dx, y + dy); if (b && b.c === a.c) todo.push([x + dx, y + dy]); }); } return done.size; };  // the squares the connections light, on the board shown (owner 25 Nov)
      for (let seed = 1; seed <= 4; seed++) {
        let rs = seed * 7919; const rand = n => { rs = (rs * 16807) % 2147483647; return rs % n; };
        __dg.restart({ seed, fast: true });
        for (let step = 0; ; step++) {
          for (let k = rand(3); k >= 0; k--) await tick();
          const s = __dg.state(), w = s.wait;
          if (s.over) break;
          if (step > 3000) { errs.push('seed ' + seed + ' stuck at ' + JSON.stringify(w)); break; }
          if (!w || w.who !== 0) continue;
          __dg.render(); const btn = id => __dg.btn(id);  // draw first: buttons are where the last picture put them
          if (w.kind === 'pick') { const ok = s.fits.map((f, i) => f ? i : -1).filter(i => i >= 0); if (!ok.length) { errs.push('seed ' + seed + ' pick with nothing to pick'); break; } await tap(btn('draft-' + ok[rand(ok.length)])); }
          else if (w.kind === 'place') {
            if (!s.spots.length) { errs.push('seed ' + seed + ' a tile with no place'); break; }
            const sp = s.spots[rand(s.spots.length)];
            while (__dg.state().wait.r !== sp.r) { await tap(__dg.held()); __dg.render(); }
            const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), d = [[1, 0], [0, 1], [-1, 0], [0, -1]][sp.r], cs = sp.cs;  // the colours it gets there (a wild tile takes its neighbours')
            const hs = [[sp.x, sp.y], [sp.x + d[0], sp.y + d[1]]], starts = []; let edges = 0;
            hs.forEach(([x, y], h) => [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const n = at(x + dx, y + dy); if (n && n.c === cs[h]) { edges++; starts.push([x, y], [x + dx, y + dy]); } }));
            const g0 = s.players[0].goods.reduce((a, b) => a + b, 0);
            await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)); __dg.render();
            const g = seen('good').filter(d => d.o === 0).length, five = __dg.state().players[0].jars - s.players[0].jars - edges, n = lit(starts);  // his new jars wait for his taps: one per connection, and one per 5 of a colour
            if (five < 0 || g + 5 * five !== g0 + n) errs.push('seed ' + seed + ': ' + edges + ' connections lighting ' + n + ' squares, goods ' + g0 + ' -> ' + g + ' and ' + (five + edges) + ' jars');
          }
          else if (w.kind === 'jar') await tap(btn('jar-0'));
          else if (w.kind === 'slot') await tap(btn('tray'));
        }
        if (errs.length > 5) break;
      }
      return errs.slice(0, 5);
    }""")
    report(not bad, 'random play: games end, what he sees adds up', '%s' % (bad or '4 games'))

# SECTION: RUN -- one browser, one page (with a fake clock that runs normally until a flow pauses it), every flow on a new game
# The browser does not wait for the screen's refresh: each step of a finger drag otherwise waits a whole frame (16 ms); the game's own time is the fake clock either way.
FLOWS = {n[2:]: f for n, f in list(globals().items()) if n.startswith('f_')}
def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--disable-gpu-vsync', '--disable-frame-rate-limit', '--disable-gpu', '--disable-gpu-compositing', '--disable-accelerated-2d-canvas']); ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True); q = ctx.new_page()
        q.clock.install(); q.goto(GAME.as_uri() + '?fast=1')
        try: q.wait_for_function("()=>window.__dg&&__dg.ready", timeout=5000)
        except Exception as e: pass
        for n in (names or FLOWS):
            NOW[0] = n
            try: q.mouse.up(); table(q); FLOWS[n](q)
            except Exception as e:
                try: s = st(q); seen = 'wait %s, phase %s, round %s' % (s['wait'], s['phase'], s['round'])
                except Exception: seen = ''
                report(False, n, 'error: %s; %s' % (str(e).splitlines()[0][:100], seen))
        b.close()
