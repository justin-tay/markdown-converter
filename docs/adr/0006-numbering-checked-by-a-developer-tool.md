# Numbering labels are checked by a developer tool, not during conversion

Word stores no numbering labels as text, so the converter works them out from numbering.xml (ADR 0007). Mistakes there are silent: a wrong or missing label still reads as plausible text. `tools/check_numbering.py` compares the labels the converter writes for a .docx with a reference rendering: a PDF that Word rendered, or LibreOffice's plain-text rendering. A label passes when the reference shows it followed by the start of the paragraph's text anywhere in the document.

At first every Conversion Run did this whenever LibreOffice was installed, recording the result in the front matter and the log. We took it out of conversion: matching each paragraph to one place in the rendering by its text was noisy (repeated text, table cells and footnote numbers gave 32 warnings on three real documents, none of them a real error), LibreOffice isn't the reference Word is, and it ran a separate program the Offline Guard (ADR 0001) can't cover, slowing every Word file.

## Consequences

- Conversion Runs stay fully offline and the front matter carries no numbering fields.
- Developers run the tool when a new kind of document comes in; each real mismatch becomes a rule fix in `word_numbering` with a synthetic test (ADR 0007).
- With a PDF reference, table paragraphs are skipped, because a PDF line runs a row's cells together; LibreOffice's text keeps cells apart, so it can check tables.
- The tool runs LibreOffice outside the Offline Guard; that is acceptable for a developer tool run deliberately, not for conversion.
