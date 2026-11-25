#!/usr/bin/env python3
# Simulation (owner 25 Nov): plays seeded games through the screen and reports, per player, the jars opened, the coins won and what the jars held.
# Run it before every rule change and give the owner the numbers: python3 tools/sim.py [games] [kid]
#   games: how many seeded games (default 30); kid: how the kid plays, "random" (any tile that fits, any place; default) or "best" (the tile and place with most connections).
# The kid's moves are taps and drags on what is drawn; the PC plays itself with its hand. Slot machines: the kid stops at once; the PC plays them its own way.
import sys, pathlib
from playwright.sync_api import sync_playwright
GAME = next((pathlib.Path(__file__).resolve().parent.parent).glob('*.html'))
PLAY = """async ([seed, kid]) => {
  const cv = document.querySelector('canvas'), tick = async () => { for (let k = 0; k < 300; k++) await null; };  // promise steps: the game answers in them at test speed
  const ev = (type, [x, y]) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, isPrimary: true, bubbles: true }));
  const tap = async p => { ev('pointerdown', p); ev('pointerup', p); await tick(); };
  const drag = async (a, b) => { ev('pointerdown', a); for (let k = 1; k <= 4; k++) ev('pointermove', [a[0] + (b[0] - a[0]) * k / 4, a[1] + (b[1] - a[1]) * k / 4]); ev('pointerup', b); await tick(); };
  let rs = seed * 7919; const rand = n => { rs = (rs * 16807) % 2147483647; return rs % n; };
  __dg.restart({ seed, fast: true }); await tick();
  for (let step = 0; step < 5000; step++) {
    await tick(); const s = __dg.state(), w = s.wait;
    if (s.over) break;
    if (!w || w.who !== 0) continue;
    __dg.render(); const btn = id => __dg.btn(id);
    if (w.kind === 'pick') {
      const ok = s.fits.map((f, i) => f ? i : -1).filter(i => i >= 0);
      await tap(btn('draft-' + (kid === 'best' ? ok[0] : ok[rand(ok.length)])));  // "best" takes the first that fits and places it where it connects most
    } else if (w.kind === 'place') {
      const sp = kid === 'best' ? s.spots.reduce((a, b) => b.m > a.m ? b : a) : s.spots[rand(s.spots.length)];
      while (__dg.state().wait.r !== sp.r) { await tap(__dg.held()); __dg.render(); }
      await drag(__dg.held(), __dg.tileAt(sp.x, sp.y, sp.r));
    }
    else if (w.kind === 'jar') await tap(btn('jar-0'));
    else if (w.kind === 'slot') await tap(btn('tray'));
  }
  __dg.render(); const s = __dg.state(), d = __dg.drawn();
  return { seed, over: s.over, players: s.players.map(p => ({ jars: Object.values(p.opened).reduce((a, b) => a + b, 0), coins: p.coins, opened: p.opened })),
    shown: [0, 1].map(o => d.filter(x => x.k === 'endcoin' && x.o === o).length) };
}"""
def play(q, seeds, kid='random'):  # q: a page with the game open at test speed; one result per seed
    return [q.evaluate(PLAY, [seed, kid]) for seed in seeds]
def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30; kid = sys.argv[2] if len(sys.argv) > 2 else 'random'
    with sync_playwright() as p:
        b = p.chromium.launch(); q = b.new_page(viewport={'width': 1280, 'height': 800}); q.clock.install(); q.goto(GAME.as_uri() + '?fast=1'); q.wait_for_function("()=>window.__dg&&__dg.ready")
        games = play(q, range(1, n + 1), kid); b.close()
    ended = sum(g['over'] for g in games)
    print('%d games (%d ended), the kid playing %s' % (n, ended, kid))
    for i, who in enumerate(('kid', 'PC')):
        ps = [g['players'][i] for g in games]; jars = sum(p['jars'] for p in ps); kinds = sorted({k for p in ps for k in p['opened']})
        print('%-4s jars %.1f a game, coins %.1f a game; jars held: %s' % (who, jars / n, sum(p['coins'] for p in ps) / n, ', '.join('%s %.1f%%' % (k, 100 * sum(p['opened'].get(k, 0) for p in ps) / max(1, jars)) for k in kinds)))
    print('both: jars %.1f a game' % (sum(p['jars'] for g in games for p in g['players']) / n))
if __name__ == '__main__': main()
