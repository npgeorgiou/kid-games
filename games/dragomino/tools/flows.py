# Flow tests: what the owner does, in the running game: real page, real mouse clicks on what he sees.
# Each flow starts a game with a set table (?fast: the PC moves without waiting) and prints PASS or FAIL, its name, and what was seen.
# Colours are numbered 0-4 (the five lands); a tile is [first half, second half]; a land square is [x, y, colour].
# Jar contents a test needs are queued: {'k': 'coins', 'n': 2}, {'k': 'slot'}, {'k': 'steal'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, json, pathlib
from playwright.sync_api import sync_playwright
GAME = pathlib.Path(__file__).resolve().parent.parent / 'dragomino.html'  # this copy's own build, so old and new code can be tested at once

# SECTION: HELPERS -- the page, a set table, clicks on what is drawn, the game's state
def page(b):
    ctx = b.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True)
    q = ctx.new_page(); q.goto(GAME.as_uri() + '?fast=1'); q.wait_for_function("()=>window.__dg&&__dg.ready", timeout=5000); return q

def table(q, **opts): q.evaluate("(o)=>__dg.restart(o)", opts); time.sleep(0.15)
def st(q): return q.evaluate("()=>__dg.state()")
def tap(q, bid):
    q.wait_for_function("(id)=>__dg.btn(id)", arg=bid, timeout=3000)
    p = q.evaluate("(id)=>__dg.btn(id)", bid); q.mouse.click(p[0], p[1]); time.sleep(0.15)
def waiting(q, kind, who=0):
    q.wait_for_function("([k,w])=>{const s=__dg.state();return s.wait&&s.wait.kind===k&&s.wait.who===w}", arg=[kind, who], timeout=3000)
def spot(q, matching):  # a place the tile can go, with or without a match
    s = st(q); c = [p for p in s['spots'] if (p['m'] > 0) == matching]; return 'spot-%d,%d' % (c[0]['x'], c[0]['y'])
def report(ok, name, seen): print('%-4s %-40s %s' % ('PASS' if ok else 'FAIL', name, seen))
def get_jar(q, contents, coins=0):  # place a tile that matches the land, then open the jar it earns
    table(q, bag=[[0, 0], [3, 4], [3, 4], [3, 4]], land=[[[1, 0, 0]], []], coins=[coins, 0], jarQueue=contents + [{'k': 'coins', 'n': 1}] * 4)
    tap(q, 'draft-0'); waiting(q, 'place'); tap(q, spot(q, True)); waiting(q, 'jar'); tap(q, 'jar-0')

# SECTION: FLOWS -- one per owner rule
def f_start(q):  # each player starts with one start square; 4 tiles laid out; the kid picks first
    s = st(q); lands = [len(p['land']) for p in s['players']]
    report(lands == [1, 1] and len(s['draft']) == 4 and s['wait'] == {'kind': 'pick', 'who': 0}, 'start: start squares, 4 tiles, kid picks', '%s %d %s' % (lands, len(s['draft']), s['wait']))

def f_place_touches(q):  # a new tile must touch your land; a half need not match
    table(q, bag=[[0, 1], [2, 3], [2, 3], [2, 3]])
    tap(q, 'draft-0'); waiting(q, 'place'); s = st(q)
    near = all(abs(p['x']) + abs(p['y']) <= 1 or any(abs(p['x'] + dx) + abs(p['y'] + dy) <= 1 for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]) for p in s['spots'])
    tap(q, spot(q, False)); n = len(st(q)['players'][0]['land'])
    report(near and s['spots'] and n == 3, 'place: tile touches the land', 'spots %d all touching %s, land %d' % (len(s['spots']), near, n))

def f_match_jar(q):  # matching edges earn a jar, opened at once by tapping it
    get_jar(q, [{'k': 'coins', 'n': 2}]); s = st(q)
    report(s['players'][0]['coins'] >= 2, 'match: jar opened at once gives coins', 'coins %d' % s['players'][0]['coins'])

def f_goods_at_start(q):  # each square makes 1 good of its colour at the start of the round; the start square makes none
    table(q, bag=[[3, 4]] * 4, land=[[[1, 0, 1], [2, 0, 1], [3, 0, 1], [0, 1, 2]], []]); g = st(q)['players'][0]['goods']
    report(g == [0, 3, 1, 0, 0], 'goods: 1 per square at round start', str(g))

def f_leftovers_jar(q):  # at the end of the round 3 of the same leftover good become a jar; the rest are lost
    table(q, bag=[[3, 3], [4, 4], [3, 3], [4, 4]], land=[[[1, 0, 1], [2, 0, 1], [3, 0, 1], [4, 0, 1]], []], jarQueue=[{'k': 'coins', 'n': 1}] * 8)
    for _ in range(2):
        waiting(q, 'pick'); s = st(q); tap(q, 'draft-%d' % next(i for i, t in enumerate(s['draft']) if t == [3, 3] or t == [4, 4]))
        waiting(q, 'place'); tap(q, spot(q, False))
        while st(q)['wait'] and st(q)['wait']['kind'] == 'jar' and st(q)['phase'] != 'end': tap(q, 'jar-0')
    q.wait_for_function("()=>__dg.state().phase==='end'", timeout=3000); s = st(q); p = s['players'][0]
    report(p['jars'] == 1 and p['goods'] == [0, 0, 0, 0, 0], 'end: 3 same leftovers make a jar, rest lost', 'jars %d goods %s' % (p['jars'], p['goods']))

def f_bid_tie_picker(q):  # the picker picks, the opponent may bid sets, they go on; a tie goes to the picker
    table(q, bag=[[2, 2], [0, 0], [0, 0], [0, 0]], land=[[[1, 0, 0], [2, 0, 1], [3, 0, 2]], [[1, 0, 2], [2, 0, 3], [3, 0, 4]]])
    tap(q, 'draft-0'); waiting(q, 'bid'); s = st(q); pc_bid = s['players'][1]['bid']
    tap(q, 'bid'); waiting(q, 'place'); s = st(q)
    report(pc_bid == 1 and s['players'][0]['goods'] == [0, 0, 0, 0, 0] and s['players'][1]['goods'] == [0, 0, 1, 1, 1], 'bid: tie goes to the picker, winner pays', 'pc bid %d, kid goods %s, pc goods %s' % (pc_bid, s['players'][0]['goods'], s['players'][1]['goods']))

def f_pc_most_matches(q):  # the PC picks the tile that gives it the most matches
    table(q, bag=[[0, 0], [1, 1], [3, 3], [4, 4]], land=[[], [[1, 0, 3], [2, 0, 3]]], jarQueue=[{'k': 'coins', 'n': 1}] * 8)  # set jars: a random bonus could change the land
    tap(q, 'draft-0'); waiting(q, 'place'); tap(q, spot(q, False)); waiting(q, 'pick')
    cs = sorted(c[2] for c in st(q)['players'][1]['land'])
    report(cs.count(3) == 4, 'pc: picks the tile with most matches', str(cs))

def f_slot_three(q):  # slot machine: pay 1 coin to reroll chosen wheels; 3 the same wins 3
    q.evaluate("()=>__dg.slotQueue([0,0,1,0])"); get_jar(q, [{'k': 'slot'}], coins=3); waiting(q, 'slot')
    tap(q, 'wheel-2'); tap(q, 'reroll'); q.wait_for_function("()=>!__dg.state().slot", timeout=3000); p = st(q)['players'][0]
    report(p['goods'][0] == 4 and p['coins'] == 2, 'slot: reroll costs a coin, 3 same win 3', 'goods %s coins %d' % (p['goods'], p['coins']))

def f_slot_two(q):  # 2 the same win 2; you can stop at any time
    q.evaluate("()=>__dg.slotQueue([5,1,5])"); get_jar(q, [{'k': 'slot'}], coins=0); waiting(q, 'slot')
    tap(q, 'collect'); q.wait_for_function("()=>!__dg.state().slot", timeout=3000); p = st(q)['players'][0]
    report(p['coins'] == 2, 'slot: stop with 2 the same wins 2', 'coins %d' % p['coins'])

def f_steal(q):  # steal a tile from the opponent's land and place it in yours
    table(q, bag=[[0, 0], [3, 4], [3, 4], [3, 4]], land=[[[1, 0, 0]], []], tiles1=[[1, 0, 2, 2]], jarQueue=[{'k': 'steal'}] + [{'k': 'coins', 'n': 1}] * 4)
    tap(q, 'draft-0'); waiting(q, 'place'); tap(q, spot(q, True)); waiting(q, 'jar'); tap(q, 'jar-0'); waiting(q, 'steal')
    tap(q, 'steal-t1'); waiting(q, 'place'); tap(q, spot(q, False)); s = st(q)
    mine = sorted(c[2] for c in s['players'][0]['land']); theirs = [c[2] for c in s['players'][1]['land']].count(2)  # the PC may have placed its own tile since
    report(mine.count(2) == 2 and theirs == 0, 'steal: tile moves to your land', 'mine %s, theirs %d' % (mine, theirs))

def f_first_token(q):  # the first-player token: you pick first
    table(q, bag=[[3, 4], [0, 0], [3, 4], [3, 4]], land=[[[1, 0, 0]], []], first=1, jarQueue=[{'k': 'first'}] + [{'k': 'coins', 'n': 1}] * 4)
    waiting(q, 'pick'); tap(q, 'draft-0'); waiting(q, 'place'); tap(q, spot(q, True)); waiting(q, 'jar'); tap(q, 'jar-0')
    report(st(q)['first'] == 0, 'first: token comes to you', 'first %s' % st(q)['first'])

def f_free_tile(q):  # a free extra tile from nowhere, placed at once
    get_jar(q, [{'k': 'tile'}]); waiting(q, 'place'); n0 = len(st(q)['players'][0]['land']); tap(q, spot(q, False))
    report(len(st(q)['players'][0]['land']) == n0 + 2, 'tile: free tile placed', 'land %d -> %d' % (n0, len(st(q)['players'][0]['land'])))

def f_another_jar(q):  # another jar, which you open yourself
    get_jar(q, [{'k': 'jar'}, {'k': 'coins', 'n': 3}]); waiting(q, 'jar'); c0 = st(q)['players'][0]['coins']
    tap(q, 'jar-0'); c1 = st(q)['players'][0]['coins']
    report(c1 >= c0 + 3, 'jar: another jar to open', 'coins %d -> %d' % (c0, c1))

def f_free_set(q):  # a free set: 3 different goods
    get_jar(q, [{'k': 'set'}]); g = st(q)['players'][0]['goods']; d = [g[0] - 1] + g[1:]  # the land's one square of colour 0 made 1 good
    report(sum(d) == 3 and max(d) == 1, 'set: 3 different goods', str(d))

def f_game_end(q):  # the game ends when the tiles run out; most points wins
    table(q, bag=[[3, 4]] * 4, coins=[20, 2])
    for _ in range(2):
        waiting(q, 'pick'); tap(q, 'draft-0'); waiting(q, 'place'); tap(q, spot(q, False))
    q.wait_for_function("()=>__dg.state().over", timeout=3000); s = st(q)
    report(s['winner'] == 0, 'end: tiles run out, most coins wins', 'winner %s coins %s' % (s['winner'], [p['coins'] for p in s['players']]))

# SECTION: RUN
FLOWS = {n[2:]: f for n, f in list(globals().items()) if n.startswith('f_')}
def run(names):
    with sync_playwright() as p:
        b = p.chromium.launch()
        for n in (names or FLOWS):
            try: q = page(b); FLOWS[n](q); q.context.close()
            except Exception as e: report(False, n, 'error: %s' % str(e).splitlines()[0][:120])
        b.close()
