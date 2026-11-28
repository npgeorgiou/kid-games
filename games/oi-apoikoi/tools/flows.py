# The game's tests (owner 28 Nov: only the rules he plays by): one whole-game run (f_game) played through the screen, then short tests for rules that need a set starting
# situation or many samples. One browser and one page for the whole run; each test prints PASS or FAIL, [its name], what it checks, and what was seen.
# Colours are numbered 0-5 (0 and 1 the most common); a tile is [first half, second half]; the board is 16 x 16 squares, the start tiles [0, 1] at (4, 10) turned 0 (the kid's) and (11, 5) turned 2 (the PC's: the kid's turned half a turn).
# A table tile is [x, y, turn, colour, colour, owner]: turn 0 puts the second half to the right, 1 below, 2 left, 3 above; owner 0 is the kid, 1 the PC.
# Jar contents a test needs are queued: {'k': 'empty'}, {'k': 'coins'}, {'k': 'coins2'}, {'k': 'changer'}, {'k': 'first'}, {'k': 'tile'}, {'k': 'jar'}, {'k': 'set'}.
import time, pathlib, datetime, math, re, json
from playwright.sync_api import sync_playwright
GAME = next((pathlib.Path(__file__).resolve().parent.parent).glob('*.html'))  # this copy's own built page (whatever its name then), so old and new code can be tested at once
COIN = {'k': 'coins'}
NOW = ['']  # the flow running, for the report lines
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
def run_until(q, cond, limit=4000):  # move the paused fake clock on in short steps until the game is in the state asked; a picture is drawn only when the condition looks at one
    look = "()=>{%s; return (%s)()}" % ('__dg.render()' if 'drawn' in cond or 'btn' in cond else '', cond)
    for _ in range(limit // 100):
        if q.evaluate(look): break
        q.clock.run_for(100)
    settle(q)
def st(q): return q.evaluate("()=>__dg.state()")
def jar_btn(q): return q.evaluate("()=>{__dg.render(); return __dg.buttons().find(b=>b.startsWith('jar-'))||'jar-0'}")  # the first jar he can break (one still being filled has no button)
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
def drawn(q, kind): return q.evaluate("(k)=>__dg.drawn().filter(d=>d.k===k)", kind)  # filtered in the page: the whole list is long
def report(ok, name, seen): print('%-4s [%s] %-40s %s' % ('PASS' if ok else 'FAIL', NOW[0], name, seen))
def diamond(q):  # the board's diamond as drawn: its centre and half sizes
    b = drawn(q, 'boardarea')[0]; return b['x'] + b['w'] / 2, b['y'] + b['h'] / 2, b['w'] / 2, b['h'] / 2
def get_jar(q, contents, coins=0, **more):  # place a tile with one connection: its jar; open it
    table(q, bag=[[0, 4]] * 4, coins=[coins, 0], jarQueue=contents + [COIN] * 8, **more)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); waiting(q, 'jar'); tap(q, jar_btn(q))
def kid_plays(q, until, steps=80):  # the kid takes the first tile that fits, places it where it earns most, opens his jars
    for _ in range(steps):
        s = st(q)
        if until(s): return s
        w = s['wait']
        if w and w['who'] == 0:
            if w['kind'] == 'pick': tap(q, 'draft-%d' % s['fits'].index(True))
            elif w['kind'] == 'place': drag_to(q, best_spot(q))
            elif w['kind'] == 'jar': tap(q, jar_btn(q))
        else: settle(q)
    return st(q)

# SECTION: GAME -- the whole-game run (owner 28 Nov): one game on the short test deck with set seeds for the tiles and the jars, played through the screen to its end and once more;
# only the rules he plays by are checked (owner 28 Nov: "make checks for the important things only"), each at its place, after every move
GAME_SEED = 7  # the pile this seed makes (with the jars below): he has to pass, tiles are left over at a round's end
GAME_JARS = ['tile', 'changer', 'set', 'jar', 'empty', 'coins2', 'first', 'coins', 'tile', 'coins'] * 4  # what the jars hold, in the order they are broken (both players)
def f_game(q):
    out = q.evaluate("""async ([seed, deck, kinds]) => {
      const cv = document.querySelector('#c'), errs = [], did = {}, err = m => { if (errs.length < 8) errs.push(m); };
      const tick = async () => { for (let k = 0; k < 300; k++) await null; };  // the game answers in promise steps at test speed
      const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
      const tap = async p => { if (!p) { err('nothing to tap at ' + JSON.stringify([S().wait, S().players[0].changer, __dg.buttons()])); return; } __dg.render(); ev('pointerdown', p); await tick(); ev('pointerup', p); await tick(); };  // the game answers the press before the finger lifts
      const drag = async (a, b) => { if (!a || !b) { err('nothing to drag at ' + JSON.stringify([S().wait, S().players[0].changer, !!a, !!b])); return; } __dg.render(); ev('pointerdown', a); await tick(); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
      const seen = k => __dg.drawn().filter(d => d.k === k), btn = id => { __dg.render(); return __dg.btn(id); };  // what the last picture shows (drawn once per look); buttons are where the last picture put them
      const sum = a => a.reduce((x, y) => x + y, 0), DIRS = [[1, 0], [0, 1], [-1, 0], [0, -1]], S = () => __dg.state();
      const lit = starts => { const sq = seen('square'), on = (x, y) => sq.find(d => d.x === x && d.y === y), done = new Set(), todo = starts.slice();  // the squares connections light, on the board shown
        while (todo.length) { const [x, y] = todo.shift(), a = on(x, y); if (!a || done.has(x + ',' + y)) continue; done.add(x + ',' + y); DIRS.forEach(([dx, dy]) => { const b = on(x + dx, y + dy); if (b && b.c === a.c) todo.push([x + dx, y + dy]); }); } return done.size; };
      const edgesAt = (cells) => { const sq = seen('square'), at = (x, y) => sq.find(d => d.x === x && d.y === y), mine = new Set(cells.map(([x, y]) => x + ',' + y)); let n = 0; const starts = [];  // matching edges of these squares with any land
        cells.forEach(([x, y, c]) => DIRS.forEach(([dx, dy]) => { const b = at(x + dx, y + dy); if (b && b.c === c && !(mine.has((x + dx) + ',' + (y + dy)) && dx + dy < 0)) { n++; starts.push([x, y], [x + dx, y + dy]); } })); return [n, starts]; };
      const adds = async (what, act, cells) => {  // owner 25 Nov: each connection gives a jar; it lights its connected land (both players') and each lit square gives a material; 5 of a colour make a jar at once
        __dg.render(); const s = S(), [edges, starts] = edgesAt(cells), g0 = sum(s.players[0].goods); await act(); __dg.render(); const t = S(), g = seen('good').filter(d => d.o === 0).length, five = t.players[0].jars - s.players[0].jars - edges, n = lit(starts);
        if (five < 0 || g + 5 * five !== g0 + n || t.players[0].goods.some(x => x >= 5)) err(what + ', round ' + s.round + ': ' + edges + ' connections lighting ' + n + ' squares, materials ' + g0 + ' -> ' + g + ', jars ' + (five + edges)); };
      const cellsOf = sp => { const d = DIRS[sp.r]; return [[sp.x, sp.y, sp.cs[0]], [sp.x + d[0], sp.y + d[1], sp.cs[1]]]; };
      const place = async (what) => {  // the tile in hand goes where it makes most connections: turned by taps where it lies, then dragged there
        const sp = S().spots.reduce((a, b) => b.m > a.m ? b : a); while (S().wait.r !== sp.r) await tap(__dg.held());
        await adds(what, () => drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r)), cellsOf(sp)); };
      const animals = () => seen('avatar').sort((a, b) => a.o - b.o).map(d => d.pic.split('/')[1].split('-')[0]);
      __dg.restart({ seed, fast: true, deck, jarQueue: kinds.map(k => ({ k })) }); await tick(); __dg.render();
      { const s = S(); const pets = animals();  // the start: the start tiles, 4 market tiles, he picks first and has the bee; each has a land changer
        if (s.tiles.length !== 2 || s.draft.filter(t => t).length !== 4 || s.wait.kind !== 'pick' || s.wait.who !== 0 || seen('token')[0].o !== 0 || s.players.some(p => p.changer !== -1)) err('start: ' + JSON.stringify([s.tiles.length, s.wait, s.players.map(p => p.changer)]));
        did.pets = pets; }
      let prev = S(), afterPass = 0, roundSeen = prev.round, beeAtEnd = 0, firstAtEnd = 0; const total = prev.left;
      for (let step = 0; ; step++) {
        await tick(); __dg.render(); const s = S(), w = s.wait;
        if (step > 3000) { err('stuck at ' + JSON.stringify(w)); break; }
        for (const o of [0, 1]) if (seen('coin').filter(d => d.o === o).length + seen('endcoin').filter(d => d.o === o).length !== s.players[o].coins) err('round ' + s.round + ': coins shown for ' + o + ' differ');
        for (const o of [0, 1]) for (let c = 0; c < 6; c++) if (seen('good').filter(d => d.o === o && d.c === c).length !== s.players[o].goods[c]) err('round ' + s.round + ': materials shown differ for ' + o + ' ' + JSON.stringify([s.players[o].goods, [0,1,2,3,4,5].map(c => seen('good').filter(d => d.o === o && d.c === c).length), s.players[o].jars, w]));
        if (s.tiles.length + (w && w.kind === 'place' ? 1 : 0) - 2 - s.fromNowhere + s.left !== total) err('a tile was thrown away');  // no tile is ever thrown: not when he passes, not at a round's end
        if (__dg.sounds().includes('dissolve')) err('materials were lost');  // owner 24 Nov: materials carry over from round to round
        if (s.over) {  // the end: no tile left fits either player; most coins wins, the ruby over his pile
          const [a, b] = s.players.map(p => p.coins), win = a > b ? 0 : b > a ? 1 : -1, ruby = seen('winner');
          if (s.leftFits) err('end: a tile left still fits');
          if (s.winner !== win || (win >= 0 && (ruby.length !== 1 || ruby[0].o !== win))) err('end: winner ' + s.winner + ' for coins ' + [a, b]);
          did.end = true; const again = seen('button').find(d => d.kind === 'again'); await tap(again && [again.x, again.y]); __dg.render(); const t = S();  // owner 28 Nov: the play button a stone button; owner 27 Nov: play again keeps the same two animals
          if (t.round !== 1 || t.players.some(p => p.coins) || JSON.stringify(animals()) !== JSON.stringify(did.pets)) err('play again: ' + JSON.stringify([t.round, t.players.map(p => p.coins), animals()]));
          else did.again = true; break;
        }
        if (s.round !== roundSeen) {  // owner 27 Nov: the bee shows who plays first the next round: at a round's end it is with him
          if (beeAtEnd !== firstAtEnd) err('round ' + roundSeen + ' ends with the bee at ' + beeAtEnd + ', ' + firstAtEnd + ' plays first'); else did.roundStart = true;
          roundSeen = s.round; }
        if (s.round === roundSeen && seen('token').length) { beeAtEnd = seen('token')[0].o; firstAtEnd = s.first; }
        if (s.passes[0] > prev.passes[0]) { did.pass = true; afterPass = { round: s.round, got: prev.players[1].got, passes: prev.passes[1], bee: seen('token').map(d => d.o) }; }
        if (afterPass && w && w.who === 0 && w.kind === 'pick') { const a = afterPass; afterPass = 0;  // nothing fits him: his turn passes and the PC plays again; owner 27 Nov: the bee stays
          if (a.round === s.round && s.players[1].got === a.got && s.passes[1] === a.passes) err('pass: the PC did not play again'); }
        prev = s;
        if (!w || w.who !== 0) continue;
        if (w.kind === 'pick') {
          s.fits.forEach((f, k) => { if (f || !s.draft[k]) return; const d = seen('tile').find(t => t.id === 'draft-' + k); did.greyed = true;  // a tile he can't place: greyed, not tappable
            if (!d || d.look !== 'grey' || btn('draft-' + k)) err('greyed: tile ' + k); });
          const spare = [0, 1].find(n => btn('extra-' + n));
          if (spare != null) {  // owner 28 Nov: an extra tile is placed for free on his turn, then he picks
            const got = s.players[0].got; await tap(btn('extra-' + spare)); if (S().wait.kind !== 'place') { err('extra tile not taken'); continue; }
            await place('extra tile'); did.extra = true; await tick();
            while (S().wait && S().wait.kind === 'jar') { await tap(btn(__dg.buttons().find(b => b.startsWith('jar-')))); }
            const t = S(); if (t.players[0].got !== got || !t.wait || t.wait.kind !== 'pick' || t.wait.who !== 0) err('extra tile: not free, or his turn ended'); continue; }
          if (btn('changer') && s.players[0].changer != null && !did.changer) {  // owner 28 Nov: the land changer turns through the lands on a tap; dropped on his square of another land it changes it
            const pc = s.tiles.find(t => t[5] === 1), want = s.tiles.find(t => t[5] === 0 && t[3] !== t[4]); if (!want) continue;
            for (let k = 0; k < 7 && S().players[0].changer !== want[4]; k++) await tap(btn('changer'));  // a tap turns it in its place
            await drag(btn('changer'), __dg.square(pc[0], pc[1])); await tick();  // owner 28 Nov: only his own land: on the PC's it goes back
            if (JSON.stringify(S().tiles) !== JSON.stringify(s.tiles) || S().players[0].changer !== want[4]) { err('land changer changed the PC\\'s land'); did.changer = true; continue; }
            await adds('land changer', () => drag(btn('changer'), __dg.square(want[0], want[1])), [[want[0], want[1], want[4]]]);
            if (S().tiles.find(t => t[6] === want[6])[3] !== want[4] || S().players[0].changer !== null) err('land changer: the square did not change'); did.changer = true; continue; }
          const k = s.fits.indexOf(true);
          if (!did.putBack && s.round >= 2) {  // owner 24 Nov: a picked tile can be put back; owner 27 Nov: left on its own place, he picks again
            await tap(btn('draft-' + k)); await drag(__dg.held(), [innerWidth / 2, innerHeight * 0.7]); await drag(__dg.held(), __dg.slot(k));
            const t = S(); if (!t.draft[k] || t.wait.kind !== 'pick' || t.wait.who !== 0 || t.passes[0] !== s.passes[0]) err('put back: ' + JSON.stringify(t.wait)); did.putBack = true; continue; }
          await tap(btn('draft-' + k)); if (S().wait.kind !== 'place') err('pick: not in hand');
        }
        else if (w.kind === 'place') await place('a market tile');
        else if (w.kind === 'jar') {  // owner 24-28 Nov: each prize reaches its place
          const b = __dg.buttons().find(x => x.startsWith('jar-')); if (!b) continue;
          const p0 = s.players[0];
          await tap(btn(b)); __dg.render(); const t = S(), p1 = t.players[0], pcFirst = (t.players[1].opened.first || 0) > (s.players[1].opened.first || 0);  // the PC may play on at once (test speed)
          const kind = Object.keys(p1.opened).find(k => (p1.opened[k] || 0) > (p0.opened[k] || 0));  // what the jar showed he got
          const got = { coins: p1.coins - p0.coins, jars: p1.jars - p0.jars + 1, goods: sum(p1.goods) - sum(p0.goods) + 5 * (p1.jars - p0.jars + 1 - (kind === 'jar' ? 1 : 0)) };
          const ok = { coins: got.coins === 1, coins2: got.coins === 2, empty: got.coins === 0 && got.goods === 0, jar: got.jars === 1, set: got.goods === 6, first: pcFirst || (seen('token')[0].o === 0 && t.first === 0),
            tile: p1.extras.some((e, n) => e && !p0.extras[n]), changer: p1.changer === -1 }[kind];
          if (!ok) err('jar of ' + kind + ': ' + JSON.stringify(got)); else did[kind] = true;
        }
      }
      return { errs, did, left: __dg.state().queued };
    }""", [GAME_SEED, SETTINGS['deck'], GAME_JARS])
    want = ['greyed', 'pass', 'putBack', 'extra', 'changer', 'roundStart', 'end', 'again'] + sorted(set(GAME_JARS))
    missing = [k for k in want if not out['did'].get(k)]
    report(not out['errs'] and not missing, 'whole game: every rule he plays by holds, every situation happens', 'not happened %s, broken %s' % (missing, out['errs']))

# SECTION: SHORT TESTS -- owner rules that need a set starting situation or many samples (each on a new set table)
def f_colour_split(q):  # owner 25 Nov (prototype): 6 colours (the 6th teal), 28 tiles: halves 10, 10, 9, 9, 9, 9; each colour has its row in his area
    table(q, deck=None); s = st(q); rows = sorted({d['c'] for d in drawn(q, 'place') if d['o'] == 0})  # the whole pile
    report(s['halves'] == [10, 10, 9, 9, 9, 9] and s['left'] == 28 and rows == list(range(6)), 'colours: 6, 28 tiles, halves 10/10/9/9/9/9', '%s, %d tiles, goods rows %s' % (s['halves'], s['left'], rows))
def f_first_round_fits(q):  # owner 24 Nov: of the first round's 4 tiles, 2 surely fit (one for each player); the other 2 are truly random
    fits, unfit_seen, places = [], 0, set()
    for seed in range(1, 41):
        table(q, seed=seed); f = st(q)['fits']; fits.append(sum(f)); unfit_seen += f.count(False); places.add(tuple(k for k, v in enumerate(f) if v))
    ok = min(fits) >= 2 and unfit_seen > 0 and len(places) > 1
    report(ok, 'first round: 2 surely fit, 2 random', 'fewest fitting %d, tiles that fit nowhere in 40 games %d, fitting tiles in %d different places' % (min(fits), unfit_seen, len(places)))

def f_own_land(q):  # a tile must have a matching edge with your own land; matching only the PC's land is not enough
    table(q, bag=[[2, 4], [0, 4], [0, 4], [0, 4]], tiles=[[9, 3, 0, 2, 2, 1]]); s = st(q)
    report(s['fits'][0] is False and q.evaluate("()=>!__dg.btn('draft-0')"), 'match: must be with your own land', 'fits %s' % s['fits'])

def f_pc_best(q):  # the PC picks and places for the most jars (2 connections)
    table(q, bag=[[0, 0], [0, 1], [0, 4], [0, 4]], first=1, jarQueue=[COIN] * 8)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] != [11, 5]]
    report(pc == [[0, 1]] and s['players'][1]['goods'] == [2, 2, 0, 0, 0, 0], 'pc: best tile, best place', 'pc tiles %s goods %s' % (pc, s['players'][1]['goods']))

def f_pc_most_jars(q):  # owner (design): the PC does what is best for this turn; owner 25 Nov rules: a move is worth the jars it makes now, its connections' and those of
    # 5 materials; here [1, 1] and [0, 3] both connect once, but [0, 3] lights 6 colour-0 squares onto his 4: 2 more jars
    table(q, bag=[[1, 1], [0, 3], [3, 3], [3, 3]], first=1, tiles=[[11, 4, 3, 0, 0, 1], [10, 4, 3, 0, 0, 1]], goods=[[0] * 6, [4, 0, 0, 0, 0, 0]], jarQueue=[COIN] * 12)
    q.wait_for_function("()=>{const s=__dg.state();return s.wait&&s.wait.who===0}", timeout=WAIT, polling=5); s = st(q)
    pc = [t[3:5] for t in s['tiles'] if t[5] == 1 and t[:2] not in ([11, 5], [11, 4], [10, 4])]; opened = sum(s['players'][1]['opened'].values())
    report(pc == [[0, 3]] and opened == 3, 'pc: the move that makes the most jars', 'pc placed %s, jars %d' % (pc, opened))

def f_break_jar_in_jar(q):  # owner 27 Nov: "you should be able to break an extra jar even at its freeze state" (a jar won from a jar, hanging where it came out)
    pause_clock(q); table(q, fast=False, bag=[[0, 4]] * 4, jarQueue=[{'k': 'jar'}] + [COIN] * 8)
    tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 3, 'y': 10, 'r': 2}); run_until(q, "()=>{const s=__dg.state();return s.wait&&s.wait.kind==='jar'}", 15000); tap(q, jar_btn(q))
    run_until(q, "()=>__dg.sounds().includes('reveal')", 3000); hanging = [d for d in drawn(q, 'jar') if d['o'] == 0 and d.get('rising')]
    tap(q, jar_btn(q)); opened = sum(st(q)['players'][0]['opened'].values()); q.clock.resume()
    report(len(hanging) == 1 and opened == 2, 'jars: a jar from a jar breaks while it hangs there', 'hanging %d, jars broken %d' % (len(hanging), opened))
def f_bee_prize_coin(q):  # owner 27 Nov: "when one already has the bee, replace bee percentage chance with coin"
    table(q, bag=[[0, 1]] * 4, jarQueue=[{'k': 'first'}, {'k': 'first'}] + [COIN] * 8); tap(q, 'draft-0'); waiting(q, 'place'); drag_to(q, {'x': 4, 'y': 11, 'r': 0})  # under his start tile: two connections, two jars
    waiting(q, 'jar'); tap(q, jar_btn(q)); holder = [d['o'] for d in drawn(q, 'token')]; c0 = st(q)['players'][0]['coins']; waiting(q, 'jar'); tap(q, jar_btn(q)); c1 = st(q)['players'][0]['coins']
    report(holder == [0] and c1 == c0 + 1, 'jars: a bee for one who has it is a coin', 'bee with %s after the first jar; coins %d then %d' % (holder, c0, c1))
def f_jar_mix(q):  # owner 25 Nov, per 100 jars: "1 coin about 45%, Empty about 10%, 2 coins about 10%, One of each material about 10%, Another jar about 8%, First player about 8%, Slot machine about 5%, Tile about 4%"; no stealing
    # owner 28 Nov: "remove the slot machine ... Give its jar percentage to the single coin"; the land changer "gets the same as the extra piece" (shares now per 104)
    table(q, bag=[[0, 4]] * 4, seed=11, changer=[None, None])  # seeded: an unseeded sample missed the 1.5% band about once in 15 runs; without a changer, so one can come
    n = 8000; m = q.evaluate("(n)=>__dg.sampleJars(n, 0)", n)
    # owner 28 Nov (later): "bee 3, extra tile 3, land changer 3, the 7 freed to the single coin"
    want = {'empty': 10, 'coins': 53, 'coins2': 10, 'tile': 3, 'changer': 3, 'first': 3, 'jar': 8, 'set': 10}
    ok = set(m) == set(want) and all(abs(100 * m[k] / n - v) < 1.5 for k, v in want.items())  # the shares are per 100 jars
    report(ok, 'jars: the owner\'s mix, no stealing', ', '.join('%s %.1f%%' % (k, 100 * m.get(k, 0) / n) for k in sorted(set(want) | set(m))))
def inside_poly(pts, x, y):
    o = False
    for k, (ax, ay) in enumerate(pts):
        bx, by = pts[(k + 1) % len(pts)]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay): o = not o
    return o
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
def f_sound_hooks(q):  # owner 28 Nov: "make sure there are sound hooks for every event, movement, action": every sound the game plays has its line in SOUNDS.md
    names = set(q.evaluate("()=>__dg.soundNames()")); doc = set(re.findall(r'^\| `([a-z]+)` \|', (GAME.parent / 'SOUNDS.md').read_text(), re.M))
    report(names == doc, 'sounds: every one has its hook in SOUNDS.md', 'missing in SOUNDS.md %s, listed but not in the game %s' % (sorted(names - doc), sorted(doc - names)))
MAIN_SEED, MAIN_JARS = 3, ['coins', 'empty', 'first', 'jar', 'tile', 'coins2', 'set']  # the main game's fixed pile (made by this seed) and the jar contents queued, in order
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

def f_glow_light(q):  # owner 28 Nov: "you have forgotten to give glow to the changer tile"; "make the changer and extra tile glow less yellow, more 'light' (as in the light the element)"
    table(q, extras=[[[0, 4], None], [None, None]], changer=[-1, None]); settle(q)
    a, b = q.evaluate("()=>[__dg.square(0,0), __dg.square(1,0)]"); hw, hh = abs(b[0] - a[0]), abs(b[1] - a[1])
    def halo(x, y):  # just outside the piece, round its lower half, against the same stone further out
        px = lambda k, t: q.evaluate("(p)=>__dg.pixel(p[0],p[1])", [x + k * hw * math.cos(t), y + hh + k * hh * math.sin(t)])[:3]
        near = [px(1.5, t) for t in (0.3, 0.8, 1.6, 2.3, 2.8)]; far = [px(3.2, t) for t in (0.3, 0.8, 1.6, 2.3, 2.8)]
        lum = lambda c: sum(c) / 3; yel = lambda c: (c[0] + c[1]) / 2 - c[2]
        return round(sum(lum(n) - lum(f) for n, f in zip(near, far)) / 5), round(sum(yel(n) - yel(f) for n, f in zip(near, far)) / 5)
    e = [d for d in drawn(q, 'extra') if d['o'] == 0][0]; c = [d for d in drawn(q, 'changer') if d['z'] == 1 and d['x'] < 640][0]
    he, hc = halo(e['x'], e['y']), halo(c['x'], c['y'])
    report(he[0] >= 20 and hc[0] >= 20 and he[1] <= 10 and hc[1] <= 10, 'glow: the extra tile and the land changer both glow, a light, not yellow', 'brighter than the stone round it, and more yellow than it: extra tile %s, land changer %s' % (he, hc))

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
