# 19: PDF Figure Snapshots

**What to build:** In a Tagged PDF, each figure drawn as vector graphics, or made of several image pieces with drawing over them, is rendered as one Figure Snapshot of just its area and linked where the figure is tagged. Charts drawn in a PDF are then captured without `--pdf-page-images`. (ADR 0008)

**Blocked by:** 17 (PDF structure from tags)

**Status:** ready-for-agent

- [x] S-17's vector chart figure becomes one 150 DPI `p00N-fig01.png` linked at its place, with the figure's alternative text as the image text (StR-046, StR-022)
- [x] A figure holding a single image and nothing else is saved as that Embedded Image in its original format, not rendered (StR-046, StR-020)
- [x] A figure made of several images, or images with drawing over them, becomes one Figure Snapshot instead of separate pieces (StR-046)
- [x] S-17's text box (a figure that is mostly tagged text) produces no picture (StR-046)
- [x] Figures smaller than `--min-image-size` are skipped (StR-046, StR-024)
- [x] The figure's area comes from its `BBox` attribute or, failing that, from the bounds of its own marked content
- [x] Rendering uses pypdfium2, already a dependency (ADR 0003)

## Notes from the prototype

- A Word-exported confidential sample has tagged figures with no raster image, which are lost today, and a screenshot with drawn markings that today becomes several separate image pieces.
- Another sample's figures have no `BBox` attribute, so the area has to be worked out from the figure's marked content.
- pypdfium2 renders an area with `page.render(scale=150/72, crop=(left, bottom, right, top))`, where each value is the margin to cut from that side in points.
