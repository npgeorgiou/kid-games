# Headless check of every level: quick build, then the full test (Tab override). One line per level.
# Usage: python3 tools/harness.py [level indexes]. Exposes internals via window.__tb (hook injected, rAF disabled, stepped manually).
# Extend this file in place for new checks; do not make new scratch harnesses.
import sys, json
from playwright.sync_api import sync_playwright
import os
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,'..','tower-builder.html')).read()
hook='''window.__tb={renderMap,get groups(){return groups},get boats(){return boats},drawFeel,updateFeel,testTick,get grid(){return grid},inRing,cellOf,SOLUTIONS,fillPile,capApproach,render,startLevel,startAutoBuild,stepPhysics,cleanupOutOfBounds,updateCheck,runCheck,checkPasses,startTest,LEVELS,pileBodies,pieces,
get test(){return test},get auto(){return auto},get mode(){return mode},set mode(v){mode=v},setTab(v){tabDown=v},get loads(){return loads},get check(){return check},get failShow(){return failShow},progress};
window.requestAnimationFrame=()=>0;
'''
k=src.rindex('})();')
src=src[:k]+hook+src[k:]
open('/tmp/tb.html','w').write(src)
JIT='jitter' in sys.argv
# wrong choices that must fail (level index -> [(name, JS: entry -> new material or nothing)])
WRONG={0:[('wood top row','e=>e[3]===2.5&&"wood"')],
 1:[('mudbrick at the bottom','e=>e[3]===0.5?"mudbrick":e[3]>=3.5?"stone":0')],
 2:[('stone in the wood courses','e=>e[0]==="beam"&&"stone"')],
 3:[('mudbrick pillars','e=>e[0]==="block"&&e[4]!==0&&"mudbrick"')],
 4:[('mudbrick base','e=>e[3]===0.5&&"mudbrick"'),('wooden lintel','e=>e[0]==="beam"&&e[2]===0&&"wood"')],
 6:[('mudbrick top step','e=>e[0]==="block"&&e[3]===2.5&&"mudbrick"')],
 7:[('mudbrick podium top','e=>e[0]==="block"&&e[3]===2.5&&"mudbrick"')],
 8:[('mudbrick base','e=>e[3]===0.5&&"mudbrick"')],
 9:[('mudbrick piers','e=>e[0]==="block"&&e[3]===0.5&&"mudbrick"')]}
levels=[int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(10))
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':800})
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('file:///tmp/tb.html'); pg.wait_for_timeout(500)
    JS_SPEED='''(s)=>{const T=__tb; const run=(n)=>{for(let k=0;k<n;k++){T.stepPhysics(1/60);T.cleanupOutOfBounds();T.updateCheck(1/60);}};
      run(s*60); let mp=0,mw=0,np=0,nw=0; for(let k=0;k<60;k++){run(1);
      for(const b of T.pileBodies()){const v=b.getLinearVelocity(),sp=Math.hypot(v.x,v.y)+Math.abs(b.getAngularVelocity())*0.5; mp=Math.max(mp,sp); if(sp>0.05)np++;}
      for(const p of T.pieces){const b=p.body,v=b.getLinearVelocity(),sp=Math.hypot(v.x,v.y)+Math.abs(b.getAngularVelocity())*0.5; mw=Math.max(mw,sp); if(sp>0.05)nw++;}}
      return {pileMax:+mp.toFixed(3),pileMovingFrames:np,worldMax:+mw.toFixed(3),worldMovingFrames:nw};}'''
    for i in levels:
        if JIT:
            pg.evaluate('(i)=>{const T=__tb;T.mode="build";T.startLevel(i);}',i)
            print(i,'pile at start',[pg.evaluate(JS_SPEED,0) for _ in range(6)])
        for vname, vsrc in [('', '')] + WRONG.get(i, []):
          r=pg.evaluate('''([i,vsrc])=>{const T=__tb; T.mode="build"; delete T.progress.done[T.LEVELS[i].key]; T.startLevel(i);
          const key=T.LEVELS[i].key, orig=T.SOLUTIONS[key];
          if(vsrc){ const f=eval(vsrc); T.SOLUTIONS[key]=orig.map(e=>{const m=f(e); return m?[e[0],m,e[2],e[3],e[4]]:e;}); T.fillPile(T.SOLUTIONS[key].map(e=>({defKey:e[0],material:e[1]}))); }
          T.startAutoBuild(); T.SOLUTIONS[key]=orig;
          const dt=1/60; let n=0; const run=(s)=>{for(let k=0;k<s*60;k++){T.stepPhysics(dt);T.cleanupOutOfBounds();T.updateCheck(dt);}};
          while(T.auto && n<60*200){run(1/60);n++;}
          run(2);
          const c=T.runCheck(), ok=T.checkPasses(c), left=T.pileBodies().map(b=>b.pileItem.defKey+'/'+b.pileItem.material);
          T.setTab(true); T.startTest(); T.setTab(false);
          let last='', phases=[]; let t=0;
          while(T.test && t<60*60){ if(T.test.phase!==last){last=T.test.phase;phases.push(last);} run(1/60); t++; if(T.test&&T.test.phase==='fail') break;}
          const fs=T.failShow; const res={lvl:T.LEVELS[i].key, ready:ok, fill:+c.fill.toFixed(3), far:c.far, hole:+c.hole.toFixed(3), wood:+c.wood.toFixed(2), load:c.load, phases:phases.join('>'),
            pass:!!T.progress.done[T.LEVELS[i].key], badLoads: fs?fs.loads.length:0, left};
          if(T.test){ run(4); } T.mode="map"; return res;}''', [i, vsrc])
          if vname: r={'lvl':r['lvl'],'WRONG':vname,'ready':r['ready'],'phases':r['phases'],'pass':r['pass'],'fill':r['fill'],'hole':r['hole'],'wood':r['wood']}
          print(json.dumps(r))
        if JIT: print(i,'after test',pg.evaluate('(s)=>{__tb.mode="build";return 0}',0) or pg.evaluate(JS_SPEED,1))
    print('errors',errs[:5])
    b.close()
