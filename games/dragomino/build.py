#!/usr/bin/env python3
"""Build src/index.html into one self-contained dragomino.html (no libraries yet)."""
import pathlib
here = pathlib.Path(__file__).resolve().parent
out = (here / "src" / "index.html").read_text(encoding="utf-8")
(here / "dragomino.html").write_text(out, encoding="utf-8")
print("wrote dragomino.html", len(out), "bytes")
