# Tries numbers for the trial's paint (its P) against the image similarity test and the passes check (similarity.py) and keeps the best: a simple evolution search
# (each try changes a few numbers of the best so far a little). Usage: tune.py <tries>; prints each better try; best numbers: tune.json in the system temp folder.
import json, random, sys
import look_all_refs as L, similarity as S
RANGE = {'pick': (0.5, 4), 'bead': (0.05, 0.3), 'beads': (0.01, 0.15), 'fling': (0, 1), 'blops': (0, 1), 'groove': (0.1, 1.5), 'churnLo': (0.05, 1), 'churnPow': (1, 4),
         'streaks': (0.2, 1.2), 'tooth': (0.05, 0.5), 'shade': (0.1, 0.8), 'shine': (0.3, 2.5), 'lump': (0.2, 1), 'rim': (0, 1), 'run': (10, 25), 'soft': (0, 0.9), 'level': (0, 4)}
random.seed(1); f = L.OUT / 'tune.json'
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:  # the trial's own numbers, to start from
    b = pw.chromium.launch(); q = b.new_page(); q.goto('file://' + str(L.H / 'acrylic-trial.html')); q.wait_for_function('()=>window.__ready'); own = q.evaluate('()=>__trial.P'); b.close()
best = json.loads(f.read_text()) if f.exists() else {k: own[k] for k in RANGE}
L.TUNE = best; top = S.score(L.paint()) + S.passes()[1]; print('start %.3f' % top, flush=True)
for t in range(int(sys.argv[1])):
    tr = dict(best)
    for k in random.sample(list(RANGE), 3):
        lo, hi = RANGE[k]; cur = tr[k]; tr[k] = round(min(hi, max(lo, cur + random.gauss(0, 0.25) * (hi - lo))), 3)
    L.TUNE = tr; sc = S.score(L.paint()) + S.passes()[1]
    if sc < top: top, best = sc, tr; f.write_text(json.dumps(best)); print('%d %.3f %s' % (t, sc, json.dumps(best)), flush=True)
print('best %.3f %s' % (top, json.dumps(best)))
