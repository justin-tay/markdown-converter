"""Word list and heading numbers, written into the text so labels like 1.2.4.a survive.

Word doesn't store a numbered paragraph's label as text: the paragraph says
"level 4 of list 90" and Word works the label out from numbering.xml when it
displays the document. mammoth turns such paragraphs into plain Markdown lists,
so legal-style labels (1.2.4.a), letters, Roman numerals and numbered headings
are lost. Here each numbered paragraph gets its label as literal text, and its
numbering is switched off so mammoth treats it as an ordinary paragraph.
Bullet lists are left as lists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from lxml import etree

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{_W_NS}}}"
_XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
_PLACEHOLDER = re.compile(r"%([1-9])")

# U+27E6/U+27E7 brackets survive Markdown escaping (as with chart markers).
_LABEL_MARKER = re.compile(r"⟦label:([^⟧]*)⟧")
_LIST_LIKE_LABEL_AT_LINE_START = re.compile(r"(?m)^⟦label:(\d{1,9})([.)])⟧")
_CONTENT = {f"{_W}drawing", f"{_W}pict", f"{_W}object", f"{_W}sym"}


@dataclass
class _Level:
    start: int = 1
    fmt: str = "decimal"
    text: str = ""
    legal: bool = False  # isLgl: show every level as a plain number
    style: str | None = None  # the paragraph style this level numbers, if any
    hidden: bool = False  # the number itself is formatted as hidden text


@dataclass
class _List:
    abstract_id: str
    levels: dict[int, _Level]
    start_overrides: dict[int, int] = field(default_factory=dict)


def label_numbered_paragraphs(document_xml: bytes, numbering_xml: bytes | None, styles_xml: bytes | None) -> bytes:
    """Return document.xml with each numbered paragraph's label written as text."""
    if numbering_xml is None:
        return document_xml
    styles = etree.fromstring(styles_xml) if styles_xml else None
    lists = _read_lists(etree.fromstring(numbering_xml), _read_numbering_styles(styles) if styles is not None else {})
    style_numbering = _read_style_numbering(styles) if styles is not None else {}
    # A list level can also name the style it numbers, with nothing on the style itself.
    for num_id, listing in lists.items():
        for ilvl, level in listing.levels.items():
            if level.style:
                style_numbering.setdefault(level.style, (num_id, ilvl))
    document = etree.fromstring(document_xml)
    counters: dict[str, dict[int, int]] = {}
    started: set[str] = set()
    for paragraph in document.iter(f"{_W}p"):
        num_id, level = _numbering_of(paragraph, style_numbering)
        listing = lists.get(num_id) if num_id else None
        if listing is None or level not in listing.levels or listing.levels[level].fmt == "bullet":
            continue
        counts = counters.setdefault(listing.abstract_id, {})
        if num_id not in started:
            started.add(num_id)
            for overridden, start in listing.start_overrides.items():
                counts[overridden] = start - 1
        counts[level] = counts.get(level, listing.levels[level].start - 1) + 1
        # An item below levels not yet used counts them as used at their start values,
        # so a later item at those levels is the next number: 1.1, 1.2, then 2.
        for shallower in range(level):
            counts.setdefault(shallower, listing.levels.get(shallower, _Level()).start)
        for deeper in [lvl for lvl in counts if lvl > level]:
            del counts[deeper]  # a new item restarts every level below it
        # Still counted, but nothing to show: templates often put an empty, hidden
        # paragraph under each heading just to move a list's chapter number on.
        if listing.levels[level].hidden or not _has_visible_content(paragraph):
            _switch_off_numbering(paragraph)
            continue
        label = _label(listing, level, counts)
        if label:
            _write_label(paragraph, label)
    return etree.tostring(document, xml_declaration=True, encoding="UTF-8", standalone=True)


def restore_labels(markdown: str) -> str:
    """Turn label markers back into text, kept literal where Markdown would see a list.

    A line starting "3. " is a Markdown ordered-list item, which viewers
    renumber; "3\\. " shows exactly "3. ".
    """
    markdown = _LIST_LIKE_LABEL_AT_LINE_START.sub(lambda m: f"{m.group(1)}\\{m.group(2)}", markdown)
    return _LABEL_MARKER.sub(lambda m: m.group(1), markdown)


def _read_lists(numbering: etree._Element, numbering_styles: dict[str, str]) -> dict[str, _List]:
    abstracts, defines_style, uses_style = {}, {}, {}
    abstract_of = {num.get(f"{_W}numId"): _val(num.find(f"{_W}abstractNumId")) for num in numbering.iter(f"{_W}num")}
    for abstract in numbering.iter(f"{_W}abstractNum"):
        abstract_id = abstract.get(f"{_W}abstractNumId")
        abstracts[abstract_id] = {
            int(level.get(f"{_W}ilvl")): _read_level(level) for level in abstract.iter(f"{_W}lvl")
        }
        if (style_link := _val(abstract.find(f"{_W}styleLink"))) is not None:
            defines_style[style_link] = abstract_id
        if (num_style_link := _val(abstract.find(f"{_W}numStyleLink"))) is not None:
            uses_style[abstract_id] = num_style_link
    # Numbering styles not declared by any list stand for the list styles.xml names.
    for style_id, num_id in numbering_styles.items():
        if style_id not in defines_style and abstract_of.get(num_id) in abstracts:
            defines_style[style_id] = abstract_of[num_id]
    lists = {}
    for num in numbering.iter(f"{_W}num"):
        abstract_id = _val(num.find(f"{_W}abstractNumId"))
        # A list may only point at a numbering style; its levels live on the list
        # that defines that style, and lists sharing the style count together.
        abstract_id = defines_style.get(uses_style.get(abstract_id), abstract_id)
        if abstract_id not in abstracts:
            continue
        levels = dict(abstracts[abstract_id])
        overrides = {}
        for override in num.iter(f"{_W}lvlOverride"):
            ilvl = int(override.get(f"{_W}ilvl"))
            start = override.find(f"{_W}startOverride")
            if start is not None:
                overrides[ilvl] = int(_val(start))
            replacement = override.find(f"{_W}lvl")
            if replacement is not None:
                levels[ilvl] = _read_level(replacement)
        lists[num.get(f"{_W}numId")] = _List(abstract_id, levels, overrides)
    return lists


def _read_level(level: etree._Element) -> _Level:
    start = level.find(f"{_W}start")
    return _Level(
        start=int(_val(start)) if start is not None else 1,
        fmt=_val(level.find(f"{_W}numFmt")) or "decimal",
        text=_val(level.find(f"{_W}lvlText")) or "",
        legal=level.find(f"{_W}isLgl") is not None,
        style=_val(level.find(f"{_W}pStyle")),
        hidden=_is_on(level.find(f"{_W}rPr/{_W}vanish")),
    )


def _read_style_numbering(styles: etree._Element) -> dict[str, tuple[str | None, int]]:
    """Style id -> (numId, level) for styles that number their paragraphs, following basedOn.

    The list and the level are inherited separately: an outline's deeper styles
    often set only their level and take the list from the style they're based on.
    """
    num_ids, levels, based_on = {}, {}, {}
    for style in styles.iter(f"{_W}style"):
        style_id = style.get(f"{_W}styleId")
        num_pr = style.find(f"{_W}pPr/{_W}numPr")
        if num_pr is not None:
            if (num_id := _val(num_pr.find(f"{_W}numId"))) is not None:
                num_ids[style_id] = num_id
            if (ilvl := _val(num_pr.find(f"{_W}ilvl"))) is not None:
                levels[style_id] = int(ilvl)
        parent = style.find(f"{_W}basedOn")
        if parent is not None:
            based_on[style_id] = _val(parent)

    def inherited(style_id: str, own: dict):
        current, seen = style_id, set()
        while current and current not in own and current not in seen:
            seen.add(current)
            current = based_on.get(current)
        return own.get(current)

    resolved = {}
    for style_id in set(num_ids) | set(levels) | set(based_on):
        num_id = inherited(style_id, num_ids)
        if num_id is not None:
            resolved[style_id] = (num_id, inherited(style_id, levels) or 0)
    return resolved


def _read_numbering_styles(styles: etree._Element) -> dict[str, str]:
    """Numbering style id -> the numId it stands for."""
    found = {}
    for style in styles.iter(f"{_W}style"):
        num_id = _val(style.find(f"{_W}pPr/{_W}numPr/{_W}numId"))
        if style.get(f"{_W}type") == "numbering" and num_id is not None:
            found[style.get(f"{_W}styleId")] = num_id
    return found


def _numbering_of(paragraph: etree._Element, style_numbering) -> tuple[str | None, int]:
    properties = paragraph.find(f"{_W}pPr")
    style = _val(properties.find(f"{_W}pStyle")) if properties is not None else None
    num_id, level = style_numbering.get(style, (None, 0))
    num_pr = properties.find(f"{_W}numPr") if properties is not None else None
    if num_pr is not None:
        num_id = _val(num_pr.find(f"{_W}numId")) or num_id
        ilvl = num_pr.find(f"{_W}ilvl")
        level = int(_val(ilvl)) if ilvl is not None else level
    return (None if num_id in (None, "0") else num_id), level


def _label(listing: _List, level: int, counts: dict[int, int]) -> str:
    current = listing.levels[level]
    if current.fmt == "none":
        return ""

    def number(match: re.Match) -> str:
        shown = int(match.group(1)) - 1
        definition = listing.levels.get(shown, _Level())
        value = counts.get(shown, definition.start)
        fmt = "decimal" if current.legal and shown < level else definition.fmt
        return _format(value, fmt)

    return _PLACEHOLDER.sub(number, current.text).strip()


def _format(value: int, fmt: str) -> str:
    if fmt in ("lowerLetter", "upperLetter"):
        if value < 1:
            return str(value)
        # Word repeats the letter after z: y, z, aa, bb, ... zz, aaa.
        repeats, remainder = divmod(value - 1, 26)
        letters = chr(ord("a") + remainder) * (repeats + 1)
        return letters.upper() if fmt == "upperLetter" else letters
    if fmt in ("lowerRoman", "upperRoman"):
        roman = _roman(value)
        return roman if fmt == "upperRoman" else roman.lower()
    if fmt == "decimalZero":
        return f"{value:02d}"
    return str(value)


def _roman(value: int) -> str:
    numerals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
                (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for amount, numeral in numerals:
        while value >= amount:
            out += numeral
            value -= amount
    return out or "0"


def _has_visible_content(paragraph: etree._Element) -> bool:
    """True when the paragraph shows any text (outside hidden runs) or a picture."""
    for run in paragraph.iter(f"{_W}r"):
        if _is_on(run.find(f"{_W}rPr/{_W}vanish")):
            continue
        if any(child.tag in _CONTENT for child in run.iter()):
            return True
        if any((text.text or "").strip() for text in run.iter(f"{_W}t")):
            return True
    return False


def _switch_off_numbering(paragraph: etree._Element) -> etree._Element:
    """Mark the paragraph "not numbered", overriding any numbering from its style.

    numId 0 means not numbered. The level must be given too: without it mammoth
    falls back to the style's list and numbers the paragraph again ("1. 17.5.1").
    """
    properties = paragraph.find(f"{_W}pPr")
    if properties is None:
        properties = etree.Element(f"{_W}pPr")
        paragraph.insert(0, properties)
    for old in properties.findall(f"{_W}numPr"):
        properties.remove(old)
    num_pr = etree.SubElement(properties, f"{_W}numPr")
    etree.SubElement(num_pr, f"{_W}ilvl").set(f"{_W}val", "0")
    etree.SubElement(num_pr, f"{_W}numId").set(f"{_W}val", "0")
    return properties


def _write_label(paragraph: etree._Element, label: str) -> None:
    properties = _switch_off_numbering(paragraph)
    run = etree.Element(f"{_W}r")
    text = etree.SubElement(run, f"{_W}t")
    text.set(_XML_SPACE, "preserve")
    text.text = f"⟦label:{label}⟧ "
    properties.addnext(run)


def _is_on(toggle: etree._Element | None) -> bool:
    """Word on/off properties: present means on unless w:val says false."""
    return toggle is not None and toggle.get(f"{_W}val", "true").lower() not in ("false", "0", "off")


def _val(element: etree._Element | None) -> str | None:
    return None if element is None else element.get(f"{_W}val")
