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
- `tools/flows.py`: flow tests, one per owner rule and bug report, a main test playing a whole fixed game, plus random play through the screen; `tools/harness.py` builds and runs them (the whole set in two browsers side by side, about 18 s on a 2-core machine).
- `tools/ci-checks.txt`: the list of every check of the game, run on GitHub on every push.
- `tools/backdoors.txt`: what a flow may never contain (moves through the game's insides); the commit check refuses it.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL.

## Now

A playable prototype against the PC on one shared board, colours only. The screen follows `tools/ui-design/README.md`: the market on top (the pile on its left, a bonus tile on its right), the bid card right under the tile it is about, the board below with a free strip along the bottom edge, and each player's panel at a side with goods big enough to count (a column per colour, each 5 outlined as the jar it will become, set rows marked) and coins in rows of 5. Tiles feel like objects: a carried tile tilts with the drag, a placed tile bounces as it lands, a tap on the board puffs dust with a knock. Each round starts with morning light and every square giving its good (all within about a second), and ends with evening (moon and big stars), goods flying into jars and leftovers breaking into specks. Jars break where tapped and their reward flies to its place; the slot machine has 4 random faces per wheel. Whose turn it is: a light flies between the faces, the player playing has a bigger glowing face, the market takes his colour. A main test plays a whole game from a set pile in which every situation happens. Rules and built-for-now choices are in `design.md`.

## Open

- Main is protected: work goes on a branch with a pull request, merged by Claude once its tests pass.
- The full test run is about 18-20 s of the 20 s limit on a 2-core machine; the cost is the browser's processor time per action. Keep flows sampling with skip, not run_for.
- Coins (measured 24 Nov, 30 seeded games, the kid taking the first fitting tile and the best place): kid 109, PC 137 coins a game; of the kid's, 106 come from jars and 4 from the slot machine; about 177 jars are opened per game, most from goods at the round's end. Waiting for the owner's choice.
- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` sections 6 and 7.

## Task list

In this order, each one tested and merged before the next (the rules are in `design.md`, 24 Nov):
1. Rules: no bidding; a placed tile gives one good per matching edge (the edge glows, its good flies out), nothing for its halves; 5 of a colour become a jar at once, opened at once; goods carry over between rounds.
2. Stockpile: one row of 5 places per colour; no tall jar outlines.
3. Sets: one of each colour lights up; at the start of his turn, tap it for a wild tile (rules in `design.md`); the jar's free tile becomes the same wild tile.
4. Remove the turn sign flying from face to face.
5. Slot machine (said twice): each wheel a shaded drum showing only the face it lands on, wheels apart; tap a wheel to keep it (a clamp), pull a lever to pay a coin and spin the others, tap the tray under the wheels to take the prizes; no circular arrow.
6. Whole screen (owner: "MANY issues"): grey sketches of every moment for the owner's yes first, then build, then screenshots in grey and the full checklist.
7. The PC plays the new rules at its best, sets included.
8. Measure jars and coins per game and tell the owner.
