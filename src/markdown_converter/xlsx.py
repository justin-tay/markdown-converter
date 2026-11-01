"""Excel Asset Extractor: each sheet's images and Charts, linked within its section.

markitdown writes one "## <sheet name>" section per sheet but drops drawings.
This reads the package directly: workbook -> sheet -> drawing -> picture/chart.
"""

from __future__ import annotations

import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from markdown_converter.assets import AssetStore
from markdown_converter.charts import chart_block, read_chart
from markdown_converter.options import ConversionOptions

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PKG = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_XDR = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"

_UNSAFE_NAME = re.compile(r"[^\w-]+")
_REFERENCE = re.compile(r"^(?:'((?:[^']|'')+)'|([^!]+))!(.+)$")


def extract(source: Path, markdown: str, store: AssetStore, options: ConversionOptions) -> str:
    resolver = _CellResolver(source)
    try:
        with zipfile.ZipFile(source) as package:
            for name, sheet_part in _sheets(package):
                location = f"sheet-{_UNSAFE_NAME.sub('-', name).strip('-')}-"
                blocks = [
                    block for block in (
                        _drawing_block(package, kind, part, store, location, resolver)
                        for kind, part in _drawing_items(package, sheet_part)
                    ) if block
                ]
                if blocks:
                    markdown = _append_to_section(markdown, name, "\n\n".join(blocks))
    finally:
        resolver.close()
    return markdown


def _sheets(package: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ElementTree.fromstring(package.read("xl/workbook.xml"))
    targets = _relationships(package, "xl/workbook.xml")
    return [
        (sheet.get("name"), targets[sheet.get(f"{_REL}id")])
        for sheet in workbook.iterfind(f"{_MAIN}sheets/{_MAIN}sheet")
        if sheet.get(f"{_REL}id") in targets
    ]


def _drawing_items(package: zipfile.ZipFile, sheet_part: str) -> list[tuple[str, str]]:
    """("img" | "chart", part name) for each picture and chart, in drawing order."""
    items = []
    for drawing_part in _relationships(package, sheet_part, kind="/drawing").values():
        targets = _relationships(package, drawing_part)
        drawing = ElementTree.fromstring(package.read(drawing_part))
        for anchor in drawing:
            for blip in anchor.iter(f"{_A}blip"):
                if blip.get(f"{_REL}embed") in targets:
                    items.append(("img", targets[blip.get(f"{_REL}embed")]))
            for chart in anchor.iter(f"{_C}chart"):
                if chart.get(f"{_REL}id") in targets:
                    items.append(("chart", targets[chart.get(f"{_REL}id")]))
    return items


def _drawing_block(package, kind, part, store, location, resolve) -> str | None:
    data = package.read(part)
    if kind == "img":
        link = store.add(data, Path(part).suffix, location)
        return f"![]({link})" if link else None
    link = store.add(data, ".xml", location, kind="chart")
    return chart_block(read_chart(data, resolve), link)


def _relationships(package: zipfile.ZipFile, part: str, kind: str = "") -> dict[str, str]:
    """Relationship id -> target part name for `part`, optionally only of one type."""
    folder, name = posixpath.split(part)
    rels_part = posixpath.join(folder, "_rels", f"{name}.rels")
    if rels_part not in package.namelist():
        return {}
    targets = {}
    for rel in ElementTree.fromstring(package.read(rels_part)).iter(f"{_PKG}Relationship"):
        if rel.get("TargetMode") == "External" or not rel.get("Type", "").endswith(kind):
            continue
        target = rel.get("Target", "")
        resolved = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(folder, target))
        targets[rel.get("Id")] = resolved
    return targets


def _append_to_section(markdown: str, sheet: str, block: str) -> str:
    heading = f"## {sheet}\n"
    start = markdown.find(heading)
    if start == -1:
        return f"{markdown.rstrip()}\n\n{block}\n"
    following = markdown.find("\n## ", start + len(heading))
    end = len(markdown) if following == -1 else following
    return f"{markdown[:end].rstrip()}\n\n{block}\n{markdown[end:]}"


class _CellResolver:
    """Reads the values of a reference like 'Sales'!$B$2:$B$3, opening the workbook on first use."""

    def __init__(self, source: Path):
        self._source = source
        self._workbook = None

    def __call__(self, formula: str) -> list[str]:
        match = _REFERENCE.match(formula.strip())
        if not match:
            return []
        if self._workbook is None:
            from openpyxl import load_workbook

            self._workbook = load_workbook(self._source, read_only=True, data_only=True)
        sheet = (match.group(1) or "").replace("''", "'") or match.group(2)
        cells = self._workbook[sheet][match.group(3).replace("$", "")]
        rows = cells if isinstance(cells, tuple) else ((cells,),)
        flat = [cell for row in rows for cell in (row if isinstance(row, tuple) else (row,))]
        return [_text(cell.value) for cell in flat]

    def close(self) -> None:
        if self._workbook is not None:
            self._workbook.close()


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
