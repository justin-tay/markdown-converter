import sys

from markdown_converter.cli import main

# Consoles that can't show a character (e.g. "…" or a non-ASCII file name)
# get a replacement mark instead of crashing the run.
sys.stdout.reconfigure(errors="replace")
sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout))
