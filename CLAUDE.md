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
- If a message asks a question, answer it and wait before coding.
- Never invent rules, stats or mechanics. Unknown or unverified details are stated as unknown. Research historical details; do not guess them.
- Change only what was asked. Fix bugs generically, not just the example mentioned.
- Answers: short plain prose, no recap, no offers, no command output. English only.
- After every change: push, and give only the changed HTML files as downloads.
- When a chat gets long, say so and give a short handoff.

## Product rules

- All player-facing text in natural, correct Modern Greek. Design docs and code comments in English.
- Never require reading or spoken instructions: short labels, clear icons, visual demonstration. Not babyish.
- Touch first: Pointer Events, large targets, no hover, no tiny controls, no required keyboard.
- One coherent Greek period and region per game or campaign; do not mix eras.
- Conflict is abstract and non-graphic. No frightening imagery, ads, monetization, streaks or punitive timers.
- Failure is informative, retry is immediate, unrelated progress is never erased.
- Introduce one new rule at a time; difficulty comes from combining known rules, not from unfair controls.
- The owner supplies voice and sound files; code provides hooks for them.

## Tech

- HTML, CSS, JavaScript. Canvas for game scenes, physics, animation; DOM for menus and UI.
- LocalStorage or IndexedDB for progress and settings; Web Audio API; fullscreen support.
- No backend. Runs locally on the PC.
- Each game independently playable and testable, launched from one library page.

## Process

- Design before code: a full GDD per game at `docs/gdd/<game>.md`, covering the list in brief lines 1367-1385, before any implementation.
- Build one game to a genuinely playable standard before starting others; fold lessons into the shared code.
- First batch, in order of the brief: Tower Builder, Donkey Caravan Trader, Castle Conquest, Women of Pindus, Little Fighters, Factory Automation.
- Lower-ranked catalogue entries are not discarded.

## Status

- Repo initialised with this file and the brief. No GDD, no code yet.
- Open decisions: which game first; file layout (see below).

## Open: file layout

The brief asks for ES modules, but browsers block ES module imports on pages opened directly from disk (`file://`). Options: one self-contained HTML file per game (opens by double-click), or ES modules served by a small local web server. Not decided.
