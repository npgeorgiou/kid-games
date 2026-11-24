#!/usr/bin/env python3
# The GitHub check: the same strict checks as the commit check, on every push, on GitHub's own machines (owner 24 Nov).
# Usage: python3 .githooks/ci_check.py <commit before the push>
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game_checks
root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
base = sys.argv[1] if len(sys.argv) > 1 and subprocess.run(['git', 'cat-file', '-e', sys.argv[1]]).returncode == 0 else 'HEAD~1'
changed = subprocess.run(['git', 'diff', '--name-only', base, 'HEAD'], capture_output=True, text=True).stdout.split()
problems = []
for g in sorted(game_checks.strict_games()):
    if not os.path.isdir(os.path.join(root, 'games', g)): continue
    code = any(f.startswith('games/%s/' % g) and (f.endswith('.html') or '/src/' in f or '/lib/' in f) for f in changed)
    f = 'games/%s/tools/flows.py' % g
    old = subprocess.run(['git', 'show', '%s:%s' % (base, f)], capture_output=True, text=True).stdout
    problems += game_checks.check(os.path.join(root, 'games', g), old, open(os.path.join(root, f), encoding='utf-8').read(), code, root)
print('\n'.join(problems) or 'all checks passed')
sys.exit(1 if problems else 0)
