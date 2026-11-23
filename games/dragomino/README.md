# Dragomino (working name)

A two-player tile-drafting game based on the board game Dragomino: each player builds his own land from two-half terrain tiles, bids sets of goods for tiles, and opens jars for gold coins and bonuses. A rough prototype with colours only; the full design is in `design.md`.

## How to play

- Open `dragomino.html` in a browser (one self-contained file). You play on the left, the PC on the right.
- Top: the 4 tiles of this round; the bars on the left are the rounds left. Tap a tile to pick it.
- If the other player wants it, a panel shows the sets needed: green takes it (a tie is yours), red lets it go.
- Your tile in hand is bottom-left on your land; tap it to turn it. Tap a blue square to place it there.
- Jars: tap the big jars to open them. Slot machine: tap wheels to choose, the green button pays a coin and spins them again, the yellow button takes what you have.
- Under each land: goods (a row per colour) and gold coins. The star is the first-player token.
- At the end the two rows of coins are shown; the star marks the winner. The round arrow starts again.

## Where things are

- `design.md`: the full design (draft): rules, jars, slot machine, points, rejected ideas, tensions, sheet rows, everything open.
- `WARNINGS.md`: traps found in this game.
- `src/index.html`: the game source; `build.py` makes `dragomino.html` from it.
- `tools/flows.py`: flow tests, one per owner rule; `tools/harness.py` builds and runs them.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL.

## Now

A rough playable prototype against the PC, colours only. Rules and what was built without an owner decision are in `design.md` sections 2 and 6.

## Open

See `design.md` sections 6 and 7.

## Task list


Owner's points (23 Nov 2026):

1. Every land is the same value.
2. What if both players have sets of 3?
3. What would jars serve?
4. By the end of the game each player would easily make many sets, because every player places maybe 20 tiles.
5. Goods lost at the end of the round: agreed.
6. Bidding: veto the opponent's choice with sets, he can outbid, and so on; the winner's tile is locked for him. But with goods lost at the end of the round there is no reason not to bid.
7. Jars: keep thinking.
8. Leftover goods: 3 of the same good become a jar (not sets). Jars are opened for points, and sometimes crazy bonuses.
9. Matching edges get jars too. Bonuses: first understand the game elements, the game loop and the win condition.
10. Game ends when tiles run out. Most points wins. Jars opened at end of round, by the kid tapping big lined-up jars. A tile nobody bids on: normal turn order. No land size limit.
11. Bonuses: benefit must be immediate, this round (jars open in the round or at its end). Free set: no. Unbeatable first pick: hard to show. Second tile: better as a free tile. Double next jar, keep goods: no, nothing "next". Ideas: steal a tile from the opponent, get the first-player token, get another jar, get points. What are points? Not discussed yet.
12. Jars from connections are opened during the round, at once. Points: gold coins drawn one by one, rows compared, agreed. Bonuses: free tile from the draft no; another jar no (you must open it yourself); empty jar no; points yes, 50% of the time. Slot machine bonus: 3 wheels showing all game resources (the 5 goods, points, jars); it spins once, then you pay 1 coin to reroll the wheels you choose, as many times as you want; when all 3 show the same, you win it.
13. Slot machine: suggest simple changes so a win does not cost about 7 coins. Steal: keep. First-player token: keep. The other 50% of jars: slot machine plus the bonuses kept. Free tile: an extra tile from nowhere. Players: 2; default against the PC, can be another human; more players unknown (screen size).
14. Slot machine: 2 the same win 2, 3 the same win 3? Wheel pictures can show amounts (2 grain, 3 coins), later. Write a clean design doc with everything another chat needs.
15. Build defaults: 1 yes, 2 yes, 3 goods made at the start of the round, become jars at the end, 4 picker picks, maybe the enemy bids, then the bidders go on, tie goes to the picker, 5 no: many more jar bonuses were mentioned and agreed, 6 yes, 7 yes for now, 8 yes, 9 no fish (not from land); colours only for now, lands and matching resource colours; what each land is, later.
16. Jar bonuses: yes also to another jar and free set.
17. Build it.
