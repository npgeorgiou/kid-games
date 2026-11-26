# kid-games

Library of independent HTML5 touchscreen games with Greek settings, for a Windows touchscreen PC. Primary player: a highly capable, curious four-year-old. Games first: real systems, strategy, physics and decisions, never preschool worksheets.

Game design rules (product rules, quantities, periods, tech, design sheet, game folders, process, the brief): `docs/design-rules.md`. Read the part a task needs.

UI design guidelines: `tools/ui-design/README.md`. Read them and follow them, checklist included, before designing or changing anything a player sees or hears.

## Start of every chat

1. Attach the repo with `add_repo` (push access). If it or a push is refused, retry once before saying anything about access. Then turn on the commit gate: `git config core.hooksPath .githooks`.
2. Read the game's `games/<game>/WARNINGS.md` (traps found in that game, written as instructions) and its `README.md` (what the game is, where every file is, how to run the checks, and its "Now" and "Task list"). Nothing else until the task needs it.

## How to work

- Act as a professional software developer: clean code (one owner per behaviour, no dead code, no leftovers, names that say what things are, no duplication) and test-driven development (a failing test first, then the code that makes it pass, then clean up).
- **Process beats speed.** Never skip, shorten or reorder a test step to save time; make the tests and tools faster instead.
- **The commit check enforces the Testing rules.** Games listed in `.githooks/strict-games.txt` are checked by `.githooks/game_checks.py` on every commit and, on GitHub, on every push that changes them: test first, no back-door moves, the whole test set within the game's own time limit (seconds in its `tools/time-limit.txt`, else 20). Any other game must carry `Flow: <game> <flow> ...` in the commit message (each named flow must pass) until its full run is fast enough to join the list. On GitHub every push and pull request also runs every check (listed in its `tools/ci-checks.txt`) of each game it changes, split over machines that run at once; see Testing. Never bypass a check (`--no-verify`).
- **When the commit check refuses work the owner wants pushed** (for example after a design phase with tests not yet updated): commit that work with the check turned off for that one commit, push it and open a pull request without asking, say so in one line with its link, and leave the merge to him; never merge it yourself (owner 26 Nov).
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
- **Test first.** For every owner point and every bug: first a test step that repeats his exact actions on screen and fails, then the code that makes it pass, then clean up. Checked: a commit that changes a game's code must change its tests in the same commit.

**What the tests are**
- **One whole-game run per game** (`games/<game>/tools/flows.py`, run by `tools/harness.py flows`). It starts from a fresh game with nothing saved and plays the game in its own order to its end: the start, the menus and screens and their interactions, then every level or part, and what follows each one in the level and on the screens after it. Every owner rule and bug report that belongs to that story is a checked step at its place, named in his words, with his words in a comment. Each step prints PASS or FAIL and the run goes on. No step is checked twice.
- **Depth where it matters, shortcuts where it doesn't.** The part the owner is working on, or the part a rule is about, is played fully by hand. Parts that are only on the way may use the game's own shortcuts for a parent (such as a quick build), so the run reaches the end fast.
- **Separate short tests** for checks that need a precise starting situation, many timing variants or many repeats: a fine detail of one interaction, its before/during/after variants, a seeded random-play check. Each starts from a saved game loaded the way the game loads its own save, never from state written into a running game. They run in parallel with the whole-game run, take seconds each, and a wobble in one cannot slow or break the others.
- **Random play.** Every game has a seeded random-play test that plays through the screen and checks, after every move, the rules the player can see.

**How tests play**
- **Only what the player does.** Taps, drags, multi-finger touches and keys on what is drawn, waiting as he waits. Never a line or cue cut off from inside, never a call or a write into the game's state. The page is only read: where things are drawn, what is heard, what is shown. Checked on GitHub: each game's `tools/backdoors.txt` lists what such a shortcut looks like, and a test containing one is refused.
- **Check what he sees and hears.** A step checks what is on screen and what he hears and when. If he reports a gap, a delay or an order, the step measures that gap, delay or order.
- **Act like a person, robustly.** Wait until the game shows the result of an action before the next one; aim with a little room rather than exactly on an edge; if an action did not take, do it again as a person would; follow things that move.
- **Read the game's own numbers** (durations, delays, sizes, limits) from the game in the check, never type a copy of them into the test.

**Fast by design, from the first test**
- **The test page has its own settings**, injected by the harness the same way for every game: a game speed above 1 (the game has one speed setting, 1 in the real game) and one short silent sound for every sound and voice line. What matters is what waits for what, not how long it lasts.
- **Everything is measured in game time.** Checks of gaps and delays, and every pause, use the game's own clock, never the computer's. A pause waits for something the game shows, with a short limit; never a fixed sleep longer than a hand's pause.
- **Build each new step on its own first** (start at it, from a saved game), then join it to the run. Never develop by re-running the whole run from the start.
- **Time every run.** Every step prints how long it took; the slowest step is made faster before anything else, never shortened or skipped. One browser and one page per run.

**Done means passing everywhere**
- **A push runs the tests of the games it changes** (`.githooks/changed_games.py`): GitHub runs every check of each changed game (listed in its `tools/ci-checks.txt`), on machines that run at once, and the parts a change touches run before its commit. A change in `games/<game>/` runs that game's tests only; a change to anything shared outside `games/` (shared code, test tools, GitHub setup) runs every game's tests; a change only to text files (`.md`) outside `games/` runs none. One FAIL refuses it. No failing tests, ever.
- **A new or changed test is done only when it has passed three runs in a row here and one run on GitHub.** A test that passes here but fails on GitHub is a failure, found by checking GitHub's result after every push.
- Tests that guard owner rules are never loosened or deleted to fit a change. When the owner changes a rule, its step changes in the same commit and the commit message names the rule he changed. A failing old step is a found conflict.
- Never change the game to make a test pass. If a step fails, first decide from the failure detail whether the game or the test is wrong; if only the owner can decide, ask him.
- **One owner point per commit**: its step, its code, the run, commit, push, GitHub's result.

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
- Go through every point and question in his message before replying; none dropped; answer in his numbering.
- His messages stay in the chat, never in the repo. What goes into the game's `README.md` "Task list" is his requests as short todos: rewritten, merged and compacted so each is terse and clear. A todo is deleted when it is done.
- Never invent rules, stats, mechanics or history. Research historical details; unknown is unknown.

## Working

- Be mindful of tokens: read only the sections a task needs. Each `src/index.html` and every other file over 500 lines has `SECTION: NAME -- what's here` markers; `grep -n "SECTION:"`, then read around the exact function. A file that grows past 500 lines gets them; a marker is updated in the same change as the code it names.
- Commands print only what is needed: counts, PASS/FAIL lines, the few lines asked for. Never print whole files, data or long logs (filter with `grep`, `grep -c`, `cut`). Never cut test results with `head` or `tail`: count every FAIL and read them all.
- Do what was asked, all of it, nothing more. No unasked refactors, features or suggestions.
- After every change: build, run the whole test set, commit, push. `main` is protected: work on a branch and open one pull request per batch of work (`gh api repos/npgeorgiou/kid-games/pulls -f title=... -f head=<branch> -f base=main -f body=...`); later commits go on the same branch.
- A change is done only when GitHub's `tests` check on the pull request's last commit has finished and passed (`gh api repos/npgeorgiou/kid-games/commits/<sha>/check-runs`). Wait for it; if it fails, read its log, fix, push again. Then merge the pull request yourself (`gh api -X PUT repos/npgeorgiou/kid-games/pulls/<n>/merge -f merge_method=squash`; owner's standing yes, 24 Nov), check main has it, and send only the changed HTML files as downloads. The owner never has to touch GitHub. Never report done before that.
- A game's own settings (test time limit, checks) live in its own folder, never in a shared file: a change to a shared file runs every game's tests (owner 25 Nov).
- When a trap is found in a game (something that cost time or caused a wrong fix), add it to that game's `WARNINGS.md` as a one-line instruction. General lessons go here only if they hold for every game.
- At the end of a chat, rewrite the game's `README.md` "Now" and "Open" (what the game is now and what is open, short) and its line in Status in `docs/design-rules.md`.
- Every game has a `README.md`, readable by a person: what the game is, how to play it, its levels or parts, where every file and folder is and what it is for, how to run its checks, then "Now", "Open" and "Task list". Example: `games/arxitektones-tou-arxaiou-kosmou/README.md`. A new game gets one from the start; a file added, moved or removed is changed in its map in the same commit.
- History lives only in git commit messages: never a history, log or changelog file, never updates appended to a file, never a list of what was done or when ("done: batch 1 ..." is a log).
- Hand off when going on costs more than a new chat: when the chat is so long that each step spends many of the owner's tokens, or when rules start slipping (a rule broken, a point dropped, a question asked twice). Not after a fixed number of messages. Then rewrite "Open", make sure every open request is a todo in the Task list, and give one line to paste into the next chat.
