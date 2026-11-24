# Flow tests: what the owner does, in the running game: real page, real mouse taps and drags on what he sees.
# One browser and one page for the whole run: each flow starts a new game with a set table (fast: the PC's hand moves without waiting)
# and prints PASS or FAIL, [its flow name], what it checks, and what was seen. Waits are on the game's state, never on a fixed sleep.
# Colours are numbered 0-4 (0 the most common); a tile is [first half, second half]; the board is 20 x 13 squares, the start tiles [0, 1] at (4, 6) and (14, 6).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'empty'}, {'k': 'coins'}, {'k': 'coins2'}, {'k': 'slot'}, {'k': 'steal'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib, datetime
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
def report(ok, name, seen): print('%-4s [%s] %-40s %s' % ('PASS' if ok else 'FAIL', NOW[0], name, seen))
FACES = [['coin', 'jar', 'set', 'g2']] * 3  # a slot machine's faces, wheel by wheel: 1 coin, 1 jar, 1 of each good, 5 of good 2 (owner 24 Nov)
K4 = [[4, 0, 0, 0, 0], [0] * 5]  # the kid has 4 goods of colour 0: one more makes a jar
K44 = [[4, 4, 0, 0, 0], [0] * 5]  # 4 of colours 0 and 1: a [0, 1] tile under the start tile makes 2 jars
def get_jar(q, contents, coins=0, slots=(), faces=FACES):  # place a tile with one matching edge; its good makes a jar; open it (slots: the face each spin lands on)
    table(q, bag=[[0, 4]] * 4, coins=[coins, 0], goods=K4, jarQueue=contents + [COIN] * 8, slotQueue=list(slots), slotFaces=faces)
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
def f_colour_split(q):  # colours are scarce in a fixed ratio: 80 halves, about 24/22/20/18/16%
    s = st(q); report(s['halves'] == [19, 18, 16, 14, 13], 'colours: fixed scarce split', str(s['halves']))

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
    drag_to(q, {'x': 3, 'y': 6, 'r': 2}); mine = [t for t in st(q)['tiles'] if t[5] == 0 and t[:5] == [3, 6, 2, 0, 4]]
    report(not marks and len(mine) == 1, 'place: dragged tile snaps in', 'extra marks %s, placed %s' % (marks, mine))

def f_drag_from_pile(q):  # owner 24 Nov: no tap first: press a tile in the pile and drag it straight to its place; a plain tap still just takes it, unturned
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8)
    path(q, q.evaluate("()=>__dg.btn('draft-0')"), q.evaluate("()=>__dg.tileAt(4,5,0)"))
    placed = [4, 5, 0, 0, 4] in [t[:5] for t in st(q)['tiles'] if t[5] == 0]
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); w = st(q)['wait']
    report(placed and w == {'kind': 'place', 'who': 0, 'r': 0}, 'pile: drag straight from the pile', 'placed %s; after a tap %s' % (placed, w))

def f_carried_tilts(q):  # owner 24 Nov ("rethink all UI": pieces do not feel physical): a carried tile tilts toward where it is going, and straightens when it stops
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h = held(q)
    tilt = lambda: drawn(q, 'heldmark')[0]['tilt']
    q.mouse.move(h[0], h[1]); q.mouse.down(); q.mouse.move(h[0] + 200, h[1] + 120, steps=6); settle(q); right = tilt()
    pause_clock(q); skip(q, 500); still = tilt(); q.clock.resume()
    q.mouse.move(h[0] - 100, h[1] + 120, steps=6); settle(q); left = tilt(); q.mouse.up(); settle(q)
    ok = right >= 4 and abs(still) < 0.5 and left <= -4
    report(ok, 'carried tile tilts with the drag', 'moving right %.1f deg, standing still %.1f deg, moving left %.1f deg' % (right, still, left))

def f_tile_bounces(q):  # owner 24 Nov ("rethink all UI": pieces do not feel physical): a tile that lands on the board bounces a little (lands big, squashes, settles), quickly
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2})
    scale = lambda: [x['scale'] for x in drawn(q, 'bounce')]
    seen = [scale()]
    for _ in range(4): skip(q, 70); seen.append(scale())
    skip(q, 200); after = scale(); q.clock.resume()
    flat = [v[0] if v else 1 for v in seen]
    ok = flat[0] > 1.04 and min(flat) < 0.99 and not after
    report(ok, 'a landing tile bounces', 'size every 70 ms %s, then %s' % ([round(v, 3) for v in flat], after or 'still'))

def f_board_tap(q):  # owner 24 Nov ("rethink all UI": the board does not answer a tap): a tap on the board puffs dust where it lands, with a soft knock, and changes nothing
    table(q, bag=[[0, 4]] * 4); before = st(q); p = q.evaluate("()=>__dg.square(10,1)")
    q.mouse.click(p[0], p[1]); settle(q); after = st(q)
    dust = [x for x in drawn(q, 'speck') if abs(x['x'] - p[0]) < 30 and abs(x['y'] - p[1]) < 30]; h = q.evaluate("()=>__dg.sounds()")
    ok = len(dust) >= 6 and 'board' in h and after['wait'] == before['wait'] and after['tiles'] == before['tiles']
    report(ok, 'a tap on the board answers', '%d dust specks at the tap, sounds %s, nothing else changed %s' % (len(dust), h, after['wait'] == before['wait']))

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

def f_pile_no_frames(q):  # owner 24 Nov: no outline around the pile's tiles
    table(q, bag=[[0, 4]] * 4); c = q.evaluate("()=>__dg.btn('draft-0')"); ds = (q.evaluate("()=>__dg.btnBox('draft-0')")['w'] - 24) / 2
    beside = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [c[0] - ds - 6, c[1]])  # just left of the tile: the market tray's own colour, not a frame
    tray = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [c[0] - ds - 14, c[1] - ds / 2 - 10])  # the tray, away from the tile
    report(beside == tray, 'pile: tiles have no outline', 'beside the tile %s, the tray %s' % (beside, tray))

def f_pile_fits(q):  # owner 24 Nov ("rethink all UI"): the pile stacked a layer per round up from its place and ran off the top of the screen; a full pile stays on screen, a layer per round
    table(q); pile = drawn(q, 'pile')[0]; ds = (q.evaluate("()=>__dg.btnBox('draft-0')")['w'] - 24) / 2; T = drawn(q, 'market')[0]
    top, bottom = pile['y'] - ds / 2, pile['bottom']
    ok = pile['layers'] >= 8 and top >= 4 and bottom <= T['y'] + T['h'] and pile['step'] >= 3
    report(ok, 'pile: a full pile stays on screen', '%d layers, %.1f px apart, from %.0f to %.0f px (screen top 0, market bottom %.0f)' % (pile['layers'], pile['step'], top, bottom, T['y'] + T['h']))

def f_round_start_no_goods(q):  # owner 24 Nov: land does not make goods each round, a tile's halves make none; goods left carry over to the next round; a round starts with morning light
    table(q, bag=[[2, 2], [2, 2], [3, 3], [3, 3], [2, 2]], tiles=[[4, 7, 0, 2, 2, 0]], jarQueue=[COIN] * 8)  # only the kid can place: the PC passes; [3, 3] fits nobody
    s = kid_plays(q, lambda s: s['round'] == 2 and s['wait'] and s['wait']['kind'] == 'pick'); h = q.evaluate("()=>__dg.sounds()"); g = s['players'][0]['goods']
    ok = s['round'] == 2 and sum(g) > 0 and sum(g) + 5 * h.count('made') == h.count('edge') and 'dissolve' not in h and h.count('dawn') == 2
    report(ok, 'round: no goods from land, goods carry over', 'round %d, goods %s, jars made %d, goods from edges %d, lost %s, morning lights %d' % (s['round'], g, h.count('made'), h.count('edge'), 'dissolve' in h, h.count('dawn')))

def f_goods_from_edges(q):  # owner 24 Nov: a placed tile gives one good for each matching edge, of that edge's colour, nothing for its halves: each matching edge glows and its good flies out of it to the stockpile
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0})
    edges = [q.evaluate("([x,y,d])=>__dg.edge(x,y,d)", e) for e in ([4, 7, 3], [5, 7, 3])]; glows, starts, ms, jar_wait = 0, [], 0, False
    while ms < EDGE_GOODS:
        skip(q, 50); ms += 50; glows = max(glows, len(drawn(q, 'edgeglow'))); w = st(q)['wait']; jar_wait = jar_wait or bool(w and w['kind'] == 'jar')
        starts += [(ms, x['fx'], x['fy'], x['c']) for x in drawn(q, 'flight') if x['look'] == 'good' and (x['fx'], x['fy'], x['c']) not in [a[1:] for a in starts]]
    q.clock.resume(); g = st(q)['players'][0]['goods']; h = [n for n in q.evaluate("()=>__dg.sounds()") if n not in ('dawn', 'turn')]
    out = sorted((min(range(2), key=lambda k: (fx - edges[k][0]) ** 2 + (fy - edges[k][1]) ** 2), c) for _, fx, fy, c in starts)
    near = all(min(((fx - e[0]) ** 2 + (fy - e[1]) ** 2) ** 0.5 for e in edges) < 5 for _, fx, fy, _ in starts)
    ok = glows == 2 and out == [(0, 0), (1, 1)] and near and len({m for m, *_ in starts}) == 2 and g == [1, 1, 0, 0, 0] and not jar_wait and h[:4] == ['pick', 'snap', 'edge', 'edge'] and 'jar' not in h
    report(ok, 'goods: one out of each matching edge, none for halves', 'edges glowing %d; goods out of the edges %s (colour by edge %s), one after another %s; goods %s; a jar %s; sounds %s' % (glows, near, out, len({m for m, *_ in starts}) == 2, g, jar_wait, h[:4]))

def f_five_make_jar(q):  # owner 24 Nov: 5 goods of one colour become a jar at once (not at the round's end) and it is opened at once; the jar comes to its place first, then the goods fly into it on curves, one by one
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=K4, jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); P = next(x for x in drawn(q, 'panel') if x['o'] == 0)['w']; drag_to(q, {'x': 3, 'y': 6, 'r': 2}); drops, intos, ms = [], [], 0
    while ms < 4000:
        skip(q, 50); ms += 50; d = q.evaluate("()=>__dg.drawn().filter(d=>d.k==='flight')")
        drops += [(ms, x) for x in d if x['look'] == 'jar']; intos += [(ms, x) for x in d if x['look'] == 'good' and x['fx'] < P]  # goods leaving the stockpile
        w = st(q)['wait']
        if w and w['kind'] == 'jar': break
    s = st(q); jar = [x for x in drawn(q, 'jar') if x['o'] == 0]; left = [x for x in drawn(q, 'good') if x['o'] == 0]; tap(q, 'jar-0')
    run_until(q, "()=>__dg.state().players[0].coins===1"); coins = st(q)['players'][0]['coins']; q.clock.resume()
    into = [(m, x) for m, x in intos if jar and abs(x['tx'] - jar[0]['x']) < 5]
    first = bool(drops) and bool(into) and into[0][0] > drops[-1][0]  # the jar is in its place before any good flies into it
    ok = bool(drops) and drops[0][1]['fy'] < 0 and len(jar) == 1 and first and len({(round(x['fx']), round(x['fy'])) for _, x in into}) == 5 and any(x['y'] < min(x['fy'], x['ty']) - 10 for _, x in into) \
        and not left and s['round'] == 1 and s['phase'] == 'round' and s['wait']['who'] == 0 and coins == 1
    report(ok, 'jars: 5 of a colour make a jar at once, opened at once', 'jar from the top %s, in place first %s, goods into it from %d places, goods left %d, round %d %s, opened for a coin %s' % (bool(drops) and drops[0][1]['fy'] < 0, first, len({(round(x['fx']), round(x['fy'])) for _, x in into}), len(left), s['round'], s['phase'], coins == 1))

def f_no_bidding(q):  # owner 24 Nov: no bidding (too slow: every pick triggered it): the player whose turn it is takes the tile he picks
    kid, pc = [[4, 4, 0, 2, 3, 0], [4, 2, 0, 4, 4, 0]], [[14, 4, 0, 2, 3, 1], [14, 2, 0, 4, 4, 1]]
    table(q, bag=[[0, 1], [0, 0], [0, 0], [0, 0]], tiles=kid + pc, goods=[[1] * 5, [1] * 5]); tap(q, 'draft-0'); w = st(q)['wait']; s = st(q)
    ok = w['kind'] == 'place' and w['who'] == 0 and s['players'][1]['goods'] == [1] * 5 and not drawn(q, 'bidcard') and 'bid' not in q.evaluate("()=>__dg.sounds()")
    report(ok, 'pick: the tile is yours, no bid', 'after the pick: %s, PC goods %s, bid card %s' % (w, s['players'][1]['goods'], bool(drawn(q, 'bidcard'))))

def f_stockpile_columns(q):  # owner 24 Nov: goods stand in a column per colour (they never widen the panel); rows of one of each are marked as sets, each 5 of a colour as a jar at the round's end (owner 24 Nov: 5, not 3)
    table(q, bag=[[0, 4]] * 4, goods=[[4, 4, 7, 2, 1], [0] * 5]); g = drawn(q, 'good'); g = [x for x in g if x['o'] == 0]
    cols = {c: {round(x['x']) for x in g if x['c'] == c} for c in range(5)}; counts = [sum(1 for x in g if x['c'] == c) for c in range(5)]
    panel = next(x for x in drawn(q, 'panel') if x['o'] == 0); inside = all(x['x'] < panel['x'] + panel['w'] for x in g)
    jars = [sum(1 for x in drawn(q, 'jargroup') if x['o'] == 0 and x['c'] == c) for c in range(5)]; sets = sum(1 for x in drawn(q, 'setrow') if x['o'] == 0)
    shaped = all(x['shape'] == 'jar' and x['parts'] == ['lip', 'neck', 'handles', 'body', 'foot'] for x in drawn(q, 'jargroup'))  # owner 24 Nov: "the sets of 5 should be outlined not by this oval, but by a jar"
    signs = [x for x in drawn(q, 'setsign') if x['o'] == 0]; side = max(x['x'] + x['r'] for x in g)  # owner 24 Nov: "the sets should on their side make a set symbol appear"
    signed = len(signs) == 1 and signs[0]['x'] > side and abs(signs[0]['y'] - min(x['y'] for x in g if x['c'] == 4)) < 2
    ok = counts == [4, 4, 7, 2, 1] and all(len(v) == 1 for c, v in cols.items() if counts[c]) and inside and jars == [0, 0, 1, 0, 0] and sets == 1 and shaped and signed
    report(ok, 'stockpile: columns, sets and jar groups shown', 'goods %s, one column each %s, jar groups %s outlined as jars %s, set rows %d with a set sign beside %s' % (counts, all(len(v) == 1 for c, v in cols.items() if counts[c]), jars, shaped, sets, signed))

def away_and_back(q, k):  # carry the tile in hand onto the board, leave it, then carry it back to its market place
    path(q, held(q), [640, 600]); path(q, held(q), q.evaluate("(k)=>__dg.slot(k)", k))
def f_put_back(q):  # owner 24 Nov: a picked tile can be put back on its market place and another picked
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); away_and_back(q, 0); waiting(q, 'pick'); s = st(q)
    ok = s['draft'][0] == [0, 4] and s['players'][0]['got'] == 0 and q.evaluate("()=>!!__dg.btn('draft-1')")
    report(ok, 'put back: returns to the market', 'back on its place %s, tiles taken %d' % (s['draft'][0], s['players'][0]['got']))

def f_sounds(q):  # owner 24 Nov: "add some sounds, it's hard to follow what happens": each thing that happens has its sound, in the order it happens
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot'); tap(q, 'wheel-2'); tap(q, 'reroll')
    q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); a = [n for n in q.evaluate("()=>__dg.sounds()") if n not in ('dawn', 'turn', 'into')]  # the morning, the turn sound and the goods going into a jar have their own flows
    want = ['pick', 'snap', 'edge', 'made', 'jar', 'roll', 'roll', 'roll', 'spin', 'stop', 'stop', 'stop', 'roll', 'spin', 'stop', 'win']  # each wheel ticks as it rolls (owner 24 Nov)
    ok = a[:len(want)] == want
    report(ok, 'sounds: one for each thing, in order', 'slot jar: %s, heard %s' % (a[:len(want)], sorted(set(a))))

def f_sound_kinds(q):  # owner 24 Nov: "a weird blip when I tap a piece"; "jars must make a breaking sound": a tap knocks like wood, a jar breaks like clay, a coin clinks; no beeps anywhere
    get_jar(q, [COIN]); settle(q); h = [k for n, k in zip(q.evaluate("()=>__dg.sounds()"), q.evaluate("()=>__dg.heardKinds()")) if n not in ('dawn', 'turn', 'into', 'made')]  # the morning, the turn sound and the jar being made have their own flows
    ok = h[:5] == ['knock', 'knock', 'chime', 'break', 'clink']  # tap, snap, the good out of its edge, the jar opened, its coin
    ok = ok and set(q.evaluate("()=>__dg.soundKinds()")) <= {'break', 'chime', 'clink', 'knock', 'whoosh'}
    report(ok, 'sounds: wood tap, clay break, coin clink', 'heard %s; kinds in the game %s' % (h[:5], q.evaluate("()=>__dg.soundKinds()")))

def f_many_jars_rows(q):  # owner 24 Nov: "when a lot of jars exist, make more rows, 6 jars per row; don't reduce their size"
    get_jar_ready = lambda goods: (table(q, bag=[[0, 4]] * 4, goods=goods, jarQueue=[COIN] * 40), tap(q, 'draft-0'), waiting(q, 'place'), drag_to(q, {'x': 3, 'y': 6, 'r': 2}), waiting(q, 'jar'))
    get_jar_ready(K4); one = drawn(q, 'jar')[0]['size']  # one jar alone: its size
    get_jar_ready([[69, 0, 0, 0, 0], [0] * 5]); jars = drawn(q, 'jar')  # 70 goods of one colour: 14 jars at once
    rows = {}; [rows.setdefault(j['row'], []).append(j) for j in jars]
    W, H = q.evaluate("()=>[innerWidth, innerHeight]")
    ok = len(jars) >= 14 and max(len(r) for r in rows.values()) == 6 and all(abs(j['size'] - one) < 0.5 for j in jars) and all(0 < j['y'] - j['size'] / 2 and j['y'] + j['size'] / 2 < H for j in jars)
    report(ok, 'jars: 6 to a row, more rows, same size', '%d jars in rows of %s, sizes %s (one alone %.0f)' % (len(jars), [len(r) for r in rows.values()], sorted({round(j['size']) for j in jars}), one))

def f_many_coins(q):  # owner 24 Nov: "make sure more coins than you predicted can fit", then "coins are too stacked and squeezed, make them easier to count": rows of 5, apart, a gap after every 10
    out = {}
    for n in (12, 100, 160):  # 160: found by the main game, more than the tray was made for: they shrink but stay apart and leave the goods their room
        table(q, bag=[[0, 4]] * 4, coins=[n, 0]); c = [x for x in drawn(q, 'coin') if x['o'] == 0]
        P, H = next(x for x in drawn(q, 'panel') if x['o'] == 0)['w'], q.evaluate("()=>innerHeight")
        inside = all(x['x'] - x['r'] > 0 and x['x'] + x['r'] < P and x['y'] + x['r'] < H for x in c)
        gap = min(((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2) ** 0.5 - a['r'] - b['r'] for i, a in enumerate(c) for b in c[i + 1:])
        rows = sorted({round(x['y']) for x in c}, reverse=True); per = [sum(1 for x in c if round(x['y']) == y) for y in rows]
        steps = [a - b for a, b in zip(rows, rows[1:])]; tens = all(steps[k] > steps[0] + 2 for k in range(1, len(steps), 2))
        goods_room = q.evaluate("()=>{const t=__dg.drawn().filter(d=>d.k==='tray'&&d.o===0);return t.length}") == 2
        out[n] = (len(c) == n and inside and gap >= 1 and goods_room and all(v == 5 for v in per[:-1]) and tens, len(c), inside, round(gap, 1), per[:3], tens)
    report(all(v[0] for v in out.values()), 'coins: rows of 5, apart, a gap after every 10', str(out))

def f_jars_apart(q):  # owner 24 Nov: "jar circles are touching": every jar and its glow stands apart, with a clear gap
    table(q, bag=[[0, 1]] * 4, goods=K44, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0}); waiting(q, 'jar'); settle(q)
    jars = sorted((d['x'], d['size'] / 2) for d in drawn(q, 'jar')); glows = sorted((d['x'], d['r']) for d in drawn(q, 'jarglow'))
    gaps = [b[0] - a[0] - a[1] - b[1] for row in (jars, glows) for a, b in zip(row, row[1:])]
    ok = len(jars) == 2 and len(glows) == 2 and min(gaps) >= 12
    report(ok, 'jars: apart, with a gap between them', 'gaps between jars and between glows %s px' % [round(g) for g in gaps])

def f_sky_stars(q):  # owner 24 Nov ("rethink all UI"): the stars in the evening sky were small; at a round's end they are big enough to see from across the room, and apart
    pause_clock(q); table(q, fast=False, bag=[[2, 2], [3, 3]], tiles=[[4, 7, 0, 2, 2, 0], [4, 8, 0, 2, 2, 0]], jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 9, 'r': 0})
    for _ in range(80):
        if drawn(q, 'skystar'): break
        skip(q, 200)
    skip(q, 1600); stars = drawn(q, 'skystar'); q.clock.resume()
    gap = min((((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2) ** 0.5 - a['r'] - b['r'] for i, a in enumerate(stars) for b in stars[i + 1:]), default=0)
    ok = len(stars) >= 4 and min(x['r'] for x in stars) >= 18 and gap >= 16
    report(ok, 'evening: big stars in the sky', '%d stars, smallest %s px across, %.0f px apart' % (len(stars), min((2 * x['r'] for x in stars), default=0), gap))

def f_round_end_shown(q):  # owner 24 Nov: the round's end is its own moment, seen and heard, before anything else happens in it; "the sunset is weird": evening falls (sky darkens from the top, a moon and stars), the board stays in view; leftover market tiles fly back to the pile
    pause_clock(q); table(q, fast=False, bag=[[2, 2], [3, 3]], tiles=[[4, 7, 0, 2, 2, 0], [4, 8, 0, 2, 2, 0]], jarQueue=[COIN] * 8)  # [3, 3] fits nobody: both pass, it is left in the market
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 9, 'r': 0})
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

def f_goods_big(q):  # owner 24 Nov ("rethink all UI"): goods were tiny (about 20 px a column); goods big enough to see and count, each 5's jar outline inside its own column, set signs big
    table(q, bag=[[0, 4]] * 4, goods=[[8, 4, 7, 2, 1], [0] * 5]); g = [x for x in drawn(q, 'good') if x['o'] == 0]
    xs = sorted({round(x['x']) for x in g}); pitch = min(b - a for a, b in zip(xs, xs[1:]))
    jars = [x for x in drawn(q, 'jargroup') if x['o'] == 0]; signs = [x for x in drawn(q, 'setsign') if x['o'] == 0]
    r = min(x['r'] for x in g); wide = max(x['half'] for x in jars); sign = min(x['r'] for x in signs)
    ok = r >= 10 and jars and 2 * wide < pitch - 2 and sign >= 12
    report(ok, 'stockpile: goods big, jar outlines inside their column', 'goods radius %.1f px (at least 10), jar outline %.1f px wide in a %d px column, set sign radius %.1f (at least 12)' % (r, 2 * wide, pitch, sign))

def f_turn_shown(q):  # owner 24 Nov: "make it obvious who plays; now there is no difference between me and the opponent playing": the player whose turn it is has his area lit, the other's is dimmed; a sound when the turn passes
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); settle(q)
    lit = lambda: {d['o']: d['lit'] for d in drawn(q, 'panel')}
    mine = lit(); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2})
    run_until(q, "()=>__dg.state().turn===1"); pcs = lit(); w = st(q)['wait']; h = q.evaluate("()=>__dg.sounds()")
    faces = {x['o']: x for x in drawn(q, 'avatar')}; light = [x for x in drawn(q, 'flight') if x['look'] == 'turnlight']; market = drawn(q, 'market')
    travels = bool(light) and abs(light[0]['fx'] - faces[0]['x']) < 5 and abs(light[0]['tx'] - faces[1]['x']) < 5  # owner 24 Nov: "it's still not obvious who plays": the light flies from one face to the other
    bigger = faces[1]['r'] > faces[0]['r'] and market and market[0]['o'] == 1; q.clock.resume()
    ok = mine == {0: True, 1: False} and pcs == {0: False, 1: True} and 'turn' in h and travels and bigger
    report(ok, 'turn: lit, the light flies over, his face bigger, the market his colour', 'kid playing %s; PC playing %s (wait %s); turn sound %s; light flies face to face %s; PC face bigger and market his %s' % (mine, pcs, w, 'turn' in h, travels, bool(bigger)))

def f_screen_parts(q):  # owner 24 Nov: "the sidebar doesn't portray any info"; "what are these 9 vertical lines on top": each player's area has his face, a goods tray and a coins tray, everything spaced apart; the pile is a stack of tiles
    table(q, bag=[[0, 4]] * 12, goods=[[4, 4, 7, 2, 1], [1, 1, 0, 0, 0]], coins=[13, 2]); d = q.evaluate("()=>__dg.drawn()")
    kinds = lambda k, o: [x for x in d if x['k'] == k and x.get('o') == o]
    def min_gap(items):  # the smallest gap between any two round things
        return min((((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2) ** 0.5 - a['r'] - b['r'] for i, a in enumerate(items) for b in items[i + 1:]), default=99)
    pile = [x for x in d if x['k'] == 'pile']; bars = [x for x in d if x['k'] == 'roundsleft']
    parts = {o: (len(kinds('avatar', o)), sorted(x['for'] for x in kinds('tray', o))) for o in (0, 1)}
    gaps = (min_gap(kinds('good', 0)), min_gap(kinds('coin', 0)))
    ok = parts == {0: (1, ['coins', 'goods']), 1: (1, ['coins', 'goods'])} and min(gaps) >= 3 and len(pile) == 1 and pile[0]['layers'] == 2 and not bars
    report(ok, 'screen: faces, goods and coins trays, things apart, a pile', 'parts %s, smallest gaps goods/coins %s px, pile %s' % (parts, [round(g, 1) for g in gaps], pile))

def f_pc_best(q):  # the PC picks and places for the most goods
    table(q, bag=[[0, 0], [0, 1], [0, 4], [0, 4]], first=1, jarQueue=[COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] != [14, 6]]
    report(pc == [[0, 1]] and s['players'][1]['goods'] == [1, 1, 0, 0, 0], 'pc: best tile, best place', 'pc tiles %s goods %s' % (pc, s['players'][1]['goods']))

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

def f_pc_slot(q):  # the PC takes the best expected result on the slot machine too (here: chasing the third coin is worth a little less than stopping, so it stops and takes 2 coins and a jar)
    table(q, bag=[[0, 4]] * 4, first=1, coins=[0, 5], goods=[[0] * 5, [4, 0, 0, 0, 0]], jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 0, 1], slotFaces=FACES)  # coin, coin, jar: chasing the third coin is worth a little less than stopping
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); c = st(q)['players'][1]['coins']
    report(c == 5 + 2 + 1, 'pc: slot machine played for the most', 'pc coins %d (5, plus 2 coins shown, plus the coin in the jar shown; no coin paid)' % c)

def f_jar_mix(q):  # owner 24 Nov, per 100 jars: 10 empty, 40 one coin, 10 two coins, 5 steal, 5 extra tile, the rest equal (7.5 each: slot, first, another jar, set)
    table(q, bag=[[0, 4]] * 4, tiles=[[14, 7, 0, 0, 1, 1]], seed=11)  # the PC has a tile the kid could steal; seeded: an unseeded sample missed the 1.5% band about once in 15 runs
    n = 8000; m = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)
    want = {'empty': 10, 'coins': 40, 'coins2': 10, 'steal': 5, 'tile': 5, 'slot': 7.5, 'first': 7.5, 'jar': 7.5, 'set': 7.5}
    ok = set(m) == set(want) and all(abs(100 * m[k] / n - v) < 1.5 for k, v in want.items())
    report(ok, 'jars: the owner\'s mix', ', '.join('%s %.1f%%' % (k, 100 * m.get(k, 0) / n) for k in want))

def f_no_useless_steal(q):  # owner 24 Nov: "steal a tile shouldn't appear when one can't be stolen (opponent has only the starting tile)"
    table(q, bag=[[0, 4]] * 4, seed=11); n = 4000; m = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)  # seeded, so the shares never wander out of their band
    report('steal' not in m and abs(100 * m['coins'] / n - 40 / 0.95) < 2, 'jars: no steal when nothing can be stolen', str(m))

def f_empty_jar(q):  # owner 24 Nov: some jars hold nothing: it breaks, shows it is empty, and nothing is gained
    get_jar(q, [{'k': 'empty'}])
    waiting(q, 'pick'); p = st(q)['players'][0]
    report(p['coins'] == 0 and p['jars'] == 0 and 'jar' in q.evaluate("()=>__dg.sounds()"), 'jars: an empty jar gives nothing', 'coins %d jars %d' % (p['coins'], p['jars']))

def f_jar_breaks(q):  # owner 24 Nov: "jars should visually break and the revealed bonus comes from inside them"; "the you play first should fly to its place"; a coin flies to his coins
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, goods=K44, jarQueue=[COIN, {'k': 'first'}] + [COIN] * 8)  # the tile meets 2 edges: 2 jars
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}")
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
    star = flights(seen0, 'star'); token = drawn(q, 'token'); star_flew = bool(star) and bool(token) and near((star[-1]['tx'], star[-1]['ty']), (token[0]['x'], token[0]['y'])) and all(s['first'] is None for d, s in seen0 if any(x['k'] == 'flight' and x['look'] == 'star' for x in d))
    q.clock.resume()
    report(broke and came_out and coin_flew and star_flew, 'jars: break where tapped, the bonus comes out, rewards fly to their place', 'broke where tapped %s, bonus out of it %s, coin flew to his coins %s, star flew to its place %s' % (broke, came_out, coin_flew, star_flew))

def f_jars_step_aside(q):  # owner 24 Nov: "the extra tile bonus makes the jars I was opening disappear; it should temporarily fly them to some free area"
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, goods=K44, jarQueue=[{'k': 'tile'}] + [COIN] * 8)  # 2 jars; the first holds a tile
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-1')
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='place'}", 3000); q.clock.run_for(600); settle(q)
    T = q.evaluate("()=>innerHeight*0.16"); away = [j for j in drawn(q, 'jar') if j['o'] == 0]
    aside = len(away) == 1 and away[0]['y'] < T + 20
    drag_to(q, best_spot(q)); q.clock.run_for(1400); settle(q); back = [j for j in drawn(q, 'jar') if j['o'] == 0 and not j.get('new')]; q.clock.resume()
    ok = aside and len(back) == 1 and back[0]['y'] > T + 100
    report(ok, 'jars: step aside during a bonus tile, then come back', 'waiting jar seen aside while placing %s (%s), back in the row after %s' % (aside, [(round(j['x']), round(j['y'])) for j in away], [(round(j['x']), round(j['y'])) for j in back]))

def f_jar_labels(q):  # owner 24 Nov: "for bonus jars add some text, I don't get what some of those mean": every jar's contents carry a short label
    seen = {}
    for k in ['empty', 'coins', 'coins2', 'slot', 'steal', 'first', 'tile', 'jar', 'set']:
        pause_clock(q); table(q, bag=[[0, 4]] * 4, fast=False, goods=K4, jarQueue=[{'k': k}] + [COIN] * 8)
        tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
        seen[k] = [d['text'] for d in drawn(q, 'label')]; q.clock.resume()
    ok = all(len(v) == 1 and v[0] for v in seen.values()) and len({v[0] for v in seen.values() if v}) == 9
    report(ok, 'jars: each content has its own label', str(seen))

def f_new_game_mid_jar(q):  # found by the tests: a new game started while a jar is being shown: the old jar never pays into the new game
    pause_clock(q)
    table(q, bag=[[0, 4]] * 4, fast=False, goods=K4, jarQueue=[{'k': 'coins2'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    table(q, bag=[[0, 4]] * 4); q.clock.run_for(2000); settle(q); s = st(q); q.clock.resume()
    report(s['players'][0]['coins'] == 0 and s['wait']['kind'] == 'pick', 'new game: an old jar pays nothing into it', 'coins %d, wait %s' % (s['players'][0]['coins'], s['wait']))

def f_many_goods_drawn(q):  # found by the tests (a seeded main game crashed): a column with very many goods of one colour must still draw
    try: table(q, bag=[[0, 4]] * 4, goods=[[0, 0, 90, 0, 0], [0] * 5]); n = sum(1 for x in drawn(q, 'good') if x['o'] == 0 and x['c'] == 2); ok = n == 90; seen = '%d goods of colour 2 drawn' % n
    except Exception as e: ok, seen = False, 'drawing failed: %s' % str(e).splitlines()[0][:80]
    report(ok, 'stockpile: very many goods still draw', seen)

def f_coins2(q):  # the 2 coins bonus
    get_jar(q, [{'k': 'coins2'}]); c = st(q)['players'][0]['coins']
    report(c == 2, 'jar: 2 coins', 'coins %d' % c)

def f_slot_rolls(q):  # owner 24 Nov: the wheels roll fast, then slow down and stop one after another (first, second, third), ticking as they pass and knocking as they stop
    pause_clock(q)
    table(q, bag=[[0, 4]] * 4, fast=False, coins=[3, 0], goods=K4, jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 0, 1])
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    stops, rolling_seen, ms, at = [None] * 3, False, 0, []
    while ms < 4000 and None in stops:
        skip(q, 100); ms += 100
        ws = sorted(drawn(q, 'wheel'), key=lambda d: d['n'])
        if ws and ws[0]['rolling']: at.append(ws[0]['at'])
        for k, w in enumerate(ws):
            rolling_seen = rolling_seen or w['rolling']
            if not w['rolling'] and stops[k] is None and rolling_seen: stops[k] = ms
    q.clock.resume(); h = q.evaluate("()=>__dg.sounds()")
    steps = [b - a for a, b in zip(at, at[1:])]; slows = len(steps) >= 4 and steps[0] > 3 * steps[-1] > 0
    ok = rolling_seen and None not in stops and stops[0] < stops[1] < stops[2] and stops[0] >= 500 and slows and h.count('roll') == 3 and h.count('stop') == 3
    report(ok, 'slot: wheels roll fast, slow down, stop one by one', 'stops at %s ms; first wheel moves %s per 100 ms; roll sounds %d, stop sounds %d' % (stops, [round(x, 1) for x in steps], h.count('roll'), h.count('stop')))

def f_slot_says_price(q):  # owner 24 Nov: "I can't even see what I pay", and then "no text; the slot machine should have none": price, prize and coins are pictures
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 1, 3]); waiting(q, 'slot'); tap(q, 'wheel-2')
    pics = {d['for']: d for d in drawn(q, 'pic')}; texts = drawn(q, 'label')
    ok = not texts and pics.get('reroll', {}).get('coins') == 1 and pics.get('collect', {}).get('faces') == ['coin', 'jar', 'g2'] and pics.get('coins', {}).get('n') == 3
    report(ok, 'slot: price, prize and coins as pictures, no text', 'texts %s, pictures %s' % ([t['text'] for t in texts], pics))

def f_slot_three(q):  # owner 24 Nov: pay 1 coin to respin chosen wheels; three the same double what you see
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot')
    tap(q, 'wheel-2'); tap(q, 'reroll'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); p = st(q)['players'][0]
    report(p['coins'] == 3 - 1 + 6, 'slot: respin costs a coin, three the same double', 'coins %d (3, paid 1, three coins doubled)' % p['coins'])

def f_slot_two(q):  # owner 24 Nov: you win what the 3 wheels show (each face several things); you can stop at any time
    get_jar(q, [{'k': 'slot'}], coins=0, slots=[0, 2, 3]); waiting(q, 'slot'); g0 = st(q)['players'][0]['goods']
    tap(q, 'collect'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); p = st(q)['players'][0]
    gained = [a - b for a, b in zip(p['goods'], g0)]  # 1 of each, and 5 of good 2: those 6 make a jar at once (owner 24 Nov)
    report(p['coins'] == 1 and gained == [1, 1, 1, 1, 1] and p['jars'] == 1, 'slot: win what you see', 'coins %d, goods gained %s, jars %d (1 of each, and 5 of good 2 that made a jar)' % (p['coins'], gained, p['jars']))

def f_slot_faces(q):  # owner 24 Nov: each wheel has 4 faces drawn at random (not every option on every wheel), and at least one face is on all three wheels
    seen, shared = set(), True
    for seed in range(1, 13):
        table(q, seed=seed, bag=[[0, 4]] * 4, goods=K4, jarQueue=[{'k': 'slot'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'slot')
        f = st(q)['slot']['faces']; seen.add(tuple(map(tuple, f))); shared = shared and bool(set(f[0]) & set(f[1]) & set(f[2])) and all(len(set(w)) == 4 for w in f)
    report(len(seen) > 6 and shared, 'slot: 4 random faces per wheel, one on all three', '%d different machines in 12, each with 4 faces and a shared one %s' % (len(seen), shared))

def f_steal(q):  # steal a PC tile: it is lifted where it lay and you place it; a tile with no place for you can't be stolen
    table(q, bag=[[0, 4]] * 4, goods=K4, tiles=[[14, 7, 0, 0, 0, 1], [14, 2, 0, 3, 3, 1]], jarQueue=[{'k': 'steal'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')
    blocked = q.evaluate("()=>!__dg.btn('steal-t2')"); spot = q.evaluate("()=>__dg.tileAt(14,7,0)"); tap(q, 'steal-t1'); waiting(q, 'place')
    h = held(q); lifted = abs(h[0] - spot[0]) < 2 and abs(h[1] - spot[1]) < 2
    drag_to(q, best_spot(q)); s = st(q); mine = [t[3:5] for t in s['tiles'] if t[5] == 0]; theirs = [t[3:5] for t in s['tiles'] if t[5] == 1]
    report(blocked and lifted and [0, 0] in mine and [0, 0] not in theirs, 'steal: tile moves to you, unfit one blocked', 'blocked %s, lifted there %s, mine %s' % (blocked, lifted, mine))

def f_stolen_tile_jars(q):  # owner 24 Nov: "I stole a tile and made 2 connections, and 5 jars appear": the jars a tile earns are shown apart from jars still waiting
    table(q, bag=[[0, 1]] * 4, goods=[[4, 4, 4, 4, 0], [0] * 5], tiles=[[6, 6, 0, 2, 3, 0], [14, 8, 0, 2, 3, 1]], jarQueue=[{'k': 'steal'}] + [COIN] * 8)  # the PC's [2, 3] fits under the kid's [2, 3]
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')  # 2 jars; the first steals; one waits
    tap(q, 'steal-t2'); waiting(q, 'place'); drag_to(q, {'x': 6, 'y': 7, 'r': 0}); waiting(q, 'jar')
    jars = drawn(q, 'jar'); new = sum(1 for j in jars if j.get('new'))
    report(len(jars) == 3 and new == 2, 'steal: 2 matches show 2 new jars apart', 'jars shown %d, new %d' % (len(jars), new))

def f_first_token(q):  # the first-player token comes from a jar
    get_jar(q, [{'k': 'first'}]); report(st(q)['first'] == 0, 'first: token comes to you', 'first %s' % st(q)['first'])

def f_free_tile(q):  # a free extra tile from nowhere, always one that fits, placed at once
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'place'); n0 = tile_count(q, 0); ok = len(st(q)['spots']) > 0; drag_to(q, best_spot(q))
    report(ok and tile_count(q, 0) == n0 + 1, 'tile: free tile fits and is placed', 'tiles %d -> %d' % (n0, tile_count(q, 0)))

def f_free_tile_from_jar(q):  # owner 24 Nov: "the bonus tile should not appear on the board, but marked as yours", and then "not on top of the deck: next to the 4 tiles of the market"
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'place'); h = held(q); m = drawn(q, 'market')[0]; mark = drawn(q, 'heldmark'); P = q.evaluate("()=>innerWidth*0.87")
    ok = m['x'] + m['w'] < h[0] < P and abs(h[1] - (m['y'] + m['h'] / 2)) < 5 and [x['o'] for x in mark] == [0]
    report(ok, 'free tile: beside the market, marked as yours', 'tile at %s, market from x %d to %d, marked for %s' % (h, m['x'], m['x'] + m['w'], [x['o'] for x in mark]))

def f_another_jar(q):  # another jar, which you open yourself
    get_jar(q, [{'k': 'jar'}, {'k': 'coins2'}]); waiting(q, 'jar'); c0 = st(q)['players'][0]['coins']
    tap(q, 'jar-0'); c1 = st(q)['players'][0]['coins']
    report(c1 == c0 + 2, 'jar: another jar to open', 'coins %d -> %d' % (c0, c1))

def f_free_set(q):  # a free set: one of each of the 5 goods (on top of the placed tile's own 2, owner 24 Nov)
    get_jar(q, [{'k': 'set'}]); g = st(q)['players'][0]['goods']
    report(g == [1, 1, 1, 1, 1], 'set: one of each good', str(g))

def f_borders(q):  # each player's land has a border all around: green for the kid, red for the PC; a tile is one rectangle, no gap between its halves
    table(q, bag=[[0, 4]] * 4); b = drawn(q, 'border'); kid = sum(1 for x in b if x['o'] == 0); pc = sum(1 for x in b if x['o'] == 1)
    seam = q.evaluate("()=>__dg.edge(4,6,0)"); mid = q.evaluate("(p)=>__dg.pixel(p[0]-1,p[1])", seam)
    ok = kid == 6 and pc == 6 and mid == [232, 197, 71, 255]
    report(ok, 'borders: all around each land, one rectangle', 'kid edges %d, pc edges %d, seam %s' % (kid, pc, mid))

MAIN_SEED, MAIN_JARS = 3, ['coins', 'empty', 'slot', 'steal', 'first', 'jar', 'tile', 'coins2', 'set']  # the main game's fixed pile (made by this seed) and the jar contents queued, in order
def f_main_game(q):  # owner 24 Nov: one main test plays a whole game with a fixed pile and fixed jar contents, so every situation happens in order; at each situation it checks that situation's rules, and after every move what he sees adds up
    out = q.evaluate("""async ([seed, kinds]) => {
      const cv = document.querySelector('canvas'), errs = [], did = {}, err = m => errs.push(m);
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { if (!p) { err('nothing to tap at ' + JSON.stringify(__dg.state().wait)); return; } __dg.render(); ev('pointerdown', p); ev('pointerup', p); await tick(); };
      const drag = async (a, b) => { if (!a || !b) { err('nothing to drag at ' + JSON.stringify(__dg.state().wait)); return; } __dg.render(); ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = kind => __dg.drawn().filter(d => d.k === kind), btn = id => { __dg.render(); return __dg.btn(id); };  // buttons are where the last picture put them: draw first
      const sum = a => a.reduce((x, y) => x + y, 0), DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
      __dg.restart({ seed, fast: true, jarQueue: kinds.concat(kinds).map(k => ({ k })), slotQueue: [0, 0, 1, 0] }); await tick();
      { const s = __dg.state(), starts = s.tiles.map(t => t.slice(0, 5).join()).sort();  // the start: the same start tile for both, the two most common colours, at the centres of the board's halves; nobody has the token; the kid picks first
        if (starts.join('|') !== '14,6,0,0,1|4,6,0,0,1' || s.draft.length !== 4 || !s.wait || s.wait.kind !== 'pick' || s.wait.who !== 0 || s.first !== null) err('start: ' + JSON.stringify([starts, s.wait, s.first])); }
      let putBack = false, picked = -1, prev = __dg.state(), afterPass = 0;
      for (let step = 0; ; step++) {
        await tick(); const s = __dg.state(), w = s.wait; __dg.render();
        if (step > 4000 || errs.length > 5) { err('stuck at ' + JSON.stringify(w)); break; }
        for (const o of [0, 1]) if (seen('coin').filter(d => d.o === o).length !== s.players[o].coins) err('round ' + s.round + ': coins shown for ' + o + ' differ');
        if (s.over) {  // the end: no tile left can be placed by either player (none thrown); most coins wins, his star shown
          const [a, b] = s.players.map(p => p.coins), win = a > b ? 0 : b > a ? 1 : -1, star = seen('winner');
          if (s.leftFits) err('end: a tile left still fits');
          if (s.winner !== win || (win >= 0 && (star.length !== 1 || star[0].o !== win))) err('end: winner ' + s.winner + ' for coins ' + [a, b]);
          did.end = true; break;
        }
        if (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left !== 40) err('a tile was thrown away: board, hand and left make ' + (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left));  // no tile is ever thrown: not when he passes, not at the round's end (the tile in hand counts)
        for (const o of [0, 1]) for (let c = 0; c < 5; c++) if (seen('good').filter(d => d.o === o && d.c === c).length !== s.players[o].goods[c]) err('round ' + s.round + ': goods shown differ for ' + o);
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
          const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), held = __dg.drawn().find(e => e.id === 'held').cs, d = DIRS[sp.r];  // matching edges with any land, counted on the board shown
          let edges = 0; [[sp.x, sp.y], [sp.x + d[0], sp.y + d[1]]].forEach(([x, y], h) => DIRS.forEach(([dx, dy]) => { const n = at(x + dx, y + dy); if (n && n.c === held[h]) edges++; }));
          const g0 = sum(s.players[0].goods);
          await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)); __dg.render();
          const t = __dg.state(), g = seen('good').filter(d => d.o === 0).length, jars = t.players[0].jars - s.players[0].jars;  // his new jars wait for his taps  // one good per matching edge, with any land; each 5 of a colour a jar at once
          if (g + 5 * jars !== g0 + edges || t.players[0].goods.some(x => x >= 5)) err('round ' + s.round + ': ' + edges + ' matching edges, goods ' + g0 + ' -> ' + g + ' and ' + jars + ' jars');
        }
        else if (w.kind === 'jar') { const n = s.players[0].jars; await tap(btn('jar-0')); if (__dg.state().players[0].jars >= n) did.moreJars = true; }  // a jar that brings another jar, or goods that make one
        else if (w.kind === 'steal') { did.steal = true; await tap(btn(__dg.buttons().find(b => b.startsWith('steal-')))); }
        else if (w.kind === 'slot') { did.slot = true; await tap(btn(s.players[0].coins && !did.reroll ? 'wheel-2' : 'collect')); if (__dg.state().slot && __dg.state().slot.sel[2]) { did.reroll = true; await tap(btn('reroll')); } }
      }
      return { errs: errs.slice(0, 5), did, left: __dg.state().queued };
    }""", [MAIN_SEED, MAIN_JARS])
    want = ['unusable', 'pass', 'putBack', 'bonusTile', 'steal', 'slot', 'reroll', 'moreJars', 'end']
    missing = [k for k in want if not out['did'].get(k)]
    report(not out['errs'] and not missing and out['left'] == 0, 'main game: every situation, what he sees adds up', 'missing %s, errors %s, jar contents left %s' % (missing, out['errs'], out['left']))

def f_random_play(q):  # seeded games played through the screen (taps and drags on what is drawn, at random moments); after every move, what he can see holds:
    # the goods a placement gives match its matching edges on the board shown, each 5 of a colour a jar at once
    bad = q.evaluate("""async () => {
      const cv = document.querySelector('canvas'), ch = new MessageChannel(), errs = [];
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };  // let the game's answers run (they are promise steps in fast mode); no timer, no message: those wait for the browser
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { ev('pointerdown', p); ev('pointerup', p); await tick(); };  // the game answers after the event: wait for it
      const drag = async (a, b) => { ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = kind => __dg.drawn().filter(d => d.k === kind);
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
            const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), d = [[1, 0], [0, 1], [-1, 0], [0, -1]][sp.r], cs = [__dg.drawn().find(e => e.id === 'held').cs[0], __dg.drawn().find(e => e.id === 'held').cs[1]];
            const hs = [[sp.x, sp.y], [sp.x + d[0], sp.y + d[1]]]; let edges = 0;
            hs.forEach(([x, y], h) => [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const n = at(x + dx, y + dy); if (n && n.c === cs[h]) edges++; }));
            const g0 = s.players[0].goods.reduce((a, b) => a + b, 0);
            await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)); __dg.render();
            const g = seen('good').filter(d => d.o === 0).length, jars = __dg.state().players[0].jars - s.players[0].jars;  // his new jars wait for his taps
            if (g + 5 * jars !== g0 + edges) errs.push('seed ' + seed + ': ' + edges + ' matching edges on the board, goods ' + g0 + ' -> ' + g + ' and ' + jars + ' jars');
          }
          else if (w.kind === 'jar') await tap(btn('jar-0'));
          else if (w.kind === 'steal') { const ids = __dg.buttons().filter(b => b.startsWith('steal-')); await tap(btn(ids[rand(ids.length)])); }
          else if (w.kind === 'slot') await tap(btn('collect'));
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
