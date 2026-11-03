# 23: Headings from the contents list

**What to build:** In a Tagged PDF, a section title that the contents list names but the tags mark only as a paragraph, or as the opening paragraph of a full-width table row, becomes a heading. Comparing with Word's PDF import, PyMuPDF4LLM and Docling on the confidential samples showed every one of them found such titles where the tag path didn't, though each also promoted many lines that aren't titles. (ADR 0008, StR-017)

**Blocked by:** 17 (PDF structure from tags)

**Status:** ready-for-agent

- [x] Titles are matched in the contents list's order: a tagged heading or a promoted block claims the list's next unclaimed title, or the one after it, so the same words elsewhere in the document stay plain text
- [x] A promoted title's level comes from its entry's indentation in the contents list: indented like a tagged heading's entry, it takes that heading's level; each step further in is one level deeper
- [x] A full-width table row opening with the next title splits the table: the title becomes a heading, and the rest of the row's cell stays in the table that follows
- [x] Other short bold lines are not promoted
- [x] S-17 covers a title tagged as a paragraph, one as a table's first row, one opening a later row, and an earlier bold label with the same words as a later title

## Notes

- On a tagged confidential sample, contents titles found as headings rose from 19 of 26 to 24 of 26, with no extra headings elsewhere. The two left sit in the middle of a table cell, which the rule deliberately doesn't search.
- PyMuPDF4LLM (AGPL) and Docling (MIT) were tried as alternatives and did not do better overall: one heading level, many false headings, and running headers kept as text. The permissive-licence rule (ADR 0003) stays.
