#!/usr/bin/env python3
# Checks the rule that picks which games' tests run (changed_games.py). Run by ci_check.py on every push.
# Owner 24 Nov 22:14: a new branch's first push ("nothing came before") ran every game's tests; it must run only the games it changes.
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import changed_games

def git(d, *a): subprocess.run(['git', '-C', d, *a], check=True, capture_output=True)

def main():
    with tempfile.TemporaryDirectory() as d:
        git(d, 'init', '-q', '-b', 'main'); git(d, 'config', 'user.email', 't@t'); git(d, 'config', 'user.name', 't')
        for g in ('a', 'b'):
            os.makedirs(os.path.join(d, 'games', g)); open(os.path.join(d, 'games', g, 'x.js'), 'w').write('1')
        git(d, 'add', '-A'); git(d, 'commit', '-qm', 'start'); git(d, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        git(d, 'checkout', '-qb', 'work'); open(os.path.join(d, 'games', 'a', 'x.js'), 'w').write('2'); git(d, 'commit', '-qam', 'a')
        changed_games.ROOT = d
        got = changed_games.touched_games('0' * 40)
        ok = got == ['a']
        print(('PASS' if ok else 'FAIL') + ' a new branch\'s first push runs only the games it changes: %s' % got)
        return ok

if __name__ == '__main__': sys.exit(0 if main() else 1)
