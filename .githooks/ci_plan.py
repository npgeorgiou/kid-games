#!/usr/bin/env python3
# The GitHub full check's job list: every check of each game the change touches (see changed_games.py).
# Usage: python3 .githooks/ci_plan.py <commit the change starts from>
# Each game lists its checks in games/<game>/tools/ci-checks.txt, one per line: a harness mode and its arguments.
# "flows N" means the play-through tests split over N machines running at once. Games on the strict rules
# (strict-games.txt) have their flows run by the strict check already, so their "flows" line is left out here.
# Prints the jobs as JSON for the workflow's matrix.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changed_games, game_checks
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jobs = []
for g in changed_games.touched_games(sys.argv[1] if len(sys.argv) > 1 else ''):
    p = os.path.join(root, 'games', g, 'tools', 'ci-checks.txt')
    if not os.path.exists(p): continue
    for line in open(p, encoding='utf-8'):
        args = line.split()
        if not args or args[0].startswith('#'): continue
        if args[0] == 'flows':
            if g in game_checks.strict_games(): continue
            n = int(args[1]) if len(args) > 1 else 1
            jobs += [{'game': g, 'check': 'flows', 'shard': k, 'of': n, 'name': '%s flows %d/%d' % (g, k + 1, n)} for k in range(n)]
        else:
            jobs.append({'game': g, 'check': ' '.join(args), 'shard': 0, 'of': 1, 'name': '%s %s' % (g, ' '.join(args))})
print(json.dumps({'include': jobs}))
