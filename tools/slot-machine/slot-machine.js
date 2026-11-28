// A slot machine for any game (taken out of Οι Άποικοι, 28 Nov 2026, where it was a jar's prize from 25 to 28 Nov).
// The model, in four parts:
// 1. Each wheel carries the same faces in its own shuffled order; a spin gives each spun wheel a random face.
// 2. The player keeps wheels (a clamp on each) and pays `cost` for each spin of the others; he stops whenever he likes by taking the tray.
// 3. A face set wins only by the game's `wins(faces)` rule; the prize is the game's `prize(faces)`, in the game's own unit.
// 4. A wheel is a reel (the standard slot-machine model): a strip of the faces in order, moving fast and easing out (cubic) to rest on its new face,
//    ticking as each face passes; the first wheel to stop rolls shortest.
// The game gives: faces, wins, prize, worth (a face's value, for the computer player's plan), a random source, drawFace(ctx, face, x, y, r),
// a sound(name, tickTimes) hook ('roll', 'spin', 'stop', 'clamp', 'win') and a pause(ms) that runs on its own clock.
// Use: const m = SlotMachine.create(opts); await m.roll([0, 1, 2]); m.toggleKeep(k); await m.pull(); m.plan(budget); m.draw(ctx, x, y, scale, live).
(function (root) {
  const easeOut = u => 1 - Math.pow(1 - u, 3);
  const ROLL_MS = [1800, 2600, 3500], LAPS = [4, 6, 8];  // by a wheel's place among the wheels rolling now

  function create(o) {
    const wheels = o.wheels || 3, faces = o.faces, N = faces.length, rnd = o.random || Math.random, cost = o.cost ?? 1, sound = o.sound || (() => {});
    const pause = o.pause || (ms => new Promise(r => setTimeout(r, ms))), now = o.now || (() => performance.now()), fast = !!o.fast;
    const strips = o.strips || Array.from({ length: wheels }, () => { const w = faces.slice(); for (let k = w.length - 1; k > 0; k--) { const j = Math.floor(rnd() * (k + 1)); [w[k], w[j]] = [w[j], w[k]]; } return w; });
    const spin = o.spin || (() => Math.floor(rnd() * N));  // the face index a spun wheel lands on (a game's tests queue these)
    const m = { at: Array(wheels).fill(0), kept: Array(wheels).fill(false), reel: Array.from({ length: wheels }, () => ({ t0: 0, ms: 0, from: 0, to: 0 })), strips, memo: new Map() };
    const shown = (w = m.at) => w.map((s, k) => strips[k][s]);
    const won = f => o.wins(f), value = w => { const f = shown(w); return won(f) ? o.prize(f) : 0; };
    m.shown = () => shown();
    m.won = () => won(shown());
    m.prize = () => value(m.at);
    m.rolling = () => m.reel.some(r => now() < r.t0 + r.ms);
    m.reelAt = (k, t = now()) => { const r = m.reel[k], u = r.ms > 0 ? Math.min(1, Math.max(0, (t - r.t0) / r.ms)) : 1; return r.from + (r.to - r.from) * easeOut(u); };
    m.toggleKeep = k => { m.kept[k] = !m.kept[k]; sound('clamp'); };
    m.roll = async list => {  // the listed wheels get their new faces, roll, and stop one by one
      const t0 = now();
      list.forEach((k, n) => {
        const s = spin(), from = m.reel[k].to, base = Math.floor(from), to = base + ((s - base) % N + N) % N + N * LAPS[Math.min(n, LAPS.length - 1)], ms = fast ? 0 : ROLL_MS[Math.min(n, ROLL_MS.length - 1)];
        m.at[k] = s; m.reel[k] = { t0, ms, from, to };
        const ticks = []; for (let f = Math.floor(from) + 1; f <= to; f++) ticks.push(ms / 1000 * (1 - Math.cbrt(1 - (f - from) / (to - from))));  // when face f passes
        sound('roll', ticks);
      });
      sound('spin'); let t = 0;
      for (let n = 0; n < list.length; n++) { const ms = fast ? 0 : ROLL_MS[Math.min(n, ROLL_MS.length - 1)]; await pause(ms - t); t = ms; sound('stop'); }
    };
    m.pull = () => m.roll(m.kept.map((k, i) => k ? -1 : i).filter(i => i >= 0));  // pays nothing itself: the game takes `cost` from the player
    m.canPull = budget => budget >= cost && m.kept.includes(false) && !m.rolling();
    m.plan = budget => {  // the best expected choice: null to stop, or the wheels to spin (expected prize minus costs, worked out once per machine)
      const V = (w, c) => {
        const key = w.join() + '|' + c; if (m.memo.has(key)) return m.memo.get(key).v;
        let best = { v: value(w), sel: null };
        if (c >= cost && !won(shown(w))) for (let mask = 1; mask < 1 << wheels; mask++) {
          const idx = [...Array(wheels).keys()].filter(j => mask >> j & 1); let e = 0, n = 0;
          const all = (k, ww) => { if (k === idx.length) { e += V(ww, c - cost); n++; return; } for (let s = 0; s < N; s++) { const w2 = ww.slice(); w2[idx[k]] = s; all(k + 1, w2); } };
          all(0, w); const v = e / n - cost * (o.costWorth ?? 1); if (v > best.v + 1e-9) best = { v, sel: idx };
        }
        m.memo.set(key, best); return best.v;
      };
      const c = Math.min(budget, (o.planDepth ?? 4) * cost); V(m.at, c); return m.memo.get(m.at.join() + '|' + c).sel;
    };
    m.draw = (cx, x, y, u = 1, live = false, budget = 0) => {  // the machine centred at (x, y), u times its made size; gives the tap areas: wheel k, the lever, the tray
      const ww = 130, fh = 120, gap = 40, t = now(), mw = 540, mx = x - mw / 2, wy = y - 130, areas = [];
      const rr = (X, Y, w, h, r, fill, line, lw) => { cx.beginPath(); cx.roundRect(X, Y, w, h, r); if (fill) { cx.fillStyle = fill; cx.fill(); } if (line) { cx.strokeStyle = line; cx.lineWidth = lw || 2; cx.stroke(); } };
      const dot = (X, Y, r, c) => { cx.beginPath(); cx.arc(X, Y, r, 0, 7); cx.fillStyle = c; cx.fill(); };
      const area = (id, X, Y, w, h) => areas.push({ id, x: x + (X - x) * u, y: y + (Y - y) * u, w: w * u, h: h * u });
      cx.save(); cx.translate(x, y); cx.scale(u, u); cx.translate(-x, -y);
      rr(mx, y - 230, mw, 440, 30, o.body || '#7a2f2f', o.border || '#3a1010', 6);
      const W = wheels * ww + (wheels - 1) * gap;
      for (let k = 0; k < wheels; k++) {  // each wheel a many-sided drum seen from the front: a face shows where the drum turns it toward you, squashed as it turns away
        const wx = x - W / 2 + k * (ww + gap), at = m.reelAt(k, t), base = Math.floor(at), frac = at - base, R = fh / (2 * Math.SQRT1_2), cy = wy + fh / 2;
        const g = cx.createLinearGradient(0, wy, 0, wy + fh); g.addColorStop(0, '#8d8478'); g.addColorStop(0.3, '#fffaf0'); g.addColorStop(0.7, '#fffaf0'); g.addColorStop(1, '#8d8478');
        rr(wx, wy, ww, fh, 14, g, '#3a2414', 3); cx.save(); cx.beginPath(); cx.roundRect(wx, wy, ww, fh, 14); cx.clip();
        for (let j = -1; j <= 1; j++) {
          const phi = (frac - j) * Math.PI / 2, top = cy + R * Math.sin(phi - Math.PI / 4), bot = cy + R * Math.sin(phi + Math.PI / 4), h = bot - top;
          if (Math.cos(phi) < 0.02 || h < 2) continue;
          cx.save(); cx.translate(wx + ww / 2, (top + bot) / 2); cx.scale(1, h / fh); o.drawFace(cx, strips[k][((base + j) % N + N) % N], 0, 0, fh * 0.4); cx.restore();
        }
        const sh = cx.createLinearGradient(0, wy, 0, wy + fh); sh.addColorStop(0, 'rgba(40,25,10,0.45)'); sh.addColorStop(0.28, 'rgba(40,25,10,0)'); sh.addColorStop(0.72, 'rgba(40,25,10,0)'); sh.addColorStop(1, 'rgba(40,25,10,0.45)');
        cx.fillStyle = sh; cx.fillRect(wx, wy, ww, fh); cx.restore();
        if (m.kept[k]) { rr(wx - 10, wy - 18, ww + 20, 20, 8, '#9aa3ad', '#3c434a', 3); rr(wx - 10, wy - 6, 16, fh * 0.6, 6, '#9aa3ad', '#3c434a', 3); rr(wx + ww - 6, wy - 6, 16, fh * 0.6, 6, '#9aa3ad', '#3c434a', 3); }  // a clamp
        if (live) area('wheel-' + k, wx - 10, wy - 20, ww + 20, fh + 30);
      }
      const rolling = m.rolling(), can = live && m.canPull(budget), lx = mx + mw + 12, ly = wy - 20, ky = rolling ? y + 120 : ly + 30;  // the lever, pulled down while the wheels roll
      cx.globalAlpha = can || rolling ? 1 : 0.45; rr(lx, y - 10, 30, 70, 10, '#5a2020', '#3a1010', 3);
      cx.strokeStyle = '#3c434a'; cx.lineWidth = 12; cx.lineCap = 'round'; cx.beginPath(); cx.moveTo(lx + 15, y + 20); cx.lineTo(lx + 45, ky); cx.stroke(); cx.lineCap = 'butt';
      dot(lx + 45, ky, 24, '#d42a2a'); dot(lx + 38, ky - 7, 7, '#ff9a9a'); cx.globalAlpha = 1;
      if (can) area('lever', lx - 10, ly, 90, 220);
      const ty = wy + fh + 30, f = shown();  // the tray holds the prize once the faces have stopped on a win
      rr(mx + 40, ty, mw - 80, 130, 22, '#ffe9a8', '#e0a020', 4); rr(mx + 56, ty + 12, mw - 112, 106, 16, '#f5d77a', null);
      if (won(f) && !rolling) f.forEach((x0, k) => o.drawFace(cx, x0, x + (k - (wheels - 1) / 2) * 150, ty + 65, 30));
      if (live) area('tray', mx + 40, ty, mw - 80, 130);
      cx.restore(); return areas;
    };
    return m;
  }
  root.SlotMachine = { create };
})(typeof window !== 'undefined' ? window : globalThis);
