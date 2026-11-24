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

A playable prototype against the PC on one shared board, colours only. Tiles are dragged straight from the pile and snap where they fit; a picked tile can be put back on its market place; a won bid reserves a tile for its winner. Each round starts with every square lighting up in turn and its good flying to the stockpile. A placed tile adds its 2 goods at once; its matched edges glow and each jar flies out of its edge. Jars break where tapped, what they held rises out of them with a short label, and the reward flies to its place (coins to the coin stacks, the star beside the face, goods to the stockpile). Jars hold the owner's mix (10% empty). At the round's end (leftover market tiles fly back to the pile, evening falls, a moon over the market), each 5 goods of a colour become a jar: it drops from the top, the goods fly into it; jars are opened, again if opening makes new groups of 5; then the leftovers break into specks. Waiting jars step aside over the market while a bonus tile is placed. Whose turn it is: a light flies between the faces, the player playing has a bigger glowing face, the market takes his colour. The bid is a small card beside the market. Jars stand 6 to a row; coins in stacks of 10. Rules and built-for-now choices are in `design.md`; the screen follows `tools/ui-design/README.md`.

## Open

- Main is protected: work goes on a branch with a pull request, merged by Claude once its tests pass.
- The full test run is about 16 s of the 20 s limit: real-speed flows cost about half a real second per fake second (see WARNINGS.md); the main test should replace small flows where it can.
- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` sections 6 and 7.

## Task list

- Main test (owner yes): one flow plays a whole game with a fixed pile and fixed jar contents, so every situation happens in order (a tile that can't be used, a bid won and lost, a pass, a tile put back, every jar kind, the slot machine, a steal, an extra tile, more jars made while opening, the end); small flows stay only for versions of one thing; the rest merge into it.
- Slot machine: pictures that mean something (no letters, no unclear marks, a right spin-again picture; the chosen-wheel mark looks like a blue C). Waiting for the owner: which new gifts (take a good from the PC, change a good's colour, move a placed tile, lock a market tile) and 3, 4 or 5 pictures per wheel; 2 the same win 2, 3 win 3.
- Waiting for the owner: should a tile need more to fit (after round 2 almost every tile fits)?
- Waiting for the owner: coins in stacks of 10 (they overlap inside a stack) instead of every coin apart: yes or no.
- Stockpile goods and their jar outlines are small: the panel may need to be wider.
- Screen pass with `tools/ui-design/README.md`'s checklist (13 points) over the whole game, with screenshots.
