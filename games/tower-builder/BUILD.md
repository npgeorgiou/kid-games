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

## Current state, update 9 (12 Nov 2026; overrides the sections above where they differ)

- Physics shapes 5 mm smaller than drawn (`SKIN_GAP`), so stacks stand where drawn; mudbrick crumbles under four mudbrick and three stone blocks (`CRUSH_FORCE` 515) and sleeping pieces keep their last load verdict; hand ease and carry speed follow each piece's mass. Level changes: see `levels.md`, "Game changes ... second list". Harness: `spec` has test 8 (outline matches the settled build), `shot` saves screenshots before and after the quick build; `LOAD=i:d,...`, `WIND=i:w,...`, `DIAG=1` overrides.

## Current state, update 10 (12 Nov 2026, sixth list; overrides the sections above where they differ)

- Outline = the shape of the building (`make-levels.py`): the build's outer edge (notches narrower than 0.6 m closed with a square, so corners stay sharp), drawn solid, minus the openings each level declares (`holes` in `level(...)`, less what the build's pieces fill); touching openings merge. No more "pockets" or enclosed-gap openings. Openings are never painted red (unfilled painting cuts them out); gaps under 10 cm between pieces are not painted (`SEAM` 0.05). Button: `CHECK.fill` 0.85.
- Hand (`advanceHeldTargets`): while touching, it carries the piece plus the weight resting on it (`weightOnTop`, from last step's contact forces), force `hypot(1.3 x that, push)`, ease and speed by that mass; above `HAND_MAX_WEIGHT` (two stone blocks, 200 N) it cannot lift. Free-air hold unchanged; the sidebar pile hand unchanged (a buried pile piece still comes out).
- Same result every time: `freshWorld()` makes a new physics world at level start, quick build, test start and restore. At test start the building first settles until every piece sleeps, then the pieces are put back to the millimetre in a fixed order. Cause found by test: the physics world kept the history of earlier builds and the test began while pieces were still settling.
- Wood: a piece lying flat presses along the whole shared face (8 points), so weight over a gap bends wood (the wooden lintel now snaps).
- Finished sites: `syncSite` saves a finished site as it is when left (`goMap`) and marks it `broken` when its headpiece is out of place or gone (`headpieceOut`); broken = red see-through circle with the site as it is, no visitors (`siteFinished`), enterable; passing the test again fixes it. Re-entering a finished site always rebuilds it from its save (the headpiece was lost when re-entering the same site right after the test). After a pass the headpiece stays (`finishTest(true)`).
- ΕΠΑΝΕΚΚΙΝΗΣΗ button bottom-left on the map (`restartButton`, `restartAll`): progress, saved game, boats, travellers back to the start.
- Music: unchanged in effect (starts at load when the browser allows it, otherwise at the first touch); now also listens for a touch or key anywhere on the page.
- Levels (see `levels.md`): pile rule for every wrong choice; Lion Gate 3 wooden planks and more mudbrick, wrong build now "one jamb left out"; Ishtar towers one course taller with a headpiece each, stone only in their two lowest courses, load density 23.5; Mausoleum lintels end to end, roof a square narrower each side, top two triangles gone, acroteria moved in with the lintel ends, wrong choices mudbrick core, mudbrick columns, one column left out; Djoser load density 33 (was 42, so the build holds 30% more).
- Harness: `python3 tools/harness.py owner [hand mudbrick repeat margin reenter site button red restart music]` (tests in `tools/owner-tests.js`); `spec` test 3 counts a wrong choice only if it fails by physics and does not end as a ready, passing building; test 4 checks the pile rule for every wrong choice; test 8 requires 85% covered.

## Current state, update 11 (12 Nov 2026, seventh and eighth lists; overrides the sections above where they differ)

- Mudbrick: `CRUSH_FORCE` 445 for a block lying flat (owner: crumbles under 4 mudbricks + 2 stones, 449 N as built; 7 mudbricks, 441 N, hold); the weight on it is read every step from its contacts (`weightOnTop`, also while asleep) and smoothed; limit scales with its drawn width (`crushLimit`); bending over a gap of 30 cm or more (`MUD_SPAN_MIN`, `MUD_SNAP_MOMENT` 10); falls: `MUD_SHATTER_SPEED` 8.3 (whole from 3.5 m, broken from 4 m; was 2.75 m). Wood and mudbrick supports for bending are the full stretch they lie over.
- Carrying by weight compared with a stone block (`CARRY_REF_MASS`, `CARRY_EASE` 0.1 s, `CARRY_SPEED` 2.7 m/s; ease x mass ratio, speed / sqrt(mass ratio)), whatever the material.
- The load's last metre is always lowered at 1.2 m/s and set down exactly on what it meets (`LOAD_LAND`, `gapBelow`): the result no longer depends on the screen size (level 3 failed on 1366x768 only).
- Pieces are grabbed only on their real shape (`outsidePiece`), in the building area and the sidebar (triangles were grabbed on the empty half of their box).
- Levels: Lion Gate one course taller; Karnak more mudbrick and wooden planks (wrong choices); Mausoleum two capitals side by side on the core; Pharos top square removed, headpiece a block lying down, three more wrong materials; outline dips shallower than 12 cm filled (arch tops). Load densities 5, 16, 12, 75, 25, 18.3, 60, 12, 13, 14.
- Owner tests added (`harness.py owner fall shape carry triangle screens`); screens runs every level on five screen sizes, plain and 1.3x.
- Open: Djoser suggested build placed roughly crushed its middle bottom mudbrick in 1 of 6 tries (new mudbrick strength); Ziggurat wrong material no longer fails; Valens pile 120%; Mausoleum posts no longer needed. Owner to decide.

## Current state, update 12 (13 Nov 2026, ninth list; overrides the sections above where they differ)

- Mudbrick: `CRUSH_FORCE` 238 for a block lying flat (owner: four mudbricks crumble it, three stones crumble it, separately; three mudbricks or two stones hold). Suggested builds changed so their mudbrick holds with 30% to spare: Djoser stone in the first three layers; Ziggurat lower terrace stone; Ishtar towers stone in the three lowest courses. Load densities 5, 8, 5, 75, 25, 8, 60, 12, 13, 14.
- Hand: every part of its strength goes with the weight held (`HAND_PUSH`, `HAND_LIFT` removed); within 25 cm of another piece it uses the touching strength, so a small piece cannot ram a big one.
- Mausoleum: middle column of two squares with one capital. The posts are still not needed (the lintels hold each other); "posts pulled out early" does not fail and is not a wrong choice.
- Openings where temporary wood stands are drawn as openings (no brown tint); the brown tint stays only for wood courses.
- CLAUDE.md: "Rules for every change (owner, 13 Nov 2026)" written.
- Open: Valens pile 120%; Mausoleum posts not needed; Djoser to be play-tested by the owner.

Tenth list (13 Nov), the owner's own words (verbatim): "Djoser can have 2 bot stone, 3 top mud, yous till dont think clearly, recheck every similar decision you took. FOR FUCKS SAKE, ARE YOU A MORON, NOW STONE MOES LIKE IN SLOW MOTION, AND CANT BE SWUNG IN CIRCLES!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! YOU FUCKING PICE OF SHIT, YOU EXHAUST ME!!!! YOU MADE EVERYHTING HARDER THAN IT SHOULD BE!!!! CAN YOU DO A MIDDLE WAY?"
Done: Djoser two stone layers and three mudbrick layers (headpiece density 8); the same check on the others: Ishtar towers back to two stone and three mudbrick courses (density 4); the Ziggurat keeps its stone lower terrace (with all-mudbrick terraces a roughly placed build crushed a mudbrick under the upper wooden course). Carrying: `CARRY_EASE` 0.07, `CARRY_SPEED` 4.6 (a stone block crosses 4 m in 0.85 s: the light version 0.77, the slow one 1.45; it swings round in circles again, test "10"). Lifting: the too-heavy limit is judged on the weight over the last half second (`wtSlow`), so two stone blocks lift again. Known: a long stone beam held at its end turns only a little in fast circles (probe "whirls beam/stone"; it turned with the old light carrying).

Ninth list, the owner's own words (13 Nov 2026, verbatim):

1. are you fucking stupid? its so clear: ""mudbrick breaks under four mudbrick and three stone blocks," SEPERATELY! NOT COMBINED!!!! sperately!!! I just give you their strength compared to 2 DIFFERENT stacks!!! FIX THAT IDIOT; and test everyhting, and rething anythign this touches, like material choise, adn make that isntar gate headpiece that you amde heaver, make it as it was or at least something thaat breaks excessive mudbrick stacks!!!! moron!!!!  2. Open questions: "Djoser" -> dont know, I have to play test it. "Ziggurat" -> that may change now "Mauseleum" -> no moron, i mean that kionocrana extrude, do there should be 2 of the small oblong pieces as kionocrano, not one that is more narrow than the kionas. also, there are 2 weird brown areas in teh outlien at mausoleum, solve that. and the wooden supports would be needed if the middle column was of half the width??? think of that, I think it can work, and should work. so forget about the double kionocrano ALSO; THE STRENGTH of me holding a small oblong stone piece is excessiove, it rams into big stones and kicks them away,  thats insanely underalistic, something is wrong with how you calculate strength per object mass. AND YES; write down your rules

## Current state, update 13 (13 Nov 2026, eleventh list)

- Lifting off: the hand is weak only when it presses into a piece or is about to hit one while moving towards it (`pressesInto`, `capApproach` toward check); lifting or sliding a piece off what it sits on keeps full strength (it trailed the hand by up to 1 m before).
- Lion Gate back to the lower version; play order Lion Gate (level 4) then Karnak (level 5): owner, "MYCENAI IS EASIER" (the campaign is otherwise chronological). SITES and `TEST_LOAD_DENSITY` swapped with it; the earthquake per position is unchanged.
- Hand tests: `harness.py owner motion` (lift-off stickiness, push, swing, carry) and the hand's feel locked against `tools/motion-ref.json` (recorded 13 Nov from this build; a change of more than 15% fails and needs the owner's yes; re-record only with `record` after he approves).
- `checklist.md`: everything the owner asked to fix, grouped for testing.

Eleventh list, the owner's own words (13 Nov 2026, verbatim): "write test for all thigs related with mouse strength and objects motion, because you are too often changing them and messing them up. WEIRD STICKINESS WHEN i PULL SQUARE FROM TOP OF BLOCK??? actually in all lifts where lifted object A is sitting on object B REVERT MYCENAI TO PREVIOUS LOWER VERSION, AND MOVE EXCHANGE LEVELS BETWEEN MYCENAI AND KARNAK, BECAUSE MYCENAI IS EASIER. I have told you to fix so many things that I lost count. AFTER ALSO FIXING THE ABOVE, compile a list with everything I told you to fix. I will test it against the game. dont fucking miss anything, but group things that can be tested together."

## Current state, update 14 (13 Nov 2026, end of chat)

- The parent key is Ctrl instead of Tab (opens every site, quick build button, fast test). Owner: "change so that tab button is replaced with CTRL. remove all open items. after this this caht is done". Open items dropped from the lists (Valens pile, Mausoleum posts, long stone beam swing, Djoser play-test); nothing is waiting on the owner.

### Seventh and eighth lists: the owner's own words (12 Nov 2026, verbatim)

Seventh list, with a screenshot saved as `owner-shots/list7-item5-mudbrick-column-holds-3-stones.png` (Karnak: an upright mudbrick column holding three stone blocks):

1. give mudbricks less falling brittleness, I want them to be able to fall from extra height equal to the short side of a mudbrick, and not break. only after that height they break. ½basically, i dont know if you can understand me, but now I think that its not height, its force that breaks them, but see if you can reduce their brittleness while still maintaining their "how much can they hold on top of them" rule and test. 2. fucking moron, level 3 just broke twice in a row your suggested build that was autobuilt. 3. whenever you do physics work you mess up the strength/weight feeling. it is now too easy to carry a usual stone piece, should be harder and everything adjusted accordingly to their mass ratio with stone. 4. I dont know how many times to tell you that you must give opportunites for wrong optiosn. haw are you thinkign when see what to give to the user? explain. Karnak needs more mudbricks in the pile, and some long wood planks too. 5.  that AHOULDNT be possible, even more than with the other mudbricks, the regular ones, because it sis obling, and my experience in thsi world tells me this should break with even less than 3 blocks.  ALSO, if places like a lintel, it should break even more easily, so add these paramters to it. pls, you are really tiresome. explain why you cant thing generally, and add PROPER FUCKING instructions to the claude md file, its horrible what is happeling, you need everythign spelled ouy. deliberate with me what your isntructiosn should be so you start thinking. 6. 7. Make mycenai taller by one layer. you still havent compleely removed teh weird intentation in the outline around the arch tops. 8. halicarnassus, add 2 instead of one kionocrano in the middle kionas. 9. pharos should ahve more wrong materials choises.  10. Pharos: remove last square piece, and make headpiece the size of a laying down regular block. that should save some space to make the need to shrink its pieces' size, less.

Eighth list (sent while the seventh was being built):

1. thre is a weird sticky thing going on, at least with the triangular pieces. solve it. ther is also something like an invisible box arounf the triangular pieces, that reacts to holding. 2. are you sure the values I gave you for how many blocks of each material a mudbrick can hold are implemented? I am in the level of gate of ishtar, and a mudbrick holds on it 6 other mudbricks!!!!!!!1 this is extremely infuriating, what the fuck do i have to tell you to make you follwo and not redo and rebreak isntructions? this is not rage, its a question, answer what instructiosn I must give you, moron. I said "mudbrick breaks under four mudbrick and three stone blocks," its clear as crystal. actually, make it under 4 mudbrick and 2 stone. Ok????????????????? I INTERRUPT YOU TO ALO CONSIDER THESE; AND; REALLY DO A GOOD JOB, BUT I THINK YOU DILLY DALLY TOO MUCH, 13 MINS ALREADY YOU WORK ONA  FEW SMALL CAHNGES

Still to agree with the owner: the CLAUDE.md instructions he asked to deliberate (proposal in the reply of 12 Nov; nothing written until he answers).

## Current state, update 15 (13 Nov 2026, map visuals list)

Owner's words: "put halicarnassus in asia minor, now it is in the aegean. make small ripples behind the boat, as if it is sailing in water. make sure the finished monuments on the world map stand on solid land, not water, in all reasonable screen sized, including small laptop sizes. travelers similarly should always stand on land, never on water, and when they stand to see the monument, they should be looking at it, not the other way. also make the spread around the monument a but while they admire it, not remain as a group. also when they are on a boat, currently the stand above the boat, in the boat only their heads should be visible."

- Halicarnassus site moved to the Asia Minor coast (665, 495), in `src/index.html` SITES and `tools/make-map-routes.py`.
- `tools/make-map-routes.py` now exports MAP_LAND (land without sea, straits or lakes); walks keep to it, so nobody walks across the straits any more.
- Finished buildings: placed at the nearest spot to their site where the building's foot is on land, on screen and not over another finished site (`donePlaces`).
- Boats: ripples behind while sailing (SKIN.mapWake); people aboard show only their heads above the boat's side.
- Travellers: get off onto the shore, never on water; at a finished building they spread round it on land, face it, then gather again.
- Test: `python3 tools/harness.py map` (eight screen sizes; buildings and people on land, spread and not clumped).

## Current state, update 16 (13 Nov 2026, map visuals, second list)

Owner's words: "I dont know in what screen you test, but for me halicarnassus is on the Aegean islands still. also, on my sccreen, mycenai and acropolis overlap. nothing should overlap even in big circle size, redive green circle size a bit, without reducing monument preview size. ripples should follow the direction of the back par tof the boat, not be horizontal all the time. fix that, in my screen alexandria is still on the water. and space out egypgs buildings a bit more. travellers spread and collect too rapidly and in and explosive motion, they shoudl slowly circle around the monument to spread, like, trading its perimeter."

- Halicarnassus moved in the game too (update 15 had moved it only in the route tool). Constantinople moved to the European side.
- Every site gets one place per screen size: the big circle wholly on its own land (no islands), on screen, a gap away from all others (`sitePlaces`). Green circle 0.85 of the old size; the building inside unchanged.
- Ripples trail behind the stern along the boat's heading.
- Visitors walk over land at walking speed to the circle, then along it to their place, look, and return the same way (`admireTour`, `landRoutes`).
- Checked by opening the map at 1366x768 and 1920x1080 with all sites finished. `harness.py map` (long run) was not rerun on the last version.

## Current state, update 17 (13 Nov 2026, map water and placement)

- Travellers' feet stay on their spot when they turn (sprites drawn by their feet column, PEOPLE_FEET), no jump.
- Sites by the sea placed first; a site is never moved to another land; only the lower half of the circle (where the building stands) must be on its land. Valens just south of Constantinople (owner) so it is never at the top edge. Pharos on the delta coast.
- Sea: owner's first water picture (`src/art/water.png`, royalty free per owner), 1.5x its size, two frames drifting slowly the same way (owner chose this from test files: frame swapping and the 40-frame OpenGameArt water were rejected).

## Task list

Done (12 Nov 2026, fourth list): stone swings less, wood lighter in the hand. Done (third list): stronger sidebar hand, pieces no longer lost at the sidebar edge, heavy pieces stay in the grip when swung. Done (second list): sidebar fixed, stronger pile hand, into-sidebar keeps motion, less swing, solid thicker ground. Done (first list): 1 sidebar and pieces 1.5x; 2 bottom pile piece lifts easily, no shooting up; 3 piece leaves the sidebar with the same hold and motion; 4 off-centre hold rebuilt as a joint. Next: owner play-test.
Done (12 Nov 2026, levels): all ten levels rebuilt to `levels.md` (approved, headpieces LOCKED in `tools/level-spec.json`); every test there passes (`tools/harness.py spec`, `tools/harness.py real`); picture `levels.png` (`tools/level-pictures.py`). Game changes are listed at the end of `levels.md`. Next: owner play-test and verdict on `levels.png`. Branch `level-proposals` is superseded.
Done (12 Nov 2026, second and third level lists): see `games/tower-builder/levels.md` (levels and game changes). Arches are the standard nine wedges again (wedge trimmed so the arch top is exactly 3 m) with a big triangle sized to sit on the arch flush with its top; levels fill the screen height (only the Lighthouse shrinks); Parthenon columns 2 m apart; Mausoleum one roof layer less; all piles fit the sidebar; every test in levels.md passes. Level 3 quick build: not reproduced. Pre-existing harness failure, not from this work: probe 'whirls beam/wood'.
Fifth list (12 Nov 2026): 1 Pharos three tie courses and one stone course on top, test 8 outline vs build; 2 solid outlines beside arches with thin wedge lines; 3 Valens back to the old design (three piers, course between the tiers, narrow walls); 4 mudbrick breaks under four mudbrick and three stone blocks, Djoser stone only in the first layer; 5 question on the Ziggurat wood (answered); 6 Karnak four identical columns, every pillar a capital of two small blocks; 7 piece weight in the hand. Done, except: Valens pile does not fit the sidebar (120%), waiting for the owner.
Sixth list (12 Nov 2026): owner's 17 items; all decisions below settled; the owner's screenshots are in `owner-shots/` (item06 Lion Gate red doorway, item10 Ishtar dips above the arch, item13 Mausoleum gaps at the roof steps, item15 Pharos line between openings, item17 Valens button lit with the upper tier unfinished): look at each before its item; build every item in one chat, generic fixes only (no per-level patches), each with a harness test that repeats what the owner does by hand.

Ground rules settled with the owner:
- OUTLINE = THE SHAPE OF THE BUILDING, not the union of the suggested build's pieces. Solid everywhere except the building's real openings (doors, arch openings, spaces between columns, the Pharos shaft, windows), which each level declares on purpose in `make-levels.py` and lists in `levels.md`. Seams, slivers, the three-pointed gaps between Valens's triangles and arches, the dips above arches: all inside the solid shape. Remove the "pockets"/union-of-pieces logic; each level's outline is drawn from its silhouette (outer boundary of the build, with notches only where the building's shape has them) minus declared openings. Touching openings are merged into one (Pharos shaft line, item 15). Tests: no two openings touch; every uncovered gap of each suggested build inside the outline is shown and must pass the button rule below; if it does not, the build changes (e.g. pieces that fill the gap), never the rule.
- GREEN BUTTON (owner, 12 Nov): `CHECK.fill` 0.83 -> 0.85 of the outline (the building's shape) covered, other rules unchanged. Openings (doors, arches, ...) are never painted red unless a piece really blocks them (item 6). Test: every suggested build lights it; the owner's Valens screenshot case (upper walls/triangles missing) is checked and reported.
- HAND: pulls with exactly the force the object needs, including everything resting on it; heavier = more lag behind the finger; above a fixed limit (weight of two big stone blocks) it cannot lift. Piece size never matters, only weight. Current bug: while touching, the force is hypot(W, min(m*maxAccel, m*PUSH_ACCEL+HAND_PUSH)) (held-piece tracking, `setMaxForce`), tied to the held piece's own mass. Test: lift every piece type with 0, 1, 2 others stacked on it; result depends only on total weight.
- MUDBRICK: crumbles under 4 mudbricks + 3 stones (or heavier), holds anything lighter. Test: build exactly that stack on one mudbrick with the hand/placement as the owner does, in the game, and the 3+3 stack; not a calculation. `CRUSH_FORCE` is now 515 N but the owner says mudbrick is still too strong in play.
- PHAROS / DETERMINISM: the owner quick-built and tested twice: one run a piece broke in the earthquake, one passed. Cause unknown (physics steps are fixed 1/60 s; settling ends within 1-2 s, so waiting time is probably not it; check pile `Math.random` spawns, Tab 10x step dropping `accumulator = 0`, anything frame-dependent). Test: in the real game loop (requestAnimationFrame, varied frame rates), quick build + test 20 times per level; all results identical; on difference, diff the runs step by step to the first split. Also a safety margin: every suggested build passes with 1.3x quake and 1.3x load.
- FINISHED SITE: stops counting as finished when the check finds a headpiece out of its place; then the map shows the site as it is now, red semi-transparent circle, no visitors, can be entered and fixed.
- MUSIC: browsers allow sound only after a real touch/click (synthetic clicks do not count). Start music at load (works when the PC allows autoplay: Edge `edge://settings/content/mediaAutoplay` -> Allow) and otherwise at the first touch anywhere.
- RESTART (ΕΠΑΝΕΚΚΙΝΗΣΗ) on the main/map screen with a restart symbol: whole map back to the beginning: all sites, travellers/humans, progress.

Items (numbers = the owner's points in his own words below):
1 ΕΠΑΝΕΚΚΙΝΗΣΗ button (above). 2 music (above). 3 hand weight (above). 4 every wrong choice (material and build) must have its material in the pile, in every level; write that rule clearly in `levels.md` and fix all levels (Ziggurat had none for its wrong build). 5 re-entering a level must always show the headpiece (sometimes missing until re-entered several times). 6 red cells: paint only cells that really break a rule (doorway painted red, red seams between pieces; `failingCells` and the "unfilled" painting). 7/8 answered. 9 Lion Gate pile: 3 wooden planks (tempting as the upper door lintel) and more mudbricks. 10 no dips above arches (Ishtar, Valens): follows from the outline rule. 11 Ishtar: towers one layer taller, two more headpieces (same thickness as the roof) lowered onto the towers; stone in the pile exactly enough for the suggested build, more mudbrick than needed to tempt. 12 mudbrick strength (above). 13 Mausoleum: side lintels moved in to meet the roof steps with no notch, roof one small square narrower, the two top triangles removed; add wrong choices beyond the 2 mudbricks (materials in the pile that tempt and fail). 14 determinism (above). 15 Pharos line between openings (above). 16 finished site (above). 17 green button (above).
Done (12 Nov 2026, sixth list): all 17 items; every `owner` test, `spec` (except the Valens pile) and `real` pass; each owner test was seen failing on the old build first, except mudbrick (the hand-placed stacks already behaved as agreed) and music (already started at load or first touch). Open for the owner: the Mausoleum posts are no longer needed now that the lintels meet (keep them or not); the Lion Gate wrong build changed to "one jamb left out".
Still open from list five: the Valens pile does not fit the sidebar (120%); owner to decide.
CLAUDE.md now has "How to speak to the owner"; follow it in every reply.

### Sixth list: the owner's own words (12 Nov 2026, verbatim; this is the authority, the summary above only helps)

Message 1 (21:30), with five screenshots, saved as `owner-shots/item06...`, `item10...`, `item13...`, `item15...`, `item17...`:

1. make in the main screen a button to start again, call it EPANEKKINISH, with an appropriate symbol. 2. fidn a way to make music play as soon as page loads. 3. you ahve a problem with calculating weight: a stone square block can easily be lifted, but 2 stacked small oblong stones, that have together less volume than the square one, cant. fix that globally, and add tests. I cant udnerstand why you fail to fix that. 4. in level 3, no material is given for wrong (that break) building options (it is in your instructions to do so, if its not clear make it clear, and add that to every level. 5. reentering a level should keep the headpiece there always, sometimes I ahve to go in and out a few times to see it there. 6.  the red at the door is wrong, fix globally 7. what is the coverage needed so the green button lights up? 8. what are the requirements so that the test succeed, what is counted? 9. same as for point 3, in mycenail, give 3 wooden planks so user is tempted to use it for upper door frame. and more mudbricks. 10. lvl 6, there is no reason for these 2 outline indentations above the arch, same exists in last level. 11. gate of ishtar, make the towers require one more layer, and have 2 headpieces, same thickness as the existing one, fall on them. you should ahve enough stone to make everything sustean the headpieces, but just enouhg, so thre must be MORE mudbricks than necessary to tempt user to use it. 12. you have messed up the mudbrick strength, read again my previous message, you made them too strong. add a test for the strength I told you in the previous message. you tire me so much, why are you missing things? answer. 13. at halicarnassus, I dont like these gaps: . I want you to bring the lintels closer so that they match, and remove a squere's (half block) width from the roof, and remove the 2 uppermost triagle pieces. also, you ahve randomly 2 mudbricks there, same as point 3, is thre really a wrong choise for the user other than these 2? if not, do something, add soemthing, or materials, to amke wrong choises possible 14. In my test, Pharos, at the earhquake, with your quick built, had a stone break, and the test failed. secont test, again your build, passed. you have some unpredictability in your physics code, fix it. that VERY crucial. 15. also, on Pharo,s what is this fucking horizondal random line in the outline? fix it. look, you were supposed to ahve tests for this shit. you tire me. 16. when I shovel a site, or in any way modify it, it shoud show like that, in its current state, in the world map, and a site that is considered not complete anymore does not get visitors,nothing, and does not ahve green circle, but the same semitransparent red circle, can be revisited to be fixed. 17. how the hell is the green button still lit? there is something wrong here.

("my previous message" in point 12 is: "I can stack 5 mudbricks and 3 stones on top of a mudbrick, and it doesn't break, so why exactly do you think in your designs that its a brittle and wrong material? mudbricks should break at a weight of 4 mudbricks and 3 stones")

Answers in the following messages (verbatim):
- Restart: "Yes, all map, of course also remove humans, all as it was in teh beginning."
- Music: "I disagree, youtube doesnt and many otehr websited just play music without me clicking." / "cant you make a click with code?" (answered: no, browsers ignore code-made clicks for sound; the PC setting Edge `edge://settings/content/mediaAutoplay` -> Allow makes it play at load)
- Finished site (point 16): "a check that makes the headpiece(s) count as outside their position."
- Halicarnassus (point 13): "yes, and make the roof a but less wide." (to: move the side lintels in to meet the roof steps with no notch)
- Lifting (point 3): "I have a lot of strength, but only use the one needed for the job. the strength should be the one needed to lift the object in question, and if that object is heavy because stuff are on it, OK, then thats it. generall heavyness is indicated by lag, and, above a limit, to not being able to lift at all." (agreed limit: the weight of two big stone blocks)
- Pharos (point 14): "no, they didnt start from different towers, both were autobuilt by you" / "how long can this settle take? seconds? I find that unlikely." (cause unknown; must be found)
- Rules: "no patches. only general rules"
- Outline: "THE OUTLINE IS NOT THE SUGGESTED BUILD PIEVCES, THAT HOW YOU LEFT THE FUCKING HOLES I TOLD YOU TO FIC IN THE FIRST EMSSAGE ... THE OUTLINE SI THE FUCKING SHAPE OF THE BUILDING"
- Green button (points 7, 17): "raise it to 85%. and make sure gaps like doors adn arches are not apointed red, as its already lsisted as an item."
- How to speak: "add in claude.md instructions about how to speak to a human" (done)

When the owner sends a numbered fix list: copy it here as the task list, then build all of it in that chat (rules in the root `CLAUDE.md`).
