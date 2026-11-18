  // tools/physics/contact.js -- contacts: how fast two bodies were closing when they touched (a real knock, not the weight of
  // a resting stack), and a body's weight counted in its material's regular block.
  // The game provides: onWorld(event, fn) (the world's events, kept when the world is made fresh), MATERIALS ({density}),
  // REGULAR_BLOCK (the piece definition of a material's regular block: {hx, hy}), SKIN_GAP (how much smaller than drawn a piece is).
  // How fast the two bodies were closing at the contact before the solver ran (m/s).
  // A resting stack has ~0 here even though its contact impulse carries the weight of
  // everything above; reading impulse/mass alone mistook that weight for a hit every step.
  function approachSpeed(contact) {
    const bA = contact.getFixtureA().getBody(), bB = contact.getFixtureB().getBody();
    const wm = new planck.WorldManifold(); contact.getWorldManifold(wm);
    let vn = 0;
    for (let i = 0; i < contact.getManifold().pointCount; i++) {
      const p = wm.points[i], va = bA.getLinearVelocityFromWorldPoint(p), vb = bB.getLinearVelocityFromWorldPoint(p);
      vn = Math.max(vn, -((vb.x - va.x) * wm.normal.x + (vb.y - va.y) * wm.normal.y));
    }
    return vn;
  }
  onWorld("pre-solve", (contact) => { contact.tbVn = approachSpeed(contact);  });
  // a body's weight counted in 2 m blocks of its material (a block weighs 1)
  function inBlocks(b, mat) { return b.getMass() / (MATERIALS[mat].density * 4 * (REGULAR_BLOCK.hx - SKIN_GAP) * (REGULAR_BLOCK.hy - SKIN_GAP)); }
