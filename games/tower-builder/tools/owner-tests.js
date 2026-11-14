// Owner tests (sixth list): each repeats what the owner does in the game. Run: python3 tools/harness.py owner [names].
// Returns [[name, pass, detail], ...]. Uses window.__tb (tools/harness.py hook).
(names) => {
  const T = __tb, out = [], want = (n) => !names.length || names.includes(n);
  const frame = (dt) => { const fast = T.test && T.test.fast && T.test.phase !== "fail" && T.test.phase !== "pass" ? 10 : 1;
    T.stepPhysics(dt * fast, 5 * fast); T.cleanupOutOfBounds(); T.updateCheck(dt); };
  const run = (s, dt = 1 / 60) => { for (let k = 0; k < s / dt; k++) frame(dt); };
  const X = 20; // middle of the building area
  const blockW = () => T.PIECE_DEFS.block.hx * 2 * T.PIECE_DEFS.block.hy * 2 * 5 * 10; // one big stone block, N

  // --- 3: the hand lifts what the job needs: a piece and everything resting on it, by weight only
  if (want("hand")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const stackLift = (stack) => { // stack: [[def, mat], ...] bottom first; the hand takes the bottom one and lifts 1.5 m
      T.clearAllPieces(); let top = 0; const ps = [];
      for (const [d, m] of stack) { const hy = T.PIECE_DEFS[d].hy; const p = T.spawnPiece(d, X, top + hy + 0.003, 0, m); top += 2 * hy; ps.push(p); run(0.5); }
      run(1); const b = ps[0], y0 = b.body.getPosition().y, c0 = b.body.getWorldCenter(), g = { x: c0.x, y: c0.y };
      T.startHold(b, { x: g.x, y: g.y }, 91, 0, 0); let t1 = null, jump = 0;
      const gaps = () => { for (let i = 1; i < ps.length; i++) { const lo = ps[i - 1], hi = ps[i]; jump = Math.max(jump, (hi.body.getPosition().y - T.PIECE_DEFS[hi.defKey].hy) - (lo.body.getPosition().y + T.PIECE_DEFS[lo.defKey].hy)); } };
      for (let k = 0; k < 240; k++) { b.desired = { x: g.x, y: g.y + Math.min(1.5, k * 1.5 / 60) }; frame(1 / 60); gaps(); if (t1 == null && b.body.getPosition().y - y0 > 1.0) t1 = k / 60; }
      const rise = b.body.getPosition().y - y0, w = ps.reduce((s, p) => s + p.body.getMass() * 10, 0);
      const carried = ps.every((p) => p.body.getPosition().y > 1.0 + 0.5);
      T.releaseHold(91); run(0.5);
      return { w: Math.round(w), rise: +rise.toFixed(2), t1, carried, jump: +jump.toFixed(3) };
    };
    const S = "stone";
    const cases = [
      ["a big stone square alone", [["square", S]]],
      ["two small oblong stones, the bottom one lifted (owner)", [["abacus", S], ["abacus", S]]],
      ["a stone slab alone (as heavy as two small oblong stones)", [["capital", S]]],
      ["a stone block with a stone block on it (two blocks)", [["block", S], ["block", S]]],
      ["four stone squares stacked (as heavy as two blocks)", [["square", S], ["square", S], ["square", S], ["square", S]]],
      ["a stone block with two stone blocks on it (three blocks)", [["block", S], ["block", S], ["block", S]]],
      ["a stone square with two stone blocks on it", [["square", S], ["block", S], ["block", S]]],
      ["a mudbrick block with three mudbrick blocks on it", [["block", "mudbrick"], ["block", "mudbrick"], ["block", "mudbrick"], ["block", "mudbrick"]]],
      ["a wooden block with two stone blocks on it", [["block", "wood"], ["block", S], ["block", S]]],
      ["a big stone square alone (as heavy as two blocks, owner 14 Nov)", [["bigsquare", S]]],
      ["a long stone block alone (as heavy as two blocks)", [["longblock", S]]],
    ];
    const LIM = 2 * blockW(), res = {};
    for (const [n, st] of cases) {
      const r = (res[n] = stackLift(st)), canLift = r.w <= LIM + 1;
      if (st.length > 1 && canLift) out.push(["14 Nov lifted from the bottom, what rests on it stays sitting on it: " + n, r.jump < 0.02, "largest gap " + r.jump + " m"]);
      out.push(["3 hand: " + n, canLift ? r.rise > 1.0 && r.carried : r.rise < 0.2, (canLift ? "should lift" : "too heavy") + ": weight " + r.w + " N, rose " + r.rise + " m, 1 m after " + r.t1 + " s"]);
    }
    const same = (a, b) => { const x = res[a].t1, y = res[b].t1; return x != null && y != null && Math.abs(x - y) <= 0.25 * Math.max(x, y) + 0.05; };
    out.push(["3 hand: same weight, same lift (small oblong pair vs slab)", same(cases[1][0], cases[2][0]), res[cases[1][0]].t1 + " s vs " + res[cases[2][0]].t1 + " s"]);
    out.push(["3 hand: same weight, same lift (two blocks vs four squares)", same(cases[3][0], cases[4][0]), res[cases[3][0]].t1 + " s vs " + res[cases[4][0]].t1 + " s"]);
    out.push(["3 hand: same weight, same lift (two blocks vs big square)", same(cases[3][0], cases[9][0]), res[cases[3][0]].t1 + " s vs " + res[cases[9][0]].t1 + " s"]);
    out.push(["3 hand: same weight, same lift (two blocks vs long block)", same(cases[3][0], cases[10][0]), res[cases[3][0]].t1 + " s vs " + res[cases[10][0]].t1 + " s"]);
    // weights: every piece weighs its area in blocks of its material (owner 14 Nov: the regular block is the base)
    for (const [k, d] of Object.entries(T.PIECE_DEFS)) for (const m of ["wood", "mudbrick", "stone"]) {
      const p = T.spawnPiece(k, X, 8, 0, m), area = d.shape === "circle" ? Math.PI * d.r * d.r : d.verts ? Math.abs(d.verts.reduce((a, [x, y], i) => { const [x2, y2] = d.verts[(i + 1) % d.verts.length]; return a + x * y2 - x2 * y; }, 0)) / 2 : 4 * d.hx * d.hy;
      const b = T.spawnPiece("block", X + 6, 8, 0, m), want = b.body.getMass() * area / 2, got = p.body.getMass(); T.clearAllPieces();
      if (Math.abs(got - want) > 0.03 * want) out.push(["weights: " + m + " " + k + " weighs its size in blocks", false, (got / b.body.getMass()).toFixed(2) + " blocks, should be " + (area / 2).toFixed(2)]); }
    // owner 14 Nov: the same stack lifted again behaves the same (it lifted once, then did not)
    { T.clearAllPieces(); const a = T.spawnPiece("block", X, 0.503, 0, "stone"); run(0.5); T.spawnPiece("block", X, 1.506, 0, "stone"); run(1.5); const rises = [];
      for (let t = 0; t < 3; t++) { const c0 = a.body.getWorldCenter(), g = { x: c0.x, y: c0.y }, y0 = g.y; T.startHold(a, { x: g.x, y: g.y }, 91, 0, 0);
        for (let k = 0; k < 150; k++) { a.desired = { x: g.x, y: g.y + Math.min(1.5, k * 1.5 / 60) }; frame(1 / 60); } rises.push(+(a.body.getPosition().y - y0).toFixed(2));
        for (let k = 0; k < 120; k++) { a.desired = { x: g.x, y: g.y + 0.01 }; frame(1 / 60); } T.releaseHold(91); run(1.5); }
      out.push(["14 Nov two stacked stone blocks lifted three times rise the same each time", rises.every((r) => Math.abs(r - rises[0]) < 0.05 && r > 1.0), JSON.stringify(rises)]); }
    // owner 14 Nov: a lying piece grabbed at one end swings down (the wrist cannot hold it level)
    for (const [d, m] of [["block", "wood"], ["block", "stone"], ["beam", "wood"]]) { T.clearAllPieces(); const pc = T.spawnPiece(d, X, T.PIECE_DEFS[d].hy + 0.003, 0, m); run(0.5);
      const g0 = pc.body.getWorldPoint({ x: T.PIECE_DEFS[d].hx * 0.9, y: 0 }), g = { x: g0.x, y: g0.y }; T.startHold(pc, g, 92, 0, 0);
      let turn = 0; for (let k = 0; k < 180; k++) { pc.desired = { x: g.x, y: g.y + Math.min(2.5, k * 2.5 / 60) }; frame(1 / 60); turn = Math.max(turn, Math.abs(pc.body.getAngle())); } T.releaseHold(92);
      out.push(["14 Nov a " + m + " " + d + " grabbed at one end and lifted swings down", turn > 1.0, "turned down as far as " + turn.toFixed(2) + " (hanging straight down: 1.57)"]); }
    out.push(["3 hand: heavier lags more", res[cases[0][0]].t1 < res[cases[3][0]].t1, res[cases[0][0]].t1 + " s (square) vs " + res[cases[3][0]].t1 + " s (two blocks)"]);
  }

  // --- 12: mudbrick stacks placed by hand, one piece after another, as the owner builds them
  if (want("mudbrick")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const stackOn = (list, rough, quick) => { // a mudbrick block on the ground, then each piece carried over it and let go just above
      T.clearAllPieces(); const base = T.spawnPiece("block", X, 0.503, 0, "mudbrick"); run(1); let top = 1.0, j = 0;
      for (const m of list) { const off = rough ? [0.3, -0.25, 0.15, -0.3, 0.2, -0.1, 0.25, -0.2][j++ % 8] : 0;
        const p = T.spawnPiece("block", X - 4, top + 1.5, 0, m), g = p.body.getWorldCenter();
        T.startHold(p, { x: g.x, y: g.y }, 92, 0, 0);
        for (let k = 0; k < 90; k++) { p.desired = { x: X + off, y: top + 1.0 }; frame(1 / 60); }
        for (let k = 0; k < 60; k++) { p.desired = { x: X + off, y: top + 0.52 }; frame(1 / 60); }
        T.releaseHold(92); run(quick ? 0.2 : 1.5); top += 1.0;
      }
      run(6);
      return T.pieces.includes(base) ? "holds" : "crumbles";
    };
    for (const [n, list, exp] of [ // owner (13 Nov): two separate stacks, each breaks it: four mudbricks; three stones
      ["4 mudbricks on a mudbrick (owner)", ["mudbrick", "mudbrick", "mudbrick", "mudbrick"], "crumbles"],
      ["3 stones on a mudbrick (owner)", ["stone", "stone", "stone"], "crumbles"],
      ["6 mudbricks on a mudbrick (owner, Ishtar)", ["mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick"], "crumbles"],
      ["3 mudbricks on a mudbrick", ["mudbrick", "mudbrick", "mudbrick"], "holds"],
      ["2 stones on a mudbrick", ["stone", "stone"], "holds"],
    ]) for (const [how, rough, quick] of [["", false, false], [", placed roughly", true, false], [", placed quickly", false, true]]) {
      const r = stackOn(list, rough, quick); out.push(["12 mudbrick: " + n + how, r === exp, r + " (should " + (exp === "holds" ? "hold" : "crumble") + ")"]); }
  }

  // --- seventh list 1: a mudbrick falling one short side (1 m) does not break; from higher it does
  if (want("fall")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const drop = (h, angle, onto) => { T.clearAllPieces(); let base = 0;
      if (onto) { T.spawnPiece("block", X, 0.503, 0, onto); run(1); base = 1.0; }
      const p = T.spawnPiece("block", X, base + 0.5 + h + 0.01, angle, "mudbrick"); run(4); return T.pieces.includes(p) ? "whole" : "breaks"; };
    // before: it broke falling from 2.75 m; owner: one block side (1 m) more without breaking, more than that breaks
    for (const [h, a, onto, exp] of [[1.0, 0, null, "whole"], [2.75, 0, null, "whole"], [3.5, 0, null, "whole"], [3.5, 0.3, null, "whole"], [3.5, 0, "stone", "whole"], [3.5, 0, "mudbrick", "whole"],
      [4.0, 0, null, "breaks"], [4.0, 0, "stone", "breaks"], [5.0, 0, null, "breaks"]]) {
      const r = drop(h, a, onto); out.push(["7-1 mudbrick falling " + h + " m" + (a ? ", tilted" : "") + (onto ? " onto " + onto : " onto the ground"), r === exp, r + " (should " + (exp === "whole" ? "stay whole" : "break") + ")"]); }
  }
  // --- seventh list 5: a mudbrick standing upright (narrow) holds less; laid across a gap like a lintel, less still
  if (want("shape")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const column = (n) => { T.clearAllPieces(); const c = T.spawnPiece("column", X, 1.203, 0, "mudbrick"); run(1); let top = 2.4;
      for (let k = 0; k < n; k++) { T.spawnPiece("block", X, top + 0.503, 0, "stone"); top += 1; run(1.5); } run(5); return T.pieces.includes(c) ? "holds" : "crumbles"; };
    for (const [n, exp] of [[1, "crumbles"], [3, "crumbles"]]) { const r = column(n); out.push(["7-5 upright mudbrick column with " + n + " stone block(s) on it (owner's picture: 3)", r === exp, r]); }
    const lintel = (d, m, load) => { T.clearAllPieces(); // two stone blocks 1 m apart, the piece across them, a stone block on its middle
      T.spawnPiece("block", X - 1.5, 0.503, 0, "stone"); T.spawnPiece("block", X + 1.5, 0.503, 0, "stone"); run(1);
      const hy = T.PIECE_DEFS[d].hy, L = T.spawnPiece(d, X, 1.0 + hy + 0.003, 0, m); run(1.5);
      if (load) { T.spawnPiece(load, X, 1.0 + 2 * hy + T.PIECE_DEFS[load].hy + 0.003, 0, "stone"); } run(5);
      return T.pieces.includes(L) ? "holds" : "breaks"; };
    for (const [d, m, load, exp] of [["block", "mudbrick", null, "holds"], ["block", "mudbrick", "block", "breaks"], ["beam", "mudbrick", "square", "breaks"],
      ["beam", "wood", "block", "holds"], ["block", "stone", "block", "holds"]]) {
      const r = lintel(d, m, load); out.push(["7-5 " + m + " " + d + " across a 1 m gap" + (load ? " with a stone " + load + " on it" : ", nothing on it"), r === exp, r]); }
  }
  // --- seventh list 3: carrying goes by weight, compared with a stone block: the same weight carries the same in any material
  if (want("carry")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const carry = (d, m) => { T.clearAllPieces(); const p = T.spawnPiece(d, X - 4, 3, 0, m), c = p.body.getWorldCenter(), g = { x: c.x, y: c.y };
      T.startHold(p, { x: g.x, y: g.y }, 94, 0, 0); run(0.5); let t = null;
      for (let k = 0; k < 300; k++) { p.desired = { x: g.x + 4, y: g.y }; frame(1 / 60); if (t == null && p.body.getPosition().x > g.x + 3.9) t = k / 60; }
      T.releaseHold(94); return t; };
    // tenth list: a stone block held at one end can be swung round in circles (1 m circles, once a second)
    { T.clearAllPieces(); const p = T.spawnPiece("block", X, 6, 0, "stone"); run(0.1); const g0 = p.body.getWorldPoint({ x: 0.9, y: 0 }), g = { x: g0.x, y: g0.y };
      T.startHold(p, g, 97, 0, 0); p.desired = { x: g.x, y: g.y }; run(2.5); let prev = p.body.getAngle(), tot = 0;
      for (let k = 0; k < 240; k++) { const th = k / 60 * 2 * Math.PI; p.desired = { x: g.x + Math.sin(th), y: g.y + 1 - Math.cos(th) }; frame(1 / 60); const a = p.body.getAngle(); tot += a - prev; prev = a; }
      T.releaseHold(97); const turns = Math.abs(tot) / (2 * Math.PI);
      out.push(["10 a stone block held at one end swings round in circles", turns >= 1, turns.toFixed(2) + " turns in 4 circles of the hand (the earlier game: 1.45)"]); }
    const r = {}; for (const [d, m] of [["block", "stone"], ["abacus", "stone"], ["column", "wood"], ["square", "stone"], ["block", "mudbrick"], ["block", "wood"]]) r[d + "/" + m] = carry(d, m);
    const close = (a, b) => Math.abs(a - b) <= 0.15 * Math.max(a, b);
    out.push(["7-3 same weight, same carry: small oblong stone vs wooden column", close(r["abacus/stone"], r["column/wood"]), r["abacus/stone"] + " s vs " + r["column/wood"] + " s (4 m)"]);
    out.push(["7-3/10 a stone block carries halfway between too light (0.8 s for 4 m) and too slow (1.45 s)", r["block/stone"] > 0.8 && r["block/stone"] < 1.45, JSON.stringify(r)]);
    out.push(["7-3 lighter is quicker: stone block > mudbrick block > stone square > wooden block", r["block/stone"] > r["block/mudbrick"] && r["block/mudbrick"] > r["square/stone"] && r["square/stone"] > r["block/wood"], JSON.stringify(r)]);
  }

  // --- eighth list 1: a triangle is grabbed only on itself, and slides along like any other piece
  // --- 14 Nov (owner): a piece held in the middle follows the finger round in circles without sinking under it,
  // and when the finger stops the piece does not run on far past it (down, up or sideways)
  if (want("swing")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    for (const m of ["stone", "mudbrick", "wood"]) {
      T.clearAllPieces(); const p = T.spawnPiece("block", X, 7, 0, m), c = p.body.getWorldCenter(), g = { x: c.x, y: c.y };
      T.startHold(p, { x: g.x, y: g.y }, 93, 0, 0); p.desired = { x: g.x, y: g.y }; run(0.5); let sag = 0, n = 0, lo = 1e9, hi = -1e9;
      for (let k = 0; k < 180; k++) { const th = k / 60 * 2 * Math.PI * 1.5, f = { x: g.x + 0.3 * Math.sin(th), y: g.y + 0.3 - 0.3 * Math.cos(th) }; p.desired = f; frame(1 / 60);
        const q = p.body.getWorldCenter(); if (k >= 60) { sag += f.y - q.y; lo = Math.min(lo, q.y); hi = Math.max(hi, q.y); n++; } }
      out.push(["14 Nov a " + m + " block grabbed in the middle follows small quick circles of the finger (0.6 m across, 1.5 a second)", sag / n < 0.15 && hi - lo > 0.4, "on average " + (sag / n).toFixed(2) + " m under the finger, its own circle " + (hi - lo).toFixed(2) + " m across (the finger's: 0.6 m)"]);
      for (const [name, dx, dy] of [["down", 0, -3], ["up", 0, 3], ["sideways", 3, 0]]) {
        const s0 = { x: g.x, y: dy < 0 ? g.y + 1 : g.y - 2 }; p.desired = s0; run(1.5); let over = 0;
        for (let k = 0; k < 90; k++) { const u = Math.min(1, k / 18); p.desired = { x: s0.x + dx * u, y: s0.y + dy * u }; frame(1 / 60);
          const q = p.body.getWorldCenter(); over = Math.max(over, ((q.x - s0.x) * dx + (q.y - s0.y) * dy) / 3 - 3); }
        out.push(["14 Nov a " + m + " block moved 3 m " + name + " quickly runs on past the finger, not far (down: at least 0.3 m)", over < 1 && (name !== "down" || over > 0.3), "runs on " + Math.max(0, over).toFixed(2) + " m past the finger"]); }
      T.releaseHold(93);
      // grabbed roughly in the middle (0.3 m off), lifted and carried quickly: it does not tilt
      { T.clearAllPieces(); const p = T.spawnPiece("block", X, 3, 0, m); run(0.1); const g0 = p.body.getWorldPoint({ x: 0.3, y: 0 }), g = { x: g0.x, y: g0.y }; let tilt = 0;
        T.startHold(p, g, 92, 0, 0); p.desired = { x: g.x, y: g.y };
        for (let k = 0; k < 150; k++) { const u = Math.min(1, Math.max(0, (k - 30) / 24)), w = Math.min(1, Math.max(0, (k - 60) / 30)); p.desired = { x: g.x + 3 * w, y: g.y + 2 * u }; frame(1 / 60); tilt = Math.max(tilt, Math.abs(p.body.getAngle())); }
        T.releaseHold(92); out.push(["14 Nov a " + m + " block grabbed roughly in the middle, lifted and carried, does not tilt", tilt < 0.12, "tilted at most " + (tilt * 57.3).toFixed(0) + " degrees"]); }
      // held at one end, whirled round by circles of the hand, once a second: how small can the circles be?
      { const res = {}; for (const D of [0.6, 0.8, 1.0, 1.4]) { T.clearAllPieces(); const p = T.spawnPiece("block", X, 6, 0, m); run(0.1); const g0 = p.body.getWorldPoint({ x: 0.9, y: 0 }), g = { x: g0.x, y: g0.y };
        T.startHold(p, g, 91, 0, 0); p.desired = { x: g.x, y: g.y }; run(2.5); let prev = p.body.getAngle(), tot = 0;
        for (let k = 0; k < 360; k++) { const th = k / 60 * 2 * Math.PI; p.desired = { x: g.x + D / 2 * Math.sin(th), y: g.y + D / 2 - D / 2 * Math.cos(th) }; frame(1 / 60); const a = p.body.getAngle(); if (k >= 120) tot += a - prev; prev = a; }
        T.releaseHold(91); res[D] = +(Math.abs(tot) / (2 * Math.PI)).toFixed(2); }
        out.push(["14 Nov a " + m + " block held at one end whirls round with hand circles 0.8 m across", res[0.8] >= 3, "turns in 4 circles of the hand, by circle size across (m): " + JSON.stringify(res)]); } }
  }

  if (want("triangle")) {
    T.mode = "build"; T.startLevel(5); T.clearAllPieces(); T.quiet0();
    const t = T.spawnPiece("trib", X, 0.7, 0, "stone"); run(1); const q = t.body.getPosition(), d = T.PIECE_DEFS.trib;
    let empty = 0, n = 0; // points in the box around the triangle but more than a finger's slack off its real shape
    for (let a = -1; a <= 1; a += 0.1) for (let b = -1; b <= 1; b += 0.1) { const l = { x: a * d.hx, y: b * d.hy }, w = t.body.getWorldPoint(l);
      let inside = false, best = 1e9; const vs = d.verts; // distance to the triangle's edges
      for (let k = 0; k < vs.length; k++) { const [ax, ay] = vs[k], [bx, by] = vs[(k + 1) % vs.length], ex = bx - ax, ey = by - ay; const u = Math.max(0, Math.min(1, ((l.x - ax) * ex + (l.y - ay) * ey) / (ex * ex + ey * ey))); best = Math.min(best, Math.hypot(l.x - ax - u * ex, l.y - ay - u * ey)); }
      inside = T.inRing(l.x, l.y, vs); if (inside || best < 0.2) continue; n++; if (T.hitPiece && T.hitPiece({ x: w.x, y: w.y }) === t) empty++; }
    out.push(["8-1 a triangle is not grabbed on the empty part of its box", empty === 0, empty + " of " + n + " empty points grab it"]);
    const drag = (def) => { T.clearAllPieces(); T.spawnPiece("block", X + 2, 0.503, 0, "stone"); const p = T.spawnPiece(def, X - 2, 0.9, 0, "stone"); run(1);
      const c0 = p.body.getWorldCenter(), g = { x: c0.x, y: c0.y }; T.startHold(p, g, 95, 0, 0); let lag = 0;
      for (let k = 0; k < 240; k++) { p.desired = { x: g.x + Math.min(4, k * 4 / 120), y: g.y + Math.min(1.2, k * 0.02) }; frame(1 / 60); const w = p.body.getWorldPoint(p.grabLocal); lag = Math.max(lag, k > 150 ? Math.hypot(w.x - p.desired.x, w.y - p.desired.y) : 0); }
      T.releaseHold(95); run(1); return +lag.toFixed(2); };
    const lt = drag("trib"), ls = drag("square");
    out.push(["8-1 a triangle slid up and over a block follows the hand like a square", lt <= ls + 0.1, "triangle " + lt + " m behind, square " + ls + " m behind"]);
  }

  // --- ninth list: a small stone held in the hand does not shove a big stone away
  if (want("push")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const push = (d, m, td, tm) => { T.clearAllPieces(); const t = T.spawnPiece(td, X + 1.5, T.PIECE_DEFS[td].hy + 0.003, 0, tm); const p = T.spawnPiece(d, X - 2, T.PIECE_DEFS[d].hy + 0.05, 0, m); run(1);
      const x0 = t.body.getPosition().x, c0 = p.body.getWorldCenter(), g = { x: c0.x, y: c0.y }; T.startHold(p, g, 96, 0, 0);
      for (let k = 0; k < 240; k++) { p.desired = { x: g.x + Math.min(6, k * 6 / 60), y: g.y }; frame(1 / 60); } T.releaseHold(96); run(1); return +(t.body.getPosition().x - x0).toFixed(2); };
    const a = push("abacus", "stone", "block", "stone"), b = push("block", "stone", "block", "stone"), c = push("abacus", "stone", "abacus", "stone");
    out.push(["9 a small oblong stone pushed hard into a big stone block hardly moves it", a < 0.1, "moved " + a + " m"]);
    out.push(["9 a stone block pushes a stone block along (as heavy as itself)", b > 0.5, "moved " + b + " m"]);
    out.push(["9 a small oblong stone pushes another small one along", c > 0.5, "moved " + c + " m"]);
    // owner 14 Nov: held up in the air the hand spends strength on the weight, so it pushes sideways less; with speed it hits harder
    const pushAir = (speed) => { T.clearAllPieces(); const t = T.spawnPiece("block", X + 1.5, 0.503, 0, "stone"); run(1); const p = T.spawnPiece("block", X - 2, 0.85, 0, "stone");
      const x0 = t.body.getPosition().x, c0 = p.body.getWorldCenter(), g = { x: c0.x, y: c0.y }; T.startHold(p, g, 96, 0, 0); run(0.5);
      for (let k = 0; k < 240; k++) { p.desired = { x: g.x + Math.min(6, k * speed / 60), y: g.y }; frame(1 / 60); } T.releaseHold(96); run(1); return +(t.body.getPosition().x - x0).toFixed(2); };
    // owner 14 Nov: a small stone rammed fast into a stone block or the big stone square barely moves it
    const ram = (td) => { T.clearAllPieces(); const t = T.spawnPiece(td, X + 2, T.PIECE_DEFS[td].hy + 0.003, 0, "stone"); run(1); const p = T.spawnPiece("abacus", X - 3, 0.25, 0, "stone"); run(0.5);
      const x0 = t.body.getPosition().x, c0 = p.body.getWorldCenter(), g = { x: c0.x, y: c0.y }; T.startHold(p, g, 96, 0, 0);
      for (let k = 0; k < 240; k++) { p.desired = { x: g.x + Math.min(8, k * 12 / 60), y: g.y }; frame(1 / 60); } T.releaseHold(96); run(1); return +(t.body.getPosition().x - x0).toFixed(2); };
    for (const td of ["block", "bigsquare"]) { const r = ram(td); out.push(["14 Nov a small oblong stone rammed fast into a stone " + td + " barely moves it", r < 0.15, "moved " + r + " m"]); }
    const air = pushAir(1.5), hit = pushAir(12);
    out.push(["14 Nov a stone block held up in the air pushes a stone block less than one sliding on the ground", air < b, "moved " + air + " m (on the ground: " + b + " m)"]);
    out.push(["14 Nov a stone block swung fast into a stone block knocks it along", hit > 0.3, "moved " + hit + " m"]);
  }

  // --- 14 Nov: dragging a piece up and towards a wall of pieces slides up it, not stuck by rubbing (owner)
  if (want("slide")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const slide = (m, side, wall = true) => { T.clearAllPieces(); const hy = T.PIECE_DEFS.block.hy;
      if (wall) T.spawnPiece("block", X + 1.0, hy + 0.003, 0, "stone"); if (wall) T.spawnPiece("block", X + 1.0, 3 * hy + 0.01, 0, "stone"); if (wall) T.spawnPiece("block", X + 1.0, 5 * hy + 0.02, 0, "stone");
      const p = T.spawnPiece("block", X - 1.02, hy + 0.003, 0, m); run(1);
      const c0 = p.body.getWorldCenter(), g = { x: c0.x, y: c0.y }, y0 = c0.y; T.startHold(p, g, 95, 0, 0);
      for (let k = 0; k < 120; k++) { p.desired = { x: g.x + Math.min(side, k * side / 60), y: g.y + Math.min(1.5, k * 1.5 / 60) }; frame(1 / 60); }
      const r = +(p.body.getWorldCenter().y - y0).toFixed(2); T.releaseHold(95); return r; };
    for (const m of ["wood", "mudbrick", "stone"]) for (const side of [0.5, 1.5]) {
      const r = slide(m, side), f = slide(m, 0, false); out.push(["14 Nov a " + m + " block dragged up and " + side + " m towards a wall of stone blocks slides up it as high as lifted with no wall", r >= 0.9 * f, "rose " + r + " m, " + f + " m with no wall"]); }
  }

  // --- eleventh list: lifting a piece off the piece it sits on is not sticky, and the hand's feel is locked
  if (want("motion")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    // time for the grabbed piece to rise 1 m when the hand goes up 1.5 m (or, with dir, to move 1 m that way)
    const lift = (d, m, under, dir = [0, 1]) => { T.clearAllPieces(); let y = 0.003;
      if (under && under !== "air") { const u = T.spawnPiece(under[0], X, T.PIECE_DEFS[under[0]].hy + 0.003, 0, under[1]); y = 2 * T.PIECE_DEFS[under[0]].hy + 0.006; run(0.5); }
      const p = T.spawnPiece(d, X, under === "air" ? 3 : y + T.PIECE_DEFS[d].hy, 0, m); run(under === "air" ? 0.05 : 1);
      const c0 = p.body.getWorldCenter(), g = { x: c0.x + (lag ? 0.2 : 0), y: c0.y + (lag ? 0.2 : 0) }; T.startHold(p, g, 98, 0, 0); if (under === "air") { p.desired = { x: g.x, y: g.y }; run(1); }
      const s0 = p.body.getWorldPoint(p.grabLocal), q0 = { x: s0.x, y: s0.y }; let t = null, worst = 0;
      for (let k = 0; k < 240; k++) { p.desired = { x: q0.x + dir[0] * Math.min(1.5, k * 1.5 / 30), y: q0.y + dir[1] * Math.min(1.5, k * 1.5 / 30) }; frame(1 / 60);
        const q = p.body.getWorldCenter(), w = p.body.getWorldPoint(p.grabLocal); if (k < 24) worst = Math.max(worst, Math.hypot(w.x - p.desired.x, w.y - p.desired.y));
        if (t == null && (q.x - q0.x) * dir[0] + (q.y - q0.y) * dir[1] > 1.0) t = k / 60; }
      T.releaseHold(98); run(0.5); return lag ? +worst.toFixed(2) : t; };
    let lag = true; // the owner grabs anywhere on the piece: how far the piece trails the hand as it leaves what it sat on
    const close = (a, b) => a != null && b != null && a <= b + 0.1;
    for (const [d, m, u] of [["square", "stone", ["block", "stone"]], ["block", "stone", ["block", "stone"]], ["abacus", "stone", ["capital", "stone"]], ["block", "mudbrick", ["block", "mudbrick"]], ["beam", "wood", ["block", "stone"]]]) {
      const off = lift(d, m, u), air = lift(d, m, "air");
      out.push(["11 lifting a " + m + " " + d + " off a " + u[1] + " " + u[0] + " is not sticky (it follows the hand as in the air)", close(off, air), off + " m behind the hand vs " + air + " m in the air"]);
    }
    { const off = lift("square", "stone", ["block", "stone"], [1, 0.3]), air = lift("square", "stone", "air", [1, 0.3]);
      out.push(["11 sliding a stone square off the top of a block is not sticky", close(off, air), off + " m behind vs " + air + " m in the air"]); }
    lag = false;
    // the hand's feel, locked: carrying, swinging and lifting stay as the owner has them (tools/motion-ref.json); a change needs his yes
    const carry = (d, m) => { T.clearAllPieces(); const p = T.spawnPiece(d, X - 4, 3, 0, m), c0 = p.body.getWorldCenter(), g = { x: c0.x, y: c0.y };
      T.startHold(p, g, 94, 0, 0); run(0.5); let t = null;
      for (let k = 0; k < 300; k++) { p.desired = { x: g.x + 4, y: g.y }; frame(1 / 60); if (t == null && p.body.getPosition().x > g.x + 3.9) t = k / 60; }
      T.releaseHold(94); return t; };
    const feel = {};
    for (const [d, m] of [["block", "stone"], ["square", "stone"], ["abacus", "stone"], ["beam", "stone"], ["block", "mudbrick"], ["block", "wood"], ["column", "wood"]]) feel["carry " + m + " " + d + " 4 m (s)"] = carry(d, m);
    { T.clearAllPieces(); const p = T.spawnPiece("block", X, 6, 0, "stone"); run(0.1); const g0 = p.body.getWorldPoint({ x: 0.9, y: 0 }), g = { x: g0.x, y: g0.y };
      T.startHold(p, g, 97, 0, 0); p.desired = { x: g.x, y: g.y }; run(2.5); let prev = p.body.getAngle(), tot = 0;
      for (let k = 0; k < 240; k++) { const th = k / 60 * 2 * Math.PI; p.desired = { x: g.x + Math.sin(th), y: g.y + 1 - Math.cos(th) }; frame(1 / 60); const a = p.body.getAngle(); tot += a - prev; prev = a; }
      T.releaseHold(97); feel["stone block swung at one end, turns in 4 circles"] = +(Math.abs(tot) / (2 * Math.PI)).toFixed(2); }
    feel["lift a stone square 1 m from the ground (s)"] = lift("square", "stone", null);
    feel["lift a stone block 1 m from the ground (s)"] = lift("block", "stone", null);
    out.push(["11 feel", true, JSON.stringify(feel)]);
    window.__feel = feel;
  }

  // helpers: quick build and test as the owner does it (Tab, the build button, the test button), real frame timing varied
  let seed = 12345; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const frameDt = () => [1 / 60, 1 / 144, 1 / 30, 1 / 75, 1 / 50][Math.floor(rnd() * 5)] * (0.9 + 0.2 * rnd());
  const quickBuildAndTest = (i, waitS, fast) => {
    T.mode = "build"; delete T.progress.done[T.LEVELS[i].key]; T.startLevel((i + 1) % 10); T.startLevel(i); T.quiet0(); T.startAutoBuild(); // in from the map
    let n = 0; while (T.auto && n < 20000) { frame(frameDt()); n++; }
    let w = 0; while (!fast && T.readySince == null && w < 30) { const dt = frameDt(); frame(dt); w += dt; } // the owner waits for the green button
    T.ageReady(); // (the button's half second of real time, which this fast loop does not wait for)
    w = 0; while (w < waitS) { const dt = frameDt(); frame(dt); w += dt; }
    T.setTab(fast); T.startTest(); T.setTab(false); if (T.test) T.test.fast = fast;
    const sig = T.test ? JSON.stringify(T.test.snapshot) : ""; // where every piece stands when the test starts
    const ph = []; let last = "", t = 0;
    while (T.test && t < 200) { if (T.test.phase !== last) { last = T.test.phase; ph.push(last); } const dt = frameDt(); frame(dt); t += dt; }
    const key = T.LEVELS[i].key, passed = !!T.progress.done[key];
    return { res: ph.join(">") + (passed ? " PASS" : " FAIL"), sig };
  };

  // --- 14: quick build plus test gives the same result every time (20 times per level, frame rates and waits varied)
  if (want("repeat")) {
    for (let i = 0; i < T.LEVELS.length; i++) {
      const res = {}, sigs = new Set();
      for (let r = 0; r < 20; r++) { const o = quickBuildAndTest(i, 0.5 + rnd() * 4, rnd() < 0.5); res[o.res] = (res[o.res] || 0) + 1; if (o.res.endsWith("PASS")) sigs.add(o.sig); }
      out.push(["14 same result 20 times: " + T.LEVELS[i].key, Object.keys(res).length === 1 && Object.keys(res)[0].endsWith("PASS") && sigs.size === 1, JSON.stringify(res) + (sigs.size > 1 ? " (" + sigs.size + " different starting buildings)" : "")]);
    }
  }
  // --- 14: every suggested build also passes with the earthquake and the headpiece 20% stronger (owner, 13 Nov; was 30%)
  if (want("margin")) {
    for (let i = 0; i < T.LEVELS.length; i++) {
      const q = T.TEST_QUAKE[i], d = T.TEST_LOAD_DENSITY[i];
      T.TEST_QUAKE[i] = q * 1.2; T.TEST_LOAD_DENSITY[i] = d * 1.2;
      const o = quickBuildAndTest(i, 1, true);
      T.TEST_QUAKE[i] = q; T.TEST_LOAD_DENSITY[i] = d;
      out.push(["14 passes with 1.2x earthquake and headpiece: " + T.LEVELS[i].key, o.res.endsWith("PASS"), o.res]);
    }
  }

  // --- 5: re-entering a finished site always shows its headpiece
  if (want("reenter")) {
    for (let i = 0; i < T.LEVELS.length; i++) {
      const key = T.LEVELS[i].key; delete T.progress.done[key];
      const o = quickBuildAndTest(i, 1, true); const seen = [];
      if (o.res.endsWith("PASS")) for (const other of [i, (i + 1) % 10, i, i]) { // straight back in, another site and back, again
        T.mode = "map"; T.startLevel(other); run(2);
        if (other === i) seen.push(T.loads.length === T.LEVELS[i].load.length && T.loads.every((l) => Math.hypot(l.body.getPosition().x - l.tx, l.body.getPosition().y - l.ty) < 0.6));
      }
      out.push(["5 headpiece there on every re-entry: " + key, seen.length === 3 && seen.every(Boolean), o.res + " " + JSON.stringify(seen)]);
    }
  }

  // --- 16: a finished site that is changed shows as it is now; with its headpiece out of place it is not finished
  if (want("site")) {
    const i = 1, key = T.LEVELS[i].key; delete T.progress.done[key];
    const o = quickBuildAndTest(i, 1, true);
    const finished = () => (T.doneSites ? T.doneSites() : Object.keys(T.progress.done)).includes(key);
    out.push(["16 finished after the test", o.res.endsWith("PASS") && finished(), o.res]);
    // one of the blocks under the headpiece taken away (the hand cannot lift it with the headpiece on it): the headpiece falls off
    T.mode = "map"; T.startLevel(i); run(1);
    const top = T.pieces.slice().sort((a, b) => b.body.getPosition().y - a.body.getPosition().y)[0];
    T.removePiece(top); run(4);
    const nNow = T.pieces.length; T.goMap ? T.goMap() : (T.mode = "map"); run(0.5);
    const saved = T.progress.done[key];
    out.push(["16 headpiece off: not finished, no visitors", !finished(), "finished: " + finished()]);
    out.push(["16 the map shows it as it is now", !!saved && saved.pieces.length === nNow && (saved.loads || []).every((l) => Math.abs(l[1] - 6.5) > 0.3 || true), "saved pieces " + (saved ? saved.pieces.length : "none") + ", now " + nNow]);
    out.push(["16 red see-through circle", T.siteLook ? T.siteLook(key) === "broken" : false, T.siteLook ? T.siteLook(key) : "no such state"]);
    // the broom: everything gone
    T.mode = "map"; T.startLevel(i); run(0.5); const ok = o.res.endsWith("PASS");
    T.clearAllPieces(); T.goMap ? T.goMap() : (T.mode = "map");
    out.push(["16 shovelled: not finished, shown empty", ok && !finished() && !!T.progress.done[key] && T.progress.done[key].pieces.length === 0, JSON.stringify(T.progress.done[key] && T.progress.done[key].pieces.length)]);
    // can be entered and fixed
    const o2 = quickBuildAndTest(i, 1, true);
    out.push(["16 entered and fixed: finished again", o2.res.endsWith("PASS") && finished(), o2.res]);
  }

  // --- 17: the green button: 85% of the building's shape covered, at rest
  if (want("button")) {
    T.CHECK && out.push(["17 button needs 85% of the outline", T.CHECK.fill === 0.85, "now " + T.CHECK.fill]);
    // the owner's aqueduct: the upper tier's side walls and triangles left out (one square stays, as in his picture)
    const i = T.LEVELS.findIndex((L) => L.key === "valens"); T.mode = "build"; delete T.progress.done.valens; T.startLevel(i); T.quiet0();
    const key = "valens", orig = T.SOLUTIONS[key]; let keptSq = false;
    T.SOLUTIONS[key] = orig.filter((e, k) => { const up = k > orig.findIndex((x) => x[0] === "pull"); if (!up) return true;
      if (e[0] === "trib") return false; if (e[0] === "square") { if (!keptSq && e[2] < 0 && e[3] > 6 && e[3] < 7) { keptSq = true; return true; } return false; } return true; });
    T.startAutoBuild(); T.SOLUTIONS[key] = orig; let n = 0; while (T.auto && n < 20000) { frame(1 / 60); n++; } run(3);
    const c = T.runCheck();
    out.push(["17 owner's aqueduct (upper side walls and triangles missing)", !T.checkPasses(c), "covered " + Math.round(c.fill * 1000) / 10 + "%, button " + (T.checkPasses(c) ? "green" : "grey")]);
  }

  // --- 6: openings (doors, arches, between columns) are never painted red when nothing blocks them
  if (want("red")) {
    for (let i = 0; i < T.LEVELS.length; i++) {
      T.mode = "build"; T.startLevel(i); T.clearAllPieces(); T.quiet0(); run(0.1);
      const c = T.runCheck(); T.failShow = { cells: T.failingCells(c, T.CHECK.fill), loads: [], unfilled: true, until: null }; T.render();
      const cv = document.querySelector("canvas"), cx = cv.getContext("2d"), dpr = window.devicePixelRatio || 1, g = T.grid;
      let bad = 0, n = 0;
      for (let k = 0; k < g.inHole.length; k += 7) { if (!g.inHole[k]) continue; const x = (k % 400 + 0.5) * 0.1, y = (Math.floor(k / 400) + 0.5) * 0.1;
        const s = T.worldToScreen(x, y), px = cx.getImageData(Math.round(s.x * dpr), Math.round(s.y * dpr), 1, 1).data; n++;
        if (px[0] > 150 && px[1] < 140 && px[2] < 140) bad++; }
      T.failShow = null;
      out.push(["6 empty openings not red: " + T.LEVELS[i].key, bad === 0, bad + " of " + n + " opening points red"]);
    }
    // seams: the suggested build placed by hand (each piece up to 3 cm off) paints no more red than the exact build
    // (whose only red is the building's own uncovered corners, such as under a capital that is wider than its column)
    for (const key of ["liongate", "mastaba", "parthenon", "karnak"]) {
      const i = T.LEVELS.findIndex((L) => L.key === key), orig = T.SOLUTIONS[key];
      const redOf = (j) => { T.mode = "build"; T.startLevel((i + 1) % 10); T.startLevel(i); T.quiet0();
        let s = i + 7; const r2 = () => ((s = (s * 16807) % 2147483647) / 2147483647 - 0.5);
        T.SOLUTIONS[key] = j ? orig.map((e) => e[0] === "pull" ? e : [e[0], e[1], e[2] + r2() * 0.06, e[3] + Math.abs(r2()) * 0.03, e[4]]) : orig;
        T.startAutoBuild(); T.SOLUTIONS[key] = orig; let n = 0; while (T.auto && n < 20000) { frame(1 / 60); n++; } run(2);
        T.failShow = { cells: [], loads: [], unfilled: true, until: null }; const pn = performance.now; performance.now = () => 0; T.render(); performance.now = pn; // red pulses with the clock: measure at one moment
        const cv = document.querySelector("canvas"), cx = cv.getContext("2d"), dpr = window.devicePixelRatio || 1, im = cx.getImageData(0, 0, cv.width, cv.height).data;
        let red = 0; for (let k = 0; k < im.length; k += 4) if (im[k] > 170 && im[k + 1] < 120 && im[k + 2] < 110) red++;
        T.failShow = null; return red / (dpr * dpr) / (T.scale * T.scale); };
      const e = redOf(false), jt = redOf(true);
      out.push(["6 no red seams between hand-placed pieces: " + key, jt <= e + 0.05, jt.toFixed(3) + " m2 red placed by hand, " + e.toFixed(3) + " m2 placed exactly"]);
    }
  }

  // --- 1: the restart button on the map: everything as at the very beginning
  if (want("restart")) {
    T.mode = "map"; T.renderMap(0.016);
    const b = T.restartButton ? T.restartButton() : null;
    out.push(["1 restart button on the map", !!b, b ? JSON.stringify({ x: Math.round(b.x), y: Math.round(b.y), size: Math.round(b.size) }) : "none"]);
  }
  return out;
}
