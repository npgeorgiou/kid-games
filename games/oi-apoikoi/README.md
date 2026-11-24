# Οι Άποικοι (Oi Apoikoi, "The Settlers")

A two-player tile-drafting game built on the loop of the board game Dragomino: each player builds his own land from two-half terrain tiles, bids sets of goods for tiles, and opens jars for gold coins and bonuses. A rough prototype with colours only; the full design is in `design.md`.

## How to play

- Open `oi-apoikoi.html` in a browser (one self-contained file). You are green (left panel), the PC is red (right panel); you share one board.
- Top: the 4 tiles of this round; the bars are the rounds left. Tap a tile to pick it. Tiles you can't place are greyed; if none fits you, your turn passes and the PC plays again.
- If the other player wants your tile, a panel shows the sets needed (a set is one of each of the 5 goods): green takes it (a tie is the picker's), red lets it go.
- The tile you win stays where it is: tap it to turn it, drag it and leave it anywhere, as often as you like. It is placed when you leave it near a place it fits (the place is shown first): two free squares with a matching edge with your own land. Left on its own market place it goes back, and you pick again; a tile won with a bid stays reserved for you.
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

A playable prototype against the PC on one shared board, colours only. Tiles are dragged straight from the pile and stay where they are left until they snap; a won bid locks a tile for its winner; a placed tile adds its 2 goods at once, and every land makes goods again at each round's start. Each player's area has his face, a goods tray (a groove per colour, set bands, jar frames) and a coins tray; the player whose turn it is has his area lit, the other's is dimmed. The pile is a stack of face-down tiles beside the market tray. When a tile snaps its matched edges glow and each jar flies out of its edge. The round's end is its own moment (a sunset); then one player turns his goods into jars one group at a time and opens them, then the other. The slot machine has no text; its wheels roll fast, slow down and stop one by one. Sounds are one soft built-in family (wood, clay, coins, chimes). The PC plays with a visible pointing hand. Rules and built-for-now choices are in `design.md`; the screen follows `tools/ui-design/README.md`.

## Open

- Main is protected: work goes on a branch with a pull request, merged by Claude once its tests pass.
- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` sections 6 and 7.

## Task list

- Main test: one flow plays a whole game with a fixed pile and fixed jar contents, so every situation happens in order; small flows stay only for versions of one thing; the rest merge into it.
- Screen pass with `tools/ui-design/README.md` (new motion rules): whose turn is obvious, the turn and the first-player star fly; the bid panel never hides the boards; round start: each land lights and its good flies to the stockpile, one by one, with sound; round end: jars drop from the top to the centre, goods fly into them on arcs; leftovers dissolve; jars break and the bonus comes out of them; jars step aside to a free place during a bonus tile and come back; a jar outline (not an oval) around each 5 of a colour; a set sign beside each set; a better round's end than the sunset.
- Jars: 6 to a row, more rows, never smaller. Coins: any number fits.
- Slot machine: pictures that mean something (no letters, no unclear marks); a right spin-again picture. Waiting for the owner: which new gifts, and 3, 4 or 5 pictures per wheel (2 the same win 2, 3 win 3).
- Waiting for the owner: should a tile need more to fit (after round 2 almost every tile fits)?
