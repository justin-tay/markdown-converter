# 17: PDF structure from tags

**What to build:** A Tagged PDF converts into one continuous Converted Document built from its tags, in the tags' reading order: headings at their tagged levels, paragraphs, lists with labels as written, tables (one per table, even across pages), a clean contents list and links. Page Furniture is left out because the tags leave it outside the content. Page boundaries become hidden Page Markers instead of `## Page N` sections. PDFs whose tags reach less than 80% of their text keep today's behaviour until ticket 18 replaces it; the log says which way each PDF was read. (ADR 0008)

**Blocked by:** none

**Status:** ready-for-agent

- [x] Add S-17 to `tests/sample_set.py`: a tagged PDF built from raw PDF objects (reportlab can't write tags) with the content listed in StRS §6.2
- [x] S-17's headings come out at their tagged levels, with empty headings skipped (StR-017)
- [x] Numbered and lettered list labels appear as written and escaped (`1\.`), bullets as `- ` items with nested bullets indented; numbered and lettered items, nested or not, are unindented paragraphs, as Word documents' numbering is written (ADR 0007) (StR-017)
- [x] The two-page table is one Markdown table with no Page Marker inside it; each paragraph or list item in a cell is a `<br>`-separated line (a line that wraps within one paragraph can't be told from a line break in a PDF, so it is joined); merged cells leave the cells they cover blank, across columns and down rows (StR-017, StR-019)
- [x] The contents list keeps entry titles without dot leaders or page numbers (StR-017)
- [x] The web link is a Markdown link; a link to another page of the PDF is plain text (StR-017)
- [x] No header, footer or page number text appears (StR-018)
- [x] One `<!-- page N -->` per page, before the first block that starts on that page (StR-019)
- [x] Embedded Images inside a tagged figure are linked at the figure's place with its alternative text (StR-021)
- [x] With `--pdf-page-images`, each Page Snapshot is linked straight after its Page Marker (StR-026)
- [x] Existing PDF tests updated from `## Page N` sections to Page Markers; scanned and encrypted PDF behaviour unchanged (StR-054, StR-055)

## Notes from the prototype

A throwaway prototype of this ticket and ticket 18 was run against three confidential sample PDFs kept outside the repository.

- `pdfplumber.structure.PDFStructTree(pdf)` walks the whole document; each element has `page_number`, `mcids`, `children`, `alt_text` and `actual_text`. Characters carry `mcid`, so index page objects by `(page, mcid)` once. Avoid `page.structure_tree`: its `to_dict()` fails on Python 3.14 ("cannot pickle 'BufferedReader'").
- Extract an element's text with one `extract_text()` call over all its characters per page. Calling it per character spaced every letter out.
- Tags can put content out of page order (a text box near the end of a document tagged near the start).
- Word tags lettered sub-sections at the same level as numbered sections (an "(A)" sub-section as H1). That is expected (ADR 0008).
- Tag coverage on both Word-exported samples was 100%.
