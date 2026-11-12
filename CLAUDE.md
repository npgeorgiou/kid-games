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

## Rules for every change (owner, 13 Nov 2026)

1. Before building a level, list every place in the building and what the child could put there from the pile. Each place that matters gets a tempting wrong piece that fails in the test.
2. Every rule the owner gives (strength, weight, size, outline) gets a test made of the cases he named. For a rule about a material, add one case for each way a piece can be used: lying flat, standing up, across a gap, falling.
3. After any physics change, rerun every earlier rule's test, not just the new one: mudbrick stacks, lifting, carrying, pushing, falls, repeated runs, all screen sizes, every level's suggested build and wrong choices.
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
- The owner supplies voice and sound files; code provides hooks for them.

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

- Tower Builder: free play, picture world map with ten boats on fixed ports and traveller groups, ten levels generated from their suggested builds (`tools/make-levels.py`), each with a wrong choice that fails, owner sounds and music, breaking, limited sidebar pile, arches on wooden supports the player removes, pediment pieces, and a test (wind both ways, load lowered with drumroll, earthquake; anything breaking fails it). Quick build and 10x test behind Tab. Handoff: `games/tower-builder/BUILD.md`, sections "Current state", "Current state, update 2", "Current state, update 3" and "Task list". Triangle piece; Lion Gate, Parthenon and Valens rebuilt. Hand rebuilt as a soft joint at the grab point (updates 5-8); sidebar 1.5x, fixed; ground solid and 24 px. Next: owner play-test. Levels: `games/tower-builder/levels.md` is the level spec and the process (approve, lock headpieces, tests, pictures); no level work outside it. All ten rebuilt to it and passing its tests (12 Nov); picture `games/tower-builder/levels.png`. Fifth list (12 Nov): done except the Valens pile, which does not fit the sidebar (owner to decide). Sixth list (12 Nov): all 17 done (BUILD.md "Current state, update 10"): outline = building shape, button at 85%, hand by carried weight, same test result every time, finished sites go red when their headpiece is out, restart button, level changes; owner tests in `tools/owner-tests.js`. Seventh and eighth lists (12 Nov): built (BUILD.md "Current state, update 11"); Ninth list (13 Nov): done (BUILD.md "Current state, update 12"); open: Valens pile, Mausoleum posts not needed, Djoser play-test.

## Decided

- File layout: one self-contained HTML file per game (opens by double-click) plus a library page linking to them. Shared code lives once in the repo and a build script copies it into each game file. Sounds play through audio elements or are embedded. Test saved progress on the target PC early.
- Tower Builder campaign: owner decision, an exception to the one-period rule: ancient Mediterranean and Middle East up to late Roman Constantinople, ten famous buildings in chronological order (list in its design.md).
- Physics: an existing library embedded in the game file. Planck.js 1.4.2 (MIT), fallback Matter.js only if stacking proves unstable in play. Bridge Builder decided later.
