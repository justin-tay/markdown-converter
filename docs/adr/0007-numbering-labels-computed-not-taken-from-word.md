# Numbering labels are computed from numbering.xml, not taken from Word

Labels such as 1.2.4.a must match what Word shows, because cross-references depend on them. markitdown (via mammoth) drops them, and so does pandoc, so the converter computes each label itself from numbering.xml and styles.xml. We considered taking labels from Word instead, through its COM interface (`Range.ListFormat.ListString`), wherever Word is installed, since Word defines the numbering. We rejected it: COM reports a hidden paragraph's label (a paragraph whose mark is formatted hidden, which templates use to step a list's chapter number on) against the following paragraph, giving "10" where Word displays "10.1". Checked against PDFs that Word itself rendered, the computed labels matched every multi-level label in three real documents (1,748 labels), while the COM labels did not.

## Consequences

- Accuracy depends on the converter following Word's numbering rules. Each mismatch found becomes a rule fix with a synthetic test; `tools/check_numbering.py` (ADR 0006) is how mismatches are found.
- No dependency on Word, so labels are the same on every platform and the Offline Guard (ADR 0001) is not weakened.
- To check labels against Word, compare with a PDF that Word rendered, not with COM's ListString.
- Empty numbered paragraphs that aren't hidden get no label, although Word prints their number on an empty line.
