#!/usr/bin/env python3
# Builds trials/acrylic-trial.html (one file) from acrylic-trial.src.html: his reference picture beside the paper, and the Mixbox table (lib/mixbox) as raw RGB bytes.
import base64, pathlib, re, subprocess, sys, tempfile
import numpy as np
from PIL import Image
here = pathlib.Path(__file__).resolve().parent; game = here.parent
s = (here / 'acrylic-trial.src.html').read_text()
ref = Image.open(game / 'owner-shots' / '2026-11-25-acrylic-blue-strokes.jpg').convert('RGB'); ref.thumbnail((520, 520))
import io; buf = io.BytesIO(); ref.save(buf, 'JPEG', quality=80)
s = s.replace('%REF%', 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode())
a = np.array(Image.open(game / 'lib' / 'mixbox' / 'mixbox_lut.png'))[..., :3]  # its alpha is not part of the table
if a[0, 0, 2] < 25.5: a = a[::-1]  # the shader's own check: row 0 as the shader reads it
s = s.replace('%LOADS%', re.search(r'const LOADS = (\[[^\]]*\])', (game / 'src' / 'index.html').read_text()).group(1))  # the game's paint amounts, one owner
s = s.replace('%LUTRGB%', base64.b64encode(a.tobytes()).decode())
js = re.search(r'<script>(.*)</script>', s, re.S).group(1)  # many statements share a line: a comment in the middle swallows the code after it, so the script is syntax-checked before the page is written
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f: f.write(js)
chk = subprocess.run(['node', '--check', f.name], capture_output=True, text=True)
if chk.returncode: sys.exit('script does not parse:\n' + chk.stderr[-600:])
(here / 'acrylic-trial.html').write_text(s); print('built trials/acrylic-trial.html')
