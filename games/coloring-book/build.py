#!/usr/bin/env python3
"""Copy src/index.html into one self-contained coloring-book.html (no shared code or assets yet)."""
import pathlib
here = pathlib.Path(__file__).resolve().parent
out = (here / "src" / "index.html").read_text(encoding="utf-8")
(here / "coloring-book.html").write_text(out, encoding="utf-8")
print("wrote coloring-book.html", len(out), "bytes")
