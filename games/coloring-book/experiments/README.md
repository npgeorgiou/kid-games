# Brush experiments: Krita's brushes

New brushes for the coloring book are built here first, one at a time, copying Krita's own brush presets (Krita 4 bundle), then moved into the game.

## Brushes we make (owner, 26 Nov)

The Krita families below, each with its own presets. Blender, Basics, Inking and the rest are out.

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
| `brushes.html` | **The brushes page.** Built by `build.py`; never edit it by hand. Premade brushes for the game's tools (a button each sets a preset and its sliders), then every Krita family and preset; Krita's picture of the chosen preset; a paper as big as the window allows; the picture's colours and colours to mix; the everyday settings with "Like the picture"; picture, grey or white paper. |
| `build.py` | Inlines the core, each family's presets, its Krita picture (where each preset's strip is in it) and the tips and textures the presets name into `brushes.html`. The game's `build.py` runs it. |
| `src/brush-core.js` | The shared core, ported from Krita's code: the freehand tool (no smoothing: straight from finger point to finger point; basic smoothing bent lines off the finger's path on a touchscreen), dab spacing and airbrush timing, fan corners, the pixel brush (Krita's mask generators and image pyramid, sub-pixel dabs and the dab cache's precision, sensors and curves, rotation, ratio, scatter, mirror, softness, textures, build-up and wash with average opacity, erase, masking brush), the colour smudge engine (legacy mask strategy, its colours mixed as pigment through Mixbox instead of Krita's RGB) and the spray engine (its distributions). |
| `src/brushes.html` | The brushes page's source. |
| `krita/presets/` | Every preset of the families above, read from Krita's bundle: one setting per line (`name = value`; pressure curves on one line as `x,y;` points). |
| `krita/tips/` | The brush tips the presets name (Krita `.gbr`, `.gih` animated tips, `.png`, `.svg`). |
| `krita/picture-strength.txt` | The strength (pen pressure) each preset opens at: what its picture shows, chosen by eye. |
| `krita/picture-palettes.txt` | Each preset's colours in its strip of Krita's picture, the paper first; made by `tools/picture_palettes.py`. |
| `krita/patterns/` | The paper textures the presets name (taken out of the presets, where Krita keeps them). |
| `references/krita/` | The pictures of each family from the Krita manual page (docs.krita.org, Krita 4 Preset Bundle Overview; GNU FDL 1.3+). |
| `vendor/spectral/` | Spectral.js and its shader (`LICENSE`: MIT). |
| `tools/picture_palettes.py` | Makes `krita/picture-palettes.txt` from Krita's pictures (needs Pillow). |
| `tools/kpp.py` | Reads Krita presets (`.kpp`) into `krita/presets/`, `krita/tips/`, `krita/patterns/`. |
| `tools/get_krita.sh` | Fetches Krita's source (GPL) for the brush engines and the preset bundle, at the commit these presets come from, into the temp folder. |

Tests: the `kb_` flows in `../tools/flows.py` (section KRITA BRUSHES): presets' numbers, eraser strokes, settings, premade brushes and the page's room, wet mixing, long strokes (time and memory), lines only where the finger went (moves as his touchscreen sends them), the painting time of a frame.

To read the presets again: `sh tools/get_krita.sh`, unzip `krita/data/bundles/Krita_4_Default_Resources.bundle` from it into a folder, then `python3 tools/kpp.py <folder>/paintoppresets/<presets>.kpp --out krita/presets --bundle <folder>`.

Krita is GPL: code ported from it keeps that licence.
