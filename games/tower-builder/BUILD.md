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

The page opens on a world map (owner-supplied picture `src/art/map.jpg`, filling the screen, crop centred on the sites; a few boats `src/art/boat.png` sail slowly between shores). Ten site markers in chronological level order (`SITES` in the MAP section), placed by eye in map-picture pixels and nudged apart where close. Locked: pale dashed circle. Open (first level, or the one after a finished one): solid bright circle, tap to play. Finished: the player's own building drawn small inside the circle. Parent override: hold the map's top-left corner three seconds to open every site (again to re-lock; not saved). A big button bottom-right opens free play; a folded-map button in the sidebar returns to the map. Physics is paused on the map.

## Levels data (new)

`src/levels.js` (loaded by `src/index.html`, inlined by `build.py`) holds `LEVELS`, the ten levels in play order: Greek name, date, the new demand, outline (solid rings minus holes), load lowered in the test, wood zones (`woodRole` 'support' = pulled out before the test, 'courses' = stays in). Generated by a script from piece-sized shapes.

## Levels (built)

Code: SECTIONs BREAKING, PILE and LEVELS in `src/index.html`. Their numbers are placeholders to tune by play (`CRUSH_FORCE`, `SNAP_MOMENT`, `CHECK`, `TEST_WIND`, `TEST_LOAD_DENSITY`, `TEST_QUAKE`, `PHASE_TIME`, `LEVEL_STOCK`).

- Materials: wood, mudbrick, stone (free play has three material buttons). Mudbrick: if the force pressing down on it stays above `CRUSH_FORCE` (320 N: three stone blocks hold, four crush) for 0.5 s it cracks, then crumbles to dust and is removed. Wood boxes: contacts are split into supports (pushing up) and loads (pushing down) along the long side; a load over a gap adds P x gap / 4, beyond the last support P x distance; over `SNAP_MOMENT` (80 N m: one stone block over a gap holds, two snap) for 0.25 s it cracks and snaps into two halves (`*-half` pieces, which do not snap again). Sound hooks `crumble`, `snap`.
- Pile: in levels the sidebar is a row of map, broom and test buttons over a bin. `LEVEL_STOCK` fills the bin as a separate physics world, drawn small; pressing a piece takes it out at full size at the sidebar edge; letting go over the sidebar returns it; the broom returns all pieces.
- A level zooms out so the outline plus the load's drop fits the height; the visible world may then be wider than 16 m (level stays centred on x = 8).
- Shown while building: the outline, openings in sky colour, wood zones in brown, the load's place as a dashed ghost.
- Ready check, every 0.25 s on a 0.1 m grid: outline at least 85% covered, at most 5 cells more than 0.5 m outside it, openings at most 3% blocked (wood allowed in them on 'support' levels), 'courses' zones at least 60% wood. Pressing the grey button paints the failing cells red for 2 s (sound hook `not-ready`).
- Test (no touching meanwhile; the map button aborts and puts the pieces back): supports pulled out ('support' levels), settle, check; wind from the left (each 0.1 m band pushes the first thing it meets), settle, check; load lowered until it touches, settle, check; earthquake, settle, check. A check needs 80% of the outline covered and every load within 0.6 m and 0.35 rad of its place. The first failed check stops the test: missing cells red, a misplaced load and its place red, then after 3 s the pieces return (sound hook `fail`). All checks passed: petals, `cheer`, saved, back to the map.
- Verified in the browser: level 1 mudbrick passes, wooden blocks fail at the wind; level 2 passes with stone low and mudbrick high, crumbles with stone on top of mudbrick. Levels 3-10 untested: stock and wind may need tuning.
- Not built: optional goals (fewer pieces, taller).

## Current state (11 Nov 2026, handoff; overrides earlier sections where they differ)

Next chat: read this section first. The owner play-tests and sends numbered fix lists; build them all, push, give `tower-builder.html`.

- Files: `src/index.html` (code), `src/levels.js` (outlines), `src/sounds/*.mp3` (owner sounds, loudness-matched, re-encoded), `src/art/map.jpg` + `src/art/boat.png` (owner art). `build.py` inlines scripts and embeds every `"sounds/…"` / `"art/…"` string as a data URI. Tool: `tools/normalize-sounds.php` (ffmpeg two-pass loudnorm). The old coastline map data was removed.
- Sound: Web Audio (`SOUNDS` table in SECTION FEEL: name -> files with per-file volume, set by ear). Hits per material pair (`hit-<a>-<b>`, ground first), `crumble`, `snap`, `wind` (loops through the wind test), `quake` (cut at the end), `drumroll` (while the load is lowered), `cheer`, `fail`, sliding loops `drag-stone` / `drag-wood`, music `music-map` / `music-level`. Sidebar pile hits at half volume, silent for 1.5 s after the pile is filled. Audio is started at load; browsers may hold it until the first click or key. `collapse.mp3` is unused.
- Map: picture fills the screen, crop centred on the sites; `SITES` in map-picture pixels; finished sites drawn 1.6x; markers kept on screen; five boats (`BOAT_ROUTES`) sail at 20 px/s and rest 3 s in port.
- Overrides: hold the map's top-left corner 3 s (toggle all sites); hold Tab (stays on 3 s after release, touchpads ignore clicks while a key is down): all sites open and the test button runs even when not ready.
- Hands: hand force while touching another piece = 0.8 x own weight + `HAND_PUSH` 120 N (a mudbrick shoves another along the ground, stone slowly). Within `NEAR_GAP` 0.25 m of another piece or the load the held piece moves at most `NEAR_SPEED` 1.5 m/s. Off-centre grabs use the effective mass at the grab point (no trembling), angular damping 1, spin cap `LEVER_SPIN` 5 rad/s. Middle zone across the short side of a long piece is 80% of its width.
- Pile: pieces sorted stone, wood, mudbrick from the bottom. Held in the sidebar with a soft pin (mouse joint): grabbed in the middle it keeps its angle, near an end it hangs and swings so it can be turned upright. Dragged past the sidebar edge it becomes the full piece under the finger, held by its centre of mass, see-through and passing through everything until clear (let go while see-through: back to the pile). Dragged into the sidebar it shrinks back, held. Pieces knocked out of the bin drop back in. Broom = start again with the level's full pile. Re-entering a level tidies the pile. Three quick taps on a placed piece return it to the pile (free play: remove it).
- Breaking: mudbrick also crumbles on a hard landing (speed change over 7 m/s in one step); wood also snaps on impact (energy method: moment from the weight W*a*b/L plus sqrt(6*KE*EI/L), `WOOD_EI` 1, hits under 1.5 m/s ignored). Mudbrick hitting any piece sheds crumbs.
- Pieces: wedge 0.7 bottom, 1.05 top, 1.0 high (nine make a half circle of inner radius 2, keystone in the middle). New `centering` (wood half-round form, radius 1.95, flat side down): 1 in the Ishtar pile, 4 in the aqueduct pile; raised on wooden blocks to the springing (2 m Ishtar, 1 m aqueduct). Pieces are drawn y-up (wedge drawn the way its physics shape is).
- Levels: outlines sized to whole blocks (2x1), beams (3.2x0.5) and columns (0.6x2.4); arches and the Parthenon roof triangle cannot be exact. Karnak pile has 2 stone beams.
- Check and test: lying on the floor away from the outline does not count. Red always shows unfilled outline cells as well as the failing rule. Wind: from the left, 1 s lull, from the right; levels 2-10 at 5 N/m (a lone stone column tips at about 7.5). The load (orange) is lowered from above the top of the screen at 1.2 m/s with the drumroll. A failed test puts the building back as it was before the test (verified).
- 11 Nov update: suggested builds `SOLUTIONS` (SECTION LEVELS) for all ten levels; each passes the full test in a headless run (wind, load, stronger quake). The pile is made from them plus `LEVEL_EXTRA` (only the wrong choices a level is about). Quick build: hold Tab, a button appears on top of the pile: everything goes back to the pile, then the suggested build is flown in piece by piece (kinematic, see-through, 30 m/s). New fourth standard size `capital` (1.6 x 0.4, stone): Karnak middle pillars are an upright block plus a capital carrying the side beam and the upper column. Ishtar load narrowed to 7.6 m so it fits between the towers. Valens: suggested build fills 85%, so `CHECK.fill` is now 0.83.
- Check: the load's place must stay clear (`CHECK.loadCells`); ready only after passing for 0.5 s with every piece at rest. Unfilled outline drawn from the real piece shapes (outline minus pieces widened by `SEAM`), not cells. A finished site reopens with its load on top.
- Feel: hand speed capped only towards a piece within `NEAR_GAP` (planck Distance), not along or away; open/closed hand cursor; drumroll rate fitted to the lowering time; slide sound measured at the contact point (tipping is silent); quake 1.6x; pile: hand pin 10 x weight, knocked pieces capped at 4 m/s (2 m/s up), more damping and solver iterations; open sites red on the map.
- Tools: `tools/harness.py` runs every level's suggested build through the full test headless (one line per level: ready, fill, load cells, pass). Extend it in place.
- Not yet play-tested by the owner:- Not yet play-tested by the owner: these changes, levels 4-10, whether the wrong choices fail the way intended (not checked in the browser).

## Task list (owner feedback 11 Nov; do all of it in one chat, in this order)

Owner decisions already made: level checklist below agreed; Parthenon capitals reuse `capital` (1.6 x 0.4); pediment = two new stone right-angled triangle pieces (each half the gable) plus a short flat slab on top; extra ports Corinth and Miletus; villager sprites approved (in repo); wooden supports count as an error in the check.

Level checklist (agreed): looks like the real building, its famous parts actually built (pediment, capitals, acroteria), not left as gaps; one new idea per level, later levels combine known ideas; at least one tempting wrong choice that really fails the test, with the reason visible; nothing left over in the pile except the wrong choices; the load rests on the supports it should, not just the highest point; each level clearly longer than the one before (more pieces, materials, layers); buildable by hand without pixel precision.

A. Feel and test
1. Drumroll length must equal the real descent (today it is sped up far too much on level 1: the timing uses the wrong start or end). If a tall drop would squeeze the clip too much, start the drumroll a little before the load starts moving.
2. Quick build twice as fast (AUTO_SPEED 60) and its material sounds must not lag behind the pieces.
3. With the Tab latch on, the whole test runs 10x faster.
4. Sidebar hand strength: half of what it was before 11 Nov (was 60 x weight, so 30 x weight).
5. A stone held near a top corner swings as if the air holds it back; other materials less so. Find the damping or smoothing in the hold and make heavy pieces swing like heavy pieces.
6. Pile pieces jitter and get stuck hitting each other (start of level 6; also the Valens build during and after the test). Fifth report: reproduce it in the harness first (measure speeds of pieces that should be resting), find the cause, fix it generically for the pile and the building.
7. Wind stronger, and its drawing clearly a strong wind, not a breeze.

B. Check
8. When the load did not land right, only the load's place is red; no other reds then.
9. The load's place everywhere is the load's own shape (triangle at the Lion Gate), not a rectangle.
10. Wooden supports (any wood in an opening/hole or wood zone that the test would pull) count as an error in the check: the monument is not complete while they are there. Show them red like other wrong filling.

C. Levels (apply the checklist to all ten; update SOLUTIONS and LEVEL_EXTRA, run the harness, every suggested build passes and every listed wrong choice fails)
11. Every level has a wrong choice that really fails. Lion Gate: a mudbrick base does not crumble today; keep mudbrick strength fixed, add weight above (heavier stonework) instead.
12. New standard size: half block 1 x 1 (square). Ishtar: rebuild the spandrels beside the arch with it, and the load must also rest on the side pillars, not only on the arch.
13. Parthenon: pediment built (decisions above); capitals on all columns; final pieces = three acroteria, one on each corner and one on the short flat top of the pediment.
14. Mausoleum: centred; suggested build survives the quake (today the mudbrick steps crumble); more complex; final pieces = two corner acroteria plus the big middle piece (chariot).
15. Pharos: harder, fitting its place as level 9.

D. World map
16. Boats use the owner's picture `src/art/boat-owner.jpg` (cut out the white background), at 4/5 of today's size.
17. Boats never cross land.
18. Ten boats, each running between fixed ports: Athens, Crete, Rhodes, Cyrene, Alexandria, Phoenicia, Cyprus, Lycia, one Red Sea port, one Black Sea port, Corinth, Miletus.
19. Ten traveller groups, each the six characters in `src/art/villagers/` (walk and idle strips, 48 px frames; craftpix free licence, `License.txt`). Groups start on boats; when a boat reaches port they get off and walk (boat speed) to a finished site, then on to another finished site by whatever is quicker, walking or waiting for a boat. After at most three sites on foot they must board the next boat and go where it goes.
20. Finished sites on the map: semi-transparent green circles (like the locked yellow ones), not blue.
