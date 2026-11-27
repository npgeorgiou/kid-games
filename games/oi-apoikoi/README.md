# Οι Άποικοι (Oi Apoikoi, "The Settlers")

A two-player tile-drafting game built on the loop of the board game Dragomino: each player builds his own land from two-half terrain tiles; each connection gives a jar and lights up the connected land for materials; jars hold gold coins and bonuses. Drawn in the new look: a sea board in isometric view, land pictures where tiles lie, material pictures; the full design is in `design.md`.

## How to play

- Open `oi-apoikoi.html` in a browser (one self-contained file). You are green (left area), the PC is red (right area); you share one board: a square of sea, 16 x 16 squares, seen in isometric view; land is only where tiles lie.
- Top, in a band: the pile (a layer per tile) and the market, where 4 tiles are dealt one by one each round. Tap a tile to pick it. Tiles you can't place are lightly greyed; if none fits you, your turn passes (a sound) and the PC plays again.
- The tile you win stays where it is: tap it to turn it, drag it and leave it anywhere, as often as you like. It is placed when you leave it near a place it fits (the place is shown first): two free squares with a matching edge with your own land. Left on its own market place it goes back, and you pick again.
- Each connection (a matching edge, with any land) glows and drops a jar from the top; it also lights the connected land of its colour, yours and the PC's, and each lit square sends one material to your area. 5 of a colour become a jar at once. Materials stay from round to round.
- Jars stand in lines of up to 5; when the lines would reach below the screen they move up, then overlap a little. Tap them as fast as you like: each breaks and its prize pops up above it, then flies to its place: coins, the first-player star, another jar, one of each material, a random tile (shown in the jar, placed from beside the market) or the slot machine. Slot machine: tap a wheel to keep it (a clamp), pull the lever at the side to pay a coin and spin the others, tap the tray under the wheels to take the prize; only three of a kind wins.
- Each area is the two triangles beside the board on your side; their thin ends at the screen's middle are grey and empty (for later UI); materials in a row of 5 places per land, from the top, beside the screen edge (a full row flies into a jar), your face beside them; coins in 8 stacks of 10 along the bottom, from the materials to the board's bottom corner, one stack filled at a time; the star is the first-player token. The 6 lands and their materials: wheat field (grain), pomegranate orchard (pomegranates), vineyard (grapes), forest (timber), mountain (rubies), town (little statues). A hand does every PC move: it points to tap, grabs to carry a tile, opens to let go, and is raised when the PC passes.
- The game ends when no tile left can be placed by either player. Each player's coins fly into his pile over the board; the star marks the taller pile. The green play button starts again.

## Where things are

- `design.md`: the full design (draft): rules, jars, slot machine, points, tensions, sheet rows, everything open.
- `WARNINGS.md`: traps found in this game.
- `areas-sketch.png`: the areas sketch (each player's side split into areas, the board's border), to build from.
- `SOUNDS.md`: every sound's name and when it plays; the owner's own sound files go in `art/sounds/<name>.mp3` (or wav, ogg) and replace the built-in one.
- `src/index.html`: the game source; `build.py` makes `oi-apoikoi.html` from it, with the hand, land, material and sea pictures put in.
- `art/sea/`: the owner's water pack (sea and shore pictures, 6 colours); the game uses `water-c` (chosen in `build.py`), its open-water diamond only; the ripples, foam and glints moving over it are drawn by the game.
- `art/lands/`: the 6 land pictures, each as its ground (`-ground`, one square's diamond and its two front walls of earth) and the things standing on it (`-things`); made by `tools/make_lands.py` (run it after changing it).
- `art/materials/`: the 6 material pictures, made for the game.
- `art/things/stone-slab-1.png`, `stone-slab-2.png`: the owner's two stone slab pictures (free to use, he says), cut from their background (`tools/cut_pictures.py`); every area's stone top is one of them.
- `art/things/bee.svg`: the first-player bee, drawn for the game; `art/things/ruby.svg`: the ruby on the half of the stone under the pool of whoever has the most coins.
- `art/avatars/<animal>-<face>.png`: the players' stickers, 6 animals x 5 faces (neutral, happy, excited, surprised, sad), cut from the owner's two sheets by `tools/cut_stickers.py`.
- `src/hands/`: the hand pictures (Microsoft Fluent Emoji, MIT license in `src/hands/LICENSE`).
- `tools/flows.py`: flow tests, one per owner rule and bug report, a main test playing a whole fixed game, plus random play through the screen; `tools/harness.py` builds and runs them (the whole set in two browsers side by side, about 18 s on a 2-core machine).
- `tools/sim.py`: the simulation: plays seeded games through the screen and reports, per player, jars, coins and what the jars held (`python3 tools/sim.py [games] [random|best]`, the kid playing at random or for the most connections). Run it before every rule change and tell the owner the numbers.
- `tools/time-limit.txt`: the most seconds the full test run may take (owner 25 Nov: 30).
- `tools/ci-checks.txt`: the list of every check of the game, run on GitHub when a push or pull request changes this game or something shared.
- `tools/backdoors.txt`: what a flow may never contain (moves through the game's insides); the commit check refuses it.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL. Before a rule change: `python3 tools/sim.py` (see above).

## Now

A playable game against the PC on one shared board in the new look (sea board of 16 x 16 squares in isometric view, land and material pictures, market band, triangle areas): 6 lands and 28 tiles; each connection gives a jar and lights its connected land (both players') for one material a square; 5 of a colour make a jar; jars hold coins, the first-player star, another jar, one of each material, a random tile or the slot machine (the same 4 faces on every wheel, only three of a kind wins). Land squares are blocks with walls of earth, standing in moving water (ripples, foam, glints). The start tiles face each other. Faces, the hand, jars and the slot machine grow with the screen. The board is as tall as the screen under the market band allows; a tile is the same size everywhere. Jars stand in centred lines of 6, break as fast as he taps and show their prize as a picture above them. The end is a box over the board with each player's coin pile. The PC picks and places for the most jars this turn. Rules and built-for-now choices are in `design.md`. The board is 1.76 wide to 1 high at every screen size (land pictures drawn to match), as big as fits with room for a border, centred on the screen; coins are 1/8 smaller and the materials' area wider.

## Open

- The owner's own sound files, when they come, replace the built-in sounds.
- See also `design.md` section 6.
- Design phase (25-26 Nov): look, motion and layout changes are on pull request #47 (branch `oi-apoikoi-motion-fixes`), pushed with the commit check off for the owner to merge by hand; 27 flow steps fail, the same as on main, because the flow tests are not updated yet.
- Areas built from `areas-sketch.png` (deck/buttons, market, face triangle with the extra tile, dead space, materials, coins with 8 full stacks fitted, dead space); the board with its border keeps its shape and takes the most room on every screen, the areas fit around it.
- Stone look (owner close to happy, 27 Nov): rules in the project doc `claude/oi-apoikoi-stone-rules.md`; two layers of stones, bases fill the areas, tops rise, sun at the top left, pool walls straight and low, waves along the pool's edge.

## Task list

- Update the flow tests to the design phase so the commit check passes again.
