"""Asset Extractors: move a Source File's images and charts into the Asset Store.

Each extractor takes the Markdown markitdown produced and returns it with Asset
links in place. Formats without an extractor keep markitdown's output as is.
Extractors report anything the user should know through `store.warnings`.
"""

from __future__ import annotations

import base64
import re
import zipfile
from pathlib import Path
from typing import Callable

from markdown_converter import pdf, web_images, xlsx
from markdown_converter.assets import AssetStore, extension_for
from markdown_converter.charts import replace_chart_markers
from markdown_converter.options import ConversionOptions
from markdown_converter.word_numbering import restore_labels

# markitdown (with keep_data_uris) inlines images as Markdown data URIs.
_DATA_URI_IMAGE = re.compile(r"!\[([^\]]*)\]\(data:([^;,)]+)(;base64)?,([^)]*)\)")
_EXTRA_BLANK_LINES = re.compile(r"\n{3,}")
_SLIDE_MARKER = re.compile(r"<!-- Slide number: (\d+) -->")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".emf", ".wmf", ".svg"}

Extractor = Callable[[Path, str, AssetStore, ConversionOptions], str]


def extract_assets(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    extractor = _EXTRACTORS.get(source.suffix.lower())
    return extractor(source, markdown, store, options) if extractor else markdown


def replace_data_uri_images(markdown: str, store: AssetStore, location: str = "") -> str:
    """Swap each inline data-URI image for a link to the saved Asset, in place."""

    def save(match: re.Match) -> str:
        alt, mimetype, is_base64, payload = match.groups()
        data = base64.b64decode(payload) if is_base64 else payload.encode()
        link = store.add(data, extension_for(mimetype), location)
        return f"![{alt}]({link})" if link else ""

    return _EXTRA_BLANK_LINES.sub("\n\n", _DATA_URI_IMAGE.sub(save, markdown))


def _word(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    markdown = restore_labels(replace_chart_markers(replace_data_uri_images(markdown, store), source, store))
    return _add_unlinked_media(markdown, source, "word/media/", store)


def _slides(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    """Name each slide's images after the slide they appear on."""
    parts = _SLIDE_MARKER.split(markdown)
    # split() keeps the captured slide numbers: [before, n1, slide1, n2, slide2, ...]
    out = [replace_data_uri_images(parts[0], store)]
    for number, body in zip(parts[1::2], parts[2::2]):
        location = f"slide{int(number):02d}-"
        body = replace_chart_markers(replace_data_uri_images(body, store, location), source, store, location)
        out.append(f"<!-- Slide number: {number} -->{body}")
    return _add_unlinked_media("".join(out), source, "ppt/media/", store)


def _add_unlinked_media(markdown: str, source: Path, media_folder: str, store: AssetStore) -> str:
    """Save package images markitdown left out (e.g. Word headers) under "Other images"."""
    links = []
    with zipfile.ZipFile(source) as package:
        for name in sorted(package.namelist()):
            extension = Path(name).suffix.lower()
            if not name.startswith(media_folder) or extension not in _IMAGE_EXTENSIONS:
                continue
            data = package.read(name)
            if store.contains(data):
                continue
            link = store.add(data, extension)
            if link:
                links.append(f"![]({link})")
    if not links:
        return markdown
    return f"{markdown.rstrip()}\n\n## Other images\n\n" + "\n\n".join(links) + "\n"


def _with_inline_images(extractor: Extractor) -> Extractor:
    """Save any inline data-URI images first, then run `extractor` on the rest."""

    def extract(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
        return extractor(source, replace_data_uri_images(markdown, store), store, options)

    return extract


_EXTRACTORS: dict[str, Extractor] = {
    ".docx": _word,
    ".pptx": _slides,
    ".pdf": pdf.extract,
    ".xlsx": xlsx.extract,
    ".html": _with_inline_images(web_images.extract_html),
    ".htm": _with_inline_images(web_images.extract_html),
    ".epub": _with_inline_images(web_images.extract_epub),
}
