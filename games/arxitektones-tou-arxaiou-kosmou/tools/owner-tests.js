// Owner tests (sixth list): each repeats what the owner does in the game. Run: python3 tools/harness.py owner [names].
// Returns [[name, pass, detail], ...]. Uses window.__tb (tools/harness.py hook).
(names) => {
  const T = __tb, out = [], want = (n) => !names.length || names.includes(n);
  // Tests that do not look at the screen run without drawing: the canvas is one pixel while they run (a map frame then
  // takes under a millisecond instead of sixteen); afterwards it is put back and resized as the game does.
  const quick = (fn) => { const cv = document.querySelector("canvas"), W = cv.width, H = cv.height; cv.width = cv.height = 1; try { return fn(); } finally { cv.width = W; cv.height = H; window.dispatchEvent(new Event("resize")); } };
  const fleet = () => { for (const S of T.SITES) if (!T.progress.done[S.key]) T.progress.done[S.key] = { pieces: [], loads: [] }; T.renderMap(1 / 60); }; // owner 17 Nov: one boat per finished site
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
  // --- 14 Nov (owner): THE HAND LIST, approved point by point (BUILD.md "update 35"). Run: harness.py owner list
  if (want("list")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const MATS = ["stone", "mudbrick", "wood"], deg = (a) => (a * 57.3).toFixed(0);
    const piece = (d, x, y, a, m) => { T.clearAllPieces(); const p = T.spawnPiece(d, x, y, a || 0, m); run(0.3); return p; };
    const grab = (p, lx, ly) => { const w = p.body.getWorldPoint({ x: lx, y: ly }), g = { x: w.x, y: w.y }; T.startHold(p, g, 86, 0, 0); p.desired = { x: g.x, y: g.y }; return g; };
    const let_go = () => T.releaseHold(86);
    const P = (n, txt, ok, det) => out.push(["list " + n + " " + txt, !!ok, det]);
    // 1, 4: grabbed in the middle and held still: level
    for (const m of MATS) { const p = piece("block", X, 5, 0, m); grab(p, 0, 0); let t = 0; for (let k = 0; k < 90; k++) { frame(1 / 60); t = Math.max(t, Math.abs(p.body.getAngle())); } let_go();
      P("1", m + " block grabbed in the middle, held still, stays level", t < 0.05, "tilted " + deg(t) + " degrees"); }
    // 2, 4: every piece: grabbed in its middle third stays level when lifted and carried; in an outer third it turns down
    for (const m of MATS) for (const d of ["block", "block-half", "square", "abacus", "beam", "column", "bigsquare"]) {
      const hx = T.PIECE_DEFS[d].hx; let t = 0;
      { const p = piece(d, X - 2, 4, 0, m); const g = grab(p, hx * 0.3, 0);
        for (let k = 0; k < 120; k++) { const u = Math.min(1, k / 30), w = Math.min(1, Math.max(0, (k - 30) / 30)); p.desired = { x: g.x + 3 * w, y: g.y + 1.5 * u }; frame(1 / 60); t = Math.max(t, Math.abs(p.body.getAngle())); } let_go(); }
      let down = 0; { const p = piece(d, X - 2, 4, 0, m); const g = grab(p, hx * 0.85, 0);
        for (let k = 0; k < 90; k++) { p.desired = { x: g.x, y: g.y + Math.min(1.5, k / 20) }; frame(1 / 60); down = Math.max(down, Math.abs(p.body.getAngle())); } let_go(); }
      P("2", m + " " + d + ": grabbed in its middle third stays level, in an outer third turns down", t < 0.1 && down > 0.8, "middle third tilted " + deg(t) + ", outer third turned " + deg(down) + " degrees"); }
    // 1b (owner 14 Nov): a block grabbed in the middle along its length, near its top or bottom edge, dragged sideways fast through the air: no tilt
    for (const m of MATS) for (const ly of [0.45, -0.45]) { const p = piece("block", X - 3, 5, 0, m); const g = grab(p, 0, ly); run(0.5); let t = 0;
      for (let k = 0; k < 150; k++) { const u = Math.min(1, Math.max(0, k / 20)); p.desired = { x: g.x + 5 * u, y: g.y }; frame(1 / 60); t = Math.max(t, Math.abs(p.body.getAngle())); } let_go();
      P("1b", m + " block grabbed near its " + (ly > 0 ? "top" : "bottom") + " edge in the middle, dragged sideways fast, does not tilt", t < 0.1, "tilted " + deg(t) + " degrees"); }
    // 3, 4: grabbed at one end: hangs (within 20 degrees of straight down) within 1.5 s and stays there, no bouncing
    for (const m of MATS) { const p = piece("block", X, 5, 0, m); const g = grab(p, 0.9, 0); let settled = null;
      for (let k = 0; k < 300; k++) { p.desired = { x: g.x, y: g.y + Math.min(1, k / 18) }; frame(1 / 60); const off = Math.abs(Math.abs(p.body.getAngle()) - Math.PI / 2); if (off < 0.35) { if (settled == null) settled = k / 60; } else settled = null; } let_go();
      P("3", m + " block grabbed at one end hangs within 1.5 s and stays, no bouncing", settled != null && settled <= 1.5, "hangs still from " + (settled == null ? "never (5 s)" : settled.toFixed(2) + " s")); }
    // 5: standing block grabbed at its outer side half way up and lifted: falls round at once
    for (const m of MATS) { const p = piece("block", X, 3, Math.PI / 2, m); run(0.3); const a0 = p.body.getAngle(), c = p.body.getWorldCenter(), g = { x: c.x + 0.48, y: c.y }; T.startHold(p, g, 86, 0, 0); let t = null;
      for (let k = 0; k < 60; k++) { p.desired = { x: g.x, y: g.y + Math.min(1.5, k / 30) }; frame(1 / 60); if (t == null && Math.abs(p.body.getAngle() - a0) > 1.2) t = k / 60; } let_go();
      P("5", "standing " + m + " block grabbed at its outer side and lifted falls round at once", t != null && t <= 0.8, "most of the way round after " + (t == null ? "more than 1" : t.toFixed(2)) + " s"); }
    // 6-9: moved 3 m fast and stopped: runs on a little, comes back once slowly, never passes the finger again
    const RUN = { stone: 0.5, mudbrick: 0.4, wood: 0.3 };
    for (const m of MATS) for (const [n, dx, dy, y] of [["6", 3, 0, 5], ["7", 0, -3, 7.5], ["8", 0, 3, 3]]) {
      const p = piece("block", X - 1.5, y, 0, m); const g = grab(p, 0, 0); run(0.3); let peak = -9, after = 9, back = 0, prev = null;
      for (let k = 0; k < 300; k++) { const u = Math.min(1, k / 15); p.desired = { x: g.x + dx * u, y: g.y + dy * u }; frame(1 / 60);
        const c = p.body.getWorldCenter(), d = ((c.x - g.x - dx) * dx + (c.y - g.y - dy) * dy) / 3;
        if (k > 15) { if (d > peak) { peak = d; after = 9; } else after = Math.min(after, d); if (prev != null) back = Math.max(back, (prev - d) * 60); } prev = d; } let_go();
      const dir = dx ? "sideways" : dy < 0 ? "down" : "up";
      P(n, m + " block moved 3 m " + dir + " fast and stopped: runs on as its weight gives (owner: from the 9 m mudbrick throw; shown only)", true, "ran on " + Math.max(0, peak).toFixed(2) + " m");
      P("9", m + " block moved " + dir + ": comes back once, slowly, never passes the finger again", after > -0.05 && back < 1.5, "came back to " + Math.max(-9, -after).toFixed(2) + " m the other side, at up to " + back.toFixed(1) + " m/s"); }
    // 9b (owner 14 Nov): inertia: moved the same way (3 m in a second) and stopped, stone runs on further than mudbrick, mudbrick than wood
    { const ro = {}; for (const m of MATS) { const p = piece("block", X - 1.5, 5, 0, m); const g = grab(p, 0, 0); run(0.5); let peak = -9;
        for (let k = 0; k < 260; k++) { p.desired = { x: g.x + Math.min(3, 1.5 * k / 60), y: g.y }; frame(1 / 60); if (k > 120) peak = Math.max(peak, p.body.getWorldCenter().x - g.x - 3); } let_go(); ro[m] = +Math.max(0, peak).toFixed(2); }
      P("9b", "moved 3 m at a steady walk (1.5 m/s) and stopped suddenly, stone runs on further than mudbrick, mudbrick than wood", ro.stone > ro.mudbrick && ro.mudbrick > ro.wood, "ran on (m): " + JSON.stringify(ro)); }
    // 10: slow finger: within a hand-width
    for (const m of MATS) { const p = piece("block", X - 2, 5, 0, m); grab(p, 0, 0); run(1); const g0 = p.body.getWorldPoint(p.grabLocal), g = { x: g0.x, y: g0.y }; let far = 0;
      for (let k = 0; k < 180; k++) { const f = { x: g.x + 0.5 * k / 60, y: g.y + 0.2 * Math.sin(k / 30) }; p.desired = f; frame(1 / 60); const q = p.body.getWorldPoint(p.grabLocal); if (k > 30) far = Math.max(far, Math.hypot(q.x - f.x, q.y - f.y)); } let_go();
      P("10", m + " block follows a slow finger within a hand-width", far <= 0.15, "at most " + far.toFixed(2) + " m from the finger"); }
    // 11: grabbed in the middle, follows small quick circles
    for (const m of MATS) { const p = piece("block", X, 6, 0, m); const g = grab(p, 0, 0); run(0.3); let sag = 0, n = 0, lo = 1e9, hi = -1e9;
      for (let k = 0; k < 180; k++) { const th = k / 60 * 2 * Math.PI * 1.5, f = { x: g.x + 0.3 * Math.sin(th), y: g.y + 0.3 - 0.3 * Math.cos(th) }; p.desired = f; frame(1 / 60); const q = p.body.getWorldCenter(); if (k >= 60) { sag += f.y - q.y; lo = Math.min(lo, q.y); hi = Math.max(hi, q.y); n++; } } let_go();
      P("11", m + " block grabbed in the middle follows small quick circles", sag / n < 0.15 && hi - lo > 0.4, "on average " + (sag / n).toFixed(2) + " m under the finger, its circle " + (hi - lo).toFixed(2) + " m across (finger's 0.6)"); }
    // 12, 13: carrying 4 m
    const carry = (d, m) => { const p = piece(d, X - 4, 3, 0, m), c = p.body.getWorldCenter(); const g = grab(p, p.body.getLocalPoint(c).x, p.body.getLocalPoint(c).y); run(0.3); let t = null;
      for (let k = 0; k < 240 && t == null; k++) { p.desired = { x: g.x + 4, y: g.y }; frame(1 / 60); if (p.body.getPosition().x > g.x + 3.9) t = k / 60; } let_go(); return t == null ? 9 : +t.toFixed(2); };
    const ct = {}; for (const m of MATS) ct[m] = carry("block", m);
    const near = (a, b, f) => Math.abs(a - b) <= f * b;
    P("12", "carrying 4 m: wood quickest, then mudbrick, then stone (owner: same effort for every piece, times as they come)", ct.wood < ct.mudbrick && ct.mudbrick < ct.stone, JSON.stringify(ct));
    { const a = carry("abacus", "stone"), b = carry("column", "wood"); P("13", "same weight, same carry: small oblong stone and wooden column", near(a, b, 0.15), a + " s and " + b + " s"); }
    // 14, 15: lifting by weight, one piece or a stack
    const lift = (stack) => { T.clearAllPieces(); let top = 0; const ps = []; for (const [d, m] of stack) { const hy = T.PIECE_DEFS[d].hy; ps.push(T.spawnPiece(d, X, top + hy + 0.003, 0, m)); top += 2 * hy; run(0.4); }
      run(0.5); const b = ps[0], y0 = b.body.getPosition().y; const g = grab(b, 0, 0); let t = null, jump = 0;
      for (let k = 0; k < 240; k++) { b.desired = { x: g.x, y: g.y + 1.5 }; frame(1 / 60); if (t == null && b.body.getPosition().y - y0 > 1) t = k / 60;
        for (let i = 1; i < ps.length; i++) jump = Math.max(jump, (ps[i].body.getPosition().y - T.PIECE_DEFS[ps[i].defKey].hy) - (ps[i - 1].body.getPosition().y + T.PIECE_DEFS[ps[i - 1].defKey].hy)); }
      const rose = b.body.getPosition().y - y0; let_go(); return { t, rose, jump, ps }; };
    { const a = lift([["block", "stone"], ["block", "stone"]]), b = lift([["bigsquare", "stone"]]);
      P("14", "a stack lifts like one piece of the same weight (two stone blocks, big stone square)", a.t != null && b.t != null && near(a.t, b.t, 0.2), "1 m up after " + a.t + " s and " + b.t + " s");
      const c = lift([["block", "stone"], ["block", "stone"], ["block", "stone"]]);
      P("15", "two stone blocks lift slowly, three not at all", a.t != null && a.t > 0.6 && c.rose < 0.2, "two: 1 m after " + a.t + " s; three rose " + c.rose.toFixed(2) + " m"); }
    // 16-19: letting go
    const fling = (m, speed, still) => { const p = piece("block", X - 8, 5, 0, m), g = grab(p, 0, 0); run(0.3);
      for (let k = 0; k < (speed > 5 ? 58 : 150) && !still; k++) { p.desired = { x: g.x + speed * k / 60, y: g.y }; frame(1 / 60); }
      // where it lands: from its speed and height when let go (real falling; the screen's edge would stop the longest throws)
      const x0 = p.body.getPosition().x, y0 = p.body.getPosition().y, vx = p.body.getLinearVelocity().x, vy = p.body.getLinearVelocity().y; let_go();
      const t = (vy + Math.sqrt(vy * vy + 2 * 10 * (y0 - 0.5))) / 10; return +(vx * t).toFixed(2); };
    { const r = {}; for (const m of MATS) r[m] = fling(m, 15);
      P("16", "mudbrick block swept at full speed, let go at mid-screen height, lands a bit less than 8 m (owner: 9 m, then a bit less)", r.mudbrick >= 6.5 && r.mudbrick <= 7.6, "m: " + JSON.stringify(r));
      P("17", "wood flies further than mudbrick, stone less far", r.wood > r.mudbrick && r.mudbrick > r.stone, "m: " + JSON.stringify(r));
      const n = {}; for (const m of MATS) n[m] = fling(m, 2); P("18", "let go during a normal drag (2 m/s) at mid-screen height, lands where real falling puts it (about 2 m)", Object.values(n).every((v) => v >= 1.5 && v <= 2.5), "m: " + JSON.stringify(n));
      const s0 = {}; for (const m of MATS) s0[m] = fling(m, 0, true); P("19", "let go while held still, drops straight down", Object.values(s0).every((v) => Math.abs(v) < 0.1), "m: " + JSON.stringify(s0)); }
    // 20-22: stacks lifted by the bottom piece, then carried sideways and stopped
    for (const [name, st] of [["two stone blocks", [["block", "stone"], ["block", "stone"]]], ["two mudbrick blocks", [["block", "mudbrick"], ["block", "mudbrick"]]], ["two wooden blocks", [["block", "wood"], ["block", "wood"]]],
      ["four stone squares", [["square", "stone"], ["square", "stone"], ["square", "stone"], ["square", "stone"]]], ["three wooden blocks", [["block", "wood"], ["block", "wood"], ["block", "wood"]]]]) {
      T.clearAllPieces(); let top = 0; const ps = []; for (const [d, m] of st) { const hy = T.PIECE_DEFS[d].hy; ps.push(T.spawnPiece(d, X - 3, top + hy + 0.003, 0, m)); top += 2 * hy; run(0.4); }
      run(0.5); const b = ps[0], g = grab(b, 0, 0); let jump = 0, tilt = 0;
      for (let k = 0; k < 240; k++) { const u = Math.min(1, k / 40), w = Math.min(1, Math.max(0, (k - 80) / 30)); b.desired = { x: g.x + 3 * w, y: g.y + 1.5 * u }; frame(1 / 60);
        for (let i = 1; i < ps.length; i++) { if (k < 80) jump = Math.max(jump, (ps[i].body.getPosition().y - T.PIECE_DEFS[ps[i].defKey].hy) - (ps[i - 1].body.getPosition().y + T.PIECE_DEFS[ps[i - 1].defKey].hy)); tilt = Math.max(tilt, Math.abs(ps[i].body.getAngle())); }
        tilt = Math.max(tilt, Math.abs(b.body.getAngle())); }
      const on = ps.every((q, i) => i === 0 || (Math.abs(q.body.getPosition().x - ps[i - 1].body.getPosition().x) < 0.4 && q.body.getPosition().y > ps[i - 1].body.getPosition().y)); let_go();
      P("20", name + " lifted by the bottom one: the rest stays sitting on it", jump <= 0.02, "largest gap " + jump.toFixed(3) + " m");
      P("21", name + " carried sideways and stopped: nothing tips, all stay on", on && tilt < 0.1, "tilted " + deg(tilt) + " degrees, all on: " + on); }
    // 23: held at one long end, hand circles as big as the round stone: once round per circle, smoothly (owner: try slower circles)
    for (const m of MATS) { const res = {}; for (const per of [1, 1.5, 2]) { const p = piece("block", X, 6, 0, m); const g = grab(p, 0.9, 0); run(2.5); let prev = p.body.getAngle(), tot = 0, rev = 0; const R = T.PIECE_DEFS.drum.r, N = Math.round(5 * per * 60);
        for (let k = 0; k < N; k++) { const th = k / 60 / per * 2 * Math.PI; p.desired = { x: g.x + R * Math.sin(th), y: g.y + R - R * Math.cos(th) }; frame(1 / 60); const a = p.body.getAngle(); if (k >= per * 60) { tot += a - prev; rev = Math.min(rev, Math.sign(tot || 1) * (a - prev)); } prev = a; } let_go();
        res[per] = { turns: +(Math.abs(tot) / (2 * Math.PI)).toFixed(2), back: +deg(-rev) }; }
      // 23b: the same with a slow mouse or touch screen: the finger's position arrives only every third step (20 a second)
      { const p = piece("block", X, 6, 0, m); const g = grab(p, 0.9, 0); run(2.5); let prev = p.body.getAngle(), tot = 0; const R = T.PIECE_DEFS.drum.r;
        for (let k = 0; k < 300; k++) { if (k % 3 === 0) { const th = k / 60 * 2 * Math.PI; p.desired = { x: g.x + R * Math.sin(th), y: g.y + R - R * Math.cos(th) }; } frame(1 / 60); const a = p.body.getAngle(); if (k >= 60) tot += a - prev; prev = a; } let_go();
        res.slowMouse = +(Math.abs(tot) / (2 * Math.PI)).toFixed(2); }
      const ok = res[1].turns >= 3.6 && res[1].back < 2 && res.slowMouse >= 3.6;
      P("23", m + " block held at one end goes round once per hand circle (as big as the round stone), smoothly, at some speed of circles", ok, "turns in 4 circles, by seconds per circle: " + JSON.stringify(res)); }
    // 27: (owner: physics decides) small oblong stone rammed fast into a stone block
    { T.clearAllPieces(); const t = T.spawnPiece("block", X + 1.5, 0.503, 0, "stone"); run(0.5); const p = T.spawnPiece("abacus", X - 3, 0.703, 0, "stone"); run(0.3); const g = grab(p, 0, 0); const x0 = t.body.getPosition().x;
      for (let k = 0; k < 120; k++) { p.desired = { x: g.x + Math.min(6, k * 0.2), y: g.y }; frame(1 / 60); } let_go(); run(1);
      P("27", "small oblong stone rammed fast into a stone block (physics decides, shown only)", true, "moved it " + (t.body.getPosition().x - x0).toFixed(2) + " m"); }
    // 30: no slowing down before touching another piece
    { const speedAt = (wall) => { T.clearAllPieces(); if (wall) T.spawnPiece("block", X + 2, 0.503, 0, "stone"); const p = T.spawnPiece("block", X - 2, 2.5, 0, "stone"); run(0.3); const g = grab(p, 0, 0); let v = null;
        for (let k = 0; k < 120 && v == null; k++) { p.desired = { x: g.x + 6, y: g.y - 2 }; frame(1 / 60); if (p.body.getPosition().x > X - 0.3) v = p.body.getLinearVelocity().x; } let_go(); return v; };
      const a = speedAt(true), b = speedAt(false); P("30", "no slowing down before touching another piece", a != null && b != null && a >= 0.9 * b, "speed near the block " + (a || 0).toFixed(1) + " m/s, with no block " + (b || 0).toFixed(1)); }
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

  // --- owner 15 Nov night: a row of pieces pushed by one end piece moves as one load, wherever that piece is grabbed
  if (want("train")) {
    T.mode = "build"; T.startLevel(0); T.clearAllPieces(); T.fillPile([]);
    const D = T.PIECE_DEFS.block, hx = D.hx, hy = D.hy;
    // pieces: [[x, y, material]]; grab the first at local x gx (share of its half width); push right 3 m at a hand's pace
    const shove = (set, gx) => { T.clearAllPieces(); const ps = set.map(([x, y, m]) => T.spawnPiece("block", x, y, 0, m)); run(1.5);
      const x0 = ps.map((q) => q.body.getPosition().x), p = ps[0], g = p.body.getWorldPoint({ x: gx * hx, y: 0 }); T.startHold(p, { x: g.x, y: g.y }, 93, 0, 0);
      for (let k = 0; k < 240; k++) { const t = k / 60; p.desired = { x: g.x + Math.min(3, t < 0.3 ? 2 * t * t / 0.6 : 0.3 + 2 * (t - 0.3)), y: g.y }; frame(1 / 60); }
      T.releaseHold(93); run(1); return ps.map((q, i) => +(q.body.getPosition().x - x0[i]).toFixed(2)); };
    const row = (n, m) => Array.from({ length: n }, (_, i) => [X - 3 + i * (2 * hx + 0.005), hy + 0.003, m]);
    for (const gx of [-0.6, 0.6]) {
      const r = shove(row(3, "stone"), gx), lo = Math.min(...r);
      out.push(["15 Nov three stone blocks on the floor pushed like a train by an end block (grabbed " + (gx < 0 ? "outer" : "inner") + " half) all move", lo > 0.5, "moved " + r.join(", ") + " m"]);
      const q = shove([[X - 3, hy + 0.003, "mudbrick"], [X - 3 + 2 * hx + 0.005, hy + 0.003, "mudbrick"], [X - 3 + hx + 0.0025, 3 * hy + 0.01, "mudbrick"]], gx), ql = Math.min(...q);
      out.push(["15 Nov mudbrick pyramid (two below, one on top) pushed by a bottom brick (grabbed " + (gx < 0 ? "outer" : "inner") + " half) moves", ql > 0.5, "moved " + q.join(", ") + " m"]);
    }
    const four = shove(row(4, "stone"), -0.6);
    out.push(["15 Nov four stone blocks in a row: too heavy to push (shown only)", true, "moved " + four.join(", ") + " m"]);
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

  // --- owner 16 Nov, late, free play: "I cannot pull the lever down, from its left side". His build: two stone squares
  // with a small stone between, a wooden drum on them, a 10 m plank across the drum, its right end on the ground. The hand
  // takes the plank near its raised left end and pulls down 2 m in a second, as a mouse does (60 moves a second).
  // Owner 16 Nov, late: "I can lift it up from anywhere but not pull it down from anywhere (only from its end)": the same
  // pull from points all along the raised side, each must tip the plank (its raised side goes down), and lifting still works.
  if (want("lever")) {
    const build = () => { T.mode = "build"; T.startFree(); T.clearAllPieces(); if (T.fillPile) T.fillPile([]);
      T.spawnPiece("square", X - 0.95, 0.503, 0, "stone"); T.spawnPiece("square", X + 0.95, 0.503, 0, "stone"); T.spawnPiece("abacus", X, 0.203, 0, "stone"); run(0.5);
      T.spawnPiece("drum", X, 1.61, 0, "wood"); run(0.5);
      const pl = T.spawnPiece("plank10", X + 0.3, 3.0, -0.3, "wood"); run(3); return pl; };
    for (const [lx, dir] of [[-4.6, -1], [-3.5, -1], [-2.5, -1], [-1.5, -1], [-4.6, 1], [-1.5, 1], [2, 1], [4.6, 1]]) {
      const pl = build(), a0 = pl.body.getAngle(), e0 = pl.body.getWorldPoint({ x: lx, y: 0 }), g = { x: e0.x, y: e0.y };
      T.startHold(pl, g, 92, 0, 0);
      for (let k = 0; k < 120; k++) { pl.desired = { x: g.x, y: g.y + dir * Math.min(2, k * 2 / 60) }; frame(1 / 60); }
      const e1 = pl.body.getWorldPoint({ x: lx, y: 0 }), moved = dir * (e1.y - e0.y), turn = (pl.body.getAngle() - a0) * 180 / Math.PI, onDrum = Math.abs(pl.body.getPosition().x - X) < 4;
      T.releaseHold(92); run(1);
      const name = dir < 0 ? "lever: the plank pulled down 2 m at " + (lx + 5).toFixed(1) + " m from its raised end" : "lever: the plank lifted 2 m at " + (lx + 5).toFixed(1) + " m from its raised end";
      out.push([name, moved > (dir < 0 ? Math.min(1.5, 0.5 * Math.abs(lx - 0.35)) : 1.5) && onDrum, "the grab point went " + (dir < 0 ? "down " : "up ") + moved.toFixed(2) + " m, plank turned " + turn.toFixed(0) + " deg, still across the drum: " + onDrum]);
    }
  }

  // --- owner 16 Nov, late: "on quick build, stop on ESC"
  if (want("esc-quick")) {
    T.mode = "build"; T.startLevel(1); T.startAutoBuild(); run(1);
    const n0 = T.pieces.length; window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" })); run(2);
    out.push(["ESC stops the quick build", !T.auto && T.mode === "build" && n0 > 0, "building: " + !!T.auto + ", still on the site: " + (T.mode === "build") + ", pieces " + n0 + " -> " + T.pieces.length]);
  }
  // --- owner 16 Nov, late: "the intensity of the sound that objects make when they hit the ground must be relative to their mass, use current std 2m rectangular blocks as reference points"
  if (want("hit-weight")) {
    T.mode = "build"; T.startFree(); T.clearAllPieces(); const bad = [];
    for (const m of ["stone", "mudbrick", "wood"]) for (const [d, want] of [["block", 1], ["square", 0.5], ["bigsquare", 2], ["abacus", 0.16]]) {
      const p = T.spawnPiece(d, X, 3, 0, m), v = T.inBlocks(p.body, m); T.removePiece(p);
      if (Math.abs(v - want) > 0.02 * want + 0.01) bad.push(m + " " + d + " " + v.toFixed(2));
    }
    out.push(["a piece that hits, breaks or slides sounds as loud as its weight in 2 m blocks", !bad.length, bad.join("; ") || "block 1, square 1/2, big square 2, small oblong 0.16, for stone, mudbrick, wood"]);
  }

  // --- owner 16 Nov, late: "a bug with the biggest oblong piece in the sandbox sidebar, it gets dragged out and it has a lot of
  // speed ... once I saw the same with the big stone boulder ... even without coming out of the sidebar". A real mouse (60 moves
  // a second) takes each piece from the free-play sidebar: lifted inside the sidebar, then carried out to the building area;
  // on screen it is never faster than the arm can move its weight in the building area.
  if (want("sidebar-speed")) {
    const cv = document.querySelector("canvas");
    const ptr = (type, x, y) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, pointerId: 7, isPrimary: true, pointerType: "mouse", button: 0, buttons: type === "pointerup" ? 0 : 1, bubbles: true }));
    for (const [d, m, off, fast] of [["longblock", "stone", 0, 1], ["longblock", "stone", 0.8, 1], ["longblock", "stone", 0, 3], ["longblock", "stone", -0.8, 3], ["bigsquare", "stone", 0, 1], ["bigsquare", "stone", 0.7, 3], ["block", "stone", 0, 1], ["block", "stone", 0.8, 3], ["square", "stone", 0, 3], ["block", "wood", 0.8, 3]]) {
      T.mode = "build"; T.startFree(); T.clearAllPieces(); T.render(); run(3);
      const r = T.pileBinRect, b = T.pileBodies().find((q) => q.pileItem.defKey === d && q.pileItem.material === m);
      if (!b) { out.push(["sidebar speed " + m + " " + d, false, "not in the pile"]); continue; }
      const q0 = b.getWorldPoint({ x: off * T.PIECE_DEFS[d].hx, y: 0 }), a = { x: r.x + q0.x * T.pileScale, y: r.y + r.h - q0.y * T.pileScale };
      const path = [], n1 = Math.round(40 / fast), n2 = Math.round(50 / fast);
      for (let k = 0; k <= n1; k++) path.push({ x: a.x, y: a.y - Math.min(160, a.y - r.y - 40) * k / n1 }); // up inside the sidebar
      const top = path[path.length - 1];
      for (let k = 1; k <= n2; k++) path.push({ x: top.x - (top.x - T.buildingWidthPx * 0.5) * k / n2, y: top.y }); // out to the building area
      for (let k = 0; k < 60; k++) path.push(path[path.length - 1]); // held still, 1 s
      let maxIn = 0, maxOut = 0, finger = 0, prev = null, over = 0, outN = 0;
      ptr("pointerdown", a.x, a.y);
      for (let k = 0; k < path.length; k++) {
        ptr("pointermove", path[k].x, path[k].y); frame(1 / 60);
        if (k) finger = Math.max(finger, Math.hypot(path[k].x - path[k - 1].x, path[k].y - path[k - 1].y) * 60);
        const pb = T.pileBodies().includes(b) ? b : null, wp = T.pieces.find((p) => p.heldBy === 7);
        if (pb) { const h = [...T.pointers.values()].find((q) => q.pileBody === pb), v = h ? pb.getLinearVelocityFromWorldPoint(pb.getWorldPoint(h.pileGrab)) : pb.getLinearVelocity(); maxIn = Math.max(maxIn, Math.hypot(v.x, v.y) * T.pileScale); }
        else if (wp) { const v = wp.body.getLinearVelocityFromWorldPoint(wp.body.getWorldPoint(wp.grabLocal)); if (outN++ < 3) maxOut = Math.max(maxOut, Math.hypot(v.x, v.y) * T.scale); // the hand's point: the speed it comes out of the sidebar with (after that the arm in the building area moves it, as any piece)
          const g = wp.body.getWorldPoint(wp.grabLocal), sg = T.worldToScreen(g.x, g.y), f = path[k]; if (k >= path.length - 60) over = Math.max(over, Math.hypot(sg.x - f.x, sg.y - f.y)); }
      }
      ptr("pointerup", path[path.length - 1].x, path[path.length - 1].y); run(1);
      if (off && (d === "longblock" || m === "wood")) { // still: grabbed near an end, it hangs and swings in the sidebar (turned upright before it is taken out)
        T.startFree(); T.clearAllPieces(); T.render(); run(3);
        const r2 = T.pileBinRect, b2 = T.pileBodies().find((q) => q.pileItem.defKey === d && q.pileItem.material === m), a2 = b2.getAngle(), q2 = b2.getWorldPoint({ x: off * T.PIECE_DEFS[d].hx, y: 0 }), s2 = { x: r2.x + q2.x * T.pileScale, y: r2.y + r2.h - q2.y * T.pileScale };
        ptr("pointerdown", s2.x, s2.y); for (let k = 1; k <= 30; k++) { ptr("pointermove", s2.x, s2.y - 120 * k / 30); frame(1 / 60); } run(2);
        const turned = Math.abs(b2.getAngle() - a2) * 180 / Math.PI; ptr("pointerup", s2.x, s2.y - 120); run(0.5);
        out.push(["sidebar: " + m + " " + d + " grabbed near an end and lifted hangs down", turned > 45, "turned " + turned.toFixed(0) + " deg"]);
      }
      const lim = T.armTopSpeed(b.getMass() * 10) * T.scale * 1.15 + 20; // what the arm can give this weight, on screen
      out.push(["sidebar speed: " + m + " " + d + " grabbed at " + off + ", drag x" + fast + ": no faster than the arm moves its weight", maxIn <= lim && maxOut <= lim, "most " + lim.toFixed(0) + " px/s; finger " + finger.toFixed(0) + " px/s, piece in the sidebar " + maxIn.toFixed(0) + " px/s, coming out " + maxOut.toFixed(0) + " px/s"]);
    }
  }

  // --- owner 16 Nov late and 17 Nov: sound levels (map taps twice 20% lower, rock twice 50% lower; material sounds equal, by
  // weight; every sound at half; map music 20% then 10% lower)
  if (want("sound-levels")) {
    const S = T.SOUNDS, v = (k) => S[k][0][1], bad = [];
    const near = (a, b) => Math.abs(a - b) < 1e-6;
    for (const k of ["map-tap-water", "map-tap-sand", "map-tap-green"]) if (!near(v(k), 0.8 * 0.8 * 0.8)) bad.push(k + " " + v(k));
    if (!near(v("map-tap-rock"), 0.8 * 0.5 * 0.5)) bad.push("map-tap-rock " + v("map-tap-rock"));
    for (const k of Object.keys(S)) if (/^hit-|^drag-|^crumble$|^snap$/.test(k) && !near(v(k), 0.8 * 0.9)) bad.push(k + " " + v(k)); // owner 17 Nov evening: material sounds 10% lower
    if (!near(v("music-map"), 0.2 * 0.8 * 0.9)) bad.push("music-map " + v("music-map"));
    if (T.MASTER_VOLUME !== 0.5) bad.push("all sounds at " + T.MASTER_VOLUME);
    out.push(["sound levels as the owner set them", !bad.length, bad.join("; ") || "ok"]);
  }

  // --- owner 17 Nov: "make the concentric waves from the clicks push the boats away from their route, according to the
  // concentric circles direction, and of course then the boats continue smoothly toward their destination". A mouse click
  // on the water just beside a sailing boat: the boat goes away from the click, then back onto its route smoothly, sailing on.
  if (want("wave-boat")) quick(() => {
    T.goMap(); fleet(); T.renderMap(1 / 60); const cv = document.querySelector("canvas"), v = T.mapView();
    // owner 17 Nov: "the boat pushing still feels double sometimes": clicks at several places around the boat, near and far (a far click's rings fade before they reach it: no push then, but never two); owner 17 Nov: "you now push them too far away and violently, especially when the click is right on the boat": at most about half a boat (30 map px); then "now they barely push. double the current force": a click right on the boat moves it 45-60 map px
    for (const [ox, oy] of [[0, 0], [-25, 10], [-8, 0], [0, -8], [40, 0], [-60, 20], [15, 30], [0, 70], [90, -20]]) {
    for (const q of T.boats) { q.ox = q.oy = q.ovx = q.ovy = 0; } T.renderMap(1 / 60); // nothing left over from the click before
    const b = T.boats.find((q) => q.wait <= 0) || T.boats[0], s0 = v.pt(b.x, b.y), tap = { x: s0.x + ox, y: s0.y + oy };
    const opt = { clientX: tap.x, clientY: tap.y, pointerId: 9, isPrimary: true, pointerType: "mouse", button: 0, bubbles: true };
    cv.dispatchEvent(new PointerEvent("pointerdown", { ...opt, buttons: 1 })); cv.dispatchEvent(new PointerEvent("pointerup", { ...opt, buttons: 0 }));
    const ser = []; let most = 0, away = 0, jumps = 0, goes = 1, slowing = false, lastSp = 0, prev = Math.hypot(b.ox, b.oy); /* owner 17 Nov: "the waves push the boat in 2 goes, the motion is not smooth": the boat speeds up once (one push), then only slows and returns */
    for (let k = 0; k < 360; k++) { T.renderMap(1 / 60); const o = Math.hypot(b.ox, b.oy); if (o > most) { most = o; away = (b.ox * (s0.x - tap.x) + b.oy * (s0.y - tap.y)) / (o * Math.hypot(s0.x - tap.x, s0.y - tap.y)); } if (Math.abs(o - prev) > 5) jumps++; /* more than 5 map px in one frame would look like a jump */ const sp = o - prev; ser.push(sp.toFixed(2)); if (sp > lastSp + 1e-3 && slowing && sp > 0) goes++; if (sp < lastSp - 1e-3) slowing = true; else if (sp > lastSp + 1e-3) slowing = false; lastSp = sp; prev = o; }
    const back = Math.hypot(b.ox, b.oy);
    out.push(["a click's waves push a boat away and it sails back smoothly to its route (click " + ox + "," + oy + " px from it)", (Math.hypot(ox, oy / 0.6) > 50 || (most > 3 && (away > 0.8 || Math.hypot(ox, oy) < 2))) && most <= 60 && (Math.hypot(ox, oy) > 2 || most >= 45) && back < 1 && !jumps && goes === 1, "pushed in " + goes + " go(es) " + most.toFixed(0) + " map px, direction away " + away.toFixed(2) + ", off its route after 6 s " + back.toFixed(1) + " px, jumps " + jumps]);
    }
  })

  // --- owner 17 Nov: "the sand hills of africa and arabia are counted as mountains by you, for the particle effects": places
  // on the map picture (map pixels) and what a tap there must show
  if (want("map-ground")) {
    const bad = [], want = { "sand dunes, Arabia": [1760, 1120, "sand"], "sand dunes, Arabia north": [1660, 1040, "sand"], "sand dunes, Sahara": [600, 1040, "sand"], "pale desert, Sahara": [300, 1000, "sand"],
      "mountain peaks, Sinai": [1300, 1030, "rock"], "mountain peaks, Arabia": [1580, 1250, "rock"], "mountain peaks, Greece": [220, 120, "rock"], "sea": [600, 600, "water"], "Nile valley": [780, 1120, "green"],
      // owner 17 Nov: "you name many mountains as sand. can you distinguish them?"
      "Zagros range": [2000, 600, "rock"], "Caucasus": [1800, 60, "rock"], "Armenian peaks": [1580, 250, "rock"], "Pindus": [190, 320, "rock"], "east Anatolian peak": [1230, 385, "rock"], "Libyan peaks": [210, 865, "rock"], "Balkan peaks": [190, 120, "rock"],
      "Egyptian dune ridge": [560, 1050, "sand"], "dunes, south-east Arabia": [1800, 1200, "sand"], "dunes, central Arabia": [1500, 1080, "sand"] };
    for (const [n, [x, y, k]] of Object.entries(want)) { const got = T.groundAt(x, y); if (got !== k) bad.push(n + ": " + got); }
    out.push(["a map tap shows sand on the sand dunes, stones on the mountains", !bad.length, bad.join("; ") || "all " + Object.keys(want).length + " places right"]);
  }

  // --- owner 17 Nov: "make the boats change shape as they turn and move in different directions ... pick 3rd [a boat
  // drawn by the game in 3D], give it the color and shape of the current boat": the boat seen sailing east, south and
  // north-east covers different shapes on screen
  if (want("boat-3d")) {
    const shape = (a) => { const c = document.createElement("canvas"); c.width = c.height = 200; const x = c.getContext("2d");
      T.SKIN.mapBoat(x, 100, 140, 110, a, 0, 0, null); const d = x.getImageData(0, 0, 200, 200).data, m = new Uint8Array(40000);
      for (let i = 0; i < 40000; i++) m[i] = d[i * 4 + 3] > 128 ? 1 : 0; return m; };
    const diff = (m, n) => { let a = 0, u = 0; for (let i = 0; i < m.length; i++) { a += m[i] !== n[i] ? 1 : 0; u += m[i] || n[i] ? 1 : 0; } return a / u; };
    const e = shape(0), so = shape(Math.PI / 2), ne = shape(-Math.PI / 4);
    const d1 = diff(e, so), d2 = diff(e, ne), d3 = diff(so, ne);
    out.push(["a map boat changes shape as it turns", d1 > 0.2 && d2 > 0.2 && d3 > 0.2, "east/south " + d1.toFixed(2) + ", east/north-east " + d2.toFixed(2) + ", south/north-east " + d3.toFixed(2) + " of the boat's area differs"]);
  }

  // --- owner 17 Nov: "the turning is not smooth, it just jumps to another orientation ... maybe the problem is that your sea
  // routes are angular and not bended": over a minute of sailing (60 frames a second) no boat's pointing or course jumps
  // between frames (the pointing turns at most 1.5 rad/s; the course bends at most 20 degrees from one frame to the next, that much only in the narrow Dardanelles, which cannot be rounded more without crossing land), and the rounded routes stay on the water
  if (want("boat-turn")) quick(() => {
    T.goMap(); fleet(); let worstHd = 0, worstCourse = 0, onLand = 0, prev = T.boats.map((b) => [b.hd, Math.atan2(b.vy, b.vx), b.wait]);
    for (const l of BOAT_LINES) for (const leg of l.legs) leg.forEach(([x, y], i) => { if (i > 10 && i < leg.length - 11 && T.isLand(x, y)) onLand++; }); // the ports sit on the coast and the drawn routes run along it by them
    for (let k = 0; k < 3600; k++) {
      T.renderMap(1 / 60);
      T.boats.forEach((b, i) => {
        const [h0, c0, w0] = prev[i], c1 = Math.atan2(b.vy, b.vx), dd = (a, c) => Math.abs(Math.atan2(Math.sin(a - c), Math.cos(a - c)));
        if (h0 !== null && b.hd !== null) worstHd = Math.max(worstHd, dd(b.hd, h0));
        if (w0 <= 0 && b.wait <= 0) worstCourse = Math.max(worstCourse, dd(c1, c0)); // turning round in port is not a course change
        prev[i] = [b.hd, c1, b.wait];
      });
    }
    out.push(["boats turn smoothly along rounded sea routes", worstHd <= 1.5 / 60 + 1e-6 && worstCourse < 0.35 && !onLand, "largest turn in one frame: pointing " + (worstHd * 180 / Math.PI).toFixed(1) + " deg, course " + (worstCourse * 180 / Math.PI).toFixed(1) + " deg; route points on land " + onLand]);
  })

  // --- owner 17 Nov: "dragging on the sand plains of africa and arabia, leaves a line on the sand ... the sandhills
  // shouldnt be in that area ... 2 mins after the first stroke in each area is made, a wind blows that erases the
  // writing, the wind must be local in that area only": a finger dragged as the child does (touch moves every few px)
  const mapFinger = (id) => { const cv = document.querySelector("canvas");
    const ev = (type, [x, y], b) => { const q = T.mapView().pt(x, y); cv.dispatchEvent(new PointerEvent(type, { clientX: q.x, clientY: q.y, pointerId: id, isPrimary: true, pointerType: "touch", button: 0, buttons: b, bubbles: true })); };
    return { down: (p) => ev("pointerdown", p, 1), move: (p) => ev("pointermove", p, 1), up: (p) => ev("pointerup", p, 0),
      drag(pts, frames) { ev("pointerdown", pts[0], 1); for (let i = 1; i < pts.length; i++) for (let k = 1; k <= 12; k++) { ev("pointermove", [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k / 12, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k / 12], 1); if (frames) T.renderMap(1 / 60); } ev("pointerup", pts[pts.length - 1], 0); } }; };
  if (want("sand-writing")) {
    T.goMap(); T.renderMap(1 / 60); for (const A of T.SAND_AREAS) { A.c = null; A.t0 = null; A.wind = null; }
    const ink = (x, y) => { for (const A of T.SAND_AREAS) { if (!A.c || x < A.x0 || y < A.y0 || x >= A.x1 || y >= A.y1) continue; const d = A.c[2].getContext("2d").getImageData(Math.round(x - A.x0) - 3, Math.round(y - A.y0) - 3, 7, 7).data; /* the groove's floor */ let n = 0; for (let i = 3; i < d.length; i += 4) n += d[i] > 20; if (n) return n; } return 0; };
    const f = mapFinger(31), res = [];
    f.drag([[250, 1150], [450, 1180]]); res.push(["a line across the flat sand of Africa", ink(350, 1165) > 0]);
    f.drag([[1300, 880], [1450, 900]]); res.push(["a line across the flat sand of Arabia (Syrian desert)", ink(1375, 890) > 0]);
    f.drag([[540, 1060], [610, 1040]]); res.push(["no line on the Egyptian dunes", ink(575, 1050) === 0]);
    f.drag([[1500, 1060], [1650, 1080]]); res.push(["no line on the Arabian dunes", ink(1575, 1070) === 0]);
    f.drag([[1300, 1035], [1330, 1040]]); res.push(["no line on the Arabian mountains", ink(1315, 1037) === 0]);
    res.push(["Anatolia's plateau is not a writing area", T.sandArea(900, 350) === -1]);
    { // owner 17 Nov: "smooth and able to do curves": a sharp turn of the finger is drawn round, not as a corner
      const one = (x, y) => { const A = T.SAND_AREAS[0], d = A.c[2].getContext("2d").getImageData(Math.round(x - A.x0), Math.round(y - A.y0), 1, 1).data; return d[3] > 20; };
      f.down([380, 1250]); f.move([395, 1265]); f.move([410, 1280]); f.move([425, 1265]); f.move([440, 1250]); f.up([440, 1250]); // a fast V (few touch points): its tip at 410,1280
      res.push(["a sharp turn is drawn as a curve (the tip of the V is rounded off, the line passing just above it: " + [0, 2, 4, 6, 8, 10, 12, 14, 16, 20].filter((d) => one(410, 1280 - d)) + ")", !one(410, 1280) && [2, 4, 6, 8, 10, 12].some((d) => one(410, 1280 - d))]);
      const A = T.SAND_AREAS[0], sh = A.c[1].getContext("2d").getImageData(Math.round(395 - A.x0) - 4, Math.round(1265 - A.y0) - 4, 9, 9).data, lt = A.c[0].getContext("2d").getImageData(Math.round(395 - A.x0) - 4, Math.round(1265 - A.y0) - 4, 9, 9).data;
      res.push(["the groove has a shaded wall and a lit wall", sh.some((v, i) => i % 4 === 3 && v > 20) && lt.some((v, i) => i % 4 === 3 && v > 20)]);
      // owner 17 Nov evening: no lag at the start: the line is under the finger before it has moved far enough to count as a drag
      const scr = (p) => { T.renderMap(0); const q = T.mapView().pt(p[0], p[1]), d = document.querySelector("canvas").getContext("2d").getImageData(Math.round(q.x * devicePixelRatio), Math.round(q.y * devicePixelRatio), 1, 1).data; return [d[0], d[1], d[2]]; };
      const before = scr([352, 1330]); f.down([350, 1330]); f.move([354, 1330]); const during = scr([352, 1330]); f.up([354, 1330]);
      res.push(["the line shows under the finger at once", Math.abs(during[0] - before[0]) + Math.abs(during[1] - before[1]) + Math.abs(during[2] - before[2]) > 40]);
      // a mouse moved along a straight slant: whole screen pixels, each point 1 px off to alternate sides; the groove stays straight
      let A0 = null, B0 = null; // a slant of flat sand away from the earlier lines and the buttons
      for (let y = 1220; y < 1400 && !A0; y += 20) for (let x = 450; x < 900 && !A0; x += 25) { let ok = true; for (let t = 0; t <= 1 && ok; t += 0.02) for (const o of [-10, 0, 10]) ok = ok && T.sandArea(x + 160 * t, y + 50 * t + o) === 0; if (ok) { A0 = [x, y]; B0 = [x + 160, y + 50]; } }
      const v = T.mapView(), qa = v.pt(...A0), qb = v.pt(...B0), cv = document.querySelector("canvas");
      const ev = (type, x, y) => cv.dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, pointerId: 33, isPrimary: true, pointerType: "mouse", button: 0, buttons: type === "pointerup" ? 0 : 1, bubbles: true }));
      const n = Math.ceil(Math.hypot(qb.x - qa.x, qb.y - qa.y) / 3); ev("pointerdown", Math.round(qa.x), Math.round(qa.y));
      for (let k = 1; k <= n; k++) { const t = k / n, sgn = k % 2 ? 1 : -1; ev("pointermove", Math.round(qa.x + (qb.x - qa.x) * t + sgn), Math.round(qa.y + (qb.y - qa.y) * t - sgn)); }
      ev("pointerup", Math.round(qb.x), Math.round(qb.y));
      const L = Math.hypot(B0[0] - A0[0], B0[1] - A0[1]), nx = -(B0[1] - A0[1]) / L, ny = (B0[0] - A0[0]) / L, Ar = T.SAND_AREAS[0], fl = Ar.c[2].getContext("2d");
      let worst = 0, seen = 0; const offs = [];
      for (let t = 0.15; t <= 0.85; t += 0.05) { let sw = 0, so = 0; for (let o = -8; o <= 8; o += 0.5) { const x = A0[0] + (B0[0] - A0[0]) * t + nx * o, y = A0[1] + (B0[1] - A0[1]) * t + ny * o; if (T.sandArea(x, y) < 0) continue; const al = fl.getImageData(Math.round(x - Ar.x0), Math.round(y - Ar.y0), 1, 1).data[3]; sw += al; so += al * o; } if (sw) { seen++; worst = Math.max(worst, Math.abs(so / sw)); offs.push((so / sw).toFixed(1)); } }
      const wob = offs.length ? (Math.max(...offs.map(Number)) - Math.min(...offs.map(Number))) / 2 : 99; // how much it wavers either side of its own straight course
      res.push(["a shaky mouse line (each point 1.4 map px to alternate sides) comes out straight: wavers " + wob.toFixed(2) + " map px either side", seen > 8 && wob < 0.6]);
    }
    f.down([300, 1300]); f.up([300, 1300]); res.push(["a tap on the sand leaves no line", ink(300, 1300) === 0]);
    T.SAND_AREAS[0].t0 -= 121; T.SAND_AREAS[1].t0 -= 100; // Africa's first line two minutes ago, Arabia's 100 seconds ago
    quick(() => { for (let k = 0; k < 480; k++) T.renderMap(1 / 60); });
    res.push(["two minutes after Africa's first line the wind there wiped it", ink(350, 1165) === 0 && !T.SAND_AREAS[0].c]);
    res.push(["the wind blew only in Africa: Arabia's line is still there", ink(1375, 890) > 0]);
    T.SAND_AREAS[1].t0 -= 30; quick(() => { for (let k = 0; k < 480; k++) T.renderMap(1 / 60); });
    res.push(["two minutes after Arabia's first line its wind wiped it", ink(1375, 890) === 0 && !T.SAND_AREAS[1].c]);
    f.drag([[250, 1150], [450, 1180]]); res.push(["after the wind a new line starts a new two minutes", ink(350, 1165) > 0 && T.SAND_AREAS[0].t0 !== null && !T.SAND_AREAS[0].wind]);
    for (const A of T.SAND_AREAS) { A.c = null; A.t0 = null; A.wind = null; }
    const bad = res.filter((r) => !r[1]).map((r) => r[0]);
    out.push(["writing in the sand of Africa and Arabia, wiped by a local wind after two minutes", !bad.length, bad.length ? "failed: " + bad.join("; ") : res.length + " checks right"]);
  }

  // --- owner 17 Nov: "make it so the boats are draggable, and if the kid leaves them on land, then the humans go out,
  // pick up the boat on their shoulders, and carry it to the sea again, and then they go on again and they continue sailing"
  if (want("boat-drag")) quick(() => {
    T.goMap(); T.restartAll(); fleet(); T.renderMap(1 / 60); // a known start: whatever earlier tests left on the map is gone
    const f = mapFinger(32), res = [], cv = document.querySelector("canvas");
    let emptySailing = 0; // owner: no empty boats sailing around, checked every frame below
    const step = (dt = 1 / 60) => { T.active.length = 0; /* no cue holds the screen: these frames skip the cue clock */ T.renderMap(dt); for (const b of T.boats) if (!T.crewOf(b) && !(b.parked || b.stuck || b.held || b.drop || (b.back && b.back.then))) emptySailing++; };
    const pick = (ok) => { for (const b of T.boats) { if (b.wait > 0 || !ok(b)) continue; f.down([b.x, b.y - 5]); if (b.held) return b; f.up([b.x, b.y - 5]); step(); } return null; };
    const landNear = (b, land) => { for (let r = 120; r < 900; r += 20) for (let a = 0; a < 6.28; a += 0.2) { const x = b.x + Math.cos(a) * r, y = b.y + Math.sin(a) * r; let all = T.SITES.every((S) => Math.hypot(S.x - x, S.y - y) > 200); for (let rr = 0; rr <= 40 && all; rr += 8) for (let aa = 0; aa < 6.28 && all; aa += 0.4) all = T.isLand(x + Math.cos(aa) * rr, y + Math.sin(aa) * rr) === land; if (all) return [x, y]; } return null; };
    const drag = (b, to) => { // held (already down on it), moved to `to` frame by frame, let go; what was seen
      const s = { turn: 0, rise: 0, offFinger: 0 }, hd = b.hd, x0 = b.x, y0 = b.y, gy = y0 - (y0 - 5 - y0); // the finger went down 5 px above the boat's middle
      for (let k = 1; k <= 40; k++) { const fp = [x0 + (to[0] - x0) * k / 40, y0 - 5 + (to[1] - y0) * k / 40]; f.move(fp); step(); s.turn = Math.max(s.turn, Math.abs(b.hd - hd)); s.rise = Math.max(s.rise, b.lift || 0);
        s.offFinger = Math.max(s.offFinger, Math.hypot(b.x - (fp[0] + b.held.dx), b.y - b.lift * T.BOAT_LIFT_H - (fp[1] + b.held.dy))); } // the boat as seen stays at the finger
      const still = performance.now(); while (performance.now() - still < 150) { f.move([to[0], to[1] - 5]); step(); } // held still before letting go (longer than the tenth of a second a throw is measured over): put down, not thrown (owner 18 Nov: boats are thrown with the finger's speed)
      s.shadowBelow = b.y - b.held.gy; const shadow = [b.x, b.y]; f.up([to[0], to[1] - 5]);
      let lastLift = 1; s.slowest = 0; for (let k = 0; k < 60 && b.drop; k++) { lastLift = b.lift; const t0 = performance.now(); step(); s.slowest = Math.max(s.slowest, performance.now() - t0); }
      s.lastLift = lastLift; s.landedAtShadow = Math.hypot(b.x - shadow[0], b.y - shadow[1]) < 0.01 && b.lift === 0 && !b.drop; return s;
    };
    const follow = (b, secs, dt = 1 / 20) => { // until it sails its route again, in steps of dt (a boat moves 1 map px in 1/20 s); seconds seen in each part
      const seen = { wait: 0, waitMoved: 0, lift: 0, carry: 0, carryOnWater: 0, lower: 0, sail: 0, jump: 0 }; let px = b.x, py = b.y;
      for (let k = 0; k < secs / dt; k++) {
        step(dt); const W = b.back;
        seen.jump = Math.max(seen.jump, Math.hypot(b.x - px, b.y - py)); if (W && W.delay > 0) { seen.wait += dt; if (Math.hypot(b.x - px, b.y - py) > 0) seen.waitMoved++; } px = b.x; py = b.y;
        if (!W) return { ...seen, back: true, t: k * dt };
        if (W.delay > 0) continue;
        const r = W.runs[Math.min(W.i, W.runs.length - 1)];
        if (W.phase === "lift") seen.lift += dt; else if (W.phase === "lower") seen.lower += dt; else if (r.mode === "carry") { seen.carry += dt; if (!T.isLand(b.x, b.y)) seen.carryOnWater += dt; } else seen.sail += dt;
      }
      return { ...seen, back: false };
    };
    // a boat with its travellers, dragged onto land and left there
    const b1 = pick((b) => T.crewOf(b) && !b.parked);
    if (!b1) res.push(["a boat with travellers can be picked up", false]);
    else {
      T.soundLog.length = 0; const d = drag(b1, landNear(b1, true));
      res.push(["a full boat left on land makes the disappointed sound", T.soundLog.includes("boat-left-on-land")]);
      res.push(["held, it does not turn (" + d.turn.toFixed(4) + " rad)", d.turn === 0]);
      res.push(["held, it stays at the finger and its shadow drops away below it (" + d.offFinger.toFixed(2) + " px off the finger)", d.rise === 1 && d.offFinger < 0.01 && Math.abs(d.shadowBelow - T.BOAT_LIFT_H) < 0.01]);
      res.push(["it falls faster and faster and splashes the moment it reaches the shadow (height a frame before: " + d.lastLift.toFixed(2) + ")", d.lastLift > 0.15]);
      res.push(["let go, it falls onto the point of its shadow", d.landedAtShadow]);
      res.push(["no hitch when it lands with people in it (slowest frame " + d.slowest.toFixed(1) + " ms without drawing; it was 1500 ms)", d.slowest < 30]); // owner 17 Nov: the way back took 1.5 s to find
      const s = follow(b1, 300);
      const want = T.soundSeconds("boat-left-on-land") + 0.5;
      res.push(["left on land: they wait for the sound and half a second more before getting out (" + s.wait.toFixed(2) + " s, sound " + T.soundSeconds("boat-left-on-land").toFixed(2) + " s)", T.soundSeconds("boat-left-on-land") > 1 && Math.abs(s.wait - want) <= 0.06 && s.waitMoved === 0]);
      res.push(["then its travellers lift it, carry it over land, put it down", s.lift >= 0.9 && s.carry > 0 && s.lower >= 0.9 && s.carryOnWater <= 0.25 /* only the step into the water */]);
      res.push(["then it sails back to its route and on", s.back && s.sail > 0 && !!T.crewOf(b1)]);
      res.push(["no jumps on the way (" + s.jump.toFixed(1) + " map px in a frame at most)", s.jump < 1.5]);
    }
    // a boat dropped on the water next to another: the splash's waves push the other one; it sails back, not carried
    let b2 = null, other = null, to2 = null;
    for (const o of T.boats) { if (o.parked || o.wait > 0 || !T.crewOf(o)) continue; for (let a = 0; a < 6.28 && !to2; a += 0.5) { const p = [o.x + Math.cos(a) * 40, o.y + Math.sin(a) * 40]; if (!T.isLand(p[0], p[1]) && !T.isLand(p[0], p[1] - 30)) to2 = p; } if (to2) { other = o; break; } }
    if (other) b2 = pick((b) => b !== other && T.crewOf(b) && !b.parked);
    if (b2) {
      const d = drag(b2, to2); let push = 0, own = 0;
      for (let k = 0; k < 90; k++) { step(); push = Math.max(push, Math.hypot(other.ox, other.oy)); own = Math.max(own, Math.hypot(b2.ox, b2.oy)); }
      res.push(["dropped on the water, it splashes and the waves push the boat next to it (" + push.toFixed(1) + " map px)", d.landedAtShadow && push > 3]);
      res.push(["its own splash does not push it (" + own.toFixed(1) + " map px)", own === 0]); // owner 17 Nov
      const s = follow(b2, 400); res.push(["left on the water: it sails back, nobody carries it", s.back && s.carry === 0 && s.lift === 0]);
      // owner 17 Nov: "the waves dont push the boats anymore": a boat sailing back after being moved (far over the water) is pushed like any other
      for (let k = 0; k < 900 && T.boats.some((o) => o !== b2 && Math.hypot(o.x - b2.x, o.y - b2.y) < 60); k++) step(); // a finger on it takes it, not a boat lying over it
      f.down([b2.x, b2.y - 5]); drag(b2, landNear(b2, false)); const wasBack = !!b2.back, q = T.mapView().pt(b2.x, b2.y), cv = document.querySelector("canvas");
      for (const t of ["pointerdown", "pointerup"]) cv.dispatchEvent(new PointerEvent(t, { clientX: q.x - 30, clientY: q.y, pointerId: 34, isPrimary: true, pointerType: "mouse", button: 0, buttons: t === "pointerup" ? 0 : 1, bubbles: true }));
      let wp = 0; for (let k = 0; k < 90; k++) { step(); wp = Math.max(wp, Math.hypot(b2.ox, b2.oy)); }
      res.push(["a boat sailing back after being moved is pushed by waves too (" + wp.toFixed(1) + " map px)", wasBack && wp > 3]);
    } else res.push(["a boat to drop next to another", false]);
    // an empty boat: waiting where its travellers got off; moved onto land, they come for it when their round is done.
    // Set up directly: a boat with its travellers a moment before a port (all sites finished, so they get off there).
    const park = (b) => { const g = T.crewOf(b); b.wait = 0; b.dir = 1; b.d = b.lens[b.leg] - 0.5; g.recent = []; for (let k = 0; k < 900 && !b.parked; k++) { g.stops = 1; g.onFoot = 2; step(k < 60 ? 1 / 60 : 0.2); } return b.parked ? g : null; }; // on to the next port where they can walk to a site
    const under = (p) => { const q = T.mapView().pt(p[0], p[1] - 5); const sb = T.screenButtons().find((x) => x.r ? Math.hypot(q.x - x.x, q.y - x.y) <= x.r : x.rect && q.x >= x.rect.x && q.x <= x.rect.x + x.rect.w && q.y >= x.rect.y && q.y <= x.rect.y + x.rect.h); return sb ? sb.id : null; };
    let b3 = null, g3 = null; const why = [];
    for (const b of T.boats) { if (b === b1 || b === b2 || !T.crewOf(b) || b.back) continue; const g = park(b); if (!g) { why.push(T.boats.indexOf(b) + ": did not stop"); continue; } f.down([b.x, b.y - 5]); if (b.held) { b3 = b; g3 = g; break; } const other = T.boats.find((x) => x.held); why.push(T.boats.indexOf(b) + ": not held, " + (other ? "boat " + T.boats.indexOf(other) + " (in the same port) was held instead" : "under " + under([b.x, b.y]))); f.up([b.x, b.y - 5]); }
    if (!b3) res.push(["an empty waiting boat can be picked up (" + why.join("; ") + ")", false]);
    else {
      const at = [b3.x, b3.y]; f.up([b3.x, b3.y - 5]); for (let k = 0; k < 40; k++) step(0.2); // the tap's own waves rock it; then it is back
      res.push(["it waits empty where they got off", Math.hypot(b3.x - at[0], b3.y - at[1]) < 0.5 && !T.crewOf(b3) && b3.parked]);
      T.soundLog.length = 0; f.down([b3.x, b3.y - 5]); const d = drag(b3, landNear(b3, true)), left = [b3.x, b3.y];
      res.push(["an empty boat left on land makes no disappointed sound", !T.soundLog.includes("boat-left-on-land")]);
      for (let k = 0; k < 10; k++) step(0.2);
      res.push(["moved onto land, the empty boat stays there", d.landedAtShadow && b3.stuck && Math.hypot(b3.x - left[0], b3.y - left[1]) < 0.01]);
      let fetched = false, carried = false;
      for (let k = 0; k < 3000 && !(fetched && T.crewOf(b3) && !b3.back); k++) { step(0.2); if (g3.state === "walk" && g3.then.fetch) fetched = true; if (b3.back && b3.back.runs.some((r) => r.mode === "carry")) carried = true; }
      res.push(["when their round is done they walk to it, carry it to the sea and sail on (" + g3.state + ")", fetched && carried && !b3.back && T.crewOf(b3) === g3 && !b3.stuck]);
    }
    // another: back from their round, they get in their boat where they left it
    const b4 = T.boats.find((b) => b !== b1 && b !== b2 && b !== b3 && b.parked && !b.stuck) || T.boats.find((b) => b !== b1 && b !== b2 && b !== b3 && T.crewOf(b) && !b.back); let boarded = false;
    let info = b4 ? "" : "no boat";
    if (b4) { const g4 = b4.parked ? T.groups[T.boats.indexOf(b4)] : park(b4); if (!g4) info = "did not stop"; else { const spot = [b4.x, b4.y]; let k = 0; for (; k < 3000 && !T.crewOf(b4); k++) step(0.2); boarded = !!T.crewOf(b4) && Math.hypot(b4.x - spot[0], b4.y - spot[1]) < 0.5; info = `after ${(k * 0.2).toFixed(0)} s: ${g4.state} ${g4.then ? JSON.stringify(g4.then) : ""}, ${Math.hypot(b4.x - spot[0], b4.y - spot[1]).toFixed(1)} px from where they left it`; } }
    res.push(["back from their round, they get in their boat where they left it (" + info + ")", boarded]);
    res.push(["no empty boat ever sailed (" + emptySailing + " frames)", emptySailing === 0]);
    const bad = res.filter((r) => !r[1]).map((r) => r[0]);
    out.push(["boats: held without turning over a shadow, dropped with a splash, carried after a sound; empty boats wait", !bad.length, bad.length ? "failed: " + bad.join("; ") : res.length + " checks right"]);
  });

  // --- owner 17 Nov: "each site that is finished makes a boat full of people appear ... game starts with 0 boats"
  if (want("fleet")) quick(() => {
    T.goMap(); T.restartAll(); T.renderMap(1 / 60); const res = [["no boats at the start", T.boats.length === 0]];
    T.progress.done[T.SITES[0].key] = { pieces: [], loads: [] }; T.renderMap(1 / 60);
    res.push(["one finished site: one boat, full of people", T.boats.length === 1 && T.crewOf(T.boats[0]) === T.groups[0]]);
    T.progress.done[T.SITES[1].key] = { pieces: [], loads: [] }; T.renderMap(1 / 60);
    res.push(["two finished sites: two boats", T.boats.length === 2 && !!T.crewOf(T.boats[1])]);
    T.restartAll(); T.renderMap(1 / 60); res.push(["restart: none again", T.boats.length === 0]);
    const bad = res.filter((r) => !r[1]).map((r) => r[0]);
    out.push(["a boat full of people for each finished site, none at the start", !bad.length, bad.length ? "failed: " + bad.join("; ") : res.length + " checks right"]);
  })

  // --- owner 17 Nov: waves push a boat equally hard from every side (a tap the same screen distance beside, above or below it)
  if (want("wave-even")) quick(() => {
    T.goMap(); T.restartAll(); fleet(); T.renderMap(1 / 60); const cv = document.querySelector("canvas"), got = [];
    const b = T.boats.find((x) => T.crewOf(x) && !x.parked && x.wait <= 0);
    for (const [dx, dy] of [[25, 0], [-25, 0], [0, 25], [0, -25], [45, 0], [0, -45]]) {
      for (let k = 0; k < 360; k++) T.renderMap(1 / 60); // settled back on its route
      b.wait = 1000; const q = T.mapView().pt(b.x, b.y); // resting in port: it stays where it is while the wave passes
      for (const t of ["pointerdown", "pointerup"]) cv.dispatchEvent(new PointerEvent(t, { clientX: q.x + dx, clientY: q.y + dy, pointerId: 35, isPrimary: true, pointerType: "mouse", button: 0, buttons: t === "pointerup" ? 0 : 1, bubbles: true }));
      let m = 0; for (let k = 0; k < 120; k++) { T.renderMap(1 / 60); m = Math.max(m, Math.hypot(b.ox, b.oy)); } got.push(m);
    }
    const near = got.slice(0, 4), far = [got[4], got[5]], even = (a) => Math.max(...a) <= Math.min(...a) * 1.1 && Math.min(...a) > 3;
    out.push(["waves push a boat equally from every side", even(near) && even(far), "25 px right, left, below, above: " + near.map((x) => x.toFixed(1)).join(", ") + "; 45 px right, above: " + far.map((x) => x.toFixed(1)).join(", ")]);
  });

  // --- 1: the restart button on the map: everything as at the very beginning
  if (want("restart")) {
    T.mode = "map"; T.renderMap(0.016);
    const b = T.restartButton ? T.restartButton() : null;
    out.push(["1 restart button on the map", !!b, b ? JSON.stringify({ x: Math.round(b.x), y: Math.round(b.y), size: Math.round(b.size) }) : "none"]);
  }
  return out;
}
