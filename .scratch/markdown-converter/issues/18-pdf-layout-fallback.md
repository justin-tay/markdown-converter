# 18: PDF layout fallback for untagged PDFs

**What to build:** A PDF without usable tags gets its Page Furniture removed and its headings and bordered tables recovered from layout, in the same continuous document with Page Markers that ticket 17 introduced. (ADR 0008)

**Blocked by:** 17 (PDF structure from tags)

**Status:** ready-for-agent

- [x] Add S-18 to `tests/sample_set.py` (reportlab is fine, as it writes no tags) with the content listed in StRS §6.2
- [x] A line in the top or bottom 12% of the page whose text, ignoring digits, recurs at the same height (±3 pt) on three or more pages is left out, so S-18's header and its changing page-number footers are gone (StR-018)
- [x] S-18's table header row that repeats on its second page is kept, because lines inside a bordered table are never Page Furniture (StR-018)
- [x] A line under about 15 words, wholly bold or larger than body text, at the left margin, with space above it, is a heading; consecutive heading lines of the same style join into one heading (StR-017)
- [x] Larger sizes take higher levels and body-size bold takes the next level down; levels are closed up so the top one used is `#` (StR-017)
- [x] Bordered tables become Markdown tables with empty columns dropped; borderless tables stay as paragraphs (StR-017)
- [x] Numbered clauses still start new paragraphs and keep their labels as written, as today
- [x] PDFs with a structure tree that reaches less than 80% of their text take this path, and the log says so

## Notes from the prototype

- Reference document: a long untagged confidential sample kept outside the repository. Its headings are all bold, the same size as body text; its only larger text is diagram labels and form titles. Its footers change from one appendix to the next, which is why the rule counts same-height repeats rather than "on half the pages".
- On it the rule removed every header and footer except one that was printed on the same line as another, and found most section titles.
- Use `x_tolerance=1.5` in `extract_text_lines`. At the default, tightly set headings ran together with no spaces.
- `page.find_tables()` split some cells into extra empty columns where border lines doubled up; drop columns that are empty in every row.
- A larger-than-body line inside a drawing (diagram labels) must not become a heading. The left-margin and space-above checks covered this on the reference document.
