#!/usr/bin/env python3
"""Build src/index.html into one self-contained oi-apoikoi.html: the hand pictures in src/hands/ go in as data, in place of the HANDS marker;
the land, material and other pictures in art/lands/, art/materials/ and art/things/ (svg or png) and the sea pictures used (SEA) in art/sea/, in place of the ART marker."""
import pathlib, json, base64
here = pathlib.Path(__file__).resolve().parent
SEA = 'water-c'  # the water colour used (built for now)
data = lambda p, kind: 'data:%s;base64,' % kind + base64.b64encode(p.read_bytes()).decode()
hands = {p.stem: data(p, 'image/svg+xml') for p in sorted((here / "src" / "hands").glob("*.svg"))}
KIND = {'.svg': 'image/svg+xml', '.png': 'image/png'}
art = {'%s/%s' % (p.parent.name, p.stem): data(p, KIND[p.suffix]) for d in ('lands', 'materials', 'things') for p in sorted((here / "art" / d).iterdir()) if p.suffix in KIND}
art['sea'] = data(here / "art" / "sea" / (SEA + ".png"), 'image/png')
out = (here / "src" / "index.html").read_text(encoding="utf-8").replace("/*HANDS*/{}", json.dumps(hands)).replace("/*ART*/{}", json.dumps(art))
(here / "oi-apoikoi.html").write_text(out, encoding="utf-8")
print("wrote oi-apoikoi.html", len(out), "bytes")
