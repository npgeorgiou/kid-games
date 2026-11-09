#!/usr/bin/env python3
"""Inline local scripts from src/index.html into one self-contained tower-builder.html."""
import re, pathlib
here = pathlib.Path(__file__).resolve().parent
src = (here / "src" / "index.html").read_text(encoding="utf-8")
def inline(m):
    js = (here / "src" / m.group(1)).resolve().read_text(encoding="utf-8")
    return "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>"
out = re.sub(r'<script src="([^"]+)"></script>', inline, src)
(here / "tower-builder.html").write_text(out, encoding="utf-8")
print("wrote tower-builder.html", len(out), "bytes")
