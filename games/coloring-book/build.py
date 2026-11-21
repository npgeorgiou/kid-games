#!/usr/bin/env python3
"""Build src/index.html into one self-contained coloring-book.html.
Inlines lib/mixbox (pigment mixing shader and its lookup picture, CC BY-NC 4.0, Secret Weapons) and the
lib/phosphor icons (MIT, Phosphor Icons) and the lib/coolors palettes (coolors.co) where src has the markers /*%MIXBOX_GLSL%*/'', %MIXBOX_LUT% /*%ICONS%*/{} and /*%COOLORS%*/[]."""
import base64, json, pathlib, re
here = pathlib.Path(__file__).resolve().parent
out = (here / "src" / "index.html").read_text(encoding="utf-8")
glsl = (here / "lib" / "mixbox" / "mixbox.glsl").read_text(encoding="utf-8")
lut = base64.b64encode((here / "lib" / "mixbox" / "mixbox_lut.png").read_bytes()).decode()
icons = {}
for f in sorted((here / "lib" / "phosphor").glob("*-fill.svg")):
    icons[f.name[:-len("-fill.svg")]] = re.search(r'<path d="([^"]+)"', f.read_text()).group(1)
out = out.replace("/*%MIXBOX_GLSL%*/''", json.dumps(glsl)).replace("%MIXBOX_LUT%", "data:image/png;base64," + lut).replace("/*%ICONS%*/{}", json.dumps(icons))
pals = []
for line in (here / "lib" / "coolors" / "palettes.txt").read_text().splitlines():
    if not line.strip() or line.startswith("#"): continue
    grp = line[0] if line[:2] in ("c ", "s ", "f ") else ""; name, hx = [t.strip() for t in (line[2:] if grp else line).split("|")]
    pals.append({"name": name, "hex": " ".join(hx.split()), "grp": grp})
out = out.replace("/*%COOLORS%*/[]", json.dumps(pals))
prev = {f.stem: json.loads(f.read_text()) for f in sorted((here / "lib" / "previews").glob("*.json"))}  # brush previews, made by tools/previews.py
out = out.replace("/*%PREVIEWS%*/{}", json.dumps(prev))
(here / "coloring-book.html").write_text(out, encoding="utf-8")
print("wrote coloring-book.html", len(out), "bytes")
