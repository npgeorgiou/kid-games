# Οι Άποικοι: design

Status: draft, not approved. Designed in one chat with the owner on 23 Nov 2026; this file holds everything from it. Not in the brief, so all of it is "new". Base: the board game Dragomino (owner's choice); jars take the place of Dragomino's eggs.

Labels used below:
- **Owner rule**: the owner said it or agreed to it.
- **Owner idea**: the owner proposed it, not yet settled.
- **Proposal**: Claude proposed it; the owner has not answered.
- **Open**: not decided.

## 1. The game in short (draft)

Two players each build their own land from tiles with two terrain halves. Each round, tiles are laid out and players get them in turn or by bidding sets of goods. Placing a half next to the same terrain earns a jar, which the child opens at once by tapping it. Every square of land makes one good of its terrain each round. Five of the same leftover good become a jar. Jars hold nothing, gold coins (the points) or bonuses: a slot machine, stealing a tile, the first-player token, or a free tile. When the tiles run out, the longest row of coins wins.

## 2. Rules

### Players
- Owner rule: 2 players. By default you play against the PC; another human can play instead.
- Owner rule: the PC always does what is mathematically optimal, in every choice (pick, bid, place, jars, slot machine). For now (owner yes): the best expected result for this turn, not planning whole rounds ahead. To improve later.
- Owner rule: every PC (or second player) action is fully visible, done slowly by a moving hand, as if a person were doing it.
- Owner rule (24 Nov): whose turn it is is obvious: that player's area is lit and the other's dimmed, with a sound when the turn passes.
- Open: more than 2 players (the owner doesn't know if the screen is big enough).

### Tiles and land
- Owner rule: each tile has two halves, and each half is one terrain.
- Owner rule: there are 5 terrains, and each makes its own good. For now terrains are only colours, and each good has its terrain's colour; what each land is comes later (not fish: fish does not come from land).
- Owner rule: a land is all the connected squares of one terrain.
- Owner rule: every land is the same value, whatever its terrain, shape or size. No terrain, symbol or multiplier makes one land worth more than another.
- Owner rule: there is no size limit on a player's land.
- Owner rule: a tile is placed on two free squares with at least one matching edge with your own land. Matching edges with the other player's land also earn jars (rare: only when the lands have grown toward each other).
- Owner rule: each player starts with the same start tile, two halves in the two most common colours.
- Owner rule: one shared board that fits the screen. The start tiles are at the centres of its two halves. Each player's own land has a border all around its edges.
- Owner rule: the colours are scarce in a fixed ratio; tiles are random by that ratio (except the start tile). Built for now: 24/22/20/18/16% (the owner asked for scarcity based on the math and did not pick between equal and this). Note from the owner: if sets don't form easily, the split may need rethinking, or sets may get a bigger job in the game.
- Owner rule: in the first round the tiles are not random: they are made so that each player has at least one tile he can place.
- Owner rule: 4 tiles are laid out per round, 2 for each player; 10 rounds, 20 tiles each.

### A round
1. **Start of round.** Owner rule: each square of land makes 1 good of its terrain. All goods are worth the same. Owner rule (24 Nov): a tile placed during the round (picked, stolen or free) makes its 2 goods at once too.
2. **Tiles laid out** (a draft). Owner rule: tiles are picked in turn.
3. **Picking and bidding** (owner rule). A set is 5 goods, one of each. Only the winner pays. The player whose turn it is picks a tile. The opponent may bid sets on it; then the bidding goes back and forth. On a tie, the player whose turn it was wins. The bid's winner does not take the tile: it is locked for him (greyed for the other player) and only he can pick it, later, on his turn; a picker who loses the bid picks again. A picker who wins (a tie is his) takes it now. A tile nobody bids on goes to the picker.
   - Owner rule: tiles you can't place are greyed (colours still visible) and can't be picked. With none to pick, your turn passes, slowly and clearly, and the other player plays again. No tile is thrown.
4. **Placing.** Each player places his tiles in his own land.
   - Owner rule: one jar per matching edge, so one tile can earn several, and edges with the opponent's land count too. They are opened at once, during the round.
   - Owner rule (24 Nov): it is shown: when the tile snaps (with a snap sound) each matching edge glows, and each jar comes out of its edge and flies to the jar row, one after another.
   - Owner rule: a tile is one rectangle, coloured half and half. The won tile stays where it is (in the top row at first): tap it to turn it, drag it and leave it anywhere, as often as you like, until it snaps into a place; before it snaps, the place is shown.
5. **End of round.**
   - Owner rule (24 Nov): the round's end is its own moment, seen and heard, before anything else in it (built for now: a sun sets behind a horizon, with a falling chime).
   - Owner rule: goods not spent are lost at the end of the round, but each 5 of the same good become a jar (10 make 2; owner 24 Nov: 5, not 3). Sets don't become jars.
   - Owner rule: jars from leftover goods are opened at the end of the round.
   - Owner rule (24 Nov): this is shown one group at a time: each 5 of a colour fly from the stockpile into a jar; then the leftover goods fade out.
   - Owner rule (24 Nov): one player turns his goods into jars and opens them, then the other (the first-player token holder first).

### Jars
- Owner rule: the child opens jars by tapping big jars lined up on screen. Opening one yourself is the fun.
- Owner rule: a jar's benefit is immediate, in this round. Nothing carries to a "next" round.
- Owner rule, contents:
  - Per 100 jars (owner 24 Nov): 10 empty, 40 one gold coin, 10 two coins, 5 stealing a tile from the opponent, 5 a free extra tile "from nowhere" (not from the draft); the rest equal, 7.5 each: the slot machine, the first-player token, another jar, a free set.
- Owner rule: stealing takes a tile already in the opponent's land; you place it in yours. A tile with no place in your land can't be stolen. Whether the opponent's land stays connected does not matter.
- Owner rule: a free tile is always one that can be placed.
- Owner rule: nobody starts with the first-player token; a jar sometimes gives it. Without it, the human player goes first (with two humans, one of them). The holder opens his end-of-round jars first.
- Rejected by the owner:
  - An unbeatable first pick: hard to show visually.
  - A second tile next round: changed into the free tile from nowhere.
  - Double the next jar: it's a "next" thing.
  - Keeping your goods: the same reason.
  - A free tile from the draft.

### Slot machine (a jar bonus)
- Owner rule: it has 3 wheels. Their pictures are all the game's resources: the 5 goods, points (coins) and jars.
- Owner rule: it spins once. Then you pay 1 coin to reroll whichever wheels you choose, as many times as you want.
- Owner idea: wheel pictures can show amounts, such as 2 grain or 3 coins. To be worked out later.
- Known odds: with 7 pictures, once two wheels match, each reroll has a 1 in 7 chance, so a third match costs about 7 coins on average. The first spin shows a pair about 4 times in 10.
- Proposals, not chosen:
  - Each machine shows only 3 of the 7 kinds (a 1 in 3 chance per reroll).
  - The first reroll is free.
- Owner rule (for now): 7 pictures, each worth 1; 2 the same wins 2, 3 the same wins 3; you can stop at any time.
- Owner rule (24 Nov): the wheels roll fast, then slow down and stop one after another (first, second, third), with sounds.

### Points and winning
- Owner rule: points are gold coins drawn one by one, with no numbers. At the end, the players' coins are lined up side by side and the longer row wins.
- Owner rule: coins come from jars and from the slot machine, and a slot reroll costs 1 coin.
- Owner rule: the game ends when no tile left can be placed by either player (so also when the tiles run out). Most points wins.
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
- Matching edges for jars pulls toward one terrain. Sets (5 goods, one of each) for bidding pull toward variety.
- Bidding goods wins tiles, while keeping 5 of the same good makes a jar.

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

## 6. Built for now (not decided by the owner; to check)

- The colour split (see Tiles and land).
- The PC counts every jar as worth the same and judges a move by the jars it earns this turn.
- The PC counts a jar as about 0.7 coins (its coin contents only) and a good as a third of a jar; with these values the best slot play is to stop at once, so the PC never re-spins.
- Tiles nobody could place in a round go back under the pile.
- Sounds (owner 24 Nov: simple built-in sounds until his own files come; no blips, a jar breaks when opened): one soft family: wood knocks for picking, snapping and a wheel stopping; a clay break for opening a jar; a clink for coins; soft chimes for bids, passes, jars made from goods and slot wins; a whoosh for the slot spinning and a steal.
- The PC's hand: Fluent Emoji pictures; it points to tap and to carry a tile (owner 24 Nov), opens to let go, is raised when the PC passes.

## 7. Still open (all in one place)

- The slot machine: pictures with amounts, later.
- More than 2 players.
- Greek period and region (one per game, `docs/design-rules.md`).
- What each land and good is (colours only for now).
- The design sheet rows marked "Open".
