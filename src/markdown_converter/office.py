"""markitdown's Word and PowerPoint converters, adjusted for Charts and Word numbering.

markitdown drops Word charts and writes PowerPoint charts as its own table, so
both converters here leave a chart marker instead (see `charts`). The Word
converter also writes each numbered paragraph's label into its text (see
`word_numbering`), which markitdown would otherwise lose.
"""

from __future__ import annotations

import io
import posixpath
import re
import zipfile
from typing import Any, BinaryIO

from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters import DocxConverter, PptxConverter

from markdown_converter.charts import marker
from markdown_converter.word_numbering import label_numbered_paragraphs

_CHART_REF = re.compile(r'<c:chart\b[^>]*\br:id="([^"]+)"')
# A chart may sit in an mc:AlternateContent wrapper or directly in a w:drawing.
_CHART_HOLDERS = (
    re.compile(r"<mc:AlternateContent\b(?:(?!</mc:AlternateContent>).)*?<c:chart\b.*?</mc:AlternateContent>", re.S),
    re.compile(r"<w:drawing\b(?:(?!</w:drawing>).)*?<c:chart\b.*?</w:drawing>", re.S),
)
_RELATIONSHIP = re.compile(r"<Relationship\b[^>]*>")


class WordConverter(DocxConverter):
    def convert(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> DocumentConverterResult:
        return super().convert(_prepare_word_package(file_stream.read()), stream_info, **kwargs)


class PowerPointConverter(PptxConverter):
    def _convert_chart_to_markdown(self, chart) -> str:
        return f"\n\n{marker(str(chart.part.partname))}\n\n"


def _prepare_word_package(package: bytes) -> io.BytesIO:
    """Write numbering labels into the text and swap chart drawings for chart markers."""
    with zipfile.ZipFile(io.BytesIO(package)) as source:
        names = set(source.namelist())
        original = source.read("word/document.xml")
        numbering = source.read("word/numbering.xml") if "word/numbering.xml" in names else None
        styles = source.read("word/styles.xml") if "word/styles.xml" in names else None
        document = label_numbered_paragraphs(original, numbering, styles).decode("utf-8")
        if "<c:chart" in document:
            document = _mark_charts(document, source.read("word/_rels/document.xml.rels").decode("utf-8"))
        if document.encode("utf-8") == original:
            return io.BytesIO(package)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as marked:
            for item in source.infolist():
                data = document.encode("utf-8") if item.filename == "word/document.xml" else source.read(item)
                marked.writestr(item, data)
    output.seek(0)
    return output


def _mark_charts(document: str, rels: str) -> str:
    """Replace each chart drawing in the document with a run of marker text."""
    targets = _relationship_targets(rels)

    def to_marker(match: re.Match) -> str:
        reference = _CHART_REF.search(match.group(0))
        target = targets.get(reference.group(1)) if reference else None
        if target is None:
            return match.group(0)
        return f"<w:t>{marker(posixpath.normpath(posixpath.join('/word', target)))}</w:t>"

    for holder in _CHART_HOLDERS:
        document = holder.sub(to_marker, document)
    return document


def _relationship_targets(rels: str) -> dict[str, str]:
    targets = {}
    for element in _RELATIONSHIP.findall(rels):
        rel_id = re.search(r'\bId="([^"]+)"', element)
        target = re.search(r'\bTarget="([^"]+)"', element)
        if rel_id and target:
            targets[rel_id.group(1)] = target.group(1)
    return targets
