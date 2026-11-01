"""HTML and EPUB Asset Extractors: local and bundled images become Assets.

Images on the web are never fetched (ADR 0001): their links stay as they are
and the Run Summary says how many were left.
"""

from __future__ import annotations

import posixpath
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname

from markdown_converter.assets import AssetStore
from markdown_converter.options import ConversionOptions

# ![alt](target) or ![alt](target "title"); targets may contain spaces and one
# level of brackets, as in "photo (1).png".
_IMAGE = re.compile(r'!\[([^\]]*)\]\(((?:[^()]|\([^()]*\))+?)(\s+"[^"]*")?\)')
_REMOTE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]+:|//)")


def extract_html(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    def read(target: str) -> tuple[bytes, str] | None:
        path = (source.parent / target).resolve()
        return (path.read_bytes(), path.suffix) if path.is_file() else None

    return _relink(markdown, store, read)


def extract_epub(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    with zipfile.ZipFile(source) as book:
        members = [name for name in book.namelist() if not name.endswith("/")]

        def read(target: str) -> tuple[bytes, str] | None:
            # markitdown joins all chapters, so a relative link can't be resolved
            # against its chapter: match it against the end of each member path.
            cleaned = posixpath.normpath(target).lstrip("./")
            while cleaned.startswith("../"):
                cleaned = cleaned[3:]
            matches = [m for m in members if m == cleaned or m.endswith("/" + cleaned)]
            if len(matches) != 1:
                return None
            return book.read(matches[0]), posixpath.splitext(matches[0])[1]

        return _relink(markdown, store, read)


def _relink(markdown: str, store: AssetStore, read) -> str:
    remote = 0

    def relink(match: re.Match) -> str:
        nonlocal remote
        alt, target, title = match.group(1), match.group(2).strip("<>"), match.group(3) or ""
        if target.startswith("data:"):
            return match.group(0)  # handled with the other data-URI images
        if target.lower().startswith("file:"):
            path = url2pathname(urlsplit(target).path)  # a local file, not the web
        elif _REMOTE.match(target):
            remote += 1
            return match.group(0)
        else:
            path = unquote(urlsplit(target).path)
        found = read(path)
        if found is None:
            store.warnings.append(f"image not found: {target}")
            return match.group(0)
        data, extension = found
        link = store.add(data, extension or ".bin")
        return f"![{alt}]({link}{title})" if link else ""

    markdown = _IMAGE.sub(relink, markdown)
    if remote:
        store.warnings.append(f"{remote} remote image{'s' if remote > 1 else ''} not fetched")
    return markdown
