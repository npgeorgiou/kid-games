  // tools/physics/loads.js -- what rests on what: each piece's own weight plus the share of the weight above it, split
  // between what holds it up so that it balances (traceLoads). Used by the hand (what it carries), breaking and the test.
  // The game provides: world, pieces, loads (other bodies that weigh on the pieces: {body, released}), GRAVITY, groundBody.
  const SUPPORT_NY = 0.3; // a contact facing up at least this much carries weight (arch stones included)
  function shareWeight(W, xbar, sup) { // sup: [{c, w}] -> forces, summing to W, balanced about xbar
    let act = sup.map((s, i) => i), f = sup.map(() => 0);
    for (let it = 0; it <= sup.length; it++) {
      let S0 = 0, S1 = 0, S2 = 0;
      for (const i of act) { const { c, w } = sup[i]; S0 += w; S1 += w * c; S2 += w * (c * c + (w * w) / 12); } // a wide support also resists turning (its own width), so a corner touching beside it takes no share it cannot have
      const det = S0 * S2 - S1 * S1;
      let al, be;
      if (det < 1e-9 * S0 * S0) { al = W / S0; be = 0; } else { al = (W * S2 - W * xbar * S1) / det; be = (W * xbar * S0 - W * S1) / det; }
      f = sup.map(() => 0); for (const i of act) f[i] = sup[i].w * (al + be * sup[i].c);
      const neg = act.filter((i) => f[i] < 0);
      if (!neg.length) return f;
      if (act.length - neg.length < 1) break;
      act = act.filter((i) => f[i] >= 0); // a support it would have to pull on: the piece lifts off it
    }
    // weight beyond every support's edge: all of it on the support nearest the side it leans to
    let k = 0; for (let i = 1; i < sup.length; i++) if (Math.abs(sup[i].c - xbar) < Math.abs(sup[k].c - xbar)) k = i;
    f = sup.map(() => 0); f[k] = W; return f;
  }
  function traceLoads(withHeld = false) {
    const info = new Map();
    const add = (b) => info.set(b, { W: b.getMass() * GRAVITY, M: b.getMass() * GRAVITY * b.getWorldCenter().x, recv: 0, sup: [], y: b.getWorldCenter().y });
    for (const p of pieces) if (!p.ghost && !p.auto && (withHeld || p.heldBy == null)) add(p.body);
    for (const l of loads) if (l.released) add(l.body);
    const wm = new planck.WorldManifold();
    for (let c = world.getContactList(); c; c = c.getNext()) {
      if (!c.isTouching()) continue;
      const A = c.getFixtureA().getBody(), B = c.getFixtureB().getBody();
      if (!info.has(A) && !info.has(B)) continue;
      c.getWorldManifold(wm); const n = wm.normal; // from A to B
      if (Math.abs(n.y) < SUPPORT_NY) continue;
      const up = n.y > 0 ? B : A, low = up === A ? B : A, iu = info.get(up);
      if (!iu) continue;
      // where it rests: the width the two pieces share (a tiny tilt leaves the physics only one corner touching,
      // which must not move the weight); the touching points when they share no width (a corner on a face)
      const ba = c.getFixtureA().getAABB(0), bb = c.getFixtureB().getAABB(0);
      let x0 = Math.max(ba.lowerBound.x, bb.lowerBound.x), x1 = Math.min(ba.upperBound.x, bb.upperBound.x);
      if (x1 - x0 < 0.05) { x0 = Infinity; x1 = -Infinity; for (let i = 0; i < c.getManifold().pointCount; i++) { x0 = Math.min(x0, wm.points[i].x); x1 = Math.max(x1, wm.points[i].x); } }
      if (x0 > x1) continue;
      iu.sup.push({ low, c: (x0 + x1) / 2, w: Math.max(0.05, x1 - x0) });
    }
    for (const [, it] of [...info].sort((a, b) => b[1].y - a[1].y)) {
      if (!it.sup.length) continue;
      const W = it.W + it.recv, f = shareWeight(W, it.M / W, it.sup);
      it.sup.forEach((s, i) => { const il = info.get(s.low); if (il) { il.recv += f[i]; il.M += f[i] * s.c; } });
    }
    return info;
  }

