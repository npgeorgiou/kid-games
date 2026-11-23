# Saves every brush's normal stroke as tools/looks/<tool>-<brush>.png, the pictures the brush_looks flow compares against.
# Run it only when a brush's look was meant to change (and say so in the commit): python3 tools/looks.py
import sys, pathlib, subprocess
here = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(here / "tools"))
import flows
from playwright.sync_api import sync_playwright
subprocess.run([sys.executable, str(here / "build.py")], check=True, stdout=subprocess.DEVNULL)
flows.LOOKS.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); q = flows.page(b, '1600x1000')
    pics = flows.brush_strokes(q)
    for k, im in pics.items(): im.save(flows.LOOKS / (k + '.png'))
    print(len(pics), 'looks saved'); b.close()
