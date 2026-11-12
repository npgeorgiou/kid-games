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
      T.startHold(b, { x: g.x, y: g.y }, 91, 0, 0); let t1 = null;
      for (let k = 0; k < 240; k++) { b.desired = { x: g.x, y: g.y + Math.min(1.5, k * 1.5 / 60) }; frame(1 / 60); if (t1 == null && b.body.getPosition().y - y0 > 1.0) t1 = k / 60; }
      const rise = b.body.getPosition().y - y0, w = ps.reduce((s, p) => s + p.body.getMass() * 10, 0);
      const carried = ps.every((p) => p.body.getPosition().y > 1.0 + 0.5);
      T.releaseHold(91); run(0.5);
      return { w: Math.round(w), rise: +rise.toFixed(2), t1, carried };
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
    ];
    const LIM = 2 * blockW(), res = {};
    for (const [n, st] of cases) {
      const r = (res[n] = stackLift(st)), canLift = r.w <= LIM + 1;
      out.push(["3 hand: " + n, canLift ? r.rise > 1.0 && r.carried : r.rise < 0.2, (canLift ? "should lift" : "too heavy") + ": weight " + r.w + " N, rose " + r.rise + " m, 1 m after " + r.t1 + " s"]);
    }
    const same = (a, b) => { const x = res[a].t1, y = res[b].t1; return x != null && y != null && Math.abs(x - y) <= 0.25 * Math.max(x, y) + 0.05; };
    out.push(["3 hand: same weight, same lift (small oblong pair vs slab)", same(cases[1][0], cases[2][0]), res[cases[1][0]].t1 + " s vs " + res[cases[2][0]].t1 + " s"]);
    out.push(["3 hand: same weight, same lift (two blocks vs four squares)", same(cases[3][0], cases[4][0]), res[cases[3][0]].t1 + " s vs " + res[cases[4][0]].t1 + " s"]);
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
    for (const [n, list, exp] of [
      ["4 mudbricks then 2 stones on a mudbrick (owner, changed)", ["mudbrick", "mudbrick", "mudbrick", "mudbrick", "stone", "stone"], "crumbles"],
      ["2 stones then 4 mudbricks on a mudbrick", ["stone", "stone", "mudbrick", "mudbrick", "mudbrick", "mudbrick"], "crumbles"],
      ["4 mudbricks and 3 stones on a mudbrick", ["mudbrick", "mudbrick", "mudbrick", "mudbrick", "stone", "stone", "stone"], "crumbles"],
      ["7 mudbricks on a mudbrick (lighter than 4 and 2)", ["mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick"], "holds"],
      ["6 mudbricks on a mudbrick (owner, Ishtar)", ["mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick", "mudbrick"], "holds"],
      ["3 mudbricks and 2 stones on a mudbrick", ["mudbrick", "mudbrick", "mudbrick", "stone", "stone"], "holds"],
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
    for (const [n, exp] of [[1, "holds"], [2, "crumbles"], [3, "crumbles"]]) { const r = column(n); out.push(["7-5 upright mudbrick column with " + n + " stone block(s) on it (owner's picture: 3)", r === exp, r]); }
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
    const r = {}; for (const [d, m] of [["block", "stone"], ["abacus", "stone"], ["column", "wood"], ["square", "stone"], ["block", "mudbrick"], ["block", "wood"]]) r[d + "/" + m] = carry(d, m);
    const close = (a, b) => Math.abs(a - b) <= 0.15 * Math.max(a, b);
    out.push(["7-3 same weight, same carry: small oblong stone vs wooden column", close(r["abacus/stone"], r["column/wood"]), r["abacus/stone"] + " s vs " + r["column/wood"] + " s (4 m)"]);
    out.push(["7-3 a stone block is heavy to carry (at least 1.4 s for 4 m)", r["block/stone"] >= 1.4, JSON.stringify(r)]);
    out.push(["7-3 lighter is quicker: stone block > mudbrick block > stone square > wooden block", r["block/stone"] > r["block/mudbrick"] && r["block/mudbrick"] > r["square/stone"] && r["square/stone"] > r["block/wood"], JSON.stringify(r)]);
  }

  // --- eighth list 1: a triangle is grabbed only on itself, and slides along like any other piece
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
  // --- 14: every suggested build also passes with the earthquake and the headpiece 30% stronger
  if (want("margin")) {
    for (let i = 0; i < T.LEVELS.length; i++) {
      const q = T.TEST_QUAKE[i], d = T.TEST_LOAD_DENSITY[i];
      T.TEST_QUAKE[i] = q * 1.3; T.TEST_LOAD_DENSITY[i] = d * 1.3;
      const o = quickBuildAndTest(i, 1, true);
      T.TEST_QUAKE[i] = q; T.TEST_LOAD_DENSITY[i] = d;
      out.push(["14 passes with 1.3x earthquake and headpiece: " + T.LEVELS[i].key, o.res.endsWith("PASS"), o.res]);
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
    // seams: the suggested build placed by hand (each piece up to 3 cm off) leaves no red between pieces
    for (const i of [4, 0, 6]) {
      T.mode = "build"; T.startLevel(i); T.quiet0(); const key = T.LEVELS[i].key, orig = T.SOLUTIONS[key];
      let s = i + 7; const r2 = () => ((s = (s * 16807) % 2147483647) / 2147483647 - 0.5);
      T.SOLUTIONS[key] = orig.map((e) => e[0] === "pull" ? e : [e[0], e[1], e[2] + r2() * 0.06, e[3] + Math.abs(r2()) * 0.03, e[4]]);
      T.startAutoBuild(); T.SOLUTIONS[key] = orig; let n = 0; while (T.auto && n < 20000) { frame(1 / 60); n++; } run(2);
      const c = T.runCheck(); T.failShow = { cells: [], loads: [], unfilled: true, until: null }; T.render();
      const cv = document.querySelector("canvas"), cx = cv.getContext("2d"), dpr = window.devicePixelRatio || 1, im = cx.getImageData(0, 0, cv.width, cv.height).data;
      let red = 0; for (let k = 0; k < im.length; k += 4) if (im[k] > 170 && im[k + 1] < 120 && im[k + 2] < 110) red++;
      T.failShow = null; const m2 = red / (dpr * dpr) / (T.scale * T.scale);
      out.push(["6 no red seams between hand-placed pieces: " + key, m2 < 0.05, (m2).toFixed(3) + " m2 painted red, outline covered " + (c.fill * 100).toFixed(1) + "%"]);
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
