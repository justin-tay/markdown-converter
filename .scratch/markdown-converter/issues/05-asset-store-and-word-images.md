# 05: Asset Store and Word images

**What to build:** Converting a DOCX saves its Embedded Images into `<name>_assets/` in their original formats and links them inline where they appeared, using relative links and Word Asset Names. Identical images are stored once; tiny images can be dropped; EMF/WMF images are kept with a warning. No Assets Folder appears when there is nothing to save.

**Blocked by:** 01 (Walking skeleton)

**Status:** ready-for-agent

- [x] Every image in S-05 appears in its Assets Folder in its original format (StR-020)
- [x] Image links appear at the image's original position in the text (StR-021)
- [x] Asset Names follow `img01.png`, `img02.jpg`, … (StR-022)
- [x] All links are relative; moving the `.md` with its Assets Folder keeps links working (StR-016)
- [x] An image repeated with identical content is saved once and linked from every place (StR-023)
- [x] `--min-image-size <px>` drops smaller images and their links (StR-024)
- [x] S-05's EMF image is saved as-is and named in a Run Summary warning (StR-028)
- [x] Converting a CSV creates no Assets Folder (StR-010)
