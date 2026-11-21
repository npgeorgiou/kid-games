# Coloring Book: warnings

- Oil rates are per pixel of finger travel (times the dab spacing), never per dab, or the brush runs dry at a different length for every size.
- Oil looks like pinstripes or corrugated tubes when bristle strength changes pixel to pixel or shadows go dark; streaks must be soft (blurred bristles) and lit mostly by highlights, checked on a full-resolution crop, not a scaled screenshot.
- Watercolour pigment moves by flow and by diffusion in the same step; their combined outflow must stay under what a pixel holds (diffusion capped at 0.1 per neighbour), or clamping negatives creates pigment and the picture turns black.
- Water must never make paper damp in proportion to a thin film while thin films can also push onto dry paper: the wet area then creeps without end and evaporates in seconds.
- The headless test browser draws with the processor at about 8 frames a second, so wet paint runs in slow motion there; judge the look with __cb.fast(seconds), and give watercolour tests long waits.
- Never mix paint with the paper's white through Mixbox: Mixbox treats white as a pigment, so thin paint turns pastel (red goes pink). Paint over paper or dry paint uses Kubelka-Munk; Mixbox only between wet paints.
- Brush rates per dab must use 1 - exp(-rate): with the big brush sizes a linear rate exceeds 1 and takes more paint than there is.
- A tap on a colour gives a full brush; holding goes round a third, two thirds, full (0.5 s steps); hold(q, 'color-N', 1.6) is also full. Sizes, brushes and softness are in popups: the flows' tap() opens the popup first.
- Undo of old steps is asynchronous (they come back from compressed memory); undo presses are queued, never dropped. Waking the water simulation after an undo only when that step had wet paint, or undo crawls.
- Acrylic and the oil pastel (crayon) keep the paint's own colour (PIC) and what is under it (UNDER, with the coat's thickness in its alpha); everything else (simple, marker, watercolour) must write the same colour into both, or the coat shows old colours.
- The undo store and its spill to memory cover every state texture (STATES); adding a picture texture means adding it there.
- Coolors pages are drawn by script: read them through the cloud browser's page snapshot, not WebFetch.
- Never put a // comment in the middle of a one-line object literal when patching: it silently comments out the rest of the line (a stroke lost its colour and nothing painted).
- A picture's palette from plain cluster averages comes out beige and misses small bright parts: use the more colourful half of each group and weigh colourfulness.

- Brush popup marks are real strokes painted by tools/previews.py (lib/previews, under 2 minutes): rerun it after any change to how a tool, brush or canvas looks, or the popup shows the old look.
- Wet paint is worked only on runs of wet tiles (waterRuns), never the box around all wet places; any new water pass goes over those runs, and the flow is computed one pixel past each run.
- Only number entries of K become shader constants; lists (like CRAY_PRESS) stay in the script.
- Marker and simple lay one coverage per stroke over the colour from before the stroke (MISC g/b, B0). The crayon is an oil pastel on the acrylic brush model (MED.crayon, REACH for the grain); the OIL_ constants are the pastel's (no oil tool). Look at crayon strokes at full size before sending: numbers passed while it painted fish scales.
- Flows pick colours by their place in the Basic palette (6 is blue); if the Basic palette changes, change the places in the flows, never what they check.
- The undo room spills old steps to memory ahead of time while nobody paints (keepRoom); a step read back while he paints made strokes lag and show late.
- Never put a // comment inside a GLSL template line either: it comments out the rest of the shader line and the page never becomes ready.
