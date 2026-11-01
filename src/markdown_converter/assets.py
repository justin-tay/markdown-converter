"""The Asset Store: saves one Converted Document's Assets and hands back their links."""

from __future__ import annotations

import hashlib
import io
import mimetypes
import shutil
from pathlib import Path
from urllib.parse import quote

VECTOR_EXTENSIONS = {".emf", ".wmf", ".svg"}
HARD_TO_VIEW_EXTENSIONS = {".emf", ".wmf"}

_EXTENSION_BY_MIMETYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/tiff": ".tif",
    "image/svg+xml": ".svg",
    "image/x-emf": ".emf",
    "image/emf": ".emf",
    "image/x-wmf": ".wmf",
    "image/wmf": ".wmf",
}


def extension_for(mimetype: str) -> str:
    mimetype = mimetype.lower()
    return _EXTENSION_BY_MIMETYPE.get(mimetype) or mimetypes.guess_extension(mimetype) or ".bin"


class AssetStore:
    """Collects Assets in a staging folder; `commit` swaps it in for the Assets Folder.

    Identical content is stored once. Asset Names say where the Asset came from:
    a location prefix (e.g. "p003-", "slide02-") plus a per-kind counter.
    """

    def __init__(self, folder: Path, min_image_size: int | None = None):
        self.folder = folder
        self._staging = folder.with_name(f".{folder.name}.partial")
        self._min_image_size = min_image_size
        self._link_prefix = quote(folder.name) + "/"
        self._by_hash: dict[str, str] = {}
        self._counters: dict[tuple[str, str], int] = {}
        self.warnings: list[str] = []
        # A run that was interrupted may have left a staging folder behind.
        shutil.rmtree(self._staging, ignore_errors=True)

    def add(self, data: bytes, extension: str, location: str = "", kind: str = "img") -> str | None:
        """Save one Asset and return its relative link, or None if it was dropped."""
        extension = extension.lower()
        if kind == "img" and self._too_small(data, extension):
            return None
        digest = hashlib.sha256(data).hexdigest()
        if digest in self._by_hash:
            return self._by_hash[digest]
        key = (location, kind)
        self._counters[key] = self._counters.get(key, 0) + 1
        name = f"{location}{kind}{self._counters[key]:02d}{extension}"
        self._staging.mkdir(parents=True, exist_ok=True)
        (self._staging / name).write_bytes(data)
        if extension in HARD_TO_VIEW_EXTENSIONS:
            self.warnings.append(f"{name} is EMF/WMF, which some Markdown viewers can't display")
        link = self._link_prefix + quote(name)
        self._by_hash[digest] = link
        return link

    def contains(self, data: bytes) -> bool:
        """True when identical content has already been saved."""
        return hashlib.sha256(data).hexdigest() in self._by_hash

    def commit(self) -> None:
        """Replace the Assets Folder with what was saved; remove it if nothing was."""
        if self.folder.exists():
            shutil.rmtree(self.folder)
        if self._staging.exists():
            self._staging.rename(self.folder)

    def discard(self) -> None:
        shutil.rmtree(self._staging, ignore_errors=True)

    def _too_small(self, data: bytes, extension: str) -> bool:
        if not self._min_image_size or extension in VECTOR_EXTENSIONS:
            return False
        from PIL import Image

        try:
            width, height = Image.open(io.BytesIO(data)).size
        except Exception:
            return False  # unknown size: keep it rather than lose content
        return width < self._min_image_size or height < self._min_image_size
