"""Tagged PDF structure: a PDF's headings, paragraphs, lists and tables read from its tags (ADR 0008).

pdfplumber's own structure-tree reader files every marked-content run under the
page of the element that owns it, so a paragraph that runs onto the next page
loses its second half. The tree is read here with pypdf instead, keeping the
page of each run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Below this share of a PDF's text reached by its tags, the layout rules read it instead.
MIN_TAG_COVERAGE = 0.8

_LIST_LIKE_START = re.compile(r"^(\d{1,9})([.)])(?=\s|$)")
_HEADING = re.compile(r"^H([1-6]?)$")
# The dot leaders and page number ending a contents entry ("Leave ........ 3").
_CONTENTS_TAIL = re.compile(r"\s*(?:\.\s?){2,}\s*\S*$|\s+\d+$")
# Contents entries indented within this many points of each other are at the same level.
_INDENT_STEP = 4
# A block can claim the contents list's next unclaimed title or the one after it, so one
# entry whose title never appears in the text doesn't stop the rest being matched.
_TITLE_LOOKAHEAD = 2
# Elements that hold blocks of their own; anything else is read as one paragraph.
_BLOCK_TYPES = {"P", "L", "Table", "TOC", "Figure", "Formula", "BlockQuote", "Caption", "Note", "Code",
                "Document", "Part", "Art", "Sect", "Div", "NonStruct", "Private", "Index", "TOCI", "Form"}
# A figure that draws only a frame (this many rectangles or lines at most) around
# more tagged text than this is a text box, not a picture.
_FRAME_SHAPES = 4
_TEXT_BOX_CHARS = 20
# List labels that mark a bullet rather than a number or letter (including symbol-font bullets).
_BULLETS = set("•●▪■◦○–—-*o§") | {chr(c) for c in (0xF0A7, 0xF0A8, 0xF0B7, 0xF0D8, 0xF0FC, 0xF076)}


@dataclass(frozen=True)
class Content:
    """One marked-content run: what the tags point at on a page."""

    page: int
    mcid: int


@dataclass(frozen=True)
class Annotation:
    """A link annotation; `uri` is None for a link to another place in the same PDF."""

    uri: str | None


@dataclass
class Element:
    type: str
    kids: list = field(default_factory=list)  # Element | Content | Annotation, in reading order
    alt: str | None = None
    actual_text: str | None = None
    bbox: tuple[float, float, float, float] | None = None  # PDF user space: x0, y0, x1, y1
    column_span: int = 1
    row_span: int = 1
    page: int | None = None


@dataclass(frozen=True)
class Block:
    """A Markdown block and the page it starts on."""

    page: int
    markdown: str


def read_structure(reader) -> Element | None:
    """The PDF's structure tree, or None when the PDF has no tags."""
    root = reader.trailer["/Root"].get("/StructTreeRoot")
    if root is None:
        return None
    root = root.get_object()
    role_map = {str(k): str(v) for k, v in (root.get("/RoleMap") or {}).items()}
    pages = {page.indirect_reference.idnum: number for number, page in enumerate(reader.pages, start=1)}
    seen: set[int] = set()

    def standard_type(name: str) -> str:
        for _ in range(10):  # role maps may chain, and may loop
            if name not in role_map:
                break
            name = role_map[name]
        return name.lstrip("/")

    def page_of(obj, inherited):
        reference = obj.get("/Pg")
        return pages.get(reference.idnum, inherited) if reference is not None else inherited

    def kids(value, page) -> list:
        if value is None:
            return []
        value = value.get_object() if hasattr(value, "get_object") else value
        items = value if isinstance(value, list) else [value]
        result = []
        for item in items:
            reference = getattr(item, "idnum", None)
            obj = item.get_object() if hasattr(item, "get_object") else item
            if isinstance(obj, int):
                if page is not None:
                    result.append(Content(page, int(obj)))
            elif not hasattr(obj, "get"):
                continue
            elif "/MCID" in obj:
                if page_of(obj, page) is not None and "/Stm" not in obj:
                    result.append(Content(page_of(obj, page), int(obj["/MCID"])))
            elif obj.get("/Type") == "/OBJR":
                result.append(_annotation(obj["/Obj"].get_object()))
            elif "/S" in obj:
                if reference is not None:
                    if reference in seen:
                        continue
                    seen.add(reference)
                result.append(element(obj, page))
        return result

    def element(obj, inherited) -> Element:
        page = page_of(obj, inherited)
        return Element(
            type=standard_type(str(obj["/S"])),
            kids=kids(obj.get("/K"), page),
            alt=_text(obj.get("/Alt")),
            actual_text=_text(obj.get("/ActualText")),
            bbox=_bbox(_attribute(obj.get("/A"), "/BBox")),
            column_span=int(_attribute(obj.get("/A"), "/ColSpan") or 1),
            row_span=int(_attribute(obj.get("/A"), "/RowSpan") or 1),
            page=page,
        )

    return Element("Document", kids(root.get("/K"), None))


def _text(value) -> str | None:
    return str(value.get_object()) if value is not None else None


def _attribute(attributes, key: str):
    """An attribute's value from an element's attribute dictionary, or array of them."""
    if attributes is None:
        return None
    attributes = attributes.get_object()
    for entry in attributes if isinstance(attributes, list) else [attributes]:
        entry = entry.get_object() if hasattr(entry, "get_object") else entry
        if hasattr(entry, "get") and entry.get(key) is not None:
            return entry[key].get_object()
    return None


def _bbox(value) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    x0, y0, x1, y1 = (float(v) for v in value)
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def _annotation(obj) -> Annotation:
    action = obj.get("/A")
    action = action.get_object() if action is not None else {}
    return Annotation(str(action["/URI"]) if action.get("/S") == "/URI" and "/URI" in action else None)


def contents(element: Element, skip=frozenset()):
    """Every marked-content run under `element` in reading order, leaving out elements of the `skip` types."""
    for kid in element.kids:
        if isinstance(kid, Content):
            yield kid
        elif isinstance(kid, Element) and kid.type not in skip:
            yield from contents(kid, skip)


def _holds_blocks(element: Element) -> bool:
    return any(isinstance(kid, Element) and (kid.type in _BLOCK_TYPES or _HEADING.match(kid.type)
                                             or _holds_blocks(kid)) for kid in element.kids)


def _descendants(element: Element, type_: str, skip=frozenset()):
    """The outermost elements of `type_` under `element`, leaving out elements of the `skip` types."""
    for kid in element.kids:
        if isinstance(kid, Element) and kid.type not in skip:
            if kid.type == type_:
                yield kid
            else:
                yield from _descendants(kid, type_, skip)


def tag_coverage(root: Element, objects: dict) -> float:
    """The share of the PDF's text, Page Furniture aside, that its tags reach."""
    reached = set(contents(root))
    total = covered = 0
    for (page, mcid), items in objects.items():
        for item in items:
            if item["object_type"] == "char" and item["text"].strip() and item.get("tag") != "Artifact":
                total += 1
                covered += Content(page, mcid) in reached if mcid is not None else 0
    return covered / total if total else 0.0


def furniture_images(objects: dict):
    """(page number, image) for each image the tags mark as outside the content, such as a header logo."""
    for (page, mcid), items in objects.items():
        if mcid is None:
            for item in items:
                if item["object_type"] == "image" and item.get("tag") == "Artifact":
                    yield page, item


def page_objects(document) -> dict:
    """Every object on every page, keyed by (page number, MCID); MCID is None for unmarked content."""
    objects: dict = {}
    for page in document.pages:
        for kind in ("char", "image", "rect", "line", "curve"):
            for item in page.objects.get(kind, []):
                objects.setdefault((page.page_number, item.get("mcid")), []).append(item)
    return objects


class _Renderer:
    def __init__(self, objects: dict, assets):
        self.objects = objects
        self.assets = assets
        self.blocks: list[Block] = []
        self.contents_titles: list[tuple[str, int]] = []  # see find_contents_titles
        self.next_title = 0  # the first contents title not yet claimed

    def add(self, element: Element, markdown: str) -> None:
        if markdown.strip():
            self.blocks.append(Block(self.first_page(element), markdown))

    def first_page(self, element: Element) -> int:
        return next((c.page for c in contents(element)), element.page or 1)

    def text(self, element: Element, skip=frozenset()) -> str:
        if element.actual_text:
            return _clean(element.actual_text)
        from pdfplumber.utils import extract_text

        runs: list[tuple[int, list]] = []
        for content in contents(element, skip):
            chars = [o for o in self.objects.get((content.page, content.mcid), []) if o["object_type"] == "char"]
            if runs and runs[-1][0] == content.page:
                runs[-1][1].extend(chars)
            else:
                runs.append((content.page, chars))
        return _clean(" ".join(extract_text(chars) for _, chars in runs))

    def render(self, element: Element) -> None:
        heading = _HEADING.match(element.type)
        if heading:
            text = self.linked_text(element)
            if text:
                self.claim_contents_title(self.text(element))
                self.add(element, "#" * int(heading.group(1) or 1) + " " + text)
        elif element.type == "L":
            self.add(element, _join_list(self.list_items(element, 0)))
        elif element.type == "Table":
            # A full-width row opening with the contents list's next title splits the table there.
            segment: list[Element] = []
            for row in _descendants(element, "TR"):
                title, rest = self.row_title(row)
                if title:
                    if segment:
                        self.add(segment[0], self.table(segment))
                    self.add(row, title)
                    segment = [rest] if rest else []
                else:
                    segment.append(row)
            if segment:
                self.add(segment[0], self.table(segment))
        elif element.type == "TOC":
            self.add(element, "\n".join(self.contents_entries(element, 0)))
        elif element.type == "Figure" and not _holds_blocks(element):
            self.figure(element)
        elif _holds_blocks(element):
            for kid in element.kids:
                if isinstance(kid, Element):
                    self.render(kid)
        else:
            self.add(element, self.contents_heading(self.text(element)) or escape(self.linked_text(element)))

    def contents_heading(self, text: str) -> str | None:
        """A heading for `text` if it is the contents list's next title, though not tagged as a heading (StR-017).

        Authors don't always give a section title a heading style; the contents
        list still names it.
        """
        level = self.claim_contents_title(text)
        return "#" * level + " " + text if level else None

    def claim_contents_title(self, text: str) -> int | None:
        """Match `text` to the contents list's next unclaimed title, or the one after; return its level.

        Titles are claimed in the contents list's order, by tagged headings and
        promoted blocks alike, so the same words earlier or later in the document
        don't take an entry that belongs elsewhere.
        """
        key = text.casefold()
        ahead = self.contents_titles[self.next_title:self.next_title + _TITLE_LOOKAHEAD]
        for offset, (title, level) in enumerate(ahead):
            if title == key:
                self.next_title += offset + 1
                return level
        return None

    def row_title(self, row: Element) -> tuple[str | None, Element | None]:
        """A heading for a table row with one filled cell whose first paragraph (or whole text) is a contents title.

        Returns the heading and the row with that paragraph taken out (None if
        nothing is left), or (None, None) when the row holds no title.
        """
        cells = [cell for cell in row.kids if isinstance(cell, Element) and self.text(cell)]
        if len(cells) != 1:
            return None, None
        cell = cells[0]
        first = next((kid for kid in cell.kids if isinstance(kid, Element) and kid.type == "P"), None)
        heading = self.contents_heading(self.text(first if first is not None else cell))
        if not heading:
            return None, None
        if first is None:
            return heading, None
        rest = Element(cell.type, [kid for kid in cell.kids if kid is not first], page=cell.page,
                       column_span=cell.column_span, row_span=cell.row_span)
        if not self.text(rest):
            return heading, None
        return heading, Element(row.type, [rest if kid is cell else kid for kid in row.kids], page=row.page)

    def find_contents_titles(self, root: Element) -> None:
        """The contents list's titles in order, each with the heading level it stands for.

        Levels come from the contents list's indentation: entries indented like
        a tagged heading's entry take that heading's level, and each step further
        in is one level deeper.
        """
        entries = []  # (title, indent)
        for entry in _all(root, "TOCI"):
            title = _CONTENTS_TAIL.sub("", self.text(entry, skip={"TOC"})).casefold()
            chars = [o for c in contents(entry, {"TOC"}) for o in self.objects.get((c.page, c.mcid), [])
                     if o["object_type"] == "char" and o["text"].strip()]
            if title and chars:
                entries.append((title, min(c["x0"] for c in chars)))
        tagged: dict[str, list[int]] = {}
        for heading in _all(root, "H", "H1", "H2", "H3", "H4", "H5", "H6"):
            tagged.setdefault(self.text(heading).casefold(), []).append(int(heading.type[1:] or 1))
        ranks: dict[float, int] = {}  # indent -> rank, counting indents within _INDENT_STEP as one
        previous = None
        for indent in sorted({indent for _, indent in entries}):
            rank = (ranks[previous] + (indent - previous > _INDENT_STEP)) if previous is not None else 0
            ranks[indent] = rank
            previous = indent
        known: dict[int, int] = {}  # indent rank -> heading level
        for title, indent in entries:
            if tagged.get(title):
                known.setdefault(ranks[indent], tagged[title][0])
        self.contents_titles = []
        for title, indent in entries:
            rank = ranks[indent]
            nearest = min(known, key=lambda r: abs(r - rank), default=None)
            level = known[nearest] + rank - nearest if nearest is not None else rank + 1
            self.contents_titles.append((title, min(max(level, 1), 6)))

    def linked_text(self, element: Element, skip=frozenset()) -> str:
        """The element's text with its web links as Markdown links; links within the PDF stay plain text."""
        text = self.text(element, skip)
        for link in _descendants(element, "Link", skip):
            uri = next((kid.uri for kid in link.kids if isinstance(kid, Annotation) and kid.uri), None)
            label = self.text(link)
            if uri and label and label in text:
                text = text.replace(label, f"[{label}]({uri})", 1)
        return text

    def figure(self, element: Element) -> None:
        """Link the figure where it stands, described by its alternative text (StR-046).

        A figure that is a single Embedded Image is saved as that image; one with
        drawing, or several images, becomes one Figure Snapshot of its area. A
        figure holding paragraphs (a text box) is read as text instead, by
        `render`, and so is one whose area is mostly text tagged elsewhere.
        """
        owned = [(content.page, item) for content in contents(element)
                 for item in self.objects.get((content.page, content.mcid), [])]
        images = [(page, item) for page, item in owned if item["object_type"] == "image"]
        drawn = [(page, item) for page, item in owned if item["object_type"] in ("rect", "line", "curve")]
        if not images and not drawn:
            return
        page = (images or drawn)[0][0]
        if len(images) == 1 and not drawn:
            link = self.assets.link(page, images[0][1]["name"])
        else:
            bbox = element.bbox or _bounds(item for item_page, item in owned if item_page == page)
            if _only_a_frame(images, drawn) and self.text_inside(page, bbox, owned) > _TEXT_BOX_CHARS:
                return  # a box around text that is already in the Converted Document
            for image_page, image in images:
                self.assets.reached(image_page, image["name"])
            link = self.assets.snapshot(page, bbox)
        if link:
            alt = _clean(element.alt or "").replace("]", "\\]")
            self.blocks.append(Block(page, f"![{alt}]({link})"))

    def text_inside(self, page: int, bbox: tuple[float, float, float, float], owned: list) -> int:
        """How many tagged characters, other than the figure's own, lie inside `bbox` on the page."""
        own = {id(item) for _, item in owned}
        x0, y0, x1, y1 = bbox
        return sum(1 for (number, mcid), items in self.objects.items() if number == page and mcid is not None
                   for item in items if item["object_type"] == "char" and id(item) not in own
                   and item["text"].strip() and x0 <= item["x0"] and item["x1"] <= x1
                   and y0 <= item["y0"] and item["y1"] <= y1)

    def contents_entries(self, element: Element, depth: int) -> list[str]:
        """A contents list as list items: entry titles without dot leaders or page numbers."""
        entries = []
        for entry in (kid for kid in element.kids if isinstance(kid, Element)):
            title = _CONTENTS_TAIL.sub("", self.linked_text(entry, skip={"TOC"}))
            if title:
                entries.append("  " * depth + "- " + escape(title))
            for nested in _descendants(entry, "TOC"):
                entries += self.contents_entries(nested, depth + 1)
        return entries

    def table(self, table_rows: list[Element]) -> str:
        """One Markdown table of `table_rows`, however many pages it runs over; the first row is the header row.

        A merged cell leaves the cells it covers blank, across columns and down rows.
        """
        rows = []
        covered: dict[int, int] = {}  # column -> how many more rows a cell above still covers
        for row in table_rows:
            cells: list[str] = []
            for cell in (kid for kid in row.kids if isinstance(kid, Element)):
                while covered.get(len(cells)):
                    cells.append("")
                for offset in range(cell.column_span):
                    if cell.row_span > 1:
                        covered[len(cells) + offset] = cell.row_span
                cells += [self.cell_text(cell)] + [""] * (cell.column_span - 1)
            while covered.get(len(cells)):
                cells.append("")
            covered = {column: rows_left - 1 for column, rows_left in covered.items() if rows_left > 1}
            rows.append(cells)
        if not rows:
            return ""
        width = max(len(row) for row in rows)
        lines = ["| " + " | ".join(row + [""] * (width - len(row))) + " |" for row in rows]
        return "\n".join([lines[0], "|" + "---|" * width, *lines[1:]])

    def cell_text(self, cell: Element) -> str:
        """A cell's paragraphs and list items, one per `<br>`-separated line."""
        parts = [self.linked_text(kid) for kid in cell.kids if isinstance(kid, Element) and kid.type == "P"]
        parts += [line.strip() for nested in _descendants(cell, "L") for _, line in self.list_items(nested, 0)]
        if not parts:
            parts = [self.linked_text(cell)]
        return "<br>".join(part for part in parts if part).replace("|", "\\|")

    def list_items(self, element: Element, depth: int) -> list[tuple[bool, str]]:
        """(is a bullet, line) for each item of a list and its nested lists.

        Bullets become Markdown list items indented by bullet depth. Numbered and
        lettered items are paragraphs starting with their label as written, the
        way Word documents' numbering is written out (ADR 0007).
        """
        items = []
        for item in (kid for kid in element.kids if isinstance(kid, Element)):
            label = _clean(" ".join(self.text(kid) for kid in item.kids
                                    if isinstance(kid, Element) and kid.type == "Lbl"))
            body = self.linked_text(item, skip={"Lbl", "L"})
            if not label or set(label.replace(" ", "")) <= _BULLETS:
                items.append((True, "  " * depth + "- " + escape(body)))
                nested_depth = depth + 1
            else:
                items.append((False, escape(f"{label} {body}")))
                nested_depth = depth
            for nested in _descendants(item, "L"):
                items += self.list_items(nested, nested_depth)
        return items


def blocks(root: Element, objects: dict, assets) -> list[Block]:
    """The Converted Document's blocks for a Tagged PDF, in the tags' reading order.

    `assets` saves figures: `link(page, image name)` saves an Embedded Image as-is,
    `snapshot(page, bbox)` renders an area as a Figure Snapshot, and
    `reached(page, image name)` records an image a snapshot already shows. Each
    saving method returns the Asset's link, or None if it was dropped.
    """
    renderer = _Renderer(objects, assets)
    renderer.find_contents_titles(root)
    renderer.render(root)
    return renderer.blocks


def _all(element: Element, *types: str):
    """Every element of the given types under `element`, nested ones included, in reading order."""
    for kid in element.kids:
        if isinstance(kid, Element):
            if kid.type in types:
                yield kid
            yield from _all(kid, *types)


def _only_a_frame(images: list, drawn: list) -> bool:
    """Whether a figure draws no more than a box: no images, no curves, and at most four rectangles or lines."""
    return (not images and len(drawn) <= _FRAME_SHAPES
            and all(item["object_type"] != "curve" for _, item in drawn))


def _bounds(items) -> tuple[float, float, float, float]:
    """The smallest box (PDF user space) around pdfplumber objects."""
    items = list(items)
    return (min(i["x0"] for i in items), min(i["y0"] for i in items),
            max(i["x1"] for i in items), max(i["y1"] for i in items))


def _join_list(items: list[tuple[bool, str]]) -> str:
    """Bullets on consecutive lines; a labelled paragraph gets a blank line either side."""
    out = []
    for index, (bullet, line) in enumerate(items):
        if index:
            out.append("\n" if bullet and items[index - 1][0] else "\n\n")
        out.append(line)
    return "".join(out)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def escape(text: str) -> str:
    """'3. ...' would be a Markdown list item that viewers renumber; '3\\. ...' shows as written."""
    return _LIST_LIKE_START.sub(r"\1\\\2", text)
