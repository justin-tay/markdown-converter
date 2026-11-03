# 22: Layout fallback refinements learned from Word's PDF import

**What to build:** Three refinements to the untagged-PDF layout rules (ticket 18), suggested by comparing them with how Word's own PDF import rebuilds an untagged confidential sample. Word agreed with the current rules on Page Furniture, body-size bold section titles and bordered tables, and went further in these three places. (ADR 0008)

**Blocked by:** 18 (PDF layout fallback)

**Status:** needs-triage

- [ ] **Centred titles are headings.** A short, wholly bold line centred on the page (its middle within a few points of the page's text column middle) is a heading even though it isn't at the left margin, ranking one level above left-aligned body-size bold titles. Today such titles (an appendix's title page, say) stay plain paragraphs. (StR-017)
- [ ] **Numbered sub-section titles rank below unnumbered ones.** A bold title starting with a number label ("1. ...", "2.3 ...") takes the level below an unnumbered bold title of the same size, instead of sharing its level. Today every body-size bold title is the same level. (StR-017)
- [ ] **A table that continues onto the next page is one table.** When a page's first block is a bordered table with the same column count and column edges (within a few points) as the previous page's last block, its rows join that table, dropping a first row identical to the table's header row. Today each page gives its own table, each with its header row. The Page Marker for the new page goes before the joined table, as for tagged tables. (StR-017, StR-019)
- [ ] Captions ("Table 1: ...", "Figure 2: ...") stay plain paragraphs. Word makes them headings; that is not wanted here.
- [ ] S-18 (or a new sample) covers each rule, through a conversion run.

## Notes

- Word was driven through COM. Its result was read with `Document.WordOpenXML` and packaged as a `.docx` (see `tools/pdf_to_docx_with_word.ps1`), then converted with the Word converter for comparison.
- Word also joined each paragraph's wrapped lines into one line. The layout path keeps them as separate lines of one paragraph, which displays the same; no change is needed.
- Both Word and the layout rules turned a fill-in form's field labels into headings. No fix is proposed; forms are rare in the documents this tool targets.
