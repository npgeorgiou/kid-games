# A trial scene, painted straight through the trial's own stroke code; writes its picture to the system temp folder.
import pathlib, tempfile
HERE = pathlib.Path(__file__).resolve().parent; OUT = pathlib.Path(tempfile.gettempdir())
import math
from playwright.sync_api import sync_playwright
def st(q,c,s,pts):
    q.evaluate("([c,s,x,y])=>{__trial.set(c,s);__trial.start(x,y)}",[c,s,*pts[0]])
    for p in pts[1:]: q.evaluate("([x,y])=>__trial.move(x,y)",p)
    q.evaluate("()=>__trial.end()")
def line(a,b):
    n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])/5)); return [(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
def zig(x0,x1,y,h,times):
    pts=[]
    for k in range(times): pts += line((x0,y+k*h/times),(x1,y+k*h/times)) if k%2==0 else line((x1,y+k*h/times),(x0,y+k*h/times))
    return pts
with sync_playwright() as p:
    b=p.chromium.launch(); q=b.new_page(viewport={'width':1360,'height':800}); q.goto('file://'+str(HERE/'acrylic-trial.html')+''); q.wait_for_function('()=>window.__ready')
    W=lambda s: q.evaluate("(s)=>__trial.wait(s)", s)
    # left: on DRY paint (blues, then a minute later navy and white across)
    for x in (70,150,230): st(q,1 if x!=150 else 2,36,line((x,40),(x,330)))
    W(90); st(q,0,30,line((30,120),(280,120))); st(q,3,30,line((30,250),(280,270))+line((280,270),(40,300)))
    # middle: the same on WET paint
    for x in (370,450,530): st(q,1 if x!=450 else 2,36,line((x,40),(x,330)))
    st(q,0,30,line((330,120),(580,120))); st(q,3,30,line((330,250),(580,270))+line((580,270),(340,300)))
    W(90)
    # right top: the same blue scrubbed back and forth; below it white scrubbed into wet blue
    st(q,1,36,zig(640,960,40,120,8))
    st(q,1,36,line((640,230),(960,230))); st(q,3,30,zig(640,960,200,70,6))
    W(90)
    # bottom: wet-into-wet horizontal bands, dark to light (like his blue gradient picture)
    for k,c in enumerate([0,0,1,1,2,2,3,3]):
        st(q,c,30,zig(40,960,400+k*42,10,3))
    st(q,5,36,line((640,320),(960,320))); st(q,1,36,line((640,350),(960,330)))  # yellow, then blue into it while wet: green
    q.screenshot(path=str(OUT/'t2.png'), clip={'x':12,'y':12,'width':1000,'height':760}); b.close()
