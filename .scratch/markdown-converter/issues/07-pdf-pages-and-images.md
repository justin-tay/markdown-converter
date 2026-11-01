# 07: PDF pages and images

**What to build:** Converting a PDF produces one section per page, with that page's Embedded Images saved and linked after the page's text. Scanned PDFs warn that there is no text layer but still yield their images. Images in encodings pypdf can't decode are saved raw with a warning instead of failing the file.

**Blocked by:** 05 (Asset Store and Word images)

**Status:** ready-for-agent

- [x] Each PDF page gets its own section in the Converted Document
- [x] Every raster image in S-01 is saved as `pNNN-imgNN.<ext>` and linked after that page's text (StR-020, StR-021, StR-022)
- [x] S-01's repeated logo is stored once (StR-023)
- [x] S-03 converts with warning "no text layer found" and its page images in the Assets Folder (StR-055)
- [x] An image in an unsupported encoding is saved raw with a warning; the file still converts
