#!/usr/bin/env python3
"""Mutation testing (owner 24 Nov): break a game in small ways, one at a time, and run its whole test set on each broken copy.
A break that no test catches is a hole in the tests. Usage: python3 tools/mutate.py <game folder name> [how many breaks, default 40]
Prints one line per hole: the line number, the code before and after the break. Seeded, so the same code gives the same breaks.
Breaks (in the game's src/index.html, skipping comments, the test hooks and the sections that only draw): a comparison turned around, a + made -, a number nudged by 1,
true made false, a && made ||."""
import sys, re, os, random, shutil, subprocess, tempfile
CHANGES = [(r'===', '!=='), (r'!==', '==='), (r'>=', '>'), (r'<=', '<'), (r'(?<![=<>!])>(?![=>])', '>='), (r'(?<![=<>!])<(?![=<])', '<='),
           (r' \+ ', ' - '), (r'\btrue\b', 'false'), (r'&&', '||'), (r'(?<![\w.#])(\d+)(?![\w.])', None)]
SKIP = {'SHAPES', 'DRAWING'}  # how things look: line widths and colours are judged by the owner's eye, not by tests
def breaks(src):
    lines, out = src.split('\n'), []
    hooks = next((k for k, l in enumerate(lines) if 'SECTION: TEST HOOKS' in l), len(lines))
    start = next((k for k, l in enumerate(lines) if 'SECTION: SETUP' in l), 0)
    section = ''
    for k in range(start, hooks):
        if 'SECTION:' in lines[k]: section = lines[k].split('SECTION:')[1].split('--')[0].strip()
        if section in SKIP: continue
        code = lines[k].split('//')[0]
        if '<' in code and ('</' in code or code.strip().startswith('<')): continue  # page markup
        for pat, rep in CHANGES:
            for m in re.finditer(pat, code):
                new = str(int(m.group(1)) + 1) if rep is None else rep
                out.append((k, m.start(), m.end(), new))
    return lines, out
def main():
    game = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True).stdout.strip()
    gdir = os.path.join(root, 'games', game); src = open(os.path.join(gdir, 'src', 'index.html'), encoding='utf-8').read()
    lines, all_breaks = breaks(src); random.Random(1).shuffle(all_breaks)
    holes, tried = [], 0
    for k, a, b, new in all_breaks[:n]:
        tmp = tempfile.mkdtemp(); copy = os.path.join(tmp, game); shutil.copytree(gdir, copy, ignore=shutil.ignore_patterns('__pycache__'))
        broken = lines[:]; broken[k] = broken[k][:a] + new + broken[k][b:]
        open(os.path.join(copy, 'src', 'index.html'), 'w', encoding='utf-8').write('\n'.join(broken))
        env = dict(os.environ, GIT_DIR=os.path.join(root, '.git'))
        try: out = subprocess.run([sys.executable, os.path.join(copy, 'tools', 'harness.py'), 'flows'], capture_output=True, text=True, cwd=copy, timeout=120, env=env).stdout
        except subprocess.TimeoutExpired: out = 'FAIL timeout'
        shutil.rmtree(tmp, ignore_errors=True); tried += 1
        if 'FAIL' not in out and 'PASS' in out: holes.append('line %d: %s  ->  %s' % (k + 1, lines[k].strip()[:110], broken[k].strip()[:110]))
    print('%s: %d breaks tried, %d not caught by any test' % (game, tried, len(holes)))
    for h in holes: print('HOLE', h)
main()
