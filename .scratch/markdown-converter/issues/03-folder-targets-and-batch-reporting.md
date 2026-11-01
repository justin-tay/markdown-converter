# 03: Folder Targets and batch reporting

**What to build:** A Document User names a folder as the Target and every Source File in it and its subfolders is converted, with sensible skipping, a full Run Summary and a log file. One bad file never stops the run.

**Blocked by:** 01 (Walking skeleton)

**Status:** ready-for-agent

- [x] Folder Target converts every Source File at every depth; `--no-recurse` limits to the top folder (StR-002, StR-003)
- [x] Only Supported Formats are converted; other files are counted as ignored; a single unsupported file gives the message listing Supported Formats and exit code 2 (StR-004)
- [x] Hidden folders, Assets Folders, Converted Documents and the log file are skipped; symlinks are not followed (StR-005)
- [x] Paths with spaces and non-ASCII characters convert (StR-007)
- [x] A damaged file (S-15) fails with a reason and the run continues (StR-050, StR-054)
- [x] Encrypted PDF (S-04) and encrypted Office files are skipped with reason "encrypted" (StR-054)
- [x] XLS (S-08), MSG (S-12), ZIP (S-13), XML and EPUB text convert to Converted Documents
- [x] Run Summary shows converted / Up To Date / failed / ignored counts, each reason, and warnings (StR-051)
- [x] `markdown-converter.log` is written to the output root; on a read-only Target the run continues with a warning (StR-053)
- [x] Source Files' checksums and timestamps are unchanged after a run (StR-044)
- [x] Sample Set generator builds the S-16 folder tree with a hidden folder, an unsupported file and a spaces/non-ASCII subfolder
