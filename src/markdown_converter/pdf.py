"""PDF Asset Extractor: one continuous document with Page Markers, its structure from tags or layout (ADR 0008).

markitdown's text for PDFs is not used: it has no headings, and it keeps every
page's header and footer.
"""

from __future__ import annotations

import io
from pathlib import Path

from markdown_converter import pdf_layout, pdf_tags
from markdown_converter.assets import AssetStore
from markdown_converter.options import ConversionOptions

SNAPSHOT_DPI = 150

# Raw stream extensions for encodings pypdf can't turn into an image file.
_RAW_EXTENSION_BY_FILTER = {"/JPXDecode": ".jp2", "/JBIG2Decode": ".jb2", "/CCITTFaxDecode": ".ccitt"}


def extract(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    import pdfplumber
    from pypdf import PdfReader

    reader = PdfReader(source)
    structure = pdf_tags.read_structure(reader)
    figures = _FigureAssets(source, reader, store)
    try:
        with pdfplumber.open(source) as document:
            objects = pdf_tags.page_objects(document)
            coverage = pdf_tags.tag_coverage(structure, objects) if structure is not None else 0.0
            if coverage >= pdf_tags.MIN_TAG_COVERAGE:
                store.notes.append("structure read from its tags")
                blocks = pdf_tags.blocks(structure, objects, figures)
                for page_number, image in pdf_tags.furniture_images(objects):
                    figures.reached(page_number, image["name"])  # a header logo, say: never linked (StR-018)
            else:
                store.notes.append("structure read from its layout " + (
                    "(no tags)" if structure is None else f"(tags reach only {coverage:.0%} of its text)"))
                blocks = pdf_layout.blocks(document)
    finally:
        figures.close()
    if not any(item["text"].strip() for items in objects.values() for item in items
               if item["object_type"] == "char"):
        store.warnings.append("no text layer found (scanned pages need OCR, which is out of scope)")
    blocks = figures.with_leftovers(blocks)
    snapshots = _page_snapshots(source, store) if options.pdf_page_images else {}
    return _assemble(blocks, len(reader.pages), snapshots)



def _assemble(blocks: list[pdf_tags.Block], page_count: int, snapshots: dict[int, str]) -> str:
    """Join the blocks, with each page's Page Marker before the first block that starts on it (StR-019).

    Every page gets exactly one marker, for its Page Snapshot to follow. A page
    on which no block starts (one holding only the end of a table, say) gets
    its marker just before the next page's, or at the end. Where the tags'
    reading order returns to a page already marked, no second marker is added.
    """
    first_blocks = {}
    for index, block in enumerate(blocks):
        first_blocks.setdefault(block.page, index)
    markers_before: dict[int, list[int]] = {}  # block index -> pages marked just before it
    for page in range(1, page_count + 1):
        following = next((first_blocks[later] for later in range(page, page_count + 1) if later in first_blocks), None)
        markers_before.setdefault(following, []).append(page)
    out: list[str] = []

    def mark(index: int | None) -> None:
        for page in markers_before.get(index, []):
            out.append(f"<!-- page {page} -->")
            if page in snapshots:
                out.append(f"![]({snapshots[page]})")

    for index, block in enumerate(blocks):
        mark(index)
        out.append(block.markdown)
    mark(None)
    return "\n\n".join(out) + "\n"


def _page_snapshots(source: Path, store: AssetStore) -> dict[int, str]:
    """Page Snapshots: every page as a PNG, capturing vector charts (ADR 0002)."""
    import pypdfium2

    links = {}
    document = pypdfium2.PdfDocument(source)
    try:
        for number, page in enumerate(document, start=1):
            image = page.render(scale=SNAPSHOT_DPI / 72).to_pil()
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            links[number] = store.add(buffer.getvalue(), ".png", f"p{number:03d}-", kind="page")
            page.close()
    finally:
        document.close()
    return links


def _save_page_images(page, store: AssetStore, location: str, skip=()) -> list[str]:
    links = []
    for name in page.images.keys():
        if str(name) in skip:  # pypdf names nested images with a list
            continue
        link = _save_image(page, name, store, location)
        if link and link not in links:
            links.append(link)
    return links


def _save_image(page, name: str, store: AssetStore, location: str) -> str | None:
    """Save one of the page's Embedded Images under its pypdf name; return its link."""
    try:
        image = page.images[name]
        data, extension = image.data, Path(image.name).suffix or ".png"
    except Exception:
        data, extension = _raw_image(page, name)
        if data is None:
            return None
        store.warnings.append(f"an image on page {location[1:4].lstrip('0')} uses an encoding "
                              f"that can't be converted, so it was saved raw ({extension})")
    return store.add(data, extension, location)


def _last_name(key) -> str:
    """An image's own XObject name from pypdf's key: "/Im1", or a path such as ["/Fm0", "/Im1"] when nested."""
    parts = key if isinstance(key, (list, tuple)) else str(key).split("/")
    return str(parts[-1]).lstrip("/")


class _FigureAssets:
    """A Tagged PDF's figures as Assets: Embedded Images saved as-is (StR-021), or Figure Snapshots (StR-046).

    Images no figure reached are linked at the end of their page afterwards.
    """

    def __init__(self, source: Path, reader, store: AssetStore):
        self._source, self._reader, self._store = source, reader, store
        self._reached: dict[int, set[str]] = {}
        self._rendering = None

    def link(self, page_number: int, image_name: str) -> str | None:
        """Save one of the page's Embedded Images and return its link."""
        name = self.reached(page_number, image_name)
        if name is None:
            return None
        return _save_image(self._reader.pages[page_number - 1], name, self._store, f"p{page_number:03d}-")

    def reached(self, page_number: int, image_name: str):
        """Record that a figure covers this image, so it isn't linked again at the end of its page."""
        page = self._reader.pages[page_number - 1]
        name = next((key for key in page.images.keys() if _last_name(key) == image_name), None)
        if name is not None:
            self._reached.setdefault(page_number, set()).add(str(name))
        return name

    def snapshot(self, page_number: int, bbox: tuple[float, float, float, float]) -> str | None:
        """Render just `bbox` (PDF user space: x0, y0, x1, y1) of the page as a Figure Snapshot."""
        import pypdfium2

        if self._rendering is None:
            self._rendering = pypdfium2.PdfDocument(self._source)
        page = self._rendering[page_number - 1]
        try:
            left, bottom, right, top = page.get_cropbox()
            x0, y0, x1, y1 = max(bbox[0], left), max(bbox[1], bottom), min(bbox[2], right), min(bbox[3], top)
            if x1 <= x0 or y1 <= y0:
                return None
            image = page.render(scale=SNAPSHOT_DPI / 72, crop=(x0 - left, y0 - bottom, right - x1, top - y1)).to_pil()
        finally:
            page.close()
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        return self._store.add(buffer.getvalue(), ".png", f"p{page_number:03d}-", kind="fig")

    def close(self) -> None:
        if self._rendering is not None:
            self._rendering.close()

    def with_leftovers(self, blocks: list[pdf_tags.Block]) -> list[pdf_tags.Block]:
        """`blocks` with each page's unreached images after the last block of that page."""
        result = list(blocks)
        for number, page in enumerate(self._reader.pages, start=1):
            links = _save_page_images(page, self._store, f"p{number:03d}-", self._reached.get(number, ()))
            if not links:
                continue
            position = max((i + 1 for i, block in enumerate(result) if block.page == number), default=len(result))
            result[position:position] = [pdf_tags.Block(number, f"![]({link})") for link in links]
        return result


def _raw_image(page, name: str) -> tuple[bytes | None, str]:
    """The image's still-encoded stream, for encodings pypdf can't decode.

    Only images placed directly on the page are reachable; ones nested inside
    form XObjects (names like "/Fm0/Im1") are skipped.
    """
    try:
        xobject = page["/Resources"]["/XObject"][name].get_object()
    except Exception:
        return None, ""
    filters = xobject.get("/Filter")
    filters = list(filters) if isinstance(filters, list) else [filters]
    extension = next((_RAW_EXTENSION_BY_FILTER[f] for f in filters if f in _RAW_EXTENSION_BY_FILTER), ".bin")
    return xobject._data, extension  # pypdf keeps the encoded bytes in _data
