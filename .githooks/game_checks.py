# Checks for games on the strict rules (owner 24 Nov; CLAUDE.md Testing). Used by the commit check and by the GitHub check on every push.
# A game is on them when it is listed in .githooks/strict-games.txt (one folder name per line); the others keep the "Flow:" line check
# until their full test run is fast enough (at most 30 s).
# For a game on the strict rules:
# 1. A change to its code (its page, src/ or lib/) must add or change a flow (a def f_... in tools/flows.py) in the same change.
# 2. Flows never make moves through the game's insides: no flow may contain a pattern listed in tools/backdoors.txt.
# 3. Its whole current test set passes, in at most 30 seconds, browser start included (owner 25 Nov: raised from 20).
import os, re, subprocess, sys, time, tempfile, shutil
LIMIT_S = 30
HERE = os.path.dirname(os.path.abspath(__file__))
def strict_games():
    p = os.path.join(HERE, 'strict-games.txt')
    return {l.strip() for l in open(p, encoding='utf-8') if l.strip() and not l.startswith('#')} if os.path.exists(p) else set()
def flows_of(text):  # each flow's name and its source
    out, name = {}, None
    for line in (text or '').splitlines():
        m = re.match(r'def (f_\w+)\(', line)
        if m: name = m.group(1); out[name] = []
        elif line and not line[0].isspace(): name = None
        if name: out[name].append(line)
    return {k: '\n'.join(v) for k, v in out.items()}
def check(gamedir, old_flows, new_flows, code_changed, root):
    """The problems found, as lines for the owner (empty: all good)."""
    bad, g = [], os.path.basename(gamedir)
    old, new = flows_of(old_flows), flows_of(new_flows)
    if code_changed and not any(new.get(k) != old.get(k) for k in new):
        bad.append('%s: the game code changed but no flow was added or changed (test first)' % g)
    bd = os.path.join(gamedir, 'tools', 'backdoors.txt')
    if os.path.exists(bd):
        for pat in [l.strip() for l in open(bd, encoding='utf-8') if l.strip() and not l.startswith('#')]:
            for k, src in new.items():
                if pat in src: bad.append('%s: flow %s makes moves through the game\'s insides (%s); play through the screen' % (g, k[2:], pat))
    env = dict(os.environ, TMPDIR=tempfile.mkdtemp(), GIT_DIR=os.path.join(root, '.git'))
    t0 = time.time()
    out = subprocess.run([sys.executable, os.path.join(gamedir, 'tools', 'harness.py'), 'flows'], capture_output=True, text=True, cwd=gamedir, timeout=300, env=env).stdout
    dt = time.time() - t0; shutil.rmtree(env['TMPDIR'], ignore_errors=True)
    lines = [l for l in out.splitlines() if l.startswith(('PASS', 'FAIL'))]
    fails = [l for l in lines if l.startswith('FAIL')]
    if not lines: bad.append('%s: the test set did not run:\n%s' % (g, out.strip()[-400:]))
    bad += ['%s: %s' % (g, l) for l in fails]
    if dt > LIMIT_S: bad.append('%s: the full test run took %.1f s; the limit is %d s' % (g, dt, LIMIT_S))
    return bad
