# Οι Άποικοι: sound hooks

Every sound the game makes has a name. Each one plays a soft built-in sound for now. To use your own sound, put a file named after the sound in `art/sounds/`, for example `art/sounds/splash.mp3` (mp3, wav or ogg), and build. That file then plays instead of the built-in sound.

| Name | When it plays |
|---|---|
| `dawn` | A round starts (morning light sweeps over). |
| `deal` | A tile is dealt from the pile to a market place. |
| `turn` | The turn passes to the other player (his area lights up). |
| `pick` | A player takes a tile from the market. |
| `rotate` | A tile in hand is turned (a tap on it). |
| `back` | A tile in hand is put back on an empty market place. |
| `snap` | A tile snaps into its place on the board. |
| `splash` | The same moment: the tile drops onto the water (rings spread on the sea) |
| `edge` | A matching edge glows and its land lights up. |
| `good` | A material flies from a lit square to the player's area. |
| `shine` | A column of 5 materials is full and flashes. |
| `jarland` | A jar lands in its place. |
| `into` | A material jumps into a jar. |
| `made` | The last of the 5 materials is in the jar. |
| `jar` | A jar is tapped and breaks. |
| `reveal` | What the jar held pops up above it. |
| `coin` | A coin lands in the player's coin stacks. |
| `token` | The first-player star lands beside the player's face. |
| `spin` | The slot machine's lever is pulled. |
| `roll` | The slot wheels tick as their pictures pass. |
| `stop` | A slot wheel stops. |
| `clamp` | A clamp goes on or comes off a slot wheel. |
| `win` | The slot machine's prize is taken. |
| `pass` | A player has no tile he can place and passes. |
| `roundend` | A round ends. |
| `victory` | The game's winner is announced (a fanfare). |
| `popper` | The winner's ribbons burst out (a party popper). |
| `board` | A tap on the table where nothing is (dust). |
| `watertap` | A tap on the water (rings and drops); the architects game's water tap sound, in `art/sounds/watertap.mp3`. |
| `poke` | A tap on a player's sticker (it looks happy for a moment). |
| `rubyin` | The ruby forms on the side of the player who takes the lead in coins. |
| `rubyout` | The ruby bursts into bits: the coins are level. |
| `rubymove` | The ruby flies from one player's side to the other's. |

Missing a moment? Add a line: the name you want and when it should play.
