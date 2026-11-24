# Αρχιτέκτονες του αρχαίου κόσμου (Architects of the Ancient World)

A building game for a curious four-year-old, on a touchscreen PC. Formerly called Tower Builder.

The child is an architect of the ancient world. On a painted map of the Mediterranean and the Middle East, boats sail between ten famous building sites. At each site the child takes mudbricks, stones and wood from a small pile with their hand and builds the building's shape in real physics: pieces have weight, mudbrick crumbles under too much load, and wood snaps over a gap. When the shape is filled, the test button turns green. The test then blows wind from both sides, lowers a heavy headpiece onto the top and shakes the ground. If anything breaks or falls, the test fails and shows in red where. The child fixes it and tries again, and each building that stands opens the next site.

Everything is spoken (Greek voice recordings, no reading needed). The first site teaches the controls step by step.

## How to play

- **Start:** open `arxitektones-tou-arxaiou-kosmou.html` in a browser (it is one self-contained file). Press the glowing site on the map.
- **On the map:** tap a site to go there (a site opens when the one before it is built). Taps make ripples in the water; on the mountains a finger grabs stones that can be dropped or thrown (they splash in the sea, pile up on land and knock boats); a finger draws in the sand. Boats can be picked up, put down or thrown; travellers left on land carry their boat back to the sea. Map buttons in the top right: free play, textures, restart (press twice to erase everything), and the settings gear.
- **At a site:** drag pieces from the pile on the right into the dotted outline. Two fingers carry and turn a piece. Three quick taps send a piece back to the pile, as does dragging it there. Buttons: undo (top left), shovel (everything back to the pile), map, and the test button (red until the shape is filled, then green; grey once the building has passed, until it is changed).
- **Settings gear:** helper videos (a short demo at sites that teach something new), teaching (the first site's steps and the lines that explain the controls), music.
- **Parent key:** holding Ctrl opens every site and offers a quick build. The green button pressed within 3 s of letting go of Ctrl runs a 10x fast test.

## The ten sites

| # | Site | Date | What it asks for |
|---|---|---|---|
| 1 | Mastaba (Μαστάμπα) | c. 3000 BC | a wide, solid mass of mudbrick |
| 2 | Step Pyramid of Djoser (Πυραμίδα του Ζοζέρ) | c. 2650 BC | building tall in steps; heavy stone low, light mudbrick high |
| 3 | Ziggurat of Ur (Ζιγκουράτ της Ουρ) | c. 2100 BC | rows of mudbrick with long wooden courses |
| 4 | Lion Gate (Πύλη των Λεόντων) | c. 1250 BC | jambs, a stone lintel, the lion triangle on the lintel |
| 5 | Hypostyle Hall, Karnak (Υπόστυλη αίθουσα του Καρνάκ) | c. 1290-1220 BC | beams across gaps between columns |
| 6 | Ishtar Gate (Πύλη της Ιστάρ) | c. 575 BC | a stone arch on a wooden form |
| 7 | Parthenon (Παρθενώνας) | 447-432 BC | columns drum by drum, architrave, pediment |
| 8 | Mausoleum at Halicarnassus (Μαυσωλείο της Αλικαρνασσού) | c. 350 BC | beams reaching out from the core, held on wooden posts; a sloped roof |
| 9 | Pharos of Alexandria (Φάρος της Αλεξάνδρειας) | c. 280 BC | a tall hollow tower tied with wooden beams |
| 10 | Aqueduct of Valens (Υδραγωγείο του Ουάλη) | AD 368 | two tiers of arches, one form moved from arch to arch |

Each site also has one tempting wrong piece in its pile that makes the test fail.

## Where things are

| Path | What it is |
|---|---|
| `arxitektones-tou-arxaiou-kosmou.html` | **The game.** Built by `build.py`; never edit it by hand. |
| `src/index.html` | The game's code, one file with `SECTION:` markers (`grep -n "SECTION:"`). |
| `src/levels.js`, `src/map-routes.js` | The ten levels and the map's ports, boat lines and paths. Generated: edit the makers in `tools/`, not these. |
| `src/sounds/`, `src/sounds/voice/` | Sound effects and music; the voice recordings, one per line number (`NN.mp3`). |
| `src/art/` | Map, water, ground, textures, the sites' intro pictures (`intro/`), skies (`skies/`), travellers (`villagers/`), the loading picture. |
| `lib/` | planck.js, the physics engine. |
| `build.py` | Inlines code, sounds and pictures into the one game file. Run it before every test run. |
| `cues.json` | **What the game says and shows, and when**: the cue table (lines, glows, the tutorial, demos). The only place to change a line or its timing. |
| `cues.md` | The cue table in readable form, written from `cues.json` (`python3 ../../tools/cues/cues_doc.py cues.json`); never edit it. |
| `voice-lines.md` | The lines still to record; written by `build.py`. |
| `levels.md` | **What each level is**: the single source for outlines, piles and wrong pieces. Code follows it. |
| `levels.png`, `proposals/` | Pictures of the levels (made by `tools/level-pictures.py`) and the approved level proposals. |
| `design.md` | The design sheet approved at the start. |
| `checklist.md` | The owner's early fix lists (13 Nov) and what to check in the game for each. |
| `WARNINGS.md` | Traps found while working on this game. **Read first.** |
| `owner-shots/` | The owner's screenshots and recordings, named by date. |
| `tools/harness.py` | Runs every check: `python3 tools/harness.py <mode>` (modes below). |
| `tools/ci-checks.txt` | The list of every check of the game, run on GitHub when a push or pull request changes this game or something shared. |
| `tools/flows.py` | The whole-game test: one run from a fresh game to the last site, played as the child plays (the first site by hand with every lesson, the others with the quick build), every owner rule and bug report a checked step at its place. |
| `tools/backdoors.txt` | What a shortcut through the game's insides looks like; GitHub refuses a test containing one. |
| `tools/cue-tests.js` | The cue rules as pass/fail checks. |
| `tools/owner-tests.js` | Checks from the owner's lists: hand, pieces, levels, sounds, map, boats. |
| `tools/motion-ref.json` | The hand's approved feel (timings), recorded with `harness.py owner motion record` after the owner's yes. |
| `tools/level-spec.json`, `tools/level-tests.json` | The locked headpieces and the wrong builds each level must fail (written by `make-levels.py`). |
| `tools/spec-run.js`, `tools/spec-real.js` | The level checks' inner loops (used by `harness.py spec` and `real`). |
| `tools/make-levels.py`, `tools/make-map-routes.py`, `tools/make-ground.py`, `tools/geom.py` | Makers of `src/levels.js`, `src/map-routes.js` and `src/art/map-ground.png`, and their geometry helpers. |
| `tools/level-pictures.py`, `tools/sky-contrast.py` | Picture of all levels; how well each building stands out from its sky. |

Shared with other games, at the repo root: `tools/cues/` (the cue engine and its README), `tools/physics/` (the hand, contacts, loads, breaking), `tools/normalize-sounds.php` (makes every sound -16 LUFS), `docs/design-rules.md` (rules for every game).

## Running the checks

From this folder, after `python3 build.py` (and once per clone: `git config core.hooksPath .githooks`):

- `python3 tools/harness.py cuetest` -- the cue rules (seconds).
- `python3 tools/harness.py flows` -- the whole-game test (about 12 minutes here; the test page runs the game 4 times faster with short silent sounds). `STOP="<step name>"` ends it after that step.
- `python3 tools/harness.py owner [names]` -- the owner's lists (about 5 min for all).
- `python3 tools/harness.py spec [level numbers]` -- every level: the suggested build passes, every wrong piece fails, the pile (about 10 min for all).
- `python3 tools/harness.py map | real | sandbox | loudness | sizes | realwave | realintro | mapbuttons` -- the map on 14 screen sizes, the real game loop, free play, sound loudness, sizes, real taps, the intro, the map buttons.

Every check passes; a commit that changes the game must name its play-through test, which must pass (the commit gate in `.githooks/`).

## Now

The game is complete and playable. The tutorial never stops, whatever the child does and however fast; every cue has a level (tutorial, intro, explanation, flavour) and the first site's steps are a named tutorial; the cue engine knows the game only through its hooks (`tools/cues/README.md`). A failed test's red stays until its lines are said. The test button is grey while the building stands as it passed its test, until a piece is picked up or the pieces are cleared. The headpiece-dots line plays only at the first site. The map's outermost cells match the land or sea just inside them, so boats never sail along the edge.

## Open

- The whole-game test takes about 6 minutes here; the commit check allows 10. The slowest steps are the ones built by hand (the owner's first-site build, the wooden-top building).
- The drag-back lesson's "piece put in before / after the line" variants are played once, as "during"; the random cue check (cuetest) covers other orders.
- Sites 2-10 are finished with the quick build (owner 24 Nov); building them by hand is not tested.

## Task list

Owner, 24 Nov (verbatim):
2. anoter idea is to replace sound files for small files, ffs, its a test.
3. also do improvements as long as you keep in mind that theya re feature tests, so dont mock things.
4. and fix tests
5. "A parent then finishes the building with Ctrl" -> never use these hacks in tests. "they cut spoken lines off from inside the game." -> NEVER
