# Brush experiments: Krita's brushes

New brushes for the coloring book are built here first, one at a time, copying Krita's own brush presets (Krita 4 bundle), then moved into the game.

## Brushes we make (owner, 26 Nov)

The Krita families below, each with its own presets. Blender and the rest are out; Basic and Ink come in if he says yes to the game brush set (Where we are).

| Family | Krita presets (`krita/presets/`) | Krita engine | Reference picture |
|---|---|---|---|
| Eraser | `a)_Eraser_*` (3) | pixel brush (`paintbrush`) | `references/krita/a-erasers.png` |
| Pencils | `c)_Pencil-*` (6) | pixel brush | `references/krita/c-pencils.png` |
| Markers | `e)_Marker_*` (3) | pixel brush | `references/krita/e-markers.png` |
| Dry Painting | `f)_*` (7) | pixel brush | `references/krita/f-dry-painting.png` |
| Dry Painting Textured | `g)_*` (4) | pixel brush | `references/krita/g-dry-painting-textured.png` |
| Chalk, Pastel and Charcoal | `h)_*` (6) | pixel brush | `references/krita/h-chalk-pastel-charcoal.png` |
| Wet painting | `i)_*` (8) | color smudge (`colorsmudge`) | `references/krita/i-wet-painting.png` |
| Watercolors | `j)_*` (4) | color smudge (1), pixel brush (3) | `references/krita/j-watercolors.png` |
| Stamps | `z)_Stamp_*` (13) | pixel brush (11), spray (2) | `references/krita/z-stamps.png` (shrunk; the page's picture is 900x2210) |

Order: Eraser, Markers, Pencils, Chalk/Pastel, Dry Painting, Dry Textured, Stamps, Wet painting, Watercolors.

## Where we are (28 Nov)

- **Done on the page** (branch `krita-brushes-port`, pull request 48, not merged: GitHub has run no checks on any branch since 26 Nov 14:31 UTC, so the merge waits; nothing to fix in the repo for it found yet):
  all nine families on ported code; a stroke goes straight from finger point to finger point (Krita's no smoothing; basic smoothing painted lines off the finger's path on his touchscreen); each preset owns its tip pictures (memory no longer grows); painting fast (wet brushes blend Mixbox latents in a float copy of the layer, tip pyramids made when a brush is chosen); everyday settings and strength (pen pressure, opens at the picture's strength); wet brushes carry a load of paint (Paint slider = bucket) that empties and takes up the paint that was under the brush before the stroke; premade brushes per game tool (buttons that set a preset and its sliders); each preset's picture palette; paper = empty layer over its colour.
- **Waiting for him:** (1) yes to the game brush set below; (2) which two markers darken where a stroke goes back over itself at lower opacity in his Krita (Chisel Smooth, Details or Dry). Krita's code as ported (wash mode: opacity applied when the stroke is merged, alpha darken within the stroke) does that only where flow is below 1; nobody here can run Krita.
- **Proposed game brush set** (his idea, 27-28 Nov): brush = tip and texture; bucket = strength (paint amount for wet brushes); each tool's popup has a strong row and a soft row with the same tips (soft: lower opacity and flow, softer edge on round tips, thinner paint on wet ones); softness only through the soft row; size on the game's size buttons and mouse wheel. Strong rows: acrylic flat wet, round wet, knife, flat dry, textured dry, thick / impasto; watercolour soft wash, hard wash, fringe, texture; oil pastel grainy, soft, detail; pencil hard, soft, side shade, charcoal; marker bullet, chisel, dry; simple = Krita Basic; ink = Krita Ink; stickers leaves, grass, hearts, sparkles, bokeh. The eraser goes unless the game gets one. Needs porting: Krita's Basic and Ink families (`Krita_4_Default_Resources.bundle`), and Thick paint / Impasto (`krita/data/bundles/RGBA_brushes.bundle` in Krita's source: `Basic_Wet_Thick_Paint_Brush.kpp` and friends; they use Krita's paint-thickness / lightness part, not ported yet).
- **Strokes not like their pictures** (from `tools/beside_pictures.py`): Pencil-3 Large 4B has fine grain where the picture's is coarse (texture `10_drawed_dotted.png` at scale 0.1, brightness 0.3: check the texture scale and brightness port); Marker Dry lays solid paint where the picture is streaky (rect tip, density 0.8, masking off). The rest look close at their picture strengths.
- **Not seen here:** his tab freezing and crashing with wet brushes and pencils; the stray lines were the likely cause (one move painted thousands of dabs). Ask him whether it still happens.

## How we work

1. **Krita's settings, not guesses.** Each brush starts from its preset's own numbers (`krita/presets/<name>.txt`), its own tip (`krita/tips/`) and texture (`krita/patterns/`), and Krita's engine code for how those numbers are used (`tools/get_krita.sh`). Nothing is invented; anything Krita does not say is tuned by eye.
2. **One shared core.** Krita's pixel brush is one engine: dabs of a tip stamped along the stroke (spacing, size, opacity, flow, rotation, scatter, each with its pressure/speed curve), multiplied by a paper texture. The color smudge engine adds picking up the canvas colour under each dab. Built once; a brush is a preset (numbers + tip + texture).
3. **Krita's code, not tuning.** Every part of a brush is ported from Krita's engine code. The page has only the everyday settings (owner 26 Nov): size, softness, opacity, flow and strength. No pen: the strength setting is the pen pressure of the whole stroke; tilt and the other pen sensors are left out. Each preset opens at the strength its picture shows (`krita/picture-strength.txt`, by eye); "Like the picture" goes back to it.
4. **Judged by eye, beside Krita's picture**, at the same scale. No similarity scores.
5. **One brush at a time, two rounds at most.** Still wrong after two: keep it as it is or drop it.
6. **Mixing** (wet painting, watercolour): Spectral.js (`vendor/spectral/`, MIT, pigment-like mixing; blue + yellow make green), or Mixbox (`../lib/mixbox/`, CC BY-NC).

## Where things are

| Path | What it is |
|---|---|
| `brushes.html` | **The brushes page.** Built by `build.py`; never edit it by hand. Premade brushes for the game's tools (a button each sets a preset and its sliders), then every Krita family and preset; Krita's picture of the chosen preset; a paper as big as the window allows; the picture's colours and colours to mix; the everyday settings and a Paint slider for wet brushes (the bucket), with "Like the picture"; picture or white paper (an empty layer over the paper's colour), or grey paper (grey paint, for the erasers). |
| `build.py` | Inlines the core, each family's presets, its Krita picture (where each preset's strip is in it) and the tips and textures the presets name into `brushes.html`. The game's `build.py` runs it. |
| `src/brush-core.js` | The shared core, ported from Krita's code: the freehand tool (no smoothing: straight from finger point to finger point; basic smoothing bent lines off the finger's path on a touchscreen), dab spacing and airbrush timing, fan corners, the pixel brush (Krita's mask generators and image pyramid, sub-pixel dabs and the dab cache's precision, sensors and curves, rotation, ratio, scatter, mirror, softness, textures, build-up and wash with average opacity, erase, masking brush), the colour smudge engine (legacy mask strategy, its colours mixed as pigment through Mixbox instead of Krita's RGB, and, in place of Krita's fresh paint at every dab, a load of paint on the brush that is used up and takes up the paint it passes over: the game's two-way paint transfer) and the spray engine (its distributions). |
| `src/brushes.html` | The brushes page's source. |
| `krita/presets/` | Every preset of the families above, read from Krita's bundle: one setting per line (`name = value`; pressure curves on one line as `x,y;` points). |
| `krita/tips/` | The brush tips the presets name (Krita `.gbr`, `.gih` animated tips, `.png`, `.svg`). |
| `krita/picture-strength.txt` | The strength (pen pressure) each preset opens at: what its picture shows, chosen by eye. |
| `krita/picture-palettes.txt` | Each preset's colours in its strip of Krita's picture, the paper first; made by `tools/picture_palettes.py`. |
| `krita/patterns/` | The paper textures the presets name (taken out of the presets, where Krita keeps them). |
| `references/krita/` | The pictures of each family from the Krita manual page (docs.krita.org, Krita 4 Preset Bundle Overview; GNU FDL 1.3+). |
| `vendor/spectral/` | Spectral.js and its shader (`LICENSE`: MIT). |
| `tools/picture_palettes.py` | Makes `krita/picture-palettes.txt` from Krita's pictures (needs Pillow). |
| `tools/beside_pictures.py` | Paints every preset of a family in its picture's colours under its strip of Krita's picture, into one image to judge by eye (`python3 tools/beside_pictures.py "Wet painting" out.png [strength]`). |
| `tools/kpp.py` | Reads Krita presets (`.kpp`) into `krita/presets/`, `krita/tips/`, `krita/patterns/`. |
| `tools/get_krita.sh` | Fetches Krita's source (GPL) for the brush engines and the preset bundle, at the commit these presets come from, into the temp folder. |

Tests: the `kb_` flows in `../tools/flows.py` (section KRITA BRUSHES): presets' numbers, eraser strokes, settings, premade brushes and the page's room, wet mixing, wet brushes carrying what they pick up, long strokes (time and memory), lines only where the finger went (moves as his touchscreen sends them), the painting time of a frame.

To read the presets again: `sh tools/get_krita.sh`, unzip `krita/data/bundles/Krita_4_Default_Resources.bundle` from it into a folder, then `python3 tools/kpp.py <folder>/paintoppresets/<presets>.kpp --out krita/presets --bundle <folder>`.

Krita is GPL: code ported from it keeps that licence.
