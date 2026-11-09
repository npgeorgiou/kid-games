// Physics check, no browser: node games/tower-builder/stack-test.js
// Stacks N blocks, lets them settle 3 s, then fails if the top block moves during the next 27 s.
const pl = require('./lib/planck.min.js');
const N = 10, HW = 1.0, HH = 0.5;
const world = new pl.World({ gravity: pl.Vec2(0, -10) });
world.createBody().createFixture({ shape: pl.Box(20, 0.5, pl.Vec2(0, -0.5), 0), friction: 0.8 });
let top;
for (let i = 0; i < N; i++) {
  top = world.createBody({ type: 'dynamic', position: pl.Vec2(0, HH + i * 2 * HH) });
  top.createFixture({ shape: pl.Box(HW, HH), density: 2, friction: 0.8, restitution: 0 });
}
for (let i = 0; i < 3 * 60; i++) world.step(1 / 60, 8, 3);
const start = top.getPosition().clone();
for (let i = 0; i < 27 * 60; i++) world.step(1 / 60, 8, 3);
const p = top.getPosition();
const drift = Math.hypot(p.x - start.x, p.y - start.y), tilt = Math.abs(top.getAngle());
console.log(`drift ${drift.toFixed(4)} m, tilt ${tilt.toFixed(4)} rad`);
process.exit(drift < 0.02 && tilt < 0.01 ? 0 : 1);
