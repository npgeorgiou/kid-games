# Οι Άποικοι: warnings

- "Every land is the same value" means no land, terrain or square may be worth more than another by type; do not add symbols, multipliers or per-land payouts that break it.
- Check every per-tile or per-round reward against about 20 tiles each per game before proposing it.
- In tests (fast) the PC moves at once: pass slot spins and jar contents in the table, never after it starts.
- In-page test loops wait with promise steps (await null), not timers or messages: those wait for the browser and made random play many times slower.
- Never draw an SVG picture on the canvas every frame: draw it once onto its own canvas and draw that.
- A PC move is tied to its game and its tile: after any await it stops if a new game started (a new game during the hand's drag moved the new game's tile).
- The page's fake clock is paused with a date, not a number (a number after an earlier pause is refused); every fake second of real-speed play costs about half a real second.
