# Οι Άποικοι: design

Status: draft, not approved. Designed in one chat with the owner on 23 Nov 2026; this file holds everything from it. Not in the brief, so all of it is "new". Base: the board game Dragomino (owner's choice); jars take the place of Dragomino's eggs.

Labels used below:
- **Owner rule**: the owner said it or agreed to it.
- **Owner idea**: the owner proposed it, not yet settled.
- **Proposal**: Claude proposed it; the owner has not answered.
- **Open**: not decided.

## 1. The game in short (draft)

Two players each build their own land from tiles with two terrain halves, on one shared board. Each round, 4 tiles are dealt from the pile and players take them in turn. Each connection a placed tile makes (a matching edge) gives a jar, and lights up the connected land of that colour; every lit square gives one material, and 5 materials of a colour make another jar. The child opens jars by tapping them. Jars hold nothing, gold coins (the points) or bonuses: a slot machine, the first-player token, another jar, one of each material, or a random tile. When no tile can be placed, the taller pile of coins wins.

## 2. Rules

### Players
- Owner rule: 2 players. By default you play against the PC; another human can play instead.
- Owner rule: the PC always does what is mathematically optimal, in every choice (pick, place, jars, slot machine). For now (owner yes): the best expected result for this turn, not planning whole rounds ahead. To improve later.
- Owner rule: every PC (or second player) action is fully visible, done slowly by a moving hand, as if a person were doing it.
- Owner rule (24 Nov): whose turn it is is obvious: that player's area is lit and the other's dimmed, with a sound when the turn passes. No sign flies from face to face (owner 24 Nov: "weird").
- Open: more than 2 players (the owner doesn't know if the screen is big enough).

### Tiles and land
- Owner rule: each tile has two halves, and each half is one terrain.
- Owner rule (25 Nov): there are 6 terrains (the 6th teal), and each makes its own material. For now terrains are only colours, and each material has its terrain's colour; what each land is comes later (not fish: fish does not come from land).
- Owner rule: a land is all the connected squares of one terrain.
- Owner rule: every land is the same value, whatever its terrain, shape or size. No terrain, symbol or multiplier makes one land worth more than another.
- Owner rule: there is no size limit on a player's land.
- Owner rule: a tile is placed on two free squares with at least one matching edge with your own land. Matching edges with the other player's land count too (rare: only when the lands have grown toward each other).
- Owner rule: each player starts with the same start tile, two halves in the two most common colours.
- Owner rule (25 Nov): one shared board, 20 x 13 squares, as big as the screen's height allows; the player areas take the rest of the width. The start tiles are at the centres of its two halves. Each player's own land has a border all around its edges.
- Owner rule (25 Nov): 28 tiles; their 56 halves are 10, 10, 9, 9, 9, 9 of the six colours; tiles are random from these halves (except the start tile).
- Owner rule (24 Nov): of the first round's 4 tiles, 2 surely fit (one for each player); the other 2 are truly random.
- Owner rule: 4 tiles per round, 2 for each player.
- Owner rule (25 Nov): the pile holds every tile, a layer each; the 4 market tiles are dealt from it one by one.
- Owner rule (25 Nov): a tile is the same size everywhere (market, hand, board).

### A round
1. **Tiles dealt** (a draft). Owner rule: 4 tiles; the players take turns. A turn is: pick a tile, place it, open the jars it made; then the turn passes. Each player picks 2 tiles per round.
2. **Picking.** Owner rule (24 Nov): no bidding. The player whose turn it is takes the tile he picks.
   - Owner rule: tiles you can't place get a light grey wash (colours still clear, owner 25 Nov) and can't be picked. With none to pick, your turn passes and the other player plays again; a skipped turn is only its sound (owner 25 Nov). No tile is thrown.
   - Owner rule (25 Nov): no wild tiles, no sets to spend, no stealing.
   - Owner rule (24 Nov): a picked tile can be put back on its market place.
3. **Placing.** Each player places his tiles in his own land.
   - Owner rule: a tile is one rectangle, coloured half and half. The won tile stays where it is (in the market at first): tap it to turn it, drag it and leave it anywhere, as often as you like, until it snaps into a place; before it snaps, the place is shown.
4. **Connections and materials.** Owner rule (25 Nov): land does not make materials each round, and a tile's halves make none by themselves.
   - Each connection (a matching edge, with any land) glows and gives a jar, which drops from the top of the screen.
   - Each connection also lights the connected land of its colour, both players', spreading out from it; each lit square gives one material of that colour, flying from it to the stockpile, 120 ms apart; each colour comes in its own line.
   - 5 materials of one colour become a jar at once; the jar drops while the 5th material flies; each material is used once.
   - The stockpile is a tray in the player's area: one row of 5 places per colour.
5. **End of round.**
   - Owner rule (24 Nov): the round's end is its own moment, seen and heard, before anything else in it (built for now: leftover market tiles fly back to the pile, then evening falls from the top, a moon and stars over the market, a falling chime; a round starts with morning light sweeping over).
   - Owner rule (24 Nov): materials left in the stockpile carry over to the next round.

### Jars
- Owner rule: the child opens jars by tapping big jars lined up on screen. Opening one yourself is the fun.
- Owner rule: a jar's benefit is immediate. Nothing carries to a "next" round.
- Owner rule (25 Nov): jars stand in lines of up to 6, each line centred on its jars; a new jar takes the first free place (the others slide to keep the line centred); a broken jar leaves its place empty. No glow. Jars waiting are always drawn; while a tile is being placed they step aside over the market and come back.
- Owner rule (25 Nov): jars break at once, as fast as he taps; what a jar held pops up above it as a picture (no words; an empty jar is an X), stays a moment, then flies to its place. Only the slot machine and a tile to place wait (for the other prizes to land, then for him).
- Owner rule (25 Nov), contents, given "per 95": 10 empty, 40 one gold coin, 10 two coins, 2.5 a random tile, 5 the slot machine, 7.5 the first-player token, 7.5 another jar, 7.5 one of each material. These add up to 90; the game draws by these weights (so 40 coins is 44% of jars).
- Owner rule (25 Nov): the random tile has random colours and always fits his land; it flies to its place beside the market's 4 tiles, marked as his, and shows its colours only there; he drags it from there.
- Owner rule: nobody starts with the first-player token; a jar sometimes gives it. Without it, the human player goes first (with two humans, one of them).
- Rejected by the owner:
  - An unbeatable first pick: hard to show visually.
  - A second tile next round: changed into the free tile from nowhere.
  - Double the next jar: it's a "next" thing.
  - Keeping your goods: the same reason.
  - A free tile from the draft.

### Slot machine (a jar bonus)
- Owner rule (25 Nov): 3 wheels; every wheel has the same 4 faces in its own order: 2 coins, 2 jars, 2 of each material, and a blank (an X).
- Owner rule (25 Nov): only three of a kind wins, and you win what you see (3 faces of 2: 6 coins, 6 jars or 6 of each material); anything else wins nothing. It spins once; then you pay 1 coin to spin the wheels you don't keep, as many times as you want, and stop when you like.
- Option 1, also possible (owner 25 Nov, noted): 3 faces of 1 each (1 coin, 1 jar, 1 of each material), no blank.
- Worth in coins used by the PC: 1 coin = 1; a jar = what jars hold in coins on average, counting another jar as worth the same again; one of each material = 6/5 of a jar.
- Owner rule (25 Nov): the wheels roll fast, then slow down and stop, by their order among the wheels rolling, at 1.8, 2.6 and 3.5 s, with sounds; the tray under the wheels shows the prize only after they stop.
- Owner rule (24 Nov): each wheel looks like a turning many-sided drum, shaded, the wheels apart; only the face it lands on shows. Tap a wheel to keep it (a clamp drops on it), pull a lever on the machine's side to pay a coin and spin the others, tap the tray under the wheels to take the prizes. No text.

### Points and winning
- Owner rule: points are gold coins drawn one by one, with no numbers. They stand in the 5 material columns, in a tray under the materials, rows of 5 from the top (owner 25 Nov).
- Owner rule: coins come from jars and from the slot machine, and a slot spin costs 1 coin.
- Owner rule: the game ends when no tile left can be placed by either player (so also when the tiles run out). Most coins wins.
- Owner rule (25 Nov): the end is a smaller box over the board; each player's coins fly into his pile (rows of 10, the same coin size for both); a star stands over the taller pile; a green play button starts again.
- Note from the owner: anything earned per tile or per round must stay a real choice over a whole game (28 tiles: at most 14 each).
- Measured on the 25 Nov prototype: about 96 jars a game, the kid about 30 coins, the PC about 34. To be measured again by the simulation tool.

## 3. Rejected ideas (and why)

- **Each land pays its size times the symbols in it** (a boat on sea, a press on olive): this makes lands differ in value.
- **Each land pays 1 coin, whatever its size:** this makes many small lands worth more.
- **Lands differ by shape or size** (Kingdomino-style area scoring): the owner said lands don't differ by shape or size.
- **Coins buy the first pick or a second tile; sets buy the first pick or a second tile:** replaced by the owner's bidding idea.
- **The original sets idea had three holes** (owner's questions): ties with nothing to break them, jars with no job, and sets piling up over about 20 tiles. Goods being lost at round end and leftovers becoming jars came from fixing these.
- **Bidding sets on picked tiles** (24 Nov): too slow, every pick triggered it.
- **Other ways to spend sets offered 24 Nov** (sets buy the first pick; tiles priced in sets; a set reserves a tile; sets become coins): rejected by the owner.
- **Fewer jars by 10 of a colour per jar, one jar per colour per round, or jars only from sets** (24 Nov): rejected; things must be consistent and simple, and 10 is too many.
- **Goods lost at round end make bidding automatic:** the owner pointed out that if goods are lost anyway, there is no reason not to bid them all. Fixed by: 3 of the same leftover good become a jar.

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
- Sounds (owner 24 Nov: simple built-in sounds until his own files come; no blips, a jar breaks when opened): one soft family: wood knocks for dealing, picking, snapping and a wheel stopping; a clay break for opening a jar; a clink for coins; soft chimes for passes, lit squares, jars made from materials and slot wins; a whoosh for the slot spinning.
- The PC's hand: Fluent Emoji pictures; it points to tap and to carry a tile (owner 24 Nov), opens to let go, is raised when the PC passes.
- The pile's 28 layers are about 1 px apart on a 1280 x 800 screen (the pile stays above the market's bottom).

## 7. Still open (all in one place)

- The slot machine: pictures with amounts, later.
- More than 2 players.
- Greek period and region (one per game, `docs/design-rules.md`).
- What each land and good is (colours only for now).
- The design sheet rows marked "Open".
