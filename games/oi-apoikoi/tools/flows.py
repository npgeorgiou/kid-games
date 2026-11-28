# Flow tests: what the owner does, in the running game: real page, real mouse taps and drags on what he sees.
# One browser and one page for the whole run: each flow starts a new game with a set table (fast: the PC's hand moves without waiting)
# and prints PASS or FAIL, [its flow name], what it checks, and what was seen. Waits are on the game's state, never on a fixed sleep.
# Colours are numbered 0-5 (0 and 1 the most common); a tile is [first half, second half]; the board is 16 x 16 squares, the start tiles [0, 1] at (4, 10) turned 0 (the kid's) and (11, 5) turned 2 (the PC's: the kid's turned half a turn).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'empty'}, {'k': 'coins'}, {'k': 'coins2'}, {'k': 'changer'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib, datetime, math, re, json
from playwright.sync_api import sync_playwright
GAME = next((pathlib.Path(__file__).resolve().parent.parent).glob('*.html'))  # this copy's own built page (whatever its name then), so old and new code can be tested at once
COIN = {'k': 'coins'}
NOW = ['']  # the flow running, for the report lines
EDGE_GOODS = 1200  # ms: longer than the goods of a placed tile take to fly out of their edges
WAIT = 1500  # ms: the game answers in a few ms in fast mode, so a flow that waits longer has failed; short waits keep failing runs short

# SECTION: HELPERS -- the page, a set table, taps and drags on what is drawn, the game's state
def settle(q): q.evaluate("()=>__dg.render()")  # the game answers a tap at once; draw it now, so what is on screen (and its buttons) is current
SETTINGS = json.loads((pathlib.Path(__file__).parent / 'test-settings.json').read_text())  # the test game's settings (deck: tiles in the pile, a short game; owner 28 Nov)
def table(q, **opts):  # a new game on a set table (goods=[kid's, PC's]: the goods each player has saved)
    opts.setdefault('deck', SETTINGS['deck'])
    opts.setdefault('fast', True); opts.setdefault('seed', 1)  # always seeded: a flow never depends on luck
    opts.setdefault('changer', [-1, None])  # owner 28 Nov: the land changer; the PC's would change the board on its first move, so only the flows about it give the PC one
    if opts['fast']: pause_clock(q)  # a fast game needs no time to pass; a running clock draws 60 frames a second for nothing
    q.evaluate("(o)=>__dg.restart(o)", opts); settle(q)
    if not opts['fast']: run_until(q, "()=>!!__dg.state().wait")  # through the round's morning light, to the first pick
def skip(q, ms):  # move the paused fake clock on: every timer in that time runs, in order; the test page draws no frames, so it costs only the game's own steps
    q.clock.run_for(ms); settle(q)
def run_until(q, cond, limit=4000):  # move the paused fake clock on in short steps until the game is in the state asked; a picture is drawn only when the condition looks at one
    look = "()=>{%s; return (%s)()}" % ('__dg.render()' if 'drawn' in cond or 'btn' in cond else '', cond)
    for _ in range(limit // 100):
        if q.evaluate(look): break
        q.clock.run_for(100)
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
K3 = [[3, 0, 0, 0, 0, 0], [0] * 6]  # the kid has 3 goods of colour 0: a [0, 4] tile left of the start tile lights 2 more, and the 5 make a jar
def open_jars(q, who=0):  # he breaks every jar waiting, one after another, until it is his turn to pick again
    for _ in range(40):
        s = st(q)['wait']
        if s and s['kind'] == 'pick' and s['who'] == who: return
        if s and s['kind'] == 'jar' and s['who'] == who: tap(q, 'jar-0')
        else: skip(q, 100)
def get_jar(q, contents, coins=0, **more):  # place a tile with one connection: its jar; open it
    table(q, bag=[[0, 4]] * 4, coins=[coins, 0], jarQueue=contents + [COIN] * 8, **more)
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
    table(q, deck=None); s = st(q); rows = sorted({d['c'] for d in drawn(q, 'place') if d['o'] == 0})  # the whole pile
    report(s['halves'] == [10, 10, 9, 9, 9, 9] and s['left'] == 28 and rows == list(range(6)), 'colours: 6, 28 tiles, halves 10/10/9/9/9/9', '%s, %d tiles, goods rows %s' % (s['halves'], s['left'], rows))
def f_first_round_fits(q):  # owner 24 Nov: of the first round's 4 tiles, 2 surely fit (one for each player); the other 2 are truly random
    fits, unfit_seen, places = [], 0, set()
    for seed in range(1, 41):
        table(q, seed=seed); f = st(q)['fits']; fits.append(sum(f)); unfit_seen += f.count(False); places.add(tuple(k for k, v in enumerate(f) if v))
    ok = min(fits) >= 2 and unfit_seen > 0 and len(places) > 1
    report(ok, 'first round: 2 surely fit, 2 random', 'fewest fitting %d, tiles that fit nowhere in 40 games %d, fitting tiles in %d different places' % (min(fits), unfit_seen, len(places)))

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_tap_turns(q):  # tap the won tile where it lies (in the top row) to turn it
#     table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h = held(q)
#     q.mouse.click(h[0], h[1]); settle(q); r1 = st(q)['wait']['r']; q.mouse.click(h[0], h[1]); settle(q)
#     report(r1 == 1 and st(q)['wait']['r'] == 2, 'tile: a tap turns it where it lies', 'turns %d then %d' % (r1, st(q)['wait']['r']))
#
def f_drag_place(q):  # drag the tile from the top row; it snaps in as one tile; no squares are drawn around the land, no tray
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
    ids = q.evaluate("()=>__dg.buttons()"); marks = [b for b in ids if b.startswith('spot') or b == 'tray']
    drag_to(q, {'x': 3, 'y': 10, 'r': 2}); mine = [t for t in st(q)['tiles'] if t[5] == 0 and t[:5] == [3, 10, 2, 0, 4]]
    report(not marks and len(mine) == 1, 'place: dragged tile snaps in', 'extra marks %s, placed %s' % (marks, mine))

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_drag_from_pile(q):  # owner 24 Nov: no tap first: press a tile in the pile and drag it straight to its place; a plain tap still just takes it, unturned
#     table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8)
#     path(q, q.evaluate("()=>__dg.btn('draft-0')"), q.evaluate("()=>__dg.tileAt(4,9,0)"))
#     placed = [4, 9, 0, 0, 4] in [t[:5] for t in st(q)['tiles'] if t[5] == 0]
#     table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); w = st(q)['wait']
#     report(placed and (w['kind'], w['who'], w['r']) == ('place', 0, 0), 'pile: drag straight from the pile', 'placed %s; after a tap %s' % (placed, w))
#
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

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_drag_leave(q):  # drag, leave it anywhere, turn it there, drag again: it is placed only when it snaps
#     table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place')
#     far = q.evaluate("()=>__dg.tileAt(9,1,0)"); path(q, held(q), far); h1 = held(q); left = h1 is not None and abs(h1[0] - far[0]) < 2 and abs(h1[1] - far[1]) < 2
#     q.mouse.click(h1[0], h1[1]); settle(q); turned = st(q)['wait']['r'] == 1
#     mid = q.evaluate("()=>__dg.tileAt(9,9,1)"); path(q, held(q), mid); still = st(q)['wait']['kind'] == 'place' and tile_count(q, 0) == 1
#     drag_to(q, {'x': 3, 'y': 10, 'r': 2})
#     report(left and turned and still and tile_count(q, 0) == 2, 'tile: left anywhere until it snaps', 'left %s turned %s still %s tiles %d' % (left, turned, still, tile_count(q, 0)))
#
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_snap_preview(q):  # before it snaps the place is shown; far from any place nothing is shown
#     table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place')
#     goal = q.evaluate("()=>__dg.tileAt(4,9,0)"); path(q, held(q), [goal[0] + 8, goal[1] + 6], up=False); near = st(q)['snap']; ghost = len([d for d in drawn(q, 'tile') if d['look'] == 'ghost'])
#     far = q.evaluate("()=>__dg.tileAt(9,0,0)"); q.mouse.move(far[0], far[1]); settle(q); away = st(q)['snap']; q.mouse.up(); settle(q)
#     ok = near == {'x': 4, 'y': 9, 'r': 0} and ghost == 1 and away is None and st(q)['wait']['kind'] == 'place'
#     report(ok, 'snap: place shown before it snaps', 'near %s ghost %d, away %s' % (near, ghost, away))
#
def f_own_land(q):  # a tile must have a matching edge with your own land; matching only the PC's land is not enough
    table(q, bag=[[2, 4], [0, 4], [0, 4], [0, 4]], tiles=[[9, 3, 0, 2, 2, 1]]); s = st(q)
    report(s['fits'][0] is False and q.evaluate("()=>!__dg.btn('draft-0')"), 'match: must be with your own land', 'fits %s' % s['fits'])

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_pile_no_frames(q):  # owner 24 Nov: no outline around the pile's tiles
#     table(q, bag=[[0, 4]] * 4); c = q.evaluate("()=>__dg.btn('draft-0')"); hw = (q.evaluate("()=>__dg.btnBox('draft-0')")['w'] - 24) / 3; m = drawn(q, 'market')[0]
#     hh = hw / 3 ** 0.5; beside = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [c[0] - 1.5 * hw - 6, c[1] - hh / 2])  # just left of the tile's left corner (its walls hang below it): the market tray's own colour, not a frame
#     tray = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [m['x'] + 12, m['y'] + m['h'] - 12])  # the tray, away from the tile
#     report(beside == tray, 'pile: tiles have no outline', 'beside the tile %s, the tray %s' % (beside, tray))
#
def f_pile_fits(q):  # owner 24 Nov ("rethink all UI"): the pile ran off the top of the screen; owner 25 Nov: the pile holds every tile;
    # owner 27 Nov changed the layers (was: a layer per tile): a layer per round (of 4 tiles), each half a tile's height (a tile's ground is its full height: owner 27 Nov), layer lines kept; its base on its stone
    table(q); settle(q); pile = drawn(q, 'pile')[0]; s = st(q); in_pile = s['left'] - sum(1 for t in s['draft'] if t); ground = {round(d['ground'], 1) for d in drawn(q, 'square')}
    stone = max(p[1] for d in drawn(q, 'area') if d['o'] == 0 and d['kind'] == 'deck' for p in d['pts'])
    rounds = -(-in_pile // 4); g = ground.pop() if len(ground) == 1 else -1
    ok = pile['layers'] == rounds and abs(pile['step'] - g / 2) < 0.5 and pile['lines'] == rounds - 1 and pile['bottom'] <= stone
    report(ok, 'pile: a layer per round, half a tile high, on its stone', '%d layers for %d tiles, %.1f px each (a tile %.1f high), %d lines, base at %.0f (stone to %.0f), top at %.0f' % (pile['layers'], in_pile, pile['step'], g, pile.get('lines', -1), pile['bottom'], stone, pile['y']))
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
    quiet = 0
    while ms < 6000:
        skip(q, 50); ms += 50; d = drawn(q, 'flight'); glows = max(glows, len(drawn(q, 'edgeglow')))
        order += [at[(round(x['fx']), round(x['fy']))] for x in d if x['look'] == 'good' and (round(x['fx']), round(x['fy'])) in at and at[(round(x['fx']), round(x['fy']))] not in order]
        drops = max(drops, sum(1 for x in d if x['look'] == 'jar' and x['fy'] < 0))
        w = st(q)['wait']
        quiet = quiet + 50 if w and w['kind'] == 'jar' and not drawn(q, 'flight') else 0
        if quiet >= 1000: break  # all in: nothing has moved for a second (owner 28 Nov: he may break full jars while the rest still come)
    p = st(q)['players'][0]; q.clock.resume()
    ok = glows == 1 and order == land and p['goods'][0] == 1 and p['jars'] == 2 and drops >= 1
    report(ok, 'connections: a jar each; the connected land lights up', 'edges glowing %d; materials from %s; goods %s; jars %d; jars dropping from the top at once %d' % (glows, order, p['goods'], p['jars'], drops))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_five_make_jar(q):  # owner 24 Nov: 5 goods of one colour become a jar at once (not at the round's end) and it is opened at once; the jar comes to its place first, then the goods fly into it on curves, one by one
#     pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=K3, jarQueue=[COIN] * 8)
#     tap(q, 'draft-0'); waiting(q, 'place'); P = stock_edge(q); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); drops, intos, ms = [], [], 0
#     while ms < 4000:
#         skip(q, 50); ms += 50; d = q.evaluate("()=>__dg.drawn().filter(d=>d.k==='flight')")
#         drops += [(ms, x) for x in d if x['look'] == 'jar']; intos += [(ms, x) for x in d if x['look'] == 'good' and x['fx'] < P]  # goods leaving the stockpile
#         w = st(q)['wait']
#         if w and w['kind'] == 'jar': break
#     s = st(q); jar = [x for x in drawn(q, 'jar') if x['o'] == 0]; left = [x for x in drawn(q, 'good') if x['o'] == 0]; tap(q, 'jar-0')
#     run_until(q, "()=>__dg.state().players[0].coins===1"); coins = st(q)['players'][0]['coins']; q.clock.resume()
#     into = [(m, x) for m, x in intos if any(abs(x['tx'] - j['x']) < 5 for j in jar)]; targets = {round(x['tx']) for _, x in into}  # the 2 lit goods make 5: they fly into one jar (the connection's jar is the other)
#     first = bool(drops) and bool(into) and into[0][0] > drops[-1][0]  # the jar is in its place before any good flies into it
#     ok = bool(drops) and drops[0][1]['fy'] < 0 and len(jar) == 2 and len(targets) == 1 and first and len({(round(x['fx']), round(x['fy'])) for _, x in into}) == 5 and any(x['y'] < min(x['fy'], x['ty']) - 10 for _, x in into) \
#         and not left and s['round'] == 1 and s['phase'] == 'round' and s['wait']['who'] == 0 and coins == 1
#     report(ok, 'jars: 5 of a colour make a jar at once, opened at once', 'jar from the top %s, in place first %s, goods into it from %d places, goods left %d, round %d %s, opened for a coin %s' % (bool(drops) and drops[0][1]['fy'] < 0, first, len({(round(x['fx']), round(x['fy'])) for _, x in into}), len(left), s['round'], s['phase'], coins == 1))
#
def f_no_bidding(q):  # owner 24 Nov: no bidding (too slow: every pick triggered it): the player whose turn it is takes the tile he picks
    kid, pc = [[4, 8, 0, 2, 3, 0], [4, 6, 0, 4, 4, 0]], [[12, 4, 0, 2, 3, 1], [12, 2, 0, 4, 4, 1]]
    table(q, bag=[[0, 1], [0, 0], [0, 0], [0, 0]], tiles=kid + pc, goods=[[1] * 6, [1] * 5]); tap(q, 'draft-0'); w = st(q)['wait']; s = st(q)
    ok = w['kind'] == 'place' and w['who'] == 0 and s['players'][1]['goods'] == [1] * 5 and not drawn(q, 'bidcard') and 'bid' not in q.evaluate("()=>__dg.sounds()")
    report(ok, 'pick: the tile is yours, no bid', 'after the pick: %s, PC goods %s, bid card %s' % (w, s['players'][1]['goods'], bool(drawn(q, 'bidcard'))))

NECK = 0.02  # owner 28 Nov: below the rim's top a good goes straight down: at most this share of the jar's width off the neck's middle
def f_goods_into_neck(q):  # owner 27 Nov: "the goods that go into jars now, dont drop in correctly, they drop in while kind of colliding with the neck of the jar. their fly curve must be higher."
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=K3, jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); hits, seen, ms = [], 0, 0
    while ms < 4000:
        skip(q, 25); ms += 25
        for d in drawn(q, 'flight'):
            if d['look'] != 'good' or not d['rim']: continue
            m = d['rim']; seen += 1; low = d['y'] + d['r'] > m['y']  # its bottom is below the rim's top
            if low and NECK * m['w'] < abs(d['x'] - d['tx']) < 0.6 * m['w']: hits.append((round(d['x'] - d['tx']), round(d['y'] + d['r'] - m['y'])))  # owner 28 Nov: "still A TINY BIT hitting its rim": below the rim's top it falls straight in
    report(seen > 5 and not hits, 'goods: drop into the jar\'s neck from above, clear of it', '%d positions seen, past the neck\'s opening below its top %s' % (seen, hits[:6]))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_material_lines(q):  # owner 25 Nov (prototype): materials come in a line per colour, so a colour never waits for another's jar; a full row's jar drops while its 5th flies; lit squares light 120 ms apart
#     pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, goods=[[4, 0, 0, 0, 0, 0], [0] * 6], jarQueue=[COIN] * 8); gap = q.evaluate("()=>__dg.gaps().lit")
#     tap(q, 'draft-0'); waiting(q, 'place'); P = stock_edge(q); drag_to(q, {'x': 4, 'y': 11, 'r': 0})  # 2 connections: colour 0 lights 2 squares (4 + 2: a jar), colour 1 lights 2
#     starts, ms, drops = {}, 0, []  # drops: each jar dropping from the top, and whether a colour 0 good was flying from the board when it set off
#     while ms < 3000:
#         skip(q, 20); ms += 20; d = drawn(q, 'flight'); board = [x for x in d if x['look'] == 'good' and x['fx'] > P]
#         for x in board: starts.setdefault((round(x['fx']), round(x['fy'])), (ms, x['c']))
#         for x in d:
#             if x['look'] == 'jar' and x['fy'] < 0 and round(x['tx']) not in [t for t, _ in drops]: drops.append((round(x['tx']), any(g['c'] == 0 for g in board)))
#         w = st(q)['wait']
#         if w and w['kind'] == 'jar': break
#     q.clock.resume(); order = sorted(starts.values()); c0 = [t for t, c in order if c == 0]; c1 = [t for t, c in order if c == 1]
#     while_flying = [f for _, f in drops]  # 2 connections' jars and the full row's jar
#     ok = len(c0) == 2 and len(c1) == 2 and c1[0] < c0[1] and abs((c1[1] - c1[0]) - gap) <= 40 and while_flying == [True] * 3
#     report(ok, 'materials: a line per colour; the jar drops while the 5th flies; lit squares apart', 'colour 0 goods leave at %s ms, colour 1 at %s ms (lit gap %d); full row\'s jar dropping while its 5th flies %s' % (c0, c1, gap, while_flying))
#
def f_row_never_overflows(q):  # owner 24 Nov: a row never needs more than 5 places: a tile giving 2 goods to a row of 4 fills it, the 5 fly into a jar, and the 6th good takes the first place
    pause_clock(q); table(q, fast=False, bag=[[0, 0]] * 4, tiles=[[4, 11, 0, 0, 0, 0]], goods=[[4, 0, 0, 0, 0, 0], [0] * 6], jarQueue=[COIN] * 8)
    xs = sorted(x['x'] for x in drawn(q, 'place') if x['o'] == 0 and x['c'] == 0); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 1}); most, targets, ms = 0, set(), 0  # 2 connections lighting 5 squares of colour 0: 4 + 5 goods
    quiet = 0
    while ms < 5000:
        skip(q, 50); ms += 50; most = max(most, sum(1 for x in drawn(q, 'good') if x['o'] == 0 and x['c'] == 0))
        targets |= {round(x['tx']) for x in drawn(q, 'flight') if x['look'] == 'good' and x['fx'] > xs[-1] + 40}  # goods flying from the board to the stockpile
        w = st(q)['wait']
        quiet = quiet + 50 if w and w['kind'] == 'jar' and not drawn(q, 'flight') else 0
        if quiet >= 1000: break  # all in: nothing has moved for a second (owner 28 Nov: he may break full jars while the rest still come)
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
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'pick'); a = [n for n in q.evaluate("()=>__dg.sounds()") if n not in ('dawn', 'deal', 'turn', 'into', 'beefly')]  # the morning, the deal, the turn, the goods going into a jar and the bee have their own flows
    want = ['pick', 'rotate', 'snap', 'splash', 'edge', 'jarland', 'edge', 'jar', 'reveal', 'extrain']  # owner 28 Nov: the extra tile lands in its place
    ok = a[:len(want)] == want
    report(ok, 'sounds: one for each thing, in order', 'tile jar: %s, heard %s' % (a[:len(want)], sorted(set(a))))

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_sound_kinds(q):  # owner 24 Nov: "a weird blip when I tap a piece"; "jars must make a breaking sound": a tap knocks like wood, a jar breaks like clay, a coin clinks; no beeps anywhere
#     get_jar(q, [COIN]); settle(q); h = [k for n, k in zip(q.evaluate("()=>__dg.sounds()"), q.evaluate("()=>__dg.heardKinds()")) if n not in ('dawn', 'deal', 'turn', 'into', 'made')]  # the morning, the deal, the turn sound and the jar being made have their own flows
#     ok = h[:6] == ['knock', 'knock', 'chime', 'chime', 'break', 'clink']  # tap, snap, a material out of each of the 2 lit squares, the jar opened, its coin
#     ok = ok and set(q.evaluate("()=>__dg.soundKinds()")) <= {'break', 'chime', 'clink', 'knock', 'whoosh'}
#     report(ok, 'sounds: wood tap, clay break, coin clink', 'heard %s; kinds in the game %s' % (h[:6], q.evaluate("()=>__dg.soundKinds()")))
#
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_many_jars_rows(q):  # owner 24 Nov: "when a lot of jars exist, make more rows, 6 jars per row; don't reduce their size"
#     table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); one = drawn(q, 'jar')[0]['size']  # one jar alone: its size
#     table(q, bag=[[0, 1]] * 4, tiles=[[3, 11, 1, 0, 0, 0], [6, 11, 1, 1, 1, 0], [4, 12, 0, 0, 1, 0]], jarQueue=[COIN] * 20)  # owner 28 Nov: no slot machine: a tile meeting 6 edges lights 5 squares of each colour: 8 jars
#     tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); waiting(q, 'jar'); jars = drawn(q, 'jar')
#     rows = {}; [rows.setdefault(j['row'], []).append(j) for j in jars]
#     W, H = q.evaluate("()=>[innerWidth, innerHeight]")
#     ok = len(jars) == 8 and max(len(r) for r in rows.values()) == 6 and all(abs(j['size'] - one) < 0.5 for j in jars) and all(0 < j['y'] - j['size'] / 2 and j['y'] + j['size'] / 2 < H for j in jars)
#     report(ok, 'jars: 6 to a row, more rows, same size', '%d jars in rows of %s, sizes %s (one alone %.0f)' % (len(jars), [len(r) for r in rows.values()], sorted({round(j['size']) for j in jars}), one))
#
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_many_coins(q):  # owner 24 Nov: "make sure more coins than you predicted can fit"; coins easy to count and apart; owner 25 Nov (design 3): rows of at most 8 from the bottom of
#     # his bottom triangle; past what it holds at full size (160 found by the main game) they shrink but stay apart, clear of the board and of his materials
#     out = {}; W, H = q.evaluate("()=>[innerWidth, innerHeight]")
#     for n in (12, 160):
#         table(q, bag=[[0, 4]] * 4, coins=[n, 0], goods=[[4] * 6, [0] * 6]); dm = diamond(q); c = [x for x in drawn(q, 'coin') if x['o'] == 0]; pl = [x for x in drawn(q, 'place') if x['o'] == 0]
#         inside = all(x['x'] - x['r'] > 0 and x['x'] < W / 2 and x['y'] + x['r'] < H and off_board(dm, x['x'], x['y'], x['r']) for x in c)
#         rows = sorted({round(x['y']) for x in c}, reverse=True); per = [sum(1 for x in c if round(x['y']) == y) for y in rows]
#         out[n] = (len(c) == n and inside and min_gap(c) >= 1 and min_gap(c + pl) >= 1 and max(per) <= 8 and all(a >= b for a, b in zip(per, per[1:])), len(c), inside, round(min_gap(c), 1), per[:4], round(c[0]['r'], 1), round(pl[0]['r'], 1))
#     report(all(v[0] for v in out.values()) and out[12][-1] == out[12][-2] > out[160][-2], 'coins: all fit, apart, rows of at most 8', str(out))  # a few coins at full size (a material's), many smaller
#
def f_jars_apart(q):  # owner 24 Nov: "jar circles are touching": every jar stands apart, with a clear gap; owner 25 Nov: no glow
    table(q, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); waiting(q, 'jar'); settle(q)
    jars = sorted((d['x'], d['size'] / 2) for d in drawn(q, 'jar')); gaps = [b[0] - a[0] - a[1] - b[1] for a, b in zip(jars, jars[1:])]; glows = drawn(q, 'jarglow')
    ok = len(jars) == 2 and min(gaps) >= 12 and not glows
    report(ok, 'jars: apart, with a gap between them, no glow', 'gaps between jars %s px, glows %d' % ([round(g) for g in gaps], len(glows)))

def f_jar_lines(q):  # owner 25 Nov (prototype): jars stand in lines of up to 6, each line centred on its jars; a broken jar leaves its place empty;
    # a new jar takes the first free place and the others slide to keep the line centred
    W = q.evaluate("()=>innerWidth"); centred = lambda xs: abs((min(xs) + max(xs)) / 2 - W / 2) < 1
    def two_jars(first):  # a tile meeting 2 edges: 2 jars; the first one opened holds first
        table(q, bag=[[0, 1]] * 4, jarQueue=[{'k': first}] + [COIN] * 20)
        tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); waiting(q, 'jar'); settle(q); return sorted((d['x'], d['slot']) for d in drawn(q, 'jar'))
    two = two_jars('empty'); tap(q, 'jar-0'); waiting(q, 'jar'); settle(q); left = [(d['x'], d['slot']) for d in drawn(q, 'jar')]
    two_jars('jar'); tap(q, 'jar-0'); waiting(q, 'jar'); run_until(q, "()=>!__dg.drawn().some(d=>d.rising)"); settle(q); jars = sorted((d['x'], d['slot']) for d in drawn(q, 'jar'))  # owner 28 Nov: no slot machine: a jar in a jar takes the first free place
    ok = [k for _, k in two] == [0, 1] and centred([x for x, _ in two]) and left == [two[1]] and [k for _, k in jars] == [0, 1] and centred([x for x, _ in jars])
    report(ok, 'jars: lines centred; broken leaves its place; new takes the first free one', 'two jars %s; after breaking the first %s; after a jar in a jar %s' % ([(round(x), k) for x, k in two], [(round(x), k) for x, k in left], [(round(x), k) for x, k in jars]))
def f_round_end_shown(q):  # owner 24 Nov: the round's end is its own moment, seen and heard, before anything else happens in it; leftover market tiles fly back to the pile
    # owner 27 Nov: "remove night animation, but strengthen the day animation": no evening any more (it fell from the top with a moon and stars)
    pause_clock(q); table(q, fast=False, bag=[[2, 2], [3, 3]], tiles=[[4, 11, 0, 2, 2, 0], [4, 12, 0, 2, 2, 0]], jarQueue=[COIN] * 8)  # [3, 3] fits nobody: both pass, it is left in the market
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 13, 'r': 0})
    for _ in range(4):  # his jars (a connection's, and one of 5 lit goods)
        run_until(q, "()=>{const s=__dg.state();return s.phase==='end'||(s.wait&&s.wait.kind==='jar')}", 8000); w = st(q)['wait']
        if not (w and w['kind'] == 'jar'): break
        tap(q, 'jar-0')
    for _ in range(80):
        if st(q)['phase'] == 'end': break
        skip(q, 200)
    pile = drawn(q, 'pile')[0]; back, night, ms, coins = [], 0, 0, None
    while ms < 6000 and coins is None:
        skip(q, 100); ms += 100; d = q.evaluate("()=>__dg.drawn()")
        back += [(ms, x) for x in d if x['k'] == 'flight' and x['look'] == 'tile']; night += len([x for x in d if x['k'] in ('dusk', 'moon', 'skystar')])
        if [x for x in d if x['k'] == 'flight' and x['look'] == 'coin']: coins = ms  # the game's end begins: its coins fly
    q.clock.resume(); h = q.evaluate("()=>__dg.sounds()")
    returned = bool(back) and abs(back[0][1]['tx'] - pile['x']) < 5 and coins is not None; gap = coins - back[-1][0] if returned else 0
    report(returned and gap >= 1000 and not night and 'roundend' in h, 'end: tiles back to the pile, its own moment, no night', 'leftover tile flew back to the pile %s; then %d ms before the next thing; night drawn %d times; sound %s' % (returned, gap, night, 'roundend' in h))
def f_clock_sounds(q):  # owner 28 Nov: his grandfather clock files: "ticking = turn change, chime = round change"; "the turn and round must pass AFTER all animations
    # (hand, ruby, changer tile/extra tile moving to its place, anything) ... all turn is finished, then half a second passes, then the new turn starts (with a clock tick sound),
    # then half a second more delay, then the enemy starts its actions"; "the chime sound should correspond with the light"; "the enemy sometimes breaks jars BEFORE all their materials have flown inside"
    pause_clock(q); n = 6
    table(q, fast=False, first=1, bag=[[0, 1], [0, 0], [0, 4], [0, 4]], goods=[[0] * n, [4] * n], jarQueue=[{'k': 'set'}] + [COIN] * 12)
    g, files = q.evaluate("()=>__dg.gaps()"), q.evaluate("()=>__dg.soundFiles()")
    look = "()=>{const d=__dg.drawn(),jars=d.filter(j=>j.k==='jar'),filling=jars.filter(j=>d.some(f=>f.k==='flight'&&f.rim&&Math.abs(f.rim.x-j.x)<5)).map(j=>j.o+':'+j.slot);return {jars:jars.map(j=>j.o+':'+j.slot),filling,now:performance.now(),ends:d.filter(f=>f.k==='flight').map(f=>f.end).concat([__dg.state().hand.end]),hand:[__dg.state().hand.x,__dg.state().hand.y],heard:__dg.heardAt(),turn:__dg.state().turn,round:__dg.state().round,phase:__dg.state().phase,wait:__dg.state().wait}}"
    motions, hand, ticks, pc_moved, ends, early, filling = [], None, [], {}, [], [], []  # ends: per tick, the last motion before it; early: jars gone while their materials still flew in
    def watch():
        nonlocal hand, filling
        v = q.evaluate(look)
        early.extend(j for j in filling if j not in v['jars'] and any(k.split(':')[0] == j.split(':')[0] for k in v['jars']))  # only one player's jars are drawn at a time; filling = v['filling']
        motions.extend(v['ends'])  # when each thing seen moving ends (its own end time, so the polls can be far apart)
        hand = v['hand']; return v
    v = watch(); seen = len(v['heard'])
    for _ in range(300):
        at = v['heard']
        for name, t in at[seen:]:
            if name in ('turn', 'tilesback', 'roundend'): ends.append((name, t, max((m for m in motions if m <= t), default=None)))
            if name == 'turn': ticks.append(t)
        seen = len(at)
        if v['round'] > 1: break
        w = v['wait']
        if w and w['who'] == 1 and ticks and len(ticks) not in pc_moved and v['hand'] != hand_at_tick: pc_moved[len(ticks)] = v['now'] - ticks[-1]
        if w and w['who'] == 0 and w['kind'] == 'pick': tap(q, 'draft-%d' % st(q)['fits'].index(True))
        elif w and w['who'] == 0 and w['kind'] == 'place': drag_to(q, best_spot(q))
        elif w and w['who'] == 0 and w['kind'] == 'jar' and q.evaluate("()=>__dg.btn('jar-0')"): tap(q, 'jar-0')
        else: skip(q, 200)
        if ticks and len(ticks) not in pc_moved and (not w or w['who'] != 1): hand_at_tick = v['hand']
        v = watch()
    at = q.evaluate("()=>__dg.heardAt()"); q.clock.resume(); names = [x[0] for x in at]
    calm = [round(t - m) for _, t, m in ends if m is not None]  # from the last motion to the tick or the round's end
    ruby = [t for nm, t in at if nm == 'rubyin']; tick_after_ruby = [t for t in ticks if ruby and t > ruby[0]]
    ruby_ok = bool(ruby) and bool(tick_after_ruby) and tick_after_ruby[0] - ruby[0] >= g['ruby'] + g['beat']
    made_first = not early
    light = q.evaluate("()=>__dg.gaps().dawnAt") == [t for nm, t in at if nm == 'dawn'][-1]
    ok = 'turn' in files and 'dawn' in files and calm and min(calm) >= g['beat'] and pc_moved and min(pc_moved.values()) >= g['beat'] and ruby_ok and made_first and light
    report(ok, 'sounds: tick, beats, chime with the light; full jars', 'files %s; motion to tick/round end %s ms; tick to PC hand %s ms; ruby to tick %s (ruby %s + beat %s); materials in before a break %s; chime with the light %s'
           % (sorted(files), calm, sorted(pc_moved.values()), round(tick_after_ruby[0] - ruby[0]) if ruby_ok or (ruby and tick_after_ruby) else None, g['ruby'], g['beat'], made_first, light))
def f_morning_strong(q):  # owner 27 Nov: "remove night animation, but strengthen the day animation" (its light was at most 0.45 strong)
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1}); peak, n, band, core = 0, 0, 1, 0  # owner 27 Nov later: "make the day stripe not so wide, more condensed ... contract that, and a bit less golden bright" (it was 0.8 strong over 0.9 of the screen, with a warm wash over all)
    for _ in range(60):
        skip(q, 50); d = drawn(q, 'dawn')
        if not d and n: break
        if d: n += 1; peak = max(peak, d[0]['a']); band = d[0]['band']; core = d[0]['core']
    # owner 27 Nov, third: "make the day ribbon brighter, and make it have a part in its core that is almost solid golden light, but dont make it annoying, its just that the light core now is like a line, extremely thin"
    report(0.7 <= peak < 0.9 and band <= 0.4 and core >= 0.3 and n * 50 >= 1200, 'round: the morning light is a narrow stripe with a wide bright core, long', 'light at most %.2f, band %.2f of the screen, core %.2f of the band, seen %d ms' % (peak, band, core, n * 50))
def f_turn_shown(q):  # owner 24 Nov: "make it obvious who plays; now there is no difference between me and the opponent playing": the player whose turn it is has his area lit, the other's is dimmed; a sound when the turn passes; no sign flies from face to face (owner 24 Nov: "weird")
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); settle(q)
    lit = lambda: {d['o']: d['lit'] for d in drawn(q, 'panel')}
    mine = lit(); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.state().turn===1", 8000); pcs = lit(); w = st(q)['wait']; h = q.evaluate("()=>__dg.sounds()")
    faces = {x['o']: x for x in drawn(q, 'avatar')}; light = [x for x in drawn(q, 'flight') if x['look'] == 'turnlight']; market = drawn(q, 'market')
    bigger = faces[1]['lit'] and not faces[0]['lit'] and market and market[0]['o'] == 1; q.clock.resume()  # owner 27 Nov: the stickers never change size; his turn is his sticker's glow
    ok = mine == {0: True, 1: False} and pcs == {0: False, 1: True} and 'turn' in h and not light and bigger
    report(ok, 'turn: lit, no sign flying, his sticker glows, the market his colour', 'kid playing %s; PC playing %s (wait %s); turn sound %s; a sign flying face to face %s; PC sticker glows and market his %s' % (mine, pcs, w, 'turn' in h, bool(light), bool(bigger)))

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_end_screen(q):  # owner 25 Nov (prototype): the end: a smaller box over the board; each player's coins fly into his pile, both piles the same coin size, rows of 10;
#     # a star over the taller pile; a green play button that works
#     pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[3, 3]] * 4, 'coins': [23, 7]}); flew, ms = False, 0  # no tile fits anyone: the game ends at once
#     while ms < 4000 and not st(q)['over']:
#         skip(q, 100); ms += 100; box = drawn(q, 'endbox'); flew = flew or any(box and box[0]['x'] < f['tx'] < box[0]['x'] + box[0]['w'] for f in drawn(q, 'flight') if f['look'] == 'coin')
#     skip(q, 100); box, board = drawn(q, 'endbox'), drawn(q, 'boardarea')[0]; piles = {o: [c for c in drawn(q, 'endcoin') if c['o'] == o] for o in (0, 1)}; star = drawn(q, 'winner'); panel = drawn(q, 'coin')
#     inside = bool(box) and board['x'] <= box[0]['x'] and box[0]['x'] + box[0]['w'] <= board['x'] + board['w'] and board['y'] <= box[0]['y'] and box[0]['y'] + box[0]['h'] <= board['y'] + board['h']
#     rows = {o: sorted(sum(1 for c in v if abs(c['y'] - y) < 1) for y in {c['y'] for c in v}) for o, v in piles.items()}; sizes = {c['r'] for v in piles.values() for c in v}
#     above = bool(star) and star[0]['o'] == 0 and star[0]['y'] < min(c['y'] for c in piles[0])
#     q.clock.resume(); tap(q, 'again'); s = st(q); again = s['round'] == 1 and [p['coins'] for p in s['players']] == [0, 0] and s['wait'] and s['wait']['kind'] == 'pick'
#     ok = flew and inside and [len(piles[0]), len(piles[1])] == [23, 7] and not panel and rows == {0: [3, 10, 10], 1: [7]} and len(sizes) == 1 and above and again
#     report(ok, 'end: a box over the board, two piles, a star, play again', 'coins flew %s; box over the board %s; piles %s in rows %s, coin sizes %s; star over the taller %s; play button works %s' % (flew, inside, [len(piles[0]), len(piles[1])], rows, sizes, above, again))
#
def f_end_winner(q):  # owner 27 Nov: "end screen: the star should be replaced by the ruby, without shadow. also, the play again button should be BELOW the coin counting. also, remove the green/red dots.
    # after the coins have gone in place, the winner can be announced, by making its sticker the excited stance, and jerking up and down as if jumping up and down excitedly, also throw some victory sounds and visuals (ribbon explosion)"
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[3, 3]] * 4, 'coins': [23, 7]}); ms, early = 0, []  # no tile fits anyone: the game ends at once
    while ms < 6000 and not st(q)['over']:
        skip(q, 100); ms += 100; early += [] if st(q)['over'] else [d for d in drawn(q, 'ribbon')] + [1 for d in drawn(q, 'avatar') if d['o'] == 0 and d['shown'].get('up')]
    h0 = len(q.evaluate("()=>__dg.sounds()")); ys = []
    for _ in range(8): skip(q, 60); a = [d for d in drawn(q, 'avatar') if d['o'] == 0][0]; ys.append(a['shown']['y'])
    win = drawn(q, 'winner'); box = drawn(q, 'endbox')[0]; coins = drawn(q, 'endcoin'); btn = q.evaluate("()=>__dg.btn('again')"); pic = [d for d in drawn(q, 'avatar') if d['o'] == 0][0]['pic']
    heard = q.evaluate("()=>__dg.sounds()")[h0 - 2:]; ribbons = len(drawn(q, 'ribbon'))
    look = "([x,y])=>{const c=document.getElementById('c'),d=c.width/innerWidth,p=c.getContext('2d').getImageData(Math.round(x*d),Math.round(y*d),1,1).data;return p[0]+p[1]+p[2]}"
    dots = [q.evaluate(look, [box['x'] + box['w'] * f, box['y'] + box['h'] - 34]) for f in (0.28, 0.72)]; q.clock.resume()
    ok = (win and win[0]['pic'] == 'ruby' and not win[0]['shadow'] and win[0]['o'] == 0 and btn and btn[1] > max(c['y'] + c['r'] for c in coins) and min(dots) > 700
          and not early and pic.endswith('excited') and max(ys) - min(ys) > 10 and 'victory' in heard and ribbons > 20)
    report(ok, 'end: ruby, button under the coins, no dots; then the winner jumps with a fanfare and ribbons', 'winner %s; button at %s under coins to %s; where the dots were %s; before the count %d; face %s, jumping %d px; heard %s; ribbons %d' % (
        win and (win[0]['pic'], win[0]['shadow']), btn and round(btn[1]), round(max(c['y'] + c['r'] for c in coins)), dots, len(early), pic, round(max(ys) - min(ys)), heard, ribbons))
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

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_pc_hand(q):  # the PC's moves are slow and done by a moving hand: it points to tap, grabs to drag, showing the pointing hand for both (owner 24 Nov) (a fake clock runs the real timings at once);
#     # a new game started while that hand still carries a tile: the old move never touches the new game
#     pause_clock(q)
#     q.evaluate("()=>__dg.restart({fast:false,bag:[[0,1],[0,0],[0,4],[0,4]],first:1,jarQueue:Array(8).fill({k:'coins'})})")
#     ms, xs, gs, dragged, drag_pics = 0, set(), set(), False, set()
#     while ms < 20000:
#         q.clock.run_for(200); ms += 200; s = st(q)
#         xs.add(round(s['hand']['x'])); gs.add(s['hand']['g']); dragged = dragged or s['handDrag']
#         if s['handDrag']: settle(q); drag_pics |= {d['pic'] for d in drawn(q, 'hand')}
#         if ms >= 2500 and dragged and {'point', 'grab'} <= gs: break  # slow enough, and seen pointing, grabbing and dragging
#     slow = ms >= 2500 and len(xs) > 10 and dragged and {'point', 'grab'} <= gs and drag_pics == {'backhand_index_pointing_up'}
#     table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); waiting(q, 'place'); h0 = held(q)
#     q.clock.run_for(1800); settle(q); h1 = held(q); q.clock.resume()  # longer than the rest of the PC's drag
#     report(slow and h0 == h1, 'pc: slow, by a moving hand; a new game is left alone', '%d ms, hand at %d places, gestures %s, pictures while dragging %s; new game tile %s then %s' % (ms, len(xs), sorted(gs), sorted(drag_pics), h0, h1))
#
def f_pc_most_jars(q):  # owner (design): the PC does what is best for this turn; owner 25 Nov rules: a move is worth the jars it makes now, its connections' and those of
    # 5 materials; here [1, 1] and [0, 3] both connect once, but [0, 3] lights 6 colour-0 squares onto his 4: 2 more jars
    table(q, bag=[[1, 1], [0, 3], [3, 3], [3, 3]], first=1, tiles=[[11, 4, 3, 0, 0, 1], [10, 4, 3, 0, 0, 1]], goods=[[0] * 6, [4, 0, 0, 0, 0, 0]], jarQueue=[COIN] * 12)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] not in ([11, 5], [11, 4], [10, 4])]; opened = sum(s['players'][1]['opened'].values())
    report(pc == [[0, 3]] and opened == 3, 'pc: the move that makes the most jars', 'pc placed %s, jars %d' % (pc, opened))

def f_break_jar_in_jar(q):  # owner 27 Nov: "you should be able to break an extra jar even at its freeze state" (a jar won from a jar, hanging where it came out)
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'jar'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); tap(q, 'jar-0')
    run_until(q, "()=>__dg.sounds().includes('reveal')", 3000); hanging = [d for d in drawn(q, 'jar') if d['o'] == 0 and d.get('rising')]
    tap(q, 'jar-0'); opened = sum(st(q)['players'][0]['opened'].values()); q.clock.resume()
    report(len(hanging) == 1 and opened == 2, 'jars: a jar from a jar breaks while it hangs there', 'hanging %d, jars broken %d' % (len(hanging), opened))
def f_bee_prize_coin(q):  # owner 27 Nov: "when one already has the bee, replace bee percentage chance with coin"
    table(q, bag=[[0, 1]] * 4, jarQueue=[{'k': 'first'}, {'k': 'first'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0})  # under his start tile: two connections, two jars
    waiting(q, 'jar'); tap(q, 'jar-0'); holder = [d['o'] for d in drawn(q, 'token')]; c0 = st(q)['players'][0]['coins']; waiting(q, 'jar'); tap(q, 'jar-0'); c1 = st(q)['players'][0]['coins']
    report(holder == [0] and c1 == c0 + 1, 'jars: a bee for one who has it is a coin', 'bee with %s after the first jar; coins %d then %d' % (holder, c0, c1))
def f_no_jar_shade(q):  # owner 27 Nov: "remove jar opening darker overlay, it makes the avatars reactions harder to notice"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000); dark = len(drawn(q, 'shade')); tap(q, 'jar-0'); n = 0
    for _ in range(10): skip(q, 100); dark += len(drawn(q, 'shade')); n += 1
    q.clock.resume(); report(dark == 0, 'jars: no darkening while they open', 'darkened in %d of %d pictures' % (dark, n + 1))
def f_pile_layers(q):  # owner 27 Nov: "make it so the deck is not this random brown color, but each layer has the same texture as the substratum of the tiles, in order of materials in the material stockpile, loop them as they are 6 and we have 8 layers"
    table(q); p = drawn(q, 'pile')[0]; cols = {d['c']: d['x'] for d in drawn(q, 'place') if d['o'] == 0}; order = sorted(cols, key=cols.get)  # the materials' columns from left to right, as he sees them
    want = [order[k % len(order)] for k in range(p['layers'])]
    # owner 27 Nov later: "weird line, remove that, there should be no seam" (the right side was two copies of the wall, meeting in its middle)
    report(p.get('lands') == want and p.get('copies') == [1, 1], 'deck: each layer a land\'s earth, one piece per side (no seam), in the materials\' order, from the bottom', 'layers %s (bottom up), materials %s, pictures per side %s' % (p.get('lands'), order, p.get('copies')))
def f_goods_smooth(q):  # owner 27 Nov: "try to make materials flight path more smooth, currently it looks as if they quickly jump from spot to spot, many quick flashes, the coin is smoother"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=K3, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); gaps, seen = [], 0
    for _ in range(40):
        skip(q, 25)
        for d in drawn(q, 'flight'):
            if d['look'] != 'good' or not d.get('trail'): continue
            seen += 1; pts = [[d['x'], d['y']]] + d['trail']; gaps.append(max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(pts, pts[1:])) / d['r'])
    report(seen > 10 and max(gaps) <= 1, 'goods: fly as one smooth streak (its copies overlap)', '%d goods seen, widest gap between copies %.2f of a good\'s size' % (seen, max(gaps or [9])))
def f_stickers_centred(q):  # owner 27 Nov: "make them all 10% bigger, move them a bit more down their slab ... make sure that in every major screen dimension the avatars are kind of centered in their slab, not way too much up or down, or down and out"
    seen, ok = [], True
    for w, h in ((1920, 1080), (1440, 900), (2560, 1080), (1280, 800)):  # owner 28 Nov: no 4:3 screen
        q.set_viewport_size({'width': w, 'height': h}); table(q, animals=['hamster', 'chick']); a = [d for d in drawn(q, 'avatar') if d['o'] == 0][0]; s = a['shown']
        f = [x for x in drawn(q, 'area') if x['o'] == 0 and x['kind'] == 'face'][0]['pts']; y0, y1 = min(p[1] for p in f), max(p[1] for p in f); cy = s['feet'] - s['h0'] / 2; cx = s['x']
        mid = (cy - y0) / (y1 - y0); good = 0.3 <= mid <= 0.7 and s['feet'] <= y1 and abs(s['grow'] - 1.2 * 1.1) < 0.01; ok = ok and good; seen.append((w, h, round(mid, 2), round(s['grow'], 2), round(s['feet']), round(y1)))  # the hamster was 1.2 times the box's fit; 10% more
    q.set_viewport_size({'width': 1280, 'height': 800})
    report(ok, 'stickers: 10% bigger, in the middle of their slab on every screen', '(screen, height in the slab 0 top 1 bottom, grown, feet, slab bottom) %s' % seen)
def f_pc_jar_order(q):  # owner 27 Nov: "enemy must break jars in order they are on the screen, now it jumps weirdly"
    # the PC's first jar holds a jar, which takes the broken jar's place (the first): it is the first on screen, so it is broken next
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[1, 1], [0, 3], [3, 3], [3, 3]], 'first': 1, 'tiles': [[11, 4, 3, 0, 0, 1], [10, 4, 3, 0, 0, 1]], 'goods': [[0] * 6, [4, 0, 0, 0, 0, 0]], 'jarQueue': [{'k': 'jar'}] + [COIN] * 12})
    broke, before, n0, ms = [], None, 0, 0  # a jar is told by its place and whether it is still coming out (the jar won takes the broken one's place at once)
    while ms < 30000 and len(broke) < 4:
        skip(q, 200); ms += 200; now = {(d['slot'], d.get('rising')) for d in drawn(q, 'jar') if d['o'] == 1 and not d.get('parked')}; n = sum(st(q)['players'][1]['opened'].values())
        if before is not None and n > n0: broke += sorted(k for k, r in before - now)
        before, n0 = now, n
    report(broke == [0, 0, 1, 2], 'pc: breaks jars in their order on the screen', 'places broken in turn %s' % broke)
def f_bee_slow(q):  # owner 27 Nov: "the bee flies from player to player too fast" (it took a prize's flight, about half a second)
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[0, 4]] * 4, 'first': 1, 'jarQueue': [COIN] * 8}); ms, flying = 0, 0
    while ms < 30000 and not (flying and not [f for f in drawn(q, 'flight') if f['look'] == 'bee']):
        skip(q, 25); ms += 25; flying += 25 if [f for f in drawn(q, 'flight') if f['look'] == 'bee'] else 0
    report(flying >= 1000, 'bee: flies slowly enough to follow (about a second)', 'one flight seen for %d ms' % flying)
def f_pass_no_bee(q):  # owner 27 Nov: "when i couldn't pick a tile cause none was fitting my existing area, the bee flew to the opponent and then back. for sure a bug."
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[3, 3]] * 4, 'first': 1, 'tiles': [[11, 4, 0, 3, 3, 1]], 'jarQueue': [COIN] * 8})  # only the PC's land takes [3, 3]: after the PC's move his turn passes
    run_until(q, "()=>{const s=__dg.state();return s.players[1].got>=1&&s.wait&&s.wait.who===1}", 20000); flights, ms, after = 0, 0, 0  # the PC has placed and is opening its jars
    while ms < 20000 and after < 1500:
        skip(q, 200); ms += 200; flights += len([f for f in drawn(q, 'flight') if f['look'] == 'bee']); after += 200 if st(q)['passes'][0] else 0
    report(st(q)['passes'][0] >= 1 and flights == 0, 'pass: the bee stays where it is', 'kid passes %s, bee seen flying in %d pictures' % (st(q)['passes'], flights))
def f_left_in_its_place(q):  # owner 27 Nov: "I clicked, dragged a tiny bit, and immediately left tile in its slot, and I lost my round!"
    table(q, bag=[[0, 4], [3, 3], [3, 3], [3, 3]], tiles=[[11, 4, 0, 3, 3, 1]], jarQueue=[COIN] * 8)  # only the first market tile fits his land
    tap(q, 'draft-0'); waiting(q, 'place'); h = held(q); path(q, h, [h[0] + 20, h[1] + 4]); s = st(q)
    report(s['wait'] and s['wait']['kind'] == 'pick' and s['wait']['who'] == 0 and s['passes'][0] == 0, 'tile: left on its own place, he picks again', 'wait %s, passes %s' % (s['wait'] and (s['wait']['kind'], s['wait']['who']), s['passes']))
def f_jar_mix(q):  # owner 25 Nov, per 100 jars: "1 coin about 45%, Empty about 10%, 2 coins about 10%, One of each material about 10%, Another jar about 8%, First player about 8%, Slot machine about 5%, Tile about 4%"; no stealing
    # owner 28 Nov: "remove the slot machine ... Give its jar percentage to the single coin"; the land changer "gets the same as the extra piece" (shares now per 104)
    table(q, bag=[[0, 4]] * 4, seed=11, changer=[None, None])  # seeded: an unseeded sample missed the 1.5% band about once in 15 runs; without a changer, so one can come
    n = 8000; m = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)
    # owner 28 Nov (later): "bee 3, extra tile 3, land changer 3, the 7 freed to the single coin"
    want = {'empty': 10, 'coins': 53, 'coins2': 10, 'tile': 3, 'changer': 3, 'first': 3, 'jar': 8, 'set': 10}
    ok = set(m) == set(want) and all(abs(100 * m[k] / n - v) < 1.5 for k, v in want.items())  # the shares are per 100 jars
    report(ok, 'jars: the owner\'s mix, no stealing', ', '.join('%s %.1f%%' % (k, 100 * m.get(k, 0) / n) for k in sorted(set(want) | set(m))))
def f_empty_jar(q):  # owner 24 Nov: some jars hold nothing: it breaks, shows it is empty, and nothing is gained
    get_jar(q, [{'k': 'empty'}])
    waiting(q, 'pick'); p = st(q)['players'][0]
    report(p['coins'] == 0 and p['jars'] == 0 and 'jar' in q.evaluate("()=>__dg.sounds()"), 'jars: an empty jar gives nothing', 'coins %d jars %d' % (p['coins'], p['jars']))

# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_jar_breaks(q):  # owner 24 Nov: "jars should visually break and the revealed bonus comes from inside them"; "the you play first should fly to its place"; a coin flies to his coins
#     pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[COIN, {'k': 'first'}] + [COIN] * 8)  # the tile meets 2 edges: 2 jars
#     tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000)
#     def watch(btn, until):  # tap a jar, then watch the screen until the reward has landed
#         at = q.evaluate("(b)=>__dg.btn(b)", btn); tap(q, btn); seen, ms = [], 0
#         while ms < 3000:
#             skip(q, 50); ms += 50; d = q.evaluate("()=>__dg.drawn().filter(d=>d.k==='flight'||d.k==='speck')"); s = st(q); seen.append((d, s))
#             if until(s): break
#         return at, seen
#     at1, seen1 = watch('jar-1', lambda s: s['players'][0]['coins'] == 1)
#     at0, seen0 = watch('jar-0', lambda s: s['first'] == 0)
#     def flights(seen, look): return [x for d, _ in seen for x in d if x['k'] == 'flight' and x['look'] == look]
#     near = lambda a, b, r=12: abs(a[0] - b[0]) < r and abs(a[1] - b[1]) < r
#     specks = [(x['x'], x['y']) for d, _ in seen1 for x in d if x['k'] == 'speck']
#     broke = bool(specks) and all(near(p, at1, 40) for p in specks)
#     out = flights(seen1, 'shown'); came_out = bool(out) and near((out[0]['fx'], out[0]['fy']), at1)
#     coin = flights(seen1, 'coin'); P = drawn(q, 'panel')[0]['w']; coin_flew = bool(coin) and coin[0]['tx'] < P and all(s['players'][0]['coins'] == 0 for d, s in seen1 if any(x['k'] == 'flight' and x['look'] == 'coin' for x in d))
#     star = flights(seen0, 'bee'); token = drawn(q, 'token'); star_flew = bool(star) and bool(token) and near((star[-1]['tx'], star[-1]['ty']), (token[0]['x'], token[0]['y'])) and all(s['first'] is None for d, s in seen0 if any(x['k'] == 'flight' and x['look'] == 'bee' for x in d))
#     q.clock.resume()
#     report(broke and came_out and coin_flew and star_flew, 'jars: break where tapped, the bonus comes out, rewards fly to their place', 'broke where tapped %s, bonus out of it %s, coin flew to his coins %s, star flew to its place %s' % (broke, came_out, coin_flew, star_flew))
#
def f_jars_at_once(q):  # owner 25 Nov (prototype): jars break at once, as fast as he taps; each prize (a picture) pops up above its own jar, stays a moment, then flies to its place;
    # owner 28 Nov: no prize waits for him now (no slot machine; an extra tile waits in its place)
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[COIN, {'k': 'tile'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000)  # 2 connections: 2 jars
    jars = sorted((d['x'], d['y'], d['size']) for d in drawn(q, 'jar')); tap(q, 'jar-0'); again = (st(q)['wait'] or {}).get('kind') == 'jar'; tap(q, 'jar-0'); left = st(q)['players'][0]['jars']
    run_until(q, "()=>{const d=__dg.drawn();return d.filter(x=>x.k==='shown').length===2&&!d.some(x=>x.k==='flight'&&x.look==='shown')}", 2000); cards = sorted((d['x'], d['y']) for d in drawn(q, 'shown'))
    above = len(cards) == 2 and all(abs(c[0] - j[0]) < 5 and c[1] < j[1] - j[2] / 2 for c, j in zip(cards, jars))  # risen out of it, above it
    run_until(q, "()=>{const p=__dg.state().players[0];return p.extras[0]!==null&&p.coins===1}", 8000); s = st(q)['players'][0]; q.clock.resume()
    ok = again and left == 0 and above and s['coins'] == 1 and s['extras'][0] is not None
    report(ok, 'jars: break at once; prize above its jar; each flies to its place', 'next tap taken at once %s, jars left %d, prizes above their jars %s (%s over %s), coin %d, extra tile in its place %s' % (again, left, above, [(round(x), round(y)) for x, y in cards], [(round(x), round(y)) for x, y, _ in jars], s['coins'], s['extras'][0]))

def f_jar_picture(q):  # owner 25 Nov (prototype): what a jar held is a picture, no words (the 24 Nov labels are gone); an empty jar shows an X; owner 27 Nov: "replace the red X for nothing (jars/slot machine) with this apple"
    pause_clock(q); table(q, bag=[[0, 4]] * 4, fast=False, jarQueue=[{'k': 'empty'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='shown')", 3000); shown = [d['j'] for d in drawn(q, 'shown')]; texts = [d['text'] for d in drawn(q, 'label')]; x = len([d for d in drawn(q, 'nothing') if d.get('pic') == 'apple']); q.clock.resume()
    report(shown == ['empty'] and not texts and x == 1, 'jars: a picture, no words; empty is the apple', 'shown %s, words %s, apples drawn %d' % (shown, texts, x))

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

def f_first_token(q):  # the first-player token comes from a jar
    get_jar(q, [{'k': 'first'}]); report(st(q)['first'] == 0, 'first: token comes to you', 'first %s' % st(q)['first'])

def f_extra_glow_bright(q):  # owner 27 Nov: the extra tile's glow with more luminosity: a lighter gold, adding light to what is under it
    table(q, bag=[[0, 4]] * 4, jarQueue=[{'k': 'tile'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
    for _ in range(40):
        s = st(q)
        if s['wait'] and s['wait']['kind'] == 'place' and s['fromNowhere']: break
        skip(q, 300)
    g = drawn(q, 'extraglow'); g = g[0] if g else {}
    col = g.get('col', '#000000'); light = (max(int(col[k:k + 2], 16) for k in (1, 3, 5)) + min(int(col[k:k + 2], 16) for k in (1, 3, 5))) / 510
    report(g.get('mode') == 'lighter' and light >= 0.65, 'extra tile: a brighter glow', 'colour %s (lightness %.2f), laid on as %s' % (col, light, g.get('mode')))

def f_pc_jars_faster(q):  # owner 27 Nov: the PC breaks its jars 10% faster; later: 5% slower than that (the hand's move to a jar, between jars, and its tap); its other moves as before
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 8, jarQueue=[COIN] * 12); paces = set()
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, best_spot(q))
    for _ in range(300):
        s = st(q)
        if s['wait'] and s['wait']['kind'] == 'jar' and s['wait']['who'] == 0: tap(q, 'jar-0'); continue
        skip(q, 200); w = s['wait']; h = drawn(q, 'hand')
        if h and w and w['who'] == 1: paces.add((w['kind'], h[0].get('pace')))
        if s['turn'] == 0 and s['round'] == 1 and any(k == 'jar' for k, _ in paces): break
    q.clock.resume(); jar = {p for k, p in paces if k == 'jar'}; other = {p for k, p in paces if k != 'jar'}
    report(len(jar) == 1 and abs(next(iter(jar)) * 1.05 - 1.1) < 0.001 and other == {1}, 'pc: breaks jars 10% faster, then 5% slower', 'hand pace on jars %s, on other moves %s' % (sorted(jar, key=str), sorted(other, key=str)))

def f_bee_next(q):  # owner 27 Nov: "The bee shows who plays first the NEXT round. so, when the player take his time, first, then the bee moves to the other player, because the other play will play first the next ROUND.
    # it has nothing to do with turns, but with who plays first the next ROUND. normally it alternates, unless a jar gives it to you."; a jar's first-player prize sends it to its winner; the bee a third bigger
    pause_clock(q); q.evaluate("(o)=>__dg.restart(o)", {'fast': False, 'seed': 1, 'bag': [[0, 4]] * 8, 'jarQueue': [COIN] * 30}); settle(q); holder = lambda: [d['o'] for d in drawn(q, 'token')]
    start = holder(); u = drawn(q, 'button')[0]['ui']; size = drawn(q, 'token')[0]['r'] / u if drawn(q, 'token') else 0
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='pick'}", 8000); run_until(q, "()=>__dg.drawn().some(d=>d.k==='token'&&d.o===1)", 3000); then = holder()
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, best_spot(q)); moves = []
    while st(q)['turn'] == 0 or st(q)['wait'] and st(q)['wait']['who'] == 0:  # his jars; then the PC's turn starts: the bee stays
        w = st(q)['wait']
        if w and w['kind'] == 'jar': tap(q, 'jar-0')
        else: skip(q, 100)
    for _ in range(10): skip(q, 100); moves += [d for d in drawn(q, 'flight') if d['look'] == 'bee']
    q.clock.resume(); table(q, bag=[[0, 4]] * 8, jarQueue=[COIN] * 30); r2 = kid_plays(q, lambda s: s['round'] == 2 and any(t[6] == 't5' for t in s['tiles'])); second = [t[5] for t in r2['tiles'] if t[6] == 't5']; second = second[0] if second else None  # round 1 placed 4 tiles: the 5th is round 2's first
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'first'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000); jar = [d for d in drawn(q, 'jar') if d['o'] == 0][0]; tap(q, 'jar-0')
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='flight'&&d.look==='bee')", 3000); f = [d for d in drawn(q, 'flight') if d['look'] == 'bee']
    won = [0 if f and f[0]['tx'] < 640 and abs(f[0]['fx'] - jar['x']) < 80 else None] if f else []; q.clock.resume()
    report(start == [0] and then == [1] and not moves and second == 1 and won == [0] and size >= 31, 'bee: who plays first next round; it alternates; a jar\'s prize',
           'at the start %s, once he starts his turn %s, flights on the PC\'s turn %d, round 2 starts with %s, after his first-player jar %s, size %.1f' % (start, then, len(moves), second, won, size))
def f_bee_hovers(q):  # owner 27 Nov: the bee moves in place in a small infinity loop (obvious, not big): it crosses its spot, wider than high, and stays near it
    pause_clock(q); table(q, fast=False); run_until(q, "()=>__dg.drawn().some(d=>d.k==='token')", 3000); pts = []  # owner 27 Nov: it flies to the other as the round's first turn starts: watch it once it is there
    for _ in range(70): skip(q, 80); settle(q); t = drawn(q, 'token'); pts.append(t[0] if t else None)
    q.clock.resume(); ok = all(pts); wd = ht = r = 0; crosses = False
    if ok:
        dx = [p['x'] - p['sx'] for p in pts]; dy = [p['y'] - p['sy'] for p in pts]; r = pts[0]['r']; wd, ht = max(dx) - min(dx), max(dy) - min(dy)
        crosses = (min(dx) < -1) and (max(dx) > 1)
        ok = crosses and r * 0.15 <= wd <= r * 0.8 and 0.2 * wd <= ht < wd
    report(ok, 'bee: a small infinity loop in place', 'across %.1f, up and down %.1f px (bee %.0f px), crosses its spot %s %s' % (wd, ht, r, crosses, [round(v) for v in dx[:12]]) if all(pts) else 'no bee')

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
def f_bee_corner(q):  # owner 27 Nov: "replace the star (who goes first next round) with a bee icon, that you will put in this corner" (his face stone's corner by the pool);
    # later: the bee between the sticker and the extra tile's place, clear of the resting sticker (other faces may overlap it); every animal, on both sides
    A, bad = ['hamster', 'bunny', 'chick', 'cat', 'dog', 'frog'], []
    for k in range(6):
        for o in (0, 1):
            table(q, animals=[A[k], A[(k + 1) % 6]], first=1 - o); skip(q, 3000); b = [d for d in drawn(q, 'token') if d['o'] == o]; b = b[0] if b else None  # the bee goes to the one who plays first next round
            a = [d for d in drawn(q, 'avatar') if d['o'] == o][0]['shown']; g = [d for d in drawn(q, 'giftplace') if d['o'] == o]; gx = g[0]['x'] if g else -1
            ok = bool(b) and (a['x'] + a['w'] / 2 < b['x'] - b['r'] and b['x'] + b['r'] < gx if o == 0 else gx < b['x'] - b['r'] and b['x'] + b['r'] < a['x'] - a['w'] / 2)
            if not ok: bad.append((A[k] if o == 0 else A[(k + 1) % 6], o, (round(a['x'] - a['w'] / 2), round(a['x'] + a['w'] / 2)), b and (round(b['x'] - b['r']), round(b['x'] + b['r'])), round(gx)))
    report(not bad, 'bee: between the sticker and the extra tile\'s place', 'every animal, both sides; wrong: %s' % bad)
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
def f_ruby_shadow(q):  # owner 27 Nov: "ruby shadow does not agree with the direction of the other shadows" (the sun is at the top left: shadows fall to the bottom right)
    table(q, coins=[3, 1]); r = drawn(q, 'ruby'); d = r and r[0].get('shadow')
    report(bool(d) and d[0] > 0 and d[1] > 0, 'ruby: its shadow falls to the bottom right, as the others', 'shadow offset %s' % d)
def f_ruby_smaller(q):  # owner 27 Nov: the ruby and its animation 10% smaller (it was 44 px across its middle at a 1920 x 1080 screen)
    q.set_viewport_size({'width': 1920, 'height': 1080}); table(q, coins=[3, 1]); r = drawn(q, 'ruby'); u = drawn(q, 'button')[0]['ui']; q.set_viewport_size({'width': 1280, 'height': 800})
    report(bool(r) and abs(r[0]['r'] - 0.9 * 44 * u) < 0.5, 'ruby: 10% smaller', 'ruby %s, was %.1f' % (r and round(r[0]['r'], 1), 44 * u))
def f_extra_glow(q):  # owner 27 Nov: "the extra tile should have something like golden glow and sparkling small stars too, to draw attention to it" (owner 28 Nov: in its place too)
    table(q, bag=[[0, 4]] * 4, extras=[[[0, 4], None], [None, None]]); market = [g for g in drawn(q, 'extraglow') if g['y'] < drawn(q, 'extra')[0]['y'] - 40]
    g, e = drawn(q, 'extraglow'), drawn(q, 'extra')[0]; tap(q, 'extra-0'); waiting(q, 'place'); g2, h = drawn(q, 'extraglow'), held(q)
    ok = not market and any(abs(x['x'] - e['x']) < 2 and abs(x['y'] - e['y']) < 2 for x in g) and any(abs(x['x'] - h[0]) < 2 and abs(x['y'] - h[1]) < 2 for x in g2)
    report(ok, 'extra tile: a golden glow and stars, in its place and in hand; a market tile none', 'market tile glow %s, in its place %s, in hand %s' % (bool(market), bool(g), bool(g2)))

def f_sticker_box(q):  # owner 27 Nov: "make the avatars bigger and contain them in this box" (his red box on the face stone, beside the extra tile's place)
    table(q); tap(q, 'draft-0'); waiting(q, 'place'); ok, seen = True, []
    for i in (0, 1):
        a0 = [x for x in drawn(q, 'avatar') if x['o'] == i][0]; a, s = a0['box'], a0['shown']; face = [x for x in drawn(q, 'area') if x['o'] == i and x['kind'] == 'face'][0]['pts']
        corners = [(s['x'] + dx * s['w'] / 2, s['y'] + dy * s['h'] / 2) for dx in (-1, 1) for dy in (-1, 1)]
        within = all(inside_poly(face, x, y) for x, y in corners)  # owner 27 Nov: lower and bigger, past its box: still on the face stone
        size = lambda d: d['shown']['h0'] * (1.2 if d['pic'].split('/')[1].startswith('frog') else 1); big = abs(size(a0) - size([x for x in drawn(q, 'avatar') if x['o'] != i][0])) < 0.5  # later: the frog 20% smaller  # owner 27 Nov changed the size rule (was: as big as the box): both the same height, his turn or not; the size is checked in sticker_heights
        ok = ok and within and big; seen.append((i, round(s['w']), round(s['h']), within, big))
    report(ok, 'stickers: on the face stone, both the same height', seen)
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
    pause_clock(q); table(q, fast=False, coins=[1, 0], first=1, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); run_until(q, "()=>__dg.sounds().includes('rubyout')", 15000); outs = []  # the PC's coin levels them (owner 28 Nov: no slot machine to pay from)
    for _ in range(80):  # owner 27 Nov: "when ruby disappears, it should have the opposite animation from appearing. also, now it flickers on disappearance."
        skip(q, 50); r = drawn(q, 'ruby')
        if not r: break
        outs.append(r[0]['formed'])
    gone, h = drawn(q, 'ruby'), q.evaluate("()=>__dg.sounds()"); q.clock.resume(); backwards = len(outs) > 5 and all(a >= b for a, b in zip(outs, outs[1:])) and outs[0] > 0.9 and outs[-1] < 0.2
    report(not gone and backwards and 'rubyout' in h, 'ruby: un-forms (its forming backwards) when the coins are level, with its sound', 'ruby %s, formed per 50 ms %s, sound %s' % (gone, [round(x, 2) for x in outs], 'rubyout' in h))
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
def f_free_tile(q):  # owner 25 Nov (prototype): a jar's free tile is a random tile, no wild tile; it always fits; it is his ("marked as yours", 24 Nov)
    # owner 28 Nov: "the extra slot does not have to be immediately placed but can be placed anytime as a free action": it waits in its place; on his turn he places it and picks after
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'pick'); s = st(q); e = drawn(q, 'extra'); got, n0 = s['players'][0]['got'], tile_count(q, 0)
    kept = len(e) == 1 and e[0]['o'] == 0 and e[0]['n'] == 0 and e[0]['ok'] and s['players'][0]['extras'][0] == e[0]['cs']
    tap(q, 'extra-0'); waiting(q, 'place'); fits = len(st(q)['spots']) > 0; drag_to(q, best_spot(q)); open_jars(q); s2 = st(q)
    free = s2['wait']['who'] == 0 and s2['players'][0]['got'] == got and tile_count(q, 0) == n0 + 1 and s2['players'][0]['extras'] == [None, None]
    report(kept and fits and free, 'extra tile: waits in its place; placed for free on his turn, then he picks', 'kept in its place %s, fits %s, placed and still his turn to pick %s' % (kept, fits, free))

def f_extra_shine(q):  # owner 27 Nov: "extra tile should shine brighter, have a bit more stars, stars shouldn't be wrongly centered as now, and make sure it also shines from the beginning, not only when at its slot"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'tile'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}"); tap(q, 'jar-0')
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='shown')", 3000); shown = len(drawn(q, 'extraglow'))
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='flight'&&d.look==='tile')", 3000); flying = len(drawn(q, 'extraglow')); q.clock.resume()
    table(q, extras=[[[0, 4], None], [None, None]]); t = drawn(q, 'extra')[0]; s = drawn(q, 'extrastars'); g = drawn(q, 'extraglow'); m = s and s[0]['mean']
    w, h = [(d['w'], d['h']) for d in drawn(q, 'tile') if abs(d['x'] - t['x']) < 1 and abs(d['y'] - t['y']) < 1][0]
    # owner 28 Nov (later): "a little more glow than now (less than before), stars in a smaller area and a third fewer, centred on the middle of the whole 3D tile (ground and height), not its top"
    centred = bool(m) and abs(m[0] - t['x']) < 0.1 * w and t['y'] < m[1] < t['y'] + h / 2 and math.hypot(*s[0]['u']) <= 0.5 * w
    ok = shown >= 1 and flying >= 1 and g and g[0]['shine'] == 1 and 0.45 < g[0]['alpha'] <= 0.95  # owner 28 Nov (later): "there is no glow in the tiles, only stars": stronger again (was at most 0.65) and s and s[0]['n'] == 20 and centred  # owner 28 Nov: "make the extra tile glow less. now that they stay in the screen"
    report(ok, 'extra tile: shines from the jar on, softly, many stars round its middle', 'glow while shown %d, flying %d; shine %s, strength %s; stars %s round %s, tile at %s' % (shown, flying, g and g[0]['shine'], g and g[0]['alpha'], s and s[0]['n'], m and [round(v) for v in m], [round(t['x']), round(t['y'])]))

def f_extra_back(q):  # owner 28 Nov: an extra tile "can be taken and then returned to the slot, like the other normal drawn tiles"
    table(q, bag=[[0, 4]] * 4, extras=[[[0, 4], None], [None, None]]); tap(q, 'extra-0'); waiting(q, 'place')
    p1 = [d for d in drawn(q, 'giftplace') if d['o'] == 0 and d['n'] == 1][0]; path(q, held(q), [p1['cx'], p1['y']]); waiting(q, 'pick'); run_until(q, "()=>__dg.state().players[0].extras[1]!==null", 2000)
    s = st(q); heard = q.evaluate("()=>__dg.sounds()")
    ok = s['players'][0]['extras'][0] is None and sorted(s['players'][0]['extras'][1] or []) == [0, 4] and s['players'][0]['got'] == 0 and 'extratake' in heard and 'extraback' in heard
    report(ok, 'extra tile: left on an empty extra place it goes back there, his turn goes on', 'extras %s, tiles taken %d, sounds %s' % (s['players'][0]['extras'], s['players'][0]['got'], [x for x in heard if x.startswith('extra')]))
def f_extras_two(q):  # owner 28 Nov: "you can have max 2 extra tiles, if you have 2, then the jars dont give you more until you again have an empty extra tile slot ... their percentage goes to single coins";
    # "move the extra tile slot a bit more up (parallel to the pool edge still), so you can fit 2 of these slots on the slab"
    table(q, bag=[[0, 4]] * 4, seed=11, extras=[[[0, 4], [1, 1]], [None, None]]); n = 4000; full = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)
    table(q, bag=[[0, 4]] * 4, seed=11, extras=[[[0, 4], None], [None, None]]); one = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)
    pl = sorted([d for d in drawn(q, 'giftplace') if d['o'] == 0], key=lambda d: d['n']); a, b = q.evaluate("()=>[__dg.square(0,0), __dg.square(0,1)]")
    along = math.atan2(pl[1]['y'] - pl[0]['y'], pl[1]['cx'] - pl[0]['cx']) - math.atan2(b[1] - a[1], b[0] - a[0]); face = [x for x in drawn(q, 'area') if x['o'] == 0 and x['kind'] == 'face'][0]['pts']
    ok = 'tile' not in full and abs(100 * full.get('coins', 0) / n - 59) < 2 and 'tile' in one and abs(along) < 0.01 and pl[0]['y'] < pl[1]['y'] and all(inside_poly(face, d['cx'], d['y']) for d in pl)
    report(ok, 'extra tiles: two places along the pool\'s edge; with both full a tile jar is a coin', 'both full: tile %s, coin %.1f%%; one full: tile %s; places %s, off the edge\'s line %.3f' % ('tile' in full, 100 * full.get('coins', 0) / n, 'tile' in one, [(round(d['cx']), round(d['y'])) for d in pl], along))
def f_changer(q):  # owner 28 Nov: "a single half tile ... 6 stripes of top and sub layer of the 6 different lands ... you can tap it, and it then changes from its original form, and it rotates through the 6 lands.
    # you can drag it and drop it ON AN EXISTING HALF TILE ... to make the half tile below it change land. it triggers a new edge/harvesting occurrence. the placement preview should follow the rules of the normal
    # placement preview, with the land below that gets the white dashed border, and shown as fade preview of the new land"
    table(q, bag=[[1, 4]] * 4, jarQueue=[COIN] * 8); first = [d for d in drawn(q, 'changer') if d['z'] == 1]; striped = len(first) == 1 and first[0]['c'] == -1  # [1, 4] still fits his land once its 0 square is 1
    tap(q, 'changer'); waiting(q, 'pick'); c1 = st(q)['players'][0]['changer']; tap(q, 'changer'); waiting(q, 'pick'); c2 = st(q)['players'][0]['changer']  # the first land, then the next
    sq = q.evaluate("()=>__dg.square(4,10)"); path(q, q.evaluate("()=>__dg.btn('changer')"), sq, up=False); pv = [d for d in drawn(q, 'preview') if d['where'] == 'square']
    q.mouse.up(); settle(q); waiting(q, 'jar'); s = st(q); start = [t for t in s['tiles'] if t[:2] == [4, 10]][0]
    open_jars(q); s2 = st(q); heard = q.evaluate("()=>__dg.sounds()")
    ok = striped and (c1, c2) == (0, 1) and pv and (pv[0]['x'], pv[0]['y'], pv[0]['c']) == (4, 10, 1) and start[3:5] == [1, 1] and s['players'][0]['jars'] == 1 and s2['players'][0]['changer'] is None and s2['wait']['who'] == 0 \
        and all(x in heard for x in ('changerturn', 'changerdrop'))
    report(ok, 'land changer: striped, a tap turns its land, dropped on a square it changes it; its new edge gives a jar; his turn goes on', 'striped %s, lands after taps %s, preview %s, the square now %s, jars %d, changer after %s, his turn %s' % (striped, (c1, c2), pv and pv[0], start[3:5], s['players'][0]['jars'], s2['players'][0]['changer'], s2['wait']['who'] == 0))
def f_changer_back(q):  # owner 28 Nov: the changer changes only a square of another land; dropped anywhere else it goes back to its place
    table(q, bag=[[0, 4]] * 4); tap(q, 'changer'); waiting(q, 'pick'); path(q, q.evaluate("()=>__dg.btn('changer')"), q.evaluate("()=>__dg.square(8,8)")); waiting(q, 'pick')
    run_until(q, "()=>__dg.state().players[0].changer!==null", 2000); s = st(q); heard = q.evaluate("()=>__dg.sounds()")
    ok = s['players'][0]['changer'] == 0 and 'changerback' in heard and [t[3:5] for t in s['tiles'] if t[:2] == [4, 10]] == [[0, 1]]
    report(ok, 'land changer: dropped on the water it goes back, nothing changes', 'changer %s, back sound %s' % (s['players'][0]['changer'], 'changerback' in heard))
def f_changer_own_land(q):  # owner 28 Nov: "each player can change only his own land with the land changer" (the PC changed the kid's)
    table(q, bag=[[0, 4]] * 4); pc = [t for t in st(q)['tiles'] if t[5] == 1][0]
    while st(q)['players'][0]['changer'] in (-1, pc[3]): tap(q, 'changer'); waiting(q, 'pick')
    path(q, q.evaluate("()=>__dg.btn('changer')"), q.evaluate("(t)=>__dg.square(t[0],t[1])", pc))
    run_until(q, "()=>__dg.state().players[0].changer!==null", 2000); s = st(q)
    kid_ok = s['players'][0]['changer'] is not None and [t for t in s['tiles'] if t[6] == pc[6]][0][3:5] == pc[3:5] and 'changerback' in q.evaluate("()=>__dg.sounds()")
    table(q, seed=5, first=1, changer=[None, -1]); kids = {t[6]: t[3:5] for t in st(q)['tiles'] if t[5] == 0}
    s = kid_plays(q, lambda s: s['round'] >= 3 or s['over'], 300); used = 'changerdrop' in q.evaluate("()=>__dg.sounds()")
    pc_ok = used and all(t[3:5] == kids[t[6]] for t in s['tiles'] if t[6] in kids)
    report(kid_ok and pc_ok, 'land changer: only his own land', 'his changer on the PC\'s land went back %s; the PC used its changer %s and left his land alone %s' % (kid_ok, used, pc_ok))
def f_pc_waits_new_jar(q):  # owner 28 Nov: "PC hand: wait before breaking a new jar until it has fallen and rests"
    pause_clock(q); table(q, fast=False, first=1, bag=[[0, 1], [0, 0], [0, 4], [0, 4]], jarQueue=[{'k': 'jar'}] + [COIN] * 12)
    run_until(q, "()=>{const s=__dg.state();return s.turn===0&&s.wait&&s.wait.kind==='pick'}", 30000)
    names = [n for n, _ in q.evaluate("()=>__dg.heardAt()")]; q.clock.resume()
    first = names.index('jar'); land = names.index('jarland', first) if 'jarland' in names[first:] else len(names); between = names[first + 1:land].count('jar')  # broken before it landed: it never lands
    report(between == 0, 'pc: a new jar is broken only once it rests', 'jars broken while the new one rose and fell: %d' % between)
def f_changer_stripes(q):  # owner 28 Nov: "land changer stripes: the same way for both players (the right player's way now); the far yellow stripe solid, no brown line"
    table(q, changer=[-1, -1]); settle(q); ch = sorted(drawn(q, 'changer'), key=lambda d: d['x'])
    a, b = q.evaluate("()=>[__dg.square(0,0),__dg.square(1,0)]"); hw, hh = abs(b[0] - a[0]), abs(b[1] - a[1])
    px = lambda x, y: q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [x, y])[:3]
    grid = lambda c: [px(c['x'] + i * hw / 6, c['y'] + j * hh / 6) for i in range(-3, 1) for j in range(-5, 0) if abs(i) + abs(j) < 5]  # inside the top's upper left quarter (the PC's hand rests on the rest)
    same = sum(max(abs(u - v) for u, v in zip(p1, p2)) < 30 for p1, p2 in zip(grid(ch[0]), grid(ch[1]))) / len(grid(ch[0]))
    far = [px(c['x'] + (v - 0.08) * hw, c['y'] + (v - 0.92) * hh) for c in ch[:1] for v in (0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75)]
    med = [sorted(p[k] for p in far)[len(far) // 2] for k in range(3)]; solid = sum(max(abs(p[k] - med[k]) for k in range(3)) < 15 for p in far) / len(far)  # its stars may cross it: most of it one colour
    report(same >= 0.75 and solid >= 0.7, 'land changer: stripes one way for both, far stripe solid', 'same picture %.0f%% of the points; far stripe one colour at %.0f%%' % (100 * same, 100 * solid))
def centroid(pts):  # a polygon's middle (its area's centre: the standard shoelace formula)
    a = cx = cy = 0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]): k = x0 * y1 - x1 * y0; a += k; cx += (x0 + x1) * k; cy += (y0 + y1) * k
    return [cx / (3 * a), cy / (3 * a)]
def f_changer_place(q):  # owner 28 Nov: "land changer's place: halfway between its first place (middle of the free stone) and now; on 21:9 screens a third slot right below the two extra places, along the pool's edge like them"
    seen, ok = [], True
    for w, h in ((1280, 800), (1920, 1080), (2560, 1080), (3440, 1440)):
        q.set_viewport_size({'width': w, 'height': h}); table(q); settle(q)
        ch = [d for d in drawn(q, 'changerplace') if d['o'] == 0][0]; green = [d for d in drawn(q, 'icon') if d['o'] == 0 and d['c'] == 1][0]
        dead = [d for d in drawn(q, 'area') if d['o'] == 0 and d['kind'] == 'dead'][0]['pts']; mid = centroid(dead); g = sorted((d for d in drawn(q, 'giftplace') if d['o'] == 0), key=lambda d: d['n'])
        if w / h > 2.2: good = abs(ch['x'] - (2 * g[1]['cx'] - g[0]['cx'])) < 3 and abs(ch['y'] - (2 * g[1]['y'] - g[0]['y'])) < 3  # 21:9: the third place along the edge
        else: good = abs(ch['x'] - (mid[0] + green['x']) / 2) < 2 and min(p[1] for p in dead) < ch['y'] < mid[1]
        ok = ok and good; seen.append((w, h, good))
    q.set_viewport_size({'width': 1280, 'height': 800})
    report(ok, 'land changer: halfway to the stone\'s middle; on 21:9 below the extra places', '(screen, in place) %s' % seen)
def f_set_from_symbol(q):  # owner 28 Nov: "5-materials prize: its materials go into the stockpile one by one from the symbol, not vanishing and appearing from nowhere"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'set'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 8000); tap(q, 'jar-0')
    run_until(q, "()=>__dg.sounds().includes('reveal')", 3000); sym = [d for d in drawn(q, 'shown') if d['j'] == 'set'][-1]; starts, both, ms = set(), 0, 0
    while ms < 4000:
        skip(q, 50); ms += 50; d = q.evaluate("()=>__dg.drawn().filter(d=>d.k==='shown'||(d.k==='flight'&&d.look==='good'))")
        out = [f for f in d if f['k'] == 'flight' and abs(f['fx'] - sym['x']) < 60 and abs(f['fy'] - sym['y']) < 60]; starts |= {(round(f['fx']), round(f['fy'])) for f in out}
        if out and any(x['k'] == 'shown' for x in out + d): both += 1
        if len(starts) >= 6 and not out: break
    q.clock.resume()
    report(len(starts) == 6 and both > 0, 'set prize: its materials leave the symbol one by one', 'materials left from %d places of the symbol; symbol still there while they left %s' % (len(starts), both > 0))
def f_glows(q):  # owner 28 Nov (later): "make the tile stars (their area) be tilted to the tile position, so it is aligned with it"; "when 2 extra tiles are in their slots, the glows that overlap
    # should not become so weirdly bright"; "the stars of the changer tile are smaller than the extra tile's ... same effect for both"
    table(q, extras=[[[0, 4], [1, 2]], [None, None]]); settle(q); st_ = drawn(q, 'extrastars'); tiles = [s for s in st_ if s['halves'] == 2]; ch = [s for s in st_ if s['halves'] == 1]
    tilted = bool(tiles) and all(abs(s['u'][1]) > 0.3 * abs(s['u'][0]) for s in tiles)  # the oval's long side lies along the tile, not flat across the screen
    same = bool(ch) and bool(tiles) and ch[0]['size'] == tiles[0]['size']
    g = sorted(drawn(q, 'extraglow'), key=lambda d: d['y'])[:2]; hh = q.evaluate("()=>__dg.square(1,0)[1]-__dg.square(0,0)[1]"); mx, my = (g[0]['x'] + g[1]['x']) / 2, (g[0]['y'] + g[1]['y']) / 2
    pts = [[mx + dx * hh, my - k * hh] for k in (0.8, 1.1, 1.4, 1.7, 2.0) for dx in (-0.5, 0, 0.5)]  # over the joint, where both glows reach
    look = lambda: [q.evaluate("(p)=>__dg.pixel(p[0],p[1])", p)[:3] for p in pts]
    both = look(); table(q, extras=[[[0, 4], None], [None, None]]); settle(q); one = look(); table(q, extras=[[None, None], [None, None]]); settle(q); none = look()
    lit = [k for k in range(len(pts)) if max(o - n for o, n in zip(one[k], none[k])) > 10]  # points where one glow shows
    rise = max((max(b - o for b, o in zip(both[k], one[k])) for k in lit), default=None); soft = bool(lit) and rise < 8  # where two glows meet the brighter one shows: they do not add up
    hw = q.evaluate("()=>__dg.square(1,0)[0]-__dg.square(0,0)[0]"); ring = [[g[0]['x'] + 1.6 * hw * math.cos(a * math.pi / 8), g[0]['y'] + 1.6 * hh * math.sin(a * math.pi / 8)] for a in range(9)]  # round the first tile's lower half, just outside it
    table(q, extras=[[[0, 4], None], [None, None]]); settle(q); lone = [q.evaluate("(p)=>__dg.pixel(p[0],p[1])", p) for p in ring]  # the glow's own layer over the stone: its colour and strength
    gold = sorted(c[3] for c in lone if c[0] - c[2] > 150); shine = gold[len(gold) // 2] if len(gold) >= 3 else 0; soft = soft and shine >= 80  # owner 28 Nov (later): "there is no glow in the tiles, only stars": a deep gold, strong enough to see on the light stone
    report(tilted and same and soft, 'glows: stars along the tile, same stars on the changer, overlaps soft', 'stars along the tile %s; changer stars as big %s; glow at %d points, as strong as %d, the second glow adds up to %s' % (tilted, same, len(lit), shine, rise))
def f_square_jumps(q):  # owner 28 Nov (later): "half tiles that jump on harvesting should jump themselves, not create another tile on top of them that jumps"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2})
    run_until(q, "()=>__dg.drawn().some(d=>d.k==='square'&&d.up>0)", 3000); up = [d for d in drawn(q, 'square') if d.get('up', 0) > 0]; copies = drawn(q, 'pop'); q.clock.resume()
    report(bool(up) and not copies, 'harvest: the square itself jumps', 'squares lifted %d; copies drawn over them %d' % (len(up), len(copies)))
def f_jar_never_vanishes(q):  # owner 28 Nov (later): "falling jars momentarily disappear"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=[[4] * 6, [0] * 6], jarQueue=[{'k': 'set'}] + [COIN] * 12)  # a connection's jar, then jars made from materials
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); seen, gaps, ms = 0, [], 0
    while ms < 8000:
        q.clock.run_for(20); ms += 20; v = q.evaluate("()=>{__dg.render(); const d=__dg.drawn(); return [d.filter(x=>x.k==='flight'&&x.look==='jar').length, d.filter(x=>x.k==='jar'&&x.o===0).length]}")
        n = v[0] + v[1]
        if n < seen: gaps.append((ms, seen, n))
        seen = n
        w = st(q)['wait']
        if w and w['kind'] == 'jar' and w['who'] == 0: break
    q.clock.resume()
    report(not gaps, 'jars: a falling jar never vanishes', 'moments a jar went missing (ms, before, after): %s' % gaps[:5])
def f_break_ready_jars(q):  # owner 28 Nov (later): "i must be able to break jars that dont wait for any more materials"
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, goods=[[4] * 6, [0] * 6], jarQueue=[COIN] * 12)  # a connection's jar is full at once; its lit land's materials still fly and fill more jars
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); ms, flying = 0, None
    while ms < 8000 and flying is None:
        q.clock.run_for(50); ms += 50; v = q.evaluate("()=>{__dg.render(); const s=__dg.state(); return [!!(s.wait&&s.wait.kind==='jar'&&s.wait.who===0&&__dg.buttons().some(b=>b.startsWith('jar-'))), __dg.buttons().find(b=>b.startsWith('jar-')), __dg.drawn().some(x=>x.k==='flight'&&(x.look==='good'||x.look==='jar'))]}")
        if v[0]: flying, jar = v[2], v[1]
    if flying: tap(q, jar); broke = 'jar' in q.evaluate("()=>__dg.sounds()")
    else: broke = False
    q.clock.resume()
    report(bool(flying) and broke, 'jars: a full jar breaks while materials still fly', 'he could break one while materials or jars still came %s; it broke %s' % (flying, broke))
def f_changer_jar(q):  # owner 28 Nov: "it will be able to be refreshed by a jar (same glowing as the extra tiles, but only when given from a jar), it is NOT given from jars when you have it already, then its percentage goes to the coin"
    get_jar(q, [{'k': 'changer'}], changer=[None, None]); waiting(q, 'pick'); s = st(q); lit = lambda: [d for d in drawn(q, 'changer') if d['z'] == 1 and any(abs(g['x'] - d['x']) < 1 and abs(g['y'] - d['y']) < 1 for g in drawn(q, 'extraglow'))]; ch = lit()  # a glow laid where it is
    table(q, bag=[[0, 4]] * 4, seed=11); n = 4000; m = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n); table(q); plain = lit()
    ok = s['players'][0]['changer'] == -1 and len(ch) == 1 and 'changer' not in m and abs(100 * m.get('coins', 0) / n - 56) < 2 and len(plain) == 1  # owner 28 Nov (later): "the changer tile should glow from the beginning, not only when its gained from jar"
    report(ok, 'land changer: a jar gives a new one, shining; none while he has one (a coin instead); the first one does not shine', 'from a jar %s shining %s; with one: changer %s, coin %.1f%%; the first shines %s' % (s['players'][0]['changer'], bool(ch), 'changer' in m, 100 * m.get('coins', 0) / n, bool(plain)))
def f_pc_uses_spares(q):  # owner 28 Nov: what a player keeps is used for free; the PC does what is best for this turn: its extra tile first, its land changer when it makes a jar
    table(q, bag=[[0, 4]] * 4, first=1, changer=[-1, -1], extras=[[None, None], [[0, 4], None]], jarQueue=[COIN] * 20); waiting(q, 'pick'); s = st(q)
    pc = [t for t in s['tiles'] if t[5] == 1 and t[6] != 's1']; heard = q.evaluate("()=>__dg.sounds()")
    ok = s['players'][1]['extras'] == [None, None] and s['players'][1]['changer'] is None and len(pc) == 2 and 'changerdrop' in heard
    report(ok, 'pc: uses its extra tile and its land changer, then picks', 'pc extras %s, changer %s, tiles placed %d' % (s['players'][1]['extras'], s['players'][1]['changer'], len(pc)))
def f_bee_sparkles(q):  # owner 28 Nov: "give the bee a few small stars, like the ones the extra tile has, but a bit, and only a tiny glow, and not so bright"
    table(q); settle(q); b, glow = drawn(q, 'beestars'), drawn(q, 'beeglow'); table(q, extras=[[[0, 4], None], [None, None]]); e = drawn(q, 'extrastars'); t = drawn(q, 'token')
    # owner 28 Nov (later): "the bee should glow twice as much and have 1/3 more stars, and the stars should be 1/3 bigger" (from 0.5, 5 stars, size 0.45 of its radius)
    r = drawn(q, 'token')[0]['r']; ok = bool(b) and bool(e) and b[0]['n'] == 7 and abs(b[0]['size'] / r - 0.6 / q.evaluate('()=>__dg.gaps().beeR')) < 0.01 and bool(glow) and glow[0]['glow'] == 1.0  # owner 28 Nov (later): "bee: a bit more glow (it can't be seen now)": was at most 0.3
    report(ok, 'bee: a few small stars, a faint glow', 'bee stars %s, their size %s (the extra tile\'s %s), glow %s' % (b and b[0]['n'], b and round(b[0]['size'], 2), e and round(e[0]['size'], 2), glow and glow[0]['glow']))
def f_layout_28nov(q):  # owner 28 Nov: "On 3:2 screens the avatars run past the screen edge -> fix that"; "move changer tile slot a bit to the left, so its bot corner is aligned with the green land icon's
    # top/bot corners. and a bit more to the top, where there is space"; "the land icons can all move a bit more above the divider"
    seen, ok = [], True
    for w, h in ((1920, 1080), (1366, 768), (1440, 900), (1920, 1200), (1920, 1280), (2256, 1504)):
        q.set_viewport_size({'width': w, 'height': h}); table(q, animals=['hamster', 'chick']); settle(q)
        a = [d['shown'] for d in drawn(q, 'avatar')]; inside = all(s['x'] - s['w'] / 2 >= 0 and s['x'] + s['w'] / 2 <= w for s in a)
        ch = [d for d in drawn(q, 'changerplace') if d['o'] == 0][0]; green = [d for d in drawn(q, 'icon') if d['o'] == 0 and d['c'] == 1][0]; dead = [d for d in drawn(q, 'area') if d['o'] == 0 and d['kind'] == 'dead'][0]['pts']
        top = min(p[1] for p in dead); hh = q.evaluate("()=>__dg.square(1,0)[1]-__dg.square(0,0)[1]"); high = True  # owner 28 Nov (later): the changer's place moved (halfway to the stone's middle; below the extra places on 21:9): step changer_place
        groove = [d for d in drawn(q, 'groove') if d['o'] == 0][0]['y']; gap = (groove - (green['y'] + green['h'] / 2)) / hh  # the icon's ground bottom over the divider, in half-squares
        good = inside and high and gap > 0.75; ok = ok and good  # it was about 0.6
        seen.append((w, h, inside, high, round(gap, 2)))
    q.set_viewport_size({'width': 1280, 'height': 800})
    report(ok, 'layout: stickers on screen, icons clear over the divider', '(screen, stickers on screen, changer in line and high, icons over the divider in half-squares) %s' % seen)
def f_sound_hooks(q):  # owner 28 Nov: "make sure there are sound hooks for every event, movement, action": every sound the game plays has its line in SOUNDS.md
    names = set(q.evaluate("()=>__dg.soundNames()")); doc = set(re.findall(r'^\| `([a-z]+)` \|', (GAME.parent / 'SOUNDS.md').read_text(), re.M))
    report(names == doc, 'sounds: every one has its hook in SOUNDS.md', 'missing in SOUNDS.md %s, listed but not in the game %s' % (sorted(names - doc), sorted(doc - names)))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_screen_sizes(q):  # owner 25 Nov (design 3, the new look): the board is sea, 16 x 16 squares seen in true isometric view (a diamond 1.73 times as wide as high), as tall as the screen
#     # under the market band allows; a tile the same size everywhere; tiles he can't take: a light grey wash, their pictures clear (owner 25 Nov, prototype)
#     table(q, bag=[[0, 3], [3, 3], [0, 4], [0, 4]]); H = q.evaluate("()=>innerHeight"); b = drawn(q, 'boardarea')[0]; band = drawn(q, 'band')[0]
#     a, c = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hw, hh = c[0] - a[0], c[1] - a[1]
#     t = {d['id']: d for d in drawn(q, 'tile') if d['id'] in ('draft-0', 'draft-1')}
#     half = lambda k: q.evaluate("([k,dx,dy])=>{const [x,y]=__dg.slot(k); return __dg.pixel(x+dx,y+dy)}", [k, hw / 2, hh / 2 + hh * 0.6])[:3]  # the second half's front, where its ground shows
#     taken, grey = half(0), half(1)  # the same land picture ([0, 3] and [3, 3]): one as it is, one greyed
#     clear = grey != taken and all(abs(x - y) <= 40 for x, y in zip(grey, taken))
#     shape = b['cols'] == b['rows'] == 16 and abs(b['w'] / b['h'] - 3 ** 0.5) < 0.01 and abs(hw / hh - 3 ** 0.5) < 0.01 and abs(b['w'] - 32 * hw) < 1
#     tall = band['y'] == 0 and abs(b['y'] - (band['y'] + band['h'])) <= 1 and H - 16 <= b['y'] + b['h'] <= H
#     one = abs(t['draft-0']['w'] - 3 * hw) < 1 and abs(t['draft-0']['h'] - 3 * hh) < 1
#     ok = shape and tall and one and t['draft-1']['look'] == 'grey' and t['draft-0']['look'] is None and clear
#     report(ok, 'screen: sea diamond, as tall as allowed, one tile size, light grey', 'board %s squares, %.0f x %.0f px (%.2f), top %.0f under a band of %.0f, bottom %.0f of %d; square %.1f x %.1f; market tile %.0f x %.0f; greyed %s vs %s' % (
#         (b['cols'], b['rows']), b['w'], b['h'], b['w'] / b['h'], b['y'], band['h'], b['y'] + b['h'], H, hw, hh, t['draft-0']['w'], t['draft-0']['h'], grey, taken))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_land_pictures(q):  # owner 25 Nov (design 3, the new look): each land is a picture in the same isometric view (wheat field, pomegranate orchard, vineyard, forest, mountain, town);
#     # land exists only where tiles are placed, the rest is sea from his water pack; each land's material is its own picture (grain, pomegranates, grapes, timber, rubies, little statues)
#     table(q, bag=[[0, 4]] * 4, tiles=[[4, 11, 0, 2, 3, 0], [4, 12, 0, 4, 5, 0]], goods=[[1] * 6, [0] * 6])
#     lands, mats = ['wheat', 'pomegranate', 'vineyard', 'forest', 'mountain', 'town'], ['grain', 'pomegranate', 'grapes', 'timber', 'ruby', 'statue']
#     sq = drawn(q, 'square'); g = [x for x in drawn(q, 'good') if x['o'] == 0]; sea = drawn(q, 'sea')
#     pics = all(x['pic'] == 'lands/' + lands[x['c']] and x['ready'] for x in sq) and {x['c'] for x in sq} == set(range(6))
#     goods = sorted((x['c'], x['pic']) for x in g) == [(c, 'materials/' + m) for c, m in enumerate(mats)] and all(x['ready'] for x in g)
#     px = lambda x, y: q.evaluate("([x,y])=>{const p=__dg.square(x,y); return __dg.pixel(p[0],p[1]+3)}", [x, y])[:3]
#     wet = lambda c: c[2] > c[0] + 30  # the sea is blue; every land picture is warmer
#     land_px, sea_px = [px(x, y) for x, y in ((4, 11), (5, 12), (4, 10))], [px(x, y) for x, y in ((8, 8), (1, 1), (14, 14))]
#     ok = pics and goods and bool(sea) and sea[0]['ready'] and not any(wet(c) for c in land_px) and all(wet(c) for c in sea_px)
#     report(ok, 'look: land pictures on a sea, material pictures', 'squares %s, materials %s, sea %s, land pixels %s, sea pixels %s' % (
#         sorted({(x['c'], x['pic'], x['ready']) for x in sq}), sorted((x['c'], x['pic']) for x in g), sea, land_px, sea_px))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_player_areas(q):  # owner 25 Nov (design 3, the new look): each player's area is the two triangles beside the board on his side, joined at the board's side corner (green left, red right);
#     # owner 25 Nov: the 4 central tips (each triangle's thin end at the screen's middle) are grey and hold nothing, each cut where it is 3 material places thick;
#     # materials 1.5 times their old size (12.4 px on this screen), a row of 5 per colour from the top, beside the screen edge (owner 25 Nov: rows, not columns); his face beside them;
#     # coins fill the bottom triangle in rows from the bottom up, each as long as the triangle is wide there, at most 8 a row; owner 24 Nov: everything spaced apart, no jar outlines; the pile a stack of tiles
#     table(q, bag=[[0, 4]] * 12, goods=[[4, 4, 4, 2, 1, 0], [1, 1, 0, 0, 0, 0]], coins=[20, 3]); W, H = q.evaluate("()=>[innerWidth, innerHeight]"); dm = diamond(q); band = drawn(q, 'band')[0]
#     d = q.evaluate("()=>__dg.drawn()"); of = lambda k, o: [x for x in d if x['k'] == k and x.get('o') == o]; pile = [x for x in d if x['k'] == 'pile']
#     side = lambda o, x: x < W / 2 if o == 0 else x > W / 2; out = {}
#     for o in (0, 1):
#         face, places, goods, coins = of('avatar', o)[0], of('place', o), of('good', o), of('coin', o)
#         rws = {c: {round(x['y']) for x in places if x['c'] == c} for c in range(6)}
#         column = all(len(v) == 1 for v in rws.values()) and len({min(v) for v in rws.values()}) == 6 and all(len({round(x['x']) for x in places if x['c'] == c}) == 5 for c in range(6))
#         near_edge = (min(x['x'] - x['r'] for x in places) if o == 0 else W - max(x['x'] + x['r'] for x in places)) <= 24
#         from_top = min(x['y'] - x['r'] for x in places) - (band['y'] + band['h']) <= 16
#         inner = max(places, key=lambda x: abs(x['x'] - (0 if o == 0 else W)) + x['y'])  # the bottom row's inner place, nearest the board
#         big = min(x['r'] for x in places) >= 1.5 * 12.4 - 0.2 or not off_board(dm, inner['x'], inner['y'], inner['r'] + 4)  # owner 25 Nov: rows: as big as fits above the board
#         on_place = len(goods) == sum(st(q)['players'][o]['goods']) and all(any(abs(g['x'] - x['x']) < 1 and abs(g['y'] - x['y']) < 1 and g['c'] == x['c'] for x in places) for g in goods)
#         tips, rp = of('tip', o), min(abs(a['x'] - b['x']) for a in places for b in places if a['c'] == b['c'] and a is not b)
#         def tip_ok(t):  # touches the middle line; its side away from the middle is 3 material places long; grey where drawn
#             far = max(abs(x - W / 2) for x, _ in t['pts']); side_ys = [y for x, y in t['pts'] if abs(abs(x - W / 2) - far) < 0.5]
#             mx, my = sum(x for x, _ in t['pts']) / len(t['pts']), sum(y for _, y in t['pts']) / len(t['pts']); px = q.evaluate("([x,y])=>__dg.pixel(x,y)", [mx, my])[:3]
#             return min(abs(x - W / 2) for x, _ in t['pts']) < 0.5 and abs(max(side_ys) - min(side_ys) - 3 * rp) < 1 and max(px) - min(px) <= 6 and 90 < px[0] < 220
#         def inside(t, x, y, r):  # a round thing reaches into the tip (convex, points in order)
#             p = t['pts']; edges = list(zip(p, p[1:] + p[:1])); sgn = lambda a, b: (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
#             def dist(a, b):  # from (x, y) to the segment a-b
#                 dx, dy = b[0] - a[0], b[1] - a[1]; u = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / max(1e-9, dx * dx + dy * dy)))
#                 return ((x - a[0] - u * dx) ** 2 + (y - a[1] - u * dy) ** 2) ** 0.5
#             ins = all(sgn(a, b) >= 0 for a, b in edges) or all(sgn(a, b) <= 0 for a, b in edges)
#             return ins or min(dist(a, b) for a, b in edges) < r
#         things = places + coins + [face] + of('token', o)
#         corner = side(o, face['x']) and len(tips) == 2 and all(tip_ok(t) for t in tips) and not any(inside(t, x['x'], x['y'], x['r']) for t in tips for x in things)
#         rows = sorted({round(c['y']) for c in coins}, reverse=True); per = [sorted(c['x'] for c in coins if round(c['y']) == y) for y in rows]
#         step = min((b - a for r in per for a, b in zip(r, r[1:])), default=0); r0 = coins[0]['r'] if coins else 0
#         nxt = lambda r: (r[-1] + step) if o == 0 else (r[0] - step)
#         full = all(len(r) == 8 or not off_board(dm, nxt(r), y, r0) or any(inside(t, nxt(r), y, r0) for t in tips) for r, y in zip(per[:-1], rows))  # a row short of 8 meets the board or a tip
#         coins_ok = bool(coins) and max(len(r) for r in per) <= 8 and all(len(a) >= len(b) for a, b in zip(per, per[1:])) and H - max(c['y'] + c['r'] for c in coins) <= 24 and full
#         clear = all(off_board(dm, x['x'], x['y'], x['r']) and side(o, x['x']) for x in places + coins + [face])
#         apart = min_gap(places + coins + [face]) >= 3
#         out[o] = dict(column=column, edge=near_edge, top=from_top, big=big, on_place=on_place, corner=corner, coins=coins_ok, off_board=clear, apart=apart, rows=[len(r) for r in per])
#     ok = all(all(v for k, v in x.items() if k != 'rows') for x in out.values()) and not [x for x in d if x['k'] == 'jargroup'] and len(pile) == 1 and pile[0]['layers'] == 8
#     report(ok, 'areas: grey empty tips, material rows, coin rows', '%s, pile %s' % (out, pile))
def f_no_sets(q):  # owner 25 Nov (prototype): no wild tiles, no sets to tap: one of each colour lights nothing; only the market's tiles can be tapped
    table(q, bag=[[0, 4]] * 4, goods=[[2] * 6, [0] * 6]); b = q.evaluate("()=>__dg.buttons()"); marks = drawn(q, 'setrow') + drawn(q, 'setsign')
    b = [x for x in b if not x.startswith('avatar-') and x != 'changer']  # owner 27 Nov: the stickers answer a tap; owner 28 Nov: so does his land changer
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
def f_sticker_heights(q):  # owner 27 Nov: all stickers the same height, every animal in every face, as big as fits their box with a good empty margin around;
    # a wider pose stands with its feet on the same line and its head at the same place across as his resting pose; later: every sticker 20% bigger but the frog, lower and a little toward the lake; later: as big as possible (the box keeps the stones' room, no more), sized by the resting poses: a short wide pose may spill over
    seen = {}
    for w, h in ((1920, 1200), (1920, 1080), (3440, 1440)):
        q.set_viewport_size({'width': w, 'height': h}); per = {0: [set(), set(), {}], 1: [set(), set(), {}]}
        for a, b in (('cat', 'hamster'), ('frog', 'bunny'), ('dog', 'chick'), ('hamster', 'frog')):
            table(q, animals=[a, b]); settle(q)
            for poke in (False, True):
                if poke: tap(q, 'avatar-0'); tap(q, 'avatar-1')
                for d in drawn(q, 'avatar'):
                    sh, bx = d['shown'], d['box']; v = per[d['o']]; v[0].add(round(sh['h0'] * (1.2 if d['pic'].split('/')[1].startswith('frog') else 1), 1)); v[1].add(round(sh['feet'], 1)); v[2].setdefault(d['pic'].split('/')[1].split('-')[0], set()).add(round(sh['head'], 1))
        seen[(w, h)] = ({o: [len(v[0]), len(v[1]), max(len(x) for x in v[2].values())] for o, v in per.items()}, sorted(per[0][0] | per[1][0]))
    q.set_viewport_size({'width': 1280, 'height': 800})
    ok = all(all(n == [1, 1, 1] for n in v[0].values()) and len(v[1]) == 1 for v in seen.values())
    report(ok, 'faces: same height (the frog 20% smaller), feet on one line, each animal\'s head in one place', 'per screen (per player: how many heights, feet lines, most head places of one animal; heights) %s' % seen)
def f_starts_face(q):  # owner 25 Nov: the start tiles face each other: the PC's is the kid's turned half a turn around the board's centre (each colour on its turned square)
    table(q, bag=[[3, 3]] * 4); D = [[1, 0], [0, 1], [-1, 0], [0, -1]]
    sq = lambda t: {(t[0], t[1]): t[3], (t[0] + D[t[2]][0], t[1] + D[t[2]][1]): t[4]}
    kid, pc = [sq(t) for o in (0, 1) for t in st(q)['tiles'] if t[5] == o]
    turned = {(15 - x, 15 - y): c for (x, y), c in kid.items()}
    report(pc == turned, 'starts: the tiles face each other', 'kid %s, pc %s' % (kid, pc))
def f_scales(q):  # owner 25 Nov: "make sure your ui is adoptable to all laptop and pc screen sizes": what has its own size (faces, the hand) grows with the board, and stays on screen (owner 28 Nov: no slot machine)
    seen = []
    for w, h in ((1366, 768), (1920, 1080), (2560, 1440)):
        q.set_viewport_size({'width': w, 'height': h}); table(q); settle(q)
        a, c = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hh = c[1] - a[1]
        face = [x for x in drawn(q, 'avatar') if x['o'] == 0][0]; hand = drawn(q, 'hand')[0]
        fills = round(face['shown']['h0'] / hh, 2)  # owner 27 Nov changed the size rule (was: as big as its box): the sticker as big as its stone allows on each screen (sticker_heights), so only shown here
        seen.append((fills, round(hand['z'] / hh, 2)))
    q.set_viewport_size({'width': 1280, 'height': 800})
    same = all(abs(x[1] - seen[1][1]) <= 0.02 * seen[1][1] for x in seen)
    report(same, 'scales: sizes grow with the screen', 'per size (the sticker height and hand in half-square heights) %s' % seen)
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_thick_land(q):  # owner 25 Nov: land squares are blocks with some thickness: walls of earth under the top's front edges, the sea below them
#     table(q, bag=[[0, 4]] * 4); a, c = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hh = c[1] - a[1]
#     x, y = q.evaluate("()=>__dg.square(5,10)"); px = lambda dy: q.evaluate("([x,y])=>__dg.pixel(x,y)", [x, y + hh + dy * hh])[:3]  # under the start tile's front corner
#     wet = lambda p: p[2] > p[0] + 30; wall, sea = px(0.4), px(1.3)
#     report(not wet(wall) and wet(sea), 'land: blocks with walls over the sea', 'under the front corner: %s at 0.4 of a half square, %s at 1.3' % (wall, sea))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_moving_water(q):  # owner 25 Nov: the water moves (ripples drift over it, foam around the land); the land stays still (test pages keep the water still unless asked: it costs the run)
#     pause_clock(q); table(q, fast=False, stillWater=False, bag=[[0, 4]] * 4); spot = q.evaluate("()=>__dg.square(8,2)"); land = q.evaluate("()=>__dg.square(4,10)")
#     look = lambda: [q.evaluate("([x,y])=>__dg.pixel(x,y)", [p[0] + dx, p[1] + dy])[:3] for p in (spot, land) for dx in (-9, -3, 3, 9) for dy in (-4, 4)]
#     a = look(); skip(q, 1500); b = look(); q.clock.resume()
#     moved = sum(1 for k in range(8) if a[k] != b[k]); still = all(a[k] == b[k] for k in range(8, 16))
#     report(moved >= 4 and still and drawn(q, 'foam'), 'water: it moves, the land does not', 'sea pixels changed %d of 8, land unchanged %s, foam %s' % (moved, still, bool(drawn(q, 'foam'))))
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_borders(q):  # each player's land has a border all around: green for the kid, red for the PC; a tile's two halves meet with no gap (no sea between them)
#     table(q, bag=[[0, 4]] * 4); b = drawn(q, 'border'); kid = sum(1 for x in b if x['o'] == 0); pc = sum(1 for x in b if x['o'] == 1)
#     seam = q.evaluate("()=>__dg.edge(4,10,0)"); mid = q.evaluate("(p)=>__dg.pixel(p[0],p[1]+4)", seam)[:3]
#     ok = kid == 6 and pc == 6 and not mid[2] > mid[0] + 30
#     report(ok, 'borders: all around each land, halves joined', 'kid edges %d, pc edges %d, seam %s' % (kid, pc, mid))
MAIN_SEED, MAIN_JARS = 3, ['coins', 'empty', 'first', 'jar', 'tile', 'coins2', 'set']  # the main game's fixed pile (made by this seed) and the jar contents queued, in order
# owner 28 Nov: "comment out old tests": off until updated to the design phase
# def f_main_game(q):  # owner 24 Nov: one main test plays a whole game with a fixed pile and fixed jar contents, so every situation happens in order; at each situation it checks that situation's rules, and after every move what he sees adds up
#     out = q.evaluate("""async ([seed, kinds]) => {
#       const cv = document.querySelector('#c'), errs = [], did = {}, err = m => errs.push(m);
#       const tick = async () => { for (let k = 0; k < 300; k++) await null; };
#       const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
#       const tap = async p => { if (!p) { err('nothing to tap at ' + JSON.stringify(__dg.state().wait)); return; } __dg.render(); ev('pointerdown', p); ev('pointerup', p); await tick(); };
#       const drag = async (a, b) => { if (!a || !b) { err('nothing to drag at ' + JSON.stringify(__dg.state().wait)); return; } __dg.render(); ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
#       const seen = kind => __dg.drawn().filter(d => d.k === kind), btn = id => { __dg.render(); return __dg.btn(id); };  // buttons are where the last picture put them: draw first
#       const sum = a => a.reduce((x, y) => x + y, 0), DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1]];
#       const lit = starts => { const sq2 = seen('square'), on = (x, y) => sq2.find(d => d.x === x && d.y === y), done = new Set(), todo = starts.slice(); while (todo.length) { const [x, y] = todo.shift(), a = on(x, y); if (!a || done.has(x + ',' + y)) continue; done.add(x + ',' + y); [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const b = on(x + dx, y + dy); if (b && b.c === a.c) todo.push([x + dx, y + dy]); }); } return done.size; };  // the squares the connections light, on the board shown (owner 25 Nov)
#       __dg.restart({ seed, fast: true, jarQueue: kinds.map(k => ({ k })) }); await tick();
#       { const s = __dg.state(), starts = s.tiles.map(t => t.slice(0, 5).join()).sort();  // the start: the same start tile for both, the two most common colours, at the centres of the board's halves; nobody has the token; the kid picks first
#         if (starts.join('|') !== '11,5,2,0,1|4,10,0,0,1' || s.draft.length !== 4 || !s.wait || s.wait.kind !== 'pick' || s.wait.who !== 0 || s.first !== null) err('start: ' + JSON.stringify([starts, s.wait, s.first])); }
#       let putBack = false, picked = -1, prev = __dg.state(), afterPass = 0; const total = prev.left;  // every tile of the pile
#       for (let step = 0; ; step++) {
#         await tick(); const s = __dg.state(), w = s.wait; __dg.render();
#         if (step > 4000 || errs.length > 5) { err('stuck at ' + JSON.stringify(w)); break; }
#         for (const o of [0, 1]) if (seen('coin').filter(d => d.o === o).length + seen('endcoin').filter(d => d.o === o).length !== s.players[o].coins) err('round ' + s.round + ': coins shown for ' + o + ' differ');  // in his area, or at the end in his pile
#         if (s.over) {  // the end: no tile left can be placed by either player (none thrown); most coins wins, his star shown
#           const [a, b] = s.players.map(p => p.coins), win = a > b ? 0 : b > a ? 1 : -1, star = seen('winner');
#           if (s.leftFits) err('end: a tile left still fits');
#           if (s.winner !== win || (win >= 0 && (star.length !== 1 || star[0].o !== win))) err('end: winner ' + s.winner + ' for coins ' + [a, b]);
#           did.end = true; break;
#         }
#         if (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left !== total) err('a tile was thrown away: board, hand and left make ' + (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left));  // no tile is ever thrown: not when he passes, not at the round's end (the tile in hand counts)
#         for (const o of [0, 1]) for (let c = 0; c < 6; c++) if (seen('good').filter(d => d.o === o && d.c === c).length !== s.players[o].goods[c]) err('round ' + s.round + ': goods shown differ for ' + o);
#         if (__dg.sounds().includes('dissolve')) err('round ' + s.round + ': goods were lost');  // goods carry over between rounds (owner 24 Nov)
#         if (s.passes[0] > prev.passes[0]) { did.pass = true; afterPass = prev.round === s.round && s.phase === 'round' ? { round: s.round, got: prev.players[1].got, passes: prev.passes[1] } : 0; }  // a pass seen across a round's end is not checked: the new round may start with him  // nothing fits him: his turn passes, no tile is thrown
#         if (afterPass && w && w.who === 0 && w.kind === 'pick') { const a = afterPass; afterPass = 0; if (a.round === s.round && s.players[1].got === a.got && s.passes[1] === a.passes) err('pass: the PC did not play again ' + JSON.stringify({ a, got: s.players[1].got, passes: s.passes, round: s.round, draft: s.draft, fits1: s.draft.map(t => !!t) })); }  // and the PC plays again (it took a tile, or it passed too)
#         prev = s;
#         if (!w || w.who !== 0) continue;
#         if (w.kind === 'pick') {
#           if (s.players.some(p => p.goods.some(g => g >= 5))) err('round ' + s.round + ': 5 of a colour not made into a jar');  // at once (owner 24 Nov)
#           s.fits.forEach((f, k) => { if (f || !s.draft[k]) return; const d = seen('tile').find(t => t.id === 'draft-' + k);  // a tile he can't pick: greyed, its colours kept, not tappable
#             did.unusable = true;
#             if (!d || d.look !== 'grey' || d.cs.join() !== s.draft[k].join() || __dg.btn('draft-' + k)) err('greyed: tile ' + k + ' ' + JSON.stringify(d)); });
#           const spare = [0, 1].find(n => btn('extra-' + n)); if (spare != null) { picked = -1; await tap(btn('extra-' + spare)); continue; }  // owner 28 Nov: an extra tile is used for free, before he picks
#           if (s.round >= 2 && !did.changer && btn('changer')) {  // owner 28 Nov: the land changer: a tap turns it to the first land, a drag onto a square of another land turns that square
#             await tap(btn('changer')); await tap(__dg.held()); await tap(btn('changer'));  // taken, then a tap on it in hand turns it to the first land; taken again
#             const sq = seen('square').find(d => d.c !== 0 && d.o === 0); if (sq) { await drag(__dg.held(), __dg.square(sq.x, sq.y)); __dg.render(); did.changer = seen('square').some(d => d.x === sq.x && d.y === sq.y && d.c === 0) && !btn('changer'); } continue; }
#           const k = s.fits.indexOf(true); picked = k; await tap(btn('draft-' + k));
#           if (!putBack && s.round >= 2 && __dg.state().wait && __dg.state().wait.kind === 'place') { await drag(__dg.held(), [innerWidth - 60, 400]); await drag(__dg.held(), __dg.slot(k)); putBack = did.putBack = __dg.state().draft[k] !== null && __dg.state().wait.kind === 'pick'; }
#         }
#         else if (w.kind === 'place') {
#           if (picked < 0) did.bonusTile = true; picked = -1;
#           const sp = s.spots.reduce((a, b) => b.m > a.m ? b : a);
#           while (__dg.state().wait.r !== sp.r) { await tap(__dg.held()); __dg.render(); }
#           const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), held = sp.cs, d = DIRS[sp.r];  // the colours it gets there (a wild tile takes its neighbours')  // matching edges with any land, counted on the board shown
#           let edges = 0; const starts = []; [[sp.x, sp.y], [sp.x + d[0], sp.y + d[1]]].forEach(([x, y], h) => DIRS.forEach(([dx, dy]) => { const n = at(x + dx, y + dy); if (n && n.c === held[h]) { edges++; starts.push([x, y], [x + dx, y + dy]); } }));
#           const g0 = sum(s.players[0].goods);
#           await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)); __dg.render();
#           const t = __dg.state(), g = seen('good').filter(d => d.o === 0).length, five = t.players[0].jars - s.players[0].jars - edges, n = lit(starts);  // his new jars wait for his taps: a jar per connection, a material per lit square, each 5 of a colour a jar at once
#           if (five < 0 || g + 5 * five !== g0 + n || t.players[0].goods.some(x => x >= 5)) err('round ' + s.round + ': ' + edges + ' connections lighting ' + n + ' squares, goods ' + g0 + ' -> ' + g + ' and ' + (five + edges) + ' jars');
#         }
#         else if (w.kind === 'jar') { const n = s.players[0].jars; await tap(btn('jar-0')); if (__dg.state().players[0].jars >= n) did.moreJars = true; }  // a jar that brings another jar, or goods that make one
#       }
#       return { errs: errs.slice(0, 5), did, left: __dg.state().queued };
#     }""", [MAIN_SEED, MAIN_JARS])
#     want = ['unusable', 'pass', 'putBack', 'bonusTile', 'changer', 'moreJars', 'end']
#     missing = [k for k in want if not out['did'].get(k)]
#     report(not out['errs'] and not missing and out['left'] == 0, 'main game: every situation, what he sees adds up', 'missing %s, errors %s, jar contents left %s' % (missing, out['errs'], out['left']))
#
def f_simulation(q):  # owner 25 Nov (task list): a simulation tool plays seeded games through the screen and reports jars, coins and bonus shares per player
    import sim; r = sim.play(q, [1])[0]
    shares = all(sum(p['opened'].values()) == p['jars'] for p in r['players'])
    ok = r['over'] and shares and [p['coins'] for p in r['players']] == r['shown'] and all(p['jars'] > 0 for p in r['players'])
    report(ok, 'simulation: jars, coins and bonus shares per player', '%s' % r)

def f_random_play(q):  # seeded games played through the screen (taps and drags on what is drawn, at random moments); after every move, what he can see holds:
    # a placement gives a jar per connection and a material per square it lights, on the board shown; each 5 of a colour a jar at once
    bad = q.evaluate("""async (DECK) => {
      const cv = document.querySelector('#c'), ch = new MessageChannel(), errs = [];
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };  // let the game's answers run (they are promise steps in fast mode); no timer, no message: those wait for the browser
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { ev('pointerdown', p); ev('pointerup', p); await tick(); };  // the game answers after the event: wait for it
      const drag = async (a, b) => { ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = kind => __dg.drawn().filter(d => d.k === kind);
      const lit = starts => { const sq2 = seen('square'), on = (x, y) => sq2.find(d => d.x === x && d.y === y), done = new Set(), todo = starts.slice(); while (todo.length) { const [x, y] = todo.shift(), a = on(x, y); if (!a || done.has(x + ',' + y)) continue; done.add(x + ',' + y); [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const b = on(x + dx, y + dy); if (b && b.c === a.c) todo.push([x + dx, y + dy]); }); } return done.size; };  // the squares the connections light, on the board shown (owner 25 Nov)
      for (let seed = 1; seed <= 4; seed++) {
        let rs = seed * 7919; const rand = n => { rs = (rs * 16807) % 2147483647; return rs % n; };
        __dg.restart({ seed, fast: true, deck: DECK });
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
        }
        if (errs.length > 5) break;
      }
      return errs.slice(0, 5);
    }""", SETTINGS['deck'])
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
            NOW[0] = n; t0 = time.time()
            try: q.mouse.up(); table(q); FLOWS[n](q)
            except Exception as e:
                try: s = st(q); seen = 'wait %s, phase %s, round %s' % (s['wait'], s['phase'], s['round'])
                except Exception: seen = ''
                report(False, n, 'error: %s; %s' % (str(e).splitlines()[0][:100], seen))
            print('time [%s] %.1f s' % (n, time.time() - t0))  # every step's time: the slowest is made faster first
        b.close()
