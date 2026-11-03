# PDF structure comes from the PDF's tags, not its page layout

A PDF's Converted Document used to be one `## Page N` section per page, with the page's text read line by line. Every page's header and footer ended up in the text, and the only headings were page numbers. Converted Documents from PDFs should read like those from Word documents. Most office PDFs are exported from Word with accessibility tags, which record the author's headings (H1–H6), paragraphs, lists, tables, figures and links, and which mark headers, footers and page numbers as Page Furniture outside the content. Two of the three real-world PDFs checked have them. So a Tagged PDF is converted by walking its tags in their reading order. A PDF without usable tags falls back to layout rules: Page Furniture is a line in the top or bottom 12% of the page whose text, ignoring digits, recurs at the same height on three or more pages; a heading is a short, wholly bold or larger-than-body line at the left margin with space above it; bordered tables become Markdown tables. Page boundaries remain only as hidden Page Markers (`<!-- page 3 -->`), so readers can still find the place in the source.

## Considered Options

- **Improve the layout heuristics only.** The tags already hold what the heuristics would guess at, and guessing gets heading levels and furniture wrong where the tags do not. The heuristics stay as the fallback.
- **PDF → DOCX with Word (COM), then the Word converter.** Windows-only and needs Office installed, so it breaks StR-070/071. Word stops on hidden prompts when automated (a "convert this PDF" notice, then first-run dialogs), so unattended runs hang. Its PDF import rebuilds the document from how the page looks, so it also guesses where the tags would give the answer. ADR 0007 already rejected COM for numbering.
- **PDF → DOCX with LibreOffice.** LibreOffice opens a PDF as a drawing: a sample became thousands of text boxes with no heading styles and its headers and footers still in the body. The resulting Markdown was worse than the original page-by-page output.
- **Pandoc.** Cannot read PDF.

## Consequences

- Heading levels are the author's, as tagged, even when inconsistent (a lettered sub-section tagged at the same level as its numbered section). Correcting them from numbering would be guesswork of its own.
- The tags' reading order is followed, including where it differs from the page (a text box anchored elsewhere appears where its tag sits).
- A document uses the tag path only when its tags reach at least 80% of its non-furniture text; partly tagged PDFs use the layout rules. The log records which path each PDF took.
- Figures drawn as vector graphics in a Tagged PDF are captured by rendering just the figure's area (a Figure Snapshot). Their underlying data cannot be recovered, so ADR 0002's "charts as data" does not extend to PDFs. Untagged PDFs get no automatic figure detection; loose lines and boxes are too easily mistaken for charts, so Page Snapshots remain the way to capture them.
- Heading detection for untagged PDFs is a guess. Documents whose headings are neither bold nor larger than body text get none.
