# Οι Άποικοι (Oi Apoikoi, "The Settlers")

A two-player tile-drafting game built on the loop of the board game Dragomino: each player builds his own land from two-half terrain tiles, bids sets of goods for tiles, and opens jars for gold coins and bonuses. A rough prototype with colours only; the full design is in `design.md`.

## How to play

- Open `oi-apoikoi.html` in a browser (one self-contained file). You are green (left panel), the PC is red (right panel); you share one board.
- Top: the 4 tiles of this round; the bars are the rounds left. Tap a tile to pick it. Tiles you can't place are greyed; if none fits you, your turn passes and the PC plays again.
- If the other player wants your tile, a panel shows the sets needed (a set is one of each of the 5 goods): green takes it (a tie is the picker's), red lets it go.
- The tile you win stays where it is: tap it to turn it, drag it and leave it anywhere, as often as you like. It is placed when you leave it near a place it fits (the place is shown first): two free squares with a matching edge with your own land.
- Every matching edge, with any land, earns a jar; tap the big jars to open them. Slot machine: tap wheels to choose, the green button pays a coin and spins them again, the yellow button takes what you have.
- Each panel: goods (a row per colour), sets, gold coins; the star is the first-player token. A hand does every PC move: it points to tap, grabs to carry a tile, opens to let go, and is raised when the PC passes.
- The game ends when no tile left can be placed by either player. The two rows of coins are shown; the star marks the winner. The round arrow starts again.

## Where things are

- `design.md`: the full design (draft): rules, jars, slot machine, points, rejected ideas, tensions, sheet rows, everything open.
- `WARNINGS.md`: traps found in this game.
- `src/index.html`: the game source; `build.py` makes `oi-apoikoi.html` from it, with the hand pictures put in.
- `src/hands/`: the hand pictures (Microsoft Fluent Emoji, MIT license in `src/hands/LICENSE`).
- `tools/flows.py`: flow tests, one per owner rule and bug report, plus random play through the screen; `tools/harness.py` builds and runs them (the whole set in two browsers side by side, about 7 s).
- `tools/backdoors.txt`: what a flow may never contain (moves through the game's insides); the commit check refuses it.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL.

## Now

A playable prototype against the PC on one shared board, colours only. Tiles are dragged straight from the pile and stay where they are left until they snap; a won bid locks a tile for its winner; a placed tile adds its 2 goods at once, and every land makes goods again at each round's start; the stockpile stands in colour columns with set bands and jar frames; at the round's end each 3 of a colour fly into a jar one group at a time and the leftovers fade out; jars have labels; the slot machine rolls and shows price and prize; simple built-in sounds for each thing that happens; the PC plays with a visible hand (points, grabs with a fist). Rules and built-for-now choices are in `design.md`.

## Open

- Main is protected: changes go on a branch with a pull request for the owner to merge.
- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` sections 6 and 7.

## Task list

- Rethink the whole screen by `tools/ui-design/README.md`; the player panels must show clearly what each player has; nothing unexplained on screen (the 9 lines at the top).
- Whose turn it is must be obvious; the PC's turn must look different from yours.
- No text anywhere except the jar bonus labels; none on the slot machine.
- Everything separate and distinct (jars must not touch).
- A matched edge is shown, and each jar it earns comes out of that edge; a snap sound.
- Tapping a tile makes a weird blip: a pleasant sound instead.
- A picked tile can be put back: dropped on the pile it returns to its place, and another can be picked.
- Opening a jar plays a breaking sound.
- The PC's hand uses the pointing hand for grabbing too.
- The round's end is its own phase, clearly seen and heard.
- Round end: one player turns his goods into jars and opens them, then the other.
- Slot machine: wheels roll fast, then slow down and stop one after another, with sounds.
- A general refactor (one owner per behaviour), tests passing throughout.
