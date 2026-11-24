# Coloring Book

A painting game for a curious four-year-old, on a touchscreen PC. Not a worksheet: a real paint box. The child paints on a sandbox paper with five tools that behave like the real materials (acrylic, watercolour, oil pastel, marker, and a simple digital brush), each with its own brushes, on three kinds of paper. Wet paint mixes like pigment and dries with time; watercolour runs and dries with darker rims; the pastel smears and blends. Stickers, palettes, a colour picker and a see-through guide picture help. Every picture is kept on the PC and can be opened again. Outline pictures to colour in come later.

## How to play

- **Start:** open `coloring-book.html` in a browser (one self-contained file). The newest picture opens.
- **Paint:** one finger (or the mouse, or a pen with pressure) paints; other fingers are ignored. A finger or the mouse presses harder the slower it moves. A stroke may start beside the paper and come in. Ctrl+Z takes back the last stroke.
- **Left side, drawing tools:** acrylic, watercolour, crayon (oil pastel), marker, simple brush, spray, shapes, ink, pencil, stickers. The buttons take the colour chosen.
- **Bottom, colours:** the colour buttons are paint buckets. A tap fills the bucket (a full brush); holding goes round a third, two thirds, full, every half second. Choosing another colour keeps the amount. The palette button opens the palettes (Basic and a guide picture's own palette on top, then four columns of 10, each palette a bar of stripes: monochromes, a line, rainbows, a line, then the rest from simple to busy); white and black buckets are added when a palette has none; the pipette picks a colour from the painting (its own pointer, with a big swatch of the colour under it). With the sticker tool the bottom shows the stickers: drag one onto the paper, drag it off to remove it.
- **Right side:** brush (the brush shape, shown as the brush and as a real stroke of it), size (5 sizes, the same for every brush), canvas (a new picture on watercolour paper, smooth paper or cotton), guide picture (choose, show or hide, remove), undo (all the way back), new picture, gallery (every kept picture, with delete), delete (press twice within a few seconds; a touch anywhere else takes the first press back).
- **Esc** closes the gallery and other views.

## Tools and brushes

| Tool | Brushes | What it does |
|---|---|---|
| Acrylic | round, flat, scrub, knife | thick paint pushed by bristles, leaves streaks and leftover paint, mixes while wet, the brush runs dry; the bucket level is how much paint is on the brush |
| Watercolour | round, flat, mop (wetter, softer), dry brush | see-through pigment in water: runs inside the wet area, dries with a darker rim, layers darken, granulates in the paper's dips |
| Crayon (oil pastel) | tip, side | thick and opaque in the paper's raised grain; the bucket level is how hard it presses; passes build up, smear and blend, small lumps |
| Marker | bullet, chisel | see-through ink: each layer darker, crossings and the edge darker |
| Simple | round, square, each sharp or soft | plain digital paint: opacity is the bucket level, the soft row has blurred edges |
| Spray | fine, coarse (droplet size) | an airbrush: puffs many times a second, so a fast hand leaves them further apart; droplets scattered over a round area, thinner at its edge, as far apart at every size |
| Shapes | square, circle, triangle, star, heart, grass | as the Squares Brush: each shape twice as wide across as the hand moved in one frame (the square half that along the stroke, the others in their own proportions), touching the next, turned with the stroke, outlined, each a slightly different colour; a tap makes one shape of his usual speed's size |
| Ink | round, nib | opaque ink of many fine strands, thinner the faster the hand; a quick hand throws splash drops |
| Pencil | sharp, blunt, side | coloured lead only on the paper's raised grain; the bucket level is how hard it presses |

Flat brushes are held at one fixed angle, unless the turn switch in the brush popup is on: then every brush turns with the stroke. The lift switch there (off at the start) makes a fast hand lift the brush: above about 55 cm/s it rises, the faster the quicker, and once off it stays off until a new touch. The brush popup shows real strokes of each brush on the chosen canvas (`lib/previews`).

## Where things are

| Path | What it is |
|---|---|
| `coloring-book.html` | **The game.** Built by `build.py`; never edit it by hand. |
| `src/index.html` | The game's code, one file with `SECTION:` markers (`grep -n "SECTION:"`); its model in plain words is in the MODEL section. |
| `build.py` | Inlines Mixbox, the icons, the palettes and the brush previews into the one game file. |
| `lib/mixbox/` | Mixbox pigment mixing (shader `mixbox.glsl`, lookup picture `mixbox_lut.png`, `LICENSE`: CC BY-NC 4.0, Secret Weapons). |
| `lib/phosphor/` | Phosphor icons used on the buttons (`LICENSE`: MIT). |
| `lib/palettes/palettes.txt` | The palettes shown in the four columns, with the divider marks; the extras (x) are placed by `build.py`. |
| `tools/palette_groups.py` | Counts the hues a palette shows from its stripes; `build.py` orders the extras by it and the palette test checks it. |
| `lib/owner-palettes/` | The owner's palette files, the source of the four columns. |
| `lib/previews/` | The brush popup's stroke pictures, one file per canvas; made by `tools/previews.py`. |
| `design.md` | The design sheet approved at the start. |
| `WARNINGS.md` | Traps found while working on this game. **Read first.** |
| `owner-shots/` | The owner's pictures, named by date. |
| `tools/harness.py` | Builds the game and runs its play-through tests. |
| `tools/flows.py` | Play-through tests (`SECTION:` markers): the real page, real clicks, keys, drags and touches, at a finger's speed, each on a small test paper. |
| `tools/previews.py` | Paints the brush previews straight through the game's stroke code (under 2 minutes). |
| `tools/looks.py`, `tools/looks/` | Saves every brush's normal stroke as a picture; the `brush_looks` test fails when a brush no longer looks like its picture. |

Shared with other games, at the repo root: `.githooks/` (the commit gate), `docs/design-rules.md` (rules for every game).

## Running the checks

From this folder (once per clone: `git config core.hooksPath .githooks`):

- `python3 tools/harness.py flows [names]` -- the play-through tests; most take 2-8 s; the watercolour, undo and undo-room ones 15-30 s (paint dries in real time); all of them about 9 minutes (run in the background).
- `python3 tools/previews.py [tool ...]` -- remake the brush previews of those tools (all, if none named) after a change to how they look.
- `python3 tools/looks.py [tool ...]` -- save those tools' brush pictures again, only when their look is meant to change.

Each flow runs on a test paper (`coloring-book.html?paper=400x250@600,375`): that part of the full 1600x1000 paper, with the same canvas grain there, so a flow paints only the paper it needs. The flows that measure speed or the undo room keep the full paper.

How to work on the look: try numbers with direct measurements (strokes painted straight through the game's stroke code, as `tools/previews.py` does, no finger-speed drags); run the real-speed flow only once at the end. After the first version of anything visual, take one full-size screenshot and look at it before tuning anything.

Every check passes. A commit that changes the game must name its flow (`Flow: coloring-book <flow>`); the commit gate runs it and refuses the commit if it does not pass.

## Now

Sandbox paper with nine drawing tools on the graphics card, aiming at Rebelle's look. Words: "drawing tool" (left side), "brush" (its shape, in the brush popup), "colour button" (a paint bucket).
Speed acts as pressure; the lift switch in the brush popup makes a fast hand lift the brush (src K: LIFT_FROM, LIFT_FAST, LIFT_TIME).
Palettes: monochromes, rainbows, then the extras ordered by the hues they show (tools/palette_groups.py).
Every brush's look and brush picture is tested; the full test run takes about 9 minutes.

## Open

In this order:
1. Lifting: the three lift numbers adjustable on screen, so he can try combinations.
2. Spray: a brush choice of what it sprays: dots, shapes, leaves, stars, long grass blades, and more (propose them).
3. Shapes: remove the grass brush; no squeezed shapes (the square too); the pointer on the paper shows the shape as it paints; the start of a line (square brush) has the wrong size or turn: find it with a test.
4. Pointer: bring back the triangles pointing left and right by the direction of motion.
5. Speed: the three slowest tests (brush_looks, jerk_tail, flick_lifts) under 10 s each.
6. Pencil: draws like a professional drawing pencil (owner-shots/2026-11-23-pencil-*).
7. p5.brush (https://p5-brush.cargo.site/, MIT): try on one brush, measure stroke delay at his screen size (1536x960 at 125%), let him decide.
8. Acrylic: more impasto; no fish scales where passes cross; brush 3 looks like bad 3D; brush 4 paints jagged little lines and leaves edge traces; brushes that behave like real ones (speckles, many thin lines like pine needles).
9. Watercolour: brush 3 mixes more; brush 2 the shape of brush 1 with more water; ragged brush edges; dried speckles and granulation stronger and more real; brush 4 is bad.
10. Crayon (oil pastel) looks like bad 3D: match his pictures owner-shots/2026-11-23-oil-pastel-*.
11. Marker from scratch: follows the canvas grain, darkens over itself within one stroke, darker edges.
12. Drying times; outline pictures to colour in.

Changes reach main through a pull request (main refuses direct pushes).
