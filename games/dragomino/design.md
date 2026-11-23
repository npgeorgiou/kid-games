# Dragomino (working name): design

Status: draft, not approved. Designed in one chat with the owner on 23 Nov 2026; this file holds everything from it. Not in the brief, so all of it is "new". Base: the board game Dragomino (owner's choice); jars take the place of Dragomino's eggs.

Labels used below:
- **Owner rule**: the owner said it or agreed to it.
- **Owner idea**: the owner proposed it, not yet settled.
- **Proposal**: Claude proposed it; the owner has not answered.
- **Open**: not decided.

## 1. The game in short (draft)

Two players each build their own land from tiles with two terrain halves. Each round, tiles are laid out and players get them in turn or by bidding sets of goods. Placing a half next to the same terrain earns a jar, which the child opens at once by tapping it. Every square of land makes one good of its terrain each round. Three of the same leftover good become a jar. Jars hold gold coins (the points) or bonuses: a slot machine, stealing a tile, the first-player token, or a free tile. When the tiles run out, the longest row of coins wins.

## 2. Rules

### Players
- Owner rule: 2 players. By default you play against the PC; another human can play instead.
- Open: more than 2 players (the owner doesn't know if the screen is big enough).

### Tiles and land
- Owner rule: each tile has two halves, and each half is one terrain.
- Owner rule: there are 5 terrains, and each makes its own good. The names are a proposal: fish, grain or bread, oil, wine, stone. The owner has used "grain".
- Owner rule: a land is all the connected squares of one terrain.
- Owner rule: every land is the same value, whatever its terrain, shape or size. No terrain, symbol or multiplier makes one land worth more than another.
- Owner rule: there is no size limit on a player's land.
- Open: placement rules (must a new tile touch the land? must a half match?). Also open: how many tiles are laid out per round.

### A round
1. **Tiles laid out** (a draft). Owner rule: tiles are picked in turn.
2. **Bidding** (owner idea). You can veto your opponent's choice of a tile by bidding sets. He can outbid you, and so on. The winner's tile is locked for him. A set is 3 different goods.
   - Owner rule: a tile nobody bids on goes by normal turn order.
   - Proposal: if bids tie, the tile goes to whoever picked later last round.
3. **Placing.** Each player places his tiles in his own land.
   - Owner rule: matching edges (a half next to the same terrain) earn a jar, and it is opened at once, during the round.
4. **End of round.**
   - Owner rule: each square of land makes 1 good of its terrain. All goods are worth the same.
   - Owner rule: goods not spent are lost at the end of the round, but 3 of the same good (for example 3 grain) become a jar. Sets don't become jars.
   - Owner rule: jars from leftover goods are opened at the end of the round.
   - Open: the timing. Goods are made at the end of a round. Are they used to bid in the next round and lost at the end of that round, or are they lost right away?

### Jars
- Owner rule: the child opens jars by tapping big jars lined up on screen. Opening one yourself is the fun, so a jar never just gives another jar.
- Owner rule: a jar's benefit is immediate, in this round. Nothing carries to a "next" round.
- Owner rule, contents:
  - Points (gold coins): 50% of the time.
  - The other 50%: the slot machine, stealing a tile from the opponent, the first-player token, or a free extra tile "from nowhere" (not from the draft).
- Open: the share of each bonus within the other 50%. Also open: what stealing takes (a tile he picked this round, or one already in his land).
- Rejected by the owner:
  - A free set: its benefit came the next round.
  - An unbeatable first pick: hard to show visually.
  - A second tile next round: changed into the free tile from nowhere.
  - Double the next jar: it's a "next" thing.
  - Keeping your goods: the same reason.
  - A free tile from the draft.
  - Another jar: you must open jars yourself.
  - An empty jar.

### Slot machine (a jar bonus)
- Owner rule: it has 3 wheels. Their pictures are all the game's resources: the 5 goods, points (coins) and jars.
- Owner rule: it spins once. Then you pay 1 coin to reroll whichever wheels you choose, as many times as you want. When all 3 show the same, you win it.
- Owner idea: wheel pictures can show amounts, such as 2 grain or 3 coins. To be worked out later.
- Owner idea: 2 matching wins 2 of that thing, and 3 matching wins 3.
- Known odds: with 7 pictures, once two wheels match, each reroll has a 1 in 7 chance, so a third match costs about 7 coins on average. The first spin shows a pair about 4 times in 10.
- Proposals, not chosen:
  - Each machine shows only 3 of the 7 kinds (a 1 in 3 chance per reroll).
  - The first reroll is free.
- Open: what winning goods means when goods are lost at the end of the round.

### Points and winning
- Owner rule: points are gold coins drawn one by one, with no numbers. At the end, the players' coins are lined up side by side and the longer row wins.
- Owner rule: coins come from jars and from the slot machine, and a slot reroll costs 1 coin.
- Owner rule: the game ends when the tiles run out. Most points wins.
- Note from the owner: each player places about 20 tiles per game. Anything earned per tile or per round must stay a real choice at that count.

## 3. Rejected ideas (and why)

- **Each land pays its size times the symbols in it** (a boat on sea, a press on olive): this makes lands differ in value.
- **Each land pays 1 coin, whatever its size:** this makes many small lands worth more.
- **Lands differ by shape or size** (Kingdomino-style area scoring): the owner said lands don't differ by shape or size.
- **Coins buy the first pick or a second tile; sets buy the first pick or a second tile:** replaced by the owner's bidding idea.
- **The original sets idea had three holes** (owner's questions): ties with nothing to break them, jars with no job, and sets piling up over about 20 tiles. Goods being lost at round end and leftovers becoming jars came from fixing these.
- **Goods lost at round end make bidding automatic:** the owner pointed out that if goods are lost anyway, there is no reason not to bid them all. Fixed by: 3 of the same leftover good become a jar.

## 4. Tensions (from the rules so far)

- Placing one half well forces the other half somewhere.
- Matching edges for jars pulls toward one terrain. Sets (3 different goods) for bidding pull toward variety.
- Bidding goods wins tiles, while keeping 3 of the same good makes a jar.

## 5. Design sheet rows (required by `docs/design-rules.md`)

| Row | Content |
|---|---|
| Pitch | Draft: section 1 |
| Fantasy | Open |
| Toy | Open (opening jars and the slot machine are candidates; not decided) |
| Seconds loop | Pick or bid for a tile, place it, open the jar a match earns. |
| Minutes loop | One game: rounds until the tiles run out, then the coin rows are compared. |
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

## 6. Still open (all in one place)

- Placement rules, and the number of tiles laid out per round.
- When goods are spent and lost (the timing question in the round).
- The bid tie-break (proposal waiting).
- The bonus shares, and what stealing takes.
- The slot machine: win 2 for 2 and 3 for 3, pictures with amounts, the odds fix, and goods won from it.
- More than 2 players.
- Greek period and region (one per game, `docs/design-rules.md`).
- Terrain and good names.
- How the PC opponent plays.
- The design sheet rows marked "Open".
