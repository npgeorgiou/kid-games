#!/usr/bin/env python3
# Build the game and run its flow tests: python3 tools/harness.py flows [names]
import sys, subprocess, shutil, pathlib
here = pathlib.Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, str(here / "build.py")], check=True, stdout=subprocess.DEVNULL)
shutil.copy(here / "coloring-book.html", "/tmp/cb.html")
if len(sys.argv) > 1 and sys.argv[1] == "flows":
    sys.path.insert(0, str(here / "tools"))
    import flows
    flows.run(sys.argv[2:])
