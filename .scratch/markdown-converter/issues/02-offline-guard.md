# 02: Offline Guard

**What to build:** Every Conversion Run is protected by the Offline Guard (ADR 0001): it is installed before markitdown or any converter library is imported, blocks all non-loopback connections and DNS lookups, sets library offline flags and clears proxy variables. markitdown's online features are disabled, URL Targets are refused, and `--selftest-offline` proves the guard works. A network attempt during one Source File's conversion fails only that file.

**Blocked by:** 01 (Walking skeleton)

**Status:** ready-for-agent

- [x] Guard installed as the first action of `main`, before markitdown is imported (StR-040)
- [x] `--selftest-offline` prints "PASS: network access is blocked during conversion" on a networked machine (StR-043)
- [x] A test-only converter that opens a socket makes that Source File fail with "network access blocked"; other files convert; exit code 1 (StR-041)
- [x] No LLM client, Azure endpoint, plugins, audio or YouTube extras are enabled or installed (StR-042)
- [x] `convert https://example.com/a.pdf` stops with a "local files only" message and exit code 2, with no network access (StR-006)
