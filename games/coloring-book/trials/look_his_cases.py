# A trial scene, painted straight through the trial's own stroke code; writes its picture to the system temp folder.
import pathlib, tempfile
HERE = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir())
import math, random
from playwright.sync_api import sync_playwright
random.seed(5)
def st(q,c,s,pts):
    q.evaluate("([c,s,x,y])=>{__trial.set(c,s);__trial.start(x,y)}",[c,s,*pts[0]])
    for p in pts[1:]: q.evaluate("([x,y])=>__trial.move(x,y)",p)
    q.evaluate("()=>__trial.end()")
def line(a,b):
    n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])/5)); return [(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
def poly(ps):
    o=[]
    for a,b in zip(ps,ps[1:]): o+=line(a,b)[:-1]
    return o+[ps[-1]]
with sync_playwright() as p:
    b=p.chromium.launch(); q=b.new_page(viewport={'width':1360,'height':800}); q.goto('file://'+str(HERE/'acrylic-trial.html')+''); q.wait_for_function('()=>window.__ready')
    # 1. his spiral: one long stroke, green, size L, until the brush is empty
    sp=[]; x0,y0,x1,y1=20,20,470,370
    while x1-x0>60: sp+= [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]; x0+=40;y0+=40;x1-=40;y1-=40
    st(q,6,22,poly([(20,20)]+sp))
    # 2. his zigzags: yellow, then blue overlapping, then the brush through both
    zz=lambda xa,xb,n: [(xa+(xb-xa)*k/n, 420 if k%2==0 else 740) for k in range(n+1)]
    st(q,5,22,poly(zz(520,760,8))); st(q,2,22,poly(zz(680,960,9))); st(q,2,30,poly([(520,700),(700,600),(800,560),(980,470)]))
    # 3. his blob: a blue scribble, then yellow scribbled into it while wet: expect green
    bl=[(150+80*math.cos(a)*(0.3+0.7*(a%1)),580+60*math.sin(a*1.3)) for a in [k*0.35 for k in range(60)]]
    st(q,2,40,poly(bl)); ye=[(160+40*math.cos(a*1.7),580+30*math.sin(a*2.3)) for a in [k*0.3 for k in range(70)]]
    st(q,5,16,poly(ye))
    q.screenshot(path=str(OUT/'t3.png'), clip={'x':12,'y':12,'width':1000,'height':760}); b.close()
