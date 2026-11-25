# Οι Άποικοι (Oi Apoikoi, "The Settlers")

A two-player tile-drafting game built on the loop of the board game Dragomino: each player builds his own land from two-half terrain tiles; each connection gives a jar and lights up the connected land for materials; jars hold gold coins and bonuses. A rough prototype with colours only; the full design is in `design.md`.

## How to play

- Open `oi-apoikoi.html` in a browser (one self-contained file). You are green (left area), the PC is red (right area); you share one board.
- Top: the pile (a layer per tile) and the market, where 4 tiles are dealt one by one each round. Tap a tile to pick it. Tiles you can't place are lightly greyed; if none fits you, your turn passes (a sound) and the PC plays again.
- The tile you win stays where it is: tap it to turn it, drag it and leave it anywhere, as often as you like. It is placed when you leave it near a place it fits (the place is shown first): two free squares with a matching edge with your own land. Left on its own market place it goes back, and you pick again.
- Each connection (a matching edge, with any land) glows and drops a jar from the top; it also lights the connected land of its colour, yours and the PC's, and each lit square sends one material to your area. 5 of a colour become a jar at once. Materials stay from round to round.
- Jars stand in lines of up to 6. Tap them as fast as you like: each breaks and its prize pops up above it, then flies to its place: coins, the first-player star, another jar, one of each material, a random tile (placed from beside the market) or the slot machine. Slot machine: tap a wheel to keep it (a clamp), pull the lever at the side to pay a coin and spin the others, tap the tray under the wheels to take the prize; only three of a kind wins.
- Each area: materials (a row of 5 places per colour; a full row flies into a jar), coins in the same columns underneath; the star is the first-player token. A hand does every PC move: it points to tap, grabs to carry a tile, opens to let go, and is raised when the PC passes.
- The game ends when no tile left can be placed by either player. Each player's coins fly into his pile over the board; the star marks the taller pile. The green play button starts again.

## Where things are

- `design.md`: the full design (draft): rules, jars, slot machine, points, rejected ideas, tensions, sheet rows, everything open.
- `WARNINGS.md`: traps found in this game.
- `src/index.html`: the game source; `build.py` makes `oi-apoikoi.html` from it, with the hand pictures put in.
- `src/hands/`: the hand pictures (Microsoft Fluent Emoji, MIT license in `src/hands/LICENSE`).
- `tools/flows.py`: flow tests, one per owner rule and bug report, a main test playing a whole fixed game, plus random play through the screen; `tools/harness.py` builds and runs them (the whole set in two browsers side by side, about 18 s on a 2-core machine).
- `tools/sim.py`: the simulation: plays seeded games through the screen and reports, per player, jars, coins and what the jars held (`python3 tools/sim.py [games] [random|best]`, the kid playing at random or for the most connections). Run it before every rule change and tell the owner the numbers.
- `tools/ci-checks.txt`: the list of every check of the game, run on GitHub when a push or pull request changes this game or something shared.
- `tools/backdoors.txt`: what a flow may never contain (moves through the game's insides); the commit check refuses it.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL. Before a rule change: `python3 tools/sim.py` (see above).

## Now

A playable game against the PC on one shared board, colours only: 6 colours and 28 tiles; each connection gives a jar and lights its connected land (both players') for one material a square; 5 of a colour make a jar; jars hold coins, the first-player star, another jar, one of each material, a random tile or the slot machine (the same 4 faces on every wheel, only three of a kind wins). The board is as big as the height allows and the areas take the rest; a tile is the same size everywhere. Jars stand in centred lines of 6, break as fast as he taps and show their prize as a picture above them. The end is a box over the board with each player's coin pile. Rules and built-for-now choices are in `design.md`.

## Open

- The jar mix is given "per 95" but its numbers add up to 90; the game draws by the numbers (40 one-coin jars are 44% of jars). Ask the owner which he meant.
- The star (first-player token): the owner saw it make him play next in the same round; the code only uses it at the next round's start. Unknown whether he saw a skipped turn: ask him.
- The full test run is about 17-19 s of the 20 s limit on a 2-core machine; keep flows sampling with skip, not run_for.
- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` sections 6 and 7.

## Task list

1. The PC plays the rules at its best.
