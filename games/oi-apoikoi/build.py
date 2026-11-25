#!/usr/bin/env python3
"""Build src/index.html into one self-contained oi-apoikoi.html: the hand pictures in src/hands/ go in as data, in place of the HANDS marker;
the land and material pictures in art/lands/ and art/materials/ and the sea pictures used (SEA) in art/sea/, in place of the ART marker."""
import pathlib, json, base64
here = pathlib.Path(__file__).resolve().parent
SEA = 'water-c'  # the water colour used (built for now)
data = lambda p, kind: 'data:%s;base64,' % kind + base64.b64encode(p.read_bytes()).decode()
hands = {p.stem: data(p, 'image/svg+xml') for p in sorted((here / "src" / "hands").glob("*.svg"))}
art = {'%s/%s' % (p.parent.name, p.stem): data(p, 'image/svg+xml') for d in ('lands', 'materials') for p in sorted((here / "art" / d).glob("*.svg"))}
art['sea'] = data(here / "art" / "sea" / (SEA + ".png"), 'image/png')
out = (here / "src" / "index.html").read_text(encoding="utf-8").replace("/*HANDS*/{}", json.dumps(hands)).replace("/*ART*/{}", json.dumps(art))
(here / "oi-apoikoi.html").write_text(out, encoding="utf-8")
print("wrote oi-apoikoi.html", len(out), "bytes")
