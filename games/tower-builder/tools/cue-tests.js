// Cue tests (owner, 15 Nov 2026): every cue rule as a pass/fail check that repeats what the child does.
// Run: python3 tools/harness.py cuetest [names]. Each test starts from a fresh game (no saved progress) and runs game time
// in fixed 1/60 s ticks, so the same run gives the same result. Lines are logged as [start s, line, end s].
(() => {
  const T = __tb;
  let clock = 0, log = [];
  const run = (sec, physics = true) => {
    for (let k = 0; k < Math.round(sec * 60); k++) {
      const c0 = T.voice.cur; T.cueTick(1 / 60); clock += 1 / 60; const c = T.voice.cur;
      if (c0 && c0 !== c) { const e = log.slice().reverse().find((q) => q[1] === c0.n && q[2] == null); if (e) e[2] = clock; }
      if (c && c !== c0) log.push([clock, c.n, null]);
      if (physics && T.mode === "build" && !T.frozen()) { const f = T.test && T.test.fast && T.test.phase !== "fail" && T.test.phase !== "pass" ? 10 : 1; T.stepPhysics(f / 60, 8 * f); T.cleanupOutOfBounds(); T.updateCheck(1 / 60); }
    }
  };
  const said = () => log.map((q) => q[1]);
  const cur = () => T.voice.cur && T.voice.cur.n;
  const seq = () => T.cueMem().seq["first-site"];
  const fresh = () => { T.setTab(false); T.goMap(); T.pieces.slice().forEach(T.removePiece); T.progress.done = {}; T.cueReset(); T.goMap(); log = []; };
  const noTeach = () => { T.cueMem().seq["first-site"] = "done"; T.cueMem().ever["welcome-first"] = 1; };
  const start = (i) => { T.startLevel(i); T.render(); }; // the real game lays the screen out when it draws
  const lvl = (k) => T.LEVELS.findIndex((L) => L.key === k);
  const put = (x, y = 0.5, m = "mudbrick") => { const p = T.spawnPiece("block", x + T.LEVEL_X0, y, 0, m); T.cueEvent("placed-in-plan"); return p; };
  const clear = () => T.pieces.filter((p) => !p.demo).slice().forEach(T.removePiece);
  const glowsOn = (btn) => T.active.some((s) => (s.targets || []).some((t) => t.btn === btn));
  const pixel = (x, y) => { if (T.mode === "map") T.renderMap(0); else T.render(); T.drawCues(); const d = document.querySelector("canvas").getContext("2d").getImageData(Math.round(x), Math.round(y), 1, 1).data; return [d[0], d[1], d[2]]; };
  const rgb = (h) => h.startsWith("#") ? [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)) : h.split(",").map(Number);
  const near = (a, b, d) => a.every((v, i) => Math.abs(v - b[i]) <= d);
  // the child's own hand: pointer events on the game's canvas, moved in small steps while the game runs (about 0.6 s per drag)
  const cv = () => document.querySelector("canvas");
  const ptr = (type, x, y) => cv().dispatchEvent(new PointerEvent(type, { clientX: x, clientY: y, pointerId: 1, isPrimary: true, pointerType: "mouse", button: 0, buttons: type === "pointerup" ? 0 : 1, bubbles: true }));
  const drag = (a, b, sec = 0.6) => { ptr("pointerdown", a.x, a.y); run(0.05); for (let k = 1; k <= 20; k++) { ptr("pointermove", a.x + ((b.x - a.x) * k) / 20, a.y + ((b.y - a.y) * k) / 20); run(sec / 20); } ptr("pointerup", b.x, b.y); run(0.1); };
  const tap = (a) => { ptr("pointerdown", a.x, a.y); ptr("pointerup", a.x, a.y); run(0.1); };
  const pileAt = (m) => { const b = T.pileBodies().filter((q) => q.pileItem.material === m && q.pileItem.defKey === "block").sort((u, v) => u.getLinearVelocity().length() - v.getLinearVelocity().length())[0], q = b.getPosition(), r = T.pileBinRect; return { x: r.x + q.x * T.pileScale, y: r.y + r.h - q.y * T.pileScale }; };
  const planAt = (x = 0, y = 0.6) => T.worldToScreen(T.LEVEL_X0 + x, y);
  const pieceAt = (p) => { const q = p.body.getPosition(); return T.worldToScreen(q.x, q.y); };
  const sideAt = () => ({ x: T.buildingWidthPx + 60, y: 300 });
  const btn = (id) => T.screenButtons().find((b) => b.id === id);

  const tests = {
    // the table names only what the code knows
    "table": () => { const bad = T.cueCheckTable(); return [!bad.length, bad.join(", ")]; },

    // first launch: the first welcome, then the press-here step; a return: the short welcome only
    "order-first-launch": () => { fresh(); T.mapStart(); run(6, false); const s = said(); return [s[0] === 11 && s[1] === 92 && !s.includes(12), s.join(",")]; },
    "order-return": () => { fresh(); T.cueMem().ever["welcome-first"] = 1; T.progress.done.mastaba = { pieces: [] }; T.mapStart(); run(3, false); const s = said(); return [s[0] === 12 && !s.includes(11), s.join(",")]; },

    // list 15 Nov, 4: no second button; the restart's line says «πάτα το διπλά»; a second press within its time erases, a late one does not
    "restart-press-twice": () => {
      fresh(); noTeach(); T.progress.done.mastaba = { pieces: [] }; T.mapStart(); run(3, false);
      const n0 = T.screenButtons().length; T.restartPress(); run(0.1, false);
      const text = T.CUE_TABLE.lines[cur()] || "", one = T.screenButtons().length === n0 && !btn("restart-confirm") && /πάτα το διπλά\.$/.test(text) && !!T.progress.done.mastaba;
      run(7, false); T.restartPress(); run(0.1, false); const late = !!T.progress.done.mastaba;
      run(1, false); T.restartPress(); run(0.1, false); const erased = !T.progress.done.mastaba;
      return [one && late && erased, `one button ${one}, late press keeps ${late}, quick second press erases ${erased}`];
    },

    // list 15 Nov, 5: the textures button's stone is grey; each plain colour is close to its texture's colour; marble levels draw stone in marble
    "texture-button-colours": () => {
      const grey = T.TEX_BUTTON[0][0] === "silver-sandstone", far = T.TEX_BUTTON.filter(([k, m]) => !near(rgb(T.TEX_RGB[k]), rgb(T.PLAIN[m]), 45)).map((b) => b[0]);
      return [grey && !far.length, `stone ${T.TEX_BUTTON[0][0]}, plain far from texture: ${far.join(",") || "none"}`];
    },
    "marble-plain-stone": () => {
      const out = [];
      for (const k of ["parthenon", "liongate"]) {
        fresh(); start(lvl(k)); T.newScene(); clear(); const p = T.spawnPiece("block", T.LEVEL_X0, 4, 0, "stone");
        const q = T.worldToScreen(p.body.getPosition().x, p.body.getPosition().y); out.push([k, pixel(q.x, q.y)]);
      }
      const ok = near(out[0][1], rgb(T.PLAIN.marble), 12) && near(out[1][1], rgb(T.PLAIN.stone), 12);
      return [ok, out.map(([k, c]) => k + " " + c.join("/")).join(", ")];
    },

    // list 15 Nov, 1 and 2: the Mausoleum pile has no long mudbrick; Karnak keeps its tall mudbrick column
    "mudbrick-long-pieces": () => {
      const longMud = (k) => { fresh(); start(lvl(k)); return T.pileBodies().filter((b) => b.pileItem.material === "mudbrick" && ["column", "beam", "longplank"].includes(b.pileItem.defKey)).map((b) => b.pileItem.defKey); };
      const m = longMud("mausoleum"), k = longMud("karnak");
      return [!m.length && k.includes("column"), `Mausoleum: ${m.join(",") || "none"}; Karnak: ${k.join(",") || "none"}`];
    },

    // list 15 Nov, 3a and 12: no "wood goes here" line at Ur, nothing in the pile glows when a site starts
    "no-start-glows": () => {
      fresh(); noTeach(); const i = lvl("ziggurat"); T.progress.done.ziggurat = { pieces: [] };
      start(i); T.onEnterSite(i); T.progress.done = {}; T.cueEvent("plan-shown"); run(1, false);
      const pile = T.active.some((s) => (s.targets || []).some((t) => t.pile || t.rings)), uses108 = T.CUE_TABLE.cues.some((c) => c.say === 108);
      return [!pile && !uses108 && !said().includes(108), `pile or plan glow ${pile}, line 108 in table ${uses108}`];
    },

    // list 15 Nov, 6-9 and 15 Nov evening, 7: the first site's teaching, done with the child's own drags and taps
    "first-site-teaching": () => {
      const bad = [], step = (want, why) => { if (seq() !== want) bad.push(why + ": step " + seq() + " (want " + want + ")"); };
      const kids = () => T.pieces.filter((p) => !p.demo && !p.auto);
      fresh(); start(0); T.onEnterSite(0); run(3); step("t-drag-1", "after the welcome");
      // 9: a piece let go high up that breaks on landing does not count
      const p0 = put(0, 4); run(0.1); step("t-drag-1", "piece still falling"); T.removePiece(p0); run(8);
      if (said().includes(94)) bad.push("94 said for a piece that broke");
      drag(pileAt("mudbrick"), planAt()); run(1.5); step("t-tap3", "mudbrick dragged into the plan");
      const k1 = kids()[0]; if (k1) { const at = pieceAt(k1); tap(at); tap(at); tap(at); } run(3);
      const s7 = said(), i94 = s7.lastIndexOf(94); if (s7[i94 + 1] !== 132) bad.push("after 94 came " + s7[i94 + 1] + " not 132"); // 7
      step("t-drag-2", "after the three taps");
      drag(pileAt("mudbrick"), planAt()); run(1.5); step("t-dragback", "mudbrick in again (" + kids().map((p) => { const q = p.body.getPosition(), v = p.body.getLinearVelocity(); return [q.x.toFixed(2), q.y.toFixed(2), v.y.toFixed(3), p.heldBy, T.worldToScreen(q.x, 0).x | 0, T.buildingWidthPx | 0].join("/"); }).join(" ") + ")"); // 8
      const g = T.active.find((q) => q.n === 134 && q.act); if (!g || !g.act.drag) bad.push("no ghost drag for the drag-back");
      const k2 = kids()[0]; if (k2) drag(pieceAt(k2), sideAt()); run(3);
      step("t-drag-3", "dragged back to the pile by hand");
      run(8); step("t-drag-3", "8 s later (no going round again)");
      drag(pileAt("mudbrick"), planAt()); run(1.5); step("t-shovel", "piece for the shovel");
      // 6: the first-time mudbrick line never during the teaching (each drag above picked a mudbrick up)
      T.cueEvent("press-broom"); T.clearAllPieces(); for (let k = 0; k < 300 && (T.demo || k < 4); k++) run(0.5);
      drag(pileAt("mudbrick"), planAt(-1)); drag(pileAt("mudbrick"), planAt(1)); run(2); step("t-red", "two pieces in");
      if (said().includes(78)) bad.push("78 said during the teaching");
      T.startTest(); run(0.3); step("t-green", "red button pressed");
      T.cueMem().seq["first-site"] = "done"; T.newScene(); drag(pileAt("mudbrick"), planAt(2)); run(4);
      if (!said().includes(78)) bad.push("78 not said after the teaching");
      return [!bad.length, bad.join("; ") || said().join(",")];
    },

    // 15 Nov evening, 2: the boat, the visitors and the other flavour lines play on the map only, never on a site
    "flavour-only-on-map": () => {
      fresh(); noTeach(); T.progress.done.mastaba = { pieces: [] }; start(lvl("djoser")); T.newScene(); log = []; run(130);
      const idle = T.CUE_TABLE.groups.idle.lines, onSite = said().filter((n) => idle.includes(n));
      return [!onSite.length, "on a site: " + (onSite.join(",") || "none")];
    },

    // 15 Nov evening, 3: the Pharos outline shows where the wood goes, and the button stays red without it
    "pharos-wood-places": () => { fresh(); start(lvl("pharos")); return [T.grid.wood.length > 0 && T.grid.L.woodRole === "courses", T.grid.wood.length + " wood places"]; },

    // list 15 Nov, 10: the darkening never covers what a step points at (the map button, the plan)
    "darkening-spares-target": () => {
      const bad = [];
      fresh(); noTeach(); start(0); T.newScene(); T.cueEvent("first-win-said"); run(0.2, false);
      const h = btn("home"), a = pixel(h.x, h.y), far = pixel(200, 200); T.newScene(); run(0.1, false); const b = pixel(h.x, h.y), farB = pixel(200, 200);
      const lit = (u, v) => u[0] + u[1] + u[2] >= 0.85 * (v[0] + v[1] + v[2]); // not darkened (the darkening halves it; a glow only tints it)
      if (!lit(a, b)) bad.push("map button darkened " + a + " vs " + b); if (lit(far, farB)) bad.push("rest not darkened");
      fresh(); start(0); T.onEnterSite(0); run(3, false); const r = T.grid.solid[0], c = T.worldToScreen((r[0][0] + r[2][0]) / 2, 0.3);
      const pa = pixel(c.x, c.y); T.newScene(); run(0.1, false); const pb = pixel(c.x, c.y);
      if (!lit(pa, pb)) bad.push("plan darkened " + pa + " vs " + pb);
      return [!bad.length, bad.join("; ")];
    },

    // list 15 Nov, 13 and 19: after a win, the new site's line 2 s after the win line, with its glow; again on every return from the site before
    "map-new-site": () => {
      const bad = []; fresh(); noTeach(); T.cueMem().ever["map-new-site-first"] = 1;
      for (const k of ["mastaba", "djoser"]) T.progress.done[k] = { pieces: [] };
      start(lvl("ziggurat")); T.newScene(); T.setTab(true); T.startAutoBuild(); run(14); T.startTest(); for (let k = 0; k < 80 && !T.progress.done.ziggurat; k++) run(0.5); T.setTab(false); run(3);
      if (!T.progress.done.ziggurat) return [false, "Ur quick build did not pass its test"];
      log = []; T.goMap(); run(12, false);
      const w = log.find((q) => q[1] === 26), n = log.find((q) => [34, 35, 36, 37].includes(q[1]));
      if (!w || !n) bad.push("lines " + said().join(","));
      else if (n[0] - w[2] < 1.95 || n[0] - w[2] > 2.3) bad.push("gap " + (n[0] - w[2]).toFixed(2) + " s");
      log = []; start(lvl("ziggurat")); T.goMap(); run(0.5, false); const again = [34, 35, 36, 37].includes(cur()), glow = glowsOn("site:liongate");
      if (!again || !glow) bad.push("return from Ur: line " + cur() + ", Lion Gate glows " + glow);
      run(6, false); log = []; start(lvl("djoser")); T.goMap(); run(6, false);
      if (said().some((x) => [34, 35, 36, 37].includes(x))) bad.push("new-site line after leaving Djoser");
      return [!bad.length, bad.join("; ")];
    },
    "map-next-glow-every-60s": () => {
      fresh(); noTeach(); T.progress.done.mastaba = { pieces: [] }; T.mapStart(); run(5, false); log = [];
      const at = []; let was = false; for (let k = 0; k < 125 * 4; k++) { run(0.25, false); const g = T.active.some((s) => s.n == null && (s.targets || []).some((t) => t.btn === "site:djoser")); if (g && !was) at.push(+clock.toFixed(1)); was = g; }
      const gaps = at.slice(1).map((t, i) => t - at[i]), voiced = said().some((x) => [34, 35, 36, 37].includes(x));
      return [at.length >= 2 && gaps.every((g) => Math.abs(g - 60) < 0.5) && !voiced, `glows at ${at.join(", ")}; new-site voice ${voiced}`];
    },

    // list 15 Nov, 14a: a flavour line on the map after every 30 s of quiet
    "map-flavour-every-30s": () => {
      fresh(); noTeach(); T.progress.done.mastaba = { pieces: [] }; T.mapStart(); run(5, false); log = [];
      run(100, false); const idle = T.CUE_TABLE.groups.idle.lines, f = log.filter((q) => idle.includes(q[1]));
      const gaps = f.slice(1).map((q, i) => q[0] - f[i][2]);
      return [f.length >= 2 && gaps.every((g) => Math.abs(g - 30) < 0.3), `${f.length} lines, quiet before each ${gaps.map((g) => g.toFixed(1)).join(", ")} s`];
    },

    // list 15 Nov, 14b: the load part fails only because the headpiece did not sit well: line 133, not 75 (the real test)
    "headpiece-line": () => {
      fresh(); noTeach(); T.cueMem().ever["fail-load-first"] = 1; T.cueMem().ever["explain-wind"] = 1; start(0); T.newScene();
      T.setTab(true); T.startAutoBuild(); run(10); T.setTab(false); log = []; T.setTab(true); T.startTest(); T.setTab(false);
      for (let k = 0; k < 600 && T.test && T.test.phase !== "load"; k++) run(0.1);
      for (let k = 0; k < 200 && T.test && T.test.phase === "load"; k++) { run(0.05); for (const l of T.loads) l.body.setPosition({ x: l.body.getPosition().x + 0.3, y: l.body.getPosition().y }); }
      run(6); const s = said();
      return [s.includes(133) && !s.includes(75), "lines " + s.join(",") + ", phase " + (T.test && T.test.phase)];
    },

    // list 15 Nov, 15: a crumble during the test says nothing later, after the reset
    "no-building-lines-from-test": () => {
      fresh(); noTeach(); start(0); T.newScene(); const p = put(0); run(0.5); T.cueEvent("crumble", { piece: p }); // one just before the test, one in it
      T.setTab(true); T.startTest(); T.setTab(false); const started = !!T.test; T.cueEvent("crumble", { piece: p }); T.cueEvent("snap", { piece: p });
      const q = T.voice.queue.map((c) => c.n); T.goMap(); start(0); T.newScene(); run(5);
      return [!q.includes(72) && !q.includes(73) && !said().includes(72), "test running " + started + ", queued in the test " + q.join(",") + "; said after " + said().join(",")];
    },

    // list 15 Nov, 16: each site's welcome names every material and every kind of stone met there for the first time
    "intros-name-new-materials": () => {
      const word = { mudbrick: /πλίνθ/, wood: /ξύλ/, sandstone: /πέτρα/, "silver-sandstone": /γκρίζα πέτρα/, marble: /μάρμαρο/ }, seen = new Set(), bad = [];
      const stone = { mastaba: "sandstone", djoser: "sandstone", ziggurat: "sandstone", liongate: "silver-sandstone", karnak: "sandstone", ishtar: "sandstone", parthenon: "marble", mausoleum: "marble", pharos: "marble", valens: "silver-sandstone" };
      T.LEVELS.forEach((L, i) => {
        fresh(); start(i); const mats = new Set(T.pileBodies().map((b) => b.pileItem.material).concat(T.SOLUTIONS[L.key].map((e) => e[1])).filter(Boolean));
        const kinds = [...mats].map((m) => (m === "stone" ? stone[L.key] : m)), text = T.CUE_TABLE.lines[i + 1];
        for (const k of kinds) if (!seen.has(k)) { seen.add(k); if (!word[k].test(text)) bad.push(L.key + ": " + k); }
      });
      return [!bad.length, bad.join(", ")];
    },

    // list 15 Nov, 17: «καμαρόπετρες», never «σφήνες»
    "words-arch-stones": () => { const b = Object.entries(T.CUE_TABLE.lines).filter(([, t]) => /σφήν/i.test(t)).map(([n]) => n); return [!b.length, b.join(",")]; },

    // list 15 Nov, 3b, 11, 18, 20, 21: demos (wrong then right with the same load; supports out by three taps; Valens none)
    "demos": () => {
      const bad = [], D = T.CUE_TABLE.demos;
      if (D.valens.steps.length) bad.push("Valens has a demo");
      for (const k of ["djoser", "ziggurat", "mausoleum", "ishtar", "karnak", "mastaba"]) {
        if (!D[k].steps.length) continue;
        fresh(); noTeach(); const i = lvl(k); start(i); T.onEnterSite(i); for (let n = 0; n < 60 && !T.demo; n++) run(0.1);
        const rows = []; let carriedOut = false, tapped = false, through = 0, carried = 0, wasFade = false, curP = null;
        const removeOrig = T.removePiece;
        for (let n = 0; n < 60 * 240 && T.demo; n++) {
          const c0 = T.voice.cur, nd = T.pieces.filter((p) => p.demo).length; run(1 / 60);
          if (T.demo && T.demo.cur && T.demo.cur.out) carriedOut = true; if (T.demo && T.demo.tap) tapped = true;
          const cp = T.demo && T.demo.cur && T.demo.cur.piece; if (cp && cp !== curP) carried++; curP = cp;
          const c = T.demo && T.demo.cur, far = c && Math.hypot(c.tx - cp.body.getPosition().x, c.ty - cp.body.getPosition().y) > 0.3; // on the way, not settling into its place
          if (cp && far) { // points well inside the carried piece (its corners pulled a quarter of the way to its centre) inside another piece: passing through, not touching
            const b = cp.body, c0 = b.getWorldCenter(), pts = [c0];
            for (let f = b.getFixtureList(); f; f = f.getNext()) for (const v of (f.getShape().m_vertices || [])) { const w = b.getWorldPoint(v); pts.push({ x: w.x + (c0.x - w.x) * 0.25, y: w.y + (c0.y - w.y) * 0.25 }); }
            for (const o of T.pieces.filter((p) => p.demo && p !== cp)) for (let g = o.body.getFixtureList(); g; g = g.getNext()) if (pts.some((q) => g.testPoint(planck.Vec2(q.x, q.y)))) through++;
          }
          const fading = !!(T.demo && T.demo.ops[0] && T.demo.ops[0][0] === "fade");
          if (fading && !wasFade) { const ps = T.pieces.filter((p) => p.demo && p.placedY != null); rows.push({ mud: ps.filter((p) => p.material === "mudbrick").length, wood: ps.filter((p) => p.material === "wood").length, fell: Math.max(0, ...ps.filter((p) => p.defKey === "beam").map((p) => p.placedY - p.body.getPosition().y)) }); }
          wasFade = fading;
        }
        if (T.demo) bad.push(k + " stuck");
        if (carriedOut) bad.push(k + ": a support was carried out");
        if (through) bad.push(k + ": a carried piece passed through another (" + through + " frames)");
        const nPut = D[k].steps.filter((s) => s[0] === "put").reduce((a, s) => a + s.length - 1, 0); if (carried !== nPut) bad.push(k + ": carried " + carried + " pieces, the table puts " + nPut);
        const puts = D[k].steps.filter((s) => s[0] === "put");
        if (k === "djoser" || k === "ziggurat") {
          const top = (p) => p.slice(1).filter((e) => e[3] > 1 && e[0] === "block").map((e) => e[0] + e[1]).sort().join(); // what stands on the bottom row (the plank aside)
          if (puts.length !== 2 || top(puts[0]) !== top(puts[1])) bad.push(k + ": the two ways carry different loads");
          const want = puts.map((p) => p.slice(1).filter((e) => e[1] === "mudbrick").length);
          if (!(rows[0] && rows[0].mud < want[0])) bad.push(k + ": wrong way did not crumble (" + JSON.stringify(rows[0]) + ")");
          if (!(rows[1] && rows[1].mud === want[1])) bad.push(k + ": right way crumbled (" + JSON.stringify(rows[1]) + ")");
        }
        if (k === "mausoleum") {
          const S = T.SOLUTIONS.mausoleum, readies = D[k].steps.filter((s) => s[0] === "ready"), base = (p) => p.slice(1).sort().join();
          if (readies.length !== 2 || base(readies[0]) !== base(readies[1])) bad.push("mausoleum: different bases");
          if (puts[0] && puts[0].slice(1).some((e) => S[e][1] === "wood")) bad.push("mausoleum: wood in the wrong way");
          if (rows[0] && rows[0].wood) bad.push("mausoleum: wood standing in the wrong way");
          for (const p of readies) for (const e of p.slice(1)) { const [d, , x, y] = S[e]; if (d === "square" && y < 2) { const on = p.slice(1).filter((f) => S[f][3] < 1).reduce((a, f) => a + Math.max(0, Math.min(x + 0.5, S[f][2] + 1) - Math.max(x - 0.5, S[f][2] - 1)), 0); if (on < 0.99) bad.push("mausoleum: column at " + x + " rests on " + on.toFixed(2) + " of its width"); } }
          if (puts[1] && puts[1].length - 1 >= S.length) bad.push("mausoleum: right way builds everything");
          if (!(rows[0] && rows[0].fell > 0.5)) bad.push("mausoleum: wrong way lintel did not fall " + JSON.stringify(rows[0]));
          if (!(rows[1] && rows[1].fell < 0.1)) bad.push("mausoleum: right way beam fell " + JSON.stringify(rows[1]));
        }
        if ((k === "mausoleum" || k === "ishtar") && !tapped) bad.push(k + ": supports not tapped out");
      }
      return [!bad.length, bad.join("; ")];
    },

    // general: one line at a time; a flavour line fired with a teaching line is dropped; bg lines never interrupt; leaving drops what is left
    "general-voice": () => {
      const bad = []; fresh(); noTeach(); start(0); T.newScene();
      T.say(78, { kind: "teach" }); T.say(84); run(0.1, false); if (T.voice.queue.some((q) => q.n === 84)) bad.push("flavour kept beside a teaching line");
      T.say(85, { kind: "bg" }); if (T.voice.queue.some((q) => q.n === 85)) bad.push("bg line queued while one plays");
      T.say(79, { kind: "teach" }); T.goMap(); if (T.voice.queue.length || cur()) bad.push("lines left after leaving");
      return [!bad.length, bad.join("; ")];
    },
    // general: a first-time crumble freezes once ever; the next one in that visit is a plain line; a third says nothing
    "general-once": () => {
      fresh(); noTeach(); start(0); T.newScene(); const p = put(0); run(0.5);
      const fire = () => { T.cueEvent("crumble", { piece: p }); run(3); };
      fire(); const a = T.CUE_TABLE.lines[72] && log.filter((q) => q[1] === 72).length; fire(); const b2 = log.filter((q) => q[1] === 72).length; fire(); const c = log.filter((q) => q[1] === 72).length;
      T.newScene(); fire(); const d = log.filter((q) => q[1] === 72).length;
      return [a === 1 && b2 === 2 && c === 2 && d === 3, `said after crumbles 1-3: ${a},${b2},${c}; next visit ${d}`];
    },
    // general: a waiting step says its line again 5 s after it ends, not sooner
    "general-repeat-5s": () => {
      fresh(); start(0); T.onEnterSite(0); run(20); const f = log.filter((q) => q[1] === 93);
      const gaps = f.slice(1).map((q, i) => q[0] - f[i][2]);
      return [f.length >= 2 && gaps.every((g) => Math.abs(g - 5) < 0.1), "gaps " + gaps.map((g) => g.toFixed(2)).join(",") + " lines " + said().join(",") + " step " + seq()];
    },
    // general: during a test only the lines marked for it start
    "general-test-only": () => {
      fresh(); noTeach(); start(0); T.newScene(); put(0); run(0.5); T.setTab(true); T.startTest(); T.setTab(false);
      T.say(84); run(1); const during = said().includes(84);
      return [!during, "a plain line played during the test: " + during];
    },
  };
  window.__cueTests = (names) => Object.keys(tests).filter((n) => !names.length || names.includes(n)).map((n) => {
    try { const [ok, info] = tests[n](); return [n, !!ok, info || ""]; } catch (e) { return [n, false, "error " + e.message]; }
  });
})();
