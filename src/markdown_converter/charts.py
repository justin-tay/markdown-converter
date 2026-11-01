"""Charts as data and definition (ADR 0002).

The Office converters leave a chart marker where each Chart sits, naming its
part in the package. `replace_chart_markers` swaps each marker for a heading,
a Chart Data Table and a link to the Chart Definition saved in the Asset Store.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

from markdown_converter.assets import AssetStore

_C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# U+27E6/U+27E7 brackets survive Markdown escaping, unlike [ ] or _.
_MARKER = re.compile(r"⟦chart:([^⟧]+)⟧")

_KIND_NAMES = {
    "bar": "bar", "bar3D": "3-D bar", "line": "line", "line3D": "3-D line", "pie": "pie",
    "pie3D": "3-D pie", "ofPie": "pie-of-pie", "doughnut": "doughnut", "area": "area",
    "area3D": "3-D area", "scatter": "scatter", "radar": "radar", "bubble": "bubble",
    "stock": "stock", "surface": "surface", "surface3D": "3-D surface",
}


def marker(partname: str) -> str:
    """The placeholder an Office converter leaves where a Chart sits."""
    return f"⟦chart:{partname}⟧"


@dataclass
class Chart:
    title: str
    kind: str
    rows: list[list[str]] | None  # header first; None when the data couldn't be read


CellResolver = Callable[[str], list[str]]


def read_chart(xml: bytes, resolve: CellResolver | None = None) -> Chart:
    """Read a Chart's title, type and values from its chart XML.

    Values come from the chart's cached points. Some tools write no cache, only
    cell references such as 'Sales'!$B$2:$B$3; `resolve` turns those into values.
    """
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        return Chart("Untitled", "unknown", None)
    title = "".join(t.text or "" for t in root.iterfind(f"{_C}chart/{_C}title//{_A}t")).strip() or "Untitled"
    plots = [p for p in root.iterfind(f"{_C}chart/{_C}plotArea/*") if p.tag.endswith("Chart")]
    if not plots:
        return Chart(title, "unknown", None)
    kind = " and ".join(dict.fromkeys(_kind(plot) for plot in plots))
    try:
        rows = _table(plots, resolve)
    except ValueError:
        rows = None
    return Chart(title, kind, rows)


def chart_block(chart: Chart, link: str | None) -> str:
    lines = [f"**Chart: {chart.title} ({chart.kind} chart)**", ""]
    if chart.rows:
        header, *body = chart.rows
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        lines.extend("| " + " | ".join(row) + " |" for row in body)
    else:
        lines.append("(data not extracted)")
    if link:
        lines += ["", f"[Chart definition]({link})"]
    return "\n".join(lines)


def replace_chart_markers(markdown: str, package: Path, store: AssetStore, location: str = "") -> str:
    """Swap each chart marker for its chart block, saving its Chart Definition as an Asset."""
    if not _MARKER.search(markdown):
        return markdown
    with zipfile.ZipFile(package) as archive:

        def render(match: re.Match) -> str:
            # Markdown escaping may have added backslashes (chart\_1.xml); part names have none.
            part = match.group(1).replace("\\", "").lstrip("/")
            try:
                xml = archive.read(part)
            except KeyError:
                return f"\n\n{chart_block(Chart('Untitled', 'unknown', None), None)}\n\n"
            link = store.add(xml, ".xml", location, kind="chart")
            return f"\n\n{chart_block(read_chart(xml), link)}\n\n"

        replaced = _MARKER.sub(render, markdown)
    return re.sub(r"\n{3,}", "\n\n", replaced)


def _kind(plot: ElementTree.Element) -> str:
    name = plot.tag.removeprefix(_C).removesuffix("Chart")
    bar_direction = plot.find(f"{_C}barDir")
    if name in ("bar", "bar3D") and bar_direction is not None and bar_direction.get("val") == "col":
        return "column" if name == "bar" else "3-D column"
    return _KIND_NAMES.get(name, name)


def _table(plots: list[ElementTree.Element], resolve: CellResolver | None) -> list[list[str]]:
    series = [s for plot in plots for s in plot.iterfind(f"{_C}ser")]
    names, columns, categories = [], [], {}
    for number, ser in enumerate(series, start=1):
        values = _points(ser.find(f"{_C}val"), resolve) or _points(ser.find(f"{_C}yVal"), resolve)
        if not values:
            continue
        names.append(" ".join(_points(ser.find(f"{_C}tx"), resolve).values()) or f"Series {number}")
        columns.append(values)
        labels = _points(ser.find(f"{_C}cat"), resolve) or _points(ser.find(f"{_C}xVal"), resolve)
        for index, label in labels.items():
            categories.setdefault(index, label)
    if not columns:
        raise ValueError("no cached values")
    indices = sorted(set(categories) | {i for column in columns for i in column})
    header = ["Category", *names]
    body = [[categories.get(i, str(i + 1)), *(column.get(i, "") for column in columns)] for i in indices]
    return [header, *body]


def _points(element: ElementTree.Element | None, resolve: CellResolver | None) -> dict[int, str]:
    """Values by index from a cached point list, a literal, or the cells it refers to."""
    if element is None:
        return {}
    cached = {
        int(pt.get("idx", n)): (pt.findtext(f"{_C}v") or "").strip()
        for n, pt in enumerate(element.iter(f"{_C}pt"))
    }
    if cached:
        return cached
    literal = element.find(f"{_C}v")  # e.g. a series name typed straight into the chart
    if literal is not None and literal.text:
        return {0: literal.text.strip()}
    formula = element.findtext(f".//{_C}f")
    if formula and resolve:
        try:
            return dict(enumerate(resolve(formula)))
        except Exception:
            return {}
    return {}
