#!/usr/bin/env python3
# A test copy of the built game with other jar odds, for the owner to try a rule by hand (owner 28 Nov):
#   python3 tools/test_page.py <out.html> kind=share ...   e.g. tools/test_page.py /tmp/tiles.html coins=50 tile=50
# Build first (tools/harness.py); the shares are weights, as in JAR_MIX.
import sys, re, json, pathlib
here = pathlib.Path(__file__).resolve().parent.parent
page = (here / 'oi-apoikoi.html').read_text()
mix = {k: int(v) for k, v in (a.split('=') for a in sys.argv[2:])}
page, n = re.subn(r'const JAR_MIX = \{[^}]*\};', 'const JAR_MIX = %s;' % json.dumps(mix).replace('"', ''), page, count=1)
if n != 1: sys.exit('JAR_MIX not found in the built page')
pathlib.Path(sys.argv[1]).write_text(page)
