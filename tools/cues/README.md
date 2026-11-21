# Cues: an event system for voice, glows, the ghost hand, teaching steps and demos

How every game in this library talks to a child who cannot read: what it says, what it shows, when. The game announces its moments (events: a piece picked up, a test failed, a screen shown); one table says, for each moment and condition, what is said, what lights up and what the child must do first; the engine (`tools/cues/engine.js`) plays the table and remembers what was said. The engine knows no game: a game names its own events, conditions, points and places. First built for Tower Builder (14 Nov 2026); its files are the worked example.

## The files

| File | What it is | Who edits it |
|---|---|---|
| `games/<game>/cues.json` | **Version A**, the cue table: the only source of what the game says and shows, and when | Claude, from the owner's comments |
| `games/<game>/cues.md` | **Version B**, the readable doc, written from A by `python3 tools/cues/cues_doc.py games/<game>/cues.json` | nobody: it is written again after every change to A |
| `tools/cues/engine.js` | the cue engine, shared: included inside a game's script by its build (`// @include ../../../tools/cues/engine.js`) | Claude |
| `src/index.html`, SECTION CUES | the game's side: its conditions (`CUE_CONDITIONS`), points (`pointTargets`, `gameTargetShapes`, `POINT_KINDS`), places (`cueContext`, `placeKey`), its per-frame moments (`cueGameTick`), drawings (`cueGameDraw`), screen changes (`cueGameNewScene`), button glow colours (`buttonGlowColor`), whether alerts beat the rhythm (`cueRhythm`), and its `cueEvent(...)` calls | Claude |
| `tools/harness.py cuetest` (tests in `tools/cue-tests.js`) | pass/fail checks, one per rule and per owner point: every name in A is known to the code; order, timing, repeats, once-only, what never plays together; each demo does what its lines say; the teaching steps done by the child's own actions | Claude |

The owner reads and comments on B. Every comment becomes a change to A (never to B, never a special case in the code), then B is written again, then the game is built, then the checks run.

## The model (three parts, the same in every game)

1. **Voice.** One line at a time, in the order fired. A line lasts its recording (`sounds/voice/NN.mp3`), or 2 s as a text box with a blue bar running out. Lines belong to the screen they were fired on; leaving it drops what is left. Kinds: `teach` and `queued` wait their turn; `bg` plays only when nothing else is playing or waiting; a flavour line fired with a teaching line at the same moment is dropped. While a teaching line plays or waits its turn, or a step waits for the child, every other line is dropped (an unplayed first time stays unused); in free building between steps other lines play as usual. When a test starts, lines still waiting from the building are dropped the same way. A teaching step is never dropped: it waits its turn (after the test, if one starts).
2. **Attention.** Per cue: `none` (what it points at glows), `point` (while the step waits, the rest darkens and only what it points at, or its `touch` list, can be touched), `freeze` (while the line plays, the rest darkens and the game stops). Use `freeze` and `point` sparingly: only where the child must watch, or must do one thing. The parent override is never held back.
3. **Steps.** A step the child has done is finished at that moment and the next step starts at once; nothing else (a child's action, a test starting) can end or remove a tutorial step. The invariant, checked by the cue tests with random actions: while a tutorial runs, its current step is alive (`tutorialLive()`). A cue that waits for an action keeps its glows and ghost hand until the action is done, and says its line again 5 s after it ends. An action that ends a step fires nothing else. Steps in a sequence are resumed where the child left them; a step that `needs` something missing (it broke, the game was reloaded) goes `back` to the step that makes it.

Glows start from the thing's own outline (a plank's glow is long), with a slow ring spreading out: yellow, or green/red for a green/red thing. Buttons show pressed while held and act when let go.

## The table (cues.json)

- `places`: the game's places in order (`key`, `name`): what "once per place", `byPlace` and sequences go by (Tower Builder: its sites).
- `rules`: the model and the game's own rules, in the owner's words. `about`, `notes`: free text.
- `words`: plain meanings of every event, condition, point and field the table uses (B is written from them; the doc tool stops if one is missing). Events also say where the code fires them.
- `lines`: number → text (player language). `lineNotes`: number → note (changed, record again, ...).
- `groups`: sets of lines picked at random, never one of the last half played; `byPlace` for one set per place; `lineIf` for lines that need a condition.
- `cues`: one object per cue. `id`, `level` (see below), `topic`, `on` (event), `if` (conditions, `not ...`, `done:<cue>`), `once` (`ever`/`place`/`session`/`visit`), `kind`, `say` (number, `{byPlace}`, `{group}`), `volume` (louder or quieter line), `attention`, `points`, `touch`, `show` (`tap X`, `tap3 X`, `drag X > Y`), `wait` (event, or `until:<condition>`), `needs` + `back`, `start`, `after` (line when done), `then` (event when done), `do` (`teaching`, `demo`), `during: "test"`, `delay: "sound:<name>"`, `glow` (seconds, no line), `note`.
- `tutorials`: named groups of tutorial cues, one place each (`place`, `steps` in order, `then`). Where one stands is always known: `tutorialAt(name)` gives "not started", the cue it is on, or "done"; `tutorialRunning()` is true from its first step until its last is done; the condition `tutorial-pending` (built in) holds at a place whose tutorial is not done.
- `demos`: per place, `new` (what the place teaches) and `steps`: `tell N` (line while building), `put ...`, `wait S`, `say N` (line after, game frozen), `pull`, `taps SHAPE`, `fade`.

Every cue on an event fires when its conditions hold (in table order). Alternatives are written as conditions that exclude each other (`done:<cue>`, `not ...`).

## Levels (owner 21 Nov)

Every cue has one; the table check fails without it.
1. **tutorial**: a tutorial's steps and lines that show the child an action. Nothing interrupts them but an explanation, which waits its turn.
2. **intro**: the welcome, a place's intro.
3. **explanation**: what just happened or what a thing means (a piece crumbled, the test's lines). Never dropped by a tutorial: it waits its turn.
4. **flavour**: remarks, facts, praise, stories. Only when nothing else plays or waits, and never while a tutorial runs (also between its steps).
A dropped line's first time stays for later.

## Making cues for a new game

1. List the moments the child meets (enter, pick up, place, fail, win, idle...) as events; give each a line in `words.events` with where the code fires it.
2. List what a line can talk about as points, and the facts it depends on as conditions.
3. Write the cues and the first level's teaching steps in A; write B; the owner comments on B.
4. In the engine, add only the game's vocabularies (conditions, points, the `cueEvent` calls). The voice, attention, steps, sequences and demos parts are copied from the last game until they are moved to a shared library (shared code is taken from finished games, not built ahead).
5. Checks: the table check (every name known), one test per owner case (his exact actions), and a look at the real game for anything he will see.
