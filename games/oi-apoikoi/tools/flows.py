# Flow tests: what the owner does, in the running game: real page, real mouse taps and drags on what he sees.
# One browser and one page for the whole run: each flow starts a new game with a set table (fast: the PC's hand moves without waiting)
# and prints PASS or FAIL, [its flow name], what it checks, and what was seen. Waits are on the game's state, never on a fixed sleep.
# Colours are numbered 0-4 (0 the most common); a tile is [first half, second half]; the board is 20 x 13 squares, the start tiles [0, 1] at (4, 6) and (14, 6).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'coins'}, {'k': 'coins2'}, {'k': 'slot'}, {'k': 'steal'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib, datetime
from playwright.sync_api import sync_playwright
GAME = next((pathlib.Path(__file__).resolve().parent.parent).glob('*.html'))  # this copy's own built page (whatever its name then), so old and new code can be tested at once
COIN = {'k': 'coins'}
NOW = ['']  # the flow running, for the report lines
WAIT = 1500  # ms: the game answers in a few ms in fast mode, so a flow that waits longer has failed; short waits keep failing runs short

# SECTION: HELPERS -- the page, a set table, taps and drags on what is drawn, the game's state
def settle(q): q.evaluate("()=>__dg.render()")  # the game answers a tap at once; draw it now, so what is on screen (and its buttons) is current
def table(q, **opts): opts.setdefault('fast', True); q.evaluate("(o)=>__dg.restart(o)", opts); settle(q)
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

def f_drag_from_pile(q):  # owner 24 Nov: no tap first: press a tile in the pile and drag it straight to its place; a plain tap still just takes it, unturned
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8)
    path(q, q.evaluate("()=>__dg.btn('draft-0')"), q.evaluate("()=>__dg.tileAt(4,5,0)"))
    placed = [4, 5, 0, 0, 4] in [t[:5] for t in st(q)['tiles'] if t[5] == 0]
    table(q, bag=[[0, 4]] * 4); tap(q, 'draft-0'); w = st(q)['wait']
    report(placed and w == {'kind': 'place', 'who': 0, 'r': 0}, 'pile: drag straight from the pile', 'placed %s; after a tap %s' % (placed, w))

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

def f_pile_no_frames(q):  # owner 24 Nov: no outline around the pile's tiles
    table(q, bag=[[0, 4]] * 4); c = q.evaluate("()=>__dg.btn('draft-0')"); ds = round(min(q.evaluate("()=>innerHeight*0.16") * 0.42, 60))
    beside = q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [c[0] - ds - 6, c[1]])  # just left of the tile: nothing drawn there (the page shows through), not a frame
    report(beside[3] == 0, 'pile: tiles have no outline', 'beside the tile %s' % beside)

def f_greyed(q):  # tiles you can't pick are greyed but keep their colour, and can't be tapped
    table(q, bag=[[0, 4], [2, 3], [0, 4], [0, 4]]); s = st(q); d = {x['id']: x for x in drawn(q, 'tile')}
    ok = s['fits'] == [True, False, True, True] and q.evaluate("()=>!__dg.btn('draft-1')") and d['draft-1']['look'] == 'grey' and d['draft-1']['cs'] == [2, 3] and d['draft-0']['look'] is None
    report(ok, 'greyed: unfit tile not tappable, colours kept', 'fits %s, drawn %s' % (s['fits'], d.get('draft-1')))

def f_pass_other_plays(q):  # nothing fits you: your turn passes, clearly, and the PC plays again; no tile is thrown
    table(q, bag=[[3, 4]] * 4 + [[0, 0]] * 4, tiles=[[14, 7, 0, 3, 3, 1]], jarQueue=[COIN] * 20)
    q.wait_for_function("()=>__dg.state().round===2", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1].count([3, 4])
    report(s['passes'][0] >= 1 and pc == 4, 'pass: turn passes, PC plays again', 'kid passes %d, PC took %d' % (s['passes'][0], pc))

def f_end_rule(q):  # the game ends when no tile left can be placed by either player; no tile is thrown
    table(q, bag=[[2, 3]] * 4); q.wait_for_function("()=>__dg.state().over", timeout=WAIT, polling=5); s = st(q)
    report(s['left'] == 4, 'end: nothing placeable, game over', 'tiles left %d' % s['left'])

def f_goods_at_start(q):  # each square makes 1 good of its colour at the start of the round, the start tile too
    table(q, bag=[[0, 4]] * 4, tiles=[[4, 7, 0, 2, 2, 0]]); g = st(q)['players'][0]['goods']
    report(g == [1, 1, 2, 0, 0], 'goods: 1 per square at round start', str(g))

def f_goods_on_place(q):  # owner 24 Nov: a land's goods appear in the stockpile as soon as it is placed, not only at the round's start
    table(q, bag=[[0, 4]] * 4, jarQueue=[COIN] * 8); before = [sum(1 for x in drawn(q, 'good') if x['o'] == 0 and x['c'] == c) for c in range(5)]
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); settle(q)
    after = [sum(1 for x in drawn(q, 'good') if x['o'] == 0 and x['c'] == c) for c in range(5)]
    report(before == [1, 1, 0, 0, 0] and after == [2, 1, 0, 0, 1], 'goods: a placed land adds its goods at once', 'before %s after %s' % (before, after))

def f_stockpile_columns(q):  # owner 24 Nov: goods stand in a column per colour (they never widen the panel); rows of one of each are marked as sets, each 3 of a colour as a jar at the round's end
    tiles = [[0, 0, 0, 0, 1, 0], [2, 0, 0, 0, 1, 0], [4, 0, 0, 0, 1, 0], [0, 1, 0, 2, 2, 0], [2, 1, 0, 2, 2, 0], [4, 1, 0, 2, 2, 0], [6, 0, 0, 2, 3, 0], [6, 1, 0, 3, 4, 0]]
    table(q, bag=[[0, 4]] * 4, tiles=tiles); g = drawn(q, 'good'); g = [x for x in g if x['o'] == 0]
    cols = {c: {round(x['x']) for x in g if x['c'] == c} for c in range(5)}; counts = [sum(1 for x in g if x['c'] == c) for c in range(5)]
    panel = q.evaluate("()=>innerWidth*0.13"); inside = all(x['x'] < panel for x in g)
    jars = [sum(1 for x in drawn(q, 'jargroup') if x['o'] == 0 and x['c'] == c) for c in range(5)]; sets = sum(1 for x in drawn(q, 'setrow') if x['o'] == 0)
    ok = counts == [4, 4, 7, 2, 1] and all(len(v) == 1 for c, v in cols.items() if counts[c]) and inside and jars == [1, 1, 2, 0, 0] and sets == 1
    report(ok, 'stockpile: columns, sets and jar groups shown', 'goods %s, one column each %s, jar groups %s, set rows %d' % (counts, all(len(v) == 1 for c, v in cols.items() if counts[c]), jars, sets))

def f_sets_of_five(q):  # a set is 5 goods, one of each; the PC bids when it pays; a tie goes to the picker; only the winner pays
    kid, pc = [[4, 4, 0, 2, 3, 0], [4, 2, 0, 4, 4, 0]], [[14, 4, 0, 2, 3, 1], [14, 2, 0, 4, 4, 1]]
    table(q, bag=[[0, 1], [0, 0], [0, 0], [0, 0]], tiles=kid + pc)
    tap(q, 'draft-0'); waiting(q, 'bid'); s = st(q); pc_bid = s['players'][1]['bid']
    tap(q, 'bid'); waiting(q, 'place'); s = st(q)
    ok = pc_bid == 1 and s['players'][0]['goods'] == [0, 0, 0, 0, 1] and s['players'][1]['goods'] == [1, 1, 1, 1, 2]
    report(ok, 'bid: sets of 5, tie to picker, winner pays', 'pc bid %d, kid %s, pc %s' % (pc_bid, s['players'][0]['goods'], s['players'][1]['goods']))

def f_bid_locks(q):  # owner 24 Nov: winning a bid does not take the tile, it locks it: greyed for the other player, only the winner can pick it later
    kid, pc = [[4, 4, 0, 2, 3, 0], [4, 2, 0, 4, 4, 0]], [[14, 4, 0, 2, 3, 1], [14, 2, 0, 4, 4, 1]]
    table(q, bag=[[0, 1], [0, 0], [0, 0], [0, 0]], tiles=kid + pc, jarQueue=[COIN] * 20)
    tap(q, 'draft-0'); waiting(q, 'bid'); tap(q, 'letgo'); waiting(q, 'pick'); s = st(q)
    d = {x['id']: x for x in drawn(q, 'tile')}
    locked = s['draft'][0] == [0, 1] and q.evaluate("()=>!__dg.btn('draft-0')") and d['draft-0']['look'] == 'grey' and s['players'][1]['goods'] == [0, 0, 0, 0, 1]
    tap(q, 'draft-1'); waiting(q, 'place'); drag_to(q, best_spot(q))
    s = kid_plays(q, lambda s: any(t[5] == 1 and t[3:5] == [0, 1] and t[:2] != [14, 6] for t in s['tiles']) or s['round'] > 1)
    pc_took = any(t[5] == 1 and t[3:5] == [0, 1] and t[:2] != [14, 6] for t in s['tiles'])
    report(locked and pc_took, 'bid: winner locks the tile, picks it later', 'locked for kid %s, PC took it later %s' % (locked, pc_took))

def f_leftovers_jar(q):  # at the end of the round each 3 of the same leftover good make a jar; the rest are lost (placed tiles' goods count too, owner 24 Nov)
    table(q, bag=[[0, 0]] * 4, tiles=[[4, 2, 0, 2, 2, 0], [4, 3, 0, 2, 2, 0], [6, 3, 0, 2, 2, 0]], jarQueue=[COIN] * 20)
    kid_plays(q, lambda s: s['phase'] == 'end'); waiting(q, 'jar'); p = st(q)['players'][0]
    report(p['jars'] == 3 and p['goods'] == [0, 0, 0, 0, 0], 'end: each 3 same leftovers a jar', 'jars %d goods %s' % (p['jars'], p['goods']))

def f_goods_become_jars(q):  # owner 24 Nov: at the round's end the goods turn into jars one by one, visibly; then the leftovers fade out
    pause_clock(q)  # the kid's last tile ends the round: 8 goods, 6 of one colour (2 jars), 2 left over
    table(q, fast=False, bag=[[2, 2]], tiles=[[4, 7, 0, 2, 2, 0], [4, 8, 0, 2, 2, 0]], jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 9, 'r': 0}); q.clock.run_for(1200); waiting(q, 'jar'); tap(q, 'jar-0')  # the jars fly out of the matched edges first
    made, flying, faded, shown_left, ms = {}, False, False, {}, 0
    while ms < 5000:
        q.clock.run_for(100); ms += 100; settle(q); d = q.evaluate("()=>__dg.drawn()")
        jars = sum(1 for x in d if x['k'] == 'jar' and x['o'] == 0 and not x.get('growing'))
        goods = sum(1 for x in d if x['k'] in ('good', 'flying') and x['o'] == 0)
        flying = flying or any(x['k'] == 'flying' for x in d); faded = faded or any(x['k'] == 'good' and x.get('a', 1) < 1 for x in d)
        if jars not in made: made[jars] = ms; shown_left[jars] = goods
        if st(q)['wait'] and st(q)['wait']['kind'] == 'jar': break
    q.clock.resume()
    ok = sorted(made) == [0, 1, 2] and made[2] - made[1] >= 500 and flying and faded and shown_left[1] == 5 and st(q)['players'][0]['jars'] == 2
    report(ok, 'end: goods become jars one by one', 'jar counts first seen at %s ms, goods then %s, flying %s, fading %s' % (made, shown_left, flying, faded))

def f_sounds(q):  # owner 24 Nov: "add some sounds, it's hard to follow what happens": each thing that happens has its sound, in the order it happens
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot'); tap(q, 'wheel-2'); tap(q, 'reroll')
    q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); a = q.evaluate("()=>__dg.sounds()")
    table(q, bag=[[0, 0]] * 4, tiles=[[4, 2, 0, 2, 2, 0], [4, 3, 0, 2, 2, 0], [6, 3, 0, 2, 2, 0]], jarQueue=[COIN] * 20)
    kid_plays(q, lambda s: s['phase'] == 'end'); waiting(q, 'jar'); b = q.evaluate("()=>__dg.sounds()")
    want = ['pick', 'snap', 'edge', 'jar', 'roll', 'roll', 'roll', 'spin', 'stop', 'stop', 'stop', 'roll', 'spin', 'stop', 'win']  # each wheel ticks as it rolls (owner 24 Nov)
    made = sum(p['jars'] for p in st(q)['players'])  # both players' leftovers have become jars; none opened yet
    ok = a[:len(want)] == want and b.count('made') == made and {'pick', 'snap', 'jar', 'coin'} <= set(b) and b.index('made') > b.index('snap')
    report(ok, 'sounds: one for each thing, in order', 'slot jar: %s; round end: %d made sounds for %d jars, heard %s' % (a[:len(want)], b.count('made'), made, sorted(set(b))))

def f_round_end_in_turn(q):  # owner 24 Nov: at the round's end one player turns his goods into jars and opens them, then the other; not mixed
    table(q, bag=[[0, 0]] * 4, tiles=[[4, 2, 0, 2, 2, 0], [4, 3, 0, 2, 2, 0], [6, 3, 0, 2, 2, 0]], jarQueue=[COIN] * 30)
    kid_plays(q, lambda s: s['phase'] == 'end'); waiting(q, 'jar')
    pc_goods = sum(1 for x in drawn(q, 'good') if x['o'] == 1); pc_made = q.evaluate("()=>__dg.sounds()").count('made') - st(q)['players'][0]['jars']; pc_coins = st(q)['players'][1]['coins']
    kid_plays(q, lambda s: s['wait'] and s['wait']['who'] == 1 or s['round'] > 1); after = st(q)['players'][1]
    ok = pc_goods > 0 and pc_made == 0 and after['coins'] > pc_coins
    report(ok, 'end: one player gains and opens, then the other', 'PC goods shown while the kid opens %d, PC jars made by then %d; PC coins %d then %d' % (pc_goods, pc_made, pc_coins, after['coins']))

def f_sound_kinds(q):  # owner 24 Nov: "a weird blip when I tap a piece"; "jars must make a breaking sound": a tap knocks like wood, a jar breaks like clay, a coin clinks; no beeps anywhere
    get_jar(q, [COIN]); settle(q); h = q.evaluate("()=>__dg.heardKinds()")
    ok = h[:5] == ['knock', 'knock', 'chime', 'break', 'clink']  # tap, snap, the jar out of its edge, the jar opened, its coin
    ok = ok and set(q.evaluate("()=>__dg.soundKinds()")) <= {'break', 'chime', 'clink', 'knock', 'whoosh'}
    report(ok, 'sounds: wood tap, clay break, coin clink', 'heard %s; kinds in the game %s' % (h[:5], q.evaluate("()=>__dg.soundKinds()")))

def f_jars_from_edges(q):  # owner 24 Nov: show which edges matched, and each jar comes out of its matched edge; a snap sound
    pause_clock(q); table(q, fast=False, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0})
    edges = [q.evaluate("([x,y,d])=>__dg.edge(x,y,d)", e) for e in ([4, 7, 3], [5, 7, 3])]
    near = lambda js: sorted(min(((j['x'] - e[0]) ** 2 + (j['y'] - e[1]) ** 2) ** 0.5 for e in edges) for j in js)
    size, glows, seen = 40, 0, [False, False]  # each edge seen with a jar just out of it
    for n_ in range(16):
        q.clock.run_for(10 if n_ == 0 else 50); settle(q); glows = max(glows, len(drawn(q, 'edgeglow')))
        for j in drawn(q, 'jar'):
            for n, e in enumerate(edges): seen[n] = seen[n] or ((j['x'] - e[0]) ** 2 + (j['y'] - e[1]) ** 2) ** 0.5 < size
    early = seen
    q.clock.run_for(1500); settle(q); late = near([j for j in drawn(q, 'jar') if j['o'] == 0]); h = q.evaluate("()=>__dg.sounds()"); q.clock.resume()
    ok = glows == 2 and all(seen) and len(late) == 2 and min(late) > 3 * size and h[:3] == ['pick', 'snap', 'edge'] and h.count('edge') == 2
    report(ok, 'jars: matched edges glow, jars come out of them', 'edges glowing %d; a jar seen at each edge %s, then %s px away; sounds %s' % (glows, seen, [round(v) for v in late], h[:4]))

def f_jars_apart(q):  # owner 24 Nov: "jar circles are touching": every jar and its glow stands apart, with a clear gap
    table(q, bag=[[0, 1]] * 4, jarQueue=[COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0}); waiting(q, 'jar'); settle(q)
    jars = sorted((d['x'], d['size'] / 2) for d in drawn(q, 'jar')); glows = sorted((d['x'], d['r']) for d in drawn(q, 'jarglow'))
    gaps = [b[0] - a[0] - a[1] - b[1] for row in (jars, glows) for a, b in zip(row, row[1:])]
    ok = len(jars) == 2 and len(glows) == 2 and min(gaps) >= 12
    report(ok, 'jars: apart, with a gap between them', 'gaps between jars and between glows %s px' % [round(g) for g in gaps])

def f_round_end_shown(q):  # owner 24 Nov: the round's end must be its own phase, clearly seen and heard, before anything else happens in it
    pause_clock(q); table(q, fast=False, bag=[[2, 2]], tiles=[[4, 7, 0, 2, 2, 0], [4, 8, 0, 2, 2, 0]], jarQueue=[COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 9, 'r': 0}); q.clock.run_for(1200); waiting(q, 'jar'); tap(q, 'jar-0')
    shown, first_made, ms = [], None, 0
    while ms < 4000 and first_made is None:
        q.clock.run_for(100); ms += 100; settle(q)
        if drawn(q, 'sunset'): shown.append(ms)
        if 'made' in q.evaluate("()=>__dg.sounds()"): first_made = ms
    q.clock.resume(); h = q.evaluate("()=>__dg.sounds()")
    ok = len(shown) >= 10 and first_made is not None and max(shown) <= first_made and 'roundend' in h and h.index('roundend') < h.index('made')
    report(ok, 'end: the round end is its own moment, seen and heard', 'sunset shown %d00 ms (from %s to %s), first jar made at %s ms, round end sound %s' % (len(shown), shown[:1], shown[-1:], first_made, 'roundend' in h))

def f_pc_best(q):  # the PC picks and places for the most jars
    table(q, bag=[[0, 0], [0, 1], [0, 4], [0, 4]], first=1, jarQueue=[COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] != [14, 6]]
    report(pc == [[0, 1]] and s['players'][1]['coins'] == 2, 'pc: best tile, best place', 'pc tiles %s coins %d' % (pc, s['players'][1]['coins']))

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

def f_pc_slot(q):  # the PC takes the best expected result on the slot machine too
    table(q, bag=[[0, 4]] * 4, first=1, coins=[0, 5], jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[5, 5, 1])
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); c = st(q)['players'][1]['coins']
    report(c == 7, 'pc: slot machine played for the most', 'pc coins %d' % c)

def f_jar_mix(q):  # half the jars hold 1 coin (a coins jar always holds 1); 2 coins is one of the bonuses
    m = q.evaluate("()=>__dg.sampleJars(4000)")
    ok = set(m) == {'coins', 'coins2', 'slot', 'steal', 'first', 'tile', 'jar', 'set'} and 0.45 < m['coins'] / 4000 < 0.55
    report(ok, 'jars: 1 coin half the time', str(m))

def f_jar_labels(q):  # owner 24 Nov: "for bonus jars add some text, I don't get what some of those mean": every jar's contents carry a short label
    seen = {}
    for k in ['coins', 'coins2', 'slot', 'steal', 'first', 'tile', 'jar', 'set']:
        table(q, bag=[[0, 4]] * 4, fast=False, jarQueue=[{'k': k}] + [COIN] * 8)
        tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0')
        seen[k] = [d['text'] for d in drawn(q, 'label')]
    ok = all(len(v) == 1 and v[0] for v in seen.values()) and len({v[0] for v in seen.values() if v}) == 8
    report(ok, 'jars: each content has its own label', str(seen))

def f_new_game_mid_jar(q):  # found by the tests: a new game started while a jar is being shown: the old jar never pays into the new game
    pause_clock(q)
    table(q, bag=[[0, 4]] * 4, fast=False, jarQueue=[{'k': 'coins2'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); q.clock.run_for(1200); waiting(q, 'jar'); tap(q, 'jar-0')  # the jars fly out of the matched edges first
    table(q, bag=[[0, 4]] * 4); q.clock.run_for(2000); settle(q); s = st(q); q.clock.resume()
    report(s['players'][0]['coins'] == 0 and s['wait']['kind'] == 'pick', 'new game: an old jar pays nothing into it', 'coins %d, wait %s' % (s['players'][0]['coins'], s['wait']))

def f_coins2(q):  # the 2 coins bonus
    get_jar(q, [{'k': 'coins2'}]); c = st(q)['players'][0]['coins']
    report(c == 2, 'jar: 2 coins', 'coins %d' % c)

def f_slot_rolls(q):  # owner 24 Nov: the wheels roll fast, then slow down and stop one after another (first, second, third), ticking as they pass and knocking as they stop
    pause_clock(q)
    table(q, bag=[[0, 4]] * 4, fast=False, coins=[3, 0], jarQueue=[{'k': 'slot'}] + [COIN] * 8, slotQueue=[0, 0, 1])
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); q.clock.run_for(1200); waiting(q, 'jar'); tap(q, 'jar-0')  # the jars fly out of the matched edges first
    stops, rolling_seen, ms, at = [None] * 3, False, 0, []
    while ms < 4000 and None in stops:
        q.clock.run_for(100); ms += 100; settle(q)
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
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[5, 5, 1]); waiting(q, 'slot'); tap(q, 'wheel-2')
    pics = {d['for']: d for d in drawn(q, 'pic')}; texts = drawn(q, 'label')
    ok = not texts and pics.get('reroll', {}).get('coins') == 1 and pics.get('collect', {}).get('n') == 2 and pics.get('collect', {}).get('s') == 5 and pics.get('coins', {}).get('n') == 3
    report(ok, 'slot: price, prize and coins as pictures, no text', 'texts %s, pictures %s' % ([t['text'] for t in texts], pics))

def f_slot_three(q):  # slot machine: pay 1 coin to reroll chosen wheels; 3 the same wins 3 (on top of the placed tile's own goods, owner 24 Nov)
    get_jar(q, [{'k': 'slot'}], coins=3, slots=[0, 0, 1, 0]); waiting(q, 'slot')
    tap(q, 'wheel-2'); tap(q, 'reroll'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); p = st(q)['players'][0]
    report(p['goods'][0] == 5 and p['coins'] == 2, 'slot: reroll costs a coin, 3 same win 3', 'goods %s coins %d' % (p['goods'], p['coins']))

def f_slot_two(q):  # 2 the same win 2; you can stop at any time
    get_jar(q, [{'k': 'slot'}], coins=0, slots=[5, 1, 5]); waiting(q, 'slot')
    tap(q, 'collect'); q.wait_for_function("()=>!__dg.state().slot", timeout=WAIT, polling=5); p = st(q)['players'][0]
    report(p['coins'] == 2, 'slot: stop with 2 the same wins 2', 'coins %d' % p['coins'])

def f_steal(q):  # steal a PC tile: it is lifted where it lay and you place it; a tile with no place for you can't be stolen
    table(q, bag=[[0, 4]] * 4, tiles=[[14, 7, 0, 0, 0, 1], [14, 2, 0, 3, 3, 1]], jarQueue=[{'k': 'steal'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 6, 'r': 2}); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')
    blocked = q.evaluate("()=>!__dg.btn('steal-t2')"); spot = q.evaluate("()=>__dg.tileAt(14,7,0)"); tap(q, 'steal-t1'); waiting(q, 'place')
    h = held(q); lifted = abs(h[0] - spot[0]) < 2 and abs(h[1] - spot[1]) < 2
    drag_to(q, best_spot(q)); s = st(q); mine = [t[3:5] for t in s['tiles'] if t[5] == 0]; theirs = [t[3:5] for t in s['tiles'] if t[5] == 1]
    report(blocked and lifted and [0, 0] in mine and [0, 0] not in theirs, 'steal: tile moves to you, unfit one blocked', 'blocked %s, lifted there %s, mine %s' % (blocked, lifted, mine))

def f_stolen_tile_jars(q):  # owner 24 Nov: "I stole a tile and made 2 connections, and 5 jars appear": the jars a tile earns are shown apart from jars still waiting
    table(q, bag=[[2, 4], [2, 4]], tiles=[[4, 2, 0, 2, 2, 0], [4, 3, 0, 2, 2, 0], [6, 3, 0, 2, 2, 0], [14, 7, 0, 0, 1, 1]], jarQueue=[COIN] * 2 + [{'k': 'steal'}] + [COIN] * 8)  # only the kid can place these: the PC passes
    for sp in ({'x': 8, 'y': 3, 'r': 0}, {'x': 3, 'y': 2, 'r': 2}):
        waiting(q, 'pick'); tap(q, 'draft-%d' % st(q)['fits'].index(True)); waiting(q, 'place'); drag_to(q, sp); waiting(q, 'jar'); tap(q, 'jar-0')
    q.wait_for_function("()=>__dg.state().phase==='end'", timeout=WAIT, polling=5); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')
    tap(q, 'steal-t4'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 7, 'r': 0}); waiting(q, 'jar')
    jars = drawn(q, 'jar'); new = sum(1 for j in jars if j.get('new'))
    report(len(jars) == 3 and new == 2, 'steal: 2 matches show 2 new jars apart', 'jars shown %d, new %d' % (len(jars), new))

def f_first_token(q):  # the first-player token comes from a jar
    get_jar(q, [{'k': 'first'}]); report(st(q)['first'] == 0, 'first: token comes to you', 'first %s' % st(q)['first'])

def f_free_tile(q):  # a free extra tile from nowhere, always one that fits, placed at once
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'place'); n0 = tile_count(q, 0); ok = len(st(q)['spots']) > 0; drag_to(q, best_spot(q))
    report(ok and tile_count(q, 0) == n0 + 1, 'tile: free tile fits and is placed', 'tiles %d -> %d' % (n0, tile_count(q, 0)))

def f_free_tile_from_jar(q):  # owner 24 Nov: "an extra tile from the jar appears on top of the pile": it comes out of the jar, over the board, not in the pile's row
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'place'); h = held(q); top = q.evaluate("()=>innerHeight*0.16")
    report(h[1] > top + 40, 'free tile: comes out of the jar, not the pile', 'tile at %s, pile row ends at %d' % (h, top))

def f_another_jar(q):  # another jar, which you open yourself
    get_jar(q, [{'k': 'jar'}, {'k': 'coins2'}]); waiting(q, 'jar'); c0 = st(q)['players'][0]['coins']
    tap(q, 'jar-0'); c1 = st(q)['players'][0]['coins']
    report(c1 == c0 + 2, 'jar: another jar to open', 'coins %d -> %d' % (c0, c1))

def f_free_set(q):  # a free set: one of each of the 5 goods (on top of the placed tile's own 2, owner 24 Nov)
    get_jar(q, [{'k': 'set'}]); g = st(q)['players'][0]['goods']
    report(g == [3, 2, 1, 1, 2], 'set: one of each good', str(g))

def f_borders(q):  # each player's land has a border all around: green for the kid, red for the PC; a tile is one rectangle, no gap between its halves
    table(q, bag=[[0, 4]] * 4); b = drawn(q, 'border'); kid = sum(1 for x in b if x['o'] == 0); pc = sum(1 for x in b if x['o'] == 1)
    seam = q.evaluate("()=>__dg.edge(4,6,0)"); mid = q.evaluate("(p)=>__dg.pixel(p[0]-1,p[1])", seam)
    ok = kid == 6 and pc == 6 and mid == [232, 197, 71, 255]
    report(ok, 'borders: all around each land, one rectangle', 'kid edges %d, pc edges %d, seam %s' % (kid, pc, mid))

def f_game_end(q):  # the game ends when the tiles run out; most points wins
    table(q, bag=[[0, 0]] * 4, coins=[20, 2], jarQueue=[COIN] * 20)
    s = kid_plays(q, lambda s: s['over'])
    report(s['over'] and s['winner'] == 0, 'end: tiles run out, most coins wins', 'winner %s coins %s' % (s['winner'], [p['coins'] for p in s['players']]))

def f_random_play(q):  # seeded games played through the screen (taps and drags on what is drawn, at random moments); after every move, what he can see holds:
    # at a round's start each player's goods shown match his land shown; the jars shown after a placement match its matching edges on the board shown
    bad = q.evaluate("""async () => {
      const cv = document.querySelector('canvas'), ch = new MessageChannel(), errs = [];
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };  // let the game's answers run (they are promise steps in fast mode); no timer, no message: those wait for the browser
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { ev('pointerdown', p); ev('pointerup', p); await tick(); };  // the game answers after the event: wait for it
      const drag = async (a, b) => { ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = kind => __dg.drawn().filter(d => d.k === kind);
      for (let seed = 1; seed <= 4; seed++) {
        let rs = seed * 7919; const rand = n => { rs = (rs * 16807) % 2147483647; return rs % n; };
        __dg.restart({ seed, fast: true }); let lastRound = 0;
        for (let step = 0; ; step++) {
          for (let k = rand(3); k >= 0; k--) await tick();
          const s = __dg.state(), w = s.wait;
          if (s.over) break;
          if (step > 3000) { errs.push('seed ' + seed + ' stuck at ' + JSON.stringify(w)); break; }
          if (s.round !== lastRound && s.players.every(p => p.got === 0)) {  // a new round, nothing taken yet
            lastRound = s.round; __dg.render();
            for (const o of [0, 1]) for (let c = 0; c < 5; c++) {
              const land = seen('square').filter(d => d.o === o && d.c === c).length, goods = seen('good').filter(d => d.o === o && d.c === c).length;
              if (land !== goods) errs.push('seed ' + seed + ' round ' + s.round + ': player ' + o + ' colour ' + c + ' land ' + land + ' goods ' + goods);
            }
          }
          if (!w || w.who !== 0) continue;
          __dg.render(); const btn = id => __dg.btn(id);  // draw first: buttons are where the last picture put them
          if (w.kind === 'pick') { const ok = s.fits.map((f, i) => f ? i : -1).filter(i => i >= 0); if (!ok.length) { errs.push('seed ' + seed + ' pick with nothing to pick'); break; } await tap(btn('draft-' + ok[rand(ok.length)])); }
          else if (w.kind === 'bid') await tap(btn(rand(2) ? 'bid' : 'letgo'));
          else if (w.kind === 'place') {
            if (!s.spots.length) { errs.push('seed ' + seed + ' a tile with no place'); break; }
            const sp = s.spots[rand(s.spots.length)];
            while (__dg.state().wait.r !== sp.r) { await tap(__dg.held()); __dg.render(); }
            const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), d = [[1, 0], [0, 1], [-1, 0], [0, -1]][sp.r], cs = [__dg.drawn().find(e => e.id === 'held').cs[0], __dg.drawn().find(e => e.id === 'held').cs[1]];
            const hs = [[sp.x, sp.y], [sp.x + d[0], sp.y + d[1]]]; let edges = 0;
            hs.forEach(([x, y], h) => [[1, 0], [0, 1], [-1, 0], [0, -1]].forEach(([dx, dy]) => { const n = at(x + dx, y + dy); if (n && n.c === cs[h]) edges++; }));
            await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)); __dg.render();
            const jars = seen('jar').filter(j => j.o === 0 && j.new).length;
            if (jars !== edges) errs.push('seed ' + seed + ': ' + edges + ' matching edges on the board, ' + jars + ' new jars shown');
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
            except Exception as e:
                try: s = st(q); seen = 'wait %s, phase %s, round %s' % (s['wait'], s['phase'], s['round'])
                except Exception: seen = ''
                report(False, n, 'error: %s; %s' % (str(e).splitlines()[0][:100], seen))
        b.close()
