# Physics, shared by every game

Planck.js (in each game's `lib/`) moves the bodies; these files are the models on top of it, first built for Tower Builder. A game includes them inside its own script with `// @include ../../../tools/physics/<file>.js` lines in `src/index.html`; its build puts the files in their place. Each file starts with what it does and what the game must provide.

| File | What it is |
|---|---|
| `step.js` | The steady clock: the world moves in fixed steps (`STEP`), whatever the frame rate. The game adds its own work for each step to `physicsBefore` and `physicsAfter`. `damp`: nearly still bodies settle instead of trembling. |
| `hand.js` | The hand: a piece held by the finger, carried by an arm with a strength (it lifts its weight first, moves with what is left), slowing before it touches things, and a wrist that holds a piece level when grabbed near its middle and lets it swing when grabbed near an end. |
| `contact.js` | How fast two bodies were closing when they touched (a real knock, not the weight of a resting stack), and a body's weight counted in its material's regular block (`REGULAR_BLOCK`): equal weights behave alike whatever their shapes. |
| `loads.js` | What rests on what: each piece's own weight plus its share of what is above it, balanced between what holds it up. |
| `breaking.js` | Materials that break: a material marked `crumbles` gives way under too much weight or a hard knock; a piece with `canSnap` breaks when bent too far across a gap; an overload must last a moment first. What breaking looks and sounds like is the game's (`crumble`, `snapWood`). |

Its numbers (arm strength, grip, friction of the materials) were set with the owner for Tower Builder; another game may give its own, with the owner's yes.
