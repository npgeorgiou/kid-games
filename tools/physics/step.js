  // tools/physics/step.js -- the steady clock: the world moves in fixed steps of STEP s, whatever the screen's frame rate.
  // Shared by every game (included inside the game's script by its build). The game provides: world (a planck World).
  // The game adds its own per-step work in order: physicsBefore.push(fn) (before the world moves) and physicsAfter.push(fn) (after).
  // damp(body, vLin, vAng, k): nearly still bodies lose the last of their speed, so they stop trembling and fall asleep.
  const STEP = 1 / 60;
  const MAX_STEPS = 5;
  let accumulator = 0;
  let lastTime = null;
  const physicsBefore = [], physicsAfter = []; // the game adds its own work for each step: before the world moves, and after
  function stepPhysics(dtSeconds, maxSteps = MAX_STEPS) {
    accumulator += dtSeconds;
    let steps = 0;
    while (accumulator >= STEP && steps < maxSteps) {
      for (const f of physicsBefore) f(STEP);
      world.step(STEP, 10, 5);
      for (const f of physicsAfter) f(STEP);
      accumulator -= STEP;
      steps++;
    }
    if (steps === maxSteps) accumulator = 0;
  }
  // Pieces that are nearly still lose the last of their speed quickly, so contact noise
  // cannot keep them trembling or knocking each other in a loop, and they fall asleep.
  // Faster motion (falling, tipping, sliding) is untouched. Written into the velocity
  // directly: planck's setters would wake the body and stop it ever sleeping.
  function damp(b, vLin, vAng, k) {
    if (!b.isAwake() || !b.isDynamic()) return;
    const v = b.m_linearVelocity;
    if (Math.hypot(v.x, v.y) < vLin && Math.abs(b.m_angularVelocity) < vAng) { v.x *= k; v.y *= k; b.m_angularVelocity *= k; }
  }
