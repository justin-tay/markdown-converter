# 08: PDF Page Snapshots

**What to build:** With `--pdf-page-images`, every PDF page is rendered to a 150 DPI PNG Page Snapshot and linked at the top of that page's section, capturing vector charts. Off by default.

**Blocked by:** 07 (PDF pages and images)

**Status:** ready-for-agent

- [x] With `--pdf-page-images` on S-02, one PNG per page exists and is linked at the start of each page section (StR-026)
- [x] Without the option, no Page Snapshots are produced
- [x] Rendering uses a permissively licensed library (ADR 0003)
