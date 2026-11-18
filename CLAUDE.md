# kid-games

Library of independent HTML5 touchscreen games with Greek settings, for a Windows touchscreen PC. Primary player: a highly capable, curious four-year-old. Games first: real systems, strategy, physics and decisions, never preschool worksheets.

Game design rules (product rules, quantities, periods, tech, design sheet, game folders, process, the brief): `docs/design-rules.md`. Read the part a task needs.

## Start of every chat

1. Attach the repo with `add_repo` (push access). If it or a push is refused, retry once before saying anything about access.
2. Read the game's `games/<game>/WARNINGS.md` (traps found in that game, written as instructions) and the "Now" and "Task list" sections of its `BUILD.md`. Nothing else until the task needs it.

## The two gates (they come before everything else)

1. **A question is answered first.** If the owner's message contains a question, the first thing sent is the answer (SendUserMessage), before any tool call that changes or tests anything. If an answer could change what gets built, stop after answering and wait.
2. **Name the owner of the behaviour before any edit.** Before changing code, send one plain sentence: "this is decided by X; X does it like this now; I will change X like this." X is the existing thing that already owns the behaviour: the cue table and its engine, the level spec, the shared physics, the hand model. If the change does not go into X, it is a workaround: do not build it, say so.

## How to think about any change (first principles)

- First ask what the thing is in the real world and in the game's own systems, then change that. A complaint is evidence about the model, never a case to special-case. A fix that starts with "if <the reported situation>" is a patch.
- Use what the systems already provide. Order between things (a line, then a test part, then a sound) is the cue system's job: "after cue X is done", where a cue is done when its voice and its visuals are done. Never decide what happens next by peeking at whether something is currently playing, moving or touching.
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
- Go through every point and question in his message before replying; none dropped. A long list is copied verbatim into `BUILD.md` "Task list" first and answered point by point, numbered as he numbered them.
- Never invent rules, stats, mechanics or history. Research historical details; unknown is unknown.

## Working

- Be mindful of tokens: read only the sections a task needs. Each `src/index.html` has `// SECTION: NAME -- what's here` markers; `grep -n "SECTION:"`, then read around the exact function.
- Do what was asked, all of it, nothing more. No unasked refactors, features or suggestions.
- After every change: build, run the affected flows, commit, push, check the remote has the commit, and send only the changed HTML files as downloads.
- When a trap is found in a game (something that cost time or caused a wrong fix), add it to that game's `WARNINGS.md` as a one-line instruction. General lessons go here only if they hold for every game.
- At the end of a chat, rewrite the game's `BUILD.md` "Now" section (what the game is now and what is open, short; never an appended log) and the game's line in Status in `docs/design-rules.md`. History lives in git.
- When a chat gets long, say so and give a handoff that stands alone: the owner's words verbatim, his screenshots saved in the repo.
