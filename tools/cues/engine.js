  // tools/cues/engine.js -- the cue engine: one table (the game's cues.json, its format in tools/cues/README.md) says what is
  // said, shown and taught, and when; this engine plays it. Shared by every game (included inside the game's script by its build).
  // The game provides (its vocabulary, see README.md): CUE_CONDITIONS (condition name -> function(x)), pointTargets(name, x)
  // (what a point names, as shapes on screen), cueEvent calls at its moments, POINT_KINDS, placeKey(i) (a place's key, for
  // "once": "place"; a place is what the game calls a level, a room, a site), cueContext() (what every moment carries, e.g. { place }), progress and SAVE_KEY (the saved record), playSound/startAudio, the drawing helpers (SKIN.highlight,
  // SKIN.dim, SKIN.ghostHand), worldToScreen and the game's own hooks used below (demo, mode, test, auto).
  // ---------------------------------------------------------------------
  // The cue model, three parts (the table's "rules" say the same in the owner's words; tools/cues/README.md is the pattern):
  // 1. Voice: one line at a time, in the order fired; a line lasts its recording, or LINE_TIME as a text box whose blue bar runs
  //    out (ESC ends it early). Lines belong to the screen they were fired on; leaving drops what is left. bg lines play only if
  //    nothing is playing or waiting; a flavour line fired with a teaching line at the same moment is dropped; during a test only
  //    lines marked for it start; while a step waits for the child, every other line is dropped (a dropped first time stays unused).
  // 2. Attention, per cue: none (what it points at glows), point (while the step waits, the rest darkens and only its points or its
  //    touch list can be touched), freeze (while its line plays, the rest darkens and the game freezes). A demo darkens all but the
  //    building and takes no touch. Ctrl held (parent) is never held back.
  // 3. Steps: a cue that waits for an action (an event, or until a condition) keeps its glows and ghost hand until it is done, says
  //    its line again REPEAT_GAP s after it ends, and an action that ends a step fires nothing else. A step in a sequence that needs
  //    something gone missing goes back to the step that makes it. Sequences and the saved record (first times, recent lines of
  //    groups, where each sequence stands) live in progress.cues, cleared by the restart.
  // The table only names events, conditions and points; their meanings are the vocabularies here (CUE_CONDITIONS, pointTargets,
  // the cueEvent calls), and cueCheckTable() lists any name the code does not know.
  const CUE_TABLE = null; // build.py puts cues.json here
  const CUES_OFF = false; // the harness turns the cues off for tests of other things
  const VOICE_FILES = {}; // line number -> recording; build.py fills it from src/sounds/voice/NN.mp3
  const VOICE_SECONDS = {}; // line number -> how long its recording lasts (build.py)
  let useVoices = true; // the cue tests switch the recordings off: they test the rules with the text box's fixed time
  // The recordings are made as loud as the other sounds (tools/normalize-sounds.php: -16 LUFS); a cue with "volume" plays
  // its line that much louder (Tower Builder's welcome lines: 1.2, owner 17 Nov). A recording the browser will not start before the first touch (sound is only
  // allowed after one) waits, silent and with no text box, and starts at the child's first touch.
  const VOICE_VOLUME = 0.9; // owner 17 Nov late (Tower Builder): the voice 10% lower everywhere; a cue's own "volume" makes its line louder or quieter
  let voiceBlocked = null;
  // The map's alerts beat (owner 18 Nov): "dumdum dum dumdumdum dumdumdum", then a rest; seconds into the bar.
  const PULSE_BEATS = [0, 0.16, 0.5, 0.86, 1.02, 1.18, 1.52, 1.68, 1.84], PULSE_BAR = 2.5;
  const PULSE_LIFE = 0.7; // s a beat's ring spreads and fades
  function pulseAges(t) { // the ages (0..1) of the beats whose rings are still spreading, t seconds into the rhythm
    const out = [];
    for (let bar = Math.floor(t / PULSE_BAR) - 1; bar <= Math.floor(t / PULSE_BAR); bar++) for (const x of PULSE_BEATS) { const a = (t - bar * PULSE_BAR - x) / PULSE_LIFE; if (bar >= 0 && a >= 0 && a < 1) out.push(a); }
    return out;
  }
  const HL_DAMAGED = "#e03c2d";
  const HL_COLOR = { yellow: "#ffd23f", green: "#3fd16b", red: "#e8463a" };
  const voice = { cur: null, queue: [] };
  // the text box stands in for the recordings; the blue bar on top runs out, emptying from the left
  const cueBox = document.createElement("div"), cueText = document.createElement("div"), cueBar = document.createElement("div");
  cueBox.style.cssText = "position:fixed;left:50%;bottom:6%;transform:translateX(-50%);max-width:70%;background:#fff;color:#222;font:22px/1.35 sans-serif;padding:20px 20px 14px;border-radius:12px;box-shadow:0 4px 18px rgba(0,0,0,.35);pointer-events:none;display:none;z-index:10;overflow:hidden";
  cueBar.style.cssText = "position:absolute;top:0;right:0;left:0;height:7px;background:#2f7fd8";
  cueBox.append(cueBar, cueText);
  document.body.appendChild(cueBox);
  const LINE_TIME = 2, REPEAT_GAP = 5, HL_PERIOD = 1.8, HL_RING = 40; // s (a text box line), s (after a waiting step's line ends), s (a glow's pulse), px (how far a highlight ring spreads)
  let scene = 0, active = [], whens = [], visit = {}, cueFrame = 0, cueClock = 0, lastInput = 0, cueAudio = null;
  const cueById = (id) => CUE_TABLE.cues.find((c) => c.id === id);

  // --- the saved record
  function cueMem() {
    const m = progress.cues || (progress.cues = {});
    if (m.site && !m.place) { m.place = m.site; delete m.site; } // older saves called places sites
    for (const k of ["ever", "place", "recent", "seq"]) m[k] = m[k] || {};
    return m;
  }
  function cueSave() { try { localStorage.setItem(SAVE_KEY, JSON.stringify(progress)); } catch (err) { /* ignore */ } }
  // Memory of what was said, by how long it lasts: ever and place (saved: they survive a refresh), session (since the game
  // was opened: a refresh or the restart is the child coming back, and these lines may come again; per place), visit.
  let sessionMem = {};
  const sessionKey = (name, x) => "session:" + name + "@" + placeKey(x.place);
  function onceKey(c, x) { return !c.once ? null : c.once === "ever" ? "ever:" + c.id : c.once === "place" ? "place:" + c.id + "@" + placeKey(x.place) : c.once === "session" ? sessionKey(c.sessionName || c.id, x) : "visit:" + c.id; }
  const memBox = (w) => (w === "visit" ? visit : w === "session" ? sessionMem : cueMem()[w]);
  function isMarked(k) { if (!k) return false; const [w, r] = [k.slice(0, k.indexOf(":")), k.slice(k.indexOf(":") + 1)]; return !!memBox(w)[r]; }
  function setMark(k, on) {
    if (!k) return;
    const w = k.slice(0, k.indexOf(":")), r = k.slice(k.indexOf(":") + 1), box = memBox(w);
    if (on) box[r] = 1; else delete box[r];
    if (w !== "visit" && w !== "session") cueSave();
  }
  // a group: random, never one of the last n played, n = half the group rounded down (`allowed`: the ones that fit now)
  function pickFrom(name, lines, allowed = lines) {
    const m = cueMem(), rec = m.recent[name] || (m.recent[name] = []), n = Math.floor(lines.length / 2);
    const last = n ? rec.slice(-n) : [], ok = allowed.filter((l) => !last.includes(l)), pool = ok.length ? ok : allowed;
    if (!pool.length) return null;
    const l = pool[Math.floor(Math.random() * pool.length)];
    rec.push(l); if (rec.length > lines.length) rec.shift(); cueSave();
    return l;
  }
  function newScene() { // a new screen (the game's map, a level, free play): what is left of the old one goes, unplayed first times stay unused
    scene++;
    for (const q of voice.queue) setMark(q.onceKey, false);
    voice.queue.length = 0; if (voice.cur) endLine(voice.cur);
    active = []; whens = []; visit = {};
    cueGameNewScene();
  }
  function cueReset() { progress.cues = null; sessionMem = {}; newScene(); }

  function cond(name, x = {}) {
    if (name.startsWith("not ")) return !cond(name.slice(4), x);
    const [k, v] = name.split(":");
    if (k === "material") return x.material === v;
    if (k === "part") return x.part === v;
    if (k === "why") return x.why === v;
    if (k === "placed") return childPieces().filter((p) => p.heldBy == null && worldToScreen(p.body.getPosition().x, 0).x < buildingWidthPx).length >= +v; // N of the child's pieces stand in the building
    if (k === "done") return isMarked("ever:" + v);
    return !!CUE_CONDITIONS[name](x);
  }

  // --- events: the game calls cueEvent at each moment the table can name (its "on")
  // An action that ends a waiting step fires nothing else; otherwise every cue on that event whose conditions hold fires, in table order.
  function cueEvent(name, ctx = {}) {
    const out = { ended: false, fired: [] };
    if (CUES_OFF) return out;
    for (const s of active) if (s.waitEvent === name && waiting(s)) { s.done = true; out.ended = true; }
    if (out.ended) return out;
    const x = Object.assign(cueContext(), ctx);
    const hits = CUE_TABLE.cues.filter((c) => c.on === name && !isMarked(onceKey(c, x)) && (c.if || []).every((k) => cond(k, x)));
    // what the child does wins (cues.json rules): a cue fired by the child's own action stops the cue playing, line and visuals together
    if (hits.length && (CUE_TABLE.words.events[name] || {}).byChild) interruptCues();
    for (const c of hits) { const f = fire(c, x); if (f) out.fired.push(f); }
    return out;
  }
  function interruptCues() { // the line playing and what it shows stop; lines waiting their turn are dropped (first times stay unused)
    if (teachingBusy() || stepWaiting() || demo) return; // a teaching sequence and a demo are never cut
    const c = voice.cur;
    if (c) { c.fin = true; endLine(c); }
    for (const q of voice.queue) setMark(q.onceKey, false);
    voice.queue = [];
    active = active.filter((a) => a.seq && waiting(a)); // glows, pointing and the ghost hand of what was playing go with it
  }
  function stepWaiting() { return active.some((s) => s.seq && waiting(s)); } // a teaching step waiting for the child
  function teachingBusy() { return (voice.cur && voice.cur.kind === "teach") || voice.queue.some((q) => q.kind === "teach"); }
  // fire one cue: its line (with what it points at, its hand, its wait), or its glow, or what it does
  function fire(c, x, seq) {
    const key = onceKey(c, x);
    const then = () => { if (c.after != null && (useTeach || !c.teaching)) say(c.after, { kind: "teach" }); if (seq) nextStep(seq, c.id); else if (c.then) cueEvent(c.then, x); };
    if (c.do === "teaching") { if (!useTeach) return c; setMark(key, true); runSequence(sequenceOf(x.place)); return c; } // ΔΙΔΑΣΚΑΛΙΑ off: no steps (they wait, unmarked, for when it is ticked again)
    if (!useTeach && c.teaching) { then(); return null; } // ΔΙΔΑΣΚΑΛΙΑ off: a teaching line is not said (and stays unused); what follows it goes on, and nothing waits for it (it did not fire: owner 17 Nov, the test waited for an unsaid explanation and never ran)
    if (c.do === "demo") { setMark(key, true); if (useDemos) startDemo(placeKey(x.place), then); else then(); return c; } // ΒΟΗΘΗΤΙΚΑ ΒΙΝΤΕΟ off: no demo, the rest goes on
    const memo = {}, pts = (names) => (names || []).flatMap((n) => pointTargets(n, x, memo));
    if (c.glow) { setMark(key, true); glowFor(pts(c.points), c.glow); then(); return c; }
    if (c.say == null) { setMark(key, true); then(); return c; }
    if (!seq && (teachingBusy() || stepWaiting())) return null; // while a teaching line plays or waits, or a step waits for the child, other lines are dropped (their first time stays unused)
    const n = lineOf(c, x);
    const line = say(n, {
      cue: c, kind: c.kind || "queued", attention: c.attention || "none", targets: pts(c.points), touch: c.touch ? pts(c.touch) : null,
      act: showOf(c.show, x, memo), waitEvent: c.wait && !c.wait.startsWith("until:") ? c.wait : null,
      waitUntil: c.wait && c.wait.startsWith("until:") ? c.wait.slice(6) : null, needs: c.needs, seq,
      duringTest: c.during === "test", after: typeof c.delay === "number" ? c.delay : c.delay ? soundLength(c.delay.slice(6)) : 0, onceKey: key, then,
    });
    if (line) { setMark(key, true); if (c.sessionName) setMark(sessionKey(c.sessionName, x), true); } // a first-time line also counts as this session's
    return line;
  }
  function lineOf(c, x) {
    const s = c.say;
    if (typeof s === "number") return s;
    if (s.byPlace && !s.group) return s.byPlace[x.place];
    const g = CUE_TABLE.groups[s.group], all = g.byPlace ? g.byPlace[x.place] : g.lines;
    const ok = all.filter((n) => !g.lineIf || !g.lineIf[n] || cond(g.lineIf[n], Object.assign({}, x, { line: n })));
    return pickFrom(s.group + (g.byPlace ? ":" + placeKey(x.place) : ""), all, ok);
  }

  // --- sequences: steps in order, resumed where the child left them; a step that needs something missing goes back
  function sequenceOf(place) { const k = placeKey(place); return Object.keys(CUE_TABLE.sequences).find((n) => CUE_TABLE.sequences[n].place === k) || null; }
  function runSequence(name) { if (name) runStep(name, cueMem().seq[name] || CUE_TABLE.sequences[name].steps[0]); }
  function runStep(name, id, depth = 0) {
    const c = cueById(id), m = cueMem(); m.seq[name] = id; cueSave();
    const go = () => {
      if (c.needs && !cond(c.needs) && c.back !== id && depth < 8) { runStep(name, c.back, depth + 1); return; }
      fire(c, cueContext(), name);
    };
    if (c.start) cueWhen(() => cond(c.start), go); else go();
  }
  function nextStep(name, id) {
    const sq = CUE_TABLE.sequences[name], i = sq.steps.indexOf(id);
    if (i + 1 < sq.steps.length) { runStep(name, sq.steps[i + 1]); return; }
    cueMem().seq[name] = "done"; cueSave();
    if (sq.then) cueEvent(sq.then);
  }

  // --- part 1: the voice
  function say(n, o = {}) {
    const c = Object.assign({ n, kind: "queued", attention: "none", frame: cueFrame, scene, at: cueClock + (o.after || 0) }, o);
    const teachNow = voice.queue.some((q) => q.frame === cueFrame && q.kind === "teach");
    if (n == null || !(VOICE_FILES[n] || CUE_TABLE.lines[n]) || (n === 86 && !VOICE_FILES[n]) || (c.kind === "bg" && (voice.cur || voice.queue.length)) || (c.kind !== "teach" && teachNow)) return null;
    if (c.kind === "teach") voice.queue = voice.queue.filter((q) => { const drop = q.frame === cueFrame && q.kind !== "teach"; if (drop) setMark(q.onceKey, false); return !drop; });
    voice.queue.push(c);
    return c;
  }
  function glowFor(targets, seconds) { if (targets.length) active.push({ n: null, ended: true, scene, t0: cueClock, until: cueClock + seconds, targets, attention: "none" }); }
  function cueWhen(cond, fire) { whens.push({ cond, fire }); }
  function startLine(c) {
    voice.cur = c; c.t0 = cueClock; c.ended = false; if (!active.includes(c)) active.push(c);
    const box = () => { if (voice.cur !== c) return; cueAudio = null; c.t0 = cueClock; cueText.textContent = CUE_TABLE.lines[c.n] || ""; cueBar.style.left = "0"; cueBox.style.display = "block"; };
    if (useVoices && VOICE_FILES[c.n]) {
      const a = (cueAudio = new Audio(VOICE_FILES[c.n]));
      a.volume = Math.min(1, MASTER_VOLUME * VOICE_VOLUME * ((c.cue && c.cue.volume) || 1));
      a.onended = () => endLine(c); // the recording's real end; the game clock ends it too, at its length (cueTick)
      const go = () => a.play().then(() => { c.t0 = cueClock; c.blocked = false; }).catch((err) => {
        if (voice.cur !== c || cueAudio !== a) return;
        if (err && err.name === "NotAllowedError") { c.blocked = true; voiceBlocked = go; } // waits for the first touch
        else box();
      });
      go();
    } else box();
  }
  function endLine(c) {
    if (voice.cur !== c) return;
    voice.cur = null; c.ended = true; c.endT = cueClock; cueBox.style.display = "none";
    if (cueAudio) { cueAudio.onended = null; cueAudio.pause(); cueAudio = null; }
  }
  function finish(c) { if (c.fin) return; c.fin = true; if (c.then) c.then(); }
  const waiting = (c) => !!((c.waitEvent || c.waitUntil) && !c.fin && !c.done && !(c.waitUntil && cond(c.waitUntil)));
  function gameNow() { return cueClock * 1000; } // game time in ms (the frame clock): input, the pile and the button go by it, so a test run repeats exactly
  function cueTick(dt) {
    cueFrame++; cueClock += dt;
    const now = cueClock, c = voice.cur;
    if (c) { // the line playing: its action done, or its time up (text box), ends it
      const u = (now - c.t0) / LINE_TIME;
      if ((c.waitEvent || c.waitUntil) && !waiting(c)) endLine(c);
      else if (cueAudio) { if (!c.blocked && now - c.t0 >= (VOICE_SECONDS[c.n] || 0)) endLine(c); } // a recording ends at its real end (onended) or by the game clock at its length, whichever comes first
      else { if (u >= 1) endLine(c); else cueBar.style.left = (u * 100).toFixed(1) + "%"; }
    }
    // a step in a sequence that needs something gone missing goes back to the step that makes it
    for (const s of active) if (s.seq && s.needs && waiting(s) && !cond(s.needs)) {
      const back = s.cue.back; s.fin = true; endLine(s); voice.queue = voice.queue.filter((q) => q !== s);
      if (back) runStep(s.seq, back);
    }
    active = active.filter((s) => {
      if (s.until != null) return now < s.until;
      if (s.fin) return false;
      if (s.ended && !waiting(s)) { finish(s); return false; }
      return true;
    });
    whens = whens.filter((w) => { if (w.cond()) { w.fire(); return false; } return true; });
    voice.queue = voice.queue.filter((q) => { if ((q.waitEvent || q.waitUntil) && !waiting(q)) { finish(q); return false; } return true; }); // done before its turn
    // a step still waiting says its line again, its hand with it, REPEAT_GAP s after its line ended
    for (const s of active) if (s.n != null && s.ended && waiting(s) && now - s.endT >= REPEAT_GAP && !voice.cur && !voice.queue.length) voice.queue.push(Object.assign(s, { at: now, frame: cueFrame }));
    if (!voice.cur) { // the next one in order; lines held back only by a test or a demo let later ones marked for it go first
      for (const q of voice.queue) {
        if (now < q.at) break;
        if ((test && !q.duringTest) || (demo && demo.go && !q.demo)) continue;
        voice.queue.splice(voice.queue.indexOf(q), 1); startLine(q); break;
      }
    }
    cueGameTick(dt); // the game's own moments, noticed by looking
  }
  function shapePath(s, d = 0) { // its outline grown by d px
    const p = new Path2D();
    if (s.kind === "circle") p.arc(s.x, s.y, s.r + d, 0, Math.PI * 2);
    else if (s.kind === "rect") p.rect(s.x - d, s.y - d, s.w + 2 * d, s.h + 2 * d);
    else if (s.kind === "region") p.addPath(screenPath(s.rings));
    else { const q = d ? growPoly(s.pts, d) : s.pts; q.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); }
    return p;
  }
  function growPoly(P, d) { // each side moved out by d (mitred corners): a plank's ring is a long box, a triangle's a triangle
    const n = P.length, cx = P.reduce((s, p) => s + p[0], 0) / n, cy = P.reduce((s, p) => s + p[1], 0) / n;
    const N = P.map((p, i) => {
      const q = P[(i + 1) % n]; let nx = q[1] - p[1], ny = p[0] - q[0]; const L = Math.hypot(nx, ny) || 1; nx /= L; ny /= L;
      if (nx * ((p[0] + q[0]) / 2 - cx) + ny * ((p[1] + q[1]) / 2 - cy) < 0) { nx = -nx; ny = -ny; }
      return [nx, ny];
    });
    return P.map((p, i) => { const a = N[(i + n - 1) % n], b = N[i], k = d / Math.max(0.3, 1 + a[0] * b[0] + a[1] * b[1]); return [p[0] + (a[0] + b[0]) * k, p[1] + (a[1] + b[1]) * k]; });
  }
  function shapeHit(s, px, py) {
    if (s.kind === "circle") return Math.hypot(px - s.x, py - s.y) <= s.r;
    if (s.kind === "rect") return px >= s.x && px <= s.x + s.w && py >= s.y && py <= s.y + s.h;
    if (s.kind === "region") { if (px >= buildingWidthPx) return false; const w = screenToWorld(px, py); return s.rings.some((r) => inRing(w.x, w.y, r)); }
    let inside = false; const P = s.pts;
    for (let i = 0, j = P.length - 1; i < P.length; j = i++) if ((P[i][1] > py) !== (P[j][1] > py) && px < ((P[j][0] - P[i][0]) * (py - P[i][1])) / (P[j][1] - P[i][1]) + P[i][0]) inside = !inside;
    return inside;
  }
  function shapeCentre(s) {
    if (s.kind === "circle") return { x: s.x, y: s.y };
    if (s.kind === "rect") return { x: s.x + s.w / 2, y: s.y + s.h / 2 };
    const P = s.kind === "region" ? s.rings.flat().map(([x, y]) => { const q = worldToScreen(x, y); return [q.x, q.y]; }) : s.pts;
    return { x: P.reduce((a, p) => a + p[0], 0) / P.length, y: P.reduce((a, p) => a + p[1], 0) / P.length };
  }
  function showOf(show, x, memo) { // "tap A", "tap3 A", "drag A > B": what the ghost hand acts out
    if (!show) return null;
    const [verb, rest] = [show.slice(0, show.indexOf(" ")), show.slice(show.indexOf(" ") + 1)];
    if (verb === "drag") { const [a, b] = rest.split(" > "); return { drag: pointTargets(a, x, memo)[0], to: pointTargets(b, x, memo)[0] }; }
    return { tap: pointTargets(rest, x, memo)[0], count: verb === "tap3" ? 3 : 1 };
  }
  function targetShapes(t) {
    const Y = HL_COLOR.yellow;
    if (!t) return [];
    if (t.btn) {
      const b = screenButtons().find((q) => q.id === t.btn); if (!b) return [];
      const color = buttonGlowColor(t.btn) || Y; // the game may colour a button's glow (its state)
      return [{ shape: b.rect ? Object.assign({ kind: "rect" }, b.rect) : { kind: "circle", x: b.x, y: b.y, r: b.glowR || b.r }, color }];
    }
    return gameTargetShapes(t, Y); // every other kind of point is the game's
  }
  const shapesOf = (targets) => (targets || []).flatMap(targetShapes);
  // what holds attention now: { holes (bright), touch (can be touched) } or null
  function attention() {
    if (demo) return { holes: [{ area: "build" }], touch: [] };
    const hold = active.filter((s) => (s.attention === "freeze" && s === voice.cur) || (s.attention === "point" && (s === voice.cur || waiting(s))));
    if (!hold.length) return null;
    const touch = hold.filter((s) => s.attention === "point").flatMap((s) => s.touch || s.targets || []);
    return { holes: hold.flatMap((s) => s.targets || []).concat(touch), touch };
  }
  function cueFrozen() { const c = voice.cur; return !!(c && c.attention === "freeze"); }
  function cueBlocks(px, py) {
    lastInput = cueClock;
    if (tabHeldNow()) return false;
    if (mode === "map") { const g = settingsButton(); if (settingsOpen || Math.hypot(px - g.x, py - g.y) <= g.size / 2) return false; } // the parent's gear and its box are never darkened away
    const at = attention();
    return !!at && !shapesOf(at.touch).some((t) => shapeHit(t.shape, px, py));
  }
  // the ghost hand acting out { tap: target, count } or { drag: target, to: target }, t s into it (all slow enough for a small child)
  function drawGhost(g, t) {
    if (g.tap) {
      const [q] = targetShapes(g.tap); if (!q) return;
      const c = shapeCentre(q.shape), n = g.count || 1, end = 0.8 + n * 0.5 + 1.2;
      if (t > end) return;
      const k = Math.max(0, 0.8 - t) / 0.8, press = t >= 0.8 && t < 0.8 + n * 0.5 && (t - 0.8) % 0.5 < 0.25;
      SKIN.ghostHand(ctx, c.x + k * 70, c.y + k * 70, press, Math.min(1, t / 0.4, (end - t) / 0.4) * 0.9);
      return;
    }
    if (g.drag) {
      const [a] = targetShapes(g.drag), [b] = targetShapes(g.to); if (!a || !b || t > 3.6) return;
      const A = shapeCentre(a.shape), B = shapeCentre(b.shape), u = Math.max(0, Math.min(1, (t - 1) / 2)), e = u * u * (3 - 2 * u);
      const x = A.x + (B.x - A.x) * e, y = A.y + (B.y - A.y) * e, held = t >= 0.6 && t < 3.1;
      if (held && a.item) { ctx.save(); ctx.globalAlpha = 0.45; drawPieceShape(a.item.defKey, a.item.material, x, y, a.a || 0, a.sc + ((b.sc || a.sc) - a.sc) * e, 0, 7); ctx.restore(); }
      SKIN.ghostHand(ctx, x, y, held, Math.min(1, t / 0.4, (3.6 - t) / 0.5) * 0.9);
    }
  }
  function drawCues() {
    const at = attention();
    if (at) SKIN.dim(ctx, cssWidth, cssHeight, shapesOf(at.holes).map((t) => shapePath(t.shape, 6)));
    const u = cueRhythm() ? null : (cueClock % HL_PERIOD) / HL_PERIOD; // a screen whose alerts beat the rhythm (PULSE_BEATS), each from its own start
    for (const c of active) for (const t of shapesOf(c.targets)) SKIN.highlight(ctx, (d) => shapePath(t.shape, d), t.shape.kind === "region", t.color, u == null ? pulseAges(cueClock - (c.t0 != null ? c.t0 : 0)) : u, HL_RING);
    const g = [...active].reverse().find((q) => q.act);
    if (g) drawGhost(g.act, cueClock - g.t0);
    cueGameDraw(); // what the game draws with the cues (its own alerts, its demo's hand)
  }

  // --- the moments the game names (thin calls from the rest of the code)
  // the table names only what the code knows: every event fired, condition, point and line used (the harness prints this)
  function cueCheckTable() {
    const bad = [], conds = (n) => { const b = n.replace(/^not /, ""); if (!/^(material|part|done|why|placed):/.test(b) && !CUE_CONDITIONS[b]) bad.push("condition " + n); };
    for (const c of CUE_TABLE.cues) {
      (c.if || []).forEach(conds); if (c.needs) conds(c.needs); if (c.start) conds(c.start); if (c.wait && c.wait.startsWith("until:")) conds(c.wait.slice(6));
      for (const p of (c.points || []).concat(c.touch || [])) if (!POINT_KINDS.includes(p.split(":")[0])) bad.push("point " + p);
      const n = typeof c.say === "number" ? [c.say] : c.say && c.say.byPlace && !c.say.group ? c.say.byPlace : [];
      for (const k of n.concat(c.after != null ? [c.after] : [])) if (!CUE_TABLE.lines[k]) bad.push("line " + k);
    }
    return bad;
  }

