"""The Document Converter: turns one Source File into its Converted Document."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from markdown_converter import __version__, offline
from markdown_converter.assets import AssetStore
from markdown_converter.discovery import ASSETS_SUFFIX
from markdown_converter.extractors import extract_assets
from markdown_converter.formats import convert_to_markdown
from markdown_converter.options import ConversionOptions

ENCRYPTED = "encrypted"

_OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
_OFFICE_PACKAGES = {".docx", ".pptx", ".xlsx"}

# A colon is only special in YAML when followed by a space or at the end.
_PLAIN_YAML = re.compile(r"[A-Za-z0-9_](?:[\w .+-]|:(?=[^ ]))*")


class SkippedError(Exception):
    """The Source File can't be converted as it stands (e.g. it is encrypted)."""


def convert_document(source: Path, converted: Path, options: ConversionOptions) -> list[str]:
    """Write the Converted Document and Assets Folder for `source`; return warnings.

    Raises SkippedError for encrypted files, ConnectionError when the Offline
    Guard blocked a network attempt (even one the library swallowed), and any
    library error for damaged files. Nothing is written unless it succeeds.
    """
    if _is_encrypted(source):
        raise SkippedError(ENCRYPTED)
    store = AssetStore(converted.with_name(f"{converted.stem}{ASSETS_SUFFIX}"), options.min_image_size)
    blocked_before = offline.blocked_attempts()
    try:
        try:
            text = extract_assets(source, convert_to_markdown(source), store, options)
        finally:
            if offline.blocked_attempts() != blocked_before:
                raise ConnectionError(offline.BLOCKED_MESSAGE)
    except BaseException:
        store.discard()
        raise
    if options.front_matter:
        text = _front_matter(source) + text
    store.commit()
    converted.write_text(text, encoding="utf-8")
    return store.warnings


def _is_encrypted(source: Path) -> bool:
    extension = source.suffix.lower()
    if extension in _OFFICE_PACKAGES:
        # Password-protected Office files are OLE containers instead of ZIP packages.
        with source.open("rb") as stream:
            return stream.read(len(_OLE_SIGNATURE)) == _OLE_SIGNATURE
    if extension == ".pdf":
        from pypdf import PasswordType, PdfReader

        try:
            reader = PdfReader(source)
            # Files with only an owner password open without one, so they convert.
            return reader.is_encrypted and reader.decrypt("") == PasswordType.NOT_DECRYPTED
        except Exception:
            return False  # damaged: let the converter report it
    return False


def _front_matter(source: Path) -> str:
    fields = {
        "source": source.name,
        "format": source.suffix.lstrip(".").lower(),
        "converted": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "converter_version": __version__,
    }
    body = "".join(f"{key}: {_yaml_scalar(value)}\n" for key, value in fields.items())
    return f"---\n{body}---\n\n"


def _yaml_scalar(value: str) -> str:
    """Plain scalar when safe, otherwise a double-quoted (JSON-compatible) one."""
    return value if _PLAIN_YAML.fullmatch(value) else json.dumps(value, ensure_ascii=False)
