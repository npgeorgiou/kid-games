# Tower Builder: level spec

The single source for what each level is. Code, suggested builds and piles follow this file; if they disagree, the code is wrong. A line marked LOCKED is changed only by the owner editing this file. Status per level: `proposed` until the owner approves it, then `approved`.

Every level lists: the building, the headpiece (the load lowered in the test), what is new (pieces, technique), what makes it hard, the wrong choices the pile offers and how each fails, temporary wood, and open questions. Historical lines name their source; anything unchecked says "unverified".

## Rules for all levels

- One new piece or technique per level; everything met earlier stays in the pile.
- The pile holds the suggested build plus the wrong-choice extras for that level, little else. A wrong choice is a real piece lying in the pile that fits the outline and looks usable.
- Each wrong choice fails by physics in the test (crumbles, snaps, blows off, tips, falls in), shown in red. A level whose wrong choice only fails the ready check says so as an open question.
- Middle and higher levels (4 on) are not a solid wall: openings, columns, arches or overhangs.
- The headpiece is an important part of that building, lowered from above onto a place the player must leave the right shape for.

## Process (in this order, every time)

1. Owner approves or changes each level here (keep/change/cut per field). Headpieces are agreed first and then LOCKED.
2. The headpiece of each approved level is copied as exact data into `tools/level-spec.json` (shape, position, what it rests on). Only an owner change to this file changes that data.
3. The suggested build is written in `tools/make-levels.py` until `tools/harness.py spec` passes for that level (tests below).
4. Pictures (outline left, suggested build right, headpiece orange) go to the owner. Only after his OK does the level go into the game.

## Tests (`tools/harness.py spec`, all must pass before a level is shown)

1. Headpiece: the level's load equals `level-spec.json` (shape and position within 1 cm). Any drift fails.
2. Suggested build stands: quick build and full test pass 10 times with pieces placed slightly off (up to 3 cm, 1 degree), at normal test speed and at 10x, and once through the real game loop (real frame timing, the real ready gate, not the Tab override).
3. Each wrong choice listed here, swapped into the suggested build, fails in the test at the phase named here.
4. Pile: it contains the level's new pieces, every piece the suggested build uses, the listed wrong-choice extras, and the listed number of wooden supports (no more).
5. Wood-support levels: the same build with the supports taken out before the build is complete falls. This proves the supports are needed.
6. Reuse (Valens): the suggested build is done with the listed number of forms, moved from arch to arch, and passes.

## 1. Mastaba, Saqqara (c. 3000 BC) — proposed

- Headpiece: the flat roof slab on top, across the middle. Open: is this the most important part of a mastaba? The source for which part matters is unknown.
- New pieces: mudbrick blocks. Technique: stack a wide solid mass.
- Hard: nothing; first win.
- Wrong choices: wooden blocks (light) in the top row; they blow off in the wind.
- Temporary wood: none.

## 2. Step pyramid of Djoser, Saqqara (c. 2650 BC) — proposed

- Headpiece: the top (sixth) step, lowered onto the fifth.
- New pieces: stone blocks. Technique: heavy low, light high.
- Hard: the pile has just enough stone for the lower steps; using it high leaves mudbrick for the bottom.
- Wrong choices: mudbrick in the bottom step crumbles under the stone above (settle or load).
- Temporary wood: none.

## 3. Ziggurat of Ur (c. 2100 BC) — proposed

- Headpiece: the temple of Nanna on the top terrace (Britannica: temple on top, not preserved).
- New pieces: wooden beams laid as courses. Technique: courses of wood inside the mass (stand-ins for reed matting; Britannica: core strengthened with reed matting).
- Hard: three terraces, each narrower; wood only where it lies fully supported.
- Wrong choices: stone beams in the wood courses. Open: this fails only the ready check (red course), not physics. Needs a physical wrong choice instead or as well (for example a wooden beam overhanging a terrace edge, which snaps under the course above).
- Temporary wood: none.

## 4. Karnak hypostyle hall (c. 1290-1220 BC) — proposed

- Headpiece: the roof slab over the taller middle nave (University of Memphis: central nave taller than the sides).
- New pieces: columns, capitals. Technique: beams across gaps, each beam end resting on a column.
- Hard: columns must stand where the beams reach both; the middle is taller, so the middle supports are built up from two parts.
- Wrong choices: mudbrick pillars crumble under the roof (load); a wooden beam across a gap snaps under the roof (load).
- Temporary wood: none.

## 5. Lion Gate, Mycenae (c. 1250 BC) — proposed

- Headpiece, LOCKED once approved: the lion relief, a stone triangle (base 3.6 m, over 3 m high, Wikipedia), lowered into the triangular slot and standing on the lintel. The headpiece is at least this centre triangle; it is never replaced by a slab, a wall course or anything on top of the gate.
- New pieces: stone triangles. Technique: stones beside the slot step inward and are held by the weight on their outer ends.
- Hard: two upright jambs, one long stone lintel, the slot above it kept clear and the right shape, the side courses heavy enough to hold the overhang.
- Wrong choices: a wooden lintel snaps when the lion lands (load); mudbrick in the jambs or base crumbles (settle or load).
- Temporary wood: none.
- Reported: the current game build collapsed in the owner's play. Not reproduced yet in the headless test (passes, also with pieces 3 cm off). Test 2 adds the real game loop and ready gate, which the old harness skipped.

## 6. Ishtar Gate, Babylon (c. 575 BC) — proposed

- Headpiece: the cedar roof beam over the gate passage (worldhistory.org: door and roof of cedar). Open: the arch is the gate's most famous part; the arch is built, not lowered, so the headpiece is the roof on it.
- New pieces: wedge stones, a wooden arch form. Technique: arch built on a wooden form, the form pulled out in the test.
- Hard: the wedges only stand once the last one is in; the corners beside the arch must be filled so the roof rests level.
- Wrong choices: a straight stone beam across the passage. Open: today it only blocks the opening (ready check, red). Needs a physical one, for example a stone beam too short for the span that tips into the passage under the roof.
- Temporary wood: one arch form.

## 7. Parthenon front, Athens (447-432 BC) — proposed

- Headpiece: the pediment (the triangle with its sculptures), lowered onto the frieze. Currently the acroteria are the load; the previous chat noted the pediment is the more important part. Needs the owner's choice: pediment, or acroteria as now.
- New pieces: abacus (square column top). Technique: eight evenly spaced columns (as on the real front); every architrave stone has both ends on a column top.
- Hard: a long even row; a column placed off its spot leaves an architrave end hanging.
- Wrong choices: an architrave stone with an end between columns tips (load); a wooden architrave snaps under the pediment (load); mudbrick in the top step crumbles (settle or load).
- Temporary wood: none.

## 8. Mausoleum of Halicarnassus (c. 350 BC) — proposed. The wooden-beam support level

- Headpiece: the four-horse chariot on top of the stepped roof (Pliny via worldhistory.org).
- New: wooden posts and beams as temporary scaffolding. Technique: the stepped roof courses reach in over the hall further than they can hold alone; they rest on wooden beams on wooden posts while being built, and hold by the weight of the outer courses once complete. The scaffolding is pulled out in the test.
- Hard: the props must be placed before the overhanging courses, the outer courses must be heavy enough, and nothing may rest on the posts except the roof.
- Wrong choices: too few outer courses (light counterweight): the roof falls into the hall when the props come out (supports); mudbrick in the podium crumbles (settle or load).
- Temporary wood: posts and beams, count set by the suggested build.
- Historical: podium, 36 columns, pyramid of 24 steps, chariot (Pliny). How the roof was carried over the colonnade walkway: unverified. Building on timber scaffolding is a game simplification.

## 9. Lighthouse of Alexandria (c. 280 BC) — proposed

- Headpiece: the statue on top (Zeus or Poseidon, from Roman coins; Wikipedia). Open: also the Tritons on the corners, or the statue only.
- New: a hollow tower. Technique: two thin walls around the inner shaft (Wikipedia: inner ramp), tied together by stone beams every few courses so they stand as one; each tier narrower and centred on the one below.
- Hard: the tallest level and the strongest wind; a wall left untied tips on its own; an off-centre tier tips the tower; the pile has no spare stone.
- Wrong choices: wooden tie beams snap under the upper tiers (load or quake); a tier set off centre tips in the wind; mudbrick at the base crumbles (settle).
- Temporary wood: none.

## 10. Valens Aqueduct, Constantinople (AD 368) — proposed

- Headpiece: the water channel along the top.
- New: nothing new; combines piers, arches and two tiers. Technique: reuse the arch forms: two forms for four arches. Build an arch, pull its form out, move it to the next arch.
- Hard: arches must be finished in order, lower before upper; a form pulled before its arch is closed drops the wedges.
- Wrong choices: mudbrick piers crumble (settle or load); a form pulled out early drops the arch (during building, before the test).
- Temporary wood: two arch forms, no more.
