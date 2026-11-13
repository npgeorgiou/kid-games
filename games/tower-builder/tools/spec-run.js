([i,sol,seed])=>{const T=__tb; let r=seed*7919+1; const rnd=()=>{r=(r*16807)%2147483647; return r/2147483647-0.5;};
  T.mode="build"; delete T.progress.done[T.LEVELS[i].key]; T.startLevel(i); T.quiet0();
  const key=T.LEVELS[i].key, orig=T.SOLUTIONS[key], sup=T.LEVELS[i].woodRole==="support";
  // off by up to 3 cm and 1 degree, as a careful player would place them: never overlapping what is already there
  const box=(e)=>{const d=T.PIECE_DEFS[e[0]], c=Math.abs(Math.cos(e[4])), sn=Math.abs(Math.sin(e[4])), hx=d.hx*c+d.hy*sn, hy=d.hx*sn+d.hy*c; return [e[2]-hx,e[3]-hy,e[2]+hx,e[3]+hy];};
  const ov=(a,b)=>Math.min(a[2],b[2])-Math.max(a[0],b[0])>0.002&&Math.min(a[3],b[3])-Math.max(a[1],b[1])>0.002;
  const jit=[], placed=[];
  for(const e of sol){ if(e[0]==="pull"){jit.push(e);continue;} let q=e;
    if(seed){ const DA=+(window.__DA??0.035); const tries=[[rnd()*0.06,Math.abs(rnd())*0.03,rnd()*DA],[0,Math.abs(rnd())*0.03,rnd()*DA],[0,0.01,0]];
      for(const [dx,dy,da] of tries){ const c=[e[0],e[1],e[2]+dx,e[3]+dy,e[4]+da], bc=box(c), b0=box(e);
        if(!placed.some(([p,bp])=>ov(bc,bp)&&!ov(b0,box(p)))){q=c;break;} } }
    jit.push(q); placed.push([e,box(q)]); }
  let pulled=false; const items=[]; for(const e of sol){ if(e[0]==="pull"){pulled=true;continue;} if(!(pulled&&e[1]==="wood")) items.push({defKey:e[0],material:e[1]}); }
  T.clearAllPieces(); T.fillPile(items); T.SOLUTIONS[key]=jit; T.startAutoBuild(); T.SOLUTIONS[key]=orig;
  const mon=window.__MON?{}:null; // per mudbrick: peak weight on it / its limit, and whether it was ever bent over a gap, while strained
  const watch=()=>{ if(!mon) return; for(const p of T.pieces){ if(p.material!=="mudbrick") continue; const q=p.body.getPosition(), id=p.defKey+'@'+(q.x-20).toFixed(1)+','+q.y.toFixed(1)+':'+((T.test&&T.test.phase)||'build');
      const m=mon[id]=mon[id]||{peak:0,bent:0,strain:0}; m.peak=Math.max(m.peak,+((p.crushAvg||0)/T.crushLimit(p)).toFixed(2)); if(p.wasBent)m.bent++; m.strain=Math.max(m.strain,+(p.strain||0).toFixed(2)); } };
  const run=(s)=>{for(let k=0;k<s*60;k++){T.stepPhysics(1/60);T.cleanupOutOfBounds();T.updateCheck(1/60);watch();}};
  let n=0; while(T.auto&&n<60*300){run(1/60);n++;} run(2);
  const targets=sol.filter(e=>e[0]!=="pull"&&!(sup&&e[1]==="wood"));
  const phys=()=>{ const used=new Set(); let worst=0, missing=0; const miss=[];
    for(const e of targets){ let best=null,bd=1e9;
      for(const p of T.pieces){ if(used.has(p)||p.defKey!==e[0]||p.material!==e[1]) continue; const q=p.body.getPosition(), d=Math.hypot(q.x-20-e[2],q.y-e[3]); if(d<bd){bd=d;best=p;} }
      if(!best||bd>1.5){missing++;miss.push(e[0]+'/'+e[1]+'@'+e[2].toFixed(1)+','+e[3].toFixed(1));continue;} used.add(best); worst=Math.max(worst,bd); }
    const halves=T.pieces.filter(p=>/half/.test(p.defKey)).length; return {moved:+worst.toFixed(2),missing,miss:miss.slice(0,3),halves,phys:worst>0.3||missing>0||halves>0}; };
  const c=T.runCheck(), ready=T.checkPasses(c), after=phys();
  // test 8: the settled build matches the outline: share of the outline left uncovered, and of the pieces lying outside it (hole rims excepted)
  { const g=T.grid; let over=0; for(let k=0;k<g.cov.length;k++){ if(!g.cov[k]||g.inOutline[k]||g.inHole[k]||g.inLoad[k]) continue; const x=(k%400+0.5)*0.1, y=(Math.floor(k/400)+0.5)*0.1;
      if(!g.holes.some(r=>T.inRing(x,y,r))) over++; }
    if(window.__DIAG){ const rows={}; for(let k=0;k<g.cov.length;k++){ const y=Math.floor(k/400), x=k%400; if(g.inOutline[k]&&!g.cov[k]) (rows[y]=rows[y]||[]).push('m'+(x-200)); else if(g.cov[k]&&!g.inOutline[k]&&!g.inHole[k]&&!g.inLoad[k]&&!g.holes.some(r=>T.inRing((x+0.5)*0.1,(y+0.5)*0.1,r))) (rows[y]=rows[y]||[]).push('o'+(x-200)); }
      after.diag=Object.entries(rows).map(([y,v])=>y+':'+v.length+':'+v.slice(0,4).join(',')).join(' | '); }
    after.miss=+(1-c.fill).toFixed(3); after.over=+(over/g.solidCells).toFixed(3); }
  T.setTab(true); T.startTest(); T.setTab(false); if(T.test) T.test.fast=false; // as in play: not the Tab speed-up
  let last='',ph=[],t=0,atFail=null; while(T.test&&t<60*90){ if(T.test.phase!==last){last=T.test.phase;ph.push(last);} if(last==='fail'){atFail=phys(); const bl=T.failShow?T.failShow.loads.length:0; atFail.loadsOff=bl; atFail.loadsAt=T.loads.map(l=>[+(l.body.getPosition().x-20).toFixed(2),+l.body.getPosition().y.toFixed(2)]); if(bl) atFail.phys=true; break;} run(1/60);t++; }
  const res={mon:mon&&Object.fromEntries(Object.entries(mon).filter(([k,v])=>v.peak>0.8||v.bent||v.strain>0)),ready,phases:ph.join('>'),pass:!!T.progress.done[key],build:Object.assign(after,{fill:+c.fill.toFixed(3),hole:+c.hole.toFixed(3),load:c.load}),fail:atFail};
  if(T.test)run(4); T.mode="map"; return res;}
