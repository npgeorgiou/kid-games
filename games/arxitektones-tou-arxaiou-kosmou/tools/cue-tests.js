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
      if (c && c !== c0) log.push([clock, c.n, null, T.active.some((s) => s !== c && (s.waitEvent || s.waitUntil)) || (c0 && c0.kind === "teach")]); // 4th: a step was waiting or a teaching line just ended into it
      if (physics && T.mode === "build" && !T.frozen()) { const f = T.test && T.test.fast && T.test.phase !== "fail" && T.test.phase !== "pass" ? 10 : 1; T.stepPhysics(f / 60, 8 * f); T.cleanupOutOfBounds(); T.updateCheck(1 / 60); }
    }
  };
  const said = () => log.map((q) => q[1]);
  const cur = () => T.voice.cur && T.voice.cur.n;
  const seq = () => T.cueMem().seq["first-site"];
  const fresh = () => { T.setVoices(false); T.setTab(false); T.goMap(); T.pieces.slice().forEach(T.removePiece); T.progress.done = {}; T.cueReset(); T.goMap(); log = []; };
  const noTeach = () => { T.cueMem().seq["first-site"] = "done"; T.cueMem().ever["welcome-first"] = 1; };
  const start = (i) => { if (T.currentLevel === i && !T.progress.done[T.LEVELS[i].key]) T.startLevel(i ? 0 : 1); T.startLevel(i); T.render(); }; // always a fresh site: re-entering an unfinished one keeps what was left there // the real game lays the screen out when it draws
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
  const pileAt = (m, def = "block") => { // a pile piece of that kind lying still, whose middle no other piece covers (what a child would grab)
    const all = T.pileBodies(), free = (q) => !all.some((o) => o !== q && o.getFixtureList().testPoint(q.getPosition()));
    const b = all.filter((q) => q.pileItem.material === m && q.pileItem.defKey === def).sort((u, v) => (free(v) - free(u)) || (u.getLinearVelocity().length() - v.getLinearVelocity().length()))[0];
    if (!b) throw new Error("no " + m + " " + def + " left in the pile at step " + seq());
    const q = b.getPosition(), r = T.pileBinRect; return { x: r.x + q.x * T.pileScale, y: r.y + r.h - q.y * T.pileScale };
  };
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

    // owner 17 Nov: the restart button's "are you sure? press twice" line plays even with the teaching ticks off; the map's
    // buttons are in the top right, all one size: top row textures, settings, restart (left to right), free play below the restart
    "restart-ask-and-buttons": () => {
      const bad = [];
      for (const [d, t] of [[false, false], [true, true]]) {
        fresh(); noTeach(); T.setDemos(d); T.setTeach(t); T.progress.done.mastaba = { pieces: [] }; T.mapStart(); run(40, false);
        T.restartPress(); run(0.1, false); if (cur() !== 91) bad.push(`demos ${d} teaching ${t}: line ${cur()} instead of 91`);
        run(10, false);
      }
      T.setDemos(true); T.setTeach(true);
      const tex = T.texButton(), set = T.settingsButton(), rst = T.restartButton(), fp = T.freePlayButton(), W = T.cssW;
      if (!(tex.size === set.size && set.size === rst.size && rst.size === fp.size)) bad.push("sizes " + [tex.size, set.size, rst.size, fp.size]);
      if (!(tex.y === set.y && set.y === rst.y && tex.x < set.x && set.x < rst.x && rst.x + rst.size / 2 <= W && rst.y - rst.size / 2 >= 0)) bad.push("top row not textures, settings, restart in the top right");
      if (!(fp.x === rst.x && fp.y > rst.y + rst.size)) bad.push("free play not below the restart");
      return [!bad.length, bad.join("; ") || "line 91 with the ticks off; buttons in place"];
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
      const quiet = () => { for (let k = 0; k < 100 && (cur() || T.voice.queue.length); k++) run(0.1); }; // the child waits until the voice is quiet
      const settle = () => { const s0 = seq(); for (let k = 0; k < 40 && seq() === s0; k++) run(0.1); }; // the child waits until the piece lies still (at most 4 s)
      fresh(); start(0); T.onEnterSite(0); run(3); step("t-drag-1", "after the welcome");
      // 9: a piece let go high up that breaks on landing does not count
      const p0 = put(0, 4); run(0.1); step("t-drag-1", "piece still falling"); T.removePiece(p0); run(8);
      if (said().includes(94)) bad.push("94 said for a piece that broke");
      drag(pileAt("mudbrick"), planAt()); settle(); step("t-tap3", "mudbrick dragged into the plan");
      const k1 = kids()[0]; if (k1) { const at = pieceAt(k1); tap(at); tap(at); tap(at); } run(3);
      const s7 = said(), i94 = s7.lastIndexOf(94); if (s7[i94 + 1] !== 132) bad.push("after 94 came " + s7[i94 + 1] + " not 132"); // 7
      step("t-drag-2", "after the three taps");
      drag(pileAt("mudbrick"), planAt()); settle(); step("t-dragback", "mudbrick in again (" + kids().map((p) => { const q = p.body.getPosition(), v = p.body.getLinearVelocity(); return [q.x.toFixed(2), q.y.toFixed(2), v.y.toFixed(3), p.heldBy, T.worldToScreen(q.x, 0).x | 0, T.buildingWidthPx | 0].join("/"); }).join(" ") + ")"); // 8
      const g = T.active.find((q) => q.n === 134 && q.act); if (!g || !g.act.drag) bad.push("no ghost drag for the drag-back");
      const k2 = kids()[0]; if (k2) drag(pieceAt(k2), sideAt()); run(3);
      step("t-drag-3", "dragged back to the pile by hand");
      if (cur() !== 138 && !said().includes(138)) bad.push("after the drag back, not line 138 (" + cur() + ")"); // owner 16 Nov night, 1
      run(8); step("t-drag-3", "8 s later (no going round again)");
      drag(pileAt("mudbrick"), planAt()); settle(); run(1); step("t-shovel", "one piece in (the shovel waits for three)"); if (said().includes(95)) bad.push("95 before four pieces");
      // 15 Nov night: the shovel's line once four pieces stand
      drag(pileAt("mudbrick"), planAt(-3)); run(1); if (said().includes(95)) bad.push("95 at two pieces");
      drag(pileAt("mudbrick"), planAt(3)); run(2); if (!said().includes(95)) bad.push("95 not said at three pieces"); // 15 Nov night: three
      // 6: the first-time mudbrick line never during the teaching (each drag above picked a mudbrick up)
      const bb = btn("broom"); tap(bb); run(8); if (kids().length) bad.push("the shovel left pieces"); if (T.demo || said().includes(123)) bad.push("a demo at the first site");
      const sol = T.SOLUTIONS.mastaba.slice().sort((a, b) => a[3] - b[3] || a[2] - b[2]), spots = sol.map((e) => T.worldToScreen(T.LEVEL_X0 + e[2] + 0.05, e[3] + 0.7)); // a little off its exact place, as a child lays it, so it does not start inside its left neighbour // let go a little above its place, as a child does
      const lay = (k) => drag(pileAt(sol[k][1], sol[k][0]), spots[k]); // the k-th piece of the suggested build, bottom row first
      for (let k = 0; k < 100 && seq() !== "t-red"; k++) run(0.1); // the dotted-outline line points first; the child waits it out
      for (let k = 0; k < 4; k++) { lay(k); run(0.3); }
      // 15 Nov night: a mudbrick dropped from high up breaks in the free building: its first-time line plays
      quiet(); const hi = T.spawnPiece("block", T.LEVEL_X0 + 6, 10, 0, "mudbrick"); // a mudbrick falling from high up beside the building
      let mx = 0, pv = null; for (let k = 0; k < 360 && T.pieces.includes(hi); k++) { const v = hi.body.getLinearVelocity(); if (pv) mx = Math.max(mx, Math.hypot(v.x - pv.x, v.y - pv.y)); pv = { x: v.x, y: v.y }; run(1 / 60); } run(0.5);
      if (!hi || T.pieces.includes(hi)) bad.push("the dropped mudbrick did not break (dv " + mx.toFixed(1) + ", auto " + hi.auto + ", held " + hi.heldBy + ", ghost " + hi.ghost + ", mat " + hi.material + ")"); else if (!said().includes(72)) bad.push("72 not said for the broken mudbrick (" + said().slice(-3).join(",") + ")");
      run(6); for (let k = 4; k < 7; k++) { lay(k); run(0.3); } if (said().includes(99)) bad.push("99 before eight pieces");
      run(6); lay(7); run(2); step("t-red", "eight pieces in");
      T.startTest(); run(0.3); step("t-undo", "red button pressed (waits for ten pieces)");
      // 15 Nov evening: the undo button's line after ten pieces, pointing at the undo button
      quiet(); lay(8); run(0.3);
      lay(9); run(1.5); if (cur() !== 135 || !glowsOn("undo")) bad.push("ten pieces: line " + cur() + ", undo glows " + glowsOn("undo") + ", pieces in " + kids().length + " pile " + T.pileBodies().filter((b) => b.pileItem.material === "mudbrick").length);
      run(3); step("t-green", "after the undo line");
      const busy = log.filter((q) => (q[1] === 78 || q[1] === 72) && q[3]); if (busy.length) bad.push("78/72 started while a step waited or right after a teaching line");
      if (!said().includes(78)) bad.push("78 never said in the free building");
      { const sd = said(), a = sd.indexOf(98), b = sd.indexOf(136), c = sd.indexOf(99); if (!(a >= 0 && a < b && b < c)) bad.push("dotted-outline line 136 not between 98 and 99: " + sd.join(",")); } // 15 Nov night

      return [!bad.length, bad.join("; ") || said().join(",")];
    },

    // 15 Nov evening: the "this opening stays empty" line only at the first site whose outline has openings
    "openings-first-site-only": () => {
      const withHoles = T.LEVELS.map((L, i) => (L.holes && L.holes.length ? i : -1)).filter((i) => i >= 0), got = [];
      for (const i of withHoles) { fresh(); noTeach(); start(i); T.newScene(); T.cueEvent("plan-shown"); run(3, false); if (said().includes(109)) got.push(T.LEVELS[i].key); }
      return [got.length === 1 && got[0] === T.LEVELS[withHoles[0]].key, "said at " + (got.join(",") || "none") + "; first with openings " + T.LEVELS[withHoles[0]].key];
    },

    // 15 Nov evening, 5: every line is said by some cue, demo or group; every moment the table listens for is one the game's code makes
    "voice-hooks": () => {
      const D = T.CUE_TABLE, used = new Set(), bad = [], add = (v) => { if (typeof v === "number") used.add(v); else if (Array.isArray(v)) v.forEach(add); else if (v && typeof v === "object") { if (Array.isArray(v.bySite)) add(v.bySite); if (v.group) add(D.groups[v.group].lines || D.groups[v.group].bySite); } };
      for (const c of D.cues) { add(c.say); add(c.after); }
      for (const g of Object.values(D.groups)) { add(g.lines); add(g.bySite); }
      const ownRecording = new Set(Object.values(D.groups).flatMap((g) => Object.entries(g.lineIf || {}).filter(([, c]) => c === "recorded").map(([n]) => +n))); // the owner's own voice, no text by design
      for (const dm of Object.values(D.demos)) for (const st of dm.steps) if (st[0] === "tell" || st[0] === "say") add(st[1]);
      const lines = Object.keys(D.lines).map(Number), unused = lines.filter((n) => !used.has(n)), missing = [...used].filter((n) => !ownRecording.has(n) && (!D.lines[n] || !D.lines[n].trim()));
      if (unused.length) bad.push("lines no cue says: " + unused.join(","));
      if (missing.length) bad.push("lines said but without text: " + missing.join(","));
      const thens = new Set(D.cues.map((c) => c.then).concat(Object.values(D.sequences).map((q) => q.then)).filter(Boolean));
      const inCode = (ev) => window.__SRC.includes('cueEvent("' + ev + '"') || (["crumble", "snap"].includes(ev) && window.__SRC.includes('onBreak("' + ev + '"'));
      const deaf = [...new Set(D.cues.map((c) => c.on))].filter((ev) => ev !== "step" && !thens.has(ev) && !inCode(ev));
      if (deaf.length) bad.push("moments nothing makes: " + deaf.join(","));
      for (const [n, q] of Object.entries(D.sequences)) for (const id of q.steps) if (!D.cues.some((c) => c.id === id)) bad.push(n + ": no step " + id);
      return [!bad.length, bad.join("; ") || lines.length + " lines, all used"];
    },

    // 15 Nov night: a piece let go inside the dotted outline: line 137 pointing at it, once per visit
    "dotted-outline-covered": () => {
      fresh(); noTeach(); start(0); T.newScene(); const r = T.grid.load[0], cx = r.reduce((a, q) => a + q[0], 0) / r.length, cy = r.reduce((a, q) => a + q[1], 0) / r.length;
      const p = T.spawnPiece("block", cx, cy, 0, "mudbrick"); T.cueEvent("placed-in-plan"); run(0.2); const first = cur(), glow = T.active.some((q) => (q.targets || []).some((t) => t.rings));
      run(4); T.cueEvent("placed-in-plan"); run(0.2); const again = cur() === 137;
      return [first === 137 && glow && !again, "line " + first + ", outline glows " + glow + ", again the same visit " + again];
    },

    // 15 Nov night: each part of the test is explained the first time it is reached, even if an earlier test failed before it
    "test-explained-at-first-reach": () => {
      fresh(); noTeach(); start(0); T.newScene(); T.setTab(true); T.startAutoBuild(); run(14); T.setTab(false);
      let failedAt = null, part = null; const ph = []; T.setTab(true); T.startTest(); T.setTab(false);
      for (let k = 0; k < 400 && T.test && T.test.phase !== "fail" && T.test.phase !== "pass"; k++) {
        if (["wind", "load", "quake"].includes(T.test.phase)) part = T.test.phase; if (ph[ph.length - 1] !== T.test.phase) ph.push(T.test.phase);
        if (T.test.phase === "wind") { const top = T.pieces.filter((p) => !p.demo).sort((u, v) => v.body.getPosition().y - u.body.getPosition().y)[0]; top.body.setLinearVelocity(planck.Vec2(6, 2)); } // a gust throws the top brick off: the wind fails it
        run(0.1);
      }
      if (T.test && T.test.phase === "fail") failedAt = part; run(6);
      const s1 = said().slice(), mem = JSON.stringify(T.cueMem()); fresh(); Object.assign(T.cueMem(), JSON.parse(mem)); log = s1.map((n) => [0, n, 0]); start(0); T.newScene(); // a fresh site (the pile whole again), the same cue memory: the child's second try
      T.setTab(true); T.startAutoBuild(); run(14); const ph2 = ["built " + T.pieces.length + " pile " + T.pileBodies().length + " auto " + !!T.auto]; T.startTest(); T.setTab(false); for (let k = 0; k < 600 && !T.progress.done.mastaba; k++) { if (T.test && ph2[ph2.length - 1] !== T.test.phase) ph2.push(T.test.phase); run(0.1); } run(3); ph.push("|", ...ph2);
      const s2 = said().slice(s1.length), n = (x, l) => l.filter((q) => q === x).length;
      const all = s1.concat(s2), ok = failedAt === "wind" && !s1.includes(102) && !s1.includes(103) && s2.includes(102) && s2.includes(103) && [101, 102, 103].every((x) => n(x, all) <= 1);
      return [ok, "phases " + ph.join(">") + " first test failed at " + failedAt + ", lines " + s1.join(",") + "; second " + s2.join(",")];
    },

    // skies test (owner 15 Nov): a site being built (never finished, or damaged) shows its day sky; a finished one the next night sky on every visit
    "sky-follows-site-state": () => {
      if (!T.setSky) return [true, "no skies in this build"];
      const bad = [], enter = (i) => { T.startLevel(i); T.onEnterSite(i); return T.skyNow; };
      fresh(); noTeach(); start(0); T.onEnterSite(0); const day = T.skyNow; T.newScene(); T.setTab(true); T.startAutoBuild(); run(14); T.startTest(); for (let k = 0; k < 600 && !T.progress.done.mastaba; k++) run(0.1); T.setTab(false); run(3); // built and passed for real
      T.goMap(); const n1 = enter(0); T.goMap(); const n2 = enter(0);
      if (!T.progress.done.mastaba) return [false, "the quick build did not pass its test"];
      for (const l of T.loads) l.body.setPosition(planck.Vec2(l.body.getPosition().x + 8, 1)); run(2); T.goMap(); // the headpiece knocked off: the site is damaged
      const dmg = enter(0);
      if (day !== dmg) bad.push("damaged site sky " + dmg + ", its day " + day);
      if (n1 === day || n2 === n1) bad.push("finished visits " + n1 + ", " + n2);
      return [!bad.length, "day " + day + ", finished " + n1 + " then " + n2 + ", damaged " + dmg];
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
      // owner 18 Nov: the new-site voice only the first time per site in a session; coming back again it is silent
      log = []; start(lvl("ziggurat")); T.goMap(); run(3, false); const again = said().some((x) => [34, 35, 36, 37].includes(x));
      if (again) bad.push("return from Ur again: the new-site line played again in the same session");
      run(6, false); log = []; start(lvl("djoser")); T.goMap(); run(6, false);
      if (said().some((x) => [34, 35, 36, 37].includes(x))) bad.push("new-site line after leaving Djoser");
      return [!bad.length, bad.join("; ")];
    },
    "map-next-glow-every-10s": () => { // owner 18 Nov: "make next site glow every 10 secs"
      fresh(); noTeach(); T.progress.done.mastaba = { pieces: [] }; T.mapStart(); run(5, false); log = [];
      const at = []; let was = false; for (let k = 0; k < 40 * 4; k++) { run(0.25, false); const g = T.active.some((s) => s.n == null && (s.targets || []).some((t) => t.btn === "site:djoser")); if (g && !was) at.push(+clock.toFixed(1)); was = g; }
      const gaps = at.slice(1).map((t, i) => t - at[i]), voiced = said().some((x) => [34, 35, 36, 37].includes(x));
      return [at.length >= 3 && gaps.every((g) => Math.abs(g - 10) < 0.5) && !voiced, `glows at ${at.join(", ")}; new-site voice ${voiced}`];
    },
    // owner 18 Nov: "a damaged site too, but of course not in sync, every site flash has its own counter"; "the voice cues for
    // next site - damaged site must play sound not every time they trigger (only the visual plays every time), the sound
    // must play the first time they happen per site"
    "damaged-alerts-own-count-voice-once": () => {
      fresh(); noTeach(); T.progress.done.mastaba = { pieces: [], broken: true }; T.progress.done.djoser = { pieces: [], broken: true }; T.mapStart(); log = [];
      const at = { mastaba: [], djoser: [] }, seen = new Set();
      for (let k = 0; k < 45 * 4; k++) { run(0.25, false); for (const f of T.flashes) if (!seen.has(f)) { seen.add(f); at[f.key].push(+clock.toFixed(1)); } }
      const g = (a) => a.slice(1).map((t, i) => t - a[i]), lines = said().filter((x) => x === 39).length;
      const ok = at.mastaba.length >= 3 && at.djoser.length >= 3 && [...g(at.mastaba), ...g(at.djoser)].every((d) => Math.abs(d - 10) < 0.5) && Math.abs(at.mastaba[0] - at.djoser[0]) > 1 && lines === 2;
      return [ok, `mastaba ${at.mastaba.join(",")}; djoser ${at.djoser.join(",")}; damaged line said ${lines} times`];
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

    // owner 18 Nov: "ishtar demo removes base first, then semicircle on top? are you OK?": a demo takes the wooden
    // supports out from the top down (the form under the arch before the planks it stands on)
    "demo-takes-supports-out-from-the-top": () => {
      fresh(); noTeach(); T.setDemos(true); const i = lvl("ishtar"); start(i); T.onEnterSite(i);
      const esc = () => window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
      const seen = []; for (let k = 0; k < 300 && !T.demo; k++) { if (k % 20 === 0) seen.push(cur() + "/" + T.mode + "/" + !!T.demo); run(0.1); }
      const out = []; let last = new Map();
      for (let k = 0; k < 1500; k++) {
        if (!T.demo) break;
        T.voice.queue.length = 0; run(0.1);
        const now = new Map(T.pieces.filter((p) => p.demo && p.material === "wood").map((p) => [p, +p.body.getPosition().y.toFixed(2)]));
        for (const [p, y] of last) if (!now.has(p) && T.demo) out.push(p.defKey + "@" + y);
        last = now;
      }
      const ys = out.map((x) => +x.split("@")[1]), ok = ys.length >= 5 && ys.every((y, j) => !j || y <= ys[j - 1] + 0.05);
      return [ok, "taken out in this order: " + out.join(", ") + (out.length ? "" : "; before the demo: " + seen.join(" "))];
    },
    // owner 16 Nov night, 3 and 11: ESC ends the line playing (the intro and its picture); with none, it leaves a site or free play
    "esc": () => {
      const bad = [], esc = () => window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
      fresh(); noTeach(); const i = lvl("djoser"); start(i); T.onEnterSite(i); run(0.3);
      if (cur() !== 2) bad.push("no intro line at the Step Pyramid (" + cur() + ")");
      esc(); run(0.1); if (cur() === 2) bad.push("ESC did not end the intro"); if (T.mode !== "build") bad.push("ESC on the intro left the site");
      for (let k = 0; k < 100 && (cur() || T.voice.queue.length || T.demo); k++) { if (T.demo) { T.voice.queue.length = 0; } run(0.1); if (T.demo) break; }
      if (T.demo) { for (let k = 0; k < 400 && T.demo; k++) run(0.1); } for (let k = 0; k < 60 && (cur() || T.voice.queue.length); k++) { esc(); run(0.1); }
      esc(); run(0.1); if (T.mode !== "map") bad.push("ESC with no line did not leave the site (mode " + T.mode + ", line " + cur() + ")");
      T.startFree(); run(0.5); for (let k = 0; k < 30 && cur(); k++) { esc(); run(0.1); } esc(); run(0.1); if (T.mode !== "map") bad.push("ESC did not leave free play");
      return [!bad.length, bad.join("; ") || "ok"];
    },
    // owner 16 Nov night, 6: the intro line and its picture only at a site never won, not when a won site is damaged and fixed
    "intro-only-before-won": () => {
      const bad = [], i = lvl("djoser");
      fresh(); noTeach(); T.progress.done.djoser = { broken: true, pieces: [] }; start(i); T.onEnterSite(i); run(1);
      if (said().includes(2)) bad.push("the intro played at a damaged site");
      fresh(); noTeach(); start(i); T.onEnterSite(i); run(0.5); if (!said().includes(2)) bad.push("no intro at a site never won");
      return [!bad.length, bad.join("; ") || "ok"];
    },
    // owner 16 Nov night, 4: free play's sidebar is a pile with one of each piece; a piece taken out is replaced from above
    "free-play-pile": () => {
      const bad = []; fresh(); T.startFree(); run(2);
      const items = T.pileBodies().map((b) => b.pileItem.defKey + "/" + b.pileItem.material).sort(), want = [];
      for (const [m, gs] of Object.entries({ wood: ["square", "block", "column", "drum", "beam", "plank", "plank8", "plank10", "centering"] })) for (const k of gs) want.push(k + "/" + m);
      for (const w of want) if (!items.includes(w)) bad.push("no " + w);
      for (const k of ["plank14", "plank12", "longplank"]) if (items.includes(k + "/wood")) bad.push(k + " still there");
      if (new Set(items).size !== items.length) bad.push("doubles in the pile");
      const stand = T.pileBodies().filter((b) => b.pileItem.material === "wood" && /plank|beam/.test(b.pileItem.defKey)).map((b) => Math.abs(Math.abs(b.getAngle()) - Math.PI / 2) < 0.2);
      if (stand.some((v) => !v)) bad.push("a plank not standing");
      if (Math.abs(T.levelSidebar().bin.w - T.pileBinRect.w) > 1) bad.push("sidebar not like the levels'");
      const n0 = T.pileBodies().length; const a = pileAt("stone", "block"); drag(a, planAt(0, 2)); run(3);
      if (T.pileBodies().length !== n0) bad.push("not replaced: " + T.pileBodies().length + " vs " + n0);
      if (!T.pieces.some((p) => p.defKey === "block" && p.material === "stone")) bad.push("the stone block did not come out");
      return [!bad.length, bad.join("; ") || "ok"];
    },
    // owner 16 Nov, late: "that line plays as soon as the teaching ends, without another pickup??? by then the kid cant connect it ... make mudbrick as it was before, and make wood the same as mudbrick":
    // the first mudbrick / first wood line is not said while the teaching waits, not said when the teaching ends, and is said at the next pick-up of that material
    "first-pick-only-on-pickup": () => {
      const bad = [];
      for (const [mat, line] of [["wood", 80], ["mudbrick", 78]]) {
        fresh(); start(0); T.onEnterSite(0); run(3);
        const p0 = pileAt(mat, "block"); if (!p0) { bad.push("no " + mat + " block in the Mastaba pile"); continue; }
        drag(p0, planAt(4)); run(3); if (said().includes(line)) bad.push(line + " said while a teaching step waited");
        T.cueMem().seq["first-site"] = "done"; T.active.length = 0; run(6); // the teaching over (its last step taken away)
        if (said().includes(line)) bad.push(line + " said when the teaching ended, without a pick-up");
        const p1 = pileAt(mat, "block"); if (!p1) { bad.push("no second " + mat + " block"); continue; }
        drag(p1, planAt(3)); run(3);
        if (!said().includes(line)) bad.push(line + " not said at the next " + mat + " pick-up (" + said().join(",") + ")");
      }
      return [!bad.length, bad.join("; ") || "said only at a pick-up"];
    },
    // owner 16 Nov, late: the Mausoleum demo has two lines, one during the wrong way and one during the right way
    "mausoleum-demo-two-lines": () => {
      const st = T.CUE_TABLE.demos.mausoleum.steps, lines = st.map((o, i) => [o, i]).filter(([o]) => o[0] === "say" || o[0] === "tell"), readies = st.map((o, i) => [o, i]).filter(([o]) => o[0] === "ready").map(([, i]) => i);
      const ok = lines.length === 2 && readies.length === 2 && lines[0][1] > readies[0] && lines[0][1] < readies[1] && lines[1][1] > readies[1];
      return [ok, lines.map(([o]) => o[1]).join(",")];
    },
    // owner 16 Nov: ΔΙΔΑΣΚΑΛΙΑ unticked: no teaching steps or teaching lines at the first site (map welcome still said); ticked again, the teaching runs
    "teaching-off": () => {
      const bad = [], teachLines = new Set(T.CUE_TABLE.cues.filter((c) => c.teaching && typeof c.say === "number").map((c) => c.say));
      fresh(); T.setTeach(false); T.mapStart(); run(3); if (!said().length) bad.push("no welcome on the map");
      start(0); T.onEnterSite(0); run(20);
      const t = said().filter((n) => teachLines.has(n)); if (t.length) bad.push("teaching lines said: " + t.join(","));
      if (T.active.some((s) => s.seq)) bad.push("a teaching step waits");
      fresh(); T.setTeach(true); start(0); T.onEnterSite(0); run(20);
      if (!said().some((n) => teachLines.has(n))) bad.push("no teaching with the tick on");
      T.setTeach(true);
      return [!bad.length, bad.join("; ") || "tick off: no teaching, other lines play; tick on: teaching"];
    },
    // owner 16 Nov: ΒΟΗΘΗΤΙΚΑ ΒΙΝΤΕΟ unticked: no site plays its demo; the welcome line still plays; ticked again, the demo is back
    "demos-off": () => {
      const bad = [], k = "djoser";
      fresh(); noTeach(); T.setDemos(false); let i = lvl(k); start(i); T.onEnterSite(i); for (let n = 0; n < 100; n++) { run(0.1); if (T.demo) { bad.push("a demo played with the tick off"); break; } }
      if (!said().length) bad.push("no line at all at the site");
      fresh(); noTeach(); T.setDemos(true); i = lvl(k); start(i); T.onEnterSite(i); for (let n = 0; n < 100 && !T.demo; n++) run(0.1);
      if (!T.demo) bad.push("no demo with the tick on");
      return [!bad.length, bad.join("; ") || "tick off: no demo, lines still play; tick on: demo"];
    },
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
          if (puts[0] && puts[0].slice(1).some((e) => (typeof e === "number" ? S[e] : e)[1] === "wood")) bad.push("mausoleum: wood in the wrong way");
          const ent = (e) => (typeof e === "number" ? S[e] : e), post = puts[1] && puts[1].slice(1).map(ent).find((e) => e[1] === "wood"), lin = puts[1] ? puts[1].slice(1).map(ent).filter((e) => e[0] === "beam") : [];
          if (!post || lin.length < 2 || !lin.every((b) => Math.abs(b[2] - post[2]) < 1.6 + 0.3)) bad.push("mausoleum: the post does not sit under both lintels"); // 15 Nov night: the joint of the two
          if (rows[0] && rows[0].wood) bad.push("mausoleum: wood standing in the wrong way");
          for (const p of readies) for (const e of p.slice(1)) { const [d, , x, y] = S[e]; if (d === "square" && y < 2) { const on = p.slice(1).filter((f) => S[f][3] < 1).reduce((a, f) => a + Math.max(0, Math.min(x + 0.5, S[f][2] + 1) - Math.max(x - 0.5, S[f][2] - 1)), 0); if (on < 0.99) bad.push("mausoleum: column at " + x + " rests on " + on.toFixed(2) + " of its width"); } }
          if (puts[1] && puts[1].length - 1 >= S.length) bad.push("mausoleum: right way builds everything");
          if (!(rows[0] && rows[0].fell > 0.1)) bad.push("mausoleum: wrong way lintel did not tip " + JSON.stringify(rows[0]));
          if (!(rows[1] && rows[1].fell < 0.1)) bad.push("mausoleum: right way beam fell " + JSON.stringify(rows[1]));
          if (!(rows[1] && rows[1].wood === 0)) bad.push("mausoleum: the post was not taken out " + JSON.stringify(rows[1]));
        }
        if ((k === "mausoleum" || k === "ishtar") && !tapped) bad.push(k + ": supports not tapped out");
        if (D[k].steps.some((s) => s[0] === "pull") && rows.length && rows[rows.length - 1].wood) bad.push(k + ": wood left standing after the supports came out");
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
    // owner 17 Nov: "when some of the setting checkboxes are unchecked, the green test button doesnt work": every
    // combination of the two ticks, a first visit as the child makes it (entered from the map, built, the green button clicked)
    "settings-test-button": () => {
      const bad = [];
      for (const k of ["djoser", "ziggurat"]) for (const [d, t] of [[true, true], [false, true], [true, false], [false, false]]) {
        fresh(); noTeach(); T.setDemos(d); T.setTeach(t); const i = lvl(k); start(i); T.onEnterSite(i); run(40);
        T.setTab(true); T.startAutoBuild(); run(14); T.setTab(false); run(4);
        const b = T.screenButtons().find((x) => x.id === "test"), ready = T.testReady();
        tap(b); run(0.5);
        if (!T.test) bad.push(`${k} demos ${d} teaching ${t}: ready ${ready}, enabled ${b.enabled}, holding ${JSON.stringify(T.attention())}, demo ${!!T.demo}, active ${T.active.map((s) => s.id || s.n).join(",")}`);
        T.setTab(true); run(20); T.setTab(false);
      }
      T.setDemos(true); T.setTeach(true);
      return [!bad.length, bad.join(" | ") || "green button works with every combination"];
    },
    // owner 17 Nov: the recorded lines (src/sounds/voice; a line recorded in parts, n.1, n.2, ..., joined with 0.1 s of
    // silence between them): a recorded line plays its recording and ends when the recording does, by the game clock
    "voice-recordings": () => {
      const bad = []; fresh(); T.setVoices(true);
      for (const n of [93, 3]) {
        const len = T.VOICE_SECONDS[n]; if (!len) { bad.push("no recording for line " + n); continue; }
        T.say(n); run(0.1); if (cur() !== n || !T.cueAudio) bad.push(n + " did not start its recording");
        run(len - 0.3); if (cur() !== n) bad.push(n + " ended before its recording (" + len + " s)");
        run(0.4); if (cur() === n) bad.push(n + " still playing after its recording ended");
        run(1);
      }
      if (!(Math.abs(T.VOICE_SECONDS[3] - 51.41) < 0.1)) bad.push("line 3 (three parts) is " + T.VOICE_SECONDS[3] + " s, not 51.41");
      T.setVoices(false);
      return [!bad.length, bad.join("; ") || "recordings play to their end; parts joined"];
    },
    // owner 17 Nov: while a site's intro line speaks, the music at half and the voice 20% louder; the intro (its picture) ends when the recording ends
    "intro-voice-and-music": () => {
      const bad = []; fresh(); T.setVoices(true); start(0); T.onEnterSite(0); run(0.2);
      const c = T.voice.cur; T.updateMusic(false);
      if (!c || !c.cue || c.cue.id !== "site-intro") bad.push("no intro line (line " + (c && c.n) + ")");
      else {
        if (!T.cueAudio || Math.abs(T.cueAudio.volume - Math.min(1, T.MASTER_VOLUME * 0.9 * 1.2)) > 1e-6) bad.push("intro voice volume " + (T.cueAudio && T.cueAudio.volume));
        if (T.musicDuck !== 0.5) bad.push("music share during the intro " + T.musicDuck);
        T.cueAudio.dispatchEvent(new Event("ended")); run(0.1); T.updateMusic(false);
        if (T.voice.cur === c) bad.push("the intro line did not end when its recording ended");
        if (T.musicDuck !== 1) bad.push("music share after the intro " + T.musicDuck);
      }
      T.say(93); run(0.1); if (T.cueAudio && Math.abs(T.cueAudio.volume - T.MASTER_VOLUME * 0.9) > 1e-6) bad.push("other lines' volume " + T.cueAudio.volume);
      T.setVoices(false);
      return [!bad.length, bad.join("; ") || "music at half and voice 20% louder during the intro; it ends with its recording"];
    },
  };
  window.__cueTests = (names) => Object.keys(tests).filter((n) => !names.length || names.includes(n)).map((n) => {
    try { const [ok, info] = tests[n](); return [n, !!ok, info || ""]; } catch (e) { return [n, false, "error " + e.message]; }
  });
})();
