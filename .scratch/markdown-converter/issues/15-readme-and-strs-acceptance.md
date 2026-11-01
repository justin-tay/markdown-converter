# 15: README and StRS acceptance pass

**What to build:** A README that lets a Document User and Installer use the tool without help, and a final acceptance pass proving every Must requirement in the StRS against the full Sample Set on Windows and macOS.

**Blocked by:** 02 (Offline Guard), 04 (Output placement and re-runs), 08 (PDF Page Snapshots), 10 (Excel images and charts), 11 (HTML and EPUB images), 14 (Offline Bundle)

**Status:** ready-for-agent

- [x] README covers install, double-click / drag-and-drop / terminal usage, all options, offline guarantee and self-test, Offline Bundle, output layout and Name Collisions (StR-038)
- [x] README discloses that speaker notes, hidden slides and hidden sheets appear in output and Word comments/tracked changes aren't specially handled (StR-045)
- [x] README lists the EMF/WMF caveat and the known limitations from StRS Section 5
- [ ] Full S-16 run passes on Windows and macOS with the expected outcome per sample — passes on Windows (`test_acceptance.py`); macOS pending the first CI run (ticket 16)
- [x] Every Must requirement in the StRS is checked off against its acceptance criteria; any gaps raised as new tickets
