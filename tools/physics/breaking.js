  // tools/physics/breaking.js -- materials that break: a material with "crumbles" (MATERIALS) gives way under too much weight
  // resting on it or a hard knock; a piece with canSnap breaks when bent too far across a gap. Overload must last STRAIN_TIME.
  // The game provides: world, pieces, MATERIALS, PIECE_DEFS, test (null outside a test), crumble(piece) and snapWood(piece)
  // (what breaking looks and sounds like in that game), traceLoads (tools/physics/loads.js).
  const CRUSH_FORCE = 238; // N pressing down on one mudbrick block lying flat (2 m wide)
  // owner: a narrow mudbrick (a column standing up) holds less: what it holds goes with the width it stands on
  function crushLimit(p) {
    let x0 = Infinity, x1 = -Infinity;
    for (let f = p.body.getFixtureList(); f; f = f.getNext()) { // the drawn shape's width as it lies (not the physics' padded box)
      const sh = f.getShape();
      if (sh.getType() === "circle") { const c = p.body.getPosition(); x0 = Math.min(x0, c.x - sh.getRadius()); x1 = Math.max(x1, c.x + sh.getRadius()); }
      else for (const v of sh.m_vertices) { const q = p.body.getWorldPoint(v); x0 = Math.min(x0, q.x); x1 = Math.max(x1, q.x); }
    }
    return CRUSH_FORCE * (x1 - x0 + 2 * SKIN_GAP) / 2;
  }
  const MUD_SPAN_MIN = 0.3; // m
  const MUD_SNAP_MOMENT = 10; // N*m: mudbrick across a gap breaks under far less than wood (a stone block over a 1 m gap breaks it)
  const SNAP_MOMENT = 150;  // N*m bending a wood piece between (or beyond) its supports
  const STRAIN_TIME = { crumble: 0.5, snap: 0.25 }; // seconds of overload before it gives

  // Collect, per physics step, what presses on each mudbrick and where wood is held up and pushed down.
  onWorld("post-solve", (contact, impulse) => {
    const bA = contact.getFixtureA().getBody(), bB = contact.getFixtureB().getBody();
    const watch = (b) => b.piece && (MATERIALS[b.piece.material].crumbles || b.piece.canSnap);
    if (!watch(bA) && !watch(bB)) return;
    const wm = new planck.WorldManifold(); contact.getWorldManifold(wm);
    const n = wm.normal, cnt = contact.getManifold().pointCount;
    for (const [body, sign] of [[bA, -1], [bB, 1]]) {
      if (!watch(body)) continue;
      const piece = body.piece;
      const pts = [];
      for (let i = 0; i < cnt; i++) {
        const j = impulse.normalImpulses[i] / STEP; // N
        if (j > 0) pts.push([wm.points[i].x, wm.points[i].y, sign * n.x * j, sign * n.y * j]);
      }
      if (!pts.length) continue;
      if (MATERIALS[piece.material].crumbles && Math.abs(n.y) > 0.7) // weight pressing from above: contacts facing up or down only, not side pushes
        for (const p of pts) if (p[3] < 0) piece.crush -= p[3];
      // wood and mudbrick (owner: mudbrick laid across a gap like a lintel breaks easily) bend over gaps
      // wood: positions along the long axis, forces across it (towards up = holds it up)
      const a = body.getAngle(), along = piece.hx >= piece.hy;
      const ux = along ? Math.cos(a) : -Math.sin(a), uy = along ? Math.sin(a) : Math.cos(a);
      let px = -uy, py = ux;
      if (py < 0) { px = -px; py = -py; }
      if (py < 0.5) continue; // standing too upright to bend
      const c = body.getPosition();
      let s0 = Infinity, s1 = -Infinity, sl = 0, nl = 0;
      const down = [];
      for (const [x, y, fx, fy] of pts) {
        const s = (x - c.x) * ux + (y - c.y) * uy, f = fx * px + fy * py;
        if (f > 0) { s0 = Math.min(s0, s); s1 = Math.max(s1, s); }
        else { down.push([s, -f]); sl += s; nl++; }
      }
      // a piece lying flat on it presses along the whole face they share (the physics reports only its two ends),
      // so the part of its weight over a gap bends the wood
      if (down.length === 2) {
        const [[sa, pa], [sb, pb]] = down, N = 8;
        for (let k = 0; k < N; k++) piece.loads.push([sa + ((sb - sa) * (k + 0.5)) / N, (pa + pb) / N]);
      } else for (const d of down) piece.loads.push(d);
      // what hit it: kinetic energy it brought in = J^2 / 2m (J = the impulse that stopped it this step)
      const other = body === bA ? bB : bA, mo = other.isDynamic() ? other.getMass() : 0;
      if (nl && mo > 0 && piece.canSnap) {
        let J = 0;
        for (let i = 0; i < cnt; i++) J += impulse.normalImpulses[i];
        const hv = Math.min(J / mo, contact.tbVn || 0); // closing speed: resting weight is not a hit
        if (hv > 1.5) piece.impacts.push([sl / nl, 0.5 * mo * hv * hv, mo * GRAVITY]); // a real hit, not settling (over 1.5 m/s)
      }
      if (s1 >= s0) { // one support contact holds up the whole stretch it touches: all its manifold points count,
        // also those carrying no force this step (a slightly tilted piece rests on one corner at a time)
        for (let i = 0; i < cnt; i++) { const q = wm.points[i], sq = (q.x - c.x) * ux + (q.y - c.y) * uy; s0 = Math.min(s0, sq); s1 = Math.max(s1, sq); }
        // ... and the whole stretch where the piece lies over what holds it up (a piece tilted a little rests on corners)
        const of = body === bA ? contact.getFixtureB() : contact.getFixtureA(), ob = of.getBody(), sh = of.getShape(), ext = along ? piece.hx : piece.hy;
        let a = Infinity, b = -Infinity;
        if (sh.getType() === "circle") { const q = ob.getPosition(), sq = (q.x - c.x) * ux + (q.y - c.y) * uy; a = sq - sh.getRadius(); b = sq + sh.getRadius(); }
        else for (const v of sh.m_vertices) { const q = ob.getWorldPoint(v), sq = (q.x - c.x) * ux + (q.y - c.y) * uy; a = Math.min(a, sq); b = Math.max(b, sq); }
        a = Math.max(a, -ext); b = Math.min(b, ext);
        piece.sup.push(b > a ? [Math.min(a, s0), Math.max(b, s1)] : [s0, s1]);
      }
    }
  });

  // Bending: a load over a gap counts as if spread over that gap (P x gap / 4, so a
  // stiff block sitting near the supports still loads the beam); a load beyond the
  // last support bends by its distance from it. Loads right over a support count nothing.
  // minSpan (mudbrick): only a real lintel counts, a load over a gap at least that wide between two supports, not a
  // brick sticking out a little or the hair gaps of rough placing
  function bendMoment(p, minSpan = 0) {
    if (!p.sup.length || !p.loads.length) return 0;
    let M = 0;
    for (const [x, P] of p.loads) {
      let l = -Infinity, r = Infinity, held = false;
      for (const [a, b] of p.sup) {
        if (x >= a - 0.05 && x <= b + 0.05) { held = true; break; }
        if (b < x) l = Math.max(l, b);
        if (a > x) r = Math.min(r, a);
      }
      if (held) continue;
      if (Number.isFinite(l) && Number.isFinite(r)) { if (r - l >= minSpan) M += (P * (r - l)) / 4; }
      else if (!minSpan) M += P * Math.min(Math.abs(x - l), Math.abs(r - x));
    }
    return M;
  }

  // Impact on a beam (energy method): an object bringing kinetic energy KE onto a span L
  // between supports raises the bending moment by sqrt(6 * KE * EI / L) wherever it lands,
  // on top of its weight's own moment W*a*b/L; past the last support the arm a replaces L
  // and the weight's moment is W*a. Stiffer or shorter spans take more of the blow.
  const WOOD_EI = 1;       // bending stiffness of the wooden pieces, N*m^2 (placeholder, tune by play)
  const IMPACT_MIN_SPAN = 0.5; // m: spans shorter than this count as this
  function impactMoment(p) {
    if (!p.sup.length || !p.impacts.length) return 0;
    let M = 0;
    for (const [x, ke, W] of p.impacts) {
      let l = -Infinity, r = Infinity, held = false;
      for (const [a, b] of p.sup) {
        if (x >= a - 0.05 && x <= b + 0.05) { held = true; break; }
        if (b < x) l = Math.max(l, b);
        if (a > x) r = Math.min(r, a);
      }
      if (held) continue;
      let m;
      if (Number.isFinite(l) && Number.isFinite(r)) {
        const L = r - l;
        m = (W * (x - l) * (r - x)) / L + Math.sqrt((6 * ke * WOOD_EI) / Math.max(IMPACT_MIN_SPAN, L));
      } else {
        const a = Math.min(Math.abs(x - l), Math.abs(r - x));
        m = W * a + Math.sqrt((6 * ke * WOOD_EI) / Math.max(IMPACT_MIN_SPAN, a));
      }
      M = Math.max(M, m);
    }
    return M;
  }

  // Owner (13 Nov): weight is shared fairly. The physics engine works through the contacts one after another, so a
  // piece resting on several supports gave most of its weight to one of them: in a symmetric ziggurat the left middle
  // brick carried twice the right one. The weight on each piece is traced instead, from the top down: every piece
  // passes its own weight plus what rests on it to the pieces under it, as a stiff piece on equal springy supports
  // would: by how much of it lies on each, shifted towards the side its weight leans to.
  function updateStrain() {
    const traced = traceLoads();
    for (const p of pieces.slice()) {
      if (!MATERIALS[p.material].crumbles && !p.canSnap) continue;
      // hard landing: a mudbrick whose speed changed by more than MUD_SHATTER_SPEED in one step crumbles at once
      if (MATERIALS[p.material].crumbles) {
        const v = p.body.getLinearVelocity(), pv = p.prevV;
        p.prevV = { x: v.x, y: v.y };
        if (pv && p.heldBy == null && !p.auto && Math.hypot(v.x - pv.x, v.y - pv.y) > MUD_SHATTER_SPEED) { crumble(p); continue; }
      }
      // hit: wood snaps at once when an impact bends it past its strength
      if (p.canSnap && p.heldBy == null && impactMoment(p) > SNAP_MOMENT) { p.impacts.length = 0; snapWood(p); continue; }
      p.impacts.length = 0;
      let over = false, time = 1;
      if (p.heldBy == null) {
        if (MATERIALS[p.material].crumbles) { // the weight resting on it (read from its contacts, also while the stack sleeps), smoothed
          // over a few steps: the contacts jitter by more than the gap between holding and crumbling (seven mudbricks against four and two stones)
          const w = traced.has(p.body) ? traced.get(p.body).recv : 0;
          p.crushAvg = p.crushAvg == null ? w : p.crushAvg + (w - p.crushAvg) * 0.15;
          const bend = p.body.isAwake() ? bendMoment(p, MUD_SPAN_MIN) > MUD_SNAP_MOMENT : !!p.wasBent; p.wasBent = bend;
          over = p.crushAvg > crushLimit(p) || bend; time = STRAIN_TIME.crumble; }
        // a resting stack falls asleep and its contacts stop reporting: keep the last verdict until it wakes
        else if (!p.body.isAwake()) { over = !!p.wasOver; time = STRAIN_TIME.snap; }
        else { over = bendMoment(p) > SNAP_MOMENT; time = STRAIN_TIME.snap; }
      }
      p.wasOver = over;
      p.strain = over ? p.strain + STEP / time : Math.max(0, p.strain - STEP);
      p.crush = 0; p.sup.length = 0; p.loads.length = 0;
      if (p.strain >= 1) { if (MATERIALS[p.material].crumbles) crumble(p); else snapWood(p); }
    }
  }

  // Anything that breaks during the test fails it; its place is shown red.
