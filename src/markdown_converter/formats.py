"""Supported Formats and the markitdown converter that handles each one.

Each format is routed to exactly one converter. markitdown's own dispatcher
guesses the type and falls back to other converters, which would silently turn a
damaged Word file into plain text; routing by extension makes damage a failure.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from markitdown import DocumentConverter, MarkItDown, StreamInfo
from markitdown import converters

from markdown_converter.office import WordConverter, PowerPointConverter

_CONVERTER_BY_EXTENSION: dict[str, Callable[[], DocumentConverter]] = {
    ".pdf": converters.PdfConverter,
    ".docx": WordConverter,
    ".pptx": PowerPointConverter,
    ".xlsx": converters.XlsxConverter,
    ".xls": converters.XlsConverter,
    ".html": converters.HtmlConverter,
    ".htm": converters.HtmlConverter,
    ".csv": converters.CsvConverter,
    ".json": converters.PlainTextConverter,
    ".xml": converters.PlainTextConverter,
    ".epub": converters.EpubConverter,
    ".msg": converters.OutlookMsgConverter,
    # Files inside an archive go through markitdown's own dispatcher (plugins off);
    # the Offline Guard still applies, and no Assets are extracted from them.
    ".zip": lambda: converters.ZipConverter(markitdown=MarkItDown(enable_plugins=False)),
}

# How Supported Formats are named to users, e.g. in error messages.
SUPPORTED_FORMAT_NAMES = (
    "PDF", "DOCX", "PPTX", "XLSX", "XLS", "HTML/HTM", "CSV", "JSON", "XML", "EPUB", "MSG", "ZIP",
)


def is_supported(path: Path) -> bool:
    """True when the file's type is a Supported Format."""
    return path.suffix.lower() in _CONVERTER_BY_EXTENSION


def convert_to_markdown(source: Path) -> str:
    """Return the Markdown markitdown produces for one Source File."""
    extension = source.suffix.lower()
    converter = _CONVERTER_BY_EXTENSION[extension]()
    # No local_path: some converters (ZIP) print it, leaking the user's folder names.
    info = StreamInfo(extension=extension, filename=source.name)
    with source.open("rb") as stream:
        # Inline images as data URIs so the Asset Extractors can save them in place.
        return converter.convert(stream, info, keep_data_uris=True).markdown
