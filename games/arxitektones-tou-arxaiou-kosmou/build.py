#!/usr/bin/env python3
"""Inline local scripts, sounds and pictures from src/index.html into one self-contained arxitektones-tou-arxaiou-kosmou.html."""
import re, pathlib, json
here = pathlib.Path(__file__).resolve().parent
src = (here / "src" / "index.html").read_text(encoding="utf-8")
def inline(m):
    js = (here / "src" / m.group(1)).resolve().read_text(encoding="utf-8")
    return "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>"
out = re.sub(r'<script src="([^"]+)"></script>', inline, src)
# embed sounds and pictures referenced as "sounds/..." or "art/..." strings
import base64
MIME = {".mp3": "audio/mpeg", ".jpg": "image/jpeg", ".png": "image/png"}
def embed(m):
    f = here / "src" / m.group(1)
    return '"data:%s;base64,%s"' % (MIME[f.suffix], base64.b64encode(f.read_bytes()).decode())
out = re.sub(r'"((?:sounds|art)/[^"]+\.(?:mp3|jpg|png))"', embed, out)
# voice recordings (cues.md section 9): every src/sounds/voice/NN.mp3 that exists plays instead of line NN's text box
vf = {int(f.stem): "data:audio/mpeg;base64," + base64.b64encode(f.read_bytes()).decode() for f in sorted((here / "src" / "sounds" / "voice").glob("[0-9]*.mp3"))}
out = out.replace("const VOICE_FILES = {};", "const VOICE_FILES = " + json.dumps(vf) + ";", 1)
# and how long each recording lasts, so a line ends on the game's own clock (the same in a test as in play)
import subprocess
vs = {int(f.stem): round(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True, check=True).stdout), 3) for f in sorted((here / "src" / "sounds" / "voice").glob("[0-9]*.mp3"))}
out = out.replace("const VOICE_SECONDS = {};", "const VOICE_SECONDS = " + json.dumps(vs) + ";", 1)
# the cue table (cues.json, version A) goes into the game as it is
out = out.replace("const CUE_TABLE = null;", "const CUE_TABLE = " + json.dumps(json.loads((here / "cues.json").read_text(encoding="utf-8")), ensure_ascii=False) + ";", 1)
(here / "arxitektones-tou-arxaiou-kosmou.html").write_text(out, encoding="utf-8")
print("wrote arxitektones-tou-arxaiou-kosmou.html", len(out), "bytes")
