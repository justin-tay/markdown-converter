# 20: Manual check of PDF structure on confidential samples

**What to build:** A person converts the three confidential sample PDFs used to design ADR 0008 and records the result. They can't be committed, so this is a manual demonstration rather than a test.

**Blocked by:** 17, 18, 19

**Status:** ready-for-human

The samples are kept outside the repository: two tagged PDFs exported from Word, and one untagged PDF.

- [x] Add a "PDF structure" table to `docs/acceptance/manual-demonstrations.md` with the checks below
- [ ] No running header, footer, classification line or page number appears in any of the three Converted Documents (StR-018)
- [ ] Each tagged sample's headings match its contents page (StR-017)
- [ ] Every bold section title in the untagged sample is a heading, and its bordered tables are Markdown tables (StR-017)
- [ ] Drawn figures in the tagged samples appear as Figure Snapshots, or as text only where they just frame text, and a map with its legend is one picture (StR-046)
- [ ] Each document has a Page Marker for every page (StR-019)
- [ ] Record the results in the table
