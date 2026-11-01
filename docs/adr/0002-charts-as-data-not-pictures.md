# Capture Office charts as data and definition, not as rendered pictures

Native Office charts (DOCX/PPTX/XLSX) are stored as XML drawing instructions, not pictures, and markitdown drops them. Rendering them faithfully needs LibreOffice, a large extra install, and redrawing them with a plotting library is only approximate. We instead write each Chart's values into the Converted Document as a Chart Data Table and save the original chart XML as a Chart Definition Asset so it can be re-rendered later. For PDFs, where charts are usually vector drawings, an optional Page Snapshot captures the visual.

## Considered Options

- Embedded images only: loses chart content entirely.
- LibreOffice headless rendering: faithful pictures, but a heavy dependency on every machine and harder to set up offline.
