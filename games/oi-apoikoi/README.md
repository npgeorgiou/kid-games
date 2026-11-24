# Οι Άποικοι (Oi Apoikoi, "The Settlers")

A two-player tile-drafting game built on the loop of the board game Dragomino: each player builds his own land from two-half terrain tiles, bids sets of goods for tiles, and opens jars for gold coins and bonuses. A rough prototype with colours only; the full design is in `design.md`.

## How to play

- Open `oi-apoikoi.html` in a browser (one self-contained file). You are green (left panel), the PC is red (right panel); you share one board.
- Top: the 4 tiles of this round; the bars are the rounds left. Tap a tile to pick it. Tiles you can't place are greyed; if none fits you, your turn passes and the PC plays again.
- If the other player wants your tile, a panel shows the sets needed (a set is one of each of the 5 goods): green takes it (a tie is the picker's), red lets it go.
- The tile you win stays where it is: tap it to turn it, drag it and leave it anywhere, as often as you like. It is placed when you leave it near a place it fits (the place is shown first): two free squares with a matching edge with your own land.
- Every matching edge, with any land, earns a jar; tap the big jars to open them. Slot machine: tap wheels to choose, the green button pays a coin and spins them again, the yellow button takes what you have.
- Each panel: goods (a row per colour), sets, gold coins; the star is the first-player token. A hand does every PC move: it points to tap, grabs to carry a tile, opens to let go, and is raised when the PC passes.
- The game ends when no tile left can be placed by either player. The two rows of coins are shown; the star marks the winner. The round arrow starts again.

## Where things are

- `design.md`: the full design (draft): rules, jars, slot machine, points, rejected ideas, tensions, sheet rows, everything open.
- `WARNINGS.md`: traps found in this game.
- `src/index.html`: the game source; `build.py` makes `oi-apoikoi.html` from it, with the hand pictures put in.
- `src/hands/`: the hand pictures (Microsoft Fluent Emoji, MIT license in `src/hands/LICENSE`).
- `tools/flows.py`: flow tests, one per owner rule and bug report, plus random play through the screen; `tools/harness.py` builds and runs them (the whole set in two browsers side by side, about 7 s).
- `tools/ci-checks.txt`: the list of every check of the game, run on GitHub on every push.
- `tools/backdoors.txt`: what a flow may never contain (moves through the game's insides); the commit check refuses it.

## Running the checks

`python3 tools/harness.py flows` (all) or `python3 tools/harness.py flows <name>`; each prints PASS or FAIL.

## Now

A playable prototype against the PC on one shared board, colours only. Tiles are dragged straight from the pile and stay where they are left until they snap; a won bid locks a tile for its winner; the stockpile stands in colour columns with set bands and jar frames; jars have labels; the slot machine rolls and shows price and prize; the PC plays with a visible hand (points, grabs with a fist). Rules and built-for-now choices are in `design.md`.

## Open

- Waiting for the owner: sounds (built-in simple sounds for now, or only sound slots until his files come); whether a placed land's good appears in the stockpile at once (today goods are made at the start of each round, and at the end of the round they turn into jars or are lost).
- Then: sounds; the stockpile answer (a flow repeating his steps first); a general refactor (one owner per behaviour: the turn being asked belongs to the game; the source split by part), tests passing throughout.
- The owner turns on branch protection for main (require the "tests" check and code-owner review).
- See also `design.md` sections 6 and 7.

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

Owner's points (23 Nov 2026, second message):

1 start tile should be dual, and same for everyone. has the 2 most common colors. lets agree on color scardity. suggest based on math, you know the game needs (sets). 2 keep, all random based on color ratio of point 1, except of the start one, see point 1. 3 one tile can earn many, be smart. If you dont know the placement rules, ask me. think first, you can figure it out yourself. 4 fixed, 1. very rarely 2, so add 2 coins as another bonus. 5 sets are made of 1 of each, I change my mind. so, sets of 5. only the winner pays. 6 yes. 7 noone starts with it, a jar sometimes gives it. 8 keep. 9 the pc should respin too, all pc or second player actions are fully visible, as if a second player was doing them, with moving hand and all. 10 already answered. 11 keep. now, commnets on your first iteration: 1. tiles should not be q visible squares, but one rectangle tchromatically divided in half. 2. consider this game a game that uses drag for the tiles, not clicking, so we drag the tile. you can rotate it by tapping. you drag it to snap it in place. visual indication before snapping. remvoe the squares that you make appear around the existing land. 3. make play area bigger, players share 1 play board, own land gets boorder all around its edges. connecting with opponent tiles still gives jars. 4. opponent actions should happen more slowly, and with a hand doing them, see architect game for examples of a hand (in the tutorials) that does things. for this game make or find online a better hand.

Owner's points (23 Nov 2026, third message):

1. see, I told you to consider game mechancs. A 10% land does not allow for sets easily. 2. can understand. 3. one jar per matching edge. also, tiles CANT be palced if they dont ahve a matching edge. In the first round, tiles are not random, but made so that each player has at least 1 option. 4. the human player first, in case of 2 human players, one of them. 5 the pc does what is mathematically optimal, ALWYAYS; not only on the wheel. 6. board fits screen, starting points ad the centers of the 2 imagined halfs of board. 7. yes. 8, yes, wheter the whole landmass is conneced or no means nothing. also take the mentle of an expert UI designer and maximize all the good expericens, give palce space, dont waste space, and generally be an expert UI designer

Owner's points (23 Nov 2026, fourth message):

1. report on test logic and speed (talk as a programmer here, albeit at a high-level) , and think of what you can do (more than one item) to make tests better and faster. 2. rename game to "Oi Apoikoi" (in greek). 3. your hand is like a creepy marionette hand, can you find a better one online, or no? also comment on the hand positions (gestures?) we need. 4. I  dont want to click and take the tile in my aera, its a dragging motion is that clear ffs? I drag, i leave, i drag again, i leave again, i rotate, i rotate in the pile before i drag, i can do whatever i want until i snap it ok? 5. maybe i wasnt clear: you cant just go and snap on teh enemy board, it MUST connect to yours, its just that it can also, ON TOP OF THE FIRST RULE, also connect to the enemy board. i expect it to be VERY RARE, only if the 2 landmasses ahve grown towards each other. "The game ends once every tile left has had its turn and still fits nowhere." -> you dont make any sence, tiles dont have turns.

Owner's points (24 Nov 2026, 00:51):

start work in 1 hour, make a scheduled task: yes, only current test suite is run, find a fucking way to force yourself to write tests, moron. just font one, idiot. stupid. idiot. ALSO:  1- no reason to tap tile first in the pile, just drag immediately. 2. you have bugs, at least when stealing ahppened, I was left with no materials. 3. add some sounds, its hard to follow what happens. 4. for bonus jar shit, add some text too, i dont get what some of those mean. 5. slot machine: awfull, make it actually roll, make sounds, make the buttons more explanatory and better, I cant iven see what I pay, its crazy. 6 more bugs: I got a land, its material didnt appear at my stockpile. 6: an extra tile from the jar appears on top of the pile, its crazy, moronic, amateursish. generally your ui is shit, also the user area, IS SHIT in its layout: materials should be order vertically, not horizontally, what will you do when I will ahev 20 yellows, expand the sidebar???? lol. also there is no reason for the outline around the pile tiles.  7. You certainly ahve many bugs with stealing, I stole a tile and made 2 connections, and 5 jars appears. lol, its not that hard. your code is a mess, I demand a general refactoring. also, your tests are shit. for fucks sake, how can you write so bad tests? what the fuck do your tests test, really? you need to read the caldue rules abour tests, udnerstnad why you failed them, and improve them. you piss me off, no mater how many revision to this testing rules we make YOU CANT FUCKING FOLLOW THEM, MORON. WHY????????????????????????????????????????????????????????????????????????????????????????????????????????????????.  ALSO: Is it not clear yet: BIDDING DOES NOT AMKE THE WINNER TAKE THE FUCKING PIECE, IT JUST LOCKS IT SO ONLY HE CAN PICK IT, IT BECOMES VISUALLY GREY FOR YOU. YOU ALSO HAVE TO VISUALLY GROUP MATERIALS IN GROUPS OF SETS, AND GROUPS OF HOW MANY GIVE HARS, SO THE PLAYER CAN KNOW WHAT TO EXPECT AT THE END OF ROUND. GENERALLY YOUR ui IS SHIT. AND THAT HAND GESTURE IS NOT A grabbing gesture.
