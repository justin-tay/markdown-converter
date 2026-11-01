# 11: HTML and EPUB images

**What to build:** Images bundled in an EPUB, and images an HTML file references from the local disk, are copied into the Assets Folder with their links rewritten. Images referenced from the web are left as text links, never fetched, and counted in the Run Summary.

**Blocked by:** 02 (Offline Guard), 05 (Asset Store and Word images)

**Status:** ready-for-agent

- [x] S-10's bundled images are in its Assets Folder and linked (StR-027)
- [x] S-09's local images are copied and links rewritten to relative Asset links (StR-027)
- [x] S-09's remote image link is unchanged and reported as "remote image not fetched"; the Offline Guard test shows no connection was attempted (StR-027, StR-040)
