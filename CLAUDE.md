# kid-games

Library of independent HTML5 touchscreen games with Greek settings, for a Windows touchscreen PC. Primary player: a highly capable, curious four-year-old. Games first: real systems, strategy, physics and decisions, never preschool worksheets.

Authoritative brief: `docs/brief.txt` (full catalogue of 40 games, design principles, GDD requirements). Read only the section a task needs, by line range:

| Lines | Section |
|---|---|
| 10-60 | 1. Project brief (setting, authenticity, language, platform) |
| 61-98 | 2. What every game design must specify |
| 99-130 | 3. Global design principles |
| 131-1311 | 4. Ranked catalogue; find a game with `grep -n "^<N>\. " docs/brief.txt` |
| 1312-1345 | 5. Overlaps: how similar games stay distinct |
| 1346-1421 | 6. Development order, GDD contents, shared library, tech foundation |
| 1422-1458 | 7. Instructions for design work |

## Working rules

- Be mindful of token economy. Read only the sections a task needs, never whole files.
- Repo access: the repo is always available. Attach it with `add_repo` (push access) at chat start; if that or a push is refused, retry `add_repo` once, then push. Never tell the owner there is no access without having retried.
- Do what was asked, all of it, in one go. A message that lists fixes plus questions gets the fixes built and the questions answered in the same reply; wait only when an answer genuinely changes what gets built. Ask a question only if no reasonable reading exists; otherwise pick the obvious reading and state it in one line.
- No unasked work: no refactors, extra features, polish, extra files or "while I was there" changes. No unasked suggestions in replies.
- Never show internal reasoning, tool output, test logs, diffs or process narration. The owner sees results only: what changed (one line each), answers, downloads.
- Cheapest path first: reason from code before running anything; one verification run at the end, not one per change; small targeted reads and edits; batch independent tool calls in one turn; never re-read what is already in context.
- Suggestions the owner asks for: short concrete lists, each item one or two lines, sourced where facts are involved (licences, history). No padding, no frameworks unless asked.
- Spend as few tokens as possible: no exploratory reading, no re-reading files already seen, batch edits into one command, verify once, keep replies to what the owner needs to decide or know.
- Every game's main source file (`src/index.html`) must have `// SECTION: NAME -- what's here` comments at its major divisions. Before touching a game's code, run `grep -n "SECTION:" src/index.html` to get the map, then read only the needed section (`sed -n 'A,Bp'` or `Read` with offset/limit). Never read the whole source file. When creating a new game, add these markers from the start.
- Debugging a physics/interaction bug: read the actual formula first and reason about whether it's dimensionally/logically right (e.g. does an "impulse" scale with mass the way it should) before writing any test. Most bugs here were findable by reading code, not by running it.
- One test harness per debugging session, edited in place and reused, not a new scratch file per check. One Playwright script covering several related checks beats one launch per check — each browser launch is pure overhead.
- Don't run the same thing two ways (e.g. an isolated Node repro of a physics joint, then the same thing again in-browser) unless the first way gave an answer you don't trust. Pick one and trust it.
- Replies: no restating the bug list back, no "here's what I checked," no step-by-step narration of the fix process. State what changed and why, in a few lines, then stop. Skip a remaining-work list unless something is actually left undone.
- If a message asks a question, answer it and wait before coding.
- When a message lists several things and one says "before you do work, do X" (or similar), do X first and send it to the owner (SendUserMessage) before any other tool call or work, then go on with the rest in the same turn (owner, 16 Nov: he asked for the building names first and got them only at the end).
- Never invent rules, stats or mechanics. Unknown or unverified details are stated as unknown. Research historical details; do not guess them.
- Change only what was asked. Fix bugs generically, not just the example mentioned.
- Answers: short plain prose, no recap, no offers, no command output. English only.
- How to speak to the owner: describe what he sees and does in the game (pieces, hand, button, test), never code names or internals; one idea per sentence; give the concrete case with real things ("a small block with another on top"), not formulas or units he did not use; a question must be answerable with yes/no or by picking one of the options given, and must say what each answer changes in the game; never ask what his message already decides; if unsure what he meant, state the reading and go on.
- Talk like a person pitching a game to a friend. Plain everyday words, no design jargon (no "brief", "loop", "dynamics", "mechanic" in conversation), no undefined terms. Describe any game first as one concrete paragraph: who you are, what you do with your hands, what you are trying to achieve, what gets in the way. Example of the register: "You are a dwarf who can walk and jump; you cross dangerous moving ground and dodge enemies to reach the end of the level." Tables and frameworks come after that paragraph, never instead of it.
- After every change: push, and give only the changed HTML files as downloads.
- At the end of a chat: update Status and the game's `BUILD.md`.
- One chat does the whole task list in the game's `BUILD.md`, however many items. Never split work across chats and never send the owner to start more chats for one list. To fit it all in one chat:
  - Read only `BUILD.md` "Current state" and "Task list". Do not re-derive decisions recorded there; when an item is ambiguous, take the obvious reading and state it in one line in the reply.
  - Map the code with `grep -n "SECTION:"`, then `grep -n` for the exact function or constant an item touches and read at most about 60 lines around it. Never read a whole section to "understand" it.
  - Make all edits of the chat in as few Python patch scripts as possible (exact-string replacements that assert one match), not one tool call per edit.
  - Keep thinking short: decide, edit, move on. No long design deliberation; a real open question goes to the owner in one line.
  - No screenshots unless the item is about how something looks, and then one image covering several items.
  - Verify once at the end with the game's existing harness (`tools/harness.py`, extended in place for new checks), output filtered to one line per level. Fix and rerun only what failed.
  - Commit, push and reply once at the end.
- Design decisions and tricky problems go to the strongest model; routine building from a `BUILD.md` goes to a cheaper one. Use helper agents only for reading a lot to return a little (research, large searches) or bulk repetitive work from an agreed pattern, and only when setting them up costs less than it saves.

## Mistakes made before; every chat must avoid them

- Never call anything agreed, settled or done unless the owner said so in his words. A proposal stays a proposal until he answers; never write a proposal into a file as a decision.
- Fix the rule, never the example. No per-level patches or exceptions; if a design does not satisfy a general rule, the design changes.
- Do not reason from numbers when the owner reports what he did. Repeat his exact action in the game (his stack, his lift, his quick build + test) as a harness test, see it fail, fix, see it pass.
- Never contradict what the owner says he did or saw. If the cause is unknown, say "unknown" and find it with a test; do not offer a guessed cause as an explanation.
- The outline is the shape of the building (solid, with only its real openings), never the union of the suggested build's pieces.
- Before replying, go through every point and every question in the owner's message, one by one, including questions inside a point, and make sure each is done or answered. Nothing silently dropped.
- Handovers must stand alone: the owner's own words verbatim, his screenshots saved into the repo and named, no references to things that exist only in the chat (item numbers, "the image above").
- Proposals must fit the player: a four-year-old placing pieces roughly. No precision demands.
- Tests must cover what the owner does and sees, not only the suggested builds: hand-built stacks, lifting, re-entering levels, the map, the button, what is painted red.
- Explain in game terms (pieces, hand, button, test, map), never internals (newtons, steps, sleeping bodies, function names), and never ask vague questions.
- A rule that names several things ("breaks under four mudbricks and three stones") was read as one combined stack when the owner meant separate cases. When a rule could be read either way, state the reading in one line before building on it; the owner's separate cases are separate tests.

- Similar things happen in similar ways (owner 18 Nov 2026: "consistency"). Things of one kind (the map's alerts, the pieces, the sounds of things hitting, splashes, buttons, voice lines) share one model, one drawing and one set of numbers; a new member joins its kind and gets no copy of its own. Before adding or changing a thing, list the others of its kind and make them match: the headpiece is a stone piece for the hand, its sounds and the red; every map alert (next, damaged, finished site) has the same rings, thickness and rhythm. A difference needs a reason the owner gave; when one member changes, change the kind, then check every member.
- Equal by the owner's measure means equal everywhere. Every piece of a material weighs its size counted in that material's regular block (a piece the size of two blocks weighs two blocks); no per-shape weight factors. Everything that uses weight (lifting, carrying, pushing, breaking, the test) goes by the total weight, so equal weights behave alike whatever the shapes, one piece or a stack. Every new piece gets a test that it weighs its size in blocks and lifts, carries and pushes like the same weight built from blocks. The same holds for any other quantity (size, strength) in any game: before adding a thing, list every place that quantity is used and check the new thing behaves like its equal there.

## One model, never patches (owner, 14 Nov 2026; for every game and every kind of problem)

The worst mistake so far: each complaint about the Tower Builder hand got its own special case (a different strength when touching, when near, when something sits on it, a "too heavy" switch, smoothing, a separate sideways push...). The cases fought each other, every fix broke something else, and the hand became unpredictable. Never again:

- Any behaviour (a hand, a vehicle, water, an enemy, a price) is one small model written down in plain words first: what it is in the real world, the few quantities it has, and the one rule that drives it. Prefer the engine's own physics and a standard technique (search for how games usually do it) over home-made rules.
- When the owner reports something wrong, ask "which part of the model is wrong?" Change that part, or the model, so the right behaviour falls out of it. Never add a condition for the reported case ("if touching and going up then ..."). If the fix you are about to write starts with "if" about a situation, stop: that is a patch.
- No hidden state that remembers earlier moments (smoothed readings, previous speeds, flags left from the last time) unless the model really has memory. Reading a quantity from noisy simulation results (contact forces) and switching on it is forbidden; compute it from what things are (their weight, size, what rests on what).
- No thresholds where behaviour jumps. Limits are smooth (a strength cap), and no ordinary situation sits exactly on a limit.
- Before changing the model: tests that pin every correct behaviour the owner has confirmed (the checklist), passing on the old code. After: the same tests pass. A test that fails after a rebuild is reported to the owner as a question, not patched over.
- If a model needs more than a handful of rules to satisfy the owner, say so and propose a better model instead of adding rules. Rebuilding is cheaper than a pile of patches.

## Building a behaviour without failing the owner (owner, 14 Nov 2026; every game)

What went wrong with the Tower Builder hand, and the rule each failure gives:

1. Home-made first, standard last. The hand was invented from scratch and patched for days; the standard Box2D/planck drag (mouse joint, strength a multiple of the weight held) was found only when the owner demanded an example. Rule: before writing any interactive or physical behaviour, search for how games and the engine's own demos do it, name the source in a code comment, and start from that.
2. Not thinking like the real world. A small stone shoved a big boulder, a wooden block stayed level held at one end, a fixed "arm strength" pushed everything with full force. Rule: before shipping, write a short table of the owner's everyday cases (a small stone pushed into a big block, a block grabbed at one end, two stacked blocks lifted, a block dragged along a wall, a fast swing), what a real person sees in each, and what the model predicts. Any mismatch means the model is wrong; fix the model, not the case. People act with a brain: they use the effort the load needs and slow down before touching things.
3. Constants never checked against real cases. Every number (strength, grip, speed, reach) gets checked against the case table above before it ships, not after the owner tries it.
4. Shipping a half-built rebuild. A version that broke rules the owner had already given (a small stone must not move a big one) was pushed and handed over. Rule: never push a change that breaks one of the owner's rules; if the new model cannot satisfy it yet, say so and keep the old one in the game.
5. Treating old numbers as rules. Test values recorded from the old, patched behaviour (exact carry times) were defended as requirements. Rule: the owner's words are the rules; numbers measured from an earlier build are only references. When they conflict with what he asks now, follow his words and tell him in one line what changed.
6. Asking instead of deciding. When the owner says what he wants ("real, consistent, not hacky"), do not ask him to choose between that and something else; build it.
7. Long chats and handoffs. Say early when a chat is getting long. Every handoff is in the reply itself, ready to paste: what the thing is now, what was done, what still differs from the owner's wishes, how to test, open questions. Before saying "pushed", check the remote has the commit.

## How I fail, and the hard stops against it (owner, 14 Nov 2026; every game, every kind of task)

My failure pattern, seen again and again: I build something simple, the owner reports a problem, and instead of fixing the cause I add one more rule on top. Each rule makes one complaint go away, the rules pile up and fight each other, and the thing becomes unpredictable. It happens because:
1. When the honest answer is "the real world gives X", I add a rule to force the result he wants, instead of telling him what the real world gives and letting him choose.
2. I treat a failing test as the goal and add whatever turns it green, instead of asking what is actually wrong.
3. I test with perfect, made-up input (exact positions, exact timing, ideal cases), not what the owner really does (a real mouse at its real rate, rough placements, a four-year-old's hand), so broken things look fine to me and I report them as working.
4. I report success from my own numbers, not from what he will see.

Hard stops:
- Every behaviour, system or rule set (a hand, a vehicle, a price, an enemy, a level rule) is written as a short numbered list of parts in plain words at the top of its code. Adding a part needs the owner's yes first: "the real world gives X; to get Y I would add Z", one line, then wait.
- More than three parts: stop, say so, and propose a simpler whole before writing code.
- Never add or change anything just to make a test pass. If the real world fails his test, that is a question for him.
- Check everything he will feel or see the way he will meet it: the real program running, real input at a real rate, his screen, his actions. A test with made-up input is a supplement, never the proof.
- Before saying something works, show it (a picture or video from the real program) whenever he has said it does not work.

## Long lists of change requests: how not to get lost (owner, 14 Nov 2026; every game)

However many points a message has (5 or 100), none is dropped, none is half done, and none undoes an earlier instruction:

1. Before any work, copy the owner's message verbatim into the game's `BUILD.md` as a numbered checklist: one line per point; a point with several requests or a question inside becomes several lines.
2. For each line, look up earlier owner rules on the same thing (`BUILD.md` updates, the cue table, `checklist.md`, `levels.md`) and note them; the new build must keep them, or the conflict goes to the owner as one yes/no question.
3. A point that repeats an earlier instruction ("didn't I say...") is a bug report: repeat his exact action in the real program, see it fail, then fix the cause.
4. Fix by changing the one model or the one table that owns the thing (cues: `cues.json`; levels: the level spec), never by a special case.
5. Every line gets a check that repeats his action, in the harness or the real program, and a result.
6. Before replying, go down the checklist line by line; the reply has one short line per point, numbered as he numbered them, with his questions answered. Nothing is called done that has not passed its check.
7. When the list cannot all be built in this chat, say which lines are left, in the checklist and in the reply, before stopping.
8. Every owner point becomes a permanent pass/fail test (cues: `tools/cue-tests.js`, run by `tools/harness.py cuetest`, all of it in seconds), named after what he asked, and the whole file runs before every reply. An instruction he has to give twice means its test was missing: add it, see it fail, then fix. A rule that lives only in a note gets lost; a rule that lives in a test cannot.
9. Fix the owner's complaint at the rule that caused it, then search for the other places the same rule decides (other levels, other demos, other steps) and test them too. Example (15 Nov): "the first-time mudbrick line plays during the teaching" was fixed twice for one step; the rule was "while a step waits", and the line slipped in between steps. The owner then said that rule went too far (the first crumble line vanished from the first site); the rule is "while a teaching line plays or a step waits for the child", tested by the child doing every step and a mudbrick breaking in the free building between steps.

## Cues (voice, glows, the ghost hand, teaching): `docs/patterns/cues.md`

Every game's cues live in one table, `games/<game>/cues.json` (version A); the readable `cues.md` (version B) is written from it by `tools/cues_doc.py`. The owner comments on B; every change goes into A, then B is written again. Never edit B by hand, never add a cue in code only.

The owner records the voice from one flat list per game, `games/<game>/voice-lines.md`, made by the game's build from the table every time (never by hand), with the lines that have no recording at the top. Whenever a line is added or its words change, send him that file and say which numbers are new; never leave a line only in the table or in cues.md. A changed line's old recording must be deleted in the same change, so the list shows it as not recorded.

## Test-driven, in the browser (owner, 17 Nov 2026; every game; comes before everything else about testing)

We work test first. Nothing is built, fixed or changed without a test that shows it, and the tests are the owner's own actions done in the real game.

- Flow tests. Each one drives the real game in a browser the way the owner does: the real page with its own frame loop, voice, cues and music on as he has them, real mouse clicks, drags and keys on the real buttons and pieces, settings changed through the real settings screen. They are not unit tests, and they never call internal functions to fake an action; reading the game's state through the test hook to check the result is fine. Each game keeps them in `games/<game>/tools/flows.py`, run by `tools/harness.py flows`.
- Order of work: write the flow, run it and see it fail, build, see it pass. A change is done only when its flow passes. When the owner reports a bug, the first step is a flow that repeats his exact steps and fails the way he says; it stays in the suite for good.
- Coverage: every happy path, end to end (start and first touch, the map, entering each kind of site, building by hand and with the quick build, the test passing, back to the map, free play, restart), with every setting that changes behaviour both on and off (each switch doubles the paths: test both sides). Plus the major failure paths: the test failing, pieces breaking, a wrong piece, sound blocked before the first touch, a setting turned off in the middle.
- Snappy: each flow takes seconds and the whole suite well under a minute. Skip voice with the game's own skip (ESC) where listening adds nothing, use the shortcuts the owner uses (Ctrl quick build and fast test), start from a fresh page, check the state every 50 ms and give up fast with a message that shows what was seen.
- Run the whole flow suite before every reply that changes a game. Report only failures.

## Testing (owner, 14 and 17 Nov 2026; every game; overrides anything below that asks for more)

The owner judges the work by how long it takes. Most of a slow session is lost to tests: long runs, repeated runs, and runs that fail because the test was wrong. These rules keep testing a small part of the time.

Time
- Budget: a normal list of changes takes minutes, not half an hour. One test run takes seconds, at most a minute. A run that would take longer is badly designed: redesign it before starting it, never wait for it.
- Never sleep or poll while a long run finishes. If a run cannot finish in the foreground in about a minute, it is too big.
- If the work is clearly taking longer than it should, stop, tell the owner in one line why, and change approach.
- Time limit per owner point: if one point takes more than about five minutes, stop and tell him why in one line (owner 18 Nov: the stones took "a century", lost to broken checks, not to the game).
- When anything is slow (a test, a frame, a hitch the owner feels), measure where the time goes before changing anything: time the parts, find the one that costs, fix that.

Designing a test
- Build the situation directly; do not simulate your way to it. If the test needs "a boat waiting at a port", put a boat there through the test hook. Do not run the world for ten simulated minutes hoping it happens. Add a small setter to the hook when one is missing.
- Simulate only the seconds the checked behaviour takes, with the largest time step that still shows it.
- A test that does not look at the screen runs the game without drawing (for a canvas game: shrink the canvas to one pixel while it runs, then restore it). Drawing is most of a frame's cost.
- Whatever the owner feels in real time (a hitch, a lag, a delay between two things) gets a check on it: the slowest frame while it happens, or the time between the two events, measured in the running game.
- Switch off every system the test is not about: voice and cue prompts, demos, idle timers, music, other moving actors. A test that touches the screen must make sure nothing (a prompt, a button, a circle) sits over the spot it presses, and must check that the press took effect before going on.
- Each test starts from a known state it sets itself, never from what an earlier test left behind.
- Before the full check, run a tiny probe of the setup (one frame: did the hold/tap/state actually happen?). Only then the real check.
- Every check reports, when it fails, the values needed to see why: what was expected, what happened, the state of the objects involved. The first failure must be enough to diagnose; never rerun just to get more information.
- One small check per change: a new change gets its own short check (seconds) of that change alone, not a step added inside a long run that does everything.
- Checks never break each other: a check does not clear or change what another one reads (a shared sound list, a counter), every watcher runs long enough to see the end of what it watches, and the places it uses are what they claim to be (dry land with no river on it).

When a test fails
- First decide whether the game or the test is wrong, from the failure detail and the code. Do not rerun anything until you know.
- Look at the game before blaming the check: watch what the game actually did for a few seconds (a short trace of the thing, or a picture). If the game is right, the check is wrong; fix the check once.
- Two strikes: if a check fails twice because of the check itself, stop fixing it; ship the game with a picture of it working and fix the check afterwards.
- After the owner stops a run, first make sure nothing was left half done (code set aside, files half written) before anything else.
- Fix the cause, then rerun only that test, once.
- Never change the game to make a test pass, and never loosen a check to make it pass. If the test was wrong, fix the test and say nothing about it to the owner unless it matters to him.

What to run
- Every run is reproducible: the same inputs give the same result. Never run the same test twice to "see if it varies". If two runs with the same inputs differ, find what leaks in (the clock, unseeded random numbers, leftover state, something measured that changes with time) and fix it; where chance is part of what is tested, fix the seed.
- Before running anything, decide from the code what the change can affect, and run only those tests. Example: a change to the hand acts only while a piece is held; the level runs never hold pieces, so they are not needed.
- Run whole-level or whole-game runs only when the change touches what they use, then once each, one screen size, fast mode.
- Repeated runs with varied input: a few (3-6), only where variation is the point; never 100.
- Each new rule gets one small test repeating what the owner did: see it fail, fix, see it pass. No other test runs during the fixing.
- Never rerun the whole suite after a small change. The full suite only when the owner asks, or once before a handover.

## Rules for every change (owner, 13 Nov 2026)

1. Before building a level, list every place in the building and what the child could put there from the pile. Each place that matters gets a tempting wrong piece that fails in the test.
2. Every rule the owner gives (strength, weight, size, outline) gets a test made of the cases he named. For a rule about a material, add one case for each way a piece can be used: lying flat, standing up, across a gap, falling.
3. After a physics change, rerun the earlier tests that the change can affect (see Testing), not the whole suite.
4. When the owner reports something, first repeat exactly what he did, on his screen size, until it fails the same way. Only then look for the cause.
5. A fix is never for one level or one piece. Before fixing, write down every place the same rule applies and test them all.
6. When a new rule conflicts with an old one, or makes a level impossible, ask the owner one yes/no question saying what each answer changes. Never quietly pick one.

## Product rules

- All player-facing text in natural, correct Modern Greek. Design docs and code comments in English.
- Never require reading or spoken instructions: short labels, clear icons, visual demonstration. Not babyish.
- Touch and mouse are both first-class (development happens on a PC without a touchscreen): Pointer Events, large targets, no hover, no tiny controls, no required keyboard, no multi-touch-only gestures.
- No numerals for gameplay quantities; see Quantities below.
- Real-time games must offer pause-and-plan or turn-based play.
- Level unlocks always have a parent override that opens any level.
- One coherent Greek period and region per game or campaign; do not mix eras.
- Conflict is abstract and non-graphic. No frightening imagery, ads, monetization, streaks or punitive timers.
- Failure is informative, retry is immediate, unrelated progress is never erased.
- Introduce one new rule at a time; difficulty comes from combining known rules, not from unfair controls.
- The owner supplies voice and sound files; code provides hooks for them. Every file he gives goes through `tools/normalize-sounds.php` (-16 LUFS, peaks at most -1.5 dBTP) before it goes into a game, voice included; trimming silence comes first.

## Quantities without numbers

Any game with amounts, prices, capacities or strengths shows them as things the player can see and compare, not as digits:

- Countable objects: coins, sacks, soldiers, amphorae drawn individually, kept small enough to take in at a glance and grouped when larger.
- Size for magnitude: small and big coins, small and big loads.
- Slots for capacity: a donkey has visible saddlebag places; a full one has no empty place.
- Fill levels for continuous amounts: water, time, stamina, progress.
- Comparison by placing things side by side or pairing them off, so "more" is seen, not calculated.
- Change shown as objects moving: coins leave the purse and goods arrive.

Exact representations per game are set in its GDD. A numeral may appear only as a secondary label.

## Period coverage

The brief's period list also includes the Greco-Italian War of 1940-1941 (Women of Pindus). These settings replace the brief's, so that 1821 and the Balkan Wars are covered. Mechanics are unchanged; all historical details are researched at GDD time, not assumed.

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
- Art is replaceable: every visible thing is drawn through a named skin entry (piece, background, button, effect) with a simple code-drawn default, so free or open-licensed art can be dropped in later without touching game logic. Gameplay shapes and sizes do not depend on the art.

## Design sheet

Every game starts as a one-page sheet at `games/<game>/design.md` with exactly these rows. The owner marks each row keep, change or cut; nothing is built that is not on an approved sheet. The prototype exists only to answer the last row. Anything not taken from the brief is marked "new".

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

Sources: MDA (mechanics, dynamics, aesthetics) for the middle rows, nested loops for the loop rows, self-determination theory for competence, autonomy and relatedness.

## Game folders

Each game we work on has its own folder `games/<game>/` holding everything a new chat needs for it: `design.md` (the approved sheet), `BUILD.md` (exact instructions for the current step, written so a cheaper model can follow them without other reading), `src/`, `lib/`, and the built single HTML file. A chat working on a game reads that folder's `BUILD.md` first and nothing outside the folder unless `BUILD.md` says so.

## Process

These override the brief where they differ.

- Per game: design sheet (above), then a rough prototype of the core mechanic, tested with the child, then the full GDD at `games/<game>/gdd.md` covering the list in brief lines 1367-1385, then the full build.
- Build one game to a genuinely playable standard before starting others. Shared code is extracted from finished games, not built in advance.
- First game: Tower Builder.
- Priority after it: Waterworks, Mechanical Workshop, Siege Engineer, Cargo Train Routing and Robot Programming move up; the trade and conquest games (Donkey Caravan Trader, Merchant Shipping, Castle Conquest, Island Conquest) move down.
- Games that need on-screen run and jump buttons (Women of Pindus, Adventure Platformer, Beat-'em-up, Little Fighters) get a control prototype before any commitment.
- Tiers C and D are a backlog, not a commitment. Nothing is discarded.

## Status

- Tower Builder (renamed 17 Nov: Αρχιτέκτονες του αρχαίου κόσμου, folder `games/arxitektones-tou-arxaiou-kosmou`): free play, picture world map with ten boats on fixed ports and traveller groups, ten levels generated from their suggested builds (`tools/make-levels.py`), each with a wrong choice that fails, owner sounds and music, breaking, limited sidebar pile, arches on wooden supports the player removes, pediment pieces, and a test (wind both ways, load lowered with drumroll, earthquake; anything breaking fails it). Quick build and 10x test behind Ctrl. Handoff: `games/arxitektones-tou-arxaiou-kosmou/BUILD.md`, sections "Current state", "Current state, update 2", "Current state, update 3" and "Task list". Triangle piece; Lion Gate, Parthenon and Valens rebuilt. Hand rebuilt as a soft joint at the grab point (updates 5-8); sidebar 1.5x, fixed; ground solid and 24 px. Next: owner play-test. Levels: `games/arxitektones-tou-arxaiou-kosmou/levels.md` is the level spec and the process (approve, lock headpieces, tests, pictures); no level work outside it. All ten rebuilt to it and passing its tests (12 Nov); picture `games/arxitektones-tou-arxaiou-kosmou/levels.png`. Fifth list (12 Nov): done; the Valens pile not fitting the sidebar is not an issue (owner, 13 Nov). Sixth list (12 Nov): all 17 done (BUILD.md "Current state, update 10"): outline = building shape, button at 85%, hand by carried weight, same test result every time, finished sites go red when their headpiece is out, restart button, level changes; owner tests in `tools/owner-tests.js`. Seventh and eighth lists (12 Nov): built (BUILD.md "Current state, update 11"); Ninth to eleventh lists (13 Nov): done (BUILD.md "Current state, update 12" and "update 13"); owner's test list `games/arxitektones-tou-arxaiou-kosmou/checklist.md`. Parent key is Ctrl (was Tab). Map visuals lists (13 Nov): done (BUILD.md "Current state, update 15" to "update 17"). Fair weight sharing, all-mudbrick ziggurat with a plank, Djoser lighter top step, 20% safety test (14 Nov): BUILD.md "Current state, update 20". Sandbox shapes per material, passed level stays (14 Nov): "update 21" to "update 24"; undo button top left; stacks lift without the top jumping; hand rebuilt as one real model (BUILD.md "update 26"); the hand with a brain (BUILD.md "update 28"); voice and teaching plan in `games/arxitektones-tou-arxaiou-kosmou/cues.md`, Valens one form (BUILD.md "update 29"); the arm holds the weight, pieces circle and stop with the finger (BUILD.md "update 30"); one force budget, grip by felt pull, inertia back (BUILD.md "update 31"); steady arm and a real wrist (BUILD.md "update 32"); throwing, material differences (BUILD.md "update 33"); owner hand list as tests, hand rebuilt to it (BUILD.md "update 35"); whirling works, no tilt when dragged (BUILD.md "update 36"); same effort for every piece, whirling with a real mouse (BUILD.md "update 37"); back to the update-36 hand at the owner's choice, open points listed (BUILD.md "update 38"); cues built with text boxes (BUILD.md "update 39"), cue model rebuilt: 2 s boxes, scenes (BUILD.md "update 40"); attention (darkening, outline highlights, a real hand, 5 s repeats), buttons act on release, demos every visit until finished (BUILD.md "update 41"); Ur five rows of whole mudbricks, long planks stand in the pile (BUILD.md "update 42"); cues as a table (`cues.json`, version A) with `cues.md` written from it (version B), owner cue list of 14 Nov late (BUILD.md "update 43"); Ur temple load and earthquake 10% weaker (BUILD.md "update 44"); Ur top rows 3 and 2 blocks, passes its test (BUILD.md "update 45"); owner cue and level list of 15 Nov, all 22 points with pass/fail cue tests (`tools/harness.py cuetest`, BUILD.md "update 46"); owner list of 15 Nov evening: flavour on the map only, Pharos wood places, Mausoleum demo, demos never pass through pieces, the drag-back loop (BUILD.md "update 47"); openings line at the first site with openings only, undo-button line after ten pieces, voice hook audit test (BUILD.md "update 48"); no first-site demo, shovel after four pieces (BUILD.md "update 49"); friction 20% higher, a row of pieces pushed as one load (BUILD.md "update 50"); dotted-outline lines, test explanations at first reach, input on the game clock (BUILD.md "update 51"); shovel at three pieces, red button at eight, lines dropped only while a teaching line plays or a step waits, Lion Gate upper row in and smaller lion triangle (BUILD.md "update 52"); day sky per site and night skies for finished sites, Mausoleum demos left then right lintel and a post under both (BUILD.md "update 53"); settings gear with ΒΟΗΘΗΤΙΚΑ ΒΙΝΤΕΟ (no demos when unticked), sandbox icon, cues.md explanation first (BUILD.md "update 54"); ΔΙΔΑΣΚΑΛΙΑ tick for the teaching (BUILD.md "update 55"); intro pictures full screen with a slow zoom towards the owner's marked point during the welcome line (BUILD.md "update 56"); owner list of 16 Nov night: ESC, free play as a pile, kept first-time lines, Karnak wooden columns, wooden Parthenon option, skies (BUILD.md "update 57"); lever, map taps, sound loudness and weight, sidebar speed by weight (BUILD.md "update 58" to "update 60"); waves push boats, load screen, rename (BUILD.md "update 61"); one smooth wave push (BUILD.md "update 62"); dunes are sand for map taps (BUILD.md "update 63"); mountains drawn by hand for map taps, `tools/make-ground.py` (BUILD.md "update 64"); wave push never double (BUILD.md "update 65"); gentler wave push, then doubled (BUILD.md "update 66", "update 67"); map boats drawn in 3D (BUILD.md "update 68"); boats turn smoothly on rounded routes, curved sail (BUILD.md "update 69"); writing in the sand of Africa and Arabia wiped by a local wind, boats dragged and carried over land (BUILD.md "update 70"); one boat per finished site, empty boats wait, held boats over a shadow (BUILD.md "update 71"); boat lift and drop, left-on-land sound, smoother sand (BUILD.md "update 72"); no map hitches, map tests in seconds (BUILD.md "update 73"); waves push moved boats (BUILD.md "update 74"); a dropped boat not pushed by its own splash, waves even (update 75), voice recordings and voice-lines.md (update 76), map buttons top right (BUILD.md "update 77"); voice normalised, heard from the first touch, intro ducking (BUILD.md "update 78"); flow tests, the test runs with the teaching off (BUILD.md "update 79"); child action wins in cues, teaching only the tutorial, test result sooner (BUILD.md "update 80"); red drawn exactly with straight edges, teaching = the cues that show the game's things, test music fade, map rings stop at land, stones from the mountains (BUILD.md "update 81"); headpiece in the hand at finished sites, one 15% wrong-area rule, alert rhythm every 10 s per site, voice once per site per session, thrown stones (BUILD.md "update 82"); three voice clips, one look for every map alert, headpiece sounds as stone (BUILD.md "update 83"; open: Halicarnassus wood, middle grab vs the lever); stones stop sooner, audible earthquake, continuous wave rings (BUILD.md "update 84"); stones land smoothly, Ishtar form on planks, sand-drawing sound (BUILD.md "update 85"); stones tip over like cubes and sink at once, demos take supports out from the top (BUILD.md "update 86"); silent tipping, full-speed throws (BUILD.md "update 87"; open: the stones flow miscounts tips); latest handoff is BUILD.md "update 87"; Mausoleum demo stays right lintel first (owner 15 Nov: "mausoleum ok, forget it").

## Decided

- File layout: one self-contained HTML file per game (opens by double-click) plus a library page linking to them. Shared code lives once in the repo and a build script copies it into each game file. Sounds play through audio elements or are embedded. Test saved progress on the target PC early.
- Tower Builder campaign: owner decision, an exception to the one-period rule: ancient Mediterranean and Middle East up to late Roman Constantinople, ten famous buildings in chronological order (list in its design.md).
- Physics: an existing library embedded in the game file. Planck.js 1.4.2 (MIT), fallback Matter.js only if stacking proves unstable in play. Bridge Builder decided later.
