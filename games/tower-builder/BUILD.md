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

## Current state, update 2 (11 Nov 2026, evening; overrides the section above where they differ)

The 11 Nov task list (20 items) is fully built and pushed. What changed:

- Levels now come from `tools/make-levels.py` (needs shapely): it holds every suggested build and writes `src/levels.js` with `solution` per level and `LEVEL_PIECES` (pediment halves). Each outline is the union of the build's pieces (wooden supports left out); empty places the pieces enclose (between columns, beside arches) become openings. `SOLUTIONS` in index.html is read from `LEVELS`. Edit builds there and rerun, never by hand.
- New standard sizes: `square` 1 x 1; `gableL` / `gableR`, the two halves of a pediment (right-angled, with a 0.25 m flat tip so the top slab rests on them).
- Levels (pieces): mastaba 12, Djoser 21, ziggurat 23 (stone base, two wood courses), Karnak 25 (platform, outer aisle, stone roof slabs), Lion Gate 27 (taller walls beside a triangle slot, heavy lion slab), Ishtar 38 (square-block spandrels; the load rests on them and the crown), Parthenon 42 (three steps, capitals, architrave, frieze, pediment, three acroteria as the load), Mausoleum 44 (staggered podium, colonnade, four stone roof steps, two corner acroteria and the chariot), Pharos 45 (two staggered square tiers, three columns and a slab, statue), Valens 66.
- Wrong choices (pile extras, `LEVEL_EXTRA`), each checked to fail in the harness: wood top row blows off (mastaba); mudbrick at the bottom crumbles (Djoser, Lion Gate, Parthenon top step, Mausoleum podium, Pharos, Valens piers); stone in wood courses fails the check (ziggurat); mudbrick pillars (Karnak); wooden lintel snaps (Lion Gate); flat stone lintel blocks the arch (Ishtar).
- Check: anything that breaks during the test fails it (its place red). Load not in place: only the load's place is red. Wooden supports left in an opening fail the check (red); the test no longer pulls them; the quick build takes them out at the end. Openings count only 0.15 m in from their edge.
- Test: wind 6.5 N/m (level 1: 110), drawn as long white gusts; Tab latch: the test runs 10x faster (not the pass/fail display). Drumroll: plays at 0.85-1.2x, skips its start when too long, and starts up to 1.5 s before the load moves when the drop is short; it ends when the load lands.
- Feel: quick build 60 m/s with a landing sound per piece; sidebar hand 30 x weight; pieces held off-centre swing with little damping (stone 0.04, mudbrick 0.12, wood 0.25); nearly still pieces (pile and building) lose their last speed quickly so they stop trembling and sleep (not during wind or quake); pile angular damping 3.
- Tall levels zoom out centred (view offset `viewX0`).
- Map: `tools/make-map-routes.py` writes `src/map-routes.js` (ports, ten boat lines kept to open water through the straits, walking paths over land). Owner's boat picture `art/boat-owner.png` (background cut out), 4/5 size. Ten traveller groups of the six villagers ride, walk to finished sites, pick walk or boat by time, and board the next boat after three sites. The Red Sea boat sails to the bottom edge of the map and back (the Red Sea does not reach the other ports). Finished sites: semi-transparent green.
- Harness: `python3 tools/harness.py [levels] [jitter]` prints one line per level and per wrong choice; `jitter` also measures resting speeds.
- Not yet play-tested by the owner: all of the above.

## Current state, update 3 (11 Nov 2026, night; overrides the sections above where they differ)

The owner's second fix list (18 items) is built and pushed. What changed:

- Impacts: sound, dust/chips and wood impact-snapping use the closing speed at the contact (`approachSpeed`, measured in pre-solve) capped by impulse/mass. Before, the steady weight of pieces above was read as a hit: a still pile made thousands of false hits (one bang every 250 ms per piece), now none.
- Sidebar hand pin 60 x weight (was 30): the bottom piece of every pile lifts out (Pharos bottom piece lifted 0.03 m before, 2.5+ m now).
- Held off-centre: grip friction `swingDamping` (wood 6, mudbrick 9, stone 12 per s) applied by the hand before it reads the grab point's speed (as body angular damping it acted after the hand and dragged the piece). Harness swing check (corner held, moved 4 m sideways): stone tilt 1.9 -> 0.8 rad, still swinging 1.9 rad after 3 s -> stopped. The sidebar keeps the old free swing (`PILE_SWING_DAMP`).
- Drumroll: the roll in drumroll.mp3 is 5.5 s (`DRUM_ROLL`), the rest a quiet fade; fitting all 10.3 s skipped the roll's start (level 2 heard only the fade). Now played from its start at 0.9-1.1x; a short drop starts it up to 1.5 s early; a long drop lowers the load faster. Measured in the browser: roll length and start-to-landing agree within 0.1 s.
- Test button: little building with the orange load; yellow fast badge (two arrowheads) while Tab is latched or the test runs 10x. Map: a Tab latch from inside a level no longer shows every site open on return (`tabOnMap`).
- Pile: bigger (largest scale with rows under 80% of the bin), one height and material per row, wedges and triangles nested in up/down pairs, columns lying, round and sloped pieces on top, 240 settle steps before it is shown.
- New piece `tri` (right-angled, short sides 1.5). Lion Gate: relieving triangle of two stone triangles on two wooden triangles (supports, taken out; woodRole "support"); lion slab load on top. Ishtar: a triangle in each corner beside the arch. Valens rebuilt: two tiers of two arches, square piers, a triangle beside every arch shoulder, a full course between tiers.
- Parthenon: four columns at +-1.6, +-4.4 so capitals stand apart; pediment halves (3.7 x 1.0) either side of a square; middle acroterion on the square.
- Outlines: closed over gaps under 0.7 m (make-levels), so no lace of tiny openings.
- Harness: `probe` (pile false hits, bottom lift, held swing), `sizes` (pile hits per screen size). Drop and lead per level printed.
- Open (owner to decide): Lion Gate, Mausoleum and Pharos are too plain (ideas in chat).

## Current state, update 4 (12 Nov 2026; overrides the sections above where they differ)

- Sidebar hand: pin force (60 x own weight + 2 x the whole pile's weight) x g: the most buried piece lifts 4.3-5.7 m in 1.5 s (harness `probe`).
- Off-centre hold in the building area is a firm grip: the hand moves the piece at its centre and sets its spin to turn it towards hanging below the hand at most `SAG_SPIN` 0.8 rad/s. Harness: no tilt when moved sideways (was 0.8 rad). `swingDamping` removed; the sidebar keeps its free swing.
- The load plays `hit-stone-stone` when it lands.
- Every pile uses the same piece size: the largest at which every level's full pile fits the bin (`pileUniform`).
- Grip (supersedes the firm grip above): held off-centre the piece swings freely (grab point held, effective-mass impulse) but the hand's grip cancels spin up to GRIP 2.5 x weight x short side^2 per second: blocks, squares, wedges are carried steady; beams, columns, capitals held at an end hang and can be swung in circles. Sidebar pin doubled again (120 x own weight + 4 x pile weight).
- Pile size: one size `pilePx` = clamp(screen height / 22, 28, 48) px per m; the sidebar widens (up to half the screen) until the level's full pile fits at that size.
- Hand, final (supersedes the grip lines above): held off-centre the piece turns smoothly (no rocking) towards the pull it feels = gravity + the hand's acceleration (smoothed 0.12 s, only the part above 14 m/s^2 counts), at up to 9 rad/s, gain 7/s; the hand moves its centre so the grab point stays under the finger. Lifted by one end it hangs; dragged it stays hanging straight; whirled (about 1 Hz) it goes round like a sling. Harness `probe` prints these as PASS/FAIL tests ("hand").
- Sidebar: the pile bin is `PILE_BIN_W` 6.4 m wide (three blocks and a little); one piece size for every level, the largest at which every level's full pile fits the bin's height (about 25 px/m at 1280x800, 34 at 1920x1080); the sidebar width follows from it.
- Ground: back to the plain strip (the textured ground commit was reverted at the owner's request).
- Level redesign proposals (headpiece = important part, new shapes, history checked) are on branch `level-proposals` (make-levels.py, new piece `abacus`), all passing the harness. Not merged: waiting for the owner's verdict on the pictures.

## Current state, update 5 (12 Nov 2026; overrides the sections above where they differ)

- Sidebar and its pieces 1.5x bigger (`pilePx` x 1.5 after the fit loop), the same in every level: no per-level widening, no shrinking fallback (owner: every level's pile fits; do not change sidebar or piece sizes again).
- Sidebar hand: maxForce (200 x own weight + 8 x pile weight) x g, but the joint target stays within `PILE_LEAD` 1.5 m of the grab point (down only 0.1 m, so pressing into the pile stays gentle) and the held piece's speed is capped (15 m/s, upward 7 m/s): the most buried piece lifts, nothing shoots up.
- Out of the sidebar the piece keeps its grab point (corner stays a corner hold), its spin and its screen speed.
- Hand, final (supersedes all earlier hand lines): a planck MouseJoint at the grab point (5 Hz, damping 0.9; the Box2D testbed drag), solved with the contacts. Its target is the hand, easing to the pointer (0.03 s), capped at the carry speed, within 0.5 m of the grab point, never below it while touching (no pressing down). maxForce = weight + max(m x maxAccel, 350 N) in air; touching: hypot(weight, min(m x maxAccel, 0.8 x weight + 120 N)). Centre grab: limited torque holds the angle. Off-centre: free pendulum plus grip friction (torque 2.5 x inertia about the grab point x spin, capped at 0.25 x weight x arm), so it swings, settles, and a hard whirl goes round. Sling code removed. Harness `probe` "hand" checks hang, whirl, drag-and-settle with a tremble count, and spin kept out of the sidebar.

## Current state, update 6 (12 Nov 2026; overrides the sections above where they differ)

- Sidebar hand: maxForce (400 x own weight + 16 x pile weight) x g, `PILE_LEAD` 3 m; pieces resting on the held one (`carriedByHand`) are exempt from the pile's settling brake and slow cap and get the hand's cap (15 m/s, up 7 m/s). Harness: the bottom piece of every level rises 6-9 m in 1 s.
- Into the sidebar the piece keeps its grab point, spin and screen speed (nudged sideways only as far as needed to be inside the bin).
- Held off-centre in free air a piece weighs 1.8x (`HELD_EXTRA_G` 0.8) and the grip is firmer (`GRIP_DAMP` 4, `GRIP_MAX` 0.4): dragging swings it about 0.3 rad (was 0.5).
- Ground: drawn 24 px thick (`GROUND_PX`), its top at y = 0 (the old 12 px strip covered the bottom of the pieces). Held pieces passed through the ground because the hand joint was attached to the ground body (jointed bodies never collide); it now hangs on `anchorBody`. Ghosts use collision groups (pass through pieces, not ground or walls); their overlap with pieces is measured directly (`overlapsPiece`).

## Current state, update 7 (12 Nov 2026; overrides the sections above where they differ)

- Sidebar hand 1.5x stronger: maxForce (600 x own weight + 24 x pile weight) x g, `PILE_LEAD` 4.5 m, `PILE_LEAD_DOWN` 0.05 m.
- Out of the sidebar the new piece is nudged inside the building area and above the ground (it was born overlapping the wall or ground and thrown out of the world). Harness: a sideways turning beam out and back in at the edge, never lost.
- Hand joint 10 Hz (was 5) and aimed ahead of the hand by 2 x damping / stiffness x hand speed (a spring trails a moving point by that much); in free air its strength is `FREE_AIR_ACCEL` 400 m/s^2 x mass (the lift cap still applies when touching). Whirled pieces stay within 0.13 m of the hand (was 0.7-2.6 m).

## Current state, update 8 (12 Nov 2026; overrides the sections above where they differ)

- Materials feel more different in the hand: wood carry speed 13 m/s (was 9; mudbrick 7.5, stone 6 unchanged); the hand eases to the pointer over `HOLD_SMOOTH` wood 0.015 s, mudbrick 0.03, stone 0.05; stone's grip is firmest (`GRIP_DAMP` 7, `GRIP_MAX` 0.7; wood and mudbrick 4 and 0.4). Dragged by an end: stone block swings 0.22 rad (was 0.31), mudbrick 0.33. Densities unchanged.

## Task list

Done (12 Nov 2026, fourth list): stone swings less, wood lighter in the hand. Done (third list): stronger sidebar hand, pieces no longer lost at the sidebar edge, heavy pieces stay in the grip when swung. Done (second list): sidebar fixed, stronger pile hand, into-sidebar keeps motion, less swing, solid thicker ground. Done (first list): 1 sidebar and pieces 1.5x; 2 bottom pile piece lifts easily, no shooting up; 3 piece leaves the sidebar with the same hold and motion; 4 off-centre hold rebuilt as a joint. Next: owner play-test.
Done (12 Nov 2026, levels): all ten levels rebuilt to `levels.md` (approved, headpieces LOCKED in `tools/level-spec.json`); every test there passes (`tools/harness.py spec`, `tools/harness.py real`); picture `levels.png` (`tools/level-pictures.py`). Game changes are listed at the end of `levels.md`. Next: owner play-test and verdict on `levels.png`. Branch `level-proposals` is superseded.
Done (12 Nov 2026, second and third level lists): see `games/tower-builder/levels.md` (levels and game changes). Arches are the standard nine wedges again (wedge trimmed so the arch top is exactly 3 m) with a big triangle sized to sit on the arch flush with its top; levels fill the screen height (only the Lighthouse shrinks); Parthenon columns 2 m apart; Mausoleum one roof layer less; all piles fit the sidebar; every test in levels.md passes. Level 3 quick build: not reproduced. Pre-existing harness failure, not from this work: probe 'whirls beam/wood'.
When the owner sends a numbered fix list: copy it here as the task list, then build all of it in that chat (rules in the root `CLAUDE.md`).
