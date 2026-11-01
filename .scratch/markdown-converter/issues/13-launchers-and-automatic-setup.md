# 13: Launchers and automatic Setup

**What to build:** `convert.cmd` (Windows), `convert.sh` (macOS/Linux) and `convert.command` (macOS Finder) let a Document User run the converter by double-click, drag-and-drop or terminal. On first use they perform Setup automatically (private environment, pinned dependencies); later runs skip it. Missing Python gets a friendly message. Options pass straight through, and double-click/drag-and-drop windows stay open at the end.

**Blocked by:** 12 (Interactive prompt)

**Status:** ready-for-agent

- [x] Missing or too-old Python prints install guidance and exits without a stack trace (StR-060)
- [x] First run creates the private environment and converts; later runs skip Setup (StR-061)
- [x] `convert.cmd <path>` and `./convert.sh <path>` convert the Target; options pass through unchanged and exit codes propagate (StR-030, StR-037) — subprocess smoke tests
- [x] No administrator rights needed (StR-065)
- [x] Manual demonstration checklist covers: double-click `convert.cmd`, drag-and-drop onto it, double-click `convert.command`, window pauses at the end (StR-033, StR-034, StR-035)
- [x] `convert.sh` works on Linux (StR-071)
