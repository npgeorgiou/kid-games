"""Paints every preset of one family in its picture's colours on its picture's paper, under its strip of Krita's picture, and saves one image to look at.
Usage: python3 tools/beside_pictures.py "Wet painting" out.png [strength 0..100, default each preset's own]. Needs Playwright and Pillow; build first."""
import io, math, sys, time, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image
PAGE = (pathlib.Path(__file__).resolve().parent.parent / 'brushes.html').as_uri()
family, out = sys.argv[1], sys.argv[2]; strength = sys.argv[3] if len(sys.argv) > 3 else None
with sync_playwright() as p:
    b = p.chromium.launch(); q = b.new_context(viewport={'width': 1280, 'height': 800}).new_page()
    q.goto(PAGE); q.wait_for_function("()=>window.__kb&&__kb.ready")
    q.evaluate("(n)=>[...document.querySelectorAll('#families button')].find(b=>b.textContent===n).click()", family)
    rows = []
    for pid in q.evaluate("(n)=>FAMILIES.find(f=>f.name===n).presets.map(p=>'p-'+p.id)", family):
        q.evaluate("(id)=>document.getElementById(id).click()", pid); q.evaluate("()=>document.getElementById('paperpic').click()")
        if strength: q.evaluate("(v)=>{const r=document.getElementById('s-strength');r.value=v;r.oninput()}", strength)
        cols = q.evaluate("""()=>{const b=[...document.querySelectorAll('#palette button')].map(b=>b.id.slice(2)),v=c=>[0,2,4].map(i=>parseInt(c.slice(i,i+2),16)),p=v(b[0]);
          return b.slice(1).filter(c=>{const x=v(c);return Math.hypot(x[0]-p[0],x[1]-p[1],x[2]-p[2])>70}).map(c=>'c-'+c)}""")  # the picture's colours that stand out from its paper
        for i, c in enumerate(cols[:4]):
            q.evaluate("(id)=>document.getElementById(id).click()", c); ox, oy = q.evaluate("()=>__kb.screenOf(0,0)")
            pts = [(150 + i * 170 + k * 5, 100 + 45 * math.sin(k / 7 + i)) for k in range(60)]
            q.mouse.move(ox + pts[0][0], oy + pts[0][1]); q.mouse.down()
            for x, y in pts[1:]: q.mouse.move(ox + x, oy + y)
            q.mouse.up()
        ox, oy = q.evaluate("()=>__kb.screenOf(0,0)")
        ref = Image.open(io.BytesIO(q.locator('#ref').screenshot())).crop((0, 0, 880, 150))
        pap = Image.open(io.BytesIO(q.screenshot(clip={'x': ox, 'y': oy + 25, 'width': 880, 'height': 150})))
        row = Image.new('RGB', (880, 300)); row.paste(ref, (0, 0)); row.paste(pap, (0, 150)); rows.append(row)
    img = Image.new('RGB', (880, 300 * len(rows))); [img.paste(r, (0, 300 * i)) for i, r in enumerate(rows)]
    img.save(out); print(len(rows), 'presets ->', out); b.close()
