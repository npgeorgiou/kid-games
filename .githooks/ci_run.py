#!/usr/bin/env python3
# One job of the GitHub full check (see ci_plan.py): builds the game, runs one of its checks, prints its result lines.
# Usage: python3 .githooks/ci_run.py <game> "<check>" <shard> <of>
# The job fails when the check exits with an error, prints no PASS (or OK) line, or prints any FAIL line.
import os, re, subprocess, sys
game, check, shard, of = sys.argv[1], sys.argv[2].split(), int(sys.argv[3]), int(sys.argv[4])
gamedir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'games', game)
if os.path.exists(os.path.join(gamedir, 'build.py')): subprocess.run([sys.executable, 'build.py'], cwd=gamedir, check=True, stdout=subprocess.DEVNULL)
if check == ['flows']:
    sys.path.insert(0, os.path.join(gamedir, 'tools'))
    import flows
    check = ['flows'] + list(flows.FLOWS)[shard::of]
r = subprocess.run([sys.executable, os.path.join('tools', 'harness.py')] + check, cwd=gamedir, capture_output=True, text=True)
lines = (r.stdout + r.stderr).splitlines()
result = [l for l in lines if re.search(r'\b(PASS|FAIL|OK)\b', l)]
print('\n'.join(result) or '\n'.join(lines[-30:]))
fails = [l for l in result if re.search(r'\bFAIL\b', l)]
ok = r.returncode == 0 and not fails and any(re.search(r'\b(PASS|OK)\b', l) for l in result)
print('%s: %d FAIL, exit %d' % (' '.join(sys.argv[1:3]), len(fails), r.returncode))
sys.exit(0 if ok else 1)
