# Οι Άποικοι: warnings

- "Every land is the same value" means no land, terrain or square may be worth more than another by type; do not add symbols, multipliers or per-land payouts that break it.
- Check every per-tile or per-round reward against about 20 tiles each per game before proposing it.
- In tests (fast) the PC moves at once: pass slot spins and jar contents in the table, never after it starts.
- In-page test loops wait with promise steps (await null), not timers or messages: those wait for the browser and made random play many times slower.
- Never draw an SVG picture on the canvas every frame: draw it once onto its own canvas and draw that.
- Time passes only for the current game: pause and hand moves never end for an old game, so old jars, moves and turns stop and never touch a new game. Never read the game state across an await without that.
- The page's fake clock is paused with a date, not a number (a number after an earlier pause is refused); every fake second of real-speed play costs about half a real second.
- Sounds at test speed are only noted (`__dg.sounds()`), never played: playing hundreds at once in random play cost about half a second.
- Flows that only need the end of a wait jump the fake clock (skip: fast_forward, each due timer once); run_for steps every frame and costs about half a real second per fake second.
- Build (run the harness) before staging: the committed page must be built from the committed source; a page staged before the build goes in stale.
- A flow that samples the game's randomness is seeded (table(seed=...)): unseeded shares wander out of any tight band now and then, and the run fails at random.
- At test speed timings are 0: never divide by a duration without guarding it (a reel with 0 ms gave NaN, drew an unknown face and stopped the PC's turn).
- Run the main game on many seeds (MAIN_SEED 1..30) after a rule change: it finds crashes no small flow reaches (negative radii with very many goods or coins).
