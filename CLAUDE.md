# kid-games

Library of independent HTML5 touchscreen games with Greek settings, for a Windows touchscreen PC. Primary player: a highly capable, curious four-year-old. Games first: real systems, strategy, physics and decisions, never preschool worksheets.

Game design rules (product rules, quantities, periods, tech, design sheet, game folders, process, the brief): `docs/design-rules.md`. Read the part a task needs.

## Start of every chat

1. Attach the repo with `add_repo` (push access). If it or a push is refused, retry once before saying anything about access. Then turn on the commit gate: `git config core.hooksPath .githooks`.
2. Read the game's `games/<game>/WARNINGS.md` (traps found in that game, written as instructions) and its `README.md` (what the game is, where every file is, how to run the checks, and its "Now" and "Task list"). Nothing else until the task needs it.

## How to work

- Act as a professional software developer: clean code (one owner per behaviour, no dead code, no leftovers, names that say what things are, no duplication) and test-driven development (a failing test first, then the code that makes it pass, then clean up).
- **Process beats speed.** Never skip, shorten or reorder a test step to save time; make the tests and tools faster instead.
- **The commit gate enforces test-first.** A commit that changes a game's code must carry `Flow: <game> <flow> ...`; `.githooks/commit-msg` runs each named flow and refuses the commit unless it failed on the code before and passes now. Never bypass it (`--no-verify`).
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

- Before every change, re-read this Testing section.
- Test first, in the real game. A flow test (`games/<game>/tools/flows.py`, run by `tools/harness.py flows`) does what the owner does: real page, real clicks, keys and drags at a real rate, his settings. For a bug, first a flow repeating his exact steps that fails the way he says; it stays forever.
- A check measures what he notices. If he reports a gap, a delay or an order, the check measures that gap, delay or order.
- Tests that guard earlier owner rules are never edited, loosened or deleted to fit a change. A failing old test is a found conflict.
- Never change the game to make a test pass. If a test fails, first decide from the failure detail whether the game or the test is wrong.
- Keep runs short (seconds each). Run only what the change can affect, in the foreground. If a point takes more than about five minutes, stop and tell the owner why in one line.

## Debugging (read before touching any bug)

1. **Read the code before writing a test.** Follow the owner's action through the code by reading it: the input handler, the events it fires, the engine functions they reach. Write down every place that can change the state involved (adds it, ends it, removes it, skips it). The bug is almost always in one of those places, usually where something is removed or skipped.
2. **Name the broken invariant, then fix every path that breaks it.** E.g. "a running tutorial always has exactly one live step". Find every code path that can break it and fix them all, not only the first one found. Prefer making it impossible (one owner of the state) over guarding each path.
3. **Repeat his action exactly, then vary its timing.** His order, his speed ("fast", "at once", "during the line"). Write the same flow with the action before, during and after the moment he names. A test that never does what he did proves nothing.
4. **Anything odd in a test is a bug until the code proves otherwise.** A step skipped, a line cut, a stuck state, a repeat: never call it "how the test clicks" without showing the code path that makes it harmless.
5. **Look, don't guess.** Log the events and the state around the action once (event names, what fired, what was removed), read the log, then remove the logging.
6. **Test the invariant, not only the story.** Add a check that drives many random action orders and timings (seeded, fast) and fails when the invariant breaks.
7. **Never say "fixed" until his exact steps failed before the change and pass after**, and say what was fixed in his terms. If what he did is unknown, say so; never present a guessed path as his.
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
- After every change: build, run the affected flows, commit, push, check the remote has the commit, and send only the changed HTML files as downloads.
- When a trap is found in a game (something that cost time or caused a wrong fix), add it to that game's `WARNINGS.md` as a one-line instruction. General lessons go here only if they hold for every game.
- At the end of a chat, rewrite the game's `README.md` "Now" section, keep its file map true (what the game is now and what is open, short; never an appended log, never a list of what was done or when: "done: batch 1 ..." is a log) and the game's line in Status in `docs/design-rules.md`. History lives in git.
- Every game has a `README.md`, readable by a person: what the game is, how to play it, its levels or parts, where every file and folder is and what it is for, how to run its checks, then "Now", "Open" and "Task list". Example: `games/arxitektones-tou-arxaiou-kosmou/README.md`. A new game gets one from the start; a file added, moved or removed is changed in its map in the same commit.
- Never make a history, log or changelog file (such as `BUILD-history.md`), and never append updates to any file as a log. History lives in git commit messages only.
- Hand off when going on costs more than a new chat: when the chat is so long that each step spends many of the owner's tokens, or when rules start slipping (a rule broken, a point dropped, a question asked twice). Not after a fixed number of messages. Then rewrite "Open" and give one line to paste into the next chat; his words and screenshots stay in the repo.
