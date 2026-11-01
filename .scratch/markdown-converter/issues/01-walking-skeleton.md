# 01: Walking skeleton — one file to a Converted Document

**What to build:** A Document User runs `python -m markdown_converter <file>` on a single text-type Source File (e.g. CSV, JSON, HTML, DOCX text) and gets `<name>.md` beside it, produced via markitdown, with front matter, a progress line, a minimal Run Summary and a correct exit code. This establishes the single in-process entry point `main(argv, stdin, stdout) -> exit code`, the test harness around it, the Sample Set generator, pinned dependencies, CI on Windows and macOS, and the dependency licence check. See spec: `.scratch/markdown-converter/spec.md`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [x] `main(argv, stdin, stdout)` returns an exit code and is what `python -m markdown_converter` calls
- [x] Converting S-11 CSV/JSON/XML and a text-only DOCX produces `<name>.md` beside each, UTF-8, structure preserved (StR-001, StR-010, StR-014)
- [x] Front matter with `source`, `format`, `converted` (ISO 8601), `converter_version`; `--no-front-matter` removes it (StR-015)
- [x] Progress line `[1/1] <name> … ok` and a Run Summary are printed (StR-036)
- [x] Exit codes: 0 success, 1 failure, 2 invalid usage (bad path, bad option) (StR-052)
- [x] `--help` lists the options implemented so far (StR-037)
- [x] Sample Set generator script exists and builds the samples this ticket needs deterministically
- [x] All dependency versions pinned, markitdown with only the needed extras (StR-063)
- [x] CI runs the suite on Windows and macOS (StR-070)
- [x] Automated licence report fails on any dependency that is neither permissive nor an exception recorded in ADR 0003 (StR-072)
