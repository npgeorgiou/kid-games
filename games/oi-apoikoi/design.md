# Οι Άποικοι: design

Status: draft, not approved. Base: the board game Dragomino (owner's choice); jars take the place of Dragomino's eggs. Everything in sections 1 and 2 is the owner's rule unless marked "Open".

## 1. The game in short (draft)

Two players each build their own land from tiles with two terrain halves, on one shared board. Each round, 4 tiles are dealt from the pile and players take them in turn. Each connection a placed tile makes (a matching edge) gives a jar, and lights up the connected land of that colour; every lit square gives one material, and 5 materials of a colour make another jar. The child opens jars by tapping them. Jars hold nothing, gold coins (the points) or bonuses: the first-player token, another jar, one of each material, a land changer, or a random tile. When no tile can be placed, the taller pile of coins wins.

## 2. Rules

### Players
- 2 players. By default you play against the PC; another human can play instead.
- the PC always does what is mathematically optimal, in every choice (pick, place, jars, extra tiles, the land changer). For now: the best expected result for this turn, not planning whole rounds ahead. To improve later.
- every PC (or second player) action is fully visible, done slowly by a moving hand, as if a person were doing it.
- whose turn it is is obvious: that player's area is lit and the other's dimmed, with a sound when the turn passes.

### Tiles and land
- each tile has two halves, and each half is one terrain.
- there are 6 terrains (the 6th teal), and each makes its own material. For now terrains are only colours, and each material has its terrain's colour; what each land is comes later (not fish: fish does not come from land).
- a land is all the connected squares of one terrain.
- every land is the same value, whatever its terrain, shape or size. No terrain, symbol or multiplier makes one land worth more than another.
- there is no size limit on a player's land.
- a tile is placed on two free squares with at least one matching edge with your own land. Matching edges with the other player's land count too (rare: only when the lands have grown toward each other).
- each player starts with the same start tile, two halves in the two most common colours.
- one shared board, 20 x 13 squares, as big as the screen's height allows; the player areas take the rest of the width. The start tiles are at the centres of its two halves. Each player's own land has a border all around its edges.
- 28 tiles; their 56 halves are 10, 10, 9, 9, 9, 9 of the six colours; tiles are random from these halves (except the start tile).
- of the first round's 4 tiles, 2 surely fit (one for each player); the other 2 are truly random.
- 4 tiles per round, 2 for each player.
- the pile holds every tile, a layer each; the 4 market tiles are dealt from it one by one.
- a tile is the same size everywhere (market, hand, board).

### A round
1. **Tiles dealt** (a draft). 4 tiles; the players take turns. A turn is: pick a tile, place it, open the jars it made; then the turn passes. Each player picks 2 tiles per round.
2. **Picking.** no bidding. The player whose turn it is takes the tile he picks.
   - tiles you can't place get a light grey wash (colours still clear) and can't be picked. With none to pick, your turn passes and the other player plays again; a skipped turn is only its sound. No tile is thrown.
   - a picked tile can be put back on its market place.
3. **Placing.** Each player places his tiles in his own land.
   - a tile is one rectangle, coloured half and half. The won tile stays where it is (in the market at first): tap it to turn it, drag it and leave it anywhere, as often as you like, until it snaps into a place; before it snaps, the place is shown.
4. **Connections and materials.** land does not make materials each round, and a tile's halves make none by themselves.
   - Each connection (a matching edge, with any land) glows and gives a jar, which drops from the top of the screen.
   - Each connection also lights the connected land of its colour, both players', spreading out from it; each lit square gives one material of that colour, flying from it to the stockpile, 120 ms apart; each colour comes in its own line.
   - 5 materials of one colour become a jar at once; the jar drops while the 5th material flies; each material is used once.
   - The stockpile is a tray in the player's area: one row of 5 places per colour.
5. **End of round.**
   - the round's end is its own moment, seen and heard, before anything else in it (leftover market tiles fly back to the pile, then a falling chime; no night; a round starts with a strong, wide morning light sweeping over).
   - materials left in the stockpile carry over to the next round.

### Jars
- the child opens jars by tapping big jars lined up on screen. Opening one yourself is the fun.
- a jar's benefit is immediate. Nothing carries to a "next" round.
- jars stand in lines of up to 6, each line centred on its jars; a new jar takes the first free place (the others slide to keep the line centred); a broken jar leaves its place empty. No glow. Jars waiting are always drawn.
- jars break at once, as fast as he taps; what a jar held pops up above it as a picture (no words; an empty jar is the bitten apple), stays a moment, then flies to its place. No prize waits for him (owner 28 Nov).
- Contents, per 100 jars (owner 28 Nov: no slot machine, its 5 to the single coin; then bee, tile and land changer 3 each, the 7 freed to the single coin): 53 one gold coin, 10 empty, 10 two coins, 10 one of each material, 8 another jar, 3 the first-player token (a coin for the player who already has the bee, owner 27 Nov), 3 a random tile (a coin when both his extra places are full), 3 the land changer (a coin when he has it).
- the random tile has random colours and always fits his land when it comes; it flies to the first empty of his two extra places (on his face stone, end to end along the pool's edge) and waits there, shining. On his turn, before he picks, he can use it for free: taken, it is in hand as a market tile; placed, its connections give jars; left on an empty extra place it goes back there (owner 28 Nov).
- the land changer (owner 28 Nov): one square in its own place on his free stone, striped with the 6 lands' ground, nothing on it; each player starts with one. Its stripes run along the board's upper edge on his side. On his turn, before he picks, a tap turns it to the next land; dragged onto a square of his own land (owner 28 Nov: a tile he placed) of another land it turns that square to its land, and each edge of that square with the same land is a connection (jars, lit land); anywhere else it goes back. A jar gives a new one (shining) only when his place is empty.
- the bee (the first-player token) shows who plays first next round: the human player starts round 1 with it; when the round's first player starts his first turn it flies to the other, so the first player alternates by round; a jar that gives it sends it to its winner (owner 27 Nov).

### Slot machine
- removed from the game (owner 28 Nov); kept, generalised, in `tools/slot-machine/` at the repo's root.

### Points and winning
- points are gold coins drawn one by one, with no numbers. They stand in the 5 material columns, in a tray under the materials, rows of 5 from the top.
- coins come from jars.
- the game ends when no tile left can be placed by either player (so also when the tiles run out). Most coins wins.
- the end is a smaller box over the board; each player's coins fly into his pile (face up, in columns of 10, the same coin size for both); the ruby (no shadow) stands over the taller pile; under the piles a green play button starts again; once the coins are counted the winner's sticker jumps up and down, excited, with a fanfare and a burst of ribbons.
- Coins past 80 stack again from the first place.
- Anything earned per tile or per round must stay a real choice over a whole game (28 tiles: at most 14 each).

## 3. The look

Where it differs from section 2 (the board's size, colours), this section wins.

- Setting: Greek colonies, about 750-550 BC (proposal, owner did not object).
- Lands and their materials: wheat field: grain; pomegranate orchard: pomegranates; vineyard: grapes; forest: timber; mountain: rubies; town: little statues.
- The board is sea: a square board of 16 x 16 squares seen in true isometric view (a diamond 1.73 times as wide as high), as tall as the screen under the market band allows. Land exists only where tiles are placed; each player starts with his own 2-square start tile, as now.
- Sea pictures: the owner's water pack (MaelleMarylloup, "water sea shore material tileset", `art/sea/`): 6 water colours, each a 4 x 4 sheet of 256 x 128 diamonds (open water and shore pieces for every edge and corner). Drawn 2 to 1, squeezed to true isometric. Its terms of use are not checked yet.
- Land pictures: flat 2D pictures in the same isometric view, in the sea pack's hand-drawn style, made for the game; things stand upright, so turning a tile changes only which squares its halves cover. Touching squares of one land join into one area.
- Market: a band across the top: the pile, then the 4 tiles.
- Player areas: the two triangles beside the board on each side, joined by a narrow strip at the board's side corner (green left, red right). The face sits in the thin top corner beside the market. Materials: a column of 5 per colour, from the top, beside the screen edge. Coins fill the bottom triangle in rows from the bottom up, each as long as the triangle is wide there, at most 8 a row.

## 4. Tensions (from the rules so far)

- Placing one half well forces the other half somewhere.
- Connecting to a big land of one colour lights more squares (more materials, so jars); connecting several edges gives more jars at once.
- Growing toward the other player's land lights his land too, for you.

## 5. Design sheet rows (required by `docs/design-rules.md`)

| Row | Content |
|---|---|
| Pitch | Draft: section 1 |
| Fantasy | Open |
| Toy | Open (opening jars and the slot machine are candidates; not decided) |
| Seconds loop | Pick a tile, place it: a jar for each connection and the materials of the land it lights; 5 of a colour make a jar to open. |
| Minutes loop | One game: rounds until no tile can be placed, then the coin piles are compared. |
| Days loop | Open |
| Mechanics | Section 2 |
| Dynamics | Section 4 |
| Kinds of fun | Open |
| Competence | Open |
| Autonomy | Open |
| Relatedness | Open (playing another human is possible) |
| Mastery | Open |
| What would kill the fun | Rewards that pile up over about 20 tiles; ties with nothing to break them; a resource with no job, or two scoring systems with no clear job each; slot machine wins costing more than they give; bidding with nothing to lose. |
| Prototype must answer | Open |

## 6. Still open

- More than 2 players (the owner doesn't know if the screen is big enough).
- A settings button.

## 7. Ideas (not in the game)

- A wild tile: a tile with no lands of its own, its top in 6 stripes (one per land, 3 on each half), that takes the lands of the place it is put.
