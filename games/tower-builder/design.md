# Tower Builder: design sheet

Approved 2026-11-09. Mechanics are the brief's (lines 141-168) unless marked "new".

| Row | Content |
|---|---|
| Pitch | You are a builder in ancient Greece. At the bottom of the screen is a pile of stone pieces: blocks, columns, beams and round drums. You drag them up and stack them. They are heavy and behave like real stone: place one badly and it wobbles, slides off, or brings everything down. Each level is one building job, shown as a picture: build up to this line, or build something that can carry this statue. When you think it is ready you press the big button, and the wind blows or the statue is set on top. Still standing a few seconds later: you win and the next job opens. If it falls, you watch it fall, the pieces go back to the pile, and you try again. Later jobs give fewer pieces, sloping ground, stronger wind or a heavier statue. There is also free play with no job. |
| Fantasy | I am the master builder. What I build stands because I built it well. |
| Toy | Dragging heavy stone pieces, dropping them, and watching them thud, wobble and topple. Knocking a tower down must be as satisfying as building it. |
| Seconds loop | Pick a piece from the tray, place it, watch it settle. |
| Minutes loop | See the brief as a picture (a height line, or a statue to carry). Build. Press test: a gust blows or the load is lowered on. If it stands, the site celebrates. If it falls, the player watches it fall, the pieces return to the tray, and you rebuild. |
| Days loop | New sites open in order: quarry, acropolis, island lighthouse, Byzantine town. Each adds one new piece or condition. New: finished buildings stay visible on a site map. |
| Mechanics | Tray of pieces with shape and weight; drag to place; gravity and collision; move or remove freely before the test; later wind, uneven ground, limited pieces and loads. New: a free-build mode with no brief. |
| Dynamics | A wide base beats a narrow one. Weight high up is risky. Balance matters. With few pieces, height trades against stability. Several designs can pass the same brief. |
| Kinds of fun | Sensation (weight, thud, wobble), challenge (make it stand), expression (my design), discovery (finding what holds). Not narrative, not fellowship. |
| Competence | The result visibly follows from the player's own choices, and the collapse happens in plain view, so the fall itself is the explanation. No "weak point" marker: there is often no single one. |
| Autonomy | There is no single correct tower, and free-build has no goal. |
| Relatedness | A finished building is something to show a parent. |
| Mastery | Optional goals from the brief (fewer pieces, taller), shown as symbols, not numbers. |
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
