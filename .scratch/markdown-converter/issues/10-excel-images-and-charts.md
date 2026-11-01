# 10: Excel images and charts

**What to build:** Converting an XLSX saves its Embedded Images and Charts and links them within the owning sheet's section, named by sheet. Hidden sheets are included.

**Blocked by:** 09 (Charts in Word and PowerPoint)

**Status:** ready-for-agent

- [x] S-07's images and charts are saved as `sheet-<Name>-imgNN.<ext>` / `sheet-<Name>-chartNN.xml`, with sheet names sanitised for file systems (StR-020, StR-022)
- [x] Links appear within the owning sheet's section (StR-021)
- [x] Each chart has heading, Chart Data Table and Chart Definition link (StR-025)
- [x] S-07's hidden sheet appears in the output (StR-045)
