# Coloring Book

A painting game for a curious four-year-old, on a touchscreen PC. Not a worksheet: a real paint box. The child paints on a sandbox paper with five tools that behave like the real materials (acrylic, watercolour, oil pastel, marker, and a simple digital brush), each with its own brushes, on three kinds of paper. Wet paint mixes like pigment and dries with time; watercolour runs and dries with darker rims; the pastel smears and blends. Stickers, palettes, a colour picker and a see-through guide picture help. Every picture is kept on the PC and can be opened again. Outline pictures to colour in come later.

## How to play

- **Start:** open `coloring-book.html` in a browser (one self-contained file). The newest picture opens.
- **Paint:** one finger (or the mouse, or a pen with pressure) paints; other fingers are ignored. A finger or the mouse presses harder the slower it moves. A stroke may start beside the paper and come in. Ctrl+Z takes back the last stroke.
- **Left side, drawing tools:** acrylic, watercolour, crayon (oil pastel), marker, simple brush, spray, shapes, ink, pencil, stickers. The buttons take the colour chosen.
- **Bottom, colours:** the colour buttons are paint buckets. A tap fills the bucket (a full brush); holding goes round a third, two thirds, full, every half second. Choosing another colour keeps the amount. The palette button opens the palettes (Basic and a guide picture's own palette on top, then four columns of 10, each palette a bar of stripes: monochromes, a line, rainbows, a line, then the rest from simple to busy); white and black buckets are added when a palette has none; the pipette picks a colour from the painting: touch, slide onto the colour (a big swatch shows it), lift to pick. With the sticker tool the bottom shows the stickers: drag one onto the paper, drag it off to remove it.
- **Right side:** brush (the brush shape, shown as the brush and as a real stroke of it), size (5 sizes, the same for every brush), canvas (a new picture on watercolour paper, smooth paper or cotton), guide picture (choose, show or hide, remove), undo (all the way back), new picture, gallery (every kept picture, with delete), delete (press twice within a few seconds; a touch anywhere else takes the first press back).
- **Esc** closes the gallery and other views.

## Tools and brushes

| Tool | Brushes | What it does |
|---|---|---|
| Acrylic | round, flat, filbert, fan, rigger; a second row: the same five with impasto paint (a fuller brush, a thicker coat, deeper ridges) | thick paint pushed by bristles, leaves streaks and leftover paint, mixes while wet, the brush runs dry; the bucket level is how much paint is on the brush |
| Watercolour | round, flat, mop (wetter, softer), dry brush | see-through pigment in water: runs inside the wet area, dries with a darker rim, layers darken, granulates in the paper's dips |
| Crayon (oil pastel) | tip, side | thick and opaque in the paper's raised grain; the bucket level is how hard it presses; passes build up, smear and blend, small lumps |
| Marker | bullet, chisel | see-through ink: each layer darker, crossings and the edge darker |
| Simple | round, square, each sharp or soft | plain digital paint: opacity is the bucket level, the soft row has blurred edges |
| Spray | fine, coarse (droplet size) | an airbrush: puffs many times a second, so a fast hand leaves them further apart; droplets scattered over a round area, thinner at its edge, as far apart at every size |
| Shapes | square, circle, triangle, star, heart, grass | as the Squares Brush: each shape twice as wide across as the hand moved in one frame (the square half that along the stroke, the others in their own proportions), touching the next, turned with the stroke, outlined, each a slightly different colour; a tap makes one shape of his usual speed's size |
| Ink | round, nib | opaque ink of many fine strands, thinner the faster the hand; a quick hand throws splash drops |
| Pencil | sharp, side; a second row: the same, soft | coloured lead only on the paper's raised grain; the bucket level is how hard it presses; each pass lays its mark at once and every new pass (crossing, going back) adds a layer; the soft row lays a thinner see-through layer so colours mix |

Flat brushes are held at one fixed angle, unless the turn switch in the brush popup is on: then every brush turns with the stroke. The lift switch there (off at the start) makes a fast hand lift the brush: above about 55 cm/s it rises, the faster the quicker, and once off it stays off until a new touch. The brush popup shows real strokes of each brush on the chosen canvas (`lib/previews`).

## Where things are

| Path | What it is |
|---|---|
| `coloring-book.html` | **The game.** Built by `build.py`; never edit it by hand. |
| `src/index.html` | The game's code, one file with `SECTION:` markers (`grep -n "SECTION:"`); its model in plain words is in the MODEL section. |
| `build.py` | Inlines Mixbox, the icons, the palettes and the brush previews into the one game file. |
| `lib/mixbox/` | Mixbox pigment mixing (shader `mixbox.glsl`, lookup picture `mixbox_lut.png`, `LICENSE`: CC BY-NC 4.0, Secret Weapons). |
| `lib/phosphor/` | Phosphor icons used on the buttons (`LICENSE`: MIT). |
| `lib/palettes/palettes.txt` | The palettes shown in the four columns (the owner's own), with the divider marks. |
| `lib/owner-palettes/` | The owner's palette files (22 Nov), the source of the four columns. |
| `lib/previews/` | The brush popup's stroke pictures, one file per canvas; made by `tools/previews.py`. |
| `design.md` | The design sheet approved at the start (20 Nov). |
| `WARNINGS.md` | Traps found while working on this game. **Read first.** |
| `owner-shots/` | The owner's pictures, named by date. `owner-shots/avoid/`: his screenshots of wrong results, named by what is wrong; none of it may show again. |
| `tools/harness.py` | Builds the game and runs its play-through tests. |
| `tools/ci-checks.txt` | The list of every check of the game, run on GitHub when a push or pull request changes this game or something shared. |
| `tools/flows.py` | Play-through tests (`SECTION:` markers): the real page, real clicks, keys, drags and touches, at a finger's speed. The whole-game run (`whole_game`, section WHOLE GAME) plus separate short tests of each tool. |
| `tools/backdoors.txt` | What a shortcut through the game's insides looks like; a test containing one is refused. |
| `tools/previews.py` | Paints the brush previews straight through the game's stroke code (under 2 minutes). |
| `trials/` | The acrylic trial (25 Nov): `acrylic-trial.src.html` (a stand-alone paper with the five brushes, his reference beside it), `build_trial.py` (builds `acrylic-trial.html` with the game's paint amounts and pressure, refuses a script that does not parse), `look_all_refs.py` (a scene like each of his acrylic pictures, beside it), `look_cases.py <brush>` (his mixing cases), `look_dots.py` (tap and line per brush; each brush with a third, two thirds and a full bucket, and with a slow, usual and fast hand; spiral until empty), `look_wet.py` (his wet-paint cases), `look_shake.py` (his cases with a shaking hand), `look_moves.py [shake]` (his 26 Nov wet cases with all five brushes: starts on wet paint, a swirl over wet paint, bands over bands). Pictures go to the temp folder. |
| `tools/looks.py`, `tools/looks/` | Saves every brush's normal stroke as a picture; the `brush_looks` test fails when a brush no longer looks like its picture. |

Shared with other games, at the repo root: `.githooks/` (the commit gate), `docs/design-rules.md` (rules for every game).

## Running the checks

From this folder (once per clone: `git config core.hooksPath .githooks`):

- `python3 tools/harness.py flows [names]` -- the play-through tests; a whole-game step can be run alone by its name while it is built.

How the tests are laid out (a sandbox with no levels):
- **The whole-game run** (`whole_game`, about 2.5 minutes) plays the game on the full paper in the order the child meets it: painting, every drawing tool, the brush popup, the buckets, the palette popup, the colour picker, undo and Ctrl+Z, stickers, the guide picture, canvases, the gallery, deleting, keeping pictures. Each part is checked once, at its place; between parts it does what he would: Esc, back to the Basic palette, a new page. UI and order rules go here.
- **Separate short tests** (every other flow): how one drawing tool or brush looks or behaves (mixing, drying, lifting, splashes, widths, frame times, brush pictures). Each starts on its own fresh paper, often a small test paper, and needs many repeats or a precise start, so they stay out of the long run. They run at the same time as the whole-game run, split over machines on GitHub (`tools/ci-checks.txt`).
- A new owner rule about what he sees in the game's screens goes into the whole-game run at its place; a rule about a tool's look or physics is a separate short test.
- Tests only read the page (where things are drawn, what the paper shows, what is kept); time passes through the page's clock or real waiting, never by a call into the game (`tools/backdoors.txt`).
- `python3 tools/previews.py` -- remake the brush previews after any change to how a tool, brush or canvas looks.
- `python3 tools/looks.py` -- save the brush pictures again, only when a brush's look was meant to change.

Each flow runs on a test paper (`coloring-book.html?paper=400x250@600,375`): that part of the full 1600x1000 paper, with the same canvas grain there, so a flow paints only the paper it needs. The flows that measure speed or the undo room keep the full paper.

How to work on the look: try numbers with direct measurements (strokes painted straight through the game's stroke code, as `tools/previews.py` does, no finger-speed drags); run the real-speed flow only once at the end. After the first version of anything visual, take one full-size screenshot and look at it before tuning anything.

Every check passes. A commit that changes the game must name its flow (`Flow: coloring-book <flow>`); the commit gate runs it and refuses the commit if it does not pass.

## Now

Sandbox paper, paint engine on the graphics card, aiming at Rebelle's look. Words: "drawing tool" = acrylic, watercolour, crayon (oil pastel), marker, simple, spray, shapes, ink, pencil; "brush" = the brush shape inside one drawing tool; "colour button" = a paint bucket filled to the paint amount. Palettes are stripe bars in four columns of 12 with bold dark dividers, a palette that runs along the spectrum runs reddish first, the rest keep their own order; the extras include scene palettes from Coolors he chose: monochromes (Payne's grey between Blue and Purple) and a grey scale, a bit wider than his files, rainbows, then the extras by number of hues (one, two, three, more); no palette colour is ever dropped (a palette's own near-white or near-black is its white or black bucket, always first). The chosen bucket is a little bigger and ringed, and fits between the paper and the screen edge. Brushes and the pointer turn with the stroke (switch in the brush popup). Speed acts as pressure, and with the lift switch on a fast hand lifts the brush (numbers LIFT_FROM 2000, LIFT_FAST 4000, LIFT_TIME 0.17 in src K: paper dots a second, about 36 a cm); once off the paper it stays off until a new touch. Spray is an airbrush puffing on the clock; shapes are the Squares Brush; ink is fine strands that splash at quick (not lifting) speed. Tests include every brush's look (tools/looks) and every brush picture.

## Open

Do next, in this order (his words are in the Task list):
- Acrylic is rebuilt in `trials/` first (his yes, 25 Nov), then moved into the game, replacing the brushes and impasto row of pull request #31 (merged into main earlier; keep its spray, groove and curve fixes). Impasto is dropped (owner 25 Nov 22:42).
- Trial now (`trials/acrylic-trial.src.html`, numbered parts at the top of the script): per pixel a Mixbox pigment mix, its top coat, the dried paint under it, when it was laid (wet 25 s), its surface lumps. The brush is a row of bristles (round, flat, filbert, fan, rigger) on a short string behind the hand; a loaded brush covers fully with clean edges, paint is a paste (thicker at the sides, lumps, fine relief, lit from the top left, no shine), each bristle empties by distance then leaves opaque dry-brush specks, a fast hand presses lightly. Wet paint: the brush meets its top coat, mixes by amount, and each bristle picks a little up and lays it down again. One pass of the brush acts once per pixel.
- What is wrong now (his 26 Nov pictures in `owner-shots/avoid/`): swirling does not move or mix the wet paint under it; zigzags, arcs and rings where strokes cross wet paint or start (they come from the once-per-pixel rule); dots are stamped shapes, not taps; the blue-strokes picture is out of reach.
- Next, his yes 26 Nov 08:43, in this order: (A) paint that moves: wet paint becomes paint the brush pushes and carries along, mixing all the time (the way the better painting programs do), replacing the once-per-pixel rule; (B) tapping: a dot or a tap touches only with the bristle tips and leaves tiny clustered specks, fewer the drier the brush; (C) paint amount as in the game (tapping a colour fills its bucket a third, two thirds or full: `LOADS` in `src/index.html`) moved into the trial; (D) pressure as in the game (a pen's pressure, otherwise the hand's speed: slower is harder).
- How to work (his rules): test every case yourself before sending, with all five brushes, a steady hand and a shaking hand (look scripts above); compare with every picture in `owner-shots/2026-11-25-acrylic-*` side by side and with every picture in `owner-shots/avoid/` (none of those faults may show); send only when all are right, with the comparison sheet.
- Watercolour brush library and look (his 25 Nov pages), then 17-21; crayon (22); marker (23); spray other shapes; slow separate tests; drying times; outline pictures later.

## Task list

Numbers are his points of 23 Nov; pictures in `owner-shots/2026-11-23-*`. Acrylic references of 25 Nov: `owner-shots/2026-11-25-acrylic-*`.

- Acrylic (25 Nov): strokes like his acrylic pictures (`owner-shots/2026-11-25-acrylic-*`): flat opaque paint, scratchy broken dry-brush edges and ends, strokes on top of strokes keep their colour, wet paints mix like fluids (blue and yellow make a rich green), a full brush lasts long but does run out, no outlines when it runs out; 5 basic brushes (round, flat, filbert, fan, rigger). No impasto (owner 25 Nov 22:42: we don't do it): when the trial moves in, the game's impasto row goes too.
- Acrylic (26 Nov): swirling moves and mixes the wet paint under it; no zigzags, arcs, rings or scales where strokes cross or start; a tap leaves tiny clustered specks, not a stamped shape; paint amount and pressure as in the game; nothing in `owner-shots/avoid/` may show.
- Watercolour brush library (25 Nov): real brushes, and strokes that look like these pages and their "Similar images": https://www.shutterstock.com/image-vector/green-watercolor-splash-stain-paint-brush-2501995219, https://www.shutterstock.com/image-vector/watercolor-paint-textures-set-water-color-2819536941.
- Acrylic 25: brushes by behaviour, not only tip shape (e.g. speckles, many thin lines like pine needles): bristles that move when dragged.
- Watercolour 17: the 3rd brush mixes more.
- Watercolour 18: the second row is the first row's shapes with more water, for softer colour-to-colour mixing.
- Watercolour 19: stroke edges a bit irregular, as a real brush makes them (side-by-side picture).
- Watercolour 20: the dried look (speckles and everything else drying makes) more real and more intense.
- Watercolour 21: the 4th brush is bad.
- Crayon 22: the oil pastel looks like bad 3D; match his oil pastel pictures.
- Marker 23: model it from scratch: takes the paper texture, darkens when a stroke goes back over itself without lifting, darker outer edges (coffee-ring), darker where it crosses dry earlier ink.
- Spray: spray other shapes too, such as stars and other icons.
