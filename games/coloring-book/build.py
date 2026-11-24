#!/usr/bin/env python3
"""Build src/index.html into one self-contained coloring-book.html.
Inlines lib/mixbox (pigment mixing shader and its lookup picture, CC BY-NC 4.0, Secret Weapons) and the
lib/phosphor icons (MIT, Phosphor Icons) and the lib/palettes palettes where src has the markers /*%MIXBOX_GLSL%*/'', %MIXBOX_LUT% /*%ICONS%*/{} and /*%PALETTES%*/[]."""
import sys, base64, json, pathlib, re
here = pathlib.Path(__file__).resolve().parent
out = (here / "src" / "index.html").read_text(encoding="utf-8")
glsl = (here / "lib" / "mixbox" / "mixbox.glsl").read_text(encoding="utf-8")
lut = base64.b64encode((here / "lib" / "mixbox" / "mixbox_lut.png").read_bytes()).decode()
icons = {}
for f in sorted((here / "lib" / "phosphor").glob("*-fill.svg")):
    icons[f.name[:-len("-fill.svg")]] = re.search(r'<path d="([^"]+)"', f.read_text()).group(1)
out = out.replace("/*%MIXBOX_GLSL%*/''", json.dumps(glsl)).replace("%MIXBOX_LUT%", "data:image/png;base64," + lut).replace("/*%ICONS%*/{}", json.dumps(icons))
sys.path.insert(0, str(here / "tools")); from palette_groups import GROUPS, group, oklch  # how many hues each extra shows, computed
pals, div, extras, first = [], False, [], False
for line in (here / "lib" / "palettes" / "palettes.txt").read_text().splitlines():
    if not line.strip() or line.startswith("#"): continue
    grp, rest = line[0], line[2:]  # its column in the palettes popup, or x: an extra
    if rest.strip() == "---": div = True; continue  # a divider line before the next palette
    name, hx = [t.strip() for t in rest.split("|")]
    p = {"name": name, "hex": " ".join(hx.split()), "grp": grp, "div": div and grp != "x"}; first = first or (div and grp == "x"); div = False  # a divider before the extras stays before the first one shown
    (extras if grp == "x" else pals).append(p)
extras.sort(key=lambda p: GROUPS.index(group(p["hex"].split())))  # one progression, two hues, three, many; the file's order within a group
if extras: extras[0]["div"] = first
for p in extras:  # a progression's stripes go darkest to lightest (owner 24 Nov 10:46)
    if group(p["hex"].split()) == "progression": p["hex"] = " ".join(sorted(p["hex"].split(), key=lambda h: oklch(h)[0]))
room = 12 - sum(p["grp"] == "2" for p in pals)  # what is left of column 2 after the rainbows
for k, p in enumerate(extras): p["grp"] = "2" if k < room else "3" if k < room + 12 else "4"
pals += extras
out = out.replace("/*%PALETTES%*/[]", json.dumps(pals))
prev = {f.stem: json.loads(f.read_text()) for f in sorted((here / "lib" / "previews").glob("*.json"))}  # brush previews, made by tools/previews.py
out = out.replace("/*%PREVIEWS%*/{}", json.dumps(prev))
(here / "coloring-book.html").write_text(out, encoding="utf-8")
print("wrote coloring-book.html", len(out), "bytes")
