"""PDF Asset Extractor: one section per page, with that page's images after its text."""

from __future__ import annotations

import io
import re
from pathlib import Path

from markdown_converter.assets import AssetStore
from markdown_converter.options import ConversionOptions

SNAPSHOT_DPI = 150

_PAGE_BREAK = "\x0c"  # pdfminer ends every page with a form feed

# A gap between lines wider than this many line heights starts a new paragraph.
_PARAGRAPH_GAP = 0.6
# Lines that begin a numbered clause or list item: 1. / 1.2 / 1.2.4.a / (a) / a) / (iv) / bullets.
_LIST_LIKE_START = re.compile(r"^(\d{1,9})([.)])(?=\s|$)")
_CLAUSE_LABEL = re.compile(
    r"^(?:\d+(?:\.\d+)*\.(?:[a-z]\.?)?|\d+(?:\.\d+)+(?:\.[a-z])?\.?|\(?[a-z]{1,4}\)|\(\d+\)|[•▪◦–*-])\s"
)

# Raw stream extensions for encodings pypdf can't turn into an image file.
_RAW_EXTENSION_BY_FILTER = {"/JPXDecode": ".jp2", "/JBIG2Decode": ".jb2", "/CCITTFaxDecode": ".ccitt"}


def extract(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    from pypdf import PdfReader

    reader = PdfReader(source)
    texts = _page_texts(markdown, reader, source)
    if not any(text.strip() for text in texts):
        store.warnings.append("no text layer found (scanned pages need OCR, which is out of scope)")
    snapshots = _page_snapshots(source, store) if options.pdf_page_images else {}
    sections = []
    for number, (page, text) in enumerate(zip(reader.pages, texts), start=1):
        location = f"p{number:03d}-"
        links = _save_page_images(page, store, location)
        parts = [
            *([f"![]({snapshots[number]})"] if number in snapshots else []),
            text.strip(),
            *(f"![]({link})" for link in links),
        ]
        body = "\n\n".join(part for part in parts if part)
        sections.append(f"## Page {number}\n\n{body}".rstrip())
    return "\n\n".join(sections) + "\n"


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


def _page_texts(markdown: str, reader, source: Path) -> list[str]:
    """Each page's text.

    markitdown's plain-text path (pdfminer) groups text into blocks by column, so
    a clause label drawn apart from its text ("1.2.4.a" ... "Priority 1") ends
    up separated from it and out of order. For those PDFs the text is read line
    by line instead. Pages markitdown recognised as forms keep its table output.
    """
    pages = markdown.split(_PAGE_BREAK)
    if pages and not pages[-1].strip():
        pages.pop()  # the form feed after the last page
    if len(pages) == len(reader.pages):
        lines = _line_texts(source)
        return lines if len(lines) == len(pages) else pages
    # markitdown's form-layout path joins pages without breaks: convert singly.
    from markitdown import StreamInfo
    from markitdown.converters import PdfConverter
    from pypdf import PdfWriter

    texts = []
    for page in reader.pages:
        writer = PdfWriter()
        writer.add_page(page)
        buffer = io.BytesIO()
        writer.write(buffer)
        buffer.seek(0)
        text = PdfConverter().convert(buffer, StreamInfo(extension=".pdf")).markdown
        texts.append(text.replace(_PAGE_BREAK, ""))
    return texts


def _line_texts(source: Path) -> list[str]:
    """Each page's text read line by line, grouped into paragraphs."""
    import pdfplumber

    texts = []
    try:
        with pdfplumber.open(source) as document:
            for page in document.pages:
                texts.append(_paragraphs(page.extract_text_lines(strip=True)))
                page.close()
    except Exception:
        return []  # fall back to markitdown's text
    return texts


def _paragraphs(lines: list[dict]) -> str:
    """Join lines into paragraphs: a wide vertical gap or a numbered clause starts a new one."""
    out, previous = [], None
    for line in lines:
        text = line["text"]
        if not text:
            continue
        if previous is not None:
            height = max(previous["bottom"] - previous["top"], 1)
            gap = line["top"] - previous["bottom"]
            new_paragraph = gap > height * _PARAGRAPH_GAP or _CLAUSE_LABEL.match(text)
            out.append("\n\n" if new_paragraph else "\n")
        # "3. ..." would be a Markdown list item that viewers renumber; "3\. ..." shows as written.
        out.append(_LIST_LIKE_START.sub(r"\1\\\2", text))
        previous = line
    return "".join(out)


def _save_page_images(page, store: AssetStore, location: str) -> list[str]:
    links = []
    images = page.images
    for name in images.keys():
        try:
            image = images[name]
            data, extension = image.data, Path(image.name).suffix or ".png"
        except Exception:
            data, extension = _raw_image(page, name)
            if data is None:
                continue
            store.warnings.append(f"an image on page {location[1:4].lstrip('0')} uses an encoding "
                                  f"that can't be converted, so it was saved raw ({extension})")
        link = store.add(data, extension, location)
        if link and link not in links:
            links.append(link)
    return links


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
