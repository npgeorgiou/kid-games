# Tower Builder: design sheet

Approved 2026-11-09. Mechanics are the brief's (lines 141-168) unless marked "new".

| Row | Content |
|---|---|
| Pitch | You are a master builder of the ancient world. In a pile beside you are stone and wood pieces: blocks, columns, beams and round drums. You drag them out and stack them. They are heavy and behave like the real thing: place one badly and it wobbles, slides off, or brings everything down. Each level is one famous building, shown as a faint outline: build inside it. When you think it is ready you press the big button: the wind blows, then the building's own load is lowered on (a statue, roof slabs, a relief), then the earth shakes. Still standing: the monument goes onto the world map and the next site opens. If it falls, you watch it fall, the pieces go back to the pile, and you try again. Later buildings need wooden supports while you build, pulled out before the test. There is also free play with no job. |
| Fantasy | I am the master builder. What I build stands because I built it well. |
| Toy | Dragging heavy stone pieces, dropping them, and watching them thud, wobble and topple. Knocking a tower down must be as satisfying as building it. |
| Seconds loop | Pick a piece from the tray, place it, watch it settle. |
| Minutes loop | See the outline of the building. Build inside it; the check is forgiving (mostly filled, nothing far outside, openings kept clear). Press test: wind, then the load is lowered on, then an earthquake. If it stands, the site celebrates and the monument goes on the map. If it falls, the player watches it fall, the pieces return, and you rebuild. |
| Days loop | New (decided): a world map of the Mediterranean and the Middle East is the start screen. Ten sites, played one by one in chronological order, each harder and adding one new demand: 1 Mastaba, Saqqara (c. 3000 BC): a wide solid mass. 2 Step pyramid of Djoser, Saqqara (c. 2650 BC): tall steps. 3 Ziggurat of Ur (c. 2100 BC): wood courses inside the stone. 4 Karnak hypostyle hall (c. 1290-1220 BC): beams across gaps. 5 Lion Gate, Mycenae (c. 1250 BC): overhanging stones held by weight. 6 Ishtar Gate, Babylon (c. 575 BC): a wedge-stone arch on wooden supports. 7 Parthenon front, Athens (447-432 BC): a long row of columns, a pediment, statues. 8 Mausoleum of Halicarnassus (c. 350 BC): a heavy stepped roof on columns. 9 Lighthouse of Alexandria (c. 280 BC): very tall, strong wind. 10 Valens Aqueduct, Constantinople (AD 368): two tiers of arches. Outlines, loads and wood are in src/levels.js. Each finished monument stands on its site for good. |
| Mechanics | Pile of stone and wood pieces (block, column, beam, drum, wedge; new: wedge stones for arches) with shape and weight (stone about 4.5 times as heavy as wood); drag to place; gravity and collision; move or remove freely before the test. New (decided): the test per level is wind, then that building's load lowered on, then an earthquake, all stronger at later levels. Pass: after the test the outline is still mostly filled and the load is still in place. Wooden supports are pulled out first, as part of the test. Impacts: dust where a piece hits the ground, stone chips where stone hits stone, a small shake for heavy stone. A free-build mode with no job. |
| Dynamics | A wide base beats a narrow one. Weight high up is risky. Balance matters. With few pieces, height trades against stability. Several designs can pass the same brief. |
| Kinds of fun | Sensation (weight, thud, wobble), challenge (make it stand), expression (my design), discovery (finding what holds). Not narrative, not fellowship. |
| Competence | The result visibly follows from the player's own choices, and the collapse happens in plain view, so the fall itself is the explanation. No "weak point" marker: there is often no single one. |
| Autonomy | There is no single correct tower, and free-build has no goal. |
| Relatedness | A finished building is something to show a parent. |
| Mastery | Optional goals from the brief (fewer pieces, taller), shown as symbols, not numbers. New (decided): building techniques the levels may demand, chosen per level from its outline: staggered joints, overhangs held by weight, side supports, wood beams inside stone walls, heavy low and light high, two beams bridging a gap. |
| What would kill the fun | Pieces landing where the player did not intend. Physics jitter toppling a sound tower. A slow test. A collapse that feels like punishment. Levels with only one solution. |
| Prototype must answer | Does the child stack and topple happily for five minutes with no goal? Can they place a piece where they mean to, by touch and by mouse? Do they see why it fell? Do they ask to go again? |

## Prototype decisions

- Physics is live while building: pieces fall and wobble the moment they are released.
- No rotation. The pile offers the same piece upright and lying down.
- Pieces: broad block, narrow column, long beam, round drum.
- Free play only: no jobs, no art, no sound, no text.

New, decided during prototype testing with the child (not from the brief):

- The tray is a sidebar down one side of the screen, not a strip across the bottom. A piece is dragged straight out of its sidebar button; nothing spawns automatically ahead of the drag.
- Two materials, wood and stone, chosen per piece from two buttons above the tray. Stone is harder to pick up fast and harder to spin than wood — the weight has to be felt in the hand, not just read off a label.
- Grabbing the middle third of a piece carries it with no tilt. Grabbing nearer an edge tilts it like a real lever.
- A held piece tracks the hand exactly: no delay, no sliding start, no drift if the hand stops. It only tilts from an edge grab, never from being carried.
