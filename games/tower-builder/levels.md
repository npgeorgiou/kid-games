# Tower Builder: level spec

The single source for what each level is. Code, suggested builds and piles follow this file; if they disagree, the code is wrong. A line marked LOCKED is changed only by the owner editing this file. All ten levels are approved by the owner (12 Nov 2026; changes of the second round the same day are in). Picture of all levels (outline left, suggested build right, orange = headpiece): `levels.png`, made by `tools/level-pictures.py`.

## Rules for all levels

- One new piece or technique per level; everything met earlier stays in the pile.
- The pile holds the suggested build plus the wrong-material pieces for that level, little else. A wrong choice is a real piece lying in the pile that fits the outline and looks usable.
- Wrong choices in the pile (owner, 12 Nov): every wrong choice, of material or of building, in every level, must be buildable from the pile while every piece of the suggested build is still in it. So for each wrong choice the pile holds, on top of the suggested build, every piece that choice puts in place of the right one (mudbrick where stone belongs, wooden planks where a stone lintel belongs, and so on). The player can always build the tempting wrong way without first taking the right pieces away from the right places. `make-levels.py` adds these pieces (`extra`), and test 4 checks it for every wrong choice.
- Every level has both kinds of wrong choice: a wrong material and a wrong way to build. Each fails by physics (crumbles, snaps, blows off, tips, falls in, or the headpiece falls off), shown in red; failing only the ready check does not count.
- A wrong choice that the tests show does not fail is replaced, never kept.
- Middle and higher levels (4 on) are not a solid wall: openings, columns, arches or overhangs.
- The headpiece is an important part of that building, lowered from above onto a place the player must leave the right shape for.
- Owner: piece size in the sidebar never changes (`PILE_REF_HEIGHT` in the PILE section pins it). Every level's pile must fit the sidebar at that size; the pile packer fills the room beside tall rows with smaller pieces.
- Outline (owner, 12 Nov): the outline is the shape of the building, never the outline of the suggested build's pieces. It is solid everywhere inside the building's outer edge (seams, slivers beside arch stones, gaps between triangles and arches, and narrow dips in the edge narrower than 0.6 m all count as building), except the building's real openings: doors, arch openings, the spaces between columns, the lighthouse shaft. Each level declares its openings on purpose in `make-levels.py` (listed per level below); openings that touch are drawn as one.
- Green button (owner, 12 Nov): 85% of the outline covered, nothing in an opening, nothing far outside, the headpiece's place free, everything still. Openings are never painted red unless a piece really blocks them; gaps between pieces narrower than 10 cm are never painted.
- Mudbrick (owner, 13 Nov): a mudbrick block lying flat crumbles under four mudbrick blocks, and, separately, under three stone blocks; three mudbricks or two stones it holds. A narrower mudbrick holds less, in proportion to the width it stands on (an upright mudbrick column crumbles under one stone block). Laid across a gap of 30 cm or more like a lintel it breaks far more easily (a stone block on it over a 1 m gap breaks it). It survives a fall one block side (1 m) higher than before: whole from 3.5 m, broken from 4 m.
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
2. Suggested build stands: quick build and the full test (at play speed, not the Tab speed-up) pass with every piece exactly placed and in five more runs with every piece off by up to 3 cm and 1 degree (never overlapping what is already there, as a careful player places them); and once through the real game loop (real frames, the real ready check, no Tab). Owner (12 Nov): it also passes with the earthquake and the headpiece 30% stronger, and quick build plus test gives the same result 20 times in a row (`harness.py owner repeat margin`).
3. Each wrong choice below, swapped into the suggested build, fails: something crumbles, snaps, falls, or the headpiece comes off, and the result is not a building that lights the button and passes the test.
4. Pile: it holds every piece the suggested build uses and, for every wrong choice, the pieces it puts in place of the right ones (rule above); arch forms only as many as listed; it fits the sidebar at 1280 x 800.
5. Wood-support levels: the build without the supports, or with them taken out too early, falls (wrong builds of Ishtar, Mausoleum and Valens).
6. Reuse (Valens): built with two forms, moved from the lower to the upper arches.
7. Lighthouse: without its wooden ties the walls fall in the wind.
8. Outline matches the build: the exactly placed build, once settled, has every piece within 5 cm of its place, covers at least 85% of the outline (the building's shape; its uncovered slivers must still light the button) and has at most 2.5% of its pieces outside the outline.

Test numbers per level (placeholders in the LEVELS section, tuned only through these tests): wind 110 N/m on level 1, 18 on the Lighthouse, 6.5 elsewhere; load density (in play order) 5, 8, 5, 25, 75, 4, 60, 12, 13, 14 (heavy enough that wrong-material mudbrick crumbles, light enough that the suggested build holds 30% more on every screen size; set again 12 Nov for the new mudbrick strength); earthquake 0.32 rising to 0.61. Each arch stone has a thin guide line in the outline (owner).

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
- Pieces (owner, 13 Nov): 11 stone blocks (the first two layers), 9 mudbrick blocks (the top three layers); pile adds 8 mudbrick blocks: 6 for the wrong choice and 2 in case some break (owner, 13 Nov: two more mudbricks, no extra stone).
- New: stone. Technique: heavy low, light high.
- Hard: stone only where the weight is greatest.
- Wrong material: mudbrick in the bottom row: it crumbles under the steps above (owner, 13 Nov: no extra stone, so the old wrong choice, stone on top, can no longer be built).
- Wrong build: a top-step block more than half off the step below: it falls.
- Temporary wood: none.

## 3. Ziggurat of Ur (c. 2100 BC)

- Headpiece: the temple of Nanna on the top terrace (Britannica: temple on top, not preserved). LOCKED.
- Pieces (13 Nov, for the owner's mudbrick strength: the lower terrace stone): 9 stone blocks, 1 stone triangle (the stairway), 6 mudbrick blocks, 5 wooden beams in two courses; pile adds 5 mudbrick blocks and 2 stone blocks (owner: material for the wrong choice).
- New: wooden beams laid as courses (they stand for the reed matting that strengthened the mudbrick core, Britannica). Technique: three terraces, each narrower.
- Hard: wood only where it lies fully supported; terraces centred.
- Wrong material: mudbrick in the base and stone in the top terrace: the base crumbles. (13 Nov: crumbles again with the owner's mudbrick strength.)
- Wrong build: a top-terrace block more than half off the terrace below: it falls.
- Temporary wood: none.

## 4. Karnak hypostyle hall (c. 1290-1220 BC)

- Headpiece: the roof slab over the taller middle nave (University of Memphis: central nave taller than the sides). LOCKED.
- Pieces: 5 stone blocks, 4 stone columns (all the same, owner), 12 small oblong blocks (two stacked make each of the six capitals, owner), 2 stone beams, 2 stone squares (the pillars of the taller middle nave); pile adds mudbrick for the wrong choices.
- New: columns and capitals. Technique: beams across gaps, each end on a capital.
- Hard: columns must stand where the beams reach both; every pillar is topped by a capital of two small blocks.
- Openings: the two aisles between the columns, up to the beams.
- Wrong material (owner, 12 Nov: more mudbrick and long wooden planks): mudbrick pillars under the middle roof crumble; mudbrick middle columns crumble; mudbrick capitals crumble; a mudbrick platform crumbles; wooden planks as the side beams fall.
- Wrong build: a middle column too far in for the beam: the beam and the middle pillar fall.
- Historical: Karnak's columns carry a capital with a square abacus block on top; here the two small blocks stand for them.
- Temporary wood: none.

## 5. Lion Gate, Mycenae (c. 1250 BC)

- Headpiece: the lion relief, a stone triangle, lowered onto the lintel. LOCKED. Never replaced by a slab, a wall course or anything on top of the gate.
- Pieces: 10 stone blocks (two upright as jambs), 6 stone half-blocks, 3 stone beams (the middle one is the lintel), 2 wooden beams standing upright as flagpoles, each held between the two stones of its side's top row (owner); pile adds 3 wooden beams (tempting as the lintel over the door, owner) and 8 mudbrick blocks and 4 mudbrick half-blocks (owner: more mudbrick).
- Openings: the door.
- Owner (13 Nov): back to the lower version (the extra course removed); played before Karnak (it is easier), so the Lion Gate is level 4 and Karnak level 5.
- New: a pole held upright between two stones. Technique: jambs and a lintel; the relief stands free on the lintel.
- Wrong material: mudbrick jambs crumble under the lintel and the lion; wooden planks as the lintel snap under the lion; mudbrick for the jambs and the lower walls: the jambs crumble.
- Wrong build: one jamb left out: the lintel and the lion fall into the door. (Flagpoles standing on top of the stones, the earlier wrong build, no longer fails the test: the poles fall but the building passes, so it was replaced.)
- Temporary wood: none.
- Flagpoles: no source found for flagpoles at the Lion Gate. The sources describe a double wooden door turning in pivot holes in the lintel and threshold, closed by a crossbar in sockets in the jambs (odysseyadventures.ca; ancient-greece.org).
- Wooden lintel (owner, 12 Nov: 3 planks to tempt): a piece lying flat now presses on wood along the whole face they share (it pressed only at its two ends before, which is why the wooden lintel did not snap); the lion's weight over the door snaps a wooden lintel. The real lintel is one stone, 4.5 x 2.0 x 0.8 m, about 20 t (Wikipedia; theplaka.com); the relief's weight rests only on its lower corners (odysseyadventures.ca), close to the jambs.

## 6. Ishtar Gate, Babylon (c. 575 BC)

- Headpiece: the cedar roof over the passage (worldhistory.org: door and roof of cedar), and (owner, 12 Nov) a headpiece as thick as the roof lowered onto each tower. LOCKED.
- Pieces: 12 stone blocks (8 in the base, the towers' two lowest courses), 6 mudbrick blocks (the towers' top three courses; owner: the towers one course taller), 9 wedges, 6 stone half-blocks and 2 big triangles beside the arch, 1 wooden arch form on 4 wooden blocks; pile adds 4 mudbrick blocks. Stone exactly as much as the build needs, mudbrick more than it needs (owner).
- Openings: the arch.
- New: wedges and the wooden arch form. Technique: the arch built on the form, the form taken out once the last wedge is in. The squares beside the arch stand right at its feet; the triangles rest on the arch and come exactly to its top.
- Hard: the wedges only stand once the last one is in.
- Wrong material: mudbrick under the arch's feet crumbles; mudbrick towers all the way down: the lowest course crumbles under the tower headpiece.
- Wrong build: the form pulled out before the last wedge: the arch falls.
- Temporary wood: one arch form on four blocks.

## 7. Parthenon front, Athens (447-432 BC)

- Headpiece: the three acroteria: one on each end of the architrave beside the pediment, standing level, and one on the pediment's flat top. LOCKED. The player builds the pediment.
- Pieces: two steps (7 blocks, then 5 blocks and 2 half-blocks), 6 columns of 3 square drums each with a capital, 2 m apart, an architrave of 5 blocks, a pediment of two stones; pile adds 5 mudbrick blocks and 2 mudbrick half-blocks.
- New: the pediment stones. Technique: columns built drum by drum (σπόνδυλοι), stacked straight; every architrave block has both ends on a capital.
- Hard: loose drums wobble until the architrave ties their tops; a column off its spot leaves an architrave end hanging.
- Openings: the five spaces between the columns, up to the architrave.
- Wrong material: mudbrick in the top step crumbles under the temple.
- Wrong build: drums stacked off line: the column falls; an end column too far out: the architrave end falls.
- Temporary wood: none.
- Historical: the real front has eight columns (octastyle) built of drums, about 1.25 column widths apart; six here (owner), one column width apart, so the temple fits the screen without shrinking. The real temple has three steps and a frieze; two steps and no frieze here. The pediment stops 1 m short of each end (owner) and rises 1.33 m.

## 8. Mausoleum of Halicarnassus (c. 350 BC): the wooden-post level

- Headpiece: the four-horse chariot on top, and two acroteria on the beam ends beside the roof (owner). LOCKED. 12 Nov: the acroteria moved in with the lintel ends (from 6.5 to 5.95 m out), so they still stand on them.
- Pieces (owner, 12 Nov: the lintels meet with no gap, the roof a square narrower on each side, the top two triangles gone): 21 stone blocks (podium, core, five roof steps of 5, 4, 3, 2, 1 blocks), 6 small triangles (the roof's slope), 4 square drums and 3 capitals, 4 stone beams end to end, 2 wooden posts; pile adds 2 mudbrick blocks and 4 mudbrick half-blocks.
- Openings: the two walkways between the columns and the core.
- Owner (13 Nov): the middle column half as wide (two squares), with one capital wider than it, like the side columns, so the posts would be needed. Checked: the lintels still hold each other end to end, so pulling the posts early still does not fail.
- New: wooden posts as temporary props. Technique: the walkway beams reach out from the solid core further than they can hold alone; they rest on wooden posts while the roof goes on, and hold once its weight (five steps over the core) presses their inner ends down. The posts then come out.
- Hard: the posts must stand before the beams go on and stay until the roof is on.
- Wrong material: mudbrick in the middle column crumbles; mudbrick side columns crumble.
- Wrong build: one column left out: its lintel and the roof above it fall. (Checked 12 Nov and taken out because they no longer fail: the posts left out or pulled out early (the lintels now meet end to end and hold each other, so the posts are not needed any more; owner to decide whether the posts stay in this level) and wooden lintels (they snap while building, but the building then passes).)
- Temporary wood: two posts.
- Historical: podium, 36 columns, a pyramid of 24 steps, a four-horse chariot (Pliny, corroborated by excavation, worldhistory.org); a solid core behind the columns carried the roof (Wikipedia); ceiling beams of the walkway were found (American Journal of Archaeology); lions stood at the base of the pyramid (worldhistory.org). The real roof was stepped with a low pitch; here the steps are filled out with triangles into a 45-degree slope (owner). The acroteria are the owner's addition. The posts are the game's way of building it.

## 9. Lighthouse of Alexandria (c. 280 BC)

- Headpiece: the statue on top and the two Tritons on the corners of the lowest tier. LOCKED.
- Pieces: 9 stone blocks, 13 stone half-blocks, 8 wooden beams; pile adds 2 mudbrick blocks and 6 stone half-blocks (for the wrong build without ties).
- New: a hollow tower. Technique: the lowest tier (seven courses, owner: three tie courses and one stone course on top) is two walls round the shaft, tied every other course by two wooden beams across it; the second tier is hollow too, walls one block thick tied by single wooden beams; a stone over the shaft carries the round top.
- Hard: the tallest level and a strong wind (18 against 6.5 elsewhere). Still drawn smaller than the others (81% at 1280 x 800, 71% at 1920 x 1080); full size needs the top at most about 12 m (10.7 m at 1920 x 1080), it is 14.4 m.
- Owner (12 Nov): the square on top removed; the top headpiece is the size of a block lying down.
- Openings: the shaft in each course between the ties (touching ones drawn as one, owner).
- Wrong material: mudbrick at the base crumbles; mudbrick ties crumble; mudbrick walls in the upper tier crumble; a mudbrick stone over the shaft breaks (owner: more wrong materials).
- Wrong build: no wooden ties (test 7): the walls fall in the wind; the upper tier set off centre: the tower falls.
- Temporary wood: none.
- Historical: square, octagonal and round tiers (Wikipedia); a spiral ramp inside the lowest tier and a shaft in the upper ones (Balawi via Wikipedia; mfn.li); a statue on top and Tritons on the corners (Roman coins, Wikipedia). Timber-laced walls are an old Greek technique (ξυλοδεσιά); for the Pharos itself the sources name lead between the base blocks (Al-Idrisi via Wikipedia), not timber.

## 10. Valens Aqueduct, Constantinople (AD 368)

- Headpiece: the water channel along the top. LOCKED.
- Pieces (owner: back to the old design): 3 stone blocks as piers under the lower arches, 4 arches of 9 wedges, 8 big triangles, side walls a half-block wide in both tiers, a course of 7 stone blocks between the tiers, 2 wooden arch forms each on one wooden block; pile adds mudbrick for the wrong choice.
- New: nothing new. Technique: two forms for four arches. The lower arches spring from the piers; take the forms out, use them again for the upper arches, which stand on the course between the tiers.
- Hard: the piers carry everything.
- Openings: the four arches.
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
