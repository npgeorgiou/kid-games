# A trial scene, painted straight through the trial's own stroke code; writes its picture to the system temp folder.
import pathlib, tempfile
HERE = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir())
import random, math, sys
from playwright.sync_api import sync_playwright
from PIL import Image
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 3)
with sync_playwright() as p:
    b=p.chromium.launch(); q=b.new_page(viewport={'width':1360,'height':800}); q.goto('file://'+str(HERE/'acrylic-trial.html')+''); q.wait_for_function('()=>window.__ready')
    errs=[]; q.on('pageerror', lambda e: errs.append(str(e)))
    for k in range(46):
        x=random.uniform(130,870); c=random.choice([0,0,1,1,1,1,2,2,2,3]); s=random.choice([22,30,40])
        y0=random.uniform(60,200); y1=random.uniform(450,700); ph=random.uniform(0,6)
        q.evaluate("([c,s,x,y])=>{__trial.set(c,s);__trial.start(x,y)}",[c,s,x+5*math.sin(ph),y0])
        n=int((y1-y0)/5)
        for i in range(1,n+1): q.evaluate("([x,y])=>__trial.move(x,y)",[x+5*math.sin(i/12+ph), y0+i*5])
        q.evaluate("()=>__trial.end()")
    q.screenshot(path=str(OUT/'t.png'), clip={'x':12,'y':12,'width':1000,'height':760}); print(errs); b.close()
a=Image.open(str(OUT/'t.png')).convert('RGB'); r=Image.open(HERE.parent/'owner-shots'/'2026-11-25-acrylic-blue-strokes.jpg').convert('RGB').resize((760,760))
c=Image.new('RGB',(1760,760),'white'); c.paste(a,(0,0)); c.paste(r,(1000,0)); c.save(str(OUT/'cmp.png'))
a.crop((300,200,700,500)).resize((600,450)).save(str(OUT/'zoom.png'))
