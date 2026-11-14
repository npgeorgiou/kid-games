# Headless check of every level: quick build, then the full test (Tab override). One line per level.
# Usage: python3 tools/harness.py [level indexes]. Exposes internals via window.__tb (hook injected, rAF disabled, stepped manually).
# Extend this file in place for new checks; do not make new scratch harnesses.
import sys, json
from playwright.sync_api import sync_playwright
import os, re
HERE=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(HERE,'..','tower-builder.html')).read()
hook='''window.__tb={get undoStack(){return typeof undoStack!=='undefined'?undoStack:null},undoButton:typeof undoButton!=='undefined'?undoButton:null,startFree:typeof startFree!=='undefined'?startFree:null,shapeTiles:typeof shapeTiles!=='undefined'?shapeTiles:null,set mat(v){selectedMaterial=v},traceLoads,crushLimit,TEST_LOAD_DENSITY,renderMap,get groups(){return groups},get boats(){return boats},drawFeel,updateFeel,testTick,get grid(){return grid},inRing,cellOf,SOLUTIONS,fillPile,testReady,stockItems,TEST_WIND,PIECE_DEFS,levelSidebar,pileLayout,render,startLevel,startAutoBuild,stepPhysics,cleanupOutOfBounds,updateCheck,runCheck,checkPasses,startTest,LEVELS,pileBodies,pieces,
get test(){return test},get auto(){return auto},get mode(){return mode},set mode(v){mode=v},setTab(v){tabDown=v},get loads(){return loads},get check(){return check},get failShow(){return failShow},progress,feelHits,spawnPiece,startHold,releaseHold,startPileHold,pilePoint,worldToPile,pileToWorld,clearAllPieces,get pilePx(){return pilePx},get scale(){return scale},quiet0(){pileQuietUntil=0},get pileBinRect(){return pileBinRect},get pointers(){return pointers},get pileScale(){return pileScale},set failShow(v){failShow=v},worldToScreen,failingCells,CHECK,TEST_QUAKE,get doneSites(){return typeof doneSites!=='undefined'?doneSites:null},get goMap(){return typeof goMap!=='undefined'?goMap:null},get siteLook(){return typeof siteLook!=='undefined'?siteLook:null},get restartButton(){return typeof restartButton!=='undefined'?restartButton:null},get readySince(){return readySince},ageReady(){if(readySince!=null)readySince-=1000},get removePiece(){return removePiece},get hitPiece(){return hitPiece},music(){return {ctx:actx&&actx.state,name:musicName,on:!!music}},isLand,massAt,siteMass,mapView,siteMarker,SITES,tourPeople,trailPoints,DONE_SIZE,DONE_RING,siteRadius,WALK_SPEED,get cssW(){return cssWidth}};
window.requestAnimationFrame=()=>0;
'''
k=src.rindex('})();')
src=src[:k]+hook+src[k:]
open('/tmp/tb.html','w').write(src)
open('/tmp/tb-real.html','w').write(src.replace('window.requestAnimationFrame=()=>0;',''))
JIT='jitter' in sys.argv
# wrong choices that must fail (level index -> [(name, JS: entry -> new material or nothing)])
WRONG={}  # wrong choices now live in tools/level-tests.json (made by make-levels.py); run: harness.py spec
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
    if 'spec' in sys.argv:  # levels.md tests; one line per check
        from collections import Counter
        LV=json.loads(re.sub(r'^//.*\n','',open(os.path.join(HERE,'level-spec.json')).read()))
        TESTS=json.load(open(os.path.join(HERE,'level-tests.json')))
        js=open(os.path.join(HERE,'..','src','levels.js')).read(); LVS=json.loads(js[js.index('const LEVELS = ')+15:js.rindex(';')])
        SUPPORTS={'ishtar':{'centering':1},'valens':{'centering':2}}
        RUN=open(os.path.join(HERE,'spec-run.js')).read()
        def stock(sol):
            c=Counter(); pulled=False
            for e in sol:
                if e[0]=='pull': pulled=True; continue
                if not(pulled and e[1]=='wood'): c[e[0]+'/'+e[1]]+=1
            return c
        NJ=int(os.environ.get('NJ','6'))
        if os.environ.get('LOAD'): pg.evaluate('(a)=>{for(const [i,d] of a) __tb.TEST_LOAD_DENSITY[i]=d}',[[int(x.split(':')[0]),float(x.split(':')[1])] for x in os.environ['LOAD'].split(',')])
        if os.environ.get('DIAG'): pg.evaluate('()=>{window.__DIAG=1}')
        if os.environ.get('DA'): pg.evaluate('(v)=>{window.__DA=v}',float(os.environ['DA']))
        if os.environ.get('WIND'): pg.evaluate('(a)=>{for(const [i,w] of a) __tb.TEST_WIND[i]=w}',[[int(x.split(':')[0]),float(x.split(':')[1])] for x in os.environ['WIND'].split(',')])
        for i,l in enumerate(LVS):
            if levels and i not in levels: continue
            k=l['key']; lines=[]
            lines.append(('1 headpiece locked',json.dumps(l['load'])==json.dumps(LV[k]['headpiece']),''))
            base=[pg.evaluate(RUN,[i,l['solution'],sd]) for sd in range(NJ)]
            lines.append(('2 build stands (exact + off by up to 3 cm)',all(b['pass'] and b['ready'] for b in base),' '.join(('P' if b['pass'] and b['ready'] else 'F:'+(b['phases'] or 'ready')+':'+json.dumps(b['fail'] or b['build'])) for b in base)))
            e0=base[0]['build']  # the exactly placed run: settled pieces within 5 cm of their places, outline and pieces differ by at most 2.5%
            # owner: the outline is the building's shape; the build's uncovered parts of it must still light the button (85%)
            lines.append(('8 outline matches the settled build',e0['moved']<=0.05 and 1-e0['miss']>=0.85 and e0['over']<=0.025,'moved %s, outline uncovered %s, pieces outside %s'%(e0['moved'],e0['miss'],e0['over'])))
            for w in TESTS[k]:
                r=pg.evaluate(RUN,[i,w['sol'],0]); p=r['build']['phys'] or bool(r['fail'] and r['fail']['phys'])
                lines.append(('3 wrong %s: %s'%(w['kind'],w['name']),(not (r['pass'] and r['ready'])) and p,'%s %s'%(r['phases'] or 'not ready',json.dumps(r['fail'] or r['build']))))
            have=Counter(pg.evaluate('(i)=>__tb.stockItems(i).map(o=>o.defKey+"/"+o.material)',i))
            okp=all(have[x]>=n for x,n in stock(l['solution']).items())
            right={(e[0],round(e[2],3),round(e[3],3)):e[1] for e in l['solution'] if e[0]!='pull'}
            for w in TESTS[k]:  # levels.md: every wrong choice can be built while the suggested build's pieces stay in the pile
                swap=Counter(e[0]+'/'+e[1] for e in w['sol'] if e[0]!='pull' and right.get((e[0],round(e[2],3),round(e[3],3)),e[1])!=e[1])
                need=stock(l['solution'])+swap+((stock(w['sol'])-stock(l['solution']))-swap)
                okp=okp and all(have[x]>=n for x,n in need.items())
            for d,n in SUPPORTS.get(k,{}).items(): okp=okp and have[d+'/wood']==n
            fits=pg.evaluate('''(i)=>{const T=__tb; T.mode="build"; T.startLevel(i); const r=T.levelSidebar().bin, px=T.pilePx; const [sc,out]=T.pileLayout(T.stockItems(i),r,px);
              return +(Math.max(...out.map(([it,x,y])=>y+T.PIECE_DEFS[it.defKey].hy))/(r.h/px)).toFixed(2);}''',i)
            lines.append(('4 pile (and it fits the sidebar at 1280x800)',okp and (fits<=1.0 or k=='valens'),  # owner 13 Nov: the Valens pile not fitting is not an issue
                 '%d pieces, %d%% of the sidebar height'%(sum(have.values()),round(fits*100))))
            for name,ok,det in lines: print('%-9s %-4s %-58s %s'%(k,'PASS' if ok else 'FAIL',name,det[:170]),flush=True)
            if os.environ.get('DIAG'): print(base[0]['build'].get('diag','')[:3000])
        levels=[]
    if 'trace' in sys.argv and os.environ.get('VARIANTS'): pg.evaluate('(s)=>{window.__SOL=s}',list(json.load(open(os.environ['VARIANTS']))['sols'].values())[0])
    if 'trace' in sys.argv:  # weight traced onto each mudbrick after the quick build (fair sharing), as a share of its limit
        for i in levels:
            print(LVS[i]['key'] if 'LVS' in dir() else i, pg.evaluate("""(i)=>{const T=__tb;T.mode="build";T.startLevel(i);T.quiet0();if(window.__SOL){const k=T.LEVELS[i].key,o=T.SOLUTIONS[k];T.clearAllPieces();T.fillPile(window.__SOL.map(e=>({defKey:e[0],material:e[1]})));T.SOLUTIONS[k]=window.__SOL;T.startAutoBuild();T.SOLUTIONS[k]=o;}else T.startAutoBuild();let n=0;while(T.auto&&n<18000){T.stepPhysics(1/60);n++;}for(let k=0;k<180;k++)T.stepPhysics(1/60);
              const t=T.traceLoads();return T.pieces.filter(p=>p.material==="mudbrick"||window.__SOL).map(p=>{const q=p.body.getPosition();return p.defKey[0]+'@'+(q.x-20).toFixed(1)+','+q.y.toFixed(1)+'='+(t.get(p.body).recv/T.crushLimit(p)).toFixed(2)+'/'+(p.crushAvg/T.crushLimit(p)).toFixed(2)+'/'+t.get(p.body).sup.map(s=>s.c.toFixed(2)+':'+s.w.toFixed(2)).join(';')}).join(' ')}""",i))
    if 'variants' in sys.argv:  # owner reports: run named builds of one level (JSON file: {"level":i,"sols":{name:sol}}), NJ placements each, with what strained each mudbrick
        V=json.load(open(os.environ['VARIANTS'])); RUN=open(os.path.join(HERE,'spec-run.js')).read(); pg.evaluate('(t)=>{window.__MON=1; if(t) window.__TRACE=+t}',os.environ.get('TRACE'))
        if os.environ.get('LOAD'): pg.evaluate('(a)=>{for(const [i,d] of a) __tb.TEST_LOAD_DENSITY[i]=d}',[[int(x.split(':')[0]),float(x.split(':')[1])] for x in os.environ['LOAD'].split(',')])
        for name,sol in V['sols'].items():
            for sd in range(int(os.environ.get('NJ','6'))):
                r=pg.evaluate(RUN,[V['level'],sol,sd]); print(name,sd,'PASS' if r['pass'] else 'FAIL',r['phases'],json.dumps(r['mon']))
                if r.get('trace'): print(' '.join(r['trace']))
    if 'real' in sys.argv:  # levels.md test 2, last part: the real game loop (real frame timing, the real ready gate, no Tab), all levels at once
        import time
        POLL=open(os.path.join(HERE,'spec-real.js')).read()
        pages=[]
        for i in (levels or range(10)):
            q=b.new_page(viewport={'width':1280,'height':800}); q.goto('file:///tmp/tb-real.html'); q.wait_for_timeout(300)
            q.evaluate('(i)=>{const T=__tb; T.mode="build"; delete T.progress.done[T.LEVELS[i].key]; T.startLevel(i); T.quiet0(); T.startAutoBuild(); window.__st="build"; window.__i=i;}',i); pages.append((i,q))
        t0=time.time(); done={}
        while len(done)<len(pages) and time.time()-t0<900:
            time.sleep(2)
            for i,q in pages:
                if i not in done:
                    st=q.evaluate(POLL)
                    if st: done[i]=st
        for i,q in pages: print('%-9s %-4s %s'%(q.evaluate('(i)=>__tb.LEVELS[i].key',i),'PASS' if done.get(i,'').endswith('PASS') else 'FAIL','2 real game loop: '+done.get(i,'timeout')),flush=True)
        levels=[]
    if 'whirlvideo' in sys.argv:  # owner 14 Nov: a video of whirling with the real mouse in the running game (real time)
        import math, glob, shutil, subprocess
        shutil.rmtree('/tmp/vid',ignore_errors=True)
        ctx=b.new_context(viewport={'width':1280,'height':800},record_video_dir='/tmp/vid',record_video_size={'width':1280,'height':800}); v=ctx.new_page()
        v.goto('file:///tmp/tb-real.html'); v.wait_for_timeout(800)
        v.evaluate("""()=>{const d=document.createElement('div');d.style.cssText='position:fixed;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;background:rgba(255,0,0,.85);pointer-events:none;z-index:99';document.body.appendChild(d);
          addEventListener('pointermove',e=>{d.style.left=e.clientX+'px';d.style.top=e.clientY+'px'},true);
          const s=document.createElementNS('http://www.w3.org/2000/svg','svg');s.style.cssText='position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:98';s.innerHTML='<circle id=gc fill=none stroke=red stroke-dasharray=6,6 stroke-width=2 r=0 />';document.body.appendChild(s);}""")
        sc=lambda x,y: v.evaluate('([x,y])=>{const s=__tb.worldToScreen(x,y);const r=document.querySelector("canvas").getBoundingClientRect();return [s.x+r.left,s.y+r.top]}',[x,y])
        for m in ['stone','wood']:
            v.evaluate('(m)=>{const T=__tb;T.mode="build";T.startFree();T.mat=m;T.clearAllPieces();T.spawnPiece("block",20,0.503,0,m);}',m); v.wait_for_timeout(700)
            g=sc(20.9,0.503); v.mouse.move(*g); v.mouse.down(); v.wait_for_timeout(100)
            for k in range(1,31): v.mouse.move(*sc(20.9,0.503+3*k/30)); v.wait_for_timeout(16)
            fps=v.evaluate('()=>new Promise(res=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<1000)requestAnimationFrame(f);else res(n)};requestAnimationFrame(f)})'); print('frames per second in the recording:',fps,flush=True)
            v.wait_for_timeout(2000); c=sc(20.9,4.103); r=sc(20.9+0.6,4.103)[0]-c[0]
            v.evaluate('([x,y,r])=>{const g=document.getElementById("gc");g.setAttribute("cx",x);g.setAttribute("cy",y);g.setAttribute("r",r)}',[c[0],c[1],r])
            t0=v.evaluate('()=>performance.now()'); nm=0
            while True:
                t=(v.evaluate('()=>performance.now()')-t0)/1000
                if t>6: break
                th=t*2*math.pi; v.mouse.move(*sc(20.9+0.6*math.sin(th),3.503+0.6-0.6*math.cos(th))); nm+=1; v.wait_for_timeout(8)
            print('mouse moves per second:',nm/6,flush=True)
            v.wait_for_timeout(300); v.mouse.up(); v.wait_for_timeout(1200)
            v.evaluate('()=>{document.getElementById("gc").setAttribute("r",0)}')
        ctx.close(); src=glob.glob('/tmp/vid/*.webm')[0]; out=os.path.join(HERE,'..','owner-shots','whirl-real-mouse.mp4')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',src,'-c:v','libx264','-preset','veryfast','-pix_fmt','yuv420p',out]); print('video',out)
        levels=[]
    if 'mousewhirl' in sys.argv:  # owner 14 Nov: can a person whirl with the real mouse? stone block held at one end, circles as big as the round stone, once a second
        st=lambda n: pg.evaluate('(n)=>{for(let k=0;k<n;k++){__tb.stepPhysics(1/60);__tb.cleanupOutOfBounds();}}',n)
        sc=lambda x,y: pg.evaluate('([x,y])=>{const s=__tb.worldToScreen(x,y);const r=document.querySelector("canvas").getBoundingClientRect();return [s.x+r.left,s.y+r.top]}',[x,y])
        import math
        for m in ['stone','mudbrick','wood']:
          for name,per_step,skip in [('one mouse move per game step',1,0),('two mouse moves per step',2,0),('a move every second step',1,1)]:
            pg.evaluate('(m)=>{const T=__tb;T.mode="build";T.startFree();T.mat=m;T.clearAllPieces();T.spawnPiece("block",20,0.503,0,m);T.render();}',m); st(30)
            g=sc(20.9,0.503); pg.mouse.move(*g); pg.mouse.down(); st(2)
            for k in range(1,31): pg.mouse.move(*sc(20.9,0.503+3*k/30)); st(1)
            st(150); c=(20.9,3.503); R=0.6; a0=pg.evaluate('()=>__tb.pieces[0].body.getAngle()'); tot=0; prev=a0; i=0
            for k in range(240*per_step):
                th=k/(60*per_step)*2*math.pi; pg.mouse.move(*sc(c[0]+R*math.sin(th),c[1]+R-R*math.cos(th)))
                if (k+1)%per_step==0:
                    i+=1
                    if not skip or i%2==0: st(1 if not skip else 2)
                    a=pg.evaluate('()=>__tb.pieces[0].body.getAngle()'); tot+=a-prev; prev=a
            pg.mouse.up(); print('mousewhirl %-8s %-30s %.2f turns in 4 circles'%(m,name,abs(tot)/(2*math.pi)),flush=True)
    if 'whirlpic' in sys.argv:  # owner 14 Nov: picture of a block held at one end whirled by circles of the hand as big as the round stone
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        tr=pg.evaluate("""()=>{const T=__tb,res={};T.mode="build";T.startLevel(0);T.clearAllPieces();T.fillPile([]);
          for(const m of ["wood","mudbrick","stone"]){T.clearAllPieces();const p=T.spawnPiece("block",20,6,0,m);for(let k=0;k<6;k++){T.stepPhysics(1/60,5);}
            const g0=p.body.getWorldPoint({x:0.9,y:0}),g={x:g0.x,y:g0.y};T.startHold(p,g,87,0,0);p.desired={x:g.x,y:g.y};for(let k=0;k<150;k++)T.stepPhysics(1/60,5);
            const fr=[],hand=[];for(let k=0;k<240;k++){const th=k/60*2*Math.PI;p.desired={x:g.x+0.6*Math.sin(th),y:g.y+0.6-0.6*Math.cos(th)};T.stepPhysics(1/60,5);
              hand.push([p.desired.x,p.desired.y]);if(k%5==0){const c=[[-1,-0.5],[1,-0.5],[1,0.5],[-1,0.5]].map(([x,y])=>{const w=p.body.getWorldPoint({x,y});return[w.x,w.y]});fr.push(c);}}
            T.releaseHold(87);res[m]={fr,hand};}return res;}""")
        fig,ax=plt.subplots(1,3,figsize=(15,5.5))
        for a_,m in zip(ax,["wood","mudbrick","stone"]):
            n=len(tr[m]['fr'])
            for i,c in enumerate(tr[m]['fr']): a_.fill(*zip(*c),alpha=0.08+0.5*i/n,color='tab:brown' if m=='wood' else ('tab:orange' if m=='mudbrick' else 'grey'),ec='k',lw=0.3)
            h=tr[m]['hand']; a_.plot([q[0] for q in h],[q[1] for q in h],'r-',lw=2); a_.set_aspect('equal'); a_.set_xlim(16.5,23.5); a_.set_ylim(1.5,9.5)
            a_.set_title(m+' block held at one end: 4 circles of the hand (red), 1 a second'); a_.title.set_fontsize(9)
        plt.tight_layout(); plt.savefig(os.path.join(HERE,'..','owner-shots','whirl-4-circles.png'),dpi=90); print('saved')
    if 'owner' in sys.argv:  # the owner's sixth list: tests that repeat what he does in the game (tools/owner-tests.js)
        names=[a for a in sys.argv[2:] if not a.isdigit()]
        for name,ok,det in pg.evaluate(open(os.path.join(HERE,'owner-tests.js')).read(),names):
            print('%-4s %-70s %s'%('PASS' if ok else 'FAIL',name,det[:200]),flush=True)
        if not names or 'motion' in names:  # the hand's feel against the owner-approved reference (tools/motion-ref.json)
            feel=pg.evaluate('()=>window.__feel'); ref_p=os.path.join(HERE,'motion-ref.json')
            if feel and not os.path.exists(ref_p) or 'record' in sys.argv: json.dump(feel,open(ref_p,'w'),indent=1,ensure_ascii=False); print('     motion reference recorded')
            elif feel:
                ref=json.load(open(ref_p))
                for k,v in ref.items():
                    n=feel.get(k); ok=n is not None and v is not None and abs(n-v)<=0.15*abs(v)+0.04
                    print('%-4s %-70s %s'%('PASS' if ok else 'FAIL','11 hand feel unchanged: '+k,'now %s, approved %s'%(n,v)),flush=True)
        if not names or 'screens' in names:  # seventh list 2: the quick build and test give the same result on every screen size
            JS=open(os.path.join(HERE,'owner-tests.js')).read()
            allr={}
            for (w,h,dpr) in [(1280,800,1),(1366,768,1),(1920,1080,1),(1536,864,1.25),(1024,768,1)]:
                c=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr); q=c.new_page(); q.goto('file:///tmp/tb.html'); q.wait_for_timeout(300)
                allr['%dx%d'%(w,h)]=q.evaluate("""()=>{const T=__tb; const fr=(dt)=>{const f=T.test&&T.test.fast&&T.test.phase!=="fail"&&T.test.phase!=="pass"?10:1;T.stepPhysics(dt*f,5*f);T.cleanupOutOfBounds();T.updateCheck(dt);};
                  return T.LEVELS.map((L,i)=>[1,1.2].map((m)=>{const q0=T.TEST_QUAKE[i],d0=T.TEST_LOAD_DENSITY[i]; T.TEST_QUAKE[i]=q0*m; T.TEST_LOAD_DENSITY[i]=d0*m;
                    T.mode="build"; delete T.progress.done[L.key]; T.startLevel((i+1)%10); T.startLevel(i); T.quiet0(); T.startAutoBuild(); let n=0; while(T.auto&&n<20000){fr(1/60);n++;}
                    T.setTab(true); T.startTest(); T.setTab(false); T.test.fast=true; let k=0; while(T.test&&k<20000){fr(1/60);k++;} T.TEST_QUAKE[i]=q0; T.TEST_LOAD_DENSITY[i]=d0;
                    return T.progress.done[L.key]?"PASS":"FAIL";}).join("/"));}""")  # plain test / 20% stronger (owner, 13 Nov; was 30%) earthquake and headpiece
                c.close()
            for i in range(10):
                rs={k:v[i] for k,v in allr.items()}
                print('%-4s %-70s %s'%('PASS' if set(rs.values())=={'PASS/PASS'} else 'FAIL','7-2 same result on every screen size (also 1.2x): level %d'%(i+1),json.dumps(rs)),flush=True)
        if not names or 'restart' in names:  # 1: a real click on the restart button puts the whole map back to the beginning
            q=b.new_page(viewport={'width':1280,'height':800}); q.goto('file:///tmp/tb-real.html'); q.wait_for_timeout(500)
            st=q.evaluate("""()=>{const T=__tb; T.progress.done.mastaba={pieces:[],loads:[]}; T.progress.done.djoser={pieces:[],loads:[]};
              localStorage.setItem('tower-builder-progress-v1',JSON.stringify(T.progress)); for(const g of T.groups){g.state='visit';g.site='mastaba';g.wait=3;g.boat=null;}
              for(let k=0;k<600;k++) T.renderMap(0.05); const b=T.restartButton&&T.restartButton(); return b&&[b.x,b.y];}""")
            if st:
                q.mouse.click(st[0],st[1]); q.wait_for_timeout(300)
                r=q.evaluate("""()=>{const T=__tb; return {done:Object.keys(T.progress.done).length, saved:localStorage.getItem('tower-builder-progress-v1'),
                  people:T.groups.every((g,i)=>g.state==='boat'&&g.boat===T.boats[i]&&g.onFoot===0), boats:T.boats.every((b,i)=>b.wait>0||(b.leg===i%b.line.legs.length&&b.dir===1&&Math.abs(b.d-b.lens[b.leg]*((i*0.37)%1))<20)), mode:T.mode};}""")
                ok=r['done']==0 and r['people'] and r['boats'] and r['mode']=='map' and (r['saved'] is None or json.loads(r['saved']).get('done',{})=={})
                print('%-4s %-70s %s'%('PASS' if ok else 'FAIL','1 restart: sites, people, boats and progress as at the start',json.dumps(r)))
            else: print('FAIL 1 restart: no button on the map')
            q.close()
        if not names or 'music' in names:  # 2: music at load when the browser allows it, otherwise at the first touch
            b2=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']); q=b2.new_page(); q.goto('file:///tmp/tb-real.html'); q.wait_for_timeout(2500)
            r=q.evaluate('()=>__tb.music()'); print('%-4s %-70s %s'%('PASS' if r['on'] and r['ctx']=='running' else 'FAIL','2 music at load (PC allows sound)',json.dumps(r))); b2.close()
            b3=p.chromium.launch(args=['--autoplay-policy=user-gesture-required']); q=b3.new_page(viewport={'width':1280,'height':800}); q.goto('file:///tmp/tb-real.html'); q.wait_for_timeout(2500)
            r0=q.evaluate('()=>__tb.music()'); q.mouse.click(640,30); q.wait_for_timeout(1500); r=q.evaluate('()=>__tb.music()')
            print('%-4s %-70s %s'%('PASS' if r['on'] and r['ctx']=='running' else 'FAIL','2 music at the first touch (PC holds sound back)','before '+json.dumps(r0)+' after '+json.dumps(r))); b3.close()
        levels=[]
    if 'sandbox' in sys.argv:  # owner 14 Nov: free play shapes per material fit the sidebar on every screen size, each one can be taken; a passed level stays on the building
        for W,H in [(1280,800),(1366,768),(1920,1080),(1024,600)]:
            pg.set_viewport_size({'width':W,'height':H}); pg.wait_for_timeout(200)
            for m in ['wood','mudbrick','stone']:
                r=pg.evaluate('''(m)=>{const T=__tb; T.mode="build"; T.startFree(); T.mat=m; T.clearAllPieces(); const ts=T.shapeTiles(); T.render();
                  const over=ts.filter(t=>t.y+t.h>innerHeight-8||t.y<0).length, small=ts.filter(t=>t.h<30||t.w<30).length; let made=0;
                  for(const t of ts){T.clearAllPieces(); const d=T.PIECE_DEFS[t.def]; const p=T.spawnPiece(t.def,8,(d.hy||d.r)+0.03,0,m); for(let k=0;k<60;k++)T.stepPhysics(1/60); if(T.pieces.includes(p))made++;}
                  T.clearAllPieces(); T.render(); return {n:ts.length,over,small,made};}''',m)
                pg.screenshot(path='/tmp/sandbox-%s-%d.png'%(m,W))
                print('sandbox',W,H,m,r,'OK' if r['over']==0 and r['made']==r['n'] else 'FAIL')
        pg.set_viewport_size({'width':1280,'height':800})
        r=pg.evaluate('''()=>{const T=__tb; T.mode="build"; delete T.progress.done[T.LEVELS[0].key]; T.startLevel(0); T.quiet0(); T.startAutoBuild(); let n=0; while(T.auto&&n<18000){T.stepPhysics(1/60);n++;}
          for(let k=0;k<180;k++){T.stepPhysics(1/60);T.updateCheck(1/60);} T.setTab(true); T.startTest(); T.setTab(false); T.test.fast=true; let k=0; while(T.test&&k<20000){const f=T.test.fast&&T.test.phase!=="fail"&&T.test.phase!=="pass"?10:1;T.stepPhysics(f/60,5*f);T.cleanupOutOfBounds();T.updateCheck(1/60);k++;}
          return {mode:T.mode,saved:!!T.progress.done[T.LEVELS[0].key]};}''')
        # undo (owner 14 Nov): by mouse, as he does: take a block from the sidebar, drop it on another, press undo -> as before
        st=lambda n: pg.evaluate('(n)=>{for(let k=0;k<n;k++){__tb.stepPhysics(1/60);__tb.cleanupOutOfBounds();}}',n)
        t=pg.evaluate('()=>{const T=__tb;T.mode="build";T.startFree();T.mat="stone";T.clearAllPieces();T.spawnPiece("block",8,0.503,0,"stone");T.render();const t=T.shapeTiles().find(t=>t.def==="block");return [t.x+t.w/2,t.y+t.h/2]}')
        bp=pg.evaluate('()=>{const s=__tb.worldToScreen(8,2.2);const r=document.querySelector("canvas").getBoundingClientRect();return [s.x+r.left,s.y+r.top]}')
        pg.mouse.move(*t); pg.mouse.down(); st(5)
        for k in range(1,31): pg.mouse.move(t[0]+(bp[0]-t[0])*k/30, t[1]+(bp[1]-t[1])*k/30); st(4)
        st(60); pg.mouse.up(); st(120)
        n1=pg.evaluate('()=>__tb.pieces.length')
        u=pg.evaluate('()=>{const u=__tb.undoButton();const r=document.querySelector("canvas").getBoundingClientRect();return [u.x+r.left,u.y+r.top]}')
        pg.mouse.click(*u); st(30)
        ru=pg.evaluate('()=>({n:__tb.pieces.length,y:+__tb.pieces[0].body.getPosition().y.toFixed(2),left:__tb.undoStack.length})')
        print('undo: block put on a block by mouse, then undo',n1,ru,'OK' if n1==2 and ru['n']==1 and abs(ru['y']-0.5)<0.02 else 'FAIL')
        print('pass stays on building',r,'OK' if r['mode']=='build' and r['saved'] else 'FAIL')
        levels=[]
    if 'shot' in sys.argv:  # screenshot of each level after the quick build (before the test): /tmp/shot<i>.png
        for i in levels:
            pg.evaluate('''(i)=>{const T=__tb; T.mode="build"; T.startLevel(i); T.quiet0(); T.render();}''',i); pg.screenshot(path='/tmp/shot%da.png'%i)
            pg.evaluate('''(i)=>{const T=__tb; T.mode="build"; T.startLevel(i); T.quiet0(); T.startAutoBuild(); let n=0; while(T.auto&&n<60*300){T.stepPhysics(1/60);T.cleanupOutOfBounds();T.updateCheck(1/60);n++;}
              for(let k=0;k<120;k++){T.stepPhysics(1/60);T.updateCheck(1/60);} T.render();}''',i)
            pg.screenshot(path='/tmp/shot%d.png'%i)
        levels=[]
    if 'map' in sys.argv:  # owner 13 Nov: every big circle wholly on its own land, nothing overlaps; travellers on land, round the building slowly
        for vw,vh in [(2560,1600),(2560,1440),(1920,1200),(1920,1080),(1680,1050),(1600,900),(1536,864),(1440,900),(1366,768),(1280,800),(1280,720),(1280,1024),(1024,768),(1024,600)]:
            pg.set_viewport_size({'width':vw,'height':vh}); pg.wait_for_timeout(100)
            r=pg.evaluate('''()=>{const T=__tb; T.mode="map";
              T.LEVELS.forEach(L=>{T.progress.done[L.key]={pieces:L.solution.filter(e=>e[0]!=="pull"),loads:L.load.map(v=>[0,0,0,v.reduce((a,c,i)=>(i%2?a[a.length-1].push(c):a.push([c]),a),[])])};});
              const v=T.mapView(), bad=[], over=[], M=T.SITES.map(s=>T.siteMarker(v,s));
              T.SITES.forEach((s,i)=>{const m=M[i], mass=T.siteMass(s); for(let a=0;a<6.28;a+=0.1) for(const f of [1,0.5]){ if(T.massAt((m.x+Math.cos(a)*m.r*f-v.ox)/v.k,(m.y+Math.sin(a)*m.r*f-v.oy)/v.k)!==mass){bad.push(s.key);return;} }});
              for(let i=0;i<M.length;i++) for(let j=i+1;j<M.length;j++) if(Math.hypot(M[i].x-M[j].x,M[i].y-M[j].y)<M[i].r+M[j].r+M[i].r*0.2) over.push(T.SITES[i].key+"/"+T.SITES[j].key);
              let wk={}, water=0, jumps=0, visits=0, last=new Map();
              for(let f=0;f<6000;f++){T.renderMap(0.05);
                for(const g of T.groups){ if(g.state==="boat"){last.delete(g);continue;}
                  let P=T.trailPoints(g).map(p=>[p[0],p[1]]);
                  if(g.state==="visit"&&g.tour){ P=T.tourPeople(g).map(p=>[p.x,p.y]); if(g.phase==="look") visits++;
                    const L=last.get(g); if(L&&L.visit) P.forEach((p,k)=>{ if(Math.hypot(p[0]-L.P[k][0],p[1]-L.P[k][1])>T.WALK_SPEED*0.05*1.05+0.01) jumps++; }); }
                  last.set(g,{P,visit:g.state==="visit"&&!!g.tour});
                  for(const p of P) if(!T.isLand(p[0],p[1])) {water++; wk[g.state+(g.phase&&g.state==="visit"?g.phase:"")]=(wk[g.state+(g.phase&&g.state==="visit"?g.phase:"")]||0)+1;} }}
              return {circlesOffTheirLand:bad, overlapping:over, personFramesOnWater:water, where:wk, lookingFrames:visits, fastSteps:jumps};}''')
            ok=not r['circlesOffTheirLand'] and not r['overlapping'] and r['personFramesOnWater']==0 and r['lookingFrames']>0 and r['fastSteps']==0
            print('%-4s %-24s %s'%('PASS' if ok else 'FAIL','map %dx%d'%(vw,vh),json.dumps(r)),flush=True)
        levels=[]
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
          T.startPileHold(99,b,b.getWorldCenter(),true); const h=T.pointers.get(99); let vup=0; for(let k=0;k<60;k++){h.pileTarget={x:b.getPosition().x,y:y0+k/6};run(1);vup=Math.max(vup,b.getLinearVelocity().y);}
          const lifted=+(b.getPosition().y-y0).toFixed(2), sizeKept=T.pileScale===T.pilePx; T.releaseHold(99); run(60);
          for(let r=0;r<8;r++){const B=T.pileBodies(), c=B[Math.floor(rnd()*B.length)], q=c.getPosition();
            T.startPileHold(99,c,c.getWorldPoint({x:0.4,y:0.2}),false); const H=T.pointers.get(99);
            const tx=rnd()*8, ty=rnd()*6; for(let k=0;k<40;k++){H.pileTarget={x:q.x+(tx-q.x)*k/40,y:q.y+(ty-q.y)*k/40};run(1);} T.releaseHold(99); run(20);}
          run(180); T.feelHits[1]=0; T.feelHits[2]=0; let mx=0, nmov=0; for(let k=0;k<600;k++){run(1); for(const B of T.pileBodies()){const v=B.getLinearVelocity(),sp=Math.hypot(v.x,v.y); mx=Math.max(mx,sp); if(sp>0.05)nmov++;}}
          return {sizeKept,untouched5s:a,bottomLifted:lifted,maxUp:+vup.toFixed(1),afterMessHits10s:T.feelHits[1],rescued:T.feelHits[2]||0,maxSpeed:+mx.toFixed(2),movingBodyFrames:nmov};}''',li))
        # Hand physics tests (pass/fail). Pointer paths are human-like: speed eases in over 0.3 s.
        print('hand',pg.evaluate('''()=>{const T=__tb;T.mode="build";T.startLevel(0);const run=(n)=>{for(let k=0;k<n;k++)T.stepPhysics(1/60);};
          const res={};
          const hold=(d,mat,lx,ly,sx=7)=>{T.clearAllPieces();const p=T.spawnPiece(d,sx,6,0,mat);run(1);const g=p.body.getWorldPoint({x:lx,y:ly});T.startHold(p,g,98,0,0);p.desired={x:g.x,y:g.y};return [p,g];};
          // 1 lifted by one end, a lying piece swings down and hangs (turns about 90 deg)
          for(const [d,mat,lx] of [["block","stone",0.9],["beam","stone",1.5],["block","wood",0.9]]){const [p,g]=hold(d,mat,lx,0);const a0=p.body.getAngle();
            for(let k=0;k<60;k++){p.desired={x:g.x,y:g.y+k*1.5/60};run(1);} run(300); const turn=Math.abs(p.body.getAngle()-a0);
            res['hangs '+d+'/'+mat]=[+turn.toFixed(2), turn>1.3&&turn<1.85?'PASS':'FAIL']; T.releaseHold(98);}
          // 2 whirling the hand in circles (1 Hz, 1 m) turns the piece round and round, smoothly (no jerks in its spin)
          // trembling = the spin's acceleration flipping sign from one step to the next (smooth motion: almost never)
          for(const [d,mat,lx] of [["block","stone",0.9],["block","wood",0.9],["beam","wood",1.5],["beam","stone",1.5]]){const [p,g]=hold(d,mat,lx,0);run(150);let gap=0,fg=0,prev=p.body.getAngle(),tot=0,flips=0,w0=p.body.getAngularVelocity(),dw0=0;
            for(let k=0;k<240;k++){const th=k/60*2*Math.PI*1.0;p.desired={x:g.x+1.0*Math.sin(th),y:g.y+1.0*(1-Math.cos(th))};run(1);const a=p.body.getAngle();tot+=a-prev;prev=a;const q=p.body.getWorldPoint(p.grabLocal);if(k>30){gap=Math.max(gap,Math.hypot(q.x-p.handBody.getPosition().x,q.y-p.handBody.getPosition().y));fg=Math.max(fg,Math.hypot(q.x-p.desired.x,q.y-p.desired.y));}const w=p.body.getAngularVelocity(),dw=w-w0;if(k>30&&Math.abs(dw)>0.03&&Math.abs(dw0)>0.03&&dw*dw0<0)flips++;w0=w;dw0=dw;}
            const turns=Math.abs(tot)/(2*Math.PI); res['whirls '+d+'/'+mat]=[+turns.toFixed(2)+' turns',flips+' trembles',+gap.toFixed(2)+' m max off hand',+fg.toFixed(2)+' m off finger (hand speed cap)', flips<=4&&gap<0.2?'PASS':'FAIL']; T.releaseHold(98);}
          // 3 dragged through the air (speeding up to 3 m/s in 0.25 s, then stopping as fast), a hanging piece swings and settles, never trembles
          for(const [d,mat,lx] of [["block","stone",0.9],["block","mudbrick",0.9],["square","stone",0.4],["beam","stone",1.5]]){const [p,g]=hold(d,mat,lx,0,3);run(600);const hang=p.body.getAngle();let x=g.x,v=0,mx=0;
            for(let k=0;k<120;k++){v=k<15?v+3/15:k>=105?Math.max(0,v-3/15):v;x+=v/60;p.desired={x,y:g.y};run(1);mx=Math.max(mx,Math.abs(p.body.getAngle()-hang));}
            for(let k=0;k<60;k++){run(1);mx=Math.max(mx,Math.abs(p.body.getAngle()-hang));}
            let jerk=0,w0=p.body.getAngularVelocity(),dw0=0; for(let k=0;k<180;k++){run(1);const w=p.body.getAngularVelocity(),dw=w-w0;if(Math.abs(dw)>0.03&&Math.abs(dw0)>0.03&&dw*dw0<0)jerk++;w0=w;dw0=dw;}
            const left=Math.abs(p.body.getAngle()-hang);
            res['drag '+d+'/'+mat]=[+mx.toFixed(2)+' rad max swing',+left.toFixed(3)+' rad 4 s after stop ('+hang.toFixed(2)+'>'+p.body.getAngle().toFixed(2)+(T.pieces.includes(p)?'':' gone')+')',jerk+' trembles', left<0.1&&jerk<=4?'PASS':'FAIL']; T.releaseHold(98);}
          // 4 taken out of the sidebar held at a corner while swinging: same grab point under the finger and same spin
          {T.startLevel(3);T.quiet0&&T.quiet0();run(60);const B=T.pileBodies().sort((x,y)=>y.getPosition().y-x.getPosition().y)[0],L=B.getLocalCenter();
           const g={x:L.x+0.8*Math.abs(B.getLocalPoint(B.getWorldCenter()).x+0.9),y:L.y};T.startPileHold(96,B,B.getWorldPoint({x:0.85,y:0.4}),false);const H=T.pointers.get(96),q=B.getWorldPoint(H.pileGrab);
           for(let k=0;k<40;k++){H.pileTarget={x:q.x-k*0.05,y:q.y+1};run(1);} const w1=B.getAngularVelocity(),r=T.pileBinRect;
           T.pileToWorld(96,H,r.x-5,r.y+r.h/2);const P=T.pointers.get(96).piece,w2=P.body.getAngularVelocity();run(1);
           res['out of sidebar keeps spin and grip']=[+w1.toFixed(2),+w2.toFixed(2),P.lever,Math.abs(w1-w2)<0.01&&P.lever?'PASS':'FAIL'];T.releaseHold(96);}
          {T.clearAllPieces();const P=T.spawnPiece("block",8,6,0,"stone");run(1);const g=P.body.getWorldPoint({x:0.9,y:0.4});T.startHold(P,g,95,0,0);
           for(let k=0;k<40;k++){P.desired={x:g.x+k*0.06,y:g.y+0.5};run(1);} const w1=P.body.getAngularVelocity(),r=T.pileBinRect;
           T.worldToPile(95,T.pointers.get(95),r.x+r.w/2,r.y+r.h/2);const B=T.pointers.get(95).pileBody,w2=B.getAngularVelocity();
           res['into sidebar keeps spin and grip']=[+w1.toFixed(2),+w2.toFixed(2),!T.pointers.get(95).centred,Math.abs(w1-w2)<0.01&&!T.pointers.get(95).centred?'PASS':'FAIL'];T.releaseHold(95);}
          {T.clearAllPieces();const a=T.spawnPiece("block",8,0.5,0,"stone");run(30);const P=T.spawnPiece("block",8,0.55,0,"stone");P.ghost=false;T.startHold(P,P.body.getWorldCenter(),94,0,0);
           for(let f=P.body.getFixtureList();f;f=f.getNext())f.setFilterData({groupIndex:0,categoryBits:4,maskBits:2});P.ghost=true;
           let low=9;for(let k=0;k<120;k++){P.desired={x:8,y:-2};run(1);low=Math.min(low,P.body.getPosition().y);}
           res['ghost stays above ground']=[+low.toFixed(2),P.ghost,low>0.4&&P.ghost?'PASS':'FAIL'];T.releaseHold(94);}
          // 5 a beam lying sideways leaves the sidebar right at its edge, turning, and comes back in: never lost
          {T.startLevel(9);T.quiet0&&T.quiet0();run(60);let lost=0;for(const [dx,spin] of [[2,4],[2,-4],[30,6],[2,0]]){const B=T.pileBodies().find(b=>b.pileItem.defKey==="beam")||T.pileBodies()[0];
            T.startPileHold(93,B,B.getWorldPoint({x:1.2,y:0}),false);const H=T.pointers.get(93);B.setAngularVelocity(spin);const r=T.pileBinRect;
            T.pileToWorld(93,H,r.x-dx,r.y+r.h*0.95);const P=T.pointers.get(93).piece;for(let k=0;k<60;k++){P.desired=P.desired;run(1);T.cleanupOutOfBounds();}
            if(!T.pieces.includes(P)){lost++;T.pointers.delete(93);continue;}
            const n=T.pileBodies().length;T.worldToPile(93,T.pointers.get(93),r.x+3,r.y+r.h*0.95);for(let k=0;k<60;k++)run(1);if(T.pileBodies().length!==n+1)lost++;T.releaseHold(93);run(30);}
           res['sideways in and out of the sidebar']=[lost+' lost',lost===0?'PASS':'FAIL'];}
          return res;}'''))
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
