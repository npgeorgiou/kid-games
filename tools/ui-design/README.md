# UI design guidelines

Read this before designing or changing anything a player sees or hears, in any game here. Follow it. When a screen is done, go through the checklist at the end.

The player is a four-year-old who cannot read, on a touchscreen. The screen is the whole game for him: what is not visible, audible and clear does not exist.

## 1. The five qualities

Every screen must be all of these at once:

- **Interactive.** Everything he can touch looks touchable and answers at once. What he cannot touch looks still.
- **Informing.** At any moment he can see whose turn it is, what he has, what just happened and why.
- **Harmonious.** One visual language: one palette, one set of shapes, one spacing scale, one family of sounds and one way of moving.
- **Pleasing.** Soft, warm, rounded and calm. Effects are rewards, not noise.
- **Easily parsable.** One glance tells him what belongs together, what matters most and where to look.

## 2. Layout and grouping (how the eye groups things)

- **Proximity decides groups.** Things that belong together sit close. Things that don't have clear space between them. Proximity is the strongest grouping cue, stronger than colour or shape. Give every element its own space, with a margin around it. Groups are separated by more space than the items inside a group.
- **Common region.** A shared background or tray means "these belong together": one player's things, one bonus, one choice. Prefer a soft tinted area or a shadow to a hard outline. Borders are the last tool, not the first.
- **Similarity.** Things that work the same look the same: every jar like every jar, every coin like every coin. A thing that looks different must be different.
- **Hierarchy.** Decide what he must see first, second and third on each screen, then make it so with size, contrast, position and motion. Only one thing at a time is the most important, and it is where his eyes already are.
- **Show where the action is.** Put information where his attention already is (on the board, at the piece he moved), not in corners. Information in a far corner is missed.
- **Spacing scale.** Use a few fixed spacing steps (for example 8, 16, 24, 32, 48 px at the target size) and never values in between. Start with too much space, then remove it.
- **Nothing unexplained.** Every shape on screen must mean something he can learn. A line, mark or frame that means nothing to him is removed.
- **Don't hide what matters.** All public game state is visible on the main screen, never behind a menu or a popup.

## 3. Player areas and turns

- **One player, one place.** Each player's things (land, goods, jars, coins, tokens) live in one area that is clearly his: his colour as a soft background tint, his figure or face at its head. Both areas use the same design, so learning one teaches the other.
- **Show amounts as things.** Goods, jars and coins are shown as the objects themselves, arranged so that amounts compare at a glance: rows or stacks of equal-sized items, never a heap and never a number.
- **Whose turn it is is unmistakable.** The active player's area is lit and lifted (brighter, a soft glow, slightly larger); the other is dimmed. Changing turns is an event, seen and heard: the light moves over, with a short sound.
- **The other player is a person.** Everything the opponent does is shown slowly and in full, the way a person across the table would do it, so he can follow it.
- **Phases are events.** A new round, the end of a round and the end of the game each get their own short, unmistakable moment: the screen changes mood (a light sweep, a banner picture, a pause) with its own sound, so he knows something different is happening now.

## 4. Feedback (signs and responses)

- **Every action answers, seen and heard.** A touch gives an instant visual and sound response. Sound never carries meaning alone, because the sound may be off.
- **Cause and effect are visibly linked.** A reward comes out of what earned it: it appears at the place that caused it and travels to where it goes. Nothing appears from nowhere, and nothing vanishes without being seen to go.
- **Show the possible.** While something is being dragged, show where it can go. Things he can't use look quiet (greyed but still recognisable) and don't answer as if usable.
- **Forgiveness.** A choice can be undone until it is committed: a picked-up piece can be put back where it came from. Wrong touches cost nothing.
- **States are consistent.** Each kind of element has the same few states everywhere (ready, active, used, unavailable) and each state looks the same in every game.

## 5. Motion

Based on Disney's twelve principles of animation, as applied to interfaces:

- **Slow in, slow out.** Nothing starts or stops at full speed. Use easing curves, never linear motion: a spinning wheel winds down, a flying piece slows as it lands.
- **Anticipation and follow-through.** A small wind-up before a big move, and a small overshoot and settle after it, make moves readable and alive.
- **Staging.** One motion at a time where it matters, so the eye knows where to look. Things that happen in sequence (one jar, then the next) are shown in sequence, never all at once.
- **Timing carries meaning.** Small things are quick (about 150–300 ms); events he must follow are slower (about 0.5–1.5 s). Don't make him wait for decoration.
- **Juice serves information.** Particles, a glow, a squash and stretch go on events that matter and say what happened. More effects are not better: too much feedback is noise that hides the game.

## 6. Sound

- **One family.** All sounds come from one sound palette (for example soft wooden and clay sounds for an ancient Greek setting), so they belong together.
- **Pleasant at the hundredth time.** Frequent sounds (a tap, a snap) are short (well under a second), soft, warm and never shrill or buzzy. A sound that is unpleasant on repeat is wrong.
- **Hierarchy.** Small actions get small sounds; big moments (a won jar, a slot win, the end of a round) get richer, longer ones.
- **Sounds match the thing.** A clay jar breaks when opened, a piece clicks when it snaps in, coins clink. A sound is chosen for what the object would really do.
- **Sound with sight.** Each sound starts exactly with its visual event.

## 7. For children who can't read

- **No text.** Pictures, shapes, colour, motion and sound carry everything. Text appears only where the owner asks for it.
- **Big targets.** Touch targets are at least about 2 cm across (Nielsen Norman Group; about 75 px is the guideline for screens), with space between them, so a resting hand or a rough tap hits the right one.
- **Simple gestures.** Tap and drag only. No double taps, pinches, long presses or multi-finger gestures.
- **Familiar pictures.** Use objects he knows from the world (a jar, a coin, a hand, a star) rather than abstract symbols.
- **Reward completion.** Finishing something is celebrated with a visual, animation and sound.

## 8. Visual style

- **A small palette.** A few base colours with light and dark steps, chosen once per game. Hierarchy comes from contrast and size more than from adding colours.
- **Depth by elevation.** A few fixed shadow levels: lifted things (the piece in hand, the active player's area, a popup) cast bigger shadows than things lying flat.
- **Rounded and solid.** Rounded corners, filled shapes, clear silhouettes that read at a glance.
- **Form follows function.** A thing's look tells what it does: a button looks pressable, a piece looks liftable, a jar looks breakable.

## Checklist for every screen

1. Can he tell whose turn it is from across the room?
2. Can he tell what each player has without counting carefully?
3. Does every action he makes get an instant picture and sound response?
4. Does every reward visibly come out of its cause?
5. Is every element separate, with its own space, and is every group clearly a group?
6. Is there anything on screen that means nothing to him? Remove it.
7. Is there any text? Remove it unless the owner asked for it.
8. Do all motions ease in and out, and happen one at a time where he must follow them?
9. Would every sound still be pleasant the hundredth time?
10. Are new rounds, round ends and the game's end each their own clear moment?

## Sources

- Nielsen Norman Group: [Proximity](https://www.nngroup.com/articles/gestalt-proximity/), [Common region](https://www.nngroup.com/articles/common-region/), [Children's UX: physical development](https://www.nngroup.com/articles/children-ux-physical-development/).
- Google, [Designing engaging apps for kids](https://developers.google.com/building-for-kids/designing-engaging-apps).
- Celia Hodent, *The Gamer's Brain* (signs and feedback, form follows function, putting information where attention is); [Creative Bloq interview](https://www.creativebloq.com/features/how-neuroscience-and-ux-impacts-video-game-design).
- Board Game Arena, [guidelines for digital board games](https://be.doc.boardgamearena.com/images/7/76/5-guidelines.pdf); Asmodee Digital, [Art direction and UI](https://doc.asmodee.net/art-and-ui).
- Frank Thomas and Ollie Johnston, *The Illusion of Life* (the twelve principles of animation); [Interaction Design Foundation on applying them to UI](https://ixdf.org/literature/article/ui-animation-how-to-apply-disney-s-12-principles-of-animation-to-ui-design).
- Martin Jonasson and Petri Purho, "Juice it or lose it" (GDC 2012); [Juice overload](https://www.wayline.io/blog/juice-overload-sensory-feedback-hurts-gameplay); [Slime Road: nothing appears out of nowhere](https://www.gamedeveloper.com/design/3-game-juice-techniques-from-slime-road).
- Adam Wathan and Steve Schoger, *Refactoring UI* (spacing scale, small palette, elevation shadows, fewer borders).
- Audio: [Audiokinetic, UI audio from a UI design perspective](https://www.audiokinetic.com/en/approaching-ui-audio-ui-design-perspective-2), [Microsoft sound guidelines](https://learn.microsoft.com/en-ie/Windows/Win32/uxguide/vis-sound), [UI sound design for indie games](https://bugnet.io/blog/ui-sound-design-for-indie-games), [Material Design sound](https://m2.material.io/design/sound/about-sound.html).
