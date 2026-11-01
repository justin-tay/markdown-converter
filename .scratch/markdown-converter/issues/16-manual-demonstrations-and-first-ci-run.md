# 16: Manual demonstrations and first CI run

**What to build:** Close the acceptance gaps left by ticket 15. A person performs the manual demonstrations on Windows and macOS (Apple silicon and Intel), and the first CI run confirms the automated suite, licence check and Offline Bundle installs on macOS and Linux. Results are recorded in `docs/acceptance/strs-acceptance.md`.

**Blocked by:** 15 (README and StRS acceptance pass)

**Status:** ready-for-human

- [ ] Push the branch and confirm the CI `test` job passes on windows-latest, macos-latest, macos-15-intel and ubuntu-latest (StR-070, StR-071, StR-072)
- [ ] Confirm the CI `offline-bundle` job installs every platform's bundle with no package index (StR-062)
- [ ] Perform demonstrations W1-W6 on Windows 11 and record results (StR-031-StR-035, StR-060, StR-061, StR-065)
- [ ] Perform demonstrations M1-M4 on an Apple-silicon Mac and an Intel Mac and record results (StR-034, StR-035, StR-060, StR-061, StR-065)
- [ ] Perform demonstration B1 with networking disabled on each platform (StR-062)
- [ ] Update the acceptance record's Windows and macOS columns from "Pending CI" / "Manual" to the actual results
- [ ] Decide whether StR-029 (convert EMF/WMF to PNG, a Could) is wanted; Pillow can only render EMF/WMF on Windows
