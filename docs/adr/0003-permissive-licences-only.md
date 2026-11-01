# Permissively licensed dependencies only

The converter may be shared or embedded in other tools, so every dependency must carry a permissive licence (such as MIT, BSD, Apache-2.0, ISC, PSF, HPND/MIT-CMU, Zlib or CC0). Strong copyleft (GPL, AGPL, LGPL) is never allowed. This rules out PyMuPDF, the most capable library for extracting PDF images and rendering pages, because it is AGPL. We use pypdf (BSD) for PDF Embedded Images and pypdfium2 (Apache-2.0/BSD) for Page Snapshots instead, accepting slightly weaker handling of unusual PDF image encodings.

## Accepted exceptions

Any non-permissive dependency must be listed here with its reason, and in the licence check's reviewed exceptions.

- **certifi (MPL-2.0)**: an unmodified transitive dependency of markitdown (via requests) that can't be removed without dropping markitdown. MPL-2.0 is file-level copyleft: it only obliges sharing changes to certifi's own files, which we never make.
