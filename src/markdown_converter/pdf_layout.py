"""Untagged PDF structure: Page Furniture, headings and bordered tables recovered from layout (ADR 0008).

Used for PDFs whose tags are missing or reach too little of their text.
"""

from __future__ import annotations

import collections
import re

from markdown_converter.pdf_tags import Block, escape

# Page Furniture: a line in this top or bottom share of the page...
_FURNITURE_BAND = 0.12
# ...whose text, ignoring digits, recurs within this many points of the same height on this many pages.
_SAME_HEIGHT = 3
_FURNITURE_MIN_PAGES = 3

# A gap between lines wider than this many line heights starts a new paragraph.
_PARAGRAPH_GAP = 0.6
# Lines that begin a numbered clause or list item: 1. / 1.2 / 1.2.4.a / (a) / a) / (iv) / bullets.
_CLAUSE_LABEL = re.compile(
    r"^(?:\d+(?:\.\d+)*\.(?:[a-z]\.?)?|\d+(?:\.\d+)+(?:\.[a-z])?\.?|\(?[a-z]{1,4}\)|\(\d+\)|[•▪◦–*-])\s"
)
# A heading is a short line starting this close to the left margin.
_HEADING_MAX_WORDS = 15
_MARGIN_TOLERANCE = 6
# Text this much larger than body text counts as larger.
_LARGER = 0.5


def blocks(document) -> list[Block]:
    """The blocks of an untagged PDF, page by page, top to bottom."""
    pages = []
    for page in document.pages:
        # A tighter tolerance than pdfplumber's keeps closely set words apart, as in tightly set headings.
        lines = [line for line in page.extract_text_lines(strip=True, return_chars=True, x_tolerance=1.5)
                 if line["text"]]
        tables = [table for table in page.find_tables() if _table_rows(table)]
        pages.append((page, lines, tables))
    furniture = _furniture(pages)
    body_size, margin = _body_style(pages)
    placed = []  # (page number, markdown, heading text size or None)
    for page, lines, tables in pages:
        content = [line for line in lines if id(line) not in furniture and not _in_table(line, tables)]
        on_page = [(table.bbox[1], _table_markdown(_table_rows(table)), None) for table in tables]
        on_page += _text_blocks(content, body_size, margin)
        placed += [(page.page_number, markdown, size) for _, markdown, size in sorted(on_page, key=lambda b: b[0])]
    # Heading levels follow text size: the largest heading text used is `#`, the next `##`, and so on.
    sizes = sorted({size for _, _, size in placed if size is not None}, reverse=True)
    return [Block(number, markdown if size is None else "#" * min(sizes.index(size) + 1, 6) + " " + markdown)
            for number, markdown, size in placed]


def _furniture(pages) -> set[int]:
    """The ids of every line that is Page Furniture."""
    candidates = collections.defaultdict(list)  # digit-free text -> (page number, top, line)
    for page, lines, tables in pages:
        band = page.height * _FURNITURE_BAND
        for line in lines:
            if (line["top"] < band or line["bottom"] > page.height - band) and not _in_table(line, tables):
                candidates[re.sub(r"\d+", "#", line["text"])].append((page.page_number, line["top"], line))
    furniture = set()
    for placements in candidates.values():
        for _, top, line in placements:
            pages_at_height = {number for number, other, _ in placements if abs(other - top) <= _SAME_HEIGHT}
            if len(pages_at_height) >= _FURNITURE_MIN_PAGES:
                furniture.add(id(line))
    return furniture


def _body_style(pages) -> tuple[float, float]:
    """The most common text size and left edge: body text's."""
    sizes, edges = collections.Counter(), collections.Counter()
    for _, lines, _ in pages:
        for line in lines:
            sizes[round(line["chars"][0]["size"], 1)] += len(line["chars"])
            edges[round(line["x0"])] += 1
    return (sizes.most_common(1)[0][0] if sizes else 0.0), (edges.most_common(1)[0][0] if edges else 0.0)


def _text_blocks(lines: list[dict], body_size: float, margin: float) -> list[tuple[float, str, float | None]]:
    """Paragraphs and headings: the top of the first line, the text, and the text size if a heading."""
    placed: list[tuple[float, list[str], float | None]] = []
    previous = None
    for line in lines:
        size = _heading_size(line, previous, body_size, margin)
        if previous is not None and size is not None and placed[-1][2] == size and _gap(previous, line) < 1:
            placed[-1][1].append(line["text"])  # a heading wrapped onto a second line
        elif size is not None:
            placed.append((line["top"], [line["text"]], size))
        elif (previous is None or placed[-1][2] is not None or _gap(previous, line) > _PARAGRAPH_GAP
              or _CLAUSE_LABEL.match(line["text"])):
            placed.append((line["top"], [escape(line["text"])], None))
        else:
            placed[-1][1].append(escape(line["text"]))
        previous = line
    return [(top, " ".join(text) if size is not None else "\n".join(text), size) for top, text, size in placed]


def _heading_size(line: dict, previous: dict | None, body_size: float, margin: float) -> float | None:
    """The size that sets the line's heading level, if it is a heading: short, at the margin, after a gap,
    and bold or larger.

    Bold text within half a point of body size counts as body size, and larger
    text is rounded to the whole point, so headings set a fraction apart share a level.
    """
    chars = [char for char in line["chars"] if char["text"].strip()]
    if not chars or len(line["text"].split()) >= _HEADING_MAX_WORDS or abs(line["x0"] - margin) > _MARGIN_TOLERANCE:
        return None
    if previous is not None and _gap(previous, line) <= _PARAGRAPH_GAP:
        if not _is_heading_style(previous, body_size):
            return None
    size = chars[0]["size"]
    if size > body_size + _LARGER:
        return float(round(size))
    if abs(size - body_size) <= _LARGER and _is_bold(chars):
        return body_size
    return None


def _is_heading_style(line: dict, body_size: float) -> bool:
    chars = [char for char in line["chars"] if char["text"].strip()]
    return bool(chars) and (chars[0]["size"] > body_size + _LARGER or _is_bold(chars))


def _is_bold(chars: list[dict]) -> bool:
    return all("bold" in char["fontname"].lower() for char in chars)


def _gap(previous: dict, line: dict) -> float:
    """The space between two lines, in line heights."""
    return (line["top"] - previous["bottom"]) / max(previous["bottom"] - previous["top"], 1)


def _in_table(line: dict, tables) -> bool:
    middle = (line["top"] + line["bottom"]) / 2
    return any(t.bbox[1] <= middle <= t.bbox[3] and line["x0"] < t.bbox[2] and line["x1"] > t.bbox[0]
               for t in tables)


def _table_rows(table) -> list[list[str]]:
    """The table's rows, with the stray columns that extra border lines create taken out.

    A column empty in every row is dropped. Two neighbouring columns that are
    never both filled in the same row hold one column's cells split across
    them, so they are merged.
    """
    rows = [[re.sub(r"\s+", " ", cell or "").strip() for cell in row] for row in table.extract()]
    width = max((len(row) for row in rows), default=0)
    columns = [[row[i] if i < len(row) else "" for row in rows] for i in range(width)]
    merged: list[list[str]] = []
    for column in (column for column in columns if any(column)):
        if merged and not any(a and b for a, b in zip(merged[-1], column)):
            merged[-1] = [a or b for a, b in zip(merged[-1], column)]
        else:
            merged.append(column)
    return [list(row) for row in zip(*merged)] if len(merged) >= 2 else []


def _table_markdown(rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows]
    return "\n".join([lines[0], "|" + "---|" * len(rows[0]), *lines[1:]])
