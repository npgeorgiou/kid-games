# Tower Builder: prototype build instructions

Read this file and `design.md` (same folder). Nothing else is needed. Do not read `docs/brief.txt`.

## What to build

One page where you drag stone pieces from a pile and stack them with real physics. Free play only. It exists to answer four questions with the child: is stacking and toppling fun with no goal, can they place a piece where they mean to (touch and mouse), do they see why things fall, do they ask to go again.

Not in the prototype: building jobs, levels, test button, wind, statue, win or lose, saving, sound, text, menus, library page, final art. Do not add them.

## Files

- `src/index.html`: the source you write. Loads `../lib/planck.min.js` with a plain `<script src>` (not a module) so it opens by double-click. All CSS and JS inline in this file.
- `build.py`: already written. `python3 games/tower-builder/build.py` writes `tower-builder.html`, the single self-contained file, with the library inlined.
- `lib/planck.min.js`: Planck.js 1.4.2, MIT (licence text alongside). Global `planck`.
- `stack-test.js`: `node games/tower-builder/stack-test.js` checks a 10-block stack stays still. It passes with the settings below.

## Screen

- One full-window `<canvas>`. Landscape, any size. Redo the layout on `resize`.
- The world is 16 m wide. Scale = building-area width / 16. Ground top is at world y = 0. Draw with y up.
- The tray is a sidebar on the right, not a bottom strip. The building area is everything to its left.
- `touch-action: none` and `user-select: none` on the page. Use `devicePixelRatio` for a sharp canvas.

## Pieces

Sizes are placeholders to be tuned by feel; they are not design decisions.

| Name | Shape | Size (m) |
|---|---|---|
| block | box | 2.0 x 1.0 |
| column | box | 0.6 x 2.4 |
| beam | box | 3.2 x 0.5 |
| drum | circle | radius 0.6 |

The sidebar shows six large buttons: block, block on end, column, column lying down, beam, drum. "On end" and "lying down" are the same piece spawned turned 90 degrees. There is no rotate control. Pieces are unlimited. A seventh button, with a broom icon, removes every piece on press (not drag).

## Materials (new, decided after the first child test)

Two material buttons sit above the sidebar, wood and stone. The selected material applies to every piece spawned after it's picked.

| Material | Density | Friction | Restitution | Carry speed cap (m/s) | Spin cap while held (rad/s) |
|---|---|---|---|---|---|
| wood | 0.75 | 1.45 | 0.015 | 11 | 3.0 |
| stone | 3.6 | 1.10 | 0.0 | 6 | 1.3 |

The carry-speed and spin caps are what make the weight felt in the hand (see Hands below) — they are not just density for the physics engine.

## Physics

- `new planck.World({ gravity: planck.Vec2(0, -10) })`.
- Ground: static box, top at y = 0, wider than the screen. No side walls.
- Every piece: friction 0.8, restitution 0.
- Fixed step: accumulate real time and call `world.step(1/60, 8, 3)` per 1/60 s, at most 5 steps per frame.
- A piece whose centre goes more than 3 m outside the screen sideways, or below y = -5, is removed.

## Hands

Pointer Events only: `pointerdown`, `pointermove`, `pointerup`, `pointercancel`. Mouse and touch must behave the same. Nothing depends on hover, right-click, keyboard or two fingers. Call `setPointerCapture` on press.

- Press a sidebar piece button: a new piece spawns right at the sidebar edge, at the height of the pressed button, already held. Nothing appears elsewhere first.
- Press a piece already in the building area: pick it up.
- Grabbing the middle third of a piece (by each half-extent, or radius for the drum) is the balance zone: no tilt, carried through its centre.
- Grabbing outside the balance zone: a lever grab, carried through the real grab point, so it tilts.
- Two different holding mechanisms, by grab zone (new, decided after the first child test — the straightforward single mechanism did not give a direct, weighted feel):
  - Balance-zone (centre) grab: kinematic control. Every physics tick, set the piece's velocity directly from the gap between its current position and the pointer's target, capped at the material's carry-speed cap, and force angular velocity to zero. This is what makes the piece track the hand exactly with no lag, no sliding start, and no drift when the hand stops — there is no spring here to sag or overshoot.
  - Lever grab: a `planck.MouseJoint` at the grab point (`maxForce` = 600 x mass, `frequencyHz` 9, `dampingRatio` 0.9), target advanced each tick but clamped to the material's carry-speed cap so a fast drag can't punch the piece through others. This is what lets it tilt.
  - Either way, the per-tick target advance is clamped using the piece's actual current position, not raw pointer events — a burst of pointer events coalesced into one frame must not move the target further than one tick's cap allows, or a fast drag can tunnel a piece through a wall or another piece.
- Release or `pointercancel`: end whichever control mode was active, and cap the piece's speed at 3 m/s so a flick cannot launch it.
- Release over the sidebar: the piece is removed.
- Several pointers at once each hold their own piece.
- Picking targets in the building area are generous: test the pointer against each piece grown by 0.12 m.

## Drawing

All drawing goes through one `SKIN` object so art can be replaced later without touching game code:

```js
const SKIN = {
  background(ctx, w, h) {},          // whole building area, pixels
  ground(ctx, w, h) {},
  pile(ctx, w, h) {},
  piece: {                           // drawn centred at origin, already rotated and scaled to metres
    block(ctx, w, h) {}, column(ctx, w, h) {}, beam(ctx, w, h) {}, drum(ctx, r) {},
  },
  button(ctx, name, x, y, size, pressed) {},
};
```

Defaults: flat warm stone colours with a darker outline, pale sky, sandy ground. The drum gets one line across it so its rolling is visible. A held piece is drawn slightly lighter. Game code never draws directly and never reads sizes from the skin.

## Done when

- `node games/tower-builder/stack-test.js` exits 0.
- `python3 games/tower-builder/build.py` produces `tower-builder.html` and it opens by double-click with no console errors.
- In a browser: every pile button gives a piece; pieces stack, wobble and topple; a 6-block tower stands still; a held piece pushes others; dropping on the pile removes; the broom clears; resizing the window keeps everything usable.
- Check it once in the browser yourself before reporting. If stacks jitter, raise the iteration counts in `world.step`; if that fails, report it. Do not switch library without asking.

## Finish

Commit `src/index.html` and `tower-builder.html`, push, give `tower-builder.html` as the download, and set the Status section of the root `CLAUDE.md` to "Tower Builder prototype built, waiting for the test with the child".
