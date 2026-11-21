# Warnings for this game (read at the start of every chat)

Traps found while working on this game, as instructions. Add a line whenever a new one costs time or causes a wrong fix.

## Testing
- `tools/harness.py` loads the built file, not `src/`: run `python3 build.py` before every test run.
- The green button pressed less than 3 seconds after letting go of Ctrl runs the 10x fast test (Ctrl latch). A flow that copies the child pressing green waits more than 3 s after Ctrl.
- In a site, ESC leaves the site, so flows cannot skip a line with ESC there; on the map they can.
- Flows that run a whole test take 15-35 s each; run only the ones the change touches, a few per call, in the foreground.

## Cues
- Never let a cue finish (and start the next one) while a list of cues is being rebuilt: what it adds is lost. Rebuild the list, then finish (18 Nov: the tutorial stopped when a step was done before its line).
- A recording's length is the line's length: a quiet tail after the words delays whatever waits for the line. Check where the words end (ffmpeg volumedetect in short windows) when a wait after a line feels long.
- A cue is done when its voice and its visuals are done. Anything that must come after a cue (a part of the test, another line, a sound) waits for that cue to be done, declared in `cues.json`. Never wait on "is the voice playing".
- The test's lines: the green-button line, then each part (wind, load, earthquake) together with its own first-time explanation; after the test, its success or failure line comes before the site's finish line.
- Lines dropped while a teaching line plays or a step waits for the child, not merely between steps (owner 15 Nov).
- ESC in a site leaves at once; ESC during the site intro skips the intro (owner 18 Nov). Both are guarded by tests; keep both.

- A teaching step is never dropped from the queue (test start, a child's action): a dropped step never finishes and the teaching stops for good (21 Nov). Drop lines with the engine's dropQueued.
- Every cue has a level (tutorial, intro, explanation, flavour) in cues.json; the engine applies it. Change a cue's behaviour by its level, never with a condition in the game (owner 21 Nov).
- A cue is done only when the line its "then" started is done too: the test's red stays until the failure's lines are said (21 Nov).

## Building and the hand
- The outline is the shape of the building (solid, with only its real openings), never the union of the suggested build's pieces.
- Every piece weighs its size counted in its material's regular block; lifting, carrying, pushing, breaking and the test all go by total weight.
- The hand: the standard planck drag (mouse joint, strength a multiple of the weight held) is the base. It was once patched for days with special cases (touching, near, loaded, "too heavy"); every fix broke another. Change the model, never add a case. Real cases to check before shipping a hand change: a small stone pushed into a big block, a block grabbed at one end, two stacked blocks lifted, a block dragged along a wall, a fast swing.
- A rule naming several things ("breaks under four mudbricks and three stones") means separate cases unless the owner says combined; state the reading in one line.
- Every place in a level that matters gets a tempting wrong piece from the pile that fails the test.

## Speed
- The map's time goes into filling screen pixels, not into calculations: measure with a flush after each part of the frame before changing anything. The two water layers are the biggest cost.
