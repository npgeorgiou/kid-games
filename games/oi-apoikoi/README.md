# Οι Άποικοι (Oi Apoikoi, "The Settlers")

A two-player tile-drafting game built on the loop of the board game Dragomino: each player builds his own land from two-half terrain tiles, earns goods from matching edges, and opens jars for gold coins and bonuses. A rough prototype with colours only; the full design is in `design.md`.

## How to play

- Open `oi-apoikoi.html` in a browser (one self-contained file). You are green (left panel), the PC is red (right panel); you share one board.
- Top: the 4 tiles of this round; the bars are the rounds left. Tap a tile to pick it. Tiles you can't place are greyed; if none fits you, your turn passes and the PC plays again.
- The tile you win stays where it is: tap it to turn it, drag it and leave it anywhere, as often as you like. It is placed when you leave it near a place it fits (the place is shown first): two free squares with a matching edge with your own land. Left on its own market place it goes back, and you pick again.
- Every matching edge, with any land, gives one good of its colour (it flies out of the edge); 5 of a colour become a jar at once; tap the big jars to open them. Goods stay from round to round.
- A set (one of each colour) lights up at the start of your turn: tap it and its goods fly into a wild tile beside the market; it takes the colours of its neighbours wherever you put it (shown while you carry it). Then pick as usual. A jar's free tile is the same wild tile. Slot machine: each wheel is a drum showing one face; tap a wheel to keep it (a clamp), pull the lever at the side to pay a coin and spin the others, tap the tray under the wheels to take the prizes.
- Each panel: goods (a row of 5 places per colour; a full row flies into a jar), sets (a column with one of each), gold coins; the star is the first-player token. A hand does every PC move: it points to tap, grabs to carry a tile, opens to let go, and is raised when the PC passes.
- The game ends when no tile left can be placed by either player. The two rows of coins are shown; the star marks the winner. The round arrow starts again.

## Where things are

- `design.md`: the full design (draft): rules, jars, slot machine, points, rejected ideas, tensions, sheet rows, everything open.
- `WARNINGS.md`: traps found in this game.
- `src/index.html`: the game source; `build.py` makes `oi-apoikoi.html` from it, with the hand pictures put in.
- `src/hands/`: the hand pictures (Microsoft Fluent Emoji, MIT license in `src/hands/LICENSE`).
- `tools/flows.py`: flow tests, one per owner rule and bug report, a main test playing a whole fixed game, plus random play through the screen; `tools/harness.py` builds and runs them (the whole set in two browsers side by side, about 18 s on a 2-core machine).
- `tools/ci-checks.txt`: the list of every check of the game, run on GitHub when a push or pull request changes this game or something shared.
- `tools/backdoors.txt`: what a flow may never contain (moves through the game's insides); the commit check refuses it.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL.

## Now

A playable prototype against the PC on one shared board, colours only. The screen follows `tools/ui-design/README.md`: the market on top (the pile on its left, a bonus tile on its right), the board below with a free strip along the bottom edge, and each player's panel at a side with goods big enough to count (a row of 5 places per colour, sets marked as columns) and coins in rows of 5. Tiles feel like objects: a carried tile tilts with the drag, a placed tile bounces as it lands, a tap on the board puffs dust with a knock. A pick takes the tile; each matching edge of a placed tile glows and sends out one good; 5 of a colour fly into a jar at once, opened at once; goods carry over; a set buys a wild tile that takes its neighbours' colours (also the jar's free tile). Each round starts with morning light and ends with evening (moon and big stars). Jars break where tapped and their reward flies to its place; the slot machine has 4 random faces per wheel, shown on shaded drums, with clamps, a lever and a prize tray. Whose turn it is: his area is lit and the other dimmed, the player playing has a bigger glowing face, the market takes his colour. A main test plays a whole game from a set pile in which every situation happens. Rules and built-for-now choices are in `design.md`.

## Open

- The owner reshaped the game by playing a prototype built without tests (24-25 Nov). It is the project doc `claude/oi-apoikoi-prototype-25nov.html` (claude.ai project "kid games"), not in the repo; task 1 builds it in.
- The star (first-player token): the owner saw it make him play next in the same round; the code only uses it at the next round's start. Unknown whether he saw a skipped turn: ask him.
- The full test run is about 16-17 s of the 20 s limit on a 2-core machine; keep flows sampling with skip, not run_for.
- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` sections 6 and 7.

## Task list

1. Build the prototype in, test first (every point a failing step first), and write the rules into `design.md`:
   - 6 colours (6th teal), 28 tiles (halves 10, 10, 9, 9, 9, 9); board 20 x 13 as now.
   - Each connection gives a jar, dropping from the top of the screen; it also lights the connected land of that colour (both players'), spreading out from it; each lit square gives one material; 5 of a colour make a jar at once.
   - No wild tiles, no sets to tap, no stealing.
   - Jar contents per 95: empty 10, 1 coin 40, 2 coins 10, random tile 2.5 (no colours shown until it lies beside the market), slot machine 5, first player 7.5, another jar 7.5, one of each material 7.5.
   - Slot machine: each wheel has 2 coins, 2 jars, 2 of each material, blank (an X); only three of a kind wins, what you see; a spin costs 1 coin (option 1, 3 faces of 1 each, noted in a comment); rolling wheels stop at 1.8, 2.6, 3.5 s by their order among the rolling ones; the tray shows the prize only after they stop.
   - Board as big as the height allows, player areas take the rest of the width; a tile the same size everywhere; tiles he can't take: a light grey wash, colours clear.
   - Coins in the 5 material columns, in a tray under the materials, rows of 5 from the top.
   - Materials: each colour its own line; a full row's jar drops while its 5th flies; lit squares 120 ms apart.
   - Jars: lines of up to 6 centred on their jars; a new one takes the first free place, the others slide; a broken one leaves its place; no glow; always drawn while waiting.
   - Jars break at once, as fast as he taps; the prize (a picture, no words) pops up above its jar, stays a moment, then flies to its place; only the slot machine and a tile to place wait.
   - A skipped turn: only its sound. An X for an empty jar.
   - The pile holds every tile; the 4 market tiles are dealt one by one.
   - End: a smaller box over the board; coins fly into two piles of the same coin size (rows of 10); a star over the taller; a green play button that works.
2. A simulation tool in `tools/` that plays seeded games through the screen and reports jars, coins and bonus shares per player; run it before every rule change and tell the owner the numbers (the prototype: about 96 jars a game, kid about 30 coins, PC about 34).
3. The PC plays the rules at its best.
