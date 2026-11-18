# kid-games

Library of independent HTML5 touchscreen games with Greek settings, for a Windows touchscreen PC. Primary player: a highly capable, curious four-year-old. Games first: real systems, strategy, physics and decisions, never preschool worksheets.

Authoritative brief: `docs/brief.txt`. Read only the section a task needs:

| Lines | Section |
|---|---|
| 10-60 | 1. Project brief (setting, authenticity, language, platform) |
| 61-98 | 2. What every game design must specify |
| 99-130 | 3. Global design principles |
| 131-1311 | 4. Ranked catalogue; find a game with `grep -n "^<N>\. " docs/brief.txt` |
| 1312-1345 | 5. Overlaps: how similar games stay distinct |
| 1346-1421 | 6. Development order, GDD contents, shared library, tech foundation |
| 1422-1458 | 7. Instructions for design work |

## Start of every chat

1. Attach the repo with `add_repo` (push access). If it or a push is refused, retry once before saying anything about access.
2. Read the game's `games/<game>/WARNINGS.md` (traps found in that game, written as instructions) and the "Now" and "Task list" sections of its `BUILD.md`. Nothing else until the task needs it.

## The two gates (they come before everything else)

1. **A question is answered first.** If the owner's message contains a question, the first thing sent is the answer (SendUserMessage), before any tool call that changes or tests anything. If an answer could change what gets built, stop after answering and wait.
2. **Name the owner of the behaviour before any edit.** Before changing code, send one plain sentence: "this is decided by X; X does it like this now; I will change X like this." X is the existing thing that already owns the behaviour: the cue table and its engine, the level spec, the shared physics, the hand model. If the change does not go into X, it is a workaround: do not build it, say so.

## How to think about any change (first principles)

- First ask what the thing is in the real world and in the game's own systems, then change that. A complaint is evidence about the model, never a case to special-case. A fix that starts with "if <the reported situation>" is a patch.
- Use what the systems already provide. Order between things (a line, then a test part, then a sound) is the cue system's job: "after cue X is done", where a cue is done when its voice and its visuals are done. Never decide what happens next by peeking at whether something is currently playing, moving or touching.
- Things of one kind behave alike: one model, one drawing, one set of numbers for all map alerts, all pieces, all voice lines, all impact sounds. A difference needs the owner's reason. Equal quantities by the owner's measure (weight in blocks, size, strength) behave equally everywhere they are used.
- Start interactive or physical behaviour from the standard technique (the engine's own demos, how games usually do it), named in a code comment. Write the model as a few numbered parts in plain words at the top of its code. Adding a part needs the owner's yes; more than three parts means propose a simpler whole.
- No hidden memory of earlier moments, no switching on noisy simulation readings, no thresholds where behaviour jumps.
- When the real world gives a different result than the owner wants, tell him what it gives and let him choose. Never force the result with an extra rule.
- Read a new instruction narrowly: it changes the case he names. It never silently cancels an earlier instruction; if two conflict, ask one yes/no question saying what each answer changes.

## Testing

- Test first, in the real game. A flow test (`games/<game>/tools/flows.py`, run by `tools/harness.py flows`) does what the owner does: real page, real clicks, keys and drags at a real rate, his settings. For a bug, first a flow repeating his exact steps that fails the way he says; it stays forever.
- A check measures what he notices. If he reports a gap, a delay or an order, the check measures that gap, delay or order.
- Tests that guard earlier owner rules are never edited, loosened or deleted to fit a change. A failing old test is a found conflict.
- Never change the game to make a test pass. If a test fails, first decide from the failure detail whether the game or the test is wrong.
- Keep runs short (seconds each). Run only what the change can affect, in the foreground. If a point takes more than about five minutes, stop and tell the owner why in one line.

## Talking to the owner

- English only. Short plain prose: what changed (one line each), answers, downloads. No reasoning, logs, diffs, recaps or offers.
- Game terms only: pieces, hand, button, test, map, what he sees. Never code names or internals.
- Never contradict what he says he did or saw; an unknown cause is stated as unknown and found with a test.
- Never call anything agreed or done unless he said so. A proposal stays a proposal.
- Questions to him are yes/no or pick-one, and say what each answer changes.
- Describe a game first as one concrete paragraph: who you are, what your hands do, the goal, what gets in the way.
- Go through every point and question in his message before replying; none dropped. A long list is copied verbatim into `BUILD.md` "Task list" first and answered point by point, numbered as he numbered them.
- Never invent rules, stats, mechanics or history. Research historical details; unknown is unknown.

## Working

- Be mindful of tokens: read only the sections a task needs. Each `src/index.html` has `// SECTION: NAME -- what's here` markers; `grep -n "SECTION:"`, then read around the exact function.
- Do what was asked, all of it, nothing more. No unasked refactors, features or suggestions.
- After every change: build, run the affected flows, commit, push, check the remote has the commit, and send only the changed HTML files as downloads.
- When a trap is found in a game (something that cost time or caused a wrong fix), add it to that game's `WARNINGS.md` as a one-line instruction. General lessons go here only if they hold for every game.
- At the end of a chat, rewrite the game's `BUILD.md` "Now" section (what the game is now and what is open, short; never an appended log) and the game's line in Status below. History lives in git.
- When a chat gets long, say so and give a handoff that stands alone: the owner's words verbatim, his screenshots saved in the repo.

## Cues (voice, glows, the ghost hand, teaching)

Shared event system in `tools/cues/` (engine `engine.js`, pattern `README.md`, doc tool `cues_doc.py`). Each game's cues live in one table, `games/<game>/cues.json`; the readable `cues.md` is written from it, never by hand. Every cue, and every ordering between cues and game events, is in the table, never in code only. The owner records from `games/<game>/voice-lines.md`, written by the build from the table; when a line is added or reworded, send him that file with the new numbers, and delete a changed line's old recording.

## Product rules

- All player-facing text in natural, correct Modern Greek. Design docs and code comments in English.
- Never require reading or spoken instructions: short labels, clear icons, visual demonstration. Not babyish.
- Touch and mouse are both first-class (development is on a PC without a touchscreen): Pointer Events, large targets, no hover, no tiny controls, no required keyboard, no multi-touch-only gestures.
- Proposals fit the player: a four-year-old placing things roughly. No precision demands.
- No numerals for gameplay quantities; see Quantities below.
- Real-time games must offer pause-and-plan or turn-based play.
- Level unlocks always have a parent override that opens any level.
- One coherent Greek period and region per game or campaign; do not mix eras.
- Conflict is abstract and non-graphic. No frightening imagery, ads, monetization, streaks or punitive timers.
- Failure is informative, retry is immediate, unrelated progress is never erased.
- Introduce one new rule at a time; difficulty comes from combining known rules, not from unfair controls.
- The owner supplies voice and sound files; code provides hooks. Every file goes through `tools/normalize-sounds.php` (-16 LUFS, peaks at most -1.5 dBTP) before it goes into a game, voice included; trim silence first.

## Quantities without numbers

Amounts, prices, capacities and strengths are shown as things to see and compare, not digits:

- Countable objects drawn individually (coins, sacks, soldiers, amphorae), few enough to take in at a glance, grouped when larger.
- Size for magnitude: small and big coins, small and big loads.
- Slots for capacity: a donkey has visible saddlebag places; a full one has no empty place.
- Fill levels for continuous amounts: water, time, stamina, progress.
- Comparison by placing side by side or pairing off, so "more" is seen, not calculated.
- Change shown as objects moving: coins leave the purse and goods arrive.

Exact representations per game are set in its GDD. A numeral may appear only as a secondary label.

## Period coverage

The brief's period list also includes the Greco-Italian War of 1940-1941 (Women of Pindus). These settings replace the brief's, so that 1821 and the Balkan Wars are covered. Mechanics are unchanged; historical details are researched at GDD time.

| Game | Setting |
|---|---|
| 11. Castle Defense | War of Independence, 1821: defending a mountain pass or fortified position |
| 13. Island Conquest | War of Independence, 1821: the island fleets in the Aegean |
| 39. Treasure Hunt | First scenario: 1821-era historic house |
| 10. Cargo Train Routing | Balkan Wars, 1912-1913: supply railway |
| 6. Bridge Builder | Second campaign: Balkan Wars, 1912-1913, army engineers |
| 7. Little Fighters | Open; not tied to a historical sport (for example an all-heroes roster). Decided in its GDD |

Kept as written in the brief: Lost Mine (Byzantine mine with carts on rails) and Women of Pindus content. Siege Engineer: check which throwing machines fit which period before use.

## Tech

- HTML, CSS, JavaScript. Canvas for game scenes, physics, animation; DOM for menus and UI.
- LocalStorage or IndexedDB for progress and settings; Web Audio API; fullscreen support.
- No backend. Runs locally on the PC.
- Each game independently playable and testable, launched from one library page.
- Landscape screens of any size: layouts scale, nothing assumes a fixed resolution.
- Art is replaceable: every visible thing is drawn through a named skin entry with a simple code-drawn default. Gameplay shapes and sizes do not depend on the art.

## Design sheet

Every game starts as a one-page sheet at `games/<game>/design.md` with exactly these rows. The owner marks each row keep, change or cut; nothing is built that is not on an approved sheet. The prototype exists only to answer the last row. Anything not from the brief is marked "new".

| Row | Content |
|---|---|
| Pitch | One plain paragraph a non-designer understands at once: who you are, what you do, the goal, what gets in the way |
| Fantasy | One sentence: who the player is and what they achieve |
| Toy | What is fun to do with no goal at all |
| Seconds loop | What the player repeats every few seconds |
| Minutes loop | One level or session from start to end, including failure and retry |
| Days loop | What changes and accumulates across sessions |
| Mechanics | The rules |
| Dynamics | The behaviour and decisions that emerge from the rules |
| Kinds of fun | Which of the eight this game aims at, and which it does not: sensation, fantasy, narrative, challenge, fellowship, discovery, expression, pastime |
| Competence | How the player sees that they caused the result |
| Autonomy | Where the player chooses how |
| Relatedness | What they can show or share with someone |
| Mastery | Optional goals for a player who wants more |
| What would kill the fun | The specific risks |
| Prototype must answer | The questions the prototype is built to test with the child |

Sources: MDA for the middle rows, nested loops for the loop rows, self-determination theory for competence, autonomy and relatedness.

## Game folders

Each game has `games/<game>/` holding everything a chat needs: `design.md` (approved sheet), `BUILD.md` ("Now" and "Task list"), `WARNINGS.md` (the game's traps as instructions), `src/`, `lib/`, `tools/` and the built single HTML file. A chat on a game reads nothing outside its folder unless a file there says so.

## Process

These override the brief where they differ.

- Per game: design sheet, then a rough prototype of the core mechanic tested with the child, then the full GDD at `games/<game>/gdd.md` (brief lines 1367-1385), then the full build.
- Build one game to a genuinely playable standard before starting others. Shared code is extracted from finished games, not built in advance.
- First game: Tower Builder.
- Priority after it: Waterworks, Mechanical Workshop, Siege Engineer, Cargo Train Routing and Robot Programming move up; the trade and conquest games (Donkey Caravan Trader, Merchant Shipping, Castle Conquest, Island Conquest) move down.
- Games that need on-screen run and jump buttons (Women of Pindus, Adventure Platformer, Beat-'em-up, Little Fighters) get a control prototype before any commitment.
- Tiers C and D are a backlog, not a commitment. Nothing is discarded.

## Status

- Tower Builder, now Αρχιτέκτονες του αρχαίου κόσμου (`games/arxitektones-tou-arxaiou-kosmou`): playable; ten-site picture map, levels from `levels.md`, test (wind both ways, load, earthquake), cues and voice. Current state and open points: its `BUILD.md` "Now".

## Decided

- File layout: one self-contained HTML file per game (opens by double-click) plus a library page. Shared code lives once in the repo; a build script copies it into each game file. Test saved progress on the target PC early.
- Tower Builder campaign (owner decision, an exception to the one-period rule): ancient Mediterranean and Middle East up to late Roman Constantinople, ten famous buildings in chronological order (list in its design.md).
- Shared code: `tools/physics/` (steady clock, the hand, contacts and weight, what rests on what, breaking; `tools/physics/README.md`) and `tools/cues/` are included in each game's script by its build (`// @include ../../../tools/...` lines in `src/index.html`). A game never copies them; changes go into the shared file and every game using it is checked.
- Physics: Planck.js 1.4.2 (MIT) embedded in the game file; Matter.js only if stacking proves unstable in play.
