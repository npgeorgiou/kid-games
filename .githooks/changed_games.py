#!/usr/bin/env python3
# Which games a change touches, so GitHub runs only their tests (owner 24 Nov: a push in one game runs only that game's tests).
# 1. A changed file in games/<game>/ touches that game.
# 2. A changed file anywhere else touches every game (shared code, test tools, GitHub setup), except text files (.md), which touch none.
# 3. An unknown starting commit (a new branch, a first push) touches every game.
import os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def all_games():
    return sorted(g for g in os.listdir(os.path.join(ROOT, 'games')) if os.path.isdir(os.path.join(ROOT, 'games', g)))


def start_commit(base):
    # Where this branch's change starts: the last commit it shares with <base>; None when <base> is unknown.
    if not base or set(base) == {'0'} or subprocess.run(['git', 'cat-file', '-e', base + '^{commit}'], cwd=ROOT, capture_output=True).returncode:
        return None
    return subprocess.run(['git', 'merge-base', base, 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() or base


def changed_files(base):
    start = start_commit(base)
    if start is None: return None
    return subprocess.run(['git', 'diff', '--name-only', start, 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()


def touched_games(base):
    files = changed_files(base)
    games = all_games()
    if files is None: return games
    touched = set()
    for f in files:
        parts = f.split('/')
        if parts[0] == 'games' and len(parts) > 2: touched.add(parts[1])
        elif not f.endswith('.md'): return games
    return [g for g in games if g in touched]
