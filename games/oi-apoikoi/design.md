# Οι Άποικοι: design

Status: draft, not approved. Base: the board game Dragomino (owner's choice); jars take the place of Dragomino's eggs. Everything in sections 1 and 2 is the owner's rule unless marked "Built for now" or "Open".

## 1. The game in short (draft)

Two players each build their own land from tiles with two terrain halves, on one shared board. Each round, 4 tiles are dealt from the pile and players take them in turn. Each connection a placed tile makes (a matching edge) gives a jar, and lights up the connected land of that colour; every lit square gives one material, and 5 materials of a colour make another jar. The child opens jars by tapping them. Jars hold nothing, gold coins (the points) or bonuses: a slot machine, the first-player token, another jar, one of each material, or a random tile. When no tile can be placed, the taller pile of coins wins.

## 2. Rules

### Players
- 2 players. By default you play against the PC; another human can play instead.
- the PC always does what is mathematically optimal, in every choice (pick, place, jars, slot machine). For now: the best expected result for this turn, not planning whole rounds ahead. To improve later.
- every PC (or second player) action is fully visible, done slowly by a moving hand, as if a person were doing it.
- whose turn it is is obvious: that player's area is lit and the other's dimmed, with a sound when the turn passes.
- Open: more than 2 players (the owner doesn't know if the screen is big enough).

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
   - the round's end is its own moment, seen and heard, before anything else in it (Built for now: leftover market tiles fly back to the pile, then evening falls from the top, a moon and stars over the market, a falling chime; a round starts with morning light sweeping over).
   - materials left in the stockpile carry over to the next round.

### Jars
- the child opens jars by tapping big jars lined up on screen. Opening one yourself is the fun.
- a jar's benefit is immediate. Nothing carries to a "next" round.
- jars stand in lines of up to 6, each line centred on its jars; a new jar takes the first free place (the others slide to keep the line centred); a broken jar leaves its place empty. No glow. Jars waiting are always drawn; while a tile is being placed they step aside over the market and come back.
- jars break at once, as fast as he taps; what a jar held pops up above it as a picture (no words; an empty jar is an X), stays a moment, then flies to its place. Only the slot machine and a tile to place wait (for the other prizes to land, then for him).
- Contents, per 100 jars: 45 one gold coin, 10 empty, 10 two coins, 10 one of each material, 8 another jar, 8 the first-player token, 5 the slot machine, 4 a random tile.
- the random tile has random colours and always fits his land; it flies to its place beside the market's 4 tiles, marked as his, and shows its colours only there; he drags it from there.
- nobody starts with the first-player token; a jar sometimes gives it. Without it, the human player goes first (with two humans, one of them).

### Slot machine (a jar bonus)
- 3 wheels; every wheel has the same 4 faces in its own order: 2 coins, 2 jars, 2 of each material, and a blank (an X).
- only three of a kind wins, and you win what you see (3 faces of 2: 6 coins, 6 jars or 6 of each material); anything else wins nothing. It spins once; then you pay 1 coin to spin the wheels you don't keep, as many times as you want, and stop when you like.
- Worth in coins used by the PC: 1 coin = 1; a jar = what jars hold in coins on average, counting another jar as worth the same again; one of each material = 6/5 of a jar.
- the wheels roll fast, then slow down and stop, by their order among the wheels rolling, at 1.8, 2.6 and 3.5 s, with sounds; the tray under the wheels shows the prize only after they stop.
- each wheel looks like a turning many-sided drum, shaded, the wheels apart; only the face it lands on shows. Tap a wheel to keep it (a clamp drops on it), pull a lever on the machine's side to pay a coin and spin the others, tap the tray under the wheels to take the prizes. No text.

### Points and winning
- points are gold coins drawn one by one, with no numbers. They stand in the 5 material columns, in a tray under the materials, rows of 5 from the top.
- coins come from jars and from the slot machine, and a slot spin costs 1 coin.
- the game ends when no tile left can be placed by either player (so also when the tiles run out). Most coins wins.
- the end is a smaller box over the board; each player's coins fly into his pile (face up, in columns of 10, the same coin size for both); a star stands over the taller pile; a green play button starts again.
- Anything earned per tile or per round must stay a real choice over a whole game (28 tiles: at most 14 each).

## 3. The new look (decided, built 25 Nov)

Replaces the colours-only look. Where it differs from section 2 (the board's size, colours), this section wins.

- Setting: Greek colonies, about 750-550 BC (proposal, owner did not object).
- Lands and their materials: wheat field: grain; pomegranate orchard: pomegranates; vineyard: grapes; forest: timber; mountain: rubies; town: little statues.
- The board is sea: a square board of 16 x 16 squares seen in true isometric view (a diamond 1.73 times as wide as high), as tall as the screen under the market band allows. Land exists only where tiles are placed; each player starts with his own 2-square start tile, as now.
- Sea pictures: the owner's water pack (MaelleMarylloup, "water sea shore material tileset", `art/sea/`): 6 water colours, each a 4 x 4 sheet of 256 x 128 diamonds (open water and shore pieces for every edge and corner). Drawn 2 to 1, squeezed to true isometric. Its terms of use are not checked yet.
- Land pictures: flat 2D pictures in the same isometric view, in the sea pack's hand-drawn style, made for the game; things stand upright, so turning a tile changes only which squares its halves cover. Touching squares of one land join into one area.
- Market: a band across the top: the pile, then the 4 tiles.
- Player areas: the two triangles beside the board on each side, joined by a narrow strip at the board's side corner (green left, red right). The face sits in the thin top corner beside the market. Materials and coins are 1.5 times their old size. Materials: a column of 5 per colour, from the top, beside the screen edge. Coins fill the bottom triangle in rows from the bottom up, each as long as the triangle is wide there, at most 8 a row.

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

## 6. Built for now (not decided by the owner; to check)

- The PC's best for this turn: the pick and place that make the most jars now (one per connection, one per 5 materials, counting the land it lights onto what it has); between equal moves, the one lighting more squares. Jar contents are luck, so any jar is opened first; the slot machine is played for the most expected coins.
- Tiles nobody could place in a round go back under the pile.
- Sounds (simple built-in sounds until the owner's own files come; no blips, a jar breaks when opened): one soft family: wood knocks for dealing, picking, snapping and a wheel stopping; a clay break for opening a jar; a clink for coins; soft chimes for passes, lit squares, jars made from materials and slot wins; a whoosh for the slot spinning.
- The PC's hand: Fluent Emoji pictures; it points to tap and to carry a tile, opens to let go, is raised when the PC passes.
- The pile's 28 layers are 1.5 px apart (the band is made tall enough for them).
- Which land is which of the six: in the order section 3 lists them, most common first (wheat field and pomegranate orchard are the start tile's).
- The start tiles on the 16 x 16 board face each other (owner 25 Nov): the kid's at squares (4, 10)-(5, 10), the PC's the kid's turned half a turn around the board's centre, (11, 5)-(10, 5).
- The water colour: `water-c` of the pack.
- Coins past 80 (8 stacks of 10) stack on from the first place.
- The face's corner: the lit face and a gap fit into the corner between the band and the board's edge; the first-player star beside it, away from the board.

## 7. Still open (all in one place)

- The slot machine: pictures with amounts, later; or 3 faces of 1 each (1 coin, 1 jar, 1 of each material), no blank.
- More than 2 players.
- The region of the colony.
- The design sheet rows marked "Open".

## 8. Ideas (not in the game)

- A wild tile: a tile with no lands of its own, its top in 6 stripes (one per land, 3 on each half), that takes the lands of the place it is put; it was the look of the gift tile before its lands were shown.
