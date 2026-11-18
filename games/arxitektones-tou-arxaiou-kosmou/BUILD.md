# Tower Builder: prototype build instructions

Read this file and `design.md` (same folder). Nothing else is needed. Do not read `docs/brief.txt`.

## What to build

One page where you drag stone pieces from a pile and stack them with real physics. Free play only. It exists to answer four questions with the child: is stacking and toppling fun with no goal, can they place a piece where they mean to (touch and mouse), do they see why things fall, do they ask to go again.

Not in the prototype: building jobs, levels, test button, wind, statue, win or lose, saving, sound, text, menus, library page, final art. Do not add them.

## Files

- `src/index.html`: the source you write. Loads `../lib/planck.min.js` with a plain `<script src>` (not a module) so it opens by double-click. All CSS and JS inline in this file.
- `build.py`: already written. `python3 games/arxitektones-tou-arxaiou-kosmou/build.py` writes `arxitektones-tou-arxaiou-kosmou.html`, the single self-contained file, with the library inlined.
- `lib/planck.min.js`: Planck.js 1.4.2, MIT (licence text alongside). Global `planck`.
- `stack-test.js`: `node games/arxitektones-tou-arxaiou-kosmou/stack-test.js` checks a 10-block stack stays still. It passes with the settings below.

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

- `node games/arxitektones-tou-arxaiou-kosmou/stack-test.js` exits 0.
- `python3 games/arxitektones-tou-arxaiou-kosmou/build.py` produces `arxitektones-tou-arxaiou-kosmou.html` and it opens by double-click with no console errors.
- In a browser: every pile button gives a piece; pieces stack, wobble and topple; a 6-block tower stands still; a held piece pushes others; dropping on the pile removes; the broom clears; resizing the window keeps everything usable.
- Check it once in the browser yourself before reporting. If stacks jitter, raise the iteration counts in `world.step`; if that fails, report it. Do not switch library without asking.

## Finish

Commit `src/index.html` and `arxitektones-tou-arxaiou-kosmou.html`, push, give `arxitektones-tou-arxaiou-kosmou.html` as the download, and set the Status section of the root `CLAUDE.md` to "Tower Builder prototype built, waiting for the test with the child".

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

Next chat: read this section first. The owner play-tests and sends numbered fix lists; build them all, push, give `arxitektones-tou-arxaiou-kosmou.html`.

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
- Open: Djoser suggested build placed roughly crushed its middle bottom mudbrick in 1 of 6 tries (new mudbrick strength); Ziggurat wrong material no longer fails. Owner to decide.

## Current state, update 12 (13 Nov 2026, ninth list; overrides the sections above where they differ)

- Mudbrick: `CRUSH_FORCE` 238 for a block lying flat (owner: four mudbricks crumble it, three stones crumble it, separately; three mudbricks or two stones hold). Suggested builds changed so their mudbrick holds with 30% to spare: Djoser stone in the first three layers; Ziggurat lower terrace stone; Ishtar towers stone in the three lowest courses. Load densities 5, 8, 5, 75, 25, 8, 60, 12, 13, 14.
- Hand: every part of its strength goes with the weight held (`HAND_PUSH`, `HAND_LIFT` removed); within 25 cm of another piece it uses the touching strength, so a small piece cannot ram a big one.
- Mausoleum: middle column of two squares with one capital. The posts are still not needed (the lintels hold each other); "posts pulled out early" does not fail and is not a wrong choice.
- Openings where temporary wood stands are drawn as openings (no brown tint); the brown tint stays only for wood courses.
- CLAUDE.md: "Rules for every change (owner, 13 Nov 2026)" written.
- Open: Djoser to be play-tested by the owner.

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

## Current state, update 18 (13 Nov 2026, real textures option)

- Owner's words: "We keep this, and add it as a secong option. in the main menu, add a botton that if its clicked we ll show the real textures as you amde it now, with borders and all, and if its unclicked, which willl be the defaults, we ll have the materials as they were before".
- Map button above ΕΠΑΝΕΚΚΙΝΗΣΗ (a little wall; green ring when on), saved in localStorage "tower-builder-progress-v1-textures", off by default.
- On: owner's seamless pictures in `src/art/tex-*` (recoloured to one warm palette: marble 241,237,229; sandstone 208,162,96; wood 204,148,82; grey stone 170,165,156; mudbrick 152,106,74). Stone per building: sandstone (Mastaba, Djoser, Ur, Karnak, Ishtar), grey (Lion Gate, Valens), white marble (Parthenon, Halicarnassus, Pharos). Stone tiled 3x3 at 2.67 m per picture, mudbrick 5.33 m, wood 1.33 m with grain along the long side; each piece a random place, kept from pile to building. Border: the material's colour at half brightness. Chips take the material's colour.

## Current state, update 19 (13 Nov 2026)

Owner's words: "1. the restart arrow has a weird bulge. 2, change the material toggel icon to have the wood waters horizontally and not vertically. 3, pressing the gree test button SHOULD NOT change the textures. 4. In Ishatar, the tower headpieces should ahve weight equal to 1 stone block, so that if the user has piled 4 mudbricks on top, they then break"

- Restart arrow redrawn (flat ends, head continuing the arc). Textures icon: wood grain lies along the block.
- Each piece keeps its look (seed) through the test, a failed test, saving and re-entering (saved pieces carry the seed as a 6th value).
- `LOAD_WEIGHT`: Ishtar's two tower headpieces weigh one stone block each. Checked at 1280x800, 1366x768, 1920x1080: suggested build (three mudbricks per tower) passes; four mudbricks per tower crumble and fail.

## Current state, update 20 (14 Nov 2026, weight sharing and the ziggurat)

- Weight on mudbrick is traced, not read from the physics contacts (BREAKING: `traceLoads`, `shareWeight`). The solver handed most of a piece's weight to one of its supports (symmetric ziggurat: left middle brick twice the right). Now each piece passes its weight plus what rests on it to the pieces under it, by how much of it lies on each (shared width, from the two pieces' bounding boxes) and to which side it leans, as a stiff piece on springy supports; a wide support also resists turning, so a corner touching beside it takes no false share.
- Ziggurat (owner): all mudbrick, courses staggered, a new 6 m wooden plank (`plank`) under the top terrace; temple a fifth lighter (load density 4); wrong choice: two short beams instead of the plank (fails 100/100, the plank build passes 100/100, also with the temple 20% heavier). No triangle and no stone in this level, for good. Pile: 16 mudbrick blocks, 2 half-blocks, 5 beams, the plank.
- Djoser: top step lighter (load density 7, was 8); pile 2 spare mudbricks, no spare stone; wrong choice mudbrick in the bottom row.
- Safety test (owner tests 14 and 7-2): earthquake and headpiece 20% stronger (was 30%).
- Valens pile not fitting the sidebar: not an issue (owner); test 4 waives it.
- Harness: `variants` (named builds of one level, N placements, what strained each mudbrick; env VARIANTS, NJ, LOAD, TRACE) and `trace` (weight on each mudbrick after the quick build).
- Explored, not built: a 5-row all-mudbrick ziggurat stands only with a plank as wide as the row under every row (12, 10, 8, 6 m); with 6-7 m planks the bottom bricks reach 120-130%. With full-width planks it failed 2 of 10 runs by something moving in the wind or earthquake (cause unknown). Owner kept the current ziggurat.
- Known: owner test "no red seams" on Karnak fails on some runs, also before these changes (cause unknown).

## Current state, update 21 (14 Nov 2026)

Owner's words: "friction when I drag a block upwards and towards another block feels too much. am I wrong? do I not understnand just how much force you are using? / add an undo button that brings building to previous conditions (now, what is a condition? say ideas) / Add in the sandbox the shapes of every shape used in teh game. make sure textures/colors are consisntet (non-textured woods are different from each other). Add also 12 m long planks, stones that are 2x the regular oblong stone, and whatever other you can find. not all materials should ahve all shapes, for example it doesnt make sence to ahve very long oblong mudbricks. find a way to group shapes nicely. / change so that when you succeed a level it doesn't automatically go out to the main screen, you ahve to press button for that."

- Free play: pick a material, the sidebar shows that material's shapes as tiles, grouped one group per row (`SANDBOX_SHAPES`), broom and map at the bottom. Wood: square, block, column, log, beam, plank, new 12 m plank (`longplank`), centering. Mudbrick: square, block, small oblong. Stone: square, block, new 4 m block (`longblock`), small oblong, capital, beam, column, drum, wedge, both triangles, both pediment halves. Long mudbricks left out.
- Without textures every wooden piece has one colour.
- A passed level stays on the building; the map button goes back.
- Harness: `sandbox` (tiles fit at four screen sizes, every shape can be made, a passed level stays).
- Open, waiting for the owner: (a) friction: answered, no change yet; proposal: while the hand pushes a piece against another, it presses sideways only lightly and keeps its full lift. (b) undo: what one step back undoes, owner to choose. (c) Mausoleum's pile has a long mudbrick beam and Karnak's a tall mudbrick column (tempting wrong pieces); keep them in those levels or not. CORRECTED 15 Nov: the Mausoleum pile never had a long mudbrick (this note was wrong); owner: keep Karnak's.
- Known, before this change: `harness.py owner` stops with an error in the map travellers check (also on the previous version).

## Current state, update 22 (14 Nov 2026)

Owner's words: "sandbox: mudbrick add ball. stone add a big square. wood, make teh 12, 9m. Friction: you ahvent changed anything have you? I want you to stop this behaviour, but still be able to push anotehr block with the dragged block without reduction in power. undo: your suggestion numner 1, would that include number 2?"

- Free play: mudbrick ball; stone big square 2 m x 2 m (`bigsquare`); long plank 9 m.
- Dragging up against the side of another piece: the hand lifts at full strength and presses sideways with a separate push of the usual strength; side contacts of a held piece barely rub (`sideRub`, hand code `sidePush`). Pushing along the ground unchanged. Owner test `slide`: a block dragged up and towards a wall of stone blocks rises as far as with no wall (wood, mudbrick, stone).
- Undo: owner chose "the last piece you let go goes back to before you picked it up, with anything that fell or broke because of it" (= the whole building as before that move). Not built yet: waiting for his go.
- The Karnak "red seams" owner test varied between runs because it counted red on screen while the red pulses with the clock; it now measures at one fixed moment and gives the same result every run (passes). The game itself gave the same result for the same placement.
- Known, before this change: `harness.py owner restart` stops with an error in the map travellers drawing.

## Current state, update 23 (14 Nov 2026)

Owner's words: "the big stone you added is not as heavy as 2 blocks that together make the same size as the big stone. recheck all weights, using the regular rectangular block as the base. ... and do the undo, and put the button on top left."

- Weights: every piece weighs its size in blocks of its material (beams and planks were 15% light; now not). Owner test `hand` checks every piece and material.
- The hand's strength goes by everything it carries (the piece and what rests on it); pieces resting on the held one are carried, not pushed against. A big stone square or a long block lifts like two stacked blocks (was 0.8 s vs 1.9 s to rise 1 m). Too heavy to lift (over two blocks) now holds for single pieces too.
- Undo button, top left in free play and levels: each press puts back the building (and in levels the pile) as it was before the last piece was picked up, with whatever fell or broke since. Remembers up to 40 steps; cleared on entering a level or free play. Harness `sandbox` does it by mouse.
- Level runs and wrong choices (3 placements) pass after the weight change.

## Current state, update 24 (14 Nov 2026)

Owner's words: "now the 2 blocks on top of each otehr lifting from the bot, makes the top one jump after a while. ... can yiu mimic REAL physics? also im not sure 2stacks feel teh same as a big square. and , ahve yo changes the relative weights of materials? I am afraid you may have, somehow mudbrick and stone dont feel so different anymore"

- Cause of the jump: two stacked blocks read as heavier than they are while rising (the top one presses harder while it speeds up), so the hand flickered at its "too heavy" limit, crept, then got its full strength back at once and yanked the stack. Fixed: what rests on the held piece is weighed without that extra push; the hand's strength falls off smoothly towards its limit; carrying something on top, the hand slows no faster than things fall going up.
- Owner test `hand`: lifted from the bottom, what rests on it stays sitting (two small oblong stones, two blocks, four squares); same lift time for two blocks, four squares, big square, long block.
- Material weights unchanged (wood 1.1, mudbrick 3.2, stone 5.0 per square metre since before 13 Nov).

## Current state, update 26 (14 Nov 2026): the hand is one real model

Owner's words: "I want it to be real, consistent, and NOT hacky. I cant belive that there is not a model with a set of params that make it work"

- The hand (PHYSICS STEP, "THE HAND"): a small hand body (2 kg, no collisions, no weight of its own) pulled to the finger by the arm's spring, never harder than 210 N (a stone block weighs 100 N); the fingers are a pin at the grab point; the wrist turns the piece back to the angle it was picked up at, at most 30 N*m. Nothing else: all earlier hand rules (touching/near/free strengths, carried-weight readings, too-heavy switch, speed caps, sideways push, side rubbing, spin caps, balance zone) are gone, and so are the materials' hand limits.
- Owner tests pass (hand, carry, triangle, motion/feel, undo by mouse) except, as consequences of real physics, waiting for the owner: (1) a small stone pressed hard into a big stone block pushes it along (the hand's full strength goes through it); (2) dragging a mudbrick or stone block up while pressing 1.5 m into a wall rubs and sticks (pressing 0.5 m into it slides up); (3) a stone block crosses 4 m in 0.7 s (the earlier "too light" mark was 0.8 s).
- `harness.py probe` (old developer checks of the earlier hand) fails on hanging and swing-settling numbers; not owner tests.

## Current state, update 27 (14 Nov 2026): handoff, next chat builds "the brain"

Owner's words (answer to "a small stone pressed hard into a big stone block now pushes it along"): "because my hand is controlled by a brain that is not retarded, and is not pushing with full strength to demolish things left and right. do you know the strength that one must apply to have the tiniest rock of the game push away the big stone boulder? also, a wooden block now, grabbed from the side, is not swinging down, it remains horizontal."

Done this chat: the fingers hold a piece from turning only as hard as WRIST_STRENGTH (8 N*m, no turning back to the start angle), so a wooden block, a stone block or a beam grabbed near one end swings down (owner test `hand`, "swings down").

Next (the owner's reason, to go into the hand model, not as an exception): the brain uses the strength the load in the hand needs, not the arm's full strength. Plan, all from what things are, no special cases:
1. The brain plans where the hand should be: a point that follows the finger but never more than a short reach ahead of the grab point (the brain waits for the piece), moving at most at a speed that falls with the load (heavier slower).
2. The arm's spring is stiff in proportion to the load (load = the piece plus the share of weight resting on it, from what rests on what, as `traceLoads(true)` would give: add a `withHeld` option). Pressing into something that does not move then pushes with stiffness x reach: small for a small stone, large for a big one; the arm's top strength (210 N) still caps it.
3. Keep: hand body, finger pin, WRIST_STRENGTH.
Tried this chat and dropped: a fixed push allowance (load x (g + 20 m/s^2)) made all pieces equally quick and broke "lighter is quicker".
Owner tests still failing on the current game: small oblong stone pushed hard into a big stone block moves it 5.5 m (should hardly move); stone block dragged up while pressing 1.5 m into a wall sticks; stone block crosses 4 m in 0.68 s (the "too light" mark is 0.8 s); stone block whirled at one end turns 1.38 times in 4 circles (approved feel 1.69).
Answer given to the owner: pushing a stone block (100 N) along stone takes about 60 N; the big stone square, about 120 N; the small oblong stone weighs 16 N; the arm can give 210 N.

## Current state, update 28 (14 Nov 2026): the hand with a brain

Owner's words: "a small stone still absolutely rams the huge boulder and MOVES IT; like this is impossible ... also, a stone should still be able to be rotated, currently gravity is pushing it too much down, at that point the hand becomes stronger to maintain smooth motion. ... is there not even 1 example of how to do this that you can copy? there are a million simple games like that."

The hand now (PHYSICS STEP, "THE HAND"): Box2D/planck's standard drag (mouse joint) on a 0.2 kg hand body, strength a multiple of the weight carried (HAND_GRIP 4 x the piece plus what rests on it, from `traceLoads(true)`), capped at 210 N; fingers a pin; they resist turning with 0.6 x the weight's turning pull about the grab point (WRIST_GRIP), so off-centre pieces turn down smoothly and can be swung round. The brain plans the hand: heads for the finger at most 11 m/s, moves towards any other piece only as fast as it could still stop before it (15 m/s^2), never more than 0.3 m ahead of the piece; the spring aims ahead along the planned motion. Replaces update 27's plan.
Owner tests: all pass except: two small oblong stones lifted from the bottom, the top lifts 3.8 cm off at the stop (limit 2 cm); light pieces cross 4 m in about 0.5 s (approved feel 0.37 s) and the stone block in 0.65 s (the "too light" mark is 0.8 s), so "lighter is quicker" holds only between stone blocks and the rest; a stone block whirls 2.45 times in 4 circles (approved 1.69).

## Current state, update 29 (14 Nov 2026, voice and teaching plan)

- `cues.md` is the master doc for every voice line (01-122), what plays when, the teaching sequence from the first launch, and the per-site demos. Not built yet, apart from: test button red until ready then green with a plain triangle; open map sites yellow.
- Valens: one wooden form on one block (owner); the suggested build makes the arches one after another, taking the form out of each. Its tests passed; the pile is 110% of the sidebar height (accepted before at 120%).
- Mausoleum: the posts stay (owner: when he builds, the beams fall without them).

## Current state, update 30 (14 Nov 2026): the arm holds the weight, the brain stops at the finger

Owner's words: "the stone block should be able to be swung in circles. right now, all materials, incliding stone, get gragged down too much during an ttempted hold-and-rotate-movement, so I cant swing them in circled. at this motion, you ahve to apply stronger holding, like we do in real life. also, the genral thing than in a downward motion that stops the stuff keep going down, and in all directions follow inertia, must become smaller (in teh downwards motion too, like, the hand naturally tries to hold the item back, the item doest follow inertia and gravity uncontested. finally, this small hack that makes the object lose strength wen about to fall on another in OK, but it must become a bit smaller, it eats away too much strength now"

Changed in the hand model (PHYSICS STEP, "THE HAND"), no new cases:
- The arm holds up the weight carried by itself (an upward force at the grab point, min(weight, ARM_STRENGTH)); before, the weight came out of the moving strength, so pieces sank under the finger.
- Moving strength: HAND_GRIP 6 (was 4) x the weight, times (1 - weight / ARM_STRENGTH), so the most it can lift is still ARM_STRENGTH (210 N).
- The brain arrives at the finger no faster than it can stop (BRAIN_SHARE 0.7 of the moving strength on the weight carried). The same stopping power replaces the fixed BRAIN_STOP 15 m/s^2 for slowing before other pieces, so that slowing is weaker than before for single pieces.
- New owner test group `swing` (circles without sinking; stopping after 3 m down, up, sideways). Before: a stone block sank 1.5 m under the circling finger and ran on 4.5 m after a fast move down. Now: 0.07 m and 0.2 m.
- Owner tests hand, carry, push, slide, motion, triangle: same passes as before plus "lighter is quicker". Still failing as before: two small oblong stones lifted from the bottom (top lifts 4 cm, limit 2 cm); the stone block crosses 4 m in 0.58 s (the old "too light" mark is 0.8 s; it was 0.65 s); `motion` reference numbers from the earlier hand.

## Current state, update 31 (14 Nov 2026): one force budget, grip by felt pull, inertia back

Owner's words: "your motion and force when a block is about to hit anotehr is unnatural, it slows down unnaturealy. also, its not possible anymore to grab a block from its rough center and have it NOT tilt. also, its still not possible to swing in circles a standard (rectangular 2m) stone block, I dont knwo why you think I can. also, you should never modify mass of objects again, and if you did, revert it. also this swing I describe should happen with relatively small circular mvoements of the hand, not the huge oens required now. also, you removed inertia/gravity pull too much. please. please"

The hand now (PHYSICS STEP, "THE HAND"), replacing update 30:
- One force budget: the arm's spring pulls with up to the weight carried + HAND_GRIP 6 x weight x (1 - weight / 210 N). No separate holding-up force any more, so gravity pulls again when the hand works hard.
- The brain's planned motion: top speed such that it could stop within BRAIN_RUN 0.8 m; speeding up and slowing down at most BRAIN_SHARE 0.8 of what the strength gives; it starts each grab with the piece's own motion. The stop-at-the-finger braking of update 30 is gone: a piece runs on 0.5-0.7 m past a finger that stops suddenly.
- Slowing before other pieces: kept, gentler (BRAIN_STOP 30 m/s^2, was 15; BRAIN_TOUCH 0.8 m/s).
- Fingers: squeeze in proportion to what the arm pulls with at that moment (the arm joint's own force, never contact forces); they hold WRIST_HOLD 1.2 x the turning pull at the grab point's distance from the middle, at most at WRIST_LEVER 0.3 m. Grabbed within about 0.3 m of the middle: no tilt (0-1 degrees in test); near an end: hangs down.
- No piece weights changed (none were changed in update 30 either).
- Tests: new `swing` group (small quick circles from the middle, running on, middle grab does not tilt, whirling by the end with hand circles 0.6-1.4 m across). All hand tests pass except: whirling by the end with small circles (no turns; with the old 2 m circles 1.2 turns in 4); stone block 4 m in 0.67 s (old "too light" mark 0.8 s); two small oblong stones lifted from the bottom, top lifts 4 cm.
- Open, asked of the owner: with real physics, even a completely loose hand cannot whirl a hanging 2 m stone block with small circles (tried: about 1 turn in 4 with circles 1.4 m across). Whirling with small circles needs the wrist to turn along with the hand's circles. Tried: then a block lifted and then carried sideways also turns about 20 degrees on the bend. Removed until the owner answers.

## Current state, update 32 (14 Nov 2026): steady arm and a real wrist

Owner's words: "2 std stone blocks that are carried together, one on top of the other, grabbed from the bot one, and they agr moved sideways horizontally, when the motion stops tilt and fall. Like, wtf, this hold is sopposed to hold them, if I want rotation I grab them from the side. ... your intertia restitance is too bouncy, like its a rubber band. the stone rotation is not smooth and absolutely circular, and the only way I can kind of make it happen is with hand circles that are at least twide as big as they should be, and also the stone pulls down way too much. Ecen the std wood block rotates with too much bouncy downwards motion. stopping motion still unnatural, better drop it." Then: "just mimic real physics, and the circle I describe should happen when you hold a pieve by one of its long ends ... circles with diameter equal to the diameter of the stone circle piece" (the round stone piece, 1.2 m across). "grabbing an stb block, that is standing tall, from the vertical middle, and horizontally from the abolute outmost point and lifting it up, makes it rotate veeery slowly, and DOES NOT turn down as gravity would make it rotate." "how hard I squeeze? that should not be a param, I am not trying to crush objects."

The hand now (PHYSICS STEP, "THE HAND"), replacing updates 26-31: no spring, no planner, no slowing before other pieces.
- Arm: each step a force at the grab point = weight carried (piece plus what rests on it) + mass x the acceleration that brings the grab point to the speed heading for the finger (speed closes the gap in ARM_EASE 0.08 s; ARM_REACT 0.05 s). Never more than weight + HAND_GRIP 2.5 x weight x (1 - weight / 210 N). Speed at most what it could stop within ARM_RUN 0.6 m; acceleration at most what it has, and at most ARM_CARE 0.8 x the friction of what rests on it (so a stack carried by the bottom stays together).
- Wrist: a pin at the grab point whose turning resistance is Stribeck friction: still, up to WRIST_HOLD 0.4 m x the arm's pull; turning, WRIST_SLIP 0.05 m x it (WRIST_GIVE 0.3 rad/s between). Grabbed within 0.4 m of the middle: never turns. Farther out: falls round almost freely.
- New owner tests in group `swing`: standing block grabbed at the outer side lifted turns down (0.55 s); two stacked blocks carried sideways and stopped: nothing tips (stone, mudbrick, wood); middle grab no tilt; small quick circles; running on past a stopped finger (0.3-0.9 m); whirling by the end with circles 0.8, 1.2, 1.6 m across.
- Failing, reported to the owner: whirling by the end with 1.2 m circles (stone 0.3 turns in 4 circles, mudbrick 1.1, wood 1.4); at one circle a second that needs about six times the stone block's weight of pull and the arm has 2.3 times it. Dragging a block up while pressing 1.5 m into a wall of stone sticks at 0.6-0.7 m of 1.5 m (pressing 0.5 m: only wood, 1.34 of 1.5); this passed before only through the slowing before other pieces, removed on the owner's request. Small oblong stone pushed hard into a stone block: 0.1 m (limit under 0.1).

## Current state, update 33 (14 Nov 2026): throwing, material differences back

Owner's words: "wood drags too slowly. its as if weight differenced between materials are lost. also, teh strength of the hand is too weak, I cant drop things with force, as I could before: at full speed of a mudbrick motion, it should be able to be thrown from the height of the middle of the screen, 9 meters to the side till it reached ground. ... also, please show me a picture where you amkae to circle things by grabbing and rotating, I cant, and you cant, so what is happening"

- Arm strength: ARM_STRENGTH 210 N in all; holding up the weight first, the rest for moving, but never more than HAND_GRIP 3 x the weight for moving (was 2.5 x weight x (1 - weight/210)). ARM_RUN 1.8 m (was 0.6), so a quick sweep throws.
- New owner test `throw`: block swept sideways at full speed and let go at 5 m height: mudbrick 8.5 m, wood 9.1 m, stone 5.9 m.
- Carry 4 m: stone 0.88 s, mudbrick 0.61 s, wood about 0.57 s (approved feel: wood 0.38 s). Wood quicker needs HAND_GRIP about 5, and then a small oblong stone (about the weight of a wooden block) pushed into a stone block shoves it: asked of the owner.
- Consequences reported: a piece runs on about 1.1-1.3 m past a finger that stops at full speed; a small oblong stone rammed fast into a stone block moves it 0.6 m, pushed hard 0.2 m (owner rule: hardly moves); the wall-pressing case of update 32.
- Picture `owner-shots/whirl-4-circles.png` (`tools/harness.py whirlpic`): wood, mudbrick and stone blocks held at one end, four hand circles 1.2 m across, one a second; none goes round cleanly (stone 0.65 turns, mudbrick 1.16, wood 0.65 in 4 circles).

## Current state, update 34 (14 Nov 2026): owner verdict on update 33, open

Owner's words: "rubbery inertia thing reappeared. and many mroe thigns are wrong. and things get thrown away more than what I want. and cicles still dont ahppen,a s evidenced by your pictures. and i dont read your long texts. and I am exhausted"

Open for the next chat: the hand of updates 32-33 does not satisfy the owner (runs on too far, throws too far, no whirling with circles as big as the round stone). Before rebuilding: put the owner's cases into tests first (stack carried by the bottom stays together; grab near the middle never tilts; standing block grabbed at its outer side falls round at once; whirl by one long end with circles 1.2 m across; no rubber band; mudbrick thrown from mid-screen height about 9 m but not more than he wants; wood clearly quicker than mudbrick, mudbrick than stone; small stone does not shove a big one; dragging up a wall slides) and ask him yes/no before coding. Replies to him: a few short lines only.

## Current state, update 35 (14 Nov 2026): the owner's hand list as tests; hand rebuilt to it

The owner approved a numbered list of hand behaviours (tests: `tools/harness.py owner list`, each check named "list N"). His answers: point 2 = every piece by its own size: grabbed in its middle third stays level, in an outer third turns down (no rotate button exists; turning comes only from grabbing off-centre); 18 = real falling decides; 6-8 = how far a piece runs on follows from the 9 m mudbrick throw ("the benchmark for other materials, according to their mass"); 23 = try slower circles; 27 = physics decides (shown only); pushing and hits are mass x speed, no special rules.

The hand now: arm force at the grab point = weight carried + mass x acceleration towards the speed heading for the finger; that speed never above what it can still stop at the finger (time-optimal), nor above what one arm sweep (ARM_RUN 1.8 m) gives; acceleration at most min((210 N - weight)/mass, HAND_GRIP 3.8 x g x (1 - weight/210 N)) and at most 0.8 x the friction of what rests on it. Wrist: Stribeck friction, static hold = the arm's pull x the distance from the middle to the edge of the middle third towards the grab point; 10% once turning; fading once the piece has turned in the fingers (WRIST_TURNED 0.3 rad); viscous damping 0.35 of critical.

Results (hand list + older hand tests): 102 of 119 pass. Failing:
- 9: comes back without passing the finger, but at 2-3 m/s ("slowly" mark 1.5 m/s).
- 12: carry 4 m stone 0.98 s, mudbrick 0.67 s, wood 0.55 s (wood mark 0.4 s). Wood and the small oblong stone weigh about the same; wood at 0.4 s needs about 2.5 times the moving strength.
- 23: no whirling at circles of 1, 1.5 or 2 s: the wrist damping that stops a hanging block bouncing (point 3) also stops whirling.
- 26 / old push tests: small oblong stone pushed hard into a stone block moves it 0.3 m, rammed 1 m: from the hit (mass x speed); a gentler hand (HAND_GRIP 2.6) still 0.16 m and breaks the 9 m throw.
- 31: dragging up while pressing 1.5 m into a wall sticks half way (real friction; passed before only through the slowing near pieces, removed by the owner).
- Old test "a stone block held at one end swings round in big circles": 0.13 turns (damping).
Points 3 and 5 marks changed from my proposals to the pieces' own swing: hang within 1.5 s, standing block falls round within 0.8 s.

## Current state, update 36 (14 Nov 2026): whirling works, no tilt when dragged, a bit less throw

Owner's words: "1. stones, when dragged horizontally through the air, tilt too much, as if the air resistance can tilt them. you ahve to make stone heavier, and all amterials in proportion, and the strength in proportiona s well so no differnece is felt. 2. after that, make strength a bit les,s because no I can throw mroe than what I imagine correct. 3. you ahve to make whirling work, I dont know why you ahve so many difficulties. explain why, adn what is this connection with boincing"

- Not done: scaling every weight and the strength together changes nothing in the game (every speed and turn stays the same). The tilt came from the wrist: a block grabbed in the middle of its length but near its top or bottom edge counted as an outer third. Now the wrist holds fully against the hand's own speeding up and slowing down (the brain keeps what it moves steady); against the weight it holds as far as the middle third reaches (point 2 unchanged). New test "list 1b".
- Throw: ARM_RUN 1.8 -> 1.4: mudbrick 7.1 m, wood 8.6 m, stone 4.9 m (test 16 now 6.5-7.6 m).
- Whirling: the wrist's damping now acts against swinging relative to the finger's own turning (from the finger's last 2 x WRIST_SEEN steps; a person whirling turns the wrist with the circles, held still it calms the swing), capped at the weight's turning pull at the grab point; and pulling a piece by a point away from its middle, like a rope, the arm is ARM_PULL (5) times its weight stronger. A block held at one end now goes round once per hand circle as big as the round stone, at one circle every 1, 1.5 or 2 s, smoothly, for stone, mudbrick and wood; hanging still it settles without bouncing. Picture `owner-shots/whirl-4-circles.png` (redrawn).
- Hand tests: 112 of 125 pass. Still failing, waiting for the owner's answers (asked in update 35): coming back at 2-3 m/s, wood carry 0.57 s, small oblong stone pushed hard moves a stone block 0.3 m, dragging up while pressing hard into a wall sticks half way.

## Current state, update 37 (14 Nov 2026): same effort for every piece, real inertia, whirling with a real mouse

Owner's words: "I need to see what you do in whirling. I cant and the problem is not me, is you. answers : 1. try A 2. I think it fine as it is now 3 I think this has to do with inertia mostly, and inertia as far as I know has to do with mass, so wood should be for example move less far away from finger than stone". (1 A = the hand pushes every piece with the same effort; 2 = dragging up while pressed into a wall keeps real friction; 3 = how far a piece runs on.)

- Hand: moving effort HAND_MOVE 55 N for every piece (under the 60 N that slides a stone block along stone), on top of holding up the weight, within ARM_STRENGTH 210 N. The brain moves the hand with the finger's own speed (feed-forward) and closes any gap no faster than it can still stop at the finger, so a piece runs on past a finger that stops suddenly by its own inertia (at a steady 1.5 m/s: stone 0.22 m, mudbrick 0.15 m, wood 0.07 m; new test "list 9b") and comes back without springing past. ARM_RUN 3.4 m (throw: mudbrick 6.6 m, wood 9.9 m, stone 3.8 m). Carry 4 m: wood 0.65 s, mudbrick 1.13 s, stone 1.5 s (test 12 now checks the order only).
- Whirling: the owner could not whirl in the game; a real-time video with the real mouse at about 20 moves a second showed the stone only swinging. Cause: the finger's motion was read per physics step, so a mouse that reports less often than the game steps looked stop-and-go. Now the finger's path is kept with the time each position arrived and read over FINGER_SEEN 0.08 s windows. New check: whirling with the finger's position arriving only every third step (test 23 "slowMouse"). Video `owner-shots/whirl-real-mouse.mp4` (`tools/harness.py whirlvideo`): stone, then wood, held at one end, circles shown dashed, once a second, real game loop.
- Hand tests (owner list + older): 113 of 126 pass. Failing: hanging still takes stone 2.0 s, mudbrick 1.6 s (mark 1.5 s; heavier is slower with the same effort); after a hard stop wood comes back at 2.6-3.2 m/s (mark 1.5 m/s); a small oblong stone pushed or rammed into a stone block moves it 0.7-1 m (the hit: a light piece is now quick); dragging up while pressing 1.5 m into a wall sticks half way (owner: fine as it is).

## Current state, update 38 (14 Nov 2026, end of chat): the owner's chosen hand is the update-36 version

Owner's words: "I like the file I sent you. keep that." The file he sent is the game as built at commit 475cd61 (update 36, 18:10); `src/index.html` and `arxitektones-tou-arxaiou-kosmou.html` are restored to it byte for byte. Update 37 (same effort for every piece, hand moving with the finger's speed, finger read by real time) is undone in the game; its write-up above stays as history.

Open, from the owner, for the next chat (ask before building, per the hard stops in CLAUDE.md):
- "the wood rotation circles are wider than the stones, and that unnatural": whirling a wooden block by one end makes wider circles than a stone block. Cause unknown; find it with the real mouse in the running game (`tools/harness.py whirlvideo`) first.
- Whirling extra strength: asked "should the hand be allowed to pull that hard (about six stone blocks) so a stone block whirls fast?", the owner answered "NO". This version still has the stronger pull when pulling a piece towards the hand like a rope (ARM_PULL 5); removing it is pending his yes on what changes.
- Grab areas (owner): "kid must be able to touch an area in the center of the block and it counts as dead center anyways. same as for the 4 sides, they each have an area of forgiveness that is considered dead center edge. the rest are yes, where the hand goes." Proposed sizes, not yet approved: middle area = middle third of the piece; each side's area = middle third of that side, from the edge in to about a quarter of the piece's thickness.
- Reported on a recent version (which one unknown): grabs at the top of a standing stone block are buggy and sometimes make it jump; such a grab pulled sideways should tip the block over, instead it is dragged along the floor; a stone at 45 degrees grabbed by its top corner jumps; bounce-back after stopping is excessive; sometimes an upward drag flies far too high when stopped; whirling looks disconnected from the hand's circles (the owner: a stone on a thread, or on a finger through a hole, goes round the circling hand).
- With an uneven mouse, whirling in this version broke in a real-mouse recording (update 37 found the cause: the finger is read per game step).
- The owner test group `owner list` was written for update 37; some checks (12, 9b, throw ranges) describe that version.

## Current state, update 39 (14 Nov 2026): cues built

`cues.md` sections 2-6 are built with text boxes (section 9), in `src/index.html` SECTION: CUES (the model is the three-part list at its top). Voice recordings: put `src/sounds/voice/NN.mp3` and run `build.py`; that line then plays instead of its box. Check: `tools/harness.py cues` (each demo: what broke or fell when its line comes; the first-site steps in order; the queue rules).
Readings taken (not decided by the owner): Djoser wrong demo = two mudbricks with stone blocks three high on them (they crumble); the Ur demo is built on the bottom row's places; restart erases when pressed again while line 91 is up; no step in section 6 asks for dimming, so it is not used; line 86 is skipped until recorded; Pharos has no marked wood places, so line 108 first plays at Ur; nothing can be touched during a demo, the child's pieces are put aside and come back after; the test waits for line 71; after a first-ever fail in a part the red place stays until 74-76 and 105 are taken down; the Mausoleum right demo builds the whole roof (about 40 s), because the beam holds only under all of it.
Open (owner): Ur wrong demo (two short beams, line 112): built in the game, no brick crumbles under it, so it is left out; the Ur demo shows only the right way (line 113).

## Current state, update 40 (14 Nov 2026): cue model rebuilt

Owner's words: "1. add a visual countdown over the text, 2 secs for all texts, as a bar that becomes smaller, blue, on top, from left to right, then the text autocloses, this way we mimic a voicenot that at some point ends. 2. the CTRL fast build worked, but the CTRL fast check doesnt, in the tutorial in the 1st level. must be spagtti code, code cleanly and generically EVERYTHING. 3. the EPANEKKINISI button does something weird, does not give its bubble on fresh game, the tutorail gives its bubbles, then I exit level, then the EPANEKKINISI bubble appears. spagetti code, code better, rething your architecture. I am CTRL going to alexandria and I see random bubbles that should ahve apepared before, your event quese system is wrong."
Cause (one, for all three): a line stayed up until ESC or until the child did its action, so it held the voice channel; everything behind it waited, and the test waited for line 71. Rebuilt (SECTION CUES, three parts at its top): every text line lasts 2 s with a blue bar on top that empties from the left, then closes (ESC still ends it early); a step's glows and ghost hand last until its action, apart from its line; every line and step belongs to its scene (the map, one visit to a site, free play) and a new scene drops what is left; nothing waits for a line (the test, the restart); cue times run on game frames. `tools/harness.py cues` checks the demos, the first-site steps, the 2 s line, the restart line on a fresh map, no map lines inside a site, and the Ctrl quick build + Ctrl test during the first-site teaching.

## Current state, update 41 (14 Nov 2026): attention, buttons on release, demos every visit

Owner's words: "1. every button must also ahve a tapped state, and the actual thing happens when the click/tap is released. 2. when a bubble refers to an item( button, site, material, anything) this object should be highlighted in a cosnistent way, I suggest the yellow flashing, same as you have for the next site in the tutorial as the default, with green and red used when they highlight green/red items. 3. the tutorial hand must be more like a hand. 4. Im in teh starting screen, in the "press here to start", the hand stayes for way too little time, remember, tis for 4 year old kid, and it didint repeat ina  reasonable time (5 secs), with its sound as well. 5. make the attention-here flashing slower, but with wider ringing-out radius. 6. I am inside the first level tutorial, while the welcome message was playing, I could move stuff and press buttons, NO, some cues should freeze everything else, I suggest you use a darkening overlay to indicate that noting can be done. 7. when the red button flashes to be clicked in teh tutorial, there is no text bubble. also, the screen should freeze as I described before. and the default "leipoun akoma kommatia apo to sxedio" shouldnt appear there, only the one prescribed specicifally to explain that button. 8. the video help at lvl 2, and i assume its like that everywhere, appeard only one time. it should appear as logn as this level is not done, beacuse the kid may go out and in again. also, when it plays, nothing else should be able to be done, it should block screen, same as others explained before,a nd all similr, use your brain too. also, for every video, make a hook in the code and a line in the doc, where the coice will say what we do, nto only what the result was, that is shown after the video si amde. so, for example for lvl 2, not 2 voice hooks but 4. 9. at lvl 2, when the video tutoral is playing, a random mudbrick is flashing as well. actually i see now, its not random, its because its we will build with stone, right? but then the stone should flash, and I saw at a later level you flash wood, but its all circled, and that weird, so the flashes should start from the outline of the object, and for palnks for example, be oblong. 10. the 3 tests voice explanation must happen only the first time a test happens, at the first level, not on every level."
Built: `cues.md` section 0 lists the rules. Code: SECTION CUES (three-part model at its top: voice, attention, steps); every button is in one list (`screenButtons`, POINTER HANDLING) and acts on release. Checks: `tools/harness.py cues` (demos, first-site steps, 2 s lines, the 5 s repeat, restart line, no map lines in a site, intro freezes and blocks touch, Djoser demo on two visits, Ctrl test in the teaching, explanations only in the first test, a button acts when let go).
Open (owner): a new way to document cues (proposals given in chat 14 Nov evening; nothing chosen yet).

## Current state, update 42 (14 Nov 2026): Ur in five rows of whole mudbricks, long planks standing in the pile

Owner's words: "Can I ahve Ur with all mud std rectangular blocks, starting at 7 base, and using new length wood beans ... so it can reach 5 levels (without counting headpiece)?"; "desired outcome: all mud, 5 levels. go"; "you amde sidebar smaller everywhere, revert it and never do that again. ... also, see if adding wood on every level's top except of the top top food, would work too."; "of course a 14 m plank fits, IF YOU FUCKING PUT IT VERTICALLy ON thR SIDE ... the file you8 gave me doest ahve the 7 base blocks Ur. 4. why would a plank slide out, thats tupid. give me the level to check myself."
Built: Ur as in `levels.md` section 3 (five rows, 14 m and 10 m planks; pile also has 12 m and 8 m planks for the owner's every-row try). New pieces plank8/10/12/14 (also in free play). In the pile, a plank longer than the bin is wide stands on its end (PILE: `lying`); the sidebar size is unchanged (same as before tonight). Picture: `owner-shots/ur-five-rows-pile.png`. Checks: `harness.py spec 2` all pass (pile at 100% of the sidebar height). Then (owner): "make it for me with wood at every level. also, you have enough space moron, bor all the mudbricks to be on the floor, as 2 piles, ... putthem all down in 2 piles". Built: suggested build has a plank on every row but the top (14, 12, 10, 8 m); in the pile, standing planks share one row and blocks stack beside them as high as the tallest plank (PILE `pileLayout`, all levels). Picture `owner-shots/ur-five-rows-pile.png`. Open: the quick build fails the earthquake (the bottom plank slides with everything on it); cause unknown; the owner checks it himself. Pharos wrong build "no wooden ties" passing and the Valens pile check failing were already so before this change.

## Current state, update 43 (14 Nov 2026, late): cues as a table; the owner's cue list

The owner chose: "I choose A, with B written from it, so I can read it. B should change when A changes, my comments will amke you change A. about Ur: forget it for now, anotehr caht is dealing with it."
Built: `cues.json` (version A) is the only source of the cues; `cues.md` (version B) is written from it by `python3 tools/cues_doc.py games/arxitektones-tou-arxaiou-kosmou/cues.json` (never edit it by hand); `build.py` puts the table into the game; SECTION CUES is the engine (three-part model at its top); the pattern for every game is `docs/patterns/cues.md`. `tools/harness.py cues` checks the table's names, the demos, the first-site steps and the list below.

Owner's list, verbatim, with what was done:
1. "you repeat instructions every 3 secs, thats annoying, amke it every 5 secs" — a waiting step's line now comes again 5 s after it ends.
2. "I thought you ahd a rule to not play flavor text during tut text, the "plithoi apo laspi, elafrioi, bla bla", has no reason to play while the cue shows to drag the brick," — while a teaching step waits, every other line is dropped; a dropped first-time line plays the next time instead.
3. "Return visit (saved progress), queued: No reason to ahve black overlay." — line 12 has no darkening.
4. "I refreshed page in the middle of "if you repss 3 tiles blabla", and when I went back, I saw lvl intro and then the same fucking instruction about the 3 times was there waiting to attack me! and it was playing stuck, without any piece in the site for me to click! you ahve messed on how to clear queued messages. and should it even be queued?" — steps say what they need (a piece in the building); without it they go back to the step that makes it (here: drag a piece in).
5. "didn't I say: " the video help at lvl 2, and i assume its like that everywhere, appeard only one time. it should appear as logn as this level is not done, beacuse the kid may go out and in again"??? I need to know you can follw my instructions, I dont fuckign care if youa re retarded and get lost, I cant be giving you 5 isntructiosn at a time so you dont get lost, write in claude.md your strategy so that when I spem you even with 100 change requests you DONT GET LOST." — the demo plays on every visit until the site is finished (checked in the running game: Djoser, two visits, the demo both times); the old doc still said "first visit", the table now says it. Strategy written in CLAUDE.md, "Long lists of change requests".
6. "you overuse the overlay, no reason for freezing overlay at the refresh button." — line 91 has no darkening.
7. "Αν αυτό θέλεις, ξαναπάτα το -> Αν αυτό θέλεις, pata to dipla" — line 91 says «πάτα το δίπλα»; the first press shows a red tick button next to restart for 6 s; only it erases.
8. "triple clicking item, as per que, makes overlay flash on and off, I saw it flashing another time too, stop it." — the darkening of a waiting step stays for the whole step, whatever the child holds.
9. "make attention flashint more prominent, I suggest a bit thivher outline, and a bit thicker radius." — outline 8 px (was 5), ring 7 px (was 4) spreading 40 px (was 34).
10. "The "Des! dio plithoi ba bla ki enas sti mesi" playes before the video, it should play WITH the video, this and all similar." — demo lines that say what is done ("tell") play while the pieces come.
11. "my mudbrick in teh first tutorial broke, at the stage where it wanted me to put a mudbrick in, so the shovel would remove it. the mudbrick broke, but your cue system is WEAK: it doesnt udenrstand that a mudbrick is needed for that step, and its flashint "click the shovel!" with no mudbrick, isntead of talling me to bring anotehr mudbrick! you ahve to apply checks like that, and be able to go back to previous queues. Do that generally." — same rule as 4, for every step (needs + back in the table).
12. "Red button: "Αυτό είναι το κουμπί της δοκιμής. Όσο είναι κόκκινο, το κτίριο δεν είναι έτοιμο. Όταν γεμίσεις το σχέδιο, θα γίνει πράσινο." -> add pata to an deis ti den einai sosta topothetimeno" — line 99 adds «Πάτα το και δες τι δεν είναι σωστά τοποθετημένο.»
13. ""Leipoun akoma kommatia apo to sxedio" has no reason to have blocking overlay. you overuse it." — line 70 has no darkening.
14. ""Leipoun akoma kommatia apo to sxedio"  -> thelei souloupoma akoma" — line 70 is «Θέλει σουλούπωμα ακόμα.»
15. "WHen i sceeded first level, the sucess audio for first level did not flash freen the first level on teh map. and the "a new waits" most wait for that, and no reason for overlay too. you voeruse it" — the map line after a win makes the won site glow green, the new-site line follows it, no darkening.
16. "In the "piase ena kommati kai falto mesa sto sxedio" if I dont grap the highlighted piece, I cant grab anything." — the whole pile can be touched in that step; one piece glows.
Darkening is now only where the table says: site welcome lines, first crumble and snap, the first test's three explanations, demo "after" lines (freeze); the waiting teaching steps (point).

## Current state, update 44 (15 Nov 2026): Ur temple and earthquake 10% weaker

Owner's words: "can you amke this level headpiece and earthquake 10% less strong? then I think it will survive"
Built: Ur temple load density 4 -> 3.6, Ur earthquake 0.38 -> 0.342. Result: the quick build (plank on every row but the top) still fails in the earthquake: the bottom bricks under the bottom plank reach about three times what crumbles them while it rocks, and the plank with everything on it slides.

## Current state, update 45 (15 Nov 2026): Ur top rows 3 and 2 blocks

Owner's words: "2 blocks only at the top, and 3 at the one before the top. test that it works. if so, update outline and materials."
Built: Ur rows 7, 6, 5, 3, 2 mudbrick blocks; planks 14, 12, 10, 6 m (the 6 m on the 3-block row); outline and pile from the build (make-levels.py `ZROWS`). `harness.py spec 2` all pass. Picture `owner-shots/ur-five-rows-pile.png`.

## Current state, update 46 (15 Nov 2026): owner cue and level list of 15 Nov

Owner's list, verbatim (checklist; results below as each is done):
1. "no, mausoleum has no long mudbrick, and shouldnt, recheck your data and fix them."
2. "keep it in karnak."
3a. "in ur, remvoe the "se afta ta simaia mpainei ksilo" cue."
3b. "in ur, find a way to demonstrate that wood helps spread weight by first crimbling, adn then not crumbling."
4a. "the restart button shouldnt make another button appear,"
4b. ""pata to diplA", not "pata to dIpla.""
5a. "in the texture change button, make the texture stone be the grey one isnted of the yellow one."
5b. "Then, make sure teh plain colors correspond to the textured colors in that button."
5c. "And make for the levels that ahve marble, the grey stone be a nice solid color, ok, but of marble."
6a. "the first-time.touch.mudbrick cue shouldt appear at first level tutorial when the otehr tutorail cuees are playing, its the third time i say that."
6b. "fix your claude isntructions so you can follow my isntructions, i suspect you ge tlost when i give you lots of change requests, but i already said to vhange your isntructiosn so you dont fucking et lost, moron."
7. "add a "Mpavo, afto girise piso sto soro" when in first lvl the kid triple clicks after isntruction"
8. "after that, add cue to show how to drag and drop back to pile too. (of course update all relevant que files too)"
9. "the "if you click 3 times" cue is too hasty, I dropped a block and it broke, and that stupid cue played, you play condition is wrong"
10. "the dark overlay should NOT be also darkening the focused object. I saw that the cue to rturn to the main map also darkened the go to main map button."
11a. "at lvl 2 the 2 vieos (wrong/right) are not symmetrical, the same amount of rocks must be placed on a mudbrick and then a rock."
11b. "and one stack is enough"
12a. "in lbl 2, both stones and mudbricks flash on the sidebar, thre is no reason for that,"
12b. "and stop flashing materials on the stockpile when levels start, I dont understand the reason."
13a. "in the main map i think I didnt see lvl 4 flash when lvl 3 was done,"
13b. "and I dont see any regular reminder ques that the new site waits, make them play every 60 seconds, but only flash, the voice plays only every time you exit the previous site and for the first time the new is available."
14a. "I also dont see any of the regular flavour cues on the map, they should play every 30 secs."
14b. ""Den antekse to varos, ksanadokimase" is wrong text, I see it when the headpiece is tilted wrongly, at the secont strp of the test, nothing broke. It should say "I koronida den epikathise kala. Ksanadokimase!""
15. "after a failed test that broke some mudbrick i say the "i laspi thrimmatistike kato apo to varos", and it was pointing at a phantol location, after the levle was reset. this is supposed to play while building, and those timings were off, like leftover stuff that were not cleared."
16. "in every level flavour text, make sure new materials are mentioned, also new stone variations, mention them every first time theya re encountered."
17. "sfines -> replace in greek with "Καμαρόπετρες""
18. "in the gate of sitear level, your demo shows the wooden pieces dragged away, that is wrong, they should be triple-tapped away."
19. "add a 2 second gap between the previous level outro and the new level flash in the main map."
20a. "for your halicarnassus demo, for the wrong demo, your pillar is resting half, only on one stone."
20b. "for the right demo, you built more of the base, you should built exatly the same part of the base both ways, not half a base for the first, and a full abse for the second."
20c. "also, the second doesnt nees the full building, just up to the point that the 2 lintels stand."
21. "last level needs no demo."
22. "NOW: DO ALL THESE NOT HALF. REPORT THAT ALL ARE DONE, AFTER CHECKING THEM. ADD TEST FOR GENERAL ITEMS, LIEK WHAT PLAYS FIRST WHAT SECONG, WHAT ON TIME, WHAT PERIODICALLY, WHAT SHOULD NOT PLAY WHILE SOMETHING ELSE PLAYS, WHAT PPLAYS ONLY ONCE, WHAT AT THE RIGHT TIME,S IN SHORT, DO TEST DRIVE DEVELOPMENT,A DN TESTS HOULD BE SNAPPY AS FUCK."
Results (each checked by `python3 tools/harness.py cuetest`, 22 pass/fail tests in `tools/cue-tests.js`, about 10 s; all pass):
1. The Mausoleum pile never had a long mudbrick (it has 4 mudbrick squares); the old note saying so was wrong and is corrected; levels.md pile line fixed. Test mudbrick-long-pieces.
2. Karnak keeps its two tall mudbrick columns. Same test.
3a. The "wood goes here" cue and its line are gone. Test no-start-glows.
3b. Ur demo: four mudbricks stacked on the middle one of three bottom mudbricks (it crumbles); then the same three, a long plank, the same four on it (none crumbles). Test demos.
4a. No second button: the first press of restart says its line; a second press within 6 s erases; a later press only says the line again. Test restart-press-twice.
4b. Line 91 ends «πάτα το διπλά.» Same test.
5a. The textures button shows the grey stone texture. Test texture-button-colours.
5b. The button's plain colours are the game's plain colours, each close to its texture (the marble block was tan, now marble white). Same test.
5c. With textures off, stone in the marble levels (Parthenon, Mausoleum, Pharos) is a solid marble colour; elsewhere grey. Test marble-plain-stone (reads the drawn pixel).
6a. Rule changed: while the first site's teaching runs, from its first step to its last, only its own lines play (the mudbrick line slipped in between steps before). Test first-site-teaching.
6b. CLAUDE.md "Long lists", points 8 and 9: every owner point becomes a permanent test, the whole cue test file runs before every reply; fix at the rule and test every place it decides.
7. After the three taps: line 132 «Μπράβο, αυτό γύρισε πίσω στον σωρό!». Test first-site-teaching.
8. New steps: put a piece in again, then line 134 «Μπορείς και να το σύρεις πίσω στον σωρό. Δοκίμασε!» with the ghost hand dragging it to the pile; then one more piece in for the shovel. Same test.
9. "Put a piece in" steps now end only when a piece lies still on something in the building; a piece let go high up that breaks on landing does not count. Same test.
10. The darkening was drawn so that two holes over the same thing darkened it again (the map button was both pointed at and touchable); holes are now cut one by one. Test darkening-spares-target (map button and plan, by pixel). Picture `owner-shots/cues-15nov-map-button-step.png` (also shows the textures button).
11. Djoser demo: one stack: three stones on a mudbrick (it crumbles), then the same three stones on a stone (it holds). Test demos.
12. The glow of new pile pieces at the start of a site is gone. Test no-start-glows.
13a/b. Coming back from the site before the open one says a new-site line every time (first time with the hand), with the open site glowing; the open site glows every 60 s on the map with no voice. Tests map-new-site, map-next-glow-every-60s (Ur won by its quick build and test, then the map).
14a. On the map a flavour line plays after every 30 s of quiet. Test map-flavour-every-30s.
14b. Load part failed only because the headpiece did not sit: line 133 «Η κορωνίδα δεν επικάθισε καλά. Ξαναδοκίμασε!». Test headpiece-line (real test, headpiece pushed off during the load).
15. Crumble and snap lines are never said during a test, and lines still waiting from the building are dropped when a test starts. Test no-building-lines-from-test.
16. Welcomes name each material and stone met for the first time: Mastaba wood, Ur only mudbrick (it said stone for the base), Lion Gate grey stone, Parthenon marble. Test intros-name-new-materials. Changed lines are marked for re-recording.
17. «σφήνες» -> «καμαρόπετρες» (lines 116, 117). Test words-arch-stones.
18. Demos take wooden forms and posts out with three taps, never dragged (Ishtar and Mausoleum). Test demos.
19. 2 s between the win line ending and the new-site line. Test map-new-site.
20. Mausoleum demo: same base both ways (four blocks under both columns, the middle column wholly on them). Wrong: one lintel on a post, post tapped out, it falls. Right: the same, the second lintel and three roof stones over them, post out, both stand. A second lintel in the wrong way would not fall: its end catches on the first lintel's end. Test demos.
21. Valens has no demo. Test demos.
22. Tests above; general ones too: first-launch order, return order, voice rules (one at a time, flavour dropped beside teaching, bg never interrupts, leaving drops), once ever/once per visit, 5 s repeats, nothing plain during a test.
Also found and fixed while testing 20: taking a piece out (tapped back, or crumbled) did not wake what rested on it, so a beam could stay in the air; now it does. Level runs after it: all levels pass as before; Pharos "no wooden ties" still passes its test when it should fail (it did before this change too).

## Current state, update 47 (15 Nov 2026 evening): owner list of 15 Nov evening

Owner's list, verbatim:
1. "At the Pharos, building the walls straight up with no wooden ties still passes the test, when it should fail??? without wood the test button is red, so the wind cant even start. what do you mean?"
2. "the "a ti oraia varkoula...", etch cues, should play ont he main map, moron, not on the levels. for fucks sake"
3. "in Pharos, add in the outline the place for the wood, as in other levels."
4a. "in mausoleum, the first fail demo should not show at all the wooden support, just the inability to make both lintels stay."
4b. "also, pieces should move not THROUGH each other, so move them at the right order."
4c. "also, you dont need to build and rebuilt the base and the kiones and kionocrana, they can be ready."
4d. "also, make all demos a bit LESS transparent"
5a. ""Δες: ένα δοκάρι πάνω σε ξύλινο στύλο. Βγάζουμε τον στύλο πριν μπει η στέγη." -> "Des: den exoume orizontio anofli arketa makri gia na patisei stous dio kiones " plays while fail demo is playing ,"
5b. ""Αν βγάλεις τον στύλο πριν πατήσει η στέγη, το δοκάρι πέφτει." -> goes away,"
5c. ""Τώρα ξανά, αλλά πρώτα χτίζουμε όλη τη στέγη, και μετά βγάζουμε τους στύλους." -> Tora ksana, alla ena ksilino dikari tha stirizei to anofli, mexri na valoume apo pano polles petres, pou tha to kratane ekei me to varos tous."
6. ""124": "Δες τι γίνεται αν βάλουμε τους πλίνθους κάτω και τις πέτρες από πάνω make similar demo also for" (cut off: asked the owner which level)
7. "your tests are shit: At some point the "drag from ehre back to the pile tutorial was looping. you need to be smarter when you code conditions""

Results (`python3 tools/harness.py cuetest`: 24 tests, all pass; the new ones failed on the previous build first):
1. Answered: the check filled the tie places with stone, so the outline was full and the button green; a child leaving the ties out has gaps and a red button. The level check now counts a button that stays red as stopping a wrong build (owner's words).
2. Flavour lines (group idle) play on the map only; nothing starts them on a site. Test flavour-only-on-map.
3. Pharos has wood places in its outline (the tie courses); without wood there the button stays red. Test pharos-wood-places; Pharos level checks all pass.
4a. Mausoleum wrong way: no wood; the lintel between the columns goes on first and falls, then the outer one stays. Test demos.
4b. Demo pieces come in over everything and go straight down onto their place; test demos checks no carried piece passes through another (the Mausoleum and Ishtar demos did before).
4c. The Mausoleum base, columns and capitals stand ready in both halves (new demo step "ready"). Test demos.
4d. Demo pieces 75% opaque (were 50%).
5a. Line 129 is the owner's text, said while the wrong way plays.
5b. Line 120 removed.
5c. Line 130 is the owner's text; the right way: post, both lintels, three roof stones, post tapped out, both stand.
6. Open: the owner's sentence is cut off.
7. The loop: dragging a piece into the pile turns it into a pile piece while still held, so the step's "a piece is in the building" check failed mid-drag and the teaching went back a step, and the "dragged back" moment never fired. Now the moment fires when the piece enters the pile, and a held piece counts as the child's. The teaching test now does every step with real pointer drags and taps on the screen. Test first-site-teaching.

## Current state, update 48 (15 Nov 2026 night): owner list of 15 Nov night

Owner's list, verbatim:
1. "mausoleum demo, first put the one that doest fall, the left lintel, then the right."
2a. "show the cue for the baps in the outline that shouldnt be filled ONLY, at the first level we seem them."
2b. "make the return button cue, afther the kid has placed 10 blocks on the first level."
5. "double check your voice cues, and if theya re at the right code hooks, etch, because I will start recording"

Results (`python3 tools/harness.py cuetest`: 26 tests, all pass):
1. Not built, a question to the owner: with the left lintel first, the right one tips and jams against the left one's end (tried with gaps of 4, 15 and 25 cm); it drops 15-30 cm and hangs tilted instead of falling. The demo keeps right first, then left.
2a. Line 109 («Αυτό το άνοιγμα μένει άδειο…») only at the first site whose outline has openings. Test openings-first-site-only.
2b. Reading: "return button" = the undo button (top left). New teaching step after the red button: when ten of the child's pieces stand in the building, line 135 «Αν κάτι δεν σου αρέσει, πάτα αυτό το κουμπί και η τελευταία σου κίνηση γυρίζει πίσω.» with the undo button glowing; then the green-button step. Test first-site-teaching (ten pieces laid by hand from the suggested build).
5. New test voice-hooks: every line is said by a cue, a demo or a group; every moment the table listens for is made by the game's code or by another cue; every teaching step exists. Line 86 is the owner's own recording (no text). All lines with numbers are in `cues.md`.

## Current state, update 49 (15 Nov 2026 night): owner list

Owner, verbatim: "1. remove demo for how to put 1 brick on top of 2, at lvl 1. also, make the shovel cue appear after 4 blocks are placed. and forget about teh cutoff cenence"

Results (`python3 tools/harness.py cuetest`, all pass):
- The first site has no demo (inside the teaching or on later visits); lines 97 and 123 removed. «Τώρα χτίσε! Γέμισε όλο το σχέδιο.» now follows the shovel's line.
- The shovel step waits until four of the child's pieces stand in the building. Test first-site-teaching (pieces dragged in by hand, the real shovel button pressed).
- The cut-off point about line 124 is dropped.
- Mausoleum demo order: owner, verbatim: "mausoleum ok, forget it". It stays right lintel first, then left.

## Current state, update 50 (15 Nov 2026 night): physics list

Owner's words: "1. when I ahve 3 std stone blocks on teh flooer, and I truyto push them all by pushing one of the outside ones, like a train, its not always they drag. sometimes they do, sometimes they dont move. 2. 3 mudbricks ina perfect pyramid setup (2 bot, 1 top right in the middle) cant be pushed horizontally on the floor, when grabbed from the outer middle aprt of any of the base bricks. from the inner middle part, it can. 3. I want you to change friction and make it 20% bigger, becasue I think its too low now."

- 3: done. Every friction 20% higher: wood 0.6, mudbrick 0.84, stone 0.72, ground 0.96, test loads 0.72 (walls and the sidebar pile unchanged). All ten levels still pass their test; every wrong choice still fails.
- 1 and 2: built after the owner's yes ("yes" to: the hand feels the whole row as one heavy load; more pieces start slower; a row too heavy does not move; where the piece is grabbed no longer decides). Hand code: the load moved is the piece, what rests on it, and the pieces it pushes on its way (each as much as it lies in the way, with what rests on it); the arm holds up the weight first and moves with what is left, never more than HAND_GRIP x the weight held; the rope pull helps only the piece itself, fading with what it pushes. Tests: `harness.py owner train` (three stones, pyramid, grabbed outer and inner half; four stones shown only: they do not move). Video with the real mouse: `owner-shots/2026-11-15-push-row-and-pyramid.mp4`. Other hand tests: same passes as before (the wood/stone/mudbrick wall slides, the run-on checks, the motion reference, small oblong stone into a block: 0.18 m pushed, 0.47 m rammed, were 0.16 and 0.40, all failing before too).
- Earlier note (before the yes): Cause found in the hand code: the arm pushes only as hard as it needs to speed up the piece it holds (plus what rests on it); the other pieces it pushes are not counted. Pulling a piece by a point beyond its middle (towards where it goes) counts as a rope pull and gets far more strength. So the same push works or not depending on which half of the piece was grabbed. Proposal: count the pieces it pushes the same way as the pieces resting on it, so pushing gets the effort the whole row needs (up to the arm's strength), wherever the piece is grabbed.

## Current state, update 51 (15 Nov 2026 night): owner cue list

Owner, verbatim: "we need some more work on cues: explain somehow that the dotted outline should not be filled. ALSO, at some playtesting i did, the lvl1 failed at the wind test, and then at the secont test effort, it suceeded allt ests, but there was no bubble for the ehadpiece and earhquake, so you ahve to make them appear not just on the first est, but on teir first eppearance isntance. also cnage to "O plithos thrimmatistike apo to varos" to "Nai, oi plihtoi spane, den einai geroi san petra"."

Results (`python3 tools/harness.py cuetest`, 28 tests, all pass):
- Dotted outline: a new teaching step on the first site, after «Τώρα χτίσε!»: line 136 «Βλέπεις τις τελείες; Εκεί θα κατέβει η κορωνίδα στη δοκιμή. Μην χτίσεις μέσα τους.» with the dotted outline glowing. And whenever the child lets a piece go inside it (once per visit): line 137 «Οι τελείες μένουν άδειες! Εκεί θα κατέβει η κορωνίδα.» Tests first-site-teaching, dotted-outline-covered.
- The wind, headpiece and earthquake explanations each play the first time that part of the test is reached, whichever test that is. Test test-explained-at-first-reach (the owner's case: the first test fails in the wind, the second passes and explains the headpiece and the earthquake).
- Line 72 is «Ναι, οι πλίνθοι σπάνε, δεν είναι γεροί σαν πέτρα.»
- Found while testing: input timing (taps, the pile settling, the button turning green, the parent key) ran on the computer's clock, so test runs could differ; it now runs on the game's own frame clock. Same for the player.

## Current state, update 52 (15 Nov 2026 night): owner list

Owner, verbatim:
1. "Make the shovel cue appear on 3 pieces, not 4."
2. "make red button que appear on 8."
3. "in first level, a mudbrick broke and I saw no cue, you ahve done something with it, this que is not supposed to play while another tutorial cue is playing, not disappear compeltely from 1st lvl, or whatever you avhe done."
4. "in Mycenai, the outline is straight on the sides, while the pieces cant fit it, the 2 oblong pieces. this must be solved, but im afraid to tell you to change block dimensions, and also I dont want you to amke outline indentations. I prefer you to move the upper stones a bit inwards, adn so the headpiece becomes a bit smaller (less wide and less tall), but make sure it can still break a wooden lintel"

Results (`python3 tools/harness.py cuetest`, 28 tests, all pass; Lion Gate level checks all pass):
1. The shovel step waits for three pieces.
2. The red-button step waits for eight pieces.
3. Rule changed: other lines are dropped only while a teaching line plays or waits its turn, or a step waits for the child; in the free building between steps they play (the previous rule dropped them for the whole teaching). Test first-site-teaching: a mudbrick falling and breaking between steps says line 72.
4. Lion Gate: the upper row (two blocks, two squares) and the two flagpoles moved 0.2 inwards, so the row ends where the lintels end; the lion triangle 2.5 wide and 2.22 tall (was 2.9 and 2.58), locked in the level spec. The wooden-lintel wrong build still breaks in the test. Picture `owner-shots/liongate-15nov-upper-stones-in.png`.

## Skies test (branch skies-test, 15 Nov 2026 night; not on main)

Owner, verbatim: "can you make a test file where you add these gradients for files? I want you to divide in day skies , adn night skies. day skys are for when the level is being built. for each site, avoid skies that dont contrast well with the main materials of the building. each site has a day sky assigned to it, try to not reuse the same ones more than 2 times, ideally one sky for each site. under the constrast condition said above, and only this is ever used for this site. BUT when a site is finished,  then there is a rotation of night skys, kind of from sunset to early sunrise, that rotate between all finsihes sites (so, you go to built -> DAY OF THE SITE, you go out and click a finsiheed site or even many -> the night sky progresses)"

Built: the owner's 18 gradients (src/art/skies, 160x120 copies). Day skies by colour difference from each site's mudbrick, wood and stone (textured and plain), at least about 20 (CIE Lab): mastaba ken, djoser aug, ziggurat bah, liongate sno, karnak dro, ishtar air, parthenon omb, mausoleum sno, pharos day, valens omb (8 skies, sno and omb twice: only five skies stand out from marble). Left out of the day: ora (too close to sandstone, wood and mudbrick), sen (too close to everything). Night rotation, one step per visit to a finished site, saved: son, ice, dus, nac, twi, mon, cit, mor, ora. Picture owner-shots/skies-15nov-test.png.

Owner, verbatim: "the gaps in the building outline should also get that overlay. also, the overlay you chose for acropolis and valens, should be a night overlay."
Done: openings in the outline are cut out, so the sky shows through them (they were painted plain blue). omb moved to the night rotation (after ice); day skies now parthenon air, valens aug (air, aug and sno each used twice). Picture owner-shots/skies-15nov-test-2.png.

Owner, verbatim: "first of all, chave your code, so that when a site is destroyed and becomes red again, when you enter you enter at its day. you ahve some spagetti code somewhere, each site is tied to its day when you go to built. thats it. fidn a way to code things clearly, not patches and hacks. secondly, I dont know, but in my eyes, the day.png woudl contrast more with marble than your choise. you have an error in your color contrast logic"
Done: the sky follows the site's state in one place: being built (never finished, or damaged) shows its day sky; standing finished shows the next night sky. Test sky-follows-site-state (Mastaba built and passed for real, visited twice, then its headpiece knocked off).
The contrast logic was wrong: it compared colour lists (any material colour against any sky colour, worst pair) with the old CIE76 difference, which overrates blues and violets. Now tools/sky-contrast.py measures the real picture: the quick-built site under each sky, textures on and off, CIEDE2000 between each sky pixel along the building's edge and the building just inside it, averaged. day.png does beat the earlier choice for marble (Parthenon: day 27, air 21). New day skies (the weakest site as strong as possible, each sky at most twice): mastaba air, djoser dro, ziggurat dro, liongate sno, karnak aug, ishtar air, parthenon sno, mausoleum aug, pharos day, valens ora. Weakest site 30 (was 21).

## Current state, update 53 (15 Nov 2026 night): skies kept, Mausoleum demos

Owner, verbatim: "ok, keep that. now I want you to change the demos in halicarnassos: the wrong one should first palce the left lintel, then the right, to show how the right doesnt stand and almost falls. the correct demo should place the wood where both lintels can sit on it."

Results (`python3 tools/harness.py cuetest`, 29 tests, all pass):
- The skies (section "Skies test" above, branch skies-test) are merged into the game.
- Mausoleum wrong way: the left lintel, then the right one; the right one tips over onto its column. It is set 15 cm off the left one: set touching, its end catches on the left lintel's end and it stays up.
- Mausoleum right way: a wooden post under the joint of the two lintels, both lintels on it, three roof stones; the post tapped out, both stand. Test demos (also checks the post is gone at the end). Picture owner-shots/mausoleum-demo-15nov.png.

## Current state, update 54 (16 Nov 2026): settings, sandbox icon, cues.md layout

Owner's words: "# make parent mode, that is without level demos (still we have all the other cues, just not the level demos), with a settings gear button that opens a popup panel with that checkbox option, and an X to close the popup, all big and bold, remember its for kids, and the text should say (of the option) VOITHITIKA VIDEO # better sandbox main screen icon, make 3 stacked blocks, 2 bot 1 mid. # change https://github.com/npgeorgiou/kid-games/blob/main/games/arxitektones-tou-arxaiou-kosmou/cues.md so that the explanation of when it plays is first, in bold, and then teh greek text. this way I cn know what I read and make small changes on the fly as I speak"

1. Settings: a gear button top right on the map opens a big box with one tick box, ΒΟΗΘΗΤΙΚΑ ΒΙΝΤΕΟ, and a big red X. Unticked, no site plays its demo; every other cue stays. Ticked by default, remembered, kept by ΕΠΑΝΕΚΚΙΝΗΣΗ. The gear and its box can always be touched, also while a cue darkens the map. Test: `harness.py cuetest demos-off`; real-mouse check of gear, tick and X.
2. Free play button on the map: three stacked blocks, two below and one on top in the middle.
3. `cues.md` (written by `tools/cues_doc.py`): every cue, teaching step, demo and line now starts with the explanation in bold, then its Greek text on the next line.

## Current state, update 55 (16 Nov 2026): ΔΙΔΑΣΚΑΛΙΑ tick

Owner's words: "add another checkbox for teaching cues, by default clicked" (after he unticked ΒΟΗΘΗΤΙΚΑ ΒΙΝΤΕΟ and still got the Mastaba teaching: "i had it unclicked, and the 1st lvl cues played").

- The gear box now has a second tick, ΔΙΔΑΣΚΑΛΙΑ, ticked by default, remembered, kept by ΕΠΑΝΕΚΚΙΝΗΣΗ. Unticked: no teaching steps (the Mastaba starts with no see-through hand and no step lines) and no teaching lines anywhere; every other line stays, and the demos follow their own tick. Ticked again later, the teaching starts where it was left. Tests: `harness.py cuetest teaching-off demos-off`; real-mouse check: untick, reload, enter the Mastaba, nothing teaches.

## Current state, update 56 (16 Nov 2026): intro art received

Owner's words: "the iamges have larber byte sizethan what you suggested, make them a bit smaller but wihout losing quality visually". Ten site pictures (1376x768) re-saved as JPG quality 86, full colour detail, about 190-330 KB each (were 830-1040 KB), in `art/intro/`, named by site key. Owner: "full screen, with a slow zoom in, very slow". Built: moved to `src/art/intro/`; the site's picture covers the whole screen while its welcome line plays (finished sites, which get a fact line instead, show none), fades in over half a second, grows 1.2% per second, and fades out over 0.8 s when the line ends. Without recordings the line is a 2 s text box, so the picture shows about 2.5 s; with a recording it lasts as long as the recording. Real-program check: tapping the Mastaba on the map shows the picture, then the site. Owner later: a corrected Valens picture (kept as he sent it, 171 KB, already small), and copies with a red square on each marking where the eye should go. The square centres are stored per picture (share of width and height); the zoom grows around that point and moves it 4% of the way to the screen middle each second, never letting a picture edge come inside the screen.

## Current state, update 57 (16 Nov 2026 night): owner list of 15 points

Owner, verbatim: "1. in the 1st level tutorial, add after the kid drags the piece back to the sidebar, flavour text that isntead of saing for a third time "take a piece and put it in the design" it sais "vale tora merika kommatia na sou deikso kati akoma". 2. the wood 1st time click cue should play, like for the mudbrick, after the tutorial cues are done. actually, when does the mudbrick 1st time itneraction cue play? 3. make ESC take you away from lvl or sandbox. 4. in the sandbox, remove the biggest, second biggest, fourth biggest woods, and in the sidebar choices, put all oblong planks horizontally so the user can see their height difference. also amke sidebar in sandbox same size as in the levels, and actually instead of the click and choose mechanish you ahve now, its better if you add all materials one times each on at the pile, same as for the levels, and they get replenished each time you pick one, a new falls from above to replenish it. thats better. 5.  the voice/bubble cues after a wrong/right demo are a bit too slow, maybe 2 seconds too slow. 6. the lvl image and intro should play only when you go to build, and it not done yet, thes times, not when it is destroyed and you go to fix it. 7. replace demo que with: "Pano se kathe kiona, vale 2 petres gia kionokrano, kai pano tous storikse to dokari". 8. in your cues, the "tells" is happenign WHILE the demo palys, or before? 9. do we have wood witht eh smae size as the karnak columns? if so, give them to the kid as options. 10. make auto building 1/3 faster. 11 ESC should skip level intros. 12. parthenon, remove mudbrick and give me enough materian to build wooden parthenon except of 2 base rows. I want the kid to ahve the option to amke it wooden too. 13. in Halicarnassus, your wrong/right demos make a thumb sound when theys tart, as if stones ate thumpjg falling down. fix that. 14. in Karnak, in the wrong/right demos, have the base ready, like in Halicarnassus, to save time. 15. Alexandria sky, consider it a morning sky, put it in the right palce in the progression of "night" skies, and give alexandria anothre conrast fitting sky, according to your earlier examination. Same for valens, cosider it a sunset sky, and give it something else, contrast fitting."

1. Step t-drag-3 says new line 138 «Βάλε τώρα μερικά κομμάτια, να σου δείξω κάτι ακόμα.» (test first-site-teaching).
2. pick-mudbrick and pick-wood are "keep" lines: dropped while the teaching talks or a step waits, they play once the site's teaching is over (test wood-first-pick). Answer given: the mudbrick line plays the first time a mudbrick is picked up while no teaching line plays and no step waits (on the Mastaba, in the free building after the shovel line); now also, if that never happened, once the teaching is over.
3, 11. ESC ends the line playing (the intro and its picture with it); with no line playing it leaves a site or free play for the map; not during a demo (test esc).
4. Free play: no 14 m, 12 m or 9 m plank; the sidebar is a pile like the levels' (same size), one of each shape of each material; a piece taken out is replaced by a new one falling in from above; a piece carried into the sidebar is gone; the wooden planks (3.2, 6, 8, 10 m) stand on end side by side (reading: "horizontally" = in one row, so their heights compare). No test button in free play. Test free-play-pile; picture owner-shots/2026-11-16-free-pile-karnak-demo-parthenon-pile.png. The old free-play tile tests in tools/harness.py (startFree + shapeTiles) test what the owner replaced.
5. Every wait before a line in a demo 2 s shorter, at least 0.5 s (Step Pyramid, Ziggurat, Karnak, Mausoleum).
6. site-intro only if the site was never won (new condition site-won-before); a damaged site gets no intro or picture (test intro-only-before-won).
7. Line 114 (Karnak demo) now «Πάνω σε κάθε κίονα, βάλε δύο πέτρες για κιονόκρανο, και πάνω τους στήριξε το δοκάρι.»
8. Answer given: a "tell" line starts together with the pieces it describes; the hand starts carrying them at once, while the line plays. The demo itself starts only after the lines before it have played.
9. Yes, the wooden post is the column's size: four wooden columns added to the Karnak pile. Built with wooden columns, Karnak passes its test (tools/harness.py variants).
10. Quick build a third faster (speed 60 -> 80 m/s, pauses x 0.75).
12. Parthenon: the mudbrick wrong choice removed; wood for everything above the two steps (18 squares, 6 capitals, 5 blocks, two pediment halves). Built of wood above the steps it passes its test. Its pile is now 123% of the sidebar height by the spec count (top pieces sit above the bin, like Valens).
13. A demo's ready pieces are set down without a landing sound.
14. Karnak demo: platform and both columns ready; the hand brings the two small stones on each column and the beam.
15. Night rotation now ora (sunset), son, ice, omb, dus, nac, twi, mon, cit, mor, day (morning). New day skies from tools/sky-contrast.py: Valens ken (28, best not used elsewhere), Pharos sno (36.6, best; a third use of sno, since every other strong sky is already used twice).

All ten levels pass the quick build + test; all cue tests pass.

## Current state, update 58 (16 Nov 2026, late): owner list of 4 points

Owner, verbatim: "1, sandbox: there is something wrong in your physics, I cannot pull the lever down, from its left side. 2. "hat line plays as soon as the teaching ends, without another pickup???" by then the kid cant connect it, moron. make mudbrick as it was before, and make wood the same as mudbrick (cue). 3. halicarnassus doesnt need 3 cues for the demo, only 2, one that plays during the wrong, and one during the right 4. Make it so "when you tap finger on main map, add appropriate particles: in water: A splash and concentric circles / in desert: sand cloud / in green area: vegetation particles / in mountain: rock particles / add sound hooks too. " I give you the sound files, equalize them in that way: this is a php script you avhe give me. I see it failing on one file, and on antoehr it doesnt seem to suceed to eqaualize it, it soudns too strongly. but find a way to equalize them tot eh level the script says, thsi is how all the otehr game soudsn are equalized too" (with a picture: a long plank across a round wooden drum on two stone squares with a small stone between, its right end on the ground).

1. Cause: the wrist held the plank's turn with the arm's whole pull times the grab point's distance from the middle (about 1000 N m held at the end of a 10 m plank), so the plank could not turn about the drum. The wrist now holds against the arm's pull, like against the weight, only as far as the middle third reaches (grabbed in the middle third: unchanged). Owner test `lever` (his build, pulled 2 m down in a second at mouse rate): 0 m before, 1.98 m after; every other hand test gives the same results as before; picture owner-shots/2026-11-16-lever-pulled-down.png (the real game, real mouse).
2. pick-mudbrick and pick-wood are no longer "keep" lines: each plays the first time that material is picked up while no teaching line plays and no step waits; never later without a pick-up (test first-pick-only-on-pickup; replaces wood-first-pick).
3. Mausoleum demo: line 121 (after the post is taken out) removed from the demo and from the lines; 129 during the wrong way, 130 during the right way; after the post is out a 1 s wait, then the fade (test mausoleum-demo-two-lines).
4. Map taps: water (where the land picture has none, or the picture is blue: rivers, lakes) a splash of drops and three spreading rings; on land by the picture's colour around the tap: green -> leaves, pale sand -> a sand cloud, the rest (browns, greys) -> stone chips and a little dust. Sounds map-tap-water/sand/green/rock (owner's files: water splash, sand hit, ground-foliage hit, rock-hit). Picture owner-shots/2026-11-16-map-taps.png.
   tools/normalize-sounds.php rewritten: the old loudnorm could not measure sand hit (0.2 s, shorter than the 0.4 s a loudness measure needs) and switched to its compressing mode on rock-hit (its peaks were too high for a plain volume change), which made it harsh. Now: silence added for measuring, one plain volume change, a peak limiter only on peaks over -1.5 dBTP, re-measured until within 0.3 LU of -16 LUFS. All four new sounds: -16.0 to -16.2 LUFS, peaks -1.7 to -2.6 dBTP. Measured the same way, the older game sounds are not all at -16 (the hits are -16 to -26 LUFS); not changed.

## Current state, update 59 (16 Nov 2026, late): owner list of 6 points

Owner, verbatim: "1. make the 4 new sounds 20% less sound, except of rock, which will be 50% less. 2. make dust cloud bigger, and vegetation have a few more particles that spread more upwards and a bit wider. as for the stone particles, make them explode upwards more, now they mostly fall down a lot. 2. about your plank explanation, its unnatural I can lift it up from anywhere but not pull it down from anywhere (only from it end). dont break anything, dont amke uunatural hacks and patches, DONT BREAK ANY EXISTING BEHAVIOUR, but fix it. 4. on quick build, stop on ESC 5. the intensity of the sound that objects make when they hit the ground bust be relative  to their mass, use current std 2m rectangular blocks are reference points. 6. reduce main menu music volume by 20%"

1. Map-tap sounds: water, sand, green 0.8 -> 0.64; rock 0.8 -> 0.4.
2. Map taps: sand cloud 20 puffs, about 1.5x bigger and growing faster; leaves 15 (was 10), faster, spread over a wider fan; stone chips thrown upwards (between 45 and 135 degrees, faster, less pull down). Picture owner-shots/2026-11-16-map-taps.png.
3. Wrist: against the arm's pull it now holds only the share of the pull that moves the piece itself (piece weight / weight moved, the same share the arm already uses); the share pressing into what the piece pushes on turns nothing in a free piece. Owner test `lever` now pulls down at 0.4, 1.5, 2.5, 3.5 m from the raised end and lifts at four points: 2.5 and 3.5 m failed before (0 m), all pass now. The other hand tests give the same results as before (pushes differ by 0.01 m).
4. ESC during the quick build stops it where it is (the piece in flight is set down); test `esc-quick`.
5. A piece hitting the ground (falling or set down by the quick build) sounds at its weight in 2 m blocks of its material times the old loudness (a block as before, a square half, a big square twice, up to the loudest the sound file has); test `hit-weight`.
6. Map music 0.2 -> 0.16.

## Current state, update 60 (17 Nov 2026): owner list of 8 points

Owner, verbatim: "1. make the same 20% and 50% reduction to the terrain hits once more, further. 2. the rocks spread further than the other particles do, collect them a bit more. 3. did you make only smaler pieces that the reference thud less loud, or also  thse with more mass thud more? you should. 4. there is a bug with the biggest oblong piece in teh sandox sidebar, it gets dragged out and it has a lot of speed, there is a  bug somewhere, and once I saw the same with the big stone boulder, that has the same mass as the big oblong stone, but that even without coming out of the sdikebar. 5. be mindfull to be adding tests for the things you do. 6. see if you can equalize the sounds of the materials thudding, banging, breaking, etch, I feel they are uneven. after you do that, decrease/increase according to mass. the baseline is the rectangular 2x1 m pieces. 7. after you are done with that, reduce level of all sounds generally by 50%, I ahve it at 34% sound at my laptop and I hear them loud and annoying. 8. reduce main map music by 10% more."

1. Map taps 0.512 (water, sand, green), rock 0.2.
2. Stone chips: slower (110-180 px/s) and a narrower upward fan (54-126 degrees). Picture owner-shots/2026-11-17-map-taps.png.
3. Answer: both, but a heavier piece was held at the sound's full loudness on a hard hit. Now a sound can go up to twice the block's loudness (with everything at half, point 7, that is the old full loudness).
4. Cause: the sidebar hand moved every piece at the same speed whatever its weight, and slowed only the piece's middle, so a piece held near its end was set spinning. A two-block stone came out at up to 777 px/s, and the arm in the building area, nearly all its strength holding it up, could not stop it. Now the sidebar hand moves the held point no faster than the arm can move that weight in the building area (the arm's own top speed, armTopSpeed), slowing moving and turning together. Owner test `sidebar-speed` (10 grabs, real mouse rate, centre and ends, slow and fast): the long stone block and big stone square failed before (410-558 px/s), pass now (at most 76 px/s; the arm's limit for two blocks is 107); a long block and a wooden block grabbed near an end still hang down in the sidebar. Every other hand test gives the same results as before.
5. New tests: owner `sidebar-speed`, `sound-levels`, `hit-weight` (now hits, breaking, sliding); harness `loudness`.
6. Material sounds (all hits, crumble, snap, drag-stone, drag-wood) brought to -16 LUFS with tools/normalize-sounds.php (up to 25 rounds now), all at 0.8 in the table; hits (every hit, not only on the ground), breaking and sliding are louder or quieter by the piece's weight in 2 m blocks of its material.
7. MASTER_VOLUME 0.5 on every sound, music and voice.
8. Map music 0.16 -> 0.144.

## Current state, update 61 (17 Nov 2026): waves push boats, load screen, game renamed

Owner, verbatim: "make the cocnentric waves from the clicks, push the boats away from their route, according to the cocnentric circles direction, and of course then the boats continue smoothly toward their destination, after having been pushed. also, when the game starts, use this load screen for 2 secs. also, rename game in GitHub (and folder) to ARXITEKTONES TOU ARXAIOU KOSMOU" (with the title picture, saved as src/art/loading.jpg).

1. Each ring of a water tap gives a boat it passes a push away from the tap (weaker for the later, fading rings); the boat is drawn off its route by that push and a critically damped spring brings it back smoothly while it keeps sailing (BOAT_BACK). Owner test `wave-boat`: pushed about 40 map px straight away from the click, back on its route within 6 s, no jump.
2. Load screen: the title picture full screen for 2 s at start, then it fades and the map starts (the welcome line starts after it). The harness sets LOAD_SCREEN_MS to 0.
3. Renamed: folder games/arxitektones-tou-arxaiou-kosmou, game file arxitektones-tou-arxaiou-kosmou.html, browser tab title "Αρχιτέκτονες του αρχαίου κόσμου". The repository stays kid-games (it holds the whole library). Saved progress keeps its old storage name, so nothing is lost.

## Current state, update 62 (17 Nov 2026): one smooth wave push

Owner, verbatim: "the waves puth the boat in 2 goes, the motion is not smooth"

Cause: each of the three rings gave the boat its own sudden kick as it passed, so the boat sped up twice. Now only the first ring pushes, and it pushes gradually while its front (30 screen px wide) passes the boat; the other two rings are only drawn. Owner test `wave-boat` now also counts how many times the boat speeds up going out: 2 before, 1 now; pushed about 40 map px, back on its route within 6 s. Frames from the real game, a quarter second apart: owner-shots/2026-11-17-wave-pushes-boat.png.

## Current state, update 63 (17 Nov 2026): dunes are sand for map taps

Owner, verbatim: "the sand hills of africa and arabia are counted as mountains by you, for the aprticle effects."

The map picture's shaded dunes are darker orange-tan, so the old colour rule (pale = sand, the rest = mountain) called them mountains. Now strongly coloured warm tan (hue 28-50, saturation at least 0.3) is sand too; the drawn mountain peaks (dull grey, mauve, brown) stay mountains. The brown hatched highlands of Anatolia and Iran are warm tan as well and now give sand. Owner test `map-ground`: nine places (dunes in Arabia and the Sahara, pale desert, peaks in Sinai, Arabia and Greece, sea, Nile valley); a dune failed before, all pass now.

## Current state, update 64 (17 Nov 2026): mountains drawn by hand for map taps

Owner, verbatim: "you tire me. you ame many mountains as sand. can you distinguis them? every human can, even 1 year old"

Colour alone cannot tell the map's dunes from its hatched ranges (both warm tan with brown strokes). Now the kind of ground is a picture, src/art/map-ground.png (a quarter of the map size: blue water, green land, sand, brown mountains), made by tools/make-ground.py: water and green from the map's colours, mountains from shapes drawn by hand around every painted peak and range (Balkans, Pindus, Caucasus, Armenian highlands, Taurus, Zagros, the hills east of the Nile, the peaks of Libya, Sinai and Arabia), the rest of the land sand (so central Anatolia's plain is sand). The shapes are in the script, in map pixels; edit and rerun to change them. Picture of the result over the map: owner-shots/2026-11-17-map-ground.png. Owner test `map-ground` now has 19 places (7 more ranges and peaks, 3 more dune fields): Zagros, Caucasus and Armenian peaks were sand before, all right now.

## Current state, update 65 (17 Nov 2026): wave push never double

Owner, verbatim: "the boat pushing still feels double somethimes"

Cause: whether the wave's front was passing the boat was measured at the boat's pushed place. A click close to a boat pushed it out ahead of the front; the front then caught up with it and pushed it again. Now it is measured at the boat's place on its route, so the front passes each boat once. Owner test `wave-boat` now clicks at eight places around a boat, near and far: clicks 8 px from the boat pushed twice before, every click pushes once now (far clicks, whose rings fade before reaching the boat, push nothing).

## Current state, update 66 (17 Nov 2026): gentler wave push

Owner, verbatim: "you now push them too far away and violently, that especially noticable when the click is right ont he boat"

The push is a quarter of what it was: a click right on a boat moves it about half a boat (27 map px, was 106), a click a little away less; it starts and stops gently. Owner test `wave-boat` also clicks right on the boat and requires at most 30 map px: failed before, passes now.

## Current state, update 67 (17 Nov 2026): wave push doubled

Owner, verbatim: "god youa nnoy me. now the barely push. double the current force"

Push doubled (200 -> 400): a click right on a boat moves it about a boat's length (about 53 map px). Owner test `wave-boat`: a click on the boat moves it 45-60 map px, still once and smoothly.

## Current state, update 68 (17 Nov 2026): map boats drawn in 3D

Owner, verbatim: "can you make anything to make the boats change shape as they turn and move in different directions? now its the same image, just rotated sometimes. are there any suggestions? like even 3d?" Offered: pictures from 8-16 directions, a 3D model, or a boat drawn by the game in 3D. Owner: "pick 3rd, try to give it the color and shape of the current boat".

SKIN.mapBoat now draws the boat in 3D from points (hull of 14 sections with raised curled ends, one mast, yard, a cream square sail with two red stripes, rigging, dark ink lines), coloured like art/boat-owner.png, seen from the south 30 degrees above the sea, drawn far to near. The wind blows from the north: the yard is braced to lie across it (at most 60 degrees each way from across the boat) and the sail fills to the south, so it mostly shows its face. Travellers sit along the boat's middle, only heads above the near side. The wake starts at the stern whatever the heading. The owner's boat picture is no longer used. Picture of the boat in eight directions: owner-shots/2026-11-17-boats-3d.png. Owner test `boat-3d`: the boat sailing east, south and north-east covers different shapes.

## Current state, update 69 (17 Nov 2026): boats turn smoothly, curved sail

Owner, verbatim: "exellent. but the turning is not smooth, it just jumps to another orientation. also the sail is not curced, its traight. about the not smooth rotation, maybe the problem is that your sea routes are angular and not bended"

1. Sea routes rounded at load: each leg walked in 4 px steps, each point replaced by the average of the points up to 40 px each way along it (twice); in narrow straits (the Dardanelles) the average is made narrower so the route stays on water, changing gradually; ports kept.
2. A boat now points its own way (b.hd) and turns towards its course at most 1.5 radians a second (BOAT_TURN), also turning round in port.
3. Sail: the foot sags in the middle and the sides bow out, so its edges and stripes curve.
Owner test `boat-turn`: a minute of sailing at 60 frames a second, largest turn in one frame 1.4 degrees (pointing), course bends at most 19 degrees in a frame (only in the Dardanelles), no rounded route point on land away from the ports. Pictures: owner-shots/2026-11-17-boats-3d.png (eight directions), owner-shots/2026-11-17-boats-turning.png (the real map, 0.7 s apart).

## Current state, update 70 (17 Nov 2026): writing in the sand, boats dragged and carried

Owner, verbatim (17 Nov 2026, 12:33): "1. make it so not tapping, but dragging on the sand plains of africa and arabia, leaves aline on the sand, so the kid can draw and write there. the sandhills shouldnt be in that area. also, 2 mins after the first stroke in each area is made, a wind blows that erases the writing, the wind must be local in that area only. 2. make it so the boats are draggable, and if the kid leaves them on land, then the humans go out, pick up the boat on their shoulders, and carry it to the sea again, and then they go on again adn they continue sailing."

1. Writing in the sand: a finger dragged over the flat sand of Africa or of Arabia leaves a groove; a tap still throws sand (on flat sand the tap now shows when the finger is let go without moving). The Gulf of Suez and the Red Sea divide the two areas (Sinai and the Syrian desert count as Arabia); Anatolia's plateau is not a writing area. Dunes take no lines: `tools/make-ground.py` now marks the painted dunes (Egyptian ridge, central and south-east Arabia) in their own colour in `art/map-ground.png`; a tap there still throws sand. Two minutes after an area's first line a wind blows over that area only, from the north, its front crossing the area in 4 s with blown sand, wiping the lines behind it; the next line starts a new two minutes. Restart (ΕΠΑΝΕΚΚΙΝΗΣΗ) wipes the writing.
2. Boats: a boat can be picked up and dragged; it points the way it is moved, its travellers stay in it. Let go, it goes back to the nearest point of its route by the way that needs the least carrying, then the shortest: over water it sails; over land its travellers step out, lift it onto their shoulders (1 s), carry it at walking speed (three each side), put it down at the water (1 s), get in and sail on. A boat with nobody aboard that would need carrying stays where it was left until dragged again. A tap on a boat on its route still makes waves; picking up a carried boat puts the carriers back in it.
Owner tests `sand-writing` (11 checks) and `boat-drag` (8 checks). Picture: owner-shots/2026-11-17-sand-writing-and-boat-carried.png (`tools/harness.py mapshot`).
Open for the owner: an empty boat left on land stays there (nobody to carry it); say if it should be different.

## Current state, update 71 (17 Nov 2026): one boat per finished site, empty boats wait; held boats over a shadow; smooth deep grooves

Owner, verbatim (17 Nov 2026, 18:27): "1. make it so there are no empty boats sailing around: each site that is finished makes a boat full of people appear, and the people do their rounds on land, and tthen they go back to their boat, that is waiting for them on the point they stopped. if a stopped, empty boat is moved, its people go there to pick it up.  2. when I pick up a boat, it shouldnt be rotating. 3. when I leave it on land, make a hook for  a disapointment sound I will give you later. then, after that soudn is done, and a second later, the people carry the boat, not immediately. 4. when I drag a boat, I want a shadow under it. when I drop it, it should drop on the point its shadow is, with a spals (same as the click splash), that also created waves that push other boats. 5. your sand draying is jagged, i want ti smooth and able to do curves. also, i want it to be more visibly as a groove, like, the light/darkess conrtast that we use to show indentations. udnerstoood?" Answers (18:35): "routes: theya re not connected to routes, only route count. so, similar route logic. yes game starts with 0 boats. they finish" (the moved boat's people finish their round first).

1. Fleet: the game starts with no boats; each finished site adds one boat with its travellers (the n-th finished site the n-th route; `syncFleet`, ALL_BOATS/ALL_GROUPS). Travellers get off where a finished site is walkable; their boat waits empty at that point of its route (`b.parked`). Their round: on to finished sites they can walk to (at most three), then back to their own boat (`goHome`); the old taking of other boats between sites is gone. A moved empty boat stays where it was left (`b.stuck`); when the round is done they walk to it over land: on land they get in and carry it to the water; on the water they wait on the nearest shore and it comes to them (the only time a boat moves empty, to fetch them), then they sail back to the route. If it is moved again while they walk, they turn to where it is now; with no way there over land they wait and try again every 4 s.
2. A held boat does not turn.
3. Left on land: sound hook `boat-left-on-land` in SOUNDS (empty until the owner gives the file); a second after it ends the travellers lift and carry (`back.delay`). Also played when an empty boat is left on land.
4. Held, the boat is lifted (0.2 s) over a shadow on the ground; let go, it falls (0.2 s) onto the shadow's point, with the tap effect there (on water the splash, whose waves push other boats; sand or stones on land).
5. Sand: the finger's points (every 3 map px) are joined by quadratic curves through their midpoints, so fast strokes come out round. The groove is three layers of the same line: a dark wall shifted up-left, a light wall shifted down-right, a darker floor in the middle (lit from the top left).
Owner tests: `fleet` (4), `boat-drag` (rewritten), `sand-writing` (13).

## Current state, update 72 (17 Nov 2026): boat lifting and dropping, the left-on-land sound, smoother sand lines

Owner, verbatim (17 Nov 2026, 20:31): "forget it, see that: 1, thre is a delay between teh boat falling and the drop effects happening. 2 when I lift a boat it should go away from my hand, instead make the shadow drop. 3. this is the disappoint ment sound: trim it cause the sound is not in start and end of file, and normalize it as other sounds are, then reduce it to the same way the terrain tap effects are. 5. sand still feel a bit jagged, there must be some way to smoothen either the line (maybe you dont really follow the movement) or the movement (if the movement is somehow jagged in small, computer mouse ways). also ther is a small lag from when motion starts to the line being started to be drawn, and also I want the light/dark groove effect a tiny tiny bit more" ("forget it": the green test button report of 20:12, which could not be repeated; cue test `settings-test-button` kept.)

1. The let-go boat falls faster and faster (as things fall) and the splash comes in the frame it reaches its shadow (before, the eased fall looked landed for several frames before the splash).
2. Held, the boat stays at the finger (it follows from the first touch); once dragged, its shadow drops away below it (BOAT_LIFT_H). A tap on a boat on its route moves it back smoothly.
3. `src/sounds/boat-left-on-land.mp3`: the owner's disappointed crowd, trimmed to the sound (0.54-2.10 s), peak-normalised to -1.5 dB like the others, played at the map taps' 0.512. The carrying starts one second after it ends.
5. Sand lines: a pen follows the finger by part of the gap (more when it moves fast), averaging away a mouse's small steps but keeping quick sharp turns; points every 8 map px, joined by quadratic curves; the bit from the pressed line to the finger is drawn live from the first touch (no lag). Groove walls shifted a little further and the shade a little darker.
Owner tests: `boat-drag` (15, the waiting-boat part now set up directly: 55 s), `sand-writing` (15).

## Current state, update 73 (17 Nov 2026): no hitches on the map, carrying half a second sooner, tests in seconds

Owner, verbatim (17 Nov 2026, 20:51): "1. now there is lag when the boat is just about to hit the terrain, but only if the boat is full. 2. the waves no longer push teh boats, and sometimes thre is lag there too. 3. you obviosuly DONT write tests. 4. the ppl should get out of the boat half a second earlier. 5. 55 secs is still way too long, my whole java test suite takes 20 secs"

1-2. Cause, measured: the map's land grid (LAND) was allocated columns x columns x rows (104 million cells instead of 191 thousand), so every search over it (a boat's way back: 1.5 s; the travellers' walks to a moved boat) stalled the game; during such stalls taps and waves misbehaved. Fixed the size; the way back now uses a water-distance field per route (made once, 4 ms) and a 0-1 search for the least carrying (1-2 ms); straightening looks at most 40 cells ahead. `tools/harness.py realwave`: real clicks in the running game: waves push (48, 31, 12 map px), longest frame 36 ms; `maptime`: a frame 16 ms, a way back 1 ms.
4. The travellers get out half a second after the sound ends (was one second).
5. Owner tests that do not look at the screen run with a one-pixel canvas (`quick` in owner-tests.js): boat-drag 3.5 s, the five map tests together 10 s. boat-drag sets up waiting boats directly and starts from a restart; it checks the slowest frame when a full boat lands.

## Current state, update 74 (17 Nov 2026): waves push moved boats too

Owner, verbatim (17 Nov 2026, 21:03): "seriosuly, are you stupid? the fuckign waves, i told you before, dont push the boats anymore"
Cause: a boat the child had moved (sailing back to its route, or left empty on the water) ignored waves; in play many boats are in that state. Now every boat floating free gets the same wave push and spring as on its route (not while held, falling, carried or on land). Check in `boat-drag`: a boat sailing back is pushed (17 checks, 3.5 s). `tools/harness.py realwave`: every boat in play clicked beside in the running game, all pushed; `maptime`: slowest frame in 5 min of play without drawing 14 ms.

## Current state, update 75 (17 Nov 2026): a dropped boat is not pushed by its own splash

Owner, verbatim (17 Nov 2026, 21:09): "a boat is now lushed BY ITS OWN WAVE. also, the wave doesnt seem to push teh same way from teh sides and from front/back, is this ok for a physics reason, or a bug?"
A ring remembers the boat whose drop made it and does not push that one (check in `boat-drag`, 18 checks). Question answered, waiting: the push does not depend on which way a boat points; rings are drawn flattened (height 0.6 of width), so a tap above or below a boat reaches it later and weaker than one beside it at the same screen distance.

Owner (21:12): "do it". A boat is now pushed as hard as by a tap the same screen distance beside it, whichever side the tap is: the push follows the front's progress past the boat measured on the screen, and the pushing ring keeps going (already faded) until it has reached as far up and down as sideways. Owner test `wave-even`: 26.5 map px from all four sides at 25 px, 7.0 at 45 px.

Owner (21:17): "boat must make disappoitnment sound only when dropped full of people." Done: the sound plays only when a boat with its travellers is left on land (an empty one is silent). `boat-drag` checks both (20 checks).

## Current state, update 76 (17 Nov 2026): the voice recordings

Owner, verbatim (17 Nov 2026, 21:32): "the cue files. some files are like n.1, n.2, etch named. they belong tot he same cue, so unite them, and put 100 ms of silence between them maybe"
`src/sounds/voice/N.mp3`: the owner's recordings; lines recorded in parts (3, 4, 6, 8, 9, 25, 56, 58, 62, 78, 89, 98, 106) joined in order with 0.1 s of silence (mono 44.1 kHz, 128 kbit/s). Lines with no recording (text box as before): 130, 132-138. Recordings with no line in the table (kept, unused): 97, 108, 120-123, 131. Not used: "Recording (19)_164.mp3" (no line 164).
A recorded line now ends by the game clock at its recording's length (build.py puts the lengths in VOICE_SECONDS, from ffprobe), not by the audio's own end event, so tests and play agree. The cue tests switch the recordings off (`useVoices`) and test the rules with the text box's time; cue test `voice-recordings` checks a recorded line plays to its end and that the parts were joined. The game file is now 30 MB (the recordings are in it).

Owner (21:39): line 130's recording given (added). He records from a flat list that did not have the lines added on 15-16 Nov. Now build.py writes `voice-lines.md` from cues.json on every build: lines without a recording first (132-138), then all lines. CLAUDE.md: the flat list is the only place he records from; send it when lines change.

Owner (21:47): his recordings are numbered by his own list, not by line number ("132->125 ... 138->131"). His list numbered the lines in order with one extra item at 86, so his 1-96 are lines 1-96 and from his 97 on his n is the line one place later in the table (97->98 ... 117->119, 118->124 ... 124->130, 125->132 ... 131->138; his 128 is line 135). Voice folder rebuilt with that; every line now has a recording (voice-lines.md: 0 to record). Lines 40, 43, 44, 45, 47, 73, 90: the owner recorded different, shorter words on purpose (21:53: "the purpose of the cue is covered"); keep them.

## Current state, update 77 (17 Nov 2026): map buttons top right, restart line always

Owner, verbatim (17 Nov 2026, 22:00): "now move the buttons on the main screen to the top right: on teh top row, from left to right: texture button, setting button., restart button, on second row, the sandbox. make the bigger buttons same size as the small ones ( restart/materials), and make the restart button not ahve the epanekkinisi tcapital greek text, but give the "are you sure? then double tap" cue, even when cues are disabled"
1. Map buttons (`mapButtonAt`): top right, all the restart's size; top row textures, settings, restart; free play below the restart. Picture: owner-shots/2026-11-17-map-buttons.png.
2. The ΕΠΑΝΕΚΚΙΝΗΣΗ label is gone.
3. The restart line (91, cue `restart-ask`) is no longer a teaching line, so it plays with the ticks off. Cue test `restart-ask-and-buttons`.

## Current state, update 78 (17 Nov 2026): the voice heard from the start, louder, intro ends with it

Owner, verbatim (17 Nov 2026, 22:07): "many mistakes: I am angry:1. the "welcome architect! your words await for you" does not play, is only shown as bubble. 2. when lvel intro is playing, lvl music must be half as loud, and my voice 20% louder. 3. I finished narrating lvl itnro, and the lvl itnro screen keeps there and keeps zooming, I ahd to press esc to make it go away. 3. generally make my voice louder, actually, did you normalize it as outer sounds? the lvl music is louder than my voice"
1. The map's welcome line comes before any touch, when the browser allows no sound: it fell back to the text box. Now a recording the browser holds back waits (no box) and starts at the first touch (`voiceBlocked`, started from startAudio). Checked in the running game: `tools/harness.py realintro cuetest`.
2. During a site's intro line the music plays at half (`musicDuck`) and the voice at 1.2 times. Cue test `intro-voice-and-music`.
3. A recording now ends its line at its real end (the audio's end event) as well as by the game clock at its length (update 76 had only the clock, which runs behind real time when frames are slow), so the intro picture goes when the narration ends.
4. The voice was not normalised: it was about -30 LUFS against -16 for the other sounds. All recordings (and the boat-left-on-land sound) went through tools/normalize-sounds.php (-16 LUFS, peaks at most -1.5 dBTP), the same as the other sounds; the voice plays at full share (MASTER_VOLUME), the music at its own 0.17.

## Current state, update 79 (17 Nov 2026): the test runs with the teaching off; flow tests

Owner, verbatim (17 Nov 2026, 22:21): "I refresh everything, have teaching and all cues and videos disables, i go in first lvl, i fast build with ctrl, and then i click the green button, the "lets see if it will stand" cue plays, but notest starts. motherfucker, you ahve added 0 tests, i ahve told you 1000 times. now, in your fucking claude.md, go and write that we do test drive development, that everything EVERYTHING, every happy path is tested, not in unit tests but in brawser itneraction tests, that they should also be snappy as fuck, and cover all happy paths, and major failre paths"
Cause: with ΔΙΔΑΣΚΑΛΙΑ off, the first test's explanation line (a teaching line) was skipped but still counted as said, so the test waited for it to end and stood still. A skipped teaching line now counts as not said; nothing waits for it.
Flow tests: `tools/flows.py` (`tools/harness.py flows`): the real page, real clicks and keys. first-site-ticks-off (his steps: both ticks off through the settings screen, first site, Ctrl quick build, green button, the test runs to its end) failed before the fix and passes now; first-site-ticks-on passes. CLAUDE.md: test-driven, flow tests for every happy path and the major failure paths.

## Current state, update 80 (17 Nov 2026): the child's action wins, teaching is only the tutorial, restart shows the load screen, test result sooner

Owner, verbatim (17 Nov 2026, 22:43): "1. the restart button should show the "loading screen" again, to truly show to the player we started again 2. I click a site I should go, and the line doest play because the restart warning plays. New rule: every interaction that is the result of my action, stops the previous visual/audio cue and starts the new one. find a way to model this properly in the cue framework, and I also hope your cue modeling bundles visuals and audio. 3. a lot of cues dont play when I have "teaching" clicked off. teaching is only the 1st lvl "tutorials", and the first time I explain the tests, udnerstnad? 4. the sucess (and maybe the failure) audio in the the lvls, after the test, are quite delayed."
1. The restart (second press) shows the load screen for 2 s, then the map starts over (`showLoadScreen`).
2. cues.json: events the child causes are marked `byChild`; a cue fired by one stops the cue playing (its line and its glow, pointing, hand together: one cue row is both) and drops waiting lines (`interruptCues`). Not while a first-site teaching line plays or a teaching step waits, or during a demo (earlier owner rule). "A step waits" now means a teaching step only; the first launch's "press here to start" no longer silences everything.
3. Teaching (the ΔΙΔΑΣΚΑΛΙΑ tick) is only the first site's steps and the first explanation of each test part; 18 cues lost the teaching mark (first-pick lines, red button, fail lines, first win, openings, locked site and more).
4. Measured at normal speed: the cheer came 1.2 s after the shaking, the win line 5 s after (it waited for the test to end). Now: something breaking fails the test at once; after the earthquake the wait is 0.6 s; the win line plays 1 s after the cheer, during the test's end. All ten suggested builds still pass; all wrong choices still fail (`harness.py spec`; Parthenon and Valens piles over the sidebar as before).
Flows added: restart-load-screen, child-action-cuts-line, ticks-off-lines-play, test-end-sounds (all pass; the last takes 40 s, the test at normal speed).

## Current state, update 81 (17 Nov 2026, late): red shows exactly what is wrong, teaching is what shows the game's things, sounds, stones from the mountains

Owner, verbatim (17 Nov 2026, 23:41), with his screenshot `owner-shots/2026-11-17-red-jagged-mudbrick.png` (after a failed test: only the top of the leaning mudbrick is red, in steps):
"last chat did some work, adn then said: "Tests: there are six browser tests now and they take about 100 seconds together. One of them alone takes 40 seconds, because it runs the test at normal speed to time the sounds. Speeding them up is on the BUILD.md list, along with the flows still missing.". my anser to this, adn to many other items regarding its work: what does this step test, and can it be tested with small, mock sounds? 2. thsi is wrong, you should show with red areas that are NOT filles while they should, and areas that ARE filles while they shouldnt. there is no reason for only that top part of the uppermost mudbrick to be red, all the part of that mudbrick that is outside the desigh should be red. 3. i had teaching turned off, but the "click here to go back to the map" and "well done, your momument withstood the tests" cues played. I think you ahve assigned as teaching cues some that are not. also "the dots stay empty, the headpiece goes there" did the same, I think you have it so it does it once per level, but it shouldn't when teaching is off. pls man, focus. you know, the teaching cues are ONLY those and ALL those that show the game elements. 4. when the tests are playing, the music should fade off.  the earthquake sound is too low compared to the others. make my voice 10% lower globally. Make material sounds 10% lower. 5. your red error to show wrong filling is jagged and weird for no reason. we work with straight lines. you ahve the compeltely wrong logic to show it, maybe even to calculate it. 6. by the way, how do you calculate if wind/headpiece/earthquake broke the design? by dong the red test, or more? 7. how do you calcualte red/green area filling? 8. the headpiece outlien shouldnt disappear when the headpieec comes down.   9. How often do you plain the main screen periodic cues? 10. dont do water particle effects on rivers and small lakes. 10. wave circles should stop at land, not continue on land, but crash (you know, not crash crash, but stop there with their white thing going at the beach) 11. make intro image zoom half as slow. 12. make map alerts be more intense: I imagine they should be faster pulsating. 13. How often is the "the next site waits" cue playing? 14. same as gabbing boats, you should be agle to grab stones from the mountain and drop them on the sea (many small splashes) or on the land (they stay there, 3d small cubes, and disappear after 1 min of presence. of course theya re 3d, so they can pile op, or collide with the boats. 15. how should the image be cut, so that as much of the map is seen is an many refular laptop/tablet dimensions?"

Checklist:
1a. Question: what the slow flow (test-end-sounds) checks. 1b. Question: can it use small mock sounds.
2. Red: every part of the plan not covered, and every part of a piece outside the plan, exactly (not only the far part).
3. Teaching tick: teaching = exactly the cues that show the game's things; "press here to go back to the map", the first win line, "the dots stay empty" are teaching (silent with the tick off).
4a. Music fades out while a test runs. 4b. Earthquake louder. 4c. Voice 10% lower. 4d. Material sounds 10% lower.
5. Red drawn with straight edges (the pieces' and the plan's own edges), not cells.
6. Question: how the test decides that wind, headpiece or earthquake broke the building.
7. Question: how the covered/uncovered share is worked out.
8. The headpiece's dotted outline stays when the headpiece comes down.
9. Question: how often the map's repeating cues play.
10a. No water drops on rivers and small lakes. 10b. Wave circles stop at land, white at the shore.
11. Intro picture zoom at half the speed.
12. Map alerts pulse faster.
13. Question: how often "a new site waits" plays.
14. Stones: dragged from the mountains like boats; dropped on the sea: small splashes; on land: small 3D cubes that stay one minute, pile up, and are pushed by boats.
15. Question: how to cut the map picture for most laptop and tablet screens.
Done:
2/5. The red is three layers drawn with the plan's and the pieces' own edges (`drawFailShow`): the plan not covered; every counted piece's part outside the plan's shape (a piece in an opening included); wood courses not of wood. A piece broken in the test is drawn as its shape. Cells only say where the voice points. The check itself is unchanged (10 cm squares). Picture: `owner-shots/2026-11-17-red-fixed.png`.
3. cues.json field `teaching` (the tick gates on it, not on the kind of line): the first site's steps, map-start-step, openings, load-covered, pile-empty, form-out, explain-wind/load/quake, fail-explain, first-win, first-win-home.
4. Music fades to nothing over about half a second while a test runs, and back after; quake 1.6 -> 3.2 through a limiter (its file peaks at full scale); VOICE_VOLUME 0.9; hits, drags, crumble, snap 0.8 -> 0.72.
8. The dotted outline is drawn again over the headpiece once it is down.
10. Water drops only where the land picture has sea (rivers and lakes are land there); each ring stops per direction where it meets land and is drawn white and wider there.
11. INTRO_ZOOM 0.006, INTRO_PAN 0.02 (read as half the speed). 12. Map highlights pulse every 0.9 s (was 1.8 s).
14. Map stones, four parts written at `mapStones` in SECTION MAP.
Flows added (each failed on the old build, passes now): ticks-off-first-win, red-outside, map-water, map-stones. Cue test teaching-off now reads the `teaching` field.
Open question to the owner: should any part of a piece outside the plan keep the button red (now only parts more than 50 cm out do)?

## Current state, update 82 (18 Nov 2026): headpiece in hand, one wrong-area rule, rhythm alerts, voice once per site per session, thrown stones

Owner, verbatim (18 Nov 2026, 00:52), with his screenshot `owner-shots/2026-11-18-first-site-too-strict.png` (first site: the top row has a narrow gap and its last mudbrick sticks out past the plan on the right; the button stays red):
"1. is there a test for the failure too? and can the tests run at fast speed? 2. if a piece is on the headpiece place, all of it turns red, but it should count like the rest, like only its part that is inside the headpiece outline should be red. 3. earthqueke should be 30% louder. 4 when you go to a binished site, make it possible to grab and move headpiece as any other block, make it have the weight of stone (according to each pieces size of course) max the weight of 2x std stone blocks, so it can always be lifted, albeit with difficulty. triple clicking it makes it disappear. 7.  this does not look right, it is too strict, and maybe your explanation about pieces outside the plan was wrong... if 1st lvl doesnt allow this in the iamge, then other levels must be impossible... especially those with weird pieces, liek the valens... what is happening?  9. make next site glow every 10 secs, a damaged site too, but of course not in sync, every sit flash ahs its own counter. 10. make wave reaching the beach particles go more on land, and less on water. like they flow on the land, you know. 11. make intro zoom 20% slower still. also, give me the images that show where the focal point for the zoom is, I want to readjust some a bit. 12. a bit more, like dumdum dum dumdumdum dumdumdum. so, finished site, danaged site, enxt site, get this dumdumdum dumdumdum dumdumdum pulse. 14. each grab should grab 5 stones. also, they should be thrown, not let go, now when I release hold they just drop, not continue the momentum of motion. also i cant drop it ona  boat, it should bong on the boat and bounce on the water, and the boat should play the smae sound it plays when i let them on land."
Owner, verbatim (18 Nov 2026, 00:57): "I forgot to say that the voice cues for next site - damaged site, must play sound not every time they trigger (onyl the visual plays every time), the sound must play the first time they happen per site, and of course refreshing the page counts for that too, its like a player re-entry. if you dont ahve the cocnept of what refreshes things, reenterign the game refreshes some things liek the one I just mentioned. fidn a clean way to model these thigns in your cue framework"

Checklist:
1a. Question: is there a test for the failure sounds. 1b. Question: can the tests run fast (the slow one).
2. A piece in the headpiece's place: only its part inside the dotted outline is red.
3. Earthquake 30% louder.
4a. At a finished site the headpiece can be grabbed and moved like a block. 4b. It weighs stone by its size, at most two stone blocks. 4c. Three quick taps make it disappear.
7. Too strict: his first-site build (top row with a narrow gap, last mudbrick sticking out) keeps the button red; explain what happens.
9. Next site and each damaged site glow every 10 s, each on its own count, not together.
10. The white of a wave at the shore runs onto the land.
11a. Intro zoom 20% slower. 11b. Pictures showing each intro's zoom point.
12. Finished, damaged and next site alerts pulse "dumdum dum dumdumdum dumdumdum".
14a. One grab takes five stones. 14b. Stones are thrown with the finger's speed. 14c. A stone on a boat knocks on it and bounces into the water; the boat plays its left-on-land sound.
15. Voice for next site and damaged site: once per site per game session (a page refresh is a new session); the glow every time. A clean model for what a re-entry resets.

## Task list

- Flow tests still to write for the other happy paths (map, each kind of site, free play, hand building, test failing, settings in the middle).
- The flow suite takes about 130 s; make the slow flows faster (test-end-sounds: start the test at the earthquake with the building already standing).


Done (12 Nov 2026, fourth list): stone swings less, wood lighter in the hand. Done (third list): stronger sidebar hand, pieces no longer lost at the sidebar edge, heavy pieces stay in the grip when swung. Done (second list): sidebar fixed, stronger pile hand, into-sidebar keeps motion, less swing, solid thicker ground. Done (first list): 1 sidebar and pieces 1.5x; 2 bottom pile piece lifts easily, no shooting up; 3 piece leaves the sidebar with the same hold and motion; 4 off-centre hold rebuilt as a joint. Next: owner play-test.
Done (12 Nov 2026, levels): all ten levels rebuilt to `levels.md` (approved, headpieces LOCKED in `tools/level-spec.json`); every test there passes (`tools/harness.py spec`, `tools/harness.py real`); picture `levels.png` (`tools/level-pictures.py`). Game changes are listed at the end of `levels.md`. Next: owner play-test and verdict on `levels.png`. Branch `level-proposals` is superseded.
Done (12 Nov 2026, second and third level lists): see `games/arxitektones-tou-arxaiou-kosmou/levels.md` (levels and game changes). Arches are the standard nine wedges again (wedge trimmed so the arch top is exactly 3 m) with a big triangle sized to sit on the arch flush with its top; levels fill the screen height (only the Lighthouse shrinks); Parthenon columns 2 m apart; Mausoleum one roof layer less; all piles fit the sidebar; every test in levels.md passes. Level 3 quick build: not reproduced. Pre-existing harness failure, not from this work: probe 'whirls beam/wood'.
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
Done (12 Nov 2026, sixth list): all 17 items; every `owner` test, `spec` (except the Valens pile) and `real` pass; each owner test was seen failing on the old build first, except mudbrick (the hand-placed stacks already behaved as agreed) and music (already started at load or first touch). Open for the owner: the Lion Gate wrong build changed to "one jamb left out".
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
