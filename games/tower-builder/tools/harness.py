# Headless check of every level: quick build, then the full test (Tab override). One line per level.
# Usage: python3 tools/harness.py [level indexes]. Exposes internals via window.__tb (hook injected, rAF disabled, stepped manually).
# Extend this file in place for new checks; do not make new scratch harnesses.
import sys, json
from playwright.sync_api import sync_playwright
import os
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,'..','tower-builder.html')).read()
hook='''window.__tb={capApproach,render,startLevel,startAutoBuild,stepPhysics,cleanupOutOfBounds,updateCheck,runCheck,checkPasses,startTest,LEVELS,pileBodies,pieces,
get test(){return test},get auto(){return auto},get mode(){return mode},set mode(v){mode=v},setTab(v){tabDown=v},get loads(){return loads},get check(){return check},get failShow(){return failShow},progress};
window.requestAnimationFrame=()=>0;
'''
k=src.rindex('})();')
src=src[:k]+hook+src[k:]
open('/tmp/tb.html','w').write(src)
levels=[int(a) for a in sys.argv[1:]] or list(range(10))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':800})
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('file:///tmp/tb.html'); pg.wait_for_timeout(500)
    for i in levels:
        r=pg.evaluate('''(i)=>{const T=__tb; T.mode="build"; T.startLevel(i); T.startAutoBuild();
          const dt=1/60; let n=0; const run=(s)=>{for(let k=0;k<s*60;k++){T.stepPhysics(dt);T.cleanupOutOfBounds();T.updateCheck(dt);}};
          while(T.auto && n<60*200){run(1/60);n++;}
          run(2);
          const c=T.runCheck(), ok=T.checkPasses(c), left=T.pileBodies().map(b=>b.pileItem.defKey+'/'+b.pileItem.material);
          T.setTab(true); T.startTest(); T.setTab(false);
          let last='', phases=[]; let t=0;
          while(T.test && t<60*60){ if(T.test.phase!==last){last=T.test.phase;phases.push(last);} run(1/60); t++; if(T.test&&T.test.phase==='fail') break;}
          const fs=T.failShow; const res={lvl:T.LEVELS[i].key, ready:ok, fill:+c.fill.toFixed(3), far:c.far, hole:+c.hole.toFixed(3), wood:+c.wood.toFixed(2), load:c.load, phases:phases.join('>'),
            pass:!!T.progress.done[T.LEVELS[i].key], badLoads: fs?fs.loads.length:0, left};
          if(T.test){ run(4); } T.mode="map"; return res;}''', i)
        print(json.dumps(r))
    print('errors',errs[:5])
    b.close()
