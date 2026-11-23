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
- Owner rule: there are 5 terrains, and each makes its own good. For now terrains are only colours, and each good has its terrain's colour; what each land is comes later (not fish: fish does not come from land).
- Owner rule: a land is all the connected squares of one terrain.
- Owner rule: every land is the same value, whatever its terrain, shape or size. No terrain, symbol or multiplier makes one land worth more than another.
- Owner rule: there is no size limit on a player's land.
- Owner rule: a new tile must touch your land; a half need not match. Each player starts with one start square.
- Owner rule: 4 tiles are laid out per round, 2 for each player; 10 rounds, 20 tiles each.

### A round
1. **Tiles laid out** (a draft). Owner rule: tiles are picked in turn.
2. **Picking and bidding** (owner rule). A set is 3 different goods. The player whose turn it is picks a tile. The opponent may bid sets on it; then the bidding goes back and forth. On a tie, the player whose turn it was wins. The winner's tile is locked for him. A tile nobody bids on goes to the picker.
3. **Placing.** Each player places his tiles in his own land.
   - Owner rule: matching edges (a half next to the same terrain) earn a jar, and it is opened at once, during the round.
0. **Start of round.** Owner rule: each square of land makes 1 good of its terrain. All goods are worth the same.
4. **End of round.**
   - Owner rule: goods not spent are lost at the end of the round, but 3 of the same good (for example 3 grain) become a jar. Sets don't become jars.
   - Owner rule: jars from leftover goods are opened at the end of the round.

### Jars
- Owner rule: the child opens jars by tapping big jars lined up on screen. Opening one yourself is the fun, so a jar never just gives another jar.
- Owner rule: a jar's benefit is immediate, in this round. Nothing carries to a "next" round.
- Owner rule, contents:
  - Points (gold coins): 50% of the time.
  - The other 50%: the slot machine, stealing a tile from the opponent, the first-player token, or a free extra tile "from nowhere" (not from the draft).
- Owner rule: stealing takes a tile already in the opponent's land; you place it in yours.
- Open: the other jar bonuses the owner says were agreed (more than these four), and the share of each.
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
- Owner rule (for now): 7 pictures, each worth 1; 2 the same wins 2, 3 the same wins 3; you can stop at any time.

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

- The other agreed jar bonuses, and the bonus shares.
- The slot machine: pictures with amounts, later.
- More than 2 players.
- Greek period and region (one per game, `docs/design-rules.md`).
- What each land and good is (colours only for now).
- Owner rule: the PC picks the tile that gives it the most matches and bids only when that tile would give it a match.
- The design sheet rows marked "Open".
