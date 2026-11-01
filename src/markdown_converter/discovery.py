"""Turns a Target into the Source Files to convert."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

LOG_FILE_NAME = "markdown-converter.log"
ASSETS_SUFFIX = "_assets"


@dataclass
class Discovery:
    source_files: list[Path] = field(default_factory=list)
    ignored: list[Path] = field(default_factory=list)


def discover(
    folder: Path,
    recurse: bool,
    is_supported: Callable[[Path], bool],
    exclude: Path | None = None,
) -> Discovery:
    """Find Source Files under a folder Target, in a stable order.

    Skips hidden folders, Assets Folders, Converted Documents, the log file and
    the `exclude` folder (an output folder inside the Target), and never follows
    symbolic links. Other unsupported files are `ignored`.
    """
    found = Discovery()
    excluded = exclude.resolve() if exclude else None
    for current, folders, files in os.walk(folder, followlinks=False):
        here = Path(current)
        folders[:] = [
            name for name in folders
            if recurse and not _is_hidden(here / name) and not _is_assets_folder(here, name)
            and not (here / name).is_symlink() and (here / name).resolve() != excluded
        ]
        for name in files:
            path = here / name
            if _is_hidden(path) or path.is_symlink() or _is_converter_output(path):
                continue
            (found.source_files if is_supported(path) else found.ignored).append(path)
    found.source_files.sort(key=lambda p: p.relative_to(folder).as_posix())
    return found


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    attributes = getattr(path.lstat(), "st_file_attributes", 0)  # Windows only
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0))


def _is_assets_folder(parent: Path, name: str) -> bool:
    """An Assets Folder sits beside the Converted Document it belongs to."""
    if not name.endswith(ASSETS_SUFFIX):
        return False
    return (parent / f"{name[: -len(ASSETS_SUFFIX)]}.md").exists()


def _is_converter_output(path: Path) -> bool:
    return path.suffix.lower() == ".md" or path.name == LOG_FILE_NAME
