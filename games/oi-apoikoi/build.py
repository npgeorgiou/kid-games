#!/usr/bin/env python3
"""Build src/index.html into one self-contained oi-apoikoi.html: the hand pictures in src/hands/ go in as data, in place of the HANDS marker."""
import pathlib, json, base64
here = pathlib.Path(__file__).resolve().parent
hands = {p.stem: 'data:image/svg+xml;base64,' + base64.b64encode(p.read_bytes()).decode() for p in sorted((here / "src" / "hands").glob("*.svg"))}
out = (here / "src" / "index.html").read_text(encoding="utf-8").replace("/*HANDS*/{}", json.dumps(hands))
(here / "oi-apoikoi.html").write_text(out, encoding="utf-8")
print("wrote oi-apoikoi.html", len(out), "bytes")
