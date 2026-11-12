# Tower Builder: level spec

The single source for what each level is. Code, suggested builds and piles follow this file; if they disagree, the code is wrong. A line marked LOCKED is changed only by the owner editing this file. All ten levels are approved by the owner (12 Nov 2026; changes of the second round the same day are in). Picture of all levels (outline left, suggested build right, orange = headpiece): `levels.png`, made by `tools/level-pictures.py`.

## Rules for all levels

- One new piece or technique per level; everything met earlier stays in the pile.
- The pile holds the suggested build plus the wrong-material pieces for that level, little else. A wrong choice is a real piece lying in the pile that fits the outline and looks usable.
- Every level has both kinds of wrong choice: a wrong material and a wrong way to build. Each fails by physics (crumbles, snaps, blows off, tips, falls in, or the headpiece falls off), shown in red; failing only the ready check does not count.
- A wrong choice that the tests show does not fail is replaced, never kept.
- Middle and higher levels (4 on) are not a solid wall: openings, columns, arches or overhangs.
- The headpiece is an important part of that building, lowered from above onto a place the player must leave the right shape for.
- Owner: piece size in the sidebar never changes (`PILE_REF_HEIGHT` in the PILE section pins it). Every level's pile must fit the sidebar at that size; the pile packer fills the room beside tall rows with smaller pieces.
- Pieces fit like toy bricks: square blocks are the unit. The arch is nine equal wedges on a wooden form, its top exactly 3 m (three squares) above its feet. The big triangle (short sides 1.75 m) sits in the corner beside an arch, resting on the arch, flush with its top. The small triangle (half a square) slopes the ziggurat stairway and the mausoleum roof; one level uses only one triangle size.
- Levels are not shrunk on screen unless they must be: the building fills the height and the headpiece comes down from above the top edge (only the Lighthouse is tall enough to shrink; the aqueduct by 3% for width).

## Process (in this order, every time)

1. Owner approves or changes each level here. Headpieces are agreed first and then LOCKED.
2. The headpieces are kept as exact data in `tools/level-spec.json`. Only an owner change to this file changes that data.
3. The suggested build and the wrong choices are written in `tools/make-levels.py` (which writes `src/levels.js` and `tools/level-tests.json`) until the tests below pass.
4. `python3 tools/level-pictures.py` makes `levels.png` for the owner. Only after his OK does a level change count as done.

## Tests (12 Nov 2026: all pass)

Run from `games/tower-builder/tools`: `python3 harness.py spec` (tests 1, 2, 3, 4; one line each) and `python3 harness.py real` (test 2, real game loop). `NJ=n` sets the number of placement runs (default 6).

1. Headpiece: the level's load equals `tools/level-spec.json` exactly.
2. Suggested build stands: quick build and the full test (at play speed, not the Tab speed-up) pass with every piece exactly placed and in five more runs with every piece off by up to 3 cm and 1 degree (never overlapping what is already there, as a careful player places them); and once through the real game loop (real frames, the real ready check, no Tab).
3. Each wrong choice below, swapped into the suggested build, fails: something crumbles, snaps, falls, or the headpiece comes off.
4. Pile: it holds every piece the suggested build uses and every wrong-material piece; arch forms only as many as listed; it fits the sidebar at 1280 x 800.
5. Wood-support levels: the build without the supports, or with them taken out too early, falls (wrong builds of Ishtar, Mausoleum and Valens).
6. Reuse (Valens): built with two forms, moved from the lower to the upper arches.
7. Lighthouse: without its wooden ties the walls fall in the wind.
8. Outline matches the build: the exactly placed build, once settled, has every piece within 5 cm of its place, and the outline and the pieces differ by at most 2.5% of the outline (owner, 12 Nov: outlines and builds did not match).

Test numbers per level (placeholders in the LEVELS section, tuned only through these tests): wind 110 N/m on level 1, 18 on the Lighthouse, 6.5 elsewhere; load density 5, 42, 20, 75, 25, 10, 60, 12, 13, 14 (heavy enough that wrong-material mudbrick crumbles); earthquake 0.32 rising to 0.61. Outlines are exactly the suggested build's pieces (no gaps closed), except beside arches: slivers between arch stones and their neighbours (narrower than 0.7 m) are drawn solid and not checked, and each arch stone has a thin guide line (owner).

## 1. Mastaba, Saqqara (c. 3000 BC)

- Headpiece: the flat roof slab on top, across the middle. LOCKED.
- Pieces: 11 mudbrick blocks, 2 mudbrick half-blocks; pile adds 4 wooden blocks.
- New: mudbrick. Technique: a wide solid mass, the middle row's joints staggered.
- Hard: nothing; the first win.
- Wrong material: wooden blocks in the top row blow off in the wind.
- Wrong build: the middle of the top row left open under the roof: the roof falls in.
- Temporary wood: none.

## 2. Step pyramid of Djoser, Saqqara (c. 2650 BC)

- Headpiece: the top (sixth) step, lowered onto the fifth (the pyramid has six steps). LOCKED.
- Pieces: 6 stone blocks (the first layer only, owner), 14 mudbrick blocks; pile adds stone and mudbrick for the wrong choice.
- New: stone. Technique: heavy low, light high.
- Hard: stone only where the weight is greatest.
- Wrong material: mudbrick at the bottom, stone above it: the bottom crumbles under the stone and the top step.
- Wrong build: a top-step block more than half off the step below: it falls.
- Temporary wood: none.

## 3. Ziggurat of Ur (c. 2100 BC)

- Headpiece: the temple of Nanna on the top terrace (Britannica: temple on top, not preserved). LOCKED.
- Pieces: 5 stone blocks, 1 stone triangle (the stairway), 10 mudbrick blocks, 5 wooden beams in two courses; pile adds 3 mudbrick blocks.
- New: wooden beams laid as courses (they stand for the reed matting that strengthened the mudbrick core, Britannica). Technique: three terraces, each narrower.
- Hard: wood only where it lies fully supported; terraces centred.
- Wrong material: mudbrick in the base and stone in the top terrace: the base crumbles.
- Wrong build: a top-terrace block more than half off the terrace below: it falls.
- Temporary wood: none.

## 4. Karnak hypostyle hall (c. 1290-1220 BC)

- Headpiece: the roof slab over the taller middle nave (University of Memphis: central nave taller than the sides). LOCKED.
- Pieces: 5 stone blocks, 4 stone columns (all the same, owner), 12 small oblong blocks (two stacked make each of the six capitals, owner), 2 stone beams, 2 stone squares (the pillars of the taller middle nave); pile adds mudbrick for the wrong choices.
- New: columns and capitals. Technique: beams across gaps, each end on a capital.
- Hard: columns must stand where the beams reach both; every pillar is topped by a capital of two small blocks.
- Wrong material: mudbrick pillars under the middle roof crumble; mudbrick middle columns crumble.
- Wrong build: a middle column too far in for the beam: the beam and the middle pillar fall.
- Historical: Karnak's columns carry a capital with a square abacus block on top; here the two small blocks stand for them.
- Temporary wood: none.

## 5. Lion Gate, Mycenae (c. 1250 BC)

- Headpiece: the lion relief, a stone triangle, lowered onto the lintel. LOCKED. Never replaced by a slab, a wall course or anything on top of the gate.
- Pieces: 10 stone blocks (two upright as jambs), 6 stone half-blocks, 3 stone beams (the middle one is the lintel), 2 wooden beams standing upright as flagpoles, each held between the two stones of its side's top row (owner); pile adds 2 mudbrick blocks.
- New: a pole held upright between two stones. Technique: jambs and a lintel; the relief stands free on the lintel.
- Wrong material: mudbrick jambs crumble under the lintel and the lion.
- Wrong build: flagpoles standing on top of the stones instead of between them: the wind blows them down.
- Temporary wood: none.
- Flagpoles: no source found for flagpoles at the Lion Gate. The sources describe a double wooden door turning in pivot holes in the lintel and threshold, closed by a crossbar in sockets in the jambs (odysseyadventures.ca; ancient-greece.org).
- Wooden lintel, checked: it does not fail, so it is not a wrong choice. The real lintel is one stone, 4.5 x 2.0 x 0.8 m, about 20 t (Wikipedia; theplaka.com); the relief's weight rests only on its lower corners (odysseyadventures.ca), close to the jambs.

## 6. Ishtar Gate, Babylon (c. 575 BC)

- Headpiece: the cedar roof over the passage (worldhistory.org: door and roof of cedar). LOCKED.
- Pieces: 8 stone blocks, 8 mudbrick blocks (the side towers), 9 wedges, 6 stone half-blocks and 2 big triangles beside the arch, 1 wooden arch form on 4 wooden blocks; pile adds 4 mudbrick blocks.
- New: wedges and the wooden arch form. Technique: the arch built on the form, the form taken out once the last wedge is in. The squares beside the arch stand right at its feet; the triangles rest on the arch and come exactly to its top.
- Hard: the wedges only stand once the last one is in.
- Wrong material: mudbrick under the arch's feet crumbles.
- Wrong build: the form pulled out before the last wedge: the arch falls.
- Temporary wood: one arch form on four blocks.

## 7. Parthenon front, Athens (447-432 BC)

- Headpiece: the three acroteria: one on each end of the architrave beside the pediment, standing level, and one on the pediment's flat top. LOCKED. The player builds the pediment.
- Pieces: two steps (7 blocks, then 5 blocks and 2 half-blocks), 6 columns of 3 square drums each with a capital, 2 m apart, an architrave of 5 blocks, a pediment of two stones; pile adds 7 mudbrick blocks and 2 mudbrick half-blocks.
- New: the pediment stones. Technique: columns built drum by drum (σπόνδυλοι), stacked straight; every architrave block has both ends on a capital.
- Hard: loose drums wobble until the architrave ties their tops; a column off its spot leaves an architrave end hanging.
- Wrong material: mudbrick in the top step crumbles under the temple.
- Wrong build: drums stacked off line: the column falls; an end column too far out: the architrave end falls.
- Temporary wood: none.
- Historical: the real front has eight columns (octastyle) built of drums, about 1.25 column widths apart; six here (owner), one column width apart, so the temple fits the screen without shrinking. The real temple has three steps and a frieze; two steps and no frieze here. The pediment stops 1 m short of each end (owner) and rises 1.33 m.

## 8. Mausoleum of Halicarnassus (c. 350 BC): the wooden-post level

- Headpiece: the four-horse chariot on top, and two acroteria on the beam ends beside the roof (owner). LOCKED.
- Pieces: 26 stone blocks (podium, core, five roof steps), 8 small triangles (the roof's slope), 4 square drums and 3 capitals, 4 stone beams, 2 wooden posts; pile adds 2 mudbrick blocks.
- New: wooden posts as temporary props. Technique: the walkway beams reach out from the solid core further than they can hold alone; they rest on wooden posts while the roof goes on, and hold once its weight (five steps over the core) presses their inner ends down. The posts then come out.
- Hard: the posts must stand before the beams go on and stay until the roof is on.
- Wrong material: mudbrick in the core crumbles.
- Wrong build: no posts: the beams tip and the roof falls; posts pulled out before the roof is on: the same.
- Temporary wood: two posts.
- Historical: podium, 36 columns, a pyramid of 24 steps, a four-horse chariot (Pliny, corroborated by excavation, worldhistory.org); a solid core behind the columns carried the roof (Wikipedia); ceiling beams of the walkway were found (American Journal of Archaeology); lions stood at the base of the pyramid (worldhistory.org). The real roof was stepped with a low pitch; here the steps are filled out with triangles into a 45-degree slope (owner). The acroteria are the owner's addition. The posts are the game's way of building it.

## 9. Lighthouse of Alexandria (c. 280 BC)

- Headpiece: the statue on top and the two Tritons on the corners of the lowest tier. LOCKED.
- Pieces: 9 stone blocks, 13 stone half-blocks, 8 wooden beams; pile adds 2 mudbrick blocks.
- New: a hollow tower. Technique: the lowest tier (seven courses, owner: three tie courses and one stone course on top) is two walls round the shaft, tied every other course by two wooden beams across it; the second tier is hollow too, walls one block thick tied by single wooden beams; a stone over the shaft carries the round top.
- Hard: the tallest level and a strong wind (18 against 6.5 elsewhere). Still drawn smaller than the others (81% at 1280 x 800, 71% at 1920 x 1080); full size needs the top at most about 12 m (10.7 m at 1920 x 1080), it is 14.4 m.
- Wrong material: mudbrick at the base crumbles.
- Wrong build: no wooden ties (test 7): the walls fall in the wind; the upper tier set off centre: the tower falls.
- Temporary wood: none.
- Historical: square, octagonal and round tiers (Wikipedia); a spiral ramp inside the lowest tier and a shaft in the upper ones (Balawi via Wikipedia; mfn.li); a statue on top and Tritons on the corners (Roman coins, Wikipedia). Timber-laced walls are an old Greek technique (ξυλοδεσιά); for the Pharos itself the sources name lead between the base blocks (Al-Idrisi via Wikipedia), not timber.

## 10. Valens Aqueduct, Constantinople (AD 368)

- Headpiece: the water channel along the top. LOCKED.
- Pieces (owner: back to the old design): 3 stone blocks as piers under the lower arches, 4 arches of 9 wedges, 8 big triangles, side walls a half-block wide in both tiers, a course of 7 stone blocks between the tiers, 2 wooden arch forms each on one wooden block; pile adds mudbrick for the wrong choice.
- New: nothing new. Technique: two forms for four arches. The lower arches spring from the piers; take the forms out, use them again for the upper arches, which stand on the course between the tiers.
- Hard: the piers carry everything.
- Wrong material: mudbrick piers crumble.
- Open: this pile does not fit the sidebar (120%); waiting for the owner.
- Wrong build: a form pulled out before the last wedge: the arch falls.
- Temporary wood: two forms, no more.
- Historical: the real aqueduct stands on tall piers and its upper arches are smaller; here the arches are all one size.

## Game changes made for these levels (12 Nov 2026, second list)

- Pieces' physical shapes are 5 mm smaller on every side than drawn (`SKIN_GAP`): planck kept touching pieces about 1.4 cm apart, so every course stood higher than drawn and builds no longer matched their outlines. The check uses the drawn shape.
- Mudbrick crumbles under four mudbrick blocks and three stone blocks, not under three and three (`CRUSH_FORCE` 515 N, was 320). Resting pieces fall asleep in the physics and stopped reporting their load, so mudbrick never crumbled under a still stack; a sleeping piece now keeps its last verdict.
- In the hand a piece's ease and carry speed follow its mass (a block is the reference): small pieces follow quicker than big ones of the same material.
- New piece `abacus`: a small oblong block, half a capital (Karnak).
- `tools/make-levels.py` and `tools/level-pictures.py` use `tools/geom.py` (numpy, OpenCV) instead of shapely.

## Game changes made for these levels (12 Nov 2026)

- Level data is centred in the middle of the check grid (x 0..40 m, y 0..22 m); a level wider than the screen zooms out to fit, as tall ones do.
- The view fits the building and its headpiece with 0.6 m to spare; the headpiece starts above the top edge and comes down into view.
- Quick build: a `pull` step takes the temporary supports out (they go back to the pile to be used again); the pile counts reused supports once.
- Wrong-material pieces in each pile come from `make-levels.py` (`extra` per level), not a hand list.
- Wood: a support holds a beam along the whole stretch it touches, not just where it pushed this step; wood snaps at 150 (was 80).
- Mudbrick: only weight from above counts towards crumbling, not side pushes.
- Wedge trimmed so nine make an arch whose top is exactly 3 m above its feet; arch form radius 2.0; big triangle (1.75 m) for arch corners, small triangle (1 m) elsewhere.
- Stone and mudbrick are slower and stiffer in the hand (lift speed, acceleration, turning); weights and all building physics are unchanged.
- Pile: polygons take their real size, rows of tall pieces are topped up with smaller ones beside them, triangles of either size nest in pairs.
