# 09: Charts in Word and PowerPoint

**What to build:** Each Chart in a DOCX or PPTX appears in the Converted Document as a heading with its title and type, a Chart Data Table of its values, and a link to its Chart Definition (the original chart XML) saved in the Assets Folder (ADR 0002). Charts whose values can't be read still appear with "data not extracted". markitdown's own PPTX chart tables are replaced so all formats look the same.

**Blocked by:** 06 (PowerPoint images)

**Status:** ready-for-agent

- [x] Every chart in S-05 and S-06 appears as `**Chart: <title> (<type> chart)**`, a table of categories × series, and a working link to its `.xml` (StR-025)
- [x] Chart Definitions are named `chartNN.xml` (Word) and `slideNN-chartNN.xml` (PowerPoint) (StR-022)
- [x] A chart with unreadable data still shows heading, "data not extracted" and its Chart Definition link (StR-025)
- [x] No duplicate chart table from markitdown remains in PPTX output
