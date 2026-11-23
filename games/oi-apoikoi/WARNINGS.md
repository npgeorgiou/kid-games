# Οι Άποικοι: warnings

- "Every land is the same value" means no land, terrain or square may be worth more than another by type; do not add symbols, multipliers or per-land payouts that break it.
- Check every per-tile or per-round reward against about 20 tiles each per game before proposing it.
- In tests (fast) the PC moves at once: pass slot spins and jar contents in the table, never after it starts.
- In-page test loops wait with a message, not setTimeout(0): each timer waits about 4 ms, which made random play 30 times slower.
- Never draw an SVG picture on the canvas every frame: draw it once onto its own canvas and draw that.
