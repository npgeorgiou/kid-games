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
| wedge | trapezoid, narrow end down | 0.6 bottom, 0.9 top, 1.0 high (fits an arch of inner radius about 2) |

The sidebar shows five large buttons: block, column, beam, drum, wedge, each in one orientation. There is no rotate control. Pieces are unlimited. A seventh button, with a broom icon, removes every piece on press (not drag).

## Materials (new, decided after the first child test)

Two material buttons sit above the sidebar, wood and stone. The selected material applies to every piece spawned after it's picked.

| Material | Density | Friction | Restitution | Carry speed cap (m/s) | Spin cap while held (rad/s) |
|---|---|---|---|---|---|
| wood | 1.1 | 0.5 | 0.015 | 9 | 3.0 |
| stone | 5.0 | 0.6 | 0.0 | 6 | 1.3 |

The carry-speed and spin caps are what make the weight felt in the hand (see Hands below) — they are not just density for the physics engine.

## Physics

- `new planck.World({ gravity: planck.Vec2(0, -10) })`.
- Ground: static box, top at y = 0, wider than the screen. No side walls.
- Friction and restitution per material (table above), close to real wood and dry stone; ground friction 0.8. Hand acceleration cap: wood 30, stone 22 m/s^2.
- Fixed step: accumulate real time and call `world.step(1/60, 8, 3)` per 1/60 s, at most 5 steps per frame.
- A piece whose centre goes more than 3 m outside the screen sideways, or below y = -5, is removed.

## Hands

Pointer Events only: `pointerdown`, `pointermove`, `pointerup`, `pointercancel`. Mouse and touch must behave the same. Nothing depends on hover, right-click, keyboard or two fingers. Call `setPointerCapture` on press.

- Press a sidebar piece button: a new piece spawns right at the sidebar edge, at the height of the pressed button, already held. Nothing appears elsewhere first.
- Press a piece already in the building area: pick it up.
- Grabbing the middle third of a piece (by each half-extent, or radius for the drum) is the balance zone: no tilt, carried through its centre.
- Grabbing outside the balance zone: a lever grab, carried through the real grab point, so it tilts.
- One holding mechanism, a limited force (decided after the second round of fixes): each physics tick an impulse pushes the grab point towards the pointer, with the speed capped by the material's carry-speed cap and braking so it stops on target, the horizontal and upward push capped by the material's hand acceleration, plus the piece's own weight carried. The drive adds the pointer's own smoothed velocity, so the piece follows curves and circles. In free air the hand can pull down as hard as it pushes; while touching another piece it never presses down, so a piece pressed onto another rests there with its own weight only. Lifting is capped at the piece's weight plus a fixed hand strength of 350 N, so a piece with others on top lifts slower and slower, and stalls (a stone block lifts with three on top, slowly, not with four). While the held piece touches another piece the push cap drops to 0.8 x its own weight, so whatever it pushes resists by its own mass. The grab point stays under the finger. Centre grab: the impulse goes through the centre and a limited torque holds the pick-up angle. Lever grab: the impulse goes through the grab point, so it tilts. The target is computed from the piece's actual position each tick, never from raw pointer bursts.
- Release or `pointercancel`: the hand lets go; the piece keeps its velocity, so it can be thrown.
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

Defaults: flat warm stone colours with a darker outline, pale sky, sandy ground. The drum gets one line across it so its rolling is visible. Wood shows only grain stripes, running along the long side. Impacts, spread along the whole contact edge: dust where a piece hits the ground, stone chips where stone hits stone, nothing for wood on wood or wood on stone; a small screen shake when heavy stone makes dust or chips, and call `playSound("thud-wood"|"thud-stone", strength)` (plays `<audio id="snd-...">` if present). A held piece is drawn slightly lighter. Game code never draws directly and never reads sizes from the skin.

## Done when

- `node games/tower-builder/stack-test.js` exits 0.
- `python3 games/tower-builder/build.py` produces `tower-builder.html` and it opens by double-click with no console errors.
- In a browser: every pile button gives a piece; pieces stack, wobble and topple; a 6-block tower stands still; a held piece pushes others; dropping on the pile removes; the broom clears; resizing the window keeps everything usable.
- Check it once in the browser yourself before reporting. If stacks jitter, raise the iteration counts in `world.step`; if that fails, report it. Do not switch library without asking.

## Finish

Commit `src/index.html` and `tower-builder.html`, push, give `tower-builder.html` as the download, and set the Status section of the root `CLAUDE.md` to "Tower Builder prototype built, waiting for the test with the child".

## World map (new)

The page opens on a world map (Mediterranean and Middle East, coastline from `lib/map-land.js`, Natural Earth, see `lib/MAP-DATA-LICENSE.txt`). Ten site markers in chronological level order (`SITES` in the MAP section), placed approximately and nudged apart where close. Map crop 18-47.6E, 24.8-44N. Locked: pale dashed circle. Open (first level, or the one after a finished one): solid bright circle, tap to play. Finished: the player's own building drawn small inside the circle. Parent override: hold the map's top-left corner three seconds to open every site (again to re-lock; not saved). A big button bottom-right opens free play; a folded-map button in the sidebar returns to the map. Physics is paused on the map.

## Levels data (new)

`src/levels.js` (loaded by `src/index.html`, inlined by `build.py`) holds `LEVELS`, the ten levels in play order: Greek name, date, the new demand, outline (solid rings minus holes), load lowered in the test, wood zones (`woodRole` 'support' = pulled out before the test, 'courses' = stays in). Generated by a script from piece-sized shapes.

## Levels (built)

Code: SECTION LEVELS in `src/index.html`. All its numbers are placeholders to tune by play (`CHECK`, `TEST_WIND`, `TEST_LOAD_DENSITY`, `TEST_QUAKE`, `PHASE_TIME`).

- A level zooms out so the outline plus the load's drop fits the height; the visible world may then be wider than 16 m (level stays centred on x = 8).
- Shown while building: the outline (pale fill, dashed edge), openings in sky colour, wood zones in brown, the load's place as a dashed ghost.
- Check, every 0.25 s on a 0.1 m grid: outline at least 80% covered, at most 5 cells more than 0.5 m outside it, openings at most 5% blocked (wood allowed in them on 'support' levels), 'courses' zones at least 60% wood. The green wind button in the sidebar is grey until the check passes.
- Test (no touching meanwhile; the map button aborts and puts the pieces back): wooden supports in wood zones or openings pulled out one by one ('support' levels), wind from the left (each 0.1 m band of height pushes the first thing it meets), the load lowered from 2 m above until it touches, earthquake (the ground slides back and forth), settle.
- Pass: outline still 70% covered and every load within 0.6 m and 0.35 rad of its place. Petals, `playSound("cheer")`, then back to the map with the building saved (localStorage `tower-builder-progress-v1`). Fail: watch it fall, then the pieces return to where they were before the test.
- Sound hooks: `wind`, `quake`, `cheer`.
- Not built: optional goals (fewer pieces, taller).
