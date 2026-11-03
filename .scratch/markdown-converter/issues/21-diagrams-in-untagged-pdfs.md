# 21: Diagrams in untagged PDFs

**What to build:** To be decided. In an untagged PDF, a diagram drawn as vector graphics with text labels comes out as scattered label text, and only `--pdf-page-images` captures the picture. ADR 0008 left automatic figure finding for untagged PDFs out because lines and boxes from tables and underlines are easily mistaken for figures.

**Blocked by:** 18 (PDF layout fallback)

**Status:** needs-triage

Example: the untagged confidential sample used for ticket 18 (kept outside the repository) has a wiring diagram whose short labels are larger-than-body text among drawn shapes.

Questions to settle before it is ready:

- Is there enough of a pattern (an area dense with curves and short labels, outside any bordered table) to find such diagrams without false hits on the other samples?
- If one is found, should its labels be dropped from the text in favour of a Figure Snapshot, or kept as well?
