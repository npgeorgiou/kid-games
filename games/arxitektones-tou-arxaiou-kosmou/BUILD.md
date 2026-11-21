# Αρχιτέκτονες του αρχαίου κόσμου (Tower Builder)

Read `WARNINGS.md` first. Rules the owner gave live in the tests (`tools/flows.py`, `tools/cue-tests.js`, `tools/owner-tests.js`), the cue table (`cues.json`), the level spec (`levels.md`) and the owner's checklist (`checklist.md`). Where a decision came from: git history.

## Now

Done (owner, 18 Nov 2026). On 21 Nov: tutorial and cue fixes, the cue engine separated from the game (it knows the game only through its hooks, `tools/cues/README.md`), voice line 80 replaced.

You are an architect of the ancient world. On a picture map of the Mediterranean and the Middle East you sail to ten famous sites in order, from an Egyptian mastaba to Valens' aqueduct. At each site you take mudbricks, stones and wood from a small pile with your hand and build the building's shape. Then the green button tests it: wind from both sides, a load lowered on top, an earthquake. If anything breaks or falls, the test fails and shows in red where; fix it and try again.

- Map, sites, hand, physics: as on 18 Nov (see `levels.md`, `tools/physics/`).
- Cues (21 Nov): every cue has a level (tutorial, intro, explanation, flavour) in `cues.json`, applied by `tools/cues/engine.js`. The first site's steps are the tutorial "first-site"; the engine knows where it stands (not started, its cue, done). Tutorial steps are never dropped (a test started early no longer stops the tutorial); flavour never plays while the tutorial runs; explanations wait their turn; a failed test's red stays until its lines are said.
- Owner's words, 21 Nov: "the tutorial of 1st level stopped, after the 'plintoi apo laspi' ... no 'this is the red button', no 'this is the shovel, the undo', no 'green can be pressed now', and no red was shown when the wind moved the pieces"; "ALSO WE NEED ANOTHER CUE LEVEL LOGIC ... TUTORIAL, FLAVOUR, INTRO, EXPLANATION ... A TUTORIAL THAT HAS CUES ... SO WE CAN DETECT EASILY IF THE TUTORIAL ENDED OR WHERE IT IS NOW"; "MAKE THE CHANGES TO THE CUE FRAMEWORK, NOT PATCH THE GAME FILES".
- Tests for these: cue tests `tutorial-where`, `explanation-waits-in-tutorial`, `flavour-not-between-steps`, `tutorial-never-stops` (random actions); flows `tutorial-no-mudbrick-line`, `tutorial-test-before-red-step`, `tutorial-test-before-undo-step`, `red-during-fail-lines`, `tutorial-put-right-after-dragback`, `tutorial-piece-in-before/during/after-dragback`, `pile-piece-not-in-wall`.

## Open

- None. Every test passes (21 Nov): cue tests, flows, `owner`, `spec`, `map`, `real`, `sandbox`, `loudness`, `sizes`, `realwave`, `realintro`, `mapbuttons`. Known and accepted: the Valens and Parthenon piles do not fit the sidebar at 1280x800 (owner, 13 Nov).

## Task list

- None.
