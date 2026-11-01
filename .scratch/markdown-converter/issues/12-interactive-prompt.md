# 12: Interactive prompt

**What to build:** Started without a Target, the converter asks for one, accepts a pasted path with or without quotes, asks again when the path doesn't exist, and — for a folder typed at the prompt — shows how many Supported Files it found and asks to confirm. Targets given as an argument are never confirmed.

**Blocked by:** 03 (Folder Targets and batch reporting)

**Status:** ready-for-agent

- [x] With no argument, a prompt is shown via `stdout` and the path read from `stdin` (StR-031)
- [x] Quoted and unquoted paths both work; a nonexistent path re-prompts (StR-031)
- [x] A prompted folder shows "Found N supported files, convert? [Y/n]"; answering `n` converts nothing (StR-032)
- [x] A folder given as an argument converts without confirmation
