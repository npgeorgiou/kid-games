# kid-games

Library of independent HTML5 touchscreen games with Greek settings, for a Windows touchscreen PC. Primary player: a highly capable, curious four-year-old. Games first: real systems, strategy, physics and decisions, never preschool worksheets.

Game design rules (product rules, quantities, periods, tech, design sheet, game folders, process, the brief): `docs/design-rules.md`. Read the part a task needs.

## Start of every chat

1. Attach the repo with `add_repo` (push access). If it or a push is refused, retry once before saying anything about access. Then turn on the commit gate: `git config core.hooksPath .githooks`.
2. Read the game's `games/<game>/WARNINGS.md` (traps found in that game, written as instructions) and its `README.md` (what the game is, where every file is, how to run the checks, and its "Now" and "Task list"). Nothing else until the task needs it.

## How to work

- Act as a professional software developer: clean code (one owner per behaviour, no dead code, no leftovers, names that say what things are, no duplication) and test-driven development (a failing test first, then the code that makes it pass, then clean up).
- **Process beats speed.** Never skip, shorten or reorder a test step to save time; make the tests and tools faster instead.
- **The commit check enforces the Testing rules.** Games listed in `.githooks/strict-games.txt` are checked by `.githooks/game_checks.py` on every commit and, on GitHub, on every push: test first, no back-door moves, the whole test set within 10 s. Any other game must carry `Flow: <game> <flow> ...` in the commit message (each named flow must pass) until its full run is fast enough to join the list. On GitHub every push also runs every check of every game (listed in its `tools/ci-checks.txt`), split over machines that run at once. Never bypass a check (`--no-verify`).
- **No failing tests, ever.** Every test in the repo passes after every change. A failing test is never left in place, skipped or reported as "already failing": find whether the test or the code is wrong, and if only the owner can decide, ask him before the change is called done.

## The two gates (they come before everything else)

1. **A question is answered first.** If the owner's message contains a question, the first thing sent is the answer (SendUserMessage), before any tool call that changes or tests anything. If an answer could change what gets built, stop after answering and wait.
2. **Name the owner of the behaviour before any edit.** Before changing code, send one short line: "this is decided by X; X does it like this now; I will change X like this." X is the existing thing that already owns the behaviour: the cue table and its engine, the level spec, the shared physics, the hand model. If the change does not go into X, it is a workaround: do not build it, say so.

## How to think about any change (first principles)

- First ask what the thing is in the real world and in the game's own systems, then change that. A complaint is evidence about the model, never a case to special-case. A fix that starts with "if <the reported situation>" is a patch.
- Use what the systems already provide. Order between things (a line, then a test part, then a sound) is the cue system's job: "after cue X is done", where a cue is done when its voice and its visuals are done. Never decide what happens next by peeking at whether something is currently playing, moving or touching.
- Start interactive or physical behaviour from the standard technique (the engine's own demos, how games usually do it), named in a code comment. Write the model as a few numbered parts in plain words at the top of its code. Adding a part needs the owner's yes; more than three parts means propose a simpler whole.
- No hidden memory of earlier moments, no switching on noisy simulation readings, no thresholds where behaviour jumps.
- When the real world gives a different result than the owner wants, tell him what it gives and let him choose. Never force the result with an extra rule.
- Read a new instruction narrowly: it changes the case he names. It never silently cancels an earlier instruction; if two conflict, ask one yes/no question saying what each answer changes.

## Testing

Rules a machine can check are checked by the commit check (`.githooks/commit-msg`) and by GitHub on every push (`.github/workflows/tests.yml`); the owner reviews every change to either. Being refused is the normal way these rules are kept; never bypass a check (no `--no-verify`, no turning hooks off, no editing a check to let a change through).

- Before every change, re-read this Testing section.
- **One whole-game test per game** (`games/<game>/tools/flows.py`, run by `tools/harness.py flows`; owner 24 Nov). It starts from a fresh game, with nothing saved, and plays the whole game in the game's own order, the way the child plays it. It covers the start, the menus or map and their interactions, then every part or level in turn. Every owner rule and every bug report is a checked step at the place in the game where it happens, named in his words, with his words in a comment. Each step prints PASS or FAIL and the run goes on. There are no separate tests repeating the same steps, and no step is checked twice. A rule that needs another state (ticks off, a restart, a reopened page) gets there the way the child would: through the settings, the restart button, a reload.
- **Test first.** For every owner point and every bug: first the step that repeats his exact steps on screen and fails, then the code that makes it pass, then clean up. Checked: a commit that changes a game's code must change its test in the same commit.
- **Only what the child does.** Taps, drags, two-finger touches and keys on what is drawn, at a hand's rate, waiting as he waits (for a line to end, a demo to finish, a heavy piece to come). Never a parent's shortcut (such as the Ctrl quick build or the Ctrl fast test), never a line or cue cut off or skipped from inside the game, never a call or a write into the game's state (no setting a tutorial's place, a site as done, a memory, a piece's position). The page is only read: to find where things are drawn, what is heard (the line playing), what sounds were asked for and what is shown. Checked on GitHub: each game's `tools/backdoors.txt` lists what such a shortcut looks like, and a test containing one is refused.
- **Check what he sees and hears.** A step checks what is on screen (colours drawn, pieces where he can see them, buttons) and what he hears and when. If he reports a gap, a delay or an order, the step measures that gap, delay or order.
- **Every bug report becomes a step** at its place in the run, repeating his steps and his timing; it stays forever.
- **Random play.** Every game also has a seeded random-play part that plays through the screen and checks, after every move, the rules he can see.
- **Test sounds are short.** The test page gets the same short silent sound for every sound and voice line: what matters is what waits for them, not how long they are (owner 24 Nov).
- **The whole test runs on every push** (GitHub runs every game's checks, listed in its `tools/ci-checks.txt`, on machines that run at once), and the parts a change touches run before its commit. One FAIL refuses it. No failing tests, ever.
- **Fast.** Waits are on what the screen shows, with short limits, never fixed sleeps longer than a hand's pause; one browser and one page per run. Time every run; a slow step is made faster before anything else, never shortened or skipped.
- Tests that guard owner rules are never loosened or deleted to fit a change. When the owner changes a rule, its step changes in the same commit and the commit message names the rule he changed. A failing old step is a found conflict.
- Never change the game to make a test pass. If a step fails, first decide from the failure detail whether the game or the test is wrong; if only the owner can decide, ask him.
- **One owner point per commit**: its step, its code, the run, commit, push.

## Debugging (read before touching any bug)

1. **Read the code before writing a test.** Follow the owner's action through the code by reading it: the input handler, the events it fires, the engine functions they reach. Write down every place that can change the state involved (adds it, ends it, removes it, skips it). The bug is almost always in one of those places, usually where something is removed or skipped.
2. **Name the broken invariant, then fix every path that breaks it.** E.g. "a running tutorial always has exactly one live step". Find every code path that can break it and fix them all, not only the first one found. Prefer making it impossible (one owner of the state) over guarding each path.
3. **Repeat his action exactly, then vary its timing.** His order, his speed ("fast", "at once", "during the line"). Write the same step with the action before, during and after the moment he names. A test that never does what he did proves nothing.
4. **Anything odd in a test is a bug until the code proves otherwise.** A step skipped, a line cut, a stuck state, a repeat: never call it "how the test clicks" without showing the code path that makes it harmless.
5. **Look, don't guess.** Log the events and the state around the action once (event names, what fired, what was removed), read the log, then remove the logging.
6. **Test the invariant, not only the story.** Add a check that drives many random action orders and timings (seeded, fast) and fails when the invariant breaks.
7. **Never say "fixed" until a test step repeating his exact steps passes**, and say what was fixed in his terms. If what he did is unknown, say so; never present a guessed path as his.
8. **Time box.** If the cause is not found in 15 minutes of reading, tell him in one line what is known and what is being checked.

## Talking to the owner

- English only. One short line per item, nothing else: what changed, the answer, or the yes/no question. No causes, explanations, how it was found or tested, reasoning, logs, recaps or offers unless he asks. The whole reply fits on a phone screen.
- Game terms only: pieces, hand, button, test, map, what he sees. Never code names or internals.
- Never contradict what he says he did or saw; an unknown cause is stated as unknown and found with a test.
- Never call anything agreed or done unless he said so. A proposal stays a proposal.
- Questions to him are yes/no or pick-one, and say what each answer changes.
- Go through every point and question in his message before replying; none dropped. A long list is copied verbatim into the game's `README.md` "Task list" first and answered point by point, numbered as he numbered them.
- Never invent rules, stats, mechanics or history. Research historical details; unknown is unknown.

## Working

- Be mindful of tokens: read only the sections a task needs. Each `src/index.html` and every other file over 500 lines has `SECTION: NAME -- what's here` markers; `grep -n "SECTION:"`, then read around the exact function. A file that grows past 500 lines gets them; a marker is updated in the same change as the code it names.
- Commands print only what is needed: counts, PASS/FAIL lines, the few lines asked for. Never print whole files, data or long logs (filter with `grep`, `grep -c`, `cut`). Never cut test results with `head` or `tail`: count every FAIL and read them all.
- Do what was asked, all of it, nothing more. No unasked refactors, features or suggestions.
- After every change: build, run the affected test steps, commit, push, check the remote has the commit, and send only the changed HTML files as downloads.
- When a trap is found in a game (something that cost time or caused a wrong fix), add it to that game's `WARNINGS.md` as a one-line instruction. General lessons go here only if they hold for every game.
- At the end of a chat, rewrite the game's `README.md` "Now" section, keep its file map true (what the game is now and what is open, short; never an appended log, never a list of what was done or when: "done: batch 1 ..." is a log) and the game's line in Status in `docs/design-rules.md`. History lives in git.
- Every game has a `README.md`, readable by a person: what the game is, how to play it, its levels or parts, where every file and folder is and what it is for, how to run its checks, then "Now", "Open" and "Task list". Example: `games/arxitektones-tou-arxaiou-kosmou/README.md`. A new game gets one from the start; a file added, moved or removed is changed in its map in the same commit.
- Never make a history, log or changelog file (such as `BUILD-history.md`), and never append updates to any file as a log. History lives in git commit messages only.
- Hand off when going on costs more than a new chat: when the chat is so long that each step spends many of the owner's tokens, or when rules start slipping (a rule broken, a point dropped, a question asked twice). Not after a fixed number of messages. Then rewrite "Open" and give one line to paste into the next chat; his words and screenshots stay in the repo.
