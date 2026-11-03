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

# Diagrams: drawn shapes outside bordered tables, and smaller than this share of the page, are
# grouped when within this many points of each other...
_MAX_SHAPE_SHARE = 0.5
_SHAPE_GAP = 24
# A rule no thicker than this just under a line of text is its underline, not part of a drawing.
_UNDERLINE_THICKNESS = 2
# ...and a group is a diagram with at least this many shapes, a curve or a filled shape,
# at least one shape for every this many words of text inside it (shaded table rows and
# coloured text boxes are mostly text), and at least this size in points (curves are
# measured by their end points, so this is generous).
_DIAGRAM_MIN_SHAPES = 10
_DIAGRAM_MAX_WORDS_PER_SHAPE = 2
_DIAGRAM_MIN_WIDTH, _DIAGRAM_MIN_HEIGHT = 72, 36
# A Figure Snapshot of a diagram takes in this many points around its shapes, so thick
# strokes at its edges aren't clipped; lines of text within it are the diagram's labels.
_DIAGRAM_MARGIN = 6
# ...and this many more around its labels and caption.
_TEXT_MARGIN = 3


def blocks(document, figures) -> list[Block]:
    """The blocks of an untagged PDF, page by page, top to bottom.

    Diagrams become Figure Snapshots through `figures` (`snapshot(page, bbox)` renders
    an area and returns its link; `reached(page, image name)` records an image the
    snapshot already shows), and the text inside them is left out.
    """
    pages = []
    for page in document.pages:
        # A tighter tolerance than pdfplumber's keeps closely set words apart, as in tightly set headings.
        lines = [line for line in page.extract_text_lines(strip=True, return_chars=True, x_tolerance=1.5)
                 if line["text"]]
        tables = [table for table in page.find_tables() if _table_rows(table)]
        diagrams = _diagrams(page, tables, lines)
        labels = {id(line) for _, taken in diagrams for line in taken}  # shown in the pictures instead
        lines = [line for line in lines if id(line) not in labels]
        diagrams = [area for area, _ in diagrams]
        pages.append((page, lines, tables, diagrams))
    furniture = _furniture(pages)
    body_size, margin = _body_style(pages)
    placed = []  # (page number, markdown, heading text size or None)
    for page, lines, tables, diagrams in pages:
        content = [line for line in lines if id(line) not in furniture and not _in_table(line, tables)]
        on_page = [(table.bbox[1], _table_markdown(_table_rows(table)), None) for table in tables]
        on_page += [(area[1], f"![]({link})", None) for area in diagrams
                    if (link := _diagram_snapshot(page, area, figures))]
        on_page += _text_blocks(content, body_size, margin)
        placed += [(page.page_number, markdown, size) for _, markdown, size in sorted(on_page, key=lambda b: b[0])]
    # Heading levels follow text size: the largest heading text used is `#`, the next `##`, and so on.
    sizes = sorted({size for _, _, size in placed if size is not None}, reverse=True)
    return [Block(number, markdown if size is None else "#" * min(sizes.index(size) + 1, 6) + " " + markdown)
            for number, markdown, size in placed]


def _furniture(pages) -> set[int]:
    """The ids of every line that is Page Furniture."""
    candidates = collections.defaultdict(list)  # digit-free text -> (page number, top, line)
    for page, lines, tables, _ in pages:
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
    for _, lines, _, _ in pages:
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


def _diagrams(page, tables, lines: list[dict]) -> list[tuple[tuple[float, float, float, float], list[dict]]]:
    """The page's diagrams, dense groups of drawn shapes outside its tables: each one's area
    (x0, top, x1, bottom), and the lines of text inside its shapes, which are its labels.

    The area also takes in labels sticking out and captions, but those lines stay in the
    text as well, so widening the picture never loses text.
    """
    page_area = page.width * page.height
    shapes = [shape for kind in ("rect", "line", "curve") for shape in page.objects.get(kind, [])
              if (shape["x1"] - shape["x0"]) * (shape["bottom"] - shape["top"]) < page_area * _MAX_SHAPE_SHARE
              and _visible(shape) and not _underlines(shape, lines)
              and not any(_box_inside(shape, table.bbox) for table in tables)]
    areas = []
    for group in _groups(shapes):
        x0, top, x1, bottom = (min(s["x0"] for s in group), min(s["top"] for s in group),
                               max(s["x1"] for s in group), max(s["bottom"] for s in group))
        labels = [line for line in lines if _middle_inside(line, (x0, top, x1, bottom))]
        shapes_area = (x0 - _DIAGRAM_MARGIN, top - _DIAGRAM_MARGIN, x1 + _DIAGRAM_MARGIN, bottom + _DIAGRAM_MARGIN)
        x0, top, x1, bottom = _with_labels(shapes_area, lines)
        words = sum(len(line["text"].split()) for line in labels)
        if (len(group) >= _DIAGRAM_MIN_SHAPES and x1 - x0 >= _DIAGRAM_MIN_WIDTH
                and bottom - top >= _DIAGRAM_MIN_HEIGHT
                and words <= len(group) * _DIAGRAM_MAX_WORDS_PER_SHAPE
                and any(s["object_type"] == "curve" or s.get("fill") for s in group)):
            # Lines of text are measured to their letters' usual height; tall and italic letters reach past it.
            area = (x0 - _TEXT_MARGIN, top - _TEXT_MARGIN, x1 + _TEXT_MARGIN, bottom + _TEXT_MARGIN)
            areas.append((area, labels))
    return areas


def _with_labels(box: tuple[float, float, float, float], lines: list[dict]) -> tuple[float, float, float, float]:
    """A diagram's area widened to take in its labels and captions.

    Lines overlapping the area are labels, often sticking out past the shapes they
    name. A line within the area's width less than a paragraph gap above or below
    a line already taken in continues it, as a caption's lines do. Nothing else is
    taken in, so the area can't spread into the paragraphs around it.
    """
    taken = [line for line in lines if _overlaps(line, box)]
    box = _around(box, taken)
    grew = True
    while grew:
        grew = False
        for line in lines:
            if (not any(line is other for other in taken) and box[0] - 2 <= line["x0"] and line["x1"] <= box[2] + 2
                    and any(_continues(line, other) for other in taken)):
                taken.append(line)
                box = _around(box, [line])
                grew = True
    return box


def _underlines(shape: dict, lines: list[dict]) -> bool:
    """Whether a shape is a thin rule just under a line of text, within its width: an underline, not drawing."""
    if shape["bottom"] - shape["top"] > _UNDERLINE_THICKNESS:
        return False
    return any(line["x0"] - 2 <= shape["x0"] and shape["x1"] <= line["x1"] + 2
               and line["bottom"] - 4 <= shape["top"] <= line["bottom"] + 3 for line in lines)


def _visible(shape: dict) -> bool:
    """Whether a shape shows on the page: outlined, or filled with something other than white.

    Office exports often paint white, unoutlined boxes behind a page's content; they draw nothing.
    """
    if shape.get("stroke"):
        return True
    if not shape.get("fill"):
        return False
    colour = shape.get("non_stroking_color")
    components = list(colour) if isinstance(colour, (list, tuple)) else [colour]
    if not components or any(not isinstance(c, (int, float)) for c in components):
        return True  # a pattern or named colour: assume it shows
    white = [0, 0, 0, 0] if len(components) == 4 else [1] * len(components)  # CMYK white is no ink
    return components != white


def _middle_inside(line: dict, box: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = box
    return x0 <= (line["x0"] + line["x1"]) / 2 <= x1 and top <= (line["top"] + line["bottom"]) / 2 <= bottom


def _continues(line: dict, other: dict) -> bool:
    """Whether two lines sit one under the other, less than a paragraph gap apart."""
    upper, lower = (line, other) if line["top"] < other["top"] else (other, line)
    side_by_side = line["x0"] < other["x1"] and other["x0"] < line["x1"]
    return side_by_side and 0 <= lower["top"] - upper["bottom"] <= _gap_limit(upper)


def _gap_limit(line: dict) -> float:
    return (line["bottom"] - line["top"]) * _PARAGRAPH_GAP


def _around(box: tuple[float, float, float, float], lines: list[dict]) -> tuple[float, float, float, float]:
    x0, top, x1, bottom = box
    return (min([x0, *(line["x0"] for line in lines)]), min([top, *(line["top"] for line in lines)]),
            max([x1, *(line["x1"] for line in lines)]), max([bottom, *(line["bottom"] for line in lines)]))


def _groups(shapes: list[dict]) -> list[list[dict]]:
    """Shapes grouped with every shape within `_SHAPE_GAP` points of another in the group."""
    shapes = sorted(shapes, key=lambda s: s["x0"])
    parent = list(range(len(shapes)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(shapes):
        for j in range(i + 1, len(shapes)):
            b = shapes[j]
            if b["x0"] > a["x1"] + _SHAPE_GAP:
                break  # sorted by left edge, so no later shape is near `a` either
            if b["top"] <= a["bottom"] + _SHAPE_GAP and a["top"] <= b["bottom"] + _SHAPE_GAP:
                parent[root(j)] = root(i)
    groups = collections.defaultdict(list)
    for i, shape in enumerate(shapes):
        groups[root(i)].append(shape)
    return list(groups.values())


def _diagram_snapshot(page, area: tuple[float, float, float, float], figures) -> str | None:
    """Render a diagram's area as a Figure Snapshot; images inside it are not linked again."""
    for image in page.images:
        if _box_inside(image, area):
            figures.reached(page.page_number, image["name"])
    x0, top, x1, bottom = area
    return figures.snapshot(page.page_number, (x0, page.height - bottom, x1, page.height - top))


def _box_inside(item: dict, box: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = box
    return x0 - 2 <= item["x0"] and item["x1"] <= x1 + 2 and top - 2 <= item["top"] and item["bottom"] <= bottom + 2


def _overlaps(item: dict, box: tuple[float, float, float, float]) -> bool:
    x0, top, x1, bottom = box
    return item["x0"] < x1 and item["x1"] > x0 and item["top"] < bottom and item["bottom"] > top



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
