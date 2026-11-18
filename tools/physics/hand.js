  // tools/physics/hand.js -- the hand: a piece held by the finger, carried by an arm with a strength and a wrist.
  // Shared by every game (included inside the game's script by its build). The model is written out below, part by part.
  // The game provides: world, pieces (its pieces: {body, material, defKey or def {hx, hy}, heldBy, desired, grip, ghost, auto}),
  // PIECE_DEFS, pointers (finger id -> {piece}), traceLoads (tools/physics/loads.js), anchorBody (a static body for the
  // fingers' joints), STEP (tools/physics/step.js). Its numbers (ARM_STRENGTH and the rest) are the game's settings, changed here
  // only with the owner's yes, as they are the same for every game unless he says otherwise.
  // Run once per physics tick, not per input event: a fast flick, or several
  // pointermove events the browser coalesces into one animation frame, can
  // report the pointer far from where it was a moment ago -- possibly
  // several times before a single tick runs. Reacting to each event directly
  // would let the piece be yanked through whatever is in its path within one
  // step, which the solver would resolve as a sudden deep overlap, launching
  // the obstacle at an unrealistic speed. Computing the drive fresh from the
  // piece's actual current position, once per tick, bounds that regardless
  // of how bursty the input was.
  //
  const GRAVITY = 10;
  // THE HAND (owner 14 Nov 2026: real, consistent, one model, nothing made up). Two parts, everything else is the
  // physics engine:
  // - The arm: a steady arm, not a spring (no rubber band). Each step it wants the grab point to head for the finger
  //   and pushes with the force that gets that speed within ARM_REACT, plus holding up the weight carried (the piece
  //   plus the share of weight resting on it, from what rests on what). The arm has ARM_STRENGTH in all; what is left
  //   after holding up the weight moves the load, but the brain never uses more than HAND_GRIP x the weight for moving
  //   it (owner 12-14 Nov: strength the job needs, so a small stone cannot shove a big block; heavier lags; above two
  //   stone blocks it cannot lift). It speeds a load up over at most one sweep of the arm, ARM_RUN (owner 14 Nov: a
  //   mudbrick block dragged sideways at full speed and let go at mid-screen height flies 9 m, then 'a bit less'; every other piece by
  //   its weight), and never harder than what rests on it can follow without sliding (its friction). Heading for the
  //   finger it never goes faster than it can still stop at the finger (the standard time-optimal approach), so a
  //   piece runs on as its speed and the arm's strength make it and comes back without springing past the finger.
  //   What it moves is the piece, what rests on it, and the pieces it pushes on its way (owner 15 Nov: a row pushed
  //   like a train is one heavier load; each touching piece counted as much as it lies in the way, with what rests on
  //   it), so a row starts slower and one too heavy for the strength left does not move, wherever the piece is held.
  //   Pulling by a point beyond the middle helps only the piece itself, less and less the more it pushes.
  // - The fingers hold the piece where it was grabbed (a pin, never slipping). The wrist resists turning like
  //   friction with a static and a sliding level (the standard Stribeck friction curve, with its viscous part): while
  //   still it holds up to the weight and the pull the arm feels, each times the distance from the piece's middle to the
  //   edge of its middle third (towards the grab point; the grab point's own distance if that is less); against the pull
  //   only the share that moves the piece itself (M / Mt): the share pressing into what it pushes turns nothing in a
  //   free piece, so the wrist does not hold against it (owner 16 Nov: a plank across a log pulled down anywhere tips), once turning only WRIST_SLIP of that, less and less once the piece has
  //   turned in the fingers (WRIST_TURNED, so it hangs straight rather than stopping part way), and it damps swinging (WRIST_DAMP of
  //   critical). A pull through the grab point turns the piece by at most the grab
  //   point's distance from the middle, so a piece grabbed in its middle third never turns however the hand moves
  //   (owner 14 Nov, every piece by its own size; a stack lifted by its bottom piece too); grabbed in an outer third,
  //   the weight wins, the wrist gives way and it falls round, settling hanging without bouncing.
  const ARM_STRENGTH = 210; // N: a stone block weighs 100 N, so two blocks lift slowly and a bit more does not
  const ARM_SPEED = 11, ARM_EASE = 0.08, ARM_REACT = 0.05, ARM_RUN = 1.4, ARM_CARE = 0.8; // m/s, s, s, m, share of the friction
  const HAND_GRIP = 3.8; // most strength the brain uses for moving, as a multiple of the weight carried
  const WRIST_SLIP = 0.1, WRIST_GIVE = 0.3, WRIST_DAMP = 0.35, WRIST_TURNED = 0.3, WRIST_SEEN = 4, ARM_PULL = 5; // share, rad/s (holding to slipping), share of critical, rad (turned in the fingers)
  const HAND_MASS = 0.2; // kg: the hand, moved along with the piece
  const dIn = new planck.DistanceInput(), dOut = new planck.DistanceOutput(), dCache = new planck.SimplexCache();
  // distance from a body down to the nearest piece under it, if closer than `reach`
  function gapBelow(body, reach) {
    let best = null;
    for (let f = body.getFixtureList(); f; f = f.getNext()) {
      const bb = f.getAABB(0);
      world.queryAABB(planck.AABB(planck.Vec2(bb.lowerBound.x, bb.lowerBound.y - reach), planck.Vec2(bb.upperBound.x, bb.upperBound.y)), (fx) => {
        const b = fx.getBody();
        if (b === body || !b.piece || b.piece.ghost || b.piece.auto) return true;
        dIn.proxyA.set(f.getShape(), 0); dIn.proxyB.set(fx.getShape(), 0);
        dIn.transformA.set(body.getTransform()); dIn.transformB.set(b.getTransform());
        dIn.useRadii = true; dCache.count = 0; planck.Distance(dOut, dCache, dIn);
        if (dOut.distance < reach && dOut.pointB.y < dOut.pointA.y + 0.01 && (best == null || dOut.distance < best)) best = dOut.distance;
        return true;
      });
    }
    return best;
  }
  function touchesOtherPiece(body) {
    if (body.piece && body.piece.ghost) return false;
    for (let ce = body.getContactList(); ce; ce = ce.next) {
      if (ce.contact.isTouching() && ce.other.piece) return true;
    }
    return false;
  }
  // the pieces the held one pushes heading (dx, dy): every touching piece, as much as it lies in that direction, then
  // the pieces those push, each with the weight resting on it (from what rests on what); not what rests on the held one
  function pushedMass(body, dx, dy, d, traced) {
    if (d < 1e-6) return 0;
    const ux = dx / d, uy = dy / d, seen = new Set([body]), wm = new planck.WorldManifold();
    for (const [b, it] of traced) if (it.sup.some((q) => q.low === body)) seen.add(b);
    let m = 0, front = [[body, 1]];
    while (front.length) {
      const next = [];
      for (const [a, share] of front) for (let ce = a.getContactList(); ce; ce = ce.next) {
        const o = ce.other, c = ce.contact;
        if (seen.has(o) || !c.isTouching() || !o.piece || o.piece.ghost || o.piece.auto || o.piece.heldBy != null) continue;
        c.getWorldManifold(wm); const sg = c.getFixtureA().getBody() === a ? 1 : -1, k = share * Math.max(0, sg * (wm.normal.x * ux + wm.normal.y * uy));
        if (k <= 0) continue;
        seen.add(o); const t = traced.get(o); m += k * (o.getMass() + (t ? t.recv : 0) / GRAVITY); next.push([o, k]);
      }
      front = next;
    }
    return m;
  }
  // how hard the arm can speed up a load of weight W (N), and the top speed it gives it in one sweep (ARM_RUN)
  function armAccel(W) {
    const M = W / GRAVITY, most = Math.min(W, ARM_STRENGTH) + Math.min(HAND_GRIP * W, Math.max(0, ARM_STRENGTH - W));
    return Math.min((most - Math.min(W, most)) / M, HAND_GRIP * GRAVITY * Math.max(0, 1 - W / ARM_STRENGTH));
  }
  function armTopSpeed(W) { return Math.min(ARM_SPEED, Math.sqrt(2 * armAccel(W) * ARM_RUN)); }
  function advanceHeldTargets() {
    let traced = null;
    for (const hand of pointers.values()) {
      const piece = hand.piece;
      if (!piece || !piece.desired || !piece.grip) continue;
      if (!traced) traced = traceLoads(true);
      const body = piece.body, t = traced.get(body), W = body.getMass() * GRAVITY + (t ? t.recv : 0), M = W / GRAVITY;
      const most = Math.min(W, ARM_STRENGTH) + Math.min(HAND_GRIP * W, Math.max(0, ARM_STRENGTH - W));
      // what rests on it, and how hard it can be moved without that sliding
      let A = armAccel(W); // lighter is always quicker
      for (const [b, it] of traced) if (it.sup.some((q) => q.low === body)) A = Math.min(A, ARM_CARE * GRAVITY * Math.sqrt(b.getFixtureList().getFriction() * body.getFixtureList().getFriction()));
      const p = body.getWorldPoint(piece.grabLocal), v = body.getLinearVelocityFromWorldPoint(p), f = piece.desired;
      const dx = f.x - p.x, dy = f.y - p.y, d = Math.hypot(dx, dy), Mt = M + pushedMass(body, dx, dy, d, traced), vmax = Math.min(ARM_SPEED, Math.sqrt(2 * A * ARM_RUN));
      const s = d > 1e-6 ? Math.min(vmax, d / ARM_EASE, Math.sqrt(2 * A * d)) / d : 0;
      // pulling a piece by a point away from its middle (like a rope) the arm is much stronger than pushing or lifting
      const c = body.getWorldCenter(), def = piece.def || PIECE_DEFS[piece.defKey], hx = def.hx || def.r, hy = def.hy || def.r || hx, lc = body.getLocalCenter();
      const lx = piece.grabLocal.x - lc.x, ly = piece.grabLocal.y - lc.y, r = Math.hypot(lx, ly);
      let ax = (dx * s - v.x) / ARM_REACT, ay = (dy * s - v.y) / ARM_REACT; const al = Math.hypot(ax, ay);
      const pull = (r > 1e-6 && al > 1e-6 ? Math.max(0, (ax * (p.x - c.x) + ay * (p.y - c.y)) / (al * r)) * r / (r + 0.3) : 0) * (M / Mt) ** 2;
      const Ap = A + pull * ARM_PULL * GRAVITY;
      if (al > Ap) { ax *= Ap / al; ay *= Ap / al; }
      // the arm holds up the weight first; what is left of its strength moves the load, never more than HAND_GRIP x the
      // weight held (the moving part is shortened until both hold)
      const cap = most + pull * ARM_PULL * W, hw = Math.min(W, cap), mm = Mt * Mt * (ax * ax + ay * ay), mh = Mt * ay * hw;
      const sh = mm > 1e-9 ? Math.min(1, (HAND_GRIP + pull * ARM_PULL) * W / Math.sqrt(mm), (-mh + Math.sqrt(Math.max(0, mh * mh + mm * (cap * cap - hw * hw)))) / mm) : 0;
      let Fx = sh * Mt * ax, Fy = sh * Mt * ay + hw;
      body.applyForce(planck.Vec2(Fx, Fy), p, true);
      // the wrist: against the weight, and against the hand's own speeding up and slowing down (the brain keeps what it
      // moves steady), it holds as far as the middle third reaches towards the grab point (the piece's own size); held in
      // an outer third, a push that turns the piece about something it rests on turns it in the fingers (owner 16 Nov:
      // a plank lying across a log, pulled down by its raised end, tips like a lever)
      const reach = r < 1e-6 ? 1e3 : r * Math.min(Math.abs(lx) > 1e-6 ? hx / 3 / Math.abs(lx) : 1e3, Math.abs(ly) > 1e-6 ? hy / 3 / Math.abs(ly) : 1e3);
      const w = body.getAngularVelocity(), hold = reach * W + Math.min(r, reach) * Math.hypot(Fx, Fy - W) * (M / Mt);
      // the fingers hold firmly only in the position they closed on; once the piece has turned in them, loosely
      const turned = Math.exp(-Math.abs(piece.grip.getJointAngle()) / WRIST_TURNED);
      piece.grip.setMaxMotorTorque(hold * turned * (WRIST_SLIP + (1 - WRIST_SLIP) * Math.exp(-Math.abs(w) / WRIST_GIVE)));
      // its damping, against swinging relative to the finger's own turning (a person whirling turns the wrist with the
      // circles; held still it calms the swing): the finger's turning from its last WRIST_SEEN steps, counted only as
      // much as the finger is really moving; never more than the weight's own turning pull at the grab point
      const hist = piece.fingerHist || (piece.fingerHist = []); hist.push({ x: f.x, y: f.y }); if (hist.length > 2 * WRIST_SEEN + 1) hist.shift();
      let wf = 0;
      if (hist.length === 2 * WRIST_SEEN + 1) { const h0 = hist[0], h1 = hist[WRIST_SEEN], h2 = hist[2 * WRIST_SEEN], ux = h1.x - h0.x, uy = h1.y - h0.y, vx2 = h2.x - h1.x, vy2 = h2.y - h1.y;
        const sp = Math.min(Math.hypot(ux, uy), Math.hypot(vx2, vy2)) / (WRIST_SEEN * STEP);
        wf = Math.atan2(ux * vy2 - uy * vx2, ux * vx2 + uy * vy2) / (WRIST_SEEN * STEP) * sp * sp / (sp * sp + 0.09); }
      const Ip = body.getInertia() + body.getMass() * r * r, tq = -WRIST_DAMP * 2 * Math.sqrt(Ip * W * Math.max(r, 0.05)) * (w - wf);
      body.applyTorque(Math.max(-r * W, Math.min(r * W, tq)), true);
    }
  }
  function dropHand(piece) { // let go: the fingers open and the arm goes away
    if (piece.handBody) { try { world.destroyBody(piece.handBody); } catch (err) { /* world already gone */ } }
    piece.handBody = null; piece.grip = null;
  }

