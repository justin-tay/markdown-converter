#!/bin/bash
# Double-click in the macOS Finder to run the Markdown Converter. It asks for a
# file or folder, and the window waits for Enter before closing so the Run
# Summary can be read.
"$(dirname "$0")/convert.sh" "$@"
status=$?
echo
read -r -p "Press Enter to close this window..." _
exit $status
