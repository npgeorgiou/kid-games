#!/usr/bin/env python3
# Build the game and run its flow tests: python3 tools/harness.py flows [names]
import sys, subprocess, pathlib
if subprocess.run(['git', 'config', 'core.hooksPath'], capture_output=True, text=True).stdout.strip() != '.githooks': sys.exit('tests refused: the commit gate is off in this copy; run: git config core.hooksPath .githooks')
here = pathlib.Path(__file__).resolve().parent.parent
if (here / "src" / "index.html").exists(): subprocess.run([sys.executable, str(here / "build.py")], check=True, stdout=subprocess.DEVNULL)  # no source yet: every flow reports FAIL
if len(sys.argv) > 1 and sys.argv[1] == "flows":
    sys.path.insert(0, str(here / "tools"))
    import flows
    flows.run(sys.argv[2:])
