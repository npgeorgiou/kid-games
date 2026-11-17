()=>{const T=__tb, i=window.__i;
  if(window.__st==="build"&&!T.auto){window.__st="wait";window.__t=performance.now();}
  if(window.__st==="wait"){ if(T.testReady()){T.startTest();window.__st="test";}
    else if(performance.now()-window.__t>20000) return "not ready: "+JSON.stringify(T.check&&{fill:+T.check.fill.toFixed(3),hole:+T.check.hole.toFixed(3),load:T.check.load}); }
  if(window.__st==="test"&&T.test&&T.test.phase!==window.__ph){window.__ph=T.test.phase;(window.__phs=window.__phs||[]).push(T.test.phase);}
  if(window.__st==="test"&&!T.test) return (window.__phs||[]).join(">")+" "+ (T.progress.done[T.LEVELS[i].key]?"PASS":"FAIL");
  return "";}
