# 21: Diagrams in untagged PDFs

**What to build:** In an untagged PDF, a diagram drawn as vector graphics becomes one Figure Snapshot where it sits, instead of scattered label text. ADR 0008 left automatic figure finding for untagged PDFs out because lines and boxes from tables and underlines are easily mistaken for figures; the rules below avoid those. (ADR 0008, StR-046)

**Blocked by:** 18 (PDF layout fallback)

**Status:** ready-for-agent

- [x] Drawn shapes (rectangles, lines, curves) outside every bordered table, and smaller than half the page, are grouped: shapes within 12 pt of each other belong to one group
- [x] A group is a diagram when it has at least 10 shapes, includes a curve or a filled shape, has no more than two words of text inside it per shape, and is at least 1 inch wide and half an inch tall; a lone rule, an underline, a box around a few words or a table told apart by shaded rows is not
- [x] Each diagram becomes one 150 DPI Figure Snapshot of its area (`pNNN-figNN.png`), placed where its top sits among the page's blocks (StR-046, StR-022)
- [x] Text inside a diagram's area is left out of the text, since the picture shows it; Embedded Images inside it are not linked separately
- [x] Figures smaller than `--min-image-size` are skipped (StR-024)
- [x] S-18 gains a diagram (filled boxes joined by a curved arrow, with labels), a borderless table with shaded rows and an underline; only the diagram becomes a picture, and its bordered tables stay Markdown tables

## Notes

- Word's own PDF import (compared with `tools/pdf_to_docx_with_word.ps1`) turned the dense diagrams of an untagged confidential sample into pictures, and kept simpler drawings as editable shapes. That supports capturing dense drawing as a picture.
- On that sample, grouping shapes outside its bordered tables found exactly its diagrams: five groups of 51 to 2,709 shapes, each with curves and filled shapes. Its fill-in form and tables formed no group.
- Labels are dropped from the text rather than kept as well: inside a diagram they are short fragments that read as noise without the picture.
