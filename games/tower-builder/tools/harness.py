# Headless check of every level: quick build, then the full test (Tab override). One line per level.
# Usage: python3 tools/harness.py [level indexes]. Exposes internals via window.__tb (hook injected, rAF disabled, stepped manually).
# Extend this file in place for new checks; do not make new scratch harnesses.
import sys, json
from playwright.sync_api import sync_playwright
import os
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,'..','tower-builder.html')).read()
hook='''window.__tb={renderMap,get groups(){return groups},get boats(){return boats},drawFeel,updateFeel,testTick,get grid(){return grid},inRing,cellOf,SOLUTIONS,fillPile,capApproach,render,startLevel,startAutoBuild,stepPhysics,cleanupOutOfBounds,updateCheck,runCheck,checkPasses,startTest,LEVELS,pileBodies,pieces,
get test(){return test},get auto(){return auto},get mode(){return mode},set mode(v){mode=v},setTab(v){tabDown=v},get loads(){return loads},get check(){return check},get failShow(){return failShow},progress,feelHits,spawnPiece,startHold,releaseHold,startPileHold,pilePoint,worldToPile,quiet0(){pileQuietUntil=0},get pileBinRect(){return pileBinRect},get pointers(){return pointers},get pileScale(){return pileScale}};
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
 4:[('mudbrick base','e=>e[3]===0.5&&"mudbrick"'),('mudbrick jambs','e=>e[0]==="block"&&e[4]!==0&&"mudbrick"')],
 6:[('mudbrick top step','e=>e[0]==="block"&&e[3]===2.5&&"mudbrick"')],
 7:[('mudbrick podium','e=>(e[0]==="block"||e[0]==="square")&&e[3]<2&&"mudbrick"')],
 8:[('mudbrick base','e=>e[3]===0.5&&"mudbrick"')],
 9:[('mudbrick piers','e=>e[0]==="block"&&e[3]===0.5&&"mudbrick"')]}
PROBE='probe' in sys.argv
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
    if 'sizes' in sys.argv:
        for vw,vh in [(1920,1080),(1366,768),(1536,864),(2560,1440),(1280,1024),(1024,768)]:
            pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(100)
            print(vw,vh,pg.evaluate('''()=>{const T=__tb;const out=[];for(let i=0;i<10;i++){T.mode="build";T.startLevel(i);T.quiet0&&T.quiet0();const run=(n)=>{for(let k=0;k<n;k++){T.stepPhysics(1/60);}};
              T.feelHits[1]=0;T.feelHits[2]=0;run(600);out.push(T.feelHits[1]+'/'+(T.feelHits[2]||0));}return out.join(' ');}'''))
    if PROBE:
        print('press',pg.evaluate('''()=>{const T=__tb;const out={};const run=(n)=>{for(let k=0;k<n;k++){T.stepPhysics(1/60);}};
          for(const i of [3,7]){T.mode="build";T.startLevel(i);T.quiet0&&T.quiet0();run(120);const bs=T.pileBodies().sort((x,y)=>y.getPosition().y-x.getPosition().y),b=bs[0],q=b.getPosition();
          T.startPileHold(99,b,b.getWorldCenter(),true);const h=T.pointers.get(99);T.feelHits[1]=0;
          for(let k=0;k<180;k++){h.pileTarget={x:q.x+Math.sin(k/20)*0.5,y:0};run(1);} out['level'+i+'_pressHits3s']=T.feelHits[1]; T.releaseHold(99);}
          for(const i of [3,7]){T.mode="build";T.startLevel(i);T.quiet0&&T.quiet0();run(120);const p=T.spawnPiece("block",0,8,0,"stone");T.startHold(p,p.body.getWorldCenter(),97,0,0);
          const r=T.pileBinRect; T.feelHits[1]=0; T.worldToPile(97,T.pointers.get(97),r.x+r.w/2,r.y+r.h*0.8); const h=T.pointers.get(97);
          for(let k=0;k<120;k++){run(1);} out['level'+i+'_backIntoPileHits2s']=T.feelHits[1]; T.releaseHold(97); T.feelHits[1]=0; run(180); out['level'+i+'_afterRelease3s']=T.feelHits[1];}
          return out;}'''))
        # pile: impacts counted while untouched, then after a bottom piece is dragged about; swing: stone block held at a top corner, moved sideways
        for li in range(10):
          print('pile',li,pg.evaluate('''(i)=>{const T=__tb;T.mode="build";T.startLevel(i);T.quiet0&&T.quiet0();const run=(n)=>{for(let k=0;k<n;k++){T.stepPhysics(1/60);T.cleanupOutOfBounds();}};
          run(120);T.feelHits[1]=0;run(300);const a=T.feelHits[1]; let seed=i+1; const rnd=()=>((seed=(seed*16807)%2147483647)/2147483647);
          const bs=T.pileBodies().sort((x,y)=>x.getPosition().y-y.getPosition().y), b=bs[0], y0=b.getPosition().y;
          T.startPileHold(99,b,b.getWorldCenter(),true); const h=T.pointers.get(99); for(let k=0;k<90;k++){h.pileTarget={x:b.getPosition().x,y:y0+k/15};run(1);}
          const lifted=+(b.getPosition().y-y0).toFixed(2); T.releaseHold(99); run(60);
          for(let r=0;r<8;r++){const B=T.pileBodies(), c=B[Math.floor(rnd()*B.length)], q=c.getPosition();
            T.startPileHold(99,c,c.getWorldPoint({x:0.4,y:0.2}),false); const H=T.pointers.get(99);
            const tx=rnd()*8, ty=rnd()*6; for(let k=0;k<40;k++){H.pileTarget={x:q.x+(tx-q.x)*k/40,y:q.y+(ty-q.y)*k/40};run(1);} T.releaseHold(99); run(20);}
          run(180); T.feelHits[1]=0; let mx=0, nmov=0; for(let k=0;k<600;k++){run(1); for(const B of T.pileBodies()){const v=B.getLinearVelocity(),sp=Math.hypot(v.x,v.y); mx=Math.max(mx,sp); if(sp>0.05)nmov++;}}
          return {untouched5s:a,bottomLifted:lifted,afterMessHits10s:T.feelHits[1],maxSpeed:+mx.toFixed(2),movingBodyFrames:nmov};}''',li))
        print('swing',pg.evaluate('''()=>{const T=__tb;T.mode="build";T.startLevel(0);const run=(n)=>{for(let k=0;k<n;k++){T.stepPhysics(1/60);}};
          const out={};for(const mat of ["stone","mudbrick","wood"]){const p=T.spawnPiece("block",4,8,0,mat);const g=p.body.getWorldPoint({x:-0.9,y:0.45});
          T.startHold(p,g,98,0,0);p.desired={x:g.x,y:g.y};run(600);const hang=p.body.getAngle();let mx=0;
          let lag=0,over=0;const gx=()=>p.body.getWorldPoint(p.grabLocal).x;
          for(let k=0;k<45;k++){p.desired={x:g.x+k*4/45,y:g.y};run(1);mx=Math.max(mx,Math.abs(p.body.getAngle()-hang));lag=Math.max(lag,p.desired.x-gx());}
          let amp=[];for(let k=0;k<240;k++){run(1);amp.push(Math.abs(p.body.getAngle()-hang));over=Math.max(over,gx()-p.desired.x);}
          out[mat]={lag:+lag.toFixed(2),overshoot:+over.toFixed(2),maxTiltMoving:+mx.toFixed(2),maxAfterStop:+Math.max(...amp).toFixed(2),after2s:+Math.max(...amp.slice(120,180)).toFixed(2),after3s:+Math.max(...amp.slice(180)).toFixed(2)};T.releaseHold(98);}
          for(const [d,mat,gx] of [["beam","wood",1.5],["column","stone",0],["beam","stone",1.5]]){const p=T.spawnPiece(d,7,8,d==="column"?Math.PI/2:0,mat);const g=p.body.getWorldPoint({x:d==="column"?0:gx,y:d==="column"?1.1:0});
            const a0=p.body.getAngle();T.startHold(p,g,98,0,0);p.desired={x:g.x,y:g.y};run(180);out[d+'/'+mat+' hangs after 3s (rad turned)']=+Math.abs(p.body.getAngle()-a0).toFixed(2);T.releaseHold(98);}
          return out;}'''))
        levels=[]
    for i in levels:
        if JIT:
            pg.evaluate('(i)=>{const T=__tb;T.mode="build";T.startLevel(i);T.quiet0&&T.quiet0();}',i)
            print(i,'pile at start',[pg.evaluate(JS_SPEED,0) for _ in range(6)])
        for vname, vsrc in [('', '')] + WRONG.get(i, []):
          r=pg.evaluate('''([i,vsrc])=>{const T=__tb; T.mode="build"; delete T.progress.done[T.LEVELS[i].key]; T.startLevel(i);T.quiet0&&T.quiet0();
          const key=T.LEVELS[i].key, orig=T.SOLUTIONS[key];
          if(vsrc){ const f=eval(vsrc); T.SOLUTIONS[key]=orig.map(e=>{const m=f(e); return m?[e[0],m,e[2],e[3],e[4]]:e;}); T.fillPile(T.SOLUTIONS[key].map(e=>({defKey:e[0],material:e[1]}))); }
          T.startAutoBuild(); T.SOLUTIONS[key]=orig;
          const dt=1/60; let n=0; const run=(s)=>{for(let k=0;k<s*60;k++){T.stepPhysics(dt);T.cleanupOutOfBounds();T.updateCheck(dt);}};
          while(T.auto && n<60*200){run(1/60);n++;}
          run(2);
          const c=T.runCheck(), ok=T.checkPasses(c), left=T.pileBodies().map(b=>b.pileItem.defKey+'/'+b.pileItem.material);
          T.setTab(true); T.startTest(); T.setTab(false);
          let last='', phases=[], drop=0, lead=0; let t=0;
          while(T.test && t<60*60){ if(T.test.phase!==last){last=T.test.phase;phases.push(last); if(last==='load'){drop=Math.max(...T.loads.map(l=>(l.body.getPosition().y-l.ty)/1.2)); lead=T.test.lead;}} run(1/60); t++; if(T.test&&T.test.phase==='fail') break;}
          const fs=T.failShow; const res={lvl:T.LEVELS[i].key, ready:ok, fill:+c.fill.toFixed(3), far:c.far, hole:+c.hole.toFixed(3), wood:+c.wood.toFixed(2), load:c.load, phases:phases.join('>'),
            pass:!!T.progress.done[T.LEVELS[i].key], dropS:+drop.toFixed(2), leadS:+(lead||0).toFixed(2), badLoads: fs?fs.loads.length:0, left};
          if(T.test){ run(4); } T.mode="map"; return res;}''', [i, vsrc])
          if vname: r={'lvl':r['lvl'],'WRONG':vname,'ready':r['ready'],'phases':r['phases'],'pass':r['pass'],'fill':r['fill'],'hole':r['hole'],'wood':r['wood']}
          print(json.dumps(r))
        if JIT: print(i,'after test',pg.evaluate('(s)=>{__tb.mode="build";return 0}',0) or pg.evaluate(JS_SPEED,1))
    print('errors',errs[:5])
    b.close()
