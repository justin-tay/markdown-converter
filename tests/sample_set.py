"""Deterministic generator for the Sample Set (StRS section 6.2).

Run directly to build every sample into a folder:

    python tests/sample_set.py <output-folder>
"""

from __future__ import annotations

import io
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import cfb

# Document metadata timestamps are pinned so samples are identical on every build.
FIXED_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
ZIP_TIME = (2026, 1, 1, 0, 0, 0)

CSV_TEXT = "Region,Q1,Q2\nNorth,10,12\nSouth,7,9\n"

JSON_TEXT = '{"project": "Apollo", "owner": "Ops", "budget": 1200}\n'

XML_TEXT = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<inventory><item sku=\"A1\">Widget</item><item sku=\"B2\">Gadget</item></inventory>\n"
)


def _write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8", newline="")
    return path


def _write_zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            info = zipfile.ZipInfo(name, ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return path


def build_csv(folder: Path) -> Path:
    return _write_text(folder / "sales.csv", CSV_TEXT)


def build_json(folder: Path) -> Path:
    return _write_text(folder / "project.json", JSON_TEXT)


def build_xml(folder: Path) -> Path:
    return _write_text(folder / "inventory.xml", XML_TEXT)


def build_text_docx(folder: Path) -> Path:
    """A text-only Word document with a heading, a list and a table."""
    import docx

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    document.add_heading("Quarterly Memo", level=1)
    document.add_paragraph("Summary of the quarter.")
    document.add_paragraph("Revenue grew", style="List Bullet")
    document.add_paragraph("Costs fell", style="List Bullet")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Metric"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Revenue"
    table.cell(1, 1).text = "120"
    path = folder / "memo.docx"
    document.save(path)
    return path


def png_bytes(width: int, height: int, colour: tuple[int, int, int]) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, "PNG")
    return buffer.getvalue()


def jpeg_bytes(width: int, height: int, colour: tuple[int, int, int]) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, "JPEG", quality=90)
    return buffer.getvalue()


def emf_bytes() -> bytes:
    """The smallest valid Enhanced Metafile: a header record and an end-of-file record."""
    import struct

    header = struct.pack(
        "<II4i4iIIIIHHIII2i2i",
        1, 88, 0, 0, 10, 10, 0, 0, 264, 264,  # EMR_HEADER, size, bounds, frame
        0x464D4520, 0x10000, 108, 2, 1, 0, 0, 0, 0,  # " EMF", version, bytes, records...
        1024, 768, 320, 240,  # device size in pixels and millimetres
    )
    end_of_file = struct.pack("<IIIII", 14, 20, 0, 16, 20)
    return header + end_of_file


LOGO_PNG = png_bytes(64, 32, (20, 90, 160))


def build_word_with_images(folder: Path) -> Path:
    """S-05 (images): a repeated logo, a photo, a tiny icon and an EMF drawing."""
    import docx

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    document.add_heading("Site Report", level=1)
    document.add_paragraph("Company logo:")
    document.add_picture(io.BytesIO(LOGO_PNG))
    document.add_paragraph("Photo of the site:")
    document.add_picture(io.BytesIO(jpeg_bytes(80, 60, (90, 160, 20))))
    document.add_paragraph("Status icon:")
    document.add_picture(io.BytesIO(png_bytes(8, 8, (200, 0, 0))))
    document.add_paragraph("Floor plan:")
    # python-docx can't embed EMF, so add a placeholder and swap it in the package below.
    document.add_picture(io.BytesIO(png_bytes(16, 16, (1, 2, 3))))
    document.add_paragraph("Logo again in the footer:")
    document.add_picture(io.BytesIO(LOGO_PNG))
    buffer = io.BytesIO()
    document.save(buffer)
    return _replace_placeholder_with_emf(buffer.getvalue(), folder / "site-report.docx")


def build_word_with_header_logo(folder: Path) -> Path:
    """A letter whose only image is a logo in the page header, which markitdown skips."""
    import docx

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    document.sections[0].header.paragraphs[0].add_run().add_picture(io.BytesIO(LOGO_PNG))
    document.add_paragraph("Dear customer,")
    path = folder / "letter.docx"
    document.save(path)
    return path


_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _add_numbering(document, abstract_id: int, num_id: int, levels: list[tuple[str, str]],
                   start_override: dict[int, int] | None = None) -> None:
    """Define a list in numbering.xml the way Word does: levels of (format, label pattern)."""
    from docx.oxml import parse_xml

    numbering = document.part.numbering_part.element
    level_xml = "".join(
        f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{text}"/></w:lvl>'
        for i, (fmt, text) in enumerate(levels)
    )
    overrides = "".join(
        f'<w:lvlOverride w:ilvl="{level}"><w:startOverride w:val="{start}"/></w:lvlOverride>'
        for level, start in (start_override or {}).items()
    )
    # abstractNum elements must come before num elements in numbering.xml.
    first_num = numbering.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num")
    abstract = parse_xml(f'<w:abstractNum {_W} w:abstractNumId="{abstract_id}">{level_xml}</w:abstractNum>')
    if first_num is None:
        numbering.append(abstract)
    else:
        first_num.addprevious(abstract)
    numbering.append(parse_xml(
        f'<w:num {_W} w:numId="{num_id}"><w:abstractNumId w:val="{abstract_id}"/>{overrides}</w:num>'
    ))


def _numbered(document, text: str, num_id: int, level: int, style: str | None = None):
    from docx.oxml import parse_xml

    paragraph = document.add_paragraph(text, style=style)
    paragraph._p.get_or_add_pPr().append(
        parse_xml(f'<w:numPr {_W}><w:ilvl w:val="{level}"/><w:numId w:val="{num_id}"/></w:numPr>')
    )
    return paragraph


def build_numbered_word(folder: Path) -> Path:
    """Word numbering that exists only in numbering.xml: legal-style clauses, numbered
    headings (numbering set on the heading styles), Roman numerals, a list that
    restarts at 5, and a bullet list."""
    import docx
    from docx.oxml import parse_xml

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    _add_numbering(document, 90, 90, [
        ("decimal", "%1."), ("decimal", "%1.%2."), ("decimal", "%1.%2.%3."), ("lowerLetter", "%1.%2.%3.%4"),
    ])
    _add_numbering(document, 91, 91, [("decimal", "%1"), ("decimal", "%1.%2")])
    _add_numbering(document, 92, 92, [("upperRoman", "%1."), ("lowerRoman", "(%2)")])
    _add_numbering(document, 93, 93, [("decimal", "%1.")], start_override={0: 5})
    _add_numbering(document, 94, 94, [("bullet", "•")])

    # Numbered headings: the numbering lives on the Heading styles, not the paragraphs.
    for style_name, level in (("Heading 1", 0), ("Heading 2", 1)):
        document.styles[style_name].element.get_or_add_pPr().append(
            parse_xml(f'<w:numPr {_W}><w:ilvl w:val="{level}"/><w:numId w:val="91"/></w:numPr>')
        )

    document.add_heading("Introduction", level=1)
    document.add_heading("Purpose", level=2)
    document.add_heading("Terms", level=1)
    for text, level in [("Scope", 0), ("Definitions", 1), ("Services", 1), ("Delivery", 2), ("Support", 2),
                        ("Hours", 2), ("Response times", 2), ("Priority 1", 3), ("Priority 2", 3), ("Payment", 0)]:
        _numbered(document, text, 90, level)
    document.add_heading("Schedules", level=1)
    for text, level in [("Pricing", 0), ("Discounts", 1), ("Rebates", 1), ("Penalties", 0)]:
        _numbered(document, text, 92, level)
    for text in ["Fifth step", "Sixth step"]:
        _numbered(document, text, 93, 0)
    for text in ["Apples", "Pears"]:
        _numbered(document, text, 94, 0)
    path = folder / "contract.docx"
    document.save(path)
    return path


def build_clause_styled_word(folder: Path, styles_name_the_list: bool = True) -> Path:
    """Numbering as contract templates set it up: custom clause styles linked to a
    list from both sides (the style names the list, each list level names its
    style), the list reached through a numbering style (numStyleLink), and
    numbering that starts at 17.5. With styles_name_the_list=False the link is
    only made from the list's side, as some templates do."""
    import docx
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml import parse_xml

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    numbering = document.part.numbering_part.element
    levels = "".join(
        f'<w:lvl w:ilvl="{i}"><w:start w:val="{start}"/><w:numFmt w:val="decimal"/>'
        f'<w:pStyle w:val="Clause{i + 1}"/><w:lvlText w:val="{text}"/></w:lvl>'
        for i, (start, text) in enumerate([(17, "%1"), (5, "%1.%2"), (1, "%1.%2.%3")])
    )
    # The real levels live on the list that defines the "ContractClauses" numbering style...
    numbering.insert(0, parse_xml(
        f'<w:abstractNum {_W} w:abstractNumId="80"><w:styleLink w:val="ContractClauses"/>{levels}</w:abstractNum>'
    ))
    # ...and the list the paragraphs use only points at that numbering style.
    numbering.insert(1, parse_xml(
        f'<w:abstractNum {_W} w:abstractNumId="81"><w:numStyleLink w:val="ContractClauses"/></w:abstractNum>'
    ))
    numbering.append(parse_xml(f'<w:num {_W} w:numId="80"><w:abstractNumId w:val="80"/></w:num>'))
    numbering.append(parse_xml(f'<w:num {_W} w:numId="81"><w:abstractNumId w:val="81"/></w:num>'))
    for level in range(3):
        style = document.styles.add_style(f"Clause{level + 1}", WD_STYLE_TYPE.PARAGRAPH)
        if styles_name_the_list:
            ilvl = "" if level == 0 else f'<w:ilvl w:val="{level}"/>'  # level 0 is implied
            style.element.get_or_add_pPr().append(
                parse_xml(f'<w:numPr {_W}>{ilvl}<w:numId w:val="81"/></w:numPr>')
            )
    for text, level in [("Warranties", 1), ("Scope", 2), ("Hardware", 3), ("Software", 3), ("Liability", 1)]:
        document.add_paragraph(text, style=f"Clause{level}")
    path = folder / "clauses.docx"
    document.save(path)
    return path


def build_chapter_clauses_word(folder: Path) -> Path:
    """A specification laid out the way many templates do it: chapter headings
    from one list, clauses from another, and under each heading an empty, hidden
    paragraph at the clause list's first level that moves its chapter number on
    so the clauses read 3.1, 3.2... Also an empty numbered paragraph that isn't
    hidden, which shows no text."""
    import docx
    from docx.oxml import parse_xml

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    _add_numbering(document, 70, 70, [("decimal", "%1.")])
    _add_numbering(document, 71, 71, [("decimal", "%1."), ("decimal", "%1.%2")])

    def chapter(title: str):
        heading = _numbered(document, "", 70, 0)
        heading.add_run(title).bold = True
        hidden = _numbered(document, "", 71, 0)
        hidden._p.get_or_add_pPr().append(parse_xml(f"<w:rPr {_W}><w:vanish/></w:rPr>"))

    def clause(bold: str, rest: str):
        paragraph = _numbered(document, "", 71, 1)
        paragraph.add_run(bold).bold = True
        paragraph.add_run(rest)

    for title in ("PLANNING", "SOWING"):
        chapter(title)
        clause("Background", " is described here.")
    chapter("HARVEST")
    clause("Garden layout", " follows the plan in this chapter.")
    _numbered(document, "", 71, 1)  # an empty clause: still counted, nothing to show
    clause("Watering", " happens twice a week.")
    path = folder / "specification.docx"
    document.save(path)
    return path


def build_outline_through_numbering_style_word(folder: Path) -> Path:
    """Headings and the clauses under them numbered from one outline, the clauses
    reaching it only through a numbering style: their list's numStyleLink names a
    numbering style whose numPr in styles.xml points at the headings' list, and
    no list declares that style with styleLink. Unnumbered paragraphs and a table
    interrupt the clauses."""
    import docx
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml import parse_xml

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    _add_numbering(document, 60, 60, [("decimal", "%1"), ("decimal", "%1.%2"), ("decimal", "%1.%2.%3")])
    numbering = document.part.numbering_part.element
    numbering.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num").addprevious(parse_xml(
        f'<w:abstractNum {_W} w:abstractNumId="61"><w:numStyleLink w:val="GardenOutline"/></w:abstractNum>'
    ))
    numbering.append(parse_xml(f'<w:num {_W} w:numId="61"><w:abstractNumId w:val="61"/></w:num>'))
    outline = document.styles.add_style("GardenOutline", WD_STYLE_TYPE.LIST)
    outline.element.get_or_add_pPr().append(parse_xml(f'<w:numPr {_W}><w:numId w:val="60"/></w:numPr>'))

    _numbered(document, "Planting", 60, 0)
    _numbered(document, "Soil", 61, 1)
    _numbered(document, "Beds are dug in spring.", 61, 2)
    document.add_paragraph("A note between clauses.")
    _numbered(document, "Compost is added each autumn.", 61, 2)
    document.add_table(rows=1, cols=1).cell(0, 0).text = "Bed sizes"
    _numbered(document, "Seeds", 61, 1)
    _numbered(document, "Harvest", 60, 0)
    _numbered(document, "Picking", 61, 1)
    path = folder / "outline.docx"
    document.save(path)
    return path


def build_list_starting_below_its_top_level_word(folder: Path) -> Path:
    """Lists whose first items are at level 2, before any level-1 item: Word counts
    the missing level 1 as used at its start value. One list starts at 1, the
    other at 3."""
    import docx

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    _add_numbering(document, 30, 30, [("decimal", "%1"), ("decimal", "%1.%2")])
    _add_numbering(document, 31, 31, [("decimal", "%1"), ("decimal", "%1.%2")])
    document.part.numbering_part.element.find(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}abstractNum[@{http://schemas.openxmlformats.org/wordprocessingml/2006/main}abstractNumId='31']"
        "/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lvl"
        "/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}start"
    ).set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "3")
    for num_id in (30, 31):
        for text, level in [("Tools", 1), ("Gloves", 1), ("Sowing", 0), ("Seeds", 1), ("Weeding", 0)]:
            _numbered(document, f"{text} {num_id}", num_id, level)
    path = folder / "early.docx"
    document.save(path)
    return path


def build_long_lettered_list_word(folder: Path) -> Path:
    """A lettered list of 55 items, long enough to run past z twice."""
    import docx

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    _add_numbering(document, 40, 40, [("lowerLetter", "(%1)")])
    for item in range(1, 56):
        _numbered(document, f"Item {item}", 40, 0)
    path = folder / "lettered.docx"
    document.save(path)
    return path


def build_inherited_outline_styles_word(folder: Path) -> Path:
    """An outline numbered entirely by paragraph styles, each list level naming
    its style: the first style names the list, and each deeper style is based on
    the one above it and sets only its level, inheriting the list. Unnumbered
    paragraphs and a table interrupt the clauses."""
    import docx
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml import parse_xml

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    numbering = document.part.numbering_part.element
    levels = "".join(
        f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
        f'<w:pStyle w:val="Outline{i + 1}"/><w:lvlText w:val="{text}"/></w:lvl>'
        for i, text in enumerate(["%1", "%1.%2", "%1.%2.%3"])
    )
    numbering.insert(0, parse_xml(f'<w:abstractNum {_W} w:abstractNumId="50">{levels}</w:abstractNum>'))
    numbering.append(parse_xml(f'<w:num {_W} w:numId="50"><w:abstractNumId w:val="50"/></w:num>'))
    base = None
    for level in range(3):
        style = document.styles.add_style(f"Outline{level + 1}", WD_STYLE_TYPE.PARAGRAPH)
        if base is not None:
            style.base_style = base
        own = '<w:numId w:val="50"/>' if level == 0 else f'<w:ilvl w:val="{level}"/>'
        style.element.get_or_add_pPr().append(parse_xml(f'<w:numPr {_W}>{own}</w:numPr>'))
        base = style

    for text, level in [("Planting", 1), ("Soil", 2), ("Beds are dug in spring.", 3)]:
        document.add_paragraph(text, style=f"Outline{level}")
    document.add_paragraph("A note between clauses.")
    document.add_paragraph("Compost is added each autumn.", style="Outline3")
    document.add_table(rows=1, cols=1).cell(0, 0).text = "Bed sizes"
    for text, level in [("Seeds", 2), ("Harvest", 1), ("Picking", 2)]:
        document.add_paragraph(text, style=f"Outline{level}")
    path = folder / "outline.docx"
    document.save(path)
    return path


def build_numbered_pdf(folder: Path) -> Path:
    """A PDF where each clause label and its text are separate pieces with a gap, as
    Word's tab-aligned numbering exports them."""
    from reportlab.pdfgen import canvas

    path = folder / "contract.pdf"
    pdf = canvas.Canvas(str(path), invariant=1)
    pdf.drawString(72, 790, "Contract terms")
    y = 760
    for indent, label, text in [
        (0, "1.", "Scope"), (1, "1.1.", "Definitions"), (1, "1.2.", "Services"),
        (2, "1.2.4.", "Response times"), (3, "1.2.4.a", "Priority 1"), (3, "1.2.4.b", "Priority 2"),
        (0, "2.", "Payment"),
    ]:
        pdf.drawString(72 + 24 * indent, y, label)
        pdf.drawString(72 + 24 * indent + 50, y, text)
        y -= 20
    pdf.drawString(72, 560, "This paragraph wraps onto a second line because it is long enough")
    pdf.drawString(72, 546, "to need one, and both lines belong together.")
    pdf.showPage()
    pdf.save()
    return path


def build_slides(folder: Path) -> Path:
    """S-06: slides with images, speaker notes and a hidden slide."""
    from pptx import Presentation
    from pptx.util import Inches

    deck = Presentation()
    deck.core_properties.created = FIXED_TIME
    deck.core_properties.modified = FIXED_TIME
    layout = deck.slide_layouts[5]  # title only

    intro = deck.slides.add_slide(layout)
    intro.shapes.title.text = "Quarterly Results"
    intro.shapes.add_picture(io.BytesIO(LOGO_PNG), Inches(1), Inches(2))

    detail = deck.slides.add_slide(layout)
    detail.shapes.title.text = "Site Photos"
    detail.shapes.add_picture(io.BytesIO(jpeg_bytes(80, 60, (90, 160, 20))), Inches(1), Inches(2))
    detail.shapes.add_picture(io.BytesIO(png_bytes(50, 50, (240, 200, 0))), Inches(4), Inches(2))
    detail.notes_slide.notes_text_frame.text = "Mention the delayed delivery."

    hidden = deck.slides.add_slide(layout)
    hidden.shapes.title.text = "Backup Figures"
    hidden._element.set("show", "0")

    path = folder / "results.pptx"
    deck.save(path)
    return path


CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def chart_xml(title: str, categories: list[str], series: dict[str, list[float]]) -> bytes:
    """A clustered column chart with cached values, as Office writes it."""
    def cache(values, kind):
        points = "".join(f'<c:pt idx="{i}"><c:v>{v}</c:v></c:pt>' for i, v in enumerate(values))
        return f"<c:{kind}><c:ptCount val=\"{len(values)}\"/>{points}</c:{kind}>"

    sers = "".join(
        f'<c:ser><c:idx val="{i}"/><c:order val="{i}"/>'
        f"<c:tx><c:strRef><c:f>Sheet1!$B$1</c:f>{cache([name], 'strCache')}</c:strRef></c:tx>"
        f"<c:cat><c:strRef><c:f>Sheet1!$A$2</c:f>{cache(categories, 'strCache')}</c:strRef></c:cat>"
        f"<c:val><c:numRef><c:f>Sheet1!$B$2</c:f>{cache(values, 'numCache')}</c:numRef></c:val></c:ser>"
        for i, (name, values) in enumerate(series.items())
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<c:chartSpace xmlns:c="{CHART_NS}" xmlns:a="{DRAWING_NS}"><c:chart>'
        f"<c:title><c:tx><c:rich><a:p><a:r><a:t>{title}</a:t></a:r></a:p></c:rich></c:tx></c:title>"
        f'<c:plotArea><c:barChart><c:barDir val="col"/><c:grouping val="clustered"/>{sers}'
        f"</c:barChart></c:plotArea></c:chart></c:chartSpace>"
    ).encode()


BROKEN_CHART_XML = (
    f'<?xml version="1.0" encoding="UTF-8"?><c:chartSpace xmlns:c="{CHART_NS}" xmlns:a="{DRAWING_NS}">'
    f"<c:chart><c:plotArea><c:lineChart><c:ser><c:idx val=\"0\"/></c:ser></c:lineChart>"
    f"</c:plotArea></c:chart></c:chartSpace>"
).encode()

REVENUE_CHART_XML = chart_xml("Revenue by Quarter", ["Q1", "Q2"], {"2025": [10, 20], "2026": [12, 25]})


def build_word_with_charts(folder: Path) -> Path:
    """S-05 (charts): one readable chart and one whose data can't be read."""
    import docx
    from docx.opc.constants import RELATIONSHIP_TYPE
    from docx.opc.packuri import PackURI
    from docx.opc.part import Part
    from docx.oxml import parse_xml

    document = docx.Document()
    document.core_properties.created = FIXED_TIME
    document.core_properties.modified = FIXED_TIME
    document.add_heading("Dashboard", level=1)
    content_type = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"
    for number, (intro, blob) in enumerate(
        [("Revenue chart:", REVENUE_CHART_XML), ("Legacy chart:", BROKEN_CHART_XML)], start=1
    ):
        document.add_paragraph(intro)
        part = Part(PackURI(f"/word/charts/chart{number}.xml"), content_type, blob, document.part.package)
        rel_id = document.part.relate_to(part, RELATIONSHIP_TYPE.CHART)
        drawing = parse_xml(
            '<w:drawing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
            f'xmlns:a="{DRAWING_NS}" xmlns:c="{CHART_NS}" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<wp:inline><wp:extent cx="4572000" cy="2743200"/>'
            f'<wp:docPr id="{100 + number}" name="Chart {number}"/>'
            f'<a:graphic><a:graphicData uri="{CHART_NS}"><c:chart r:id="{rel_id}"/>'
            "</a:graphicData></a:graphic></wp:inline></w:drawing>"
        )
        document.add_paragraph().add_run()._r.append(drawing)
    document.add_paragraph("End of dashboard.")
    path = folder / "dashboard.docx"
    document.save(path)
    return path


def build_slides_with_chart(folder: Path) -> Path:
    """S-06 (charts): a column chart on the second slide, with text below it."""
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches

    deck = Presentation()
    deck.core_properties.created = FIXED_TIME
    deck.core_properties.modified = FIXED_TIME
    layout = deck.slide_layouts[5]
    deck.slides.add_slide(layout).shapes.title.text = "Metrics"
    slide = deck.slides.add_slide(layout)
    slide.shapes.title.text = "Revenue"
    data = CategoryChartData()
    data.categories = ["Q1", "Q2"]
    data.add_series("2025", (10, 20))
    data.add_series("2026", (12, 25))
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(1.5), Inches(6), Inches(4), data
    ).chart
    chart.has_title = True
    chart.chart_title.text_frame.text = "Revenue by Quarter"
    slide.shapes.add_textbox(Inches(1), Inches(6), Inches(6), Inches(1)).text_frame.text = "Source: finance"
    path = folder / "metrics.pptx"
    deck.save(path)
    return path


def build_workbook(folder: Path) -> Path:
    """S-07: a sheet with an image and a chart, a second visible sheet and a hidden sheet.

    openpyxl writes charts without cached values, as many tools do, so the
    chart's data has to be read from the cells it refers to.
    """
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.drawing.image import Image as SheetImage

    workbook = Workbook()
    workbook.properties.created = FIXED_TIME.replace(tzinfo=None)
    sales = workbook.active
    sales.title = "Sales & Costs"
    for row in [("Quarter", "2025", "2026"), ("Q1", 10, 12), ("Q2", 20, 25)]:
        sales.append(row)
    bars = BarChart()
    bars.title = "Revenue by Quarter"
    bars.add_data(Reference(sales, min_col=2, max_col=3, min_row=1, max_row=3), titles_from_data=True)
    bars.set_categories(Reference(sales, min_col=1, min_row=2, max_row=3))
    sales.add_chart(bars, "E2")
    sales.add_image(SheetImage(io.BytesIO(LOGO_PNG)), "E20")

    trend = workbook.create_sheet("Trend")
    for row in [("Month", "Visitors"), ("Jan", 100), ("Feb", 140)]:
        trend.append(row)
    line = LineChart()
    line.title = "Visitors"
    line.add_data(Reference(trend, min_col=2, min_row=1, max_row=3), titles_from_data=True)
    line.set_categories(Reference(trend, min_col=1, min_row=2, max_row=3))
    trend.add_chart(line, "D2")

    hidden = workbook.create_sheet("Hidden Notes")
    hidden["A1"] = "Internal only"
    hidden.sheet_state = "hidden"
    path = folder / "finance.xlsx"
    workbook.save(path)
    return path


def _replace_placeholder_with_emf(package: bytes, path: Path) -> Path:
    placeholder = png_bytes(16, 16, (1, 2, 3))
    members = {}
    with zipfile.ZipFile(io.BytesIO(package)) as source:
        for name in source.namelist():
            members[name] = source.read(name)
    media = next(name for name, data in members.items() if data == placeholder)
    emf_name = media.rsplit(".", 1)[0] + ".emf"
    members[emf_name] = emf_bytes()
    del members[media]
    old_target, new_target = media.split("word/", 1)[1], emf_name.split("word/", 1)[1]
    members["word/_rels/document.xml.rels"] = (
        members["word/_rels/document.xml.rels"].replace(old_target.encode(), new_target.encode())
    )
    members["[Content_Types].xml"] = members["[Content_Types].xml"].replace(
        b"<Default Extension=\"png\"",
        b"<Default Extension=\"emf\" ContentType=\"image/x-emf\"/><Default Extension=\"png\"",
    )
    return _write_zip(path, members)


def _pdf_bytes(pages: list[str]) -> bytes:
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, invariant=1)
    for text in pages:
        pdf.drawString(72, 720, text)
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def build_pdf_with_images(folder: Path) -> Path:
    """S-01: text and images on two pages, a logo on every page and a tiny icon."""
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    logo = ImageReader(io.BytesIO(LOGO_PNG))
    path = folder / "annual-report.pdf"
    pdf = canvas.Canvas(str(path), invariant=1)
    pdf.drawString(72, 720, "Annual report page one")
    pdf.drawImage(logo, 72, 600, 64, 32)
    pdf.drawImage(ImageReader(io.BytesIO(jpeg_bytes(80, 60, (90, 160, 20)))), 72, 450, 80, 60)
    pdf.drawImage(ImageReader(io.BytesIO(png_bytes(8, 8, (200, 0, 0)))), 200, 450, 8, 8)
    pdf.showPage()
    pdf.drawString(72, 720, "Annual report page two")
    pdf.drawImage(logo, 72, 600, 64, 32)
    pdf.showPage()
    pdf.save()
    return path


def build_scanned_pdf(folder: Path) -> Path:
    """S-03: pages that are only pictures, with no text layer."""
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    path = folder / "scanned.pdf"
    pdf = canvas.Canvas(str(path), invariant=1)
    pdf.drawImage(ImageReader(io.BytesIO(png_bytes(200, 260, (235, 235, 235)))), 0, 0, 595, 842)
    pdf.showPage()
    pdf.save()
    return path


def build_pdf_with_vector_chart(folder: Path) -> Path:
    """S-02: a bar chart drawn as vector shapes, so it isn't an Embedded Image."""
    from reportlab.pdfgen import canvas

    path = folder / "sales-chart.pdf"
    pdf = canvas.Canvas(str(path), invariant=1)
    pdf.drawString(72, 760, "Sales by quarter")
    for index, height in enumerate([120, 180, 90, 210]):
        pdf.setFillColorRGB(0.1, 0.4, 0.7)
        pdf.rect(100 + index * 60, 500, 40, height, fill=1, stroke=0)
    pdf.showPage()
    pdf.drawString(72, 760, "Notes on the chart")
    pdf.showPage()
    pdf.save()
    return path


JBIG2_PAYLOAD =b"\x97JB2\r\n\x1a\nnot a real JBIG2 stream"


def build_pdf_with_undecodable_image(folder: Path) -> Path:
    """A PDF whose image uses JBIG2, an encoding that can't be turned into an image file."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, NumberObject, StreamObject

    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(_pdf_bytes(["Faxed page"]))))
    image = StreamObject()
    image._data = JBIG2_PAYLOAD
    image.update({
        NameObject("/Type"): NameObject("/XObject"),
        NameObject("/Subtype"): NameObject("/Image"),
        NameObject("/Width"): NumberObject(8),
        NameObject("/Height"): NumberObject(8),
        NameObject("/BitsPerComponent"): NumberObject(1),
        NameObject("/ColorSpace"): NameObject("/DeviceGray"),
        NameObject("/Filter"): NameObject("/JBIG2Decode"),
    })
    page = writer.pages[0]
    resources = page["/Resources"].get_object()
    resources[NameObject("/XObject")] = DictionaryObject({NameObject("/Im9"): writer._add_object(image)})
    path = folder / "fax.pdf"
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def build_text_pdf(folder: Path) -> Path:
    path = folder / "brief.pdf"
    path.write_bytes(_pdf_bytes(["Project brief page one", "Project brief page two"]))
    return path


def build_encrypted_pdf(folder: Path) -> Path:
    """S-04: a PDF that needs a password to open."""
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(_pdf_bytes(["Confidential"]))))
    writer.encrypt(user_password="secret", owner_password="owner", algorithm="AES-128")
    path = folder / "locked.pdf"
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def build_encrypted_docx(folder: Path) -> Path:
    """A password-protected Word file: Office stores these as OLE containers, not ZIP."""
    path = folder / "locked.docx"
    cfb.write(path, {"EncryptionInfo": b"\x04\x00\x04\x00" + b"\0" * 60, "EncryptedPackage": b"\0" * 64})
    return path


def build_damaged_docx(folder: Path) -> Path:
    """S-15: claims to be a Word file but its package is corrupt."""
    path = folder / "broken.docx"
    path.write_bytes(b"PK\x03\x04 this is not really a Word document")
    return path


def build_xls(folder: Path) -> Path:
    """S-08: a legacy binary Excel workbook."""
    import xlwt

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Budget")
    for row, values in enumerate([("Item", "Cost"), ("Laptops", 1200), ("Desks", 300)]):
        for column, value in enumerate(values):
            sheet.write(row, column, value)
    path = folder / "legacy.xls"
    workbook.save(str(path))
    return path


def build_msg(folder: Path) -> Path:
    """S-12: an Outlook message with one attachment."""
    utf16 = lambda text: text.encode("utf-16-le")  # noqa: E731
    attachment = "__attach_version1.0_#00000000"
    path = folder / "budget-email.msg"
    cfb.write(path, {
        "__substg1.0_0037001F": utf16("Budget review"),
        "__substg1.0_0C1F001F": utf16("ops@example.com"),
        "__substg1.0_0E04001F": utf16("Finance Team"),
        "__substg1.0_1000001F": utf16("Please review the attached budget."),
        f"{attachment}/__substg1.0_3707001F": utf16("budget.csv"),
        f"{attachment}/__substg1.0_37010102": CSV_TEXT.encode(),
    })
    return path


def build_zip(folder: Path) -> Path:
    """S-13: an archive holding mixed files."""
    return _write_zip(folder / "bundle.zip", {
        "sales.csv": CSV_TEXT.encode(),
        "notes/project.json": JSON_TEXT.encode(),
    })


EPUB_CONTAINER = (
    '<?xml version="1.0"?><container version="1.0" '
    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
    '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
    "</rootfiles></container>"
)


def _epub_package(manifest: str, title: str) -> str:
    return (
        '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
        f'<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{title}</dc:title>'
        "<dc:language>en</dc:language></metadata>"
        f"<manifest>{manifest}</manifest>"
        '<spine><itemref idref="chapter1"/></spine></package>'
    )


def build_text_epub(folder: Path) -> Path:
    chapter = (
        '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml"><body>'
        "<h1>Chapter One</h1><p>It was a quiet quarter.</p></body></html>"
    )
    manifest = '<item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>'
    return _write_zip(folder / "handbook.epub", {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": EPUB_CONTAINER.encode(),
        "OEBPS/content.opf": _epub_package(manifest, "Team Handbook").encode(),
        "OEBPS/chapter1.xhtml": chapter.encode(),
    })


def build_name_collision(folder: Path) -> list[Path]:
    """S-14: report.pdf and report.docx side by side."""
    pdf = folder / "report.pdf"
    pdf.write_bytes(_pdf_bytes(["Report as PDF"]))
    docx = build_word_with_images(folder).rename(folder / "report.docx")
    return [pdf, docx]


REMOTE_IMAGE_URL = "https://example.com/logo.png"
CHART_PNG = png_bytes(120, 80, (60, 60, 200))


def build_html_with_images(folder: Path) -> Path:
    """S-09: a web page with a local image (name with a space) and a remote one."""
    images = folder / "page files"
    images.mkdir(exist_ok=True)
    (images / "sales chart.png").write_bytes(CHART_PNG)
    html = (
        "<html><body><h1>Sales Page</h1><p>Our chart:</p>"
        '<img src="page%20files/sales%20chart.png" alt="Sales chart">'
        f'<p>Partner logo:</p><img src="{REMOTE_IMAGE_URL}" alt="Partner">'
        "</body></html>"
    )
    return _write_text(folder / "page.html", html)


def build_epub_with_images(folder: Path) -> Path:
    """S-10: an e-book whose chapter shows a bundled image."""
    chapter = (
        '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml"><body>'
        '<h1>Chapter One</h1><p>The map:</p><img src="../images/map.png" alt="Map"/></body></html>'
    )
    manifest = (
        '<item id="chapter1" href="text/chapter1.xhtml" media-type="application/xhtml+xml"/>'
        '<item id="map" href="images/map.png" media-type="image/png"/>'
    )
    return _write_zip(folder / "atlas.epub", {
        "mimetype": b"application/epub+zip",
        "META-INF/container.xml": EPUB_CONTAINER.encode(),
        "OEBPS/content.opf": _epub_package(manifest, "Atlas").encode(),
        "OEBPS/text/chapter1.xhtml": chapter.encode(),
        "OEBPS/images/map.png": CHART_PNG,
    })


def build_folder_tree(folder: Path) -> Path:
    """S-16: a Target folder with nested, hidden, unsupported and awkwardly named entries."""
    root = folder / "library"
    reports = root / "reports"
    deep = reports / "deep"
    awkward = root / "Q3 résumé files"
    hidden = root / ".hidden"
    for path in (deep, awkward, hidden):
        path.mkdir(parents=True, exist_ok=True)
    build_csv(root)
    _write_text(root / "notes.txt", "Not a Supported Format.\n")
    build_text_docx(reports)
    build_json(deep)
    build_xml(awkward)
    build_csv(hidden)
    return root


class _TaggedPdf:
    """Writes a Tagged PDF from raw PDF objects, since reportlab can't write tags.

    Content is drawn as marked-content runs; `element` builds the structure tree
    from those runs, other elements and link annotations.
    """

    WIDTH, HEIGHT = 595, 842

    def __init__(self, pages: int):
        from pypdf import PdfWriter

        self.writer = PdfWriter()
        self.pages = [self.writer.add_blank_page(self.WIDTH, self.HEIGHT) for _ in range(pages)]
        self.operators: list[list[str]] = [[] for _ in range(pages)]
        self.images: list[dict] = [{} for _ in range(pages)]
        self.annotations: list[list] = [[] for _ in range(pages)]
        self.marked: list[list] = [[] for _ in range(pages)]  # element owning each MCID, per page
        self._pending: list[tuple] = []  # (element, kid) pairs resolved on save
        self.parent_tree: list = []

    def _run(self, page: int, tag: str, operators: list[str]):
        mcid = len(self.marked[page - 1])
        self.marked[page - 1].append(None)
        self.operators[page - 1] += [f"/{tag} <</MCID {mcid}>> BDC", *operators, "EMC"]
        return ("mcr", page, mcid)

    @staticmethod
    def _text_operators(x: float, y: float, text: str, size: float, bold: bool) -> list[str]:
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return ["BT", f"/{'F2' if bold else 'F1'} {size} Tf", f"{x} {y} Td", f"({escaped}) Tj", "ET"]

    def text(self, page: int, x: float, y: float, text: str, size: float = 11, bold: bool = False, tag: str = "P"):
        return self._run(page, tag, self._text_operators(x, y, text, size, bold))

    def artifact(self, page: int, x: float, y: float, text: str, size: float = 9):
        self.operators[page - 1] += ["/Artifact BMC", *self._text_operators(x, y, text, size, False), "EMC"]

    def drawing(self, page: int, operators: list[str]):
        return self._run(page, "Figure", ["q", *operators, "Q"])

    def image(self, page: int, x: float, y: float, width: float, height: float, png: bytes, artifact: bool = False):
        """Draw an image: as tagged content, or as Page Furniture outside the tags when `artifact`."""
        import zlib

        from PIL import Image
        from pypdf.generic import NameObject, NumberObject, StreamObject

        with Image.open(io.BytesIO(png)) as picture:
            rgb = picture.convert("RGB")
        stream = StreamObject()
        stream._data = zlib.compress(rgb.tobytes())
        stream.update({
            NameObject("/Type"): NameObject("/XObject"), NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(rgb.width), NameObject("/Height"): NumberObject(rgb.height),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8), NameObject("/Filter"): NameObject("/FlateDecode"),
        })
        name = f"Im{len(self.images[page - 1]) + 1}"
        self.images[page - 1][name] = self.writer._add_object(stream)
        operators = ["q", f"{width} 0 0 {height} {x} {y} cm", f"/{name} Do", "Q"]
        if artifact:
            self.operators[page - 1] += ["/Artifact BMC", *operators, "EMC"]
            return None
        return self._run(page, "Figure", operators)

    def link(self, page: int, rect: tuple, uri: str | None = None, to_page: int | None = None):
        from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject, NameObject, NullObject,
                                   TextStringObject)

        annotation = DictionaryObject({
            NameObject("/Type"): NameObject("/Annot"), NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject(FloatObject(v) for v in rect),
            NameObject("/Border"): ArrayObject([FloatObject(0)] * 3),
        })
        if uri:
            annotation[NameObject("/A")] = DictionaryObject({
                NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject(uri)})
        else:
            annotation[NameObject("/Dest")] = ArrayObject([
                self.pages[to_page - 1].indirect_reference, NameObject("/XYZ"), NullObject(), NullObject(),
                NullObject()])
        reference = self.writer._add_object(annotation)
        self.annotations[page - 1].append(reference)
        return ("objr", page, reference)

    def element(self, tag: str, *kids, alt: str | None = None, bbox: tuple | None = None,
                rows: int | None = None, columns: int | None = None):
        """A structure element; `rows` and `columns` are a table cell's RowSpan and ColSpan."""
        from pypdf.generic import (ArrayObject, DictionaryObject, FloatObject, NameObject, NumberObject,
                                   TextStringObject)

        element = DictionaryObject({NameObject("/Type"): NameObject("/StructElem"), NameObject("/S"): NameObject(f"/{tag}")})
        if alt is not None:
            element[NameObject("/Alt")] = TextStringObject(alt)
        if bbox is not None:
            element[NameObject("/A")] = DictionaryObject({
                NameObject("/O"): NameObject("/Layout"), NameObject("/BBox"): ArrayObject(FloatObject(v) for v in bbox)})
        if rows or columns:
            element[NameObject("/A")] = DictionaryObject({
                NameObject("/O"): NameObject("/Table"),
                **({NameObject("/RowSpan"): NumberObject(rows)} if rows else {}),
                **({NameObject("/ColSpan"): NumberObject(columns)} if columns else {})})
        reference = self.writer._add_object(element)
        for kid in kids:
            self._pending.append((reference, kid))
        return ("elem", reference)

    def save(self, path: Path, *top) -> Path:
        from pypdf.generic import (ArrayObject, BooleanObject, DictionaryObject, NameObject, NumberObject,
                                   StreamObject)

        document = self.element("Document", *top)
        kids_of: dict[int, list] = {}
        for parent, kid in self._pending:
            parent_object = parent.get_object()
            if kid[0] == "elem":
                kid[1].get_object()[NameObject("/P")] = parent
                kids_of.setdefault(id(parent_object), []).append(kid[1])
            elif kid[0] == "mcr":
                _, page, mcid = kid
                self.marked[page - 1][mcid] = parent
                kids_of.setdefault(id(parent_object), []).append(DictionaryObject({
                    NameObject("/Type"): NameObject("/MCR"), NameObject("/MCID"): NumberObject(mcid),
                    NameObject("/Pg"): self.pages[page - 1].indirect_reference}))
            else:
                _, page, annotation = kid
                key = len(self.pages) + len(self.parent_tree)
                annotation.get_object()[NameObject("/StructParent")] = NumberObject(key)
                self.parent_tree.append((key, parent))
                kids_of.setdefault(id(parent_object), []).append(DictionaryObject({
                    NameObject("/Type"): NameObject("/OBJR"), NameObject("/Obj"): annotation,
                    NameObject("/Pg"): self.pages[page - 1].indirect_reference}))
            parent_object[NameObject("/K")] = ArrayObject(kids_of[id(parent_object)])
        root = DictionaryObject({NameObject("/Type"): NameObject("/StructTreeRoot")})
        root_reference = self.writer._add_object(root)
        document[1].get_object()[NameObject("/P")] = root_reference
        root[NameObject("/K")] = ArrayObject([document[1]])
        numbers = ArrayObject()
        fonts = DictionaryObject({
            NameObject(f"/{name}"): DictionaryObject({
                NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject(f"/{font}"), NameObject("/Encoding"): NameObject("/WinAnsiEncoding")})
            for name, font in (("F1", "Helvetica"), ("F2", "Helvetica-Bold"))})
        for index, page in enumerate(self.pages):
            content = StreamObject()
            content._data = "\n".join(self.operators[index]).encode("latin-1")
            page[NameObject("/Contents")] = self.writer._add_object(content)
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): fonts,
                NameObject("/XObject"): DictionaryObject(
                    {NameObject(f"/{name}"): ref for name, ref in self.images[index].items()})})
            page[NameObject("/StructParents")] = NumberObject(index)
            if self.annotations[index]:
                page[NameObject("/Annots")] = ArrayObject(self.annotations[index])
            numbers += [NumberObject(index), ArrayObject(self.marked[index])]
        for key, parent in self.parent_tree:
            numbers += [NumberObject(key), parent]
        root[NameObject("/ParentTree")] = DictionaryObject({NameObject("/Nums"): numbers})
        root[NameObject("/ParentTreeNextKey")] = NumberObject(len(self.pages) + len(self.parent_tree))
        catalog = self.writer._root_object
        catalog[NameObject("/StructTreeRoot")] = root_reference
        catalog[NameObject("/MarkInfo")] = DictionaryObject({NameObject("/Marked"): BooleanObject(True)})
        with path.open("wb") as stream:
            self.writer.write(stream)
        return path


TAGGED_LOGO_PNG = png_bytes(48, 24, (160, 40, 40))


def build_tagged_pdf(folder: Path) -> Path:
    """S-17: a three-page Tagged PDF with Page Furniture, headings, lists, a table and figures."""
    pdf = _TaggedPdf(3)
    e, t = pdf.element, pdf.text
    for page in (1, 2, 3):
        pdf.artifact(page, 72, 815, "Example Club - Members only")
        pdf.artifact(page, 280, 30, f"Page {page} of 3")
        pdf.image(page, 480, 805, 48, 24, LOGO_PNG, artifact=True)

    # Page 1: title, contents, a numbered list and a paragraph with links.
    title = e("H1", t(1, 72, 760, "Club handbook", 20, True))
    # The last two entries' titles are tagged only as a paragraph and a one-cell table header row.
    contents = e("TOC",
                 e("TOCI", t(1, 72, 724, "Joining .................................. 1")),
                 e("TOCI", t(1, 72, 712, "Facilities .............................. 2")),
                 e("TOCI", t(1, 72, 700, "Questions ............................... 3")),
                 e("TOCI", t(1, 90, 688, "Room bookings ....................... 3")),
                 e("TOCI", t(1, 90, 676, "Cancellations ........................ 3")))
    leave = e("H2", t(1, 72, 670, "Joining", 14, True))
    steps = e("L",
              e("LI", e("Lbl", t(1, 72, 645, "1.")), e("LBody", t(1, 90, 645, "Fill in the form at the desk."))),
              e("LI", e("Lbl", t(1, 72, 630, "2.")), e("LBody", t(1, 90, 630, "A volunteer checks it."))))
    from reportlab.pdfbase.pdfmetrics import stringWidth

    runs = ["Forms are on the ", "website", ", and facilities are covered on ", "page 2", "."]
    x = [72.0]
    for run in runs:
        x.append(x[-1] + stringWidth(run, "Helvetica", 11))
    forms = e("P", t(1, x[0], 600, runs[0]),
              e("Link", t(1, x[1], 600, runs[1]), pdf.link(1, (x[1], 597, x[2], 611), uri="https://example.com/forms")),
              t(1, x[2], 600, runs[2]),
              e("Link", t(1, x[3], 600, runs[3]), pdf.link(1, (x[3], 597, x[4], 611), to_page=2)),
              t(1, x[4], 600, runs[4]))
    empty_heading = e("H2", t(1, 72, 580, " "))
    # A bold label that happens to match a contents title belonging much later in the document.
    early_label = e("P", t(1, 72, 560, "Room bookings", bold=True))

    # Page 2: benefits list, a vector chart, and a table that runs onto page 3.
    benefits = e("H2", t(2, 72, 760, "Facilities", 14, True))
    cover = e("L",
              e("LI", e("Lbl", t(2, 72, 735, "\x95")), e("LBody", t(2, 90, 735, "Library"))),
              e("LI", e("Lbl", t(2, 72, 720, "\x95")), e("LBody", t(2, 90, 720, "Workshop"),
                e("L", e("LI", e("Lbl", t(2, 100, 705, "\x95")), e("LBody", t(2, 116, 705, "Open on Saturdays")))))),
              e("LI", e("Lbl", t(2, 72, 690, "\x95")),
                e("LBody", e("Link", t(2, 90, 690, "Booking page"),
                             pdf.link(2, (90, 687, 160, 701), uri="https://example.com/booking")))))
    bars = [f"0.1 0.4 0.7 rg {120 + i * 50} 520 30 {h} re f" for i, h in enumerate((60, 110, 80, 140))]
    chart = e("Figure", pdf.drawing(2, ["0 0 0 RG 110 515 m 330 515 l S", *bars]), alt="Visits by quarter",
              bbox=(100, 505, 340, 670))
    header = e("TR", e("TH", t(2, 72, 470, "Room", bold=True)), e("TH", t(2, 250, 470, "Seats", bold=True)))
    basic = e("TR", e("TD", t(2, 72, 450, "Hall")), e("TD", t(2, 250, 450, "80")))
    premium = e("TR", e("TD", t(3, 72, 760, "Studio")), e("TD", t(3, 250, 760, "12")))
    table = e("Table", e("THead", header), e("TBody", basic, premium))

    # Page 3: a closing paragraph, a single-image figure and a text box.
    deadline = e("P", t(3, 72, 720, "Book rooms a week ahead."))
    logo = e("Figure", pdf.image(3, 72, 640, 96, 48, TAGGED_LOGO_PNG), alt="Club logo")
    box = e("Figure", pdf.drawing(3, ["0 0 0 RG 70 560 300 40 re S"]),
            e("P", t(3, 80, 575, "Remember to sign the visitor book.")))
    annotated = e("Figure", pdf.image(3, 72, 400, 120, 90, png_bytes(40, 30, (230, 230, 230))),
                  pdf.drawing(3, ["1 0 0 RG 2 w 80 410 m 180 480 l S"]), alt="Annotated sign-up form")
    tick = e("Figure", pdf.drawing(3, ["0 0.5 0 rg 72 360 8 8 re f"]), alt="Tick")
    # A diagram of boxes joined by a curved arrow, with its label tagged as a separate paragraph.
    diagram = e("Figure", pdf.drawing(3, ["0 0 0 RG 72 200 80 40 re S", "300 200 80 40 re S",
                                          "152 220 m 200 300 260 300 300 220 c S"]), alt="Booking flow")
    label = e("P", t(3, 110, 215, "Member sends the booking to the desk"))
    # Section titles the author styled but didn't tag as headings, and a bold label that isn't a title.
    questions = e("P", t(3, 72, 170, "Questions", 14, True))
    tip = e("P", t(3, 72, 155, "Tip", bold=True))
    bookings = e("Table",
                 e("TR", e("TH", t(3, 72, 135, "Room bookings", bold=True))),
                 e("TR", e("TH", t(3, 72, 120, "Day", bold=True)), e("TH", t(3, 200, 120, "Slots", bold=True))),
                 e("TR", e("TD", t(3, 72, 105, "Monday")), e("TD", t(3, 200, 105, "4"))),
                 # A full-width row whose cell opens with the next section's title.
                 e("TR", e("TD", e("P", t(3, 72, 90, "Cancellations", bold=True)),
                           e("P", t(3, 72, 78, "Cancel a day ahead.")))))
    return pdf.save(folder / "handbook.pdf", title, contents, leave, steps, forms, empty_heading, early_label, benefits, cover,
                    chart, table, deadline, logo, box, annotated, tick, diagram, label, questions, tip, bookings)


def build_tagged_pdf_out_of_page_order(folder: Path) -> Path:
    """A Tagged PDF whose reading order jumps ahead and back, as Word's text boxes do.

    Page 2 holds only Page Furniture, so no block starts on it.
    """
    pdf = _TaggedPdf(4)
    e, t = pdf.element, pdf.text
    for page in (1, 2, 3, 4):
        pdf.artifact(page, 280, 30, f"Page {page}")
    return pdf.save(folder / "leaflet.pdf",
                    e("P", t(1, 72, 760, "Opening paragraph.")),
                    e("P", t(3, 72, 760, "Callout drawn on page three.")),
                    e("P", t(1, 72, 700, "Rest of page one.")),
                    e("P", t(4, 72, 760, "Closing paragraph.")))


def build_tagged_pdf_with_merged_cells(folder: Path) -> Path:
    """A Tagged PDF table with a header cell merged across two columns and a cell merged down two rows."""
    pdf = _TaggedPdf(1)
    e, t = pdf.element, pdf.text
    table = e("Table",
              e("TR", e("TH", t(1, 72, 760, "Room", bold=True)),
                e("TH", t(1, 200, 760, "Equipment", bold=True), columns=2)),
              e("TR", e("TD", t(1, 72, 740, "A"), rows=2), e("TD", t(1, 200, 740, "Projector")),
                e("TD", t(1, 330, 740, "Yes"))),
              e("TR", e("TD", t(1, 200, 720, "Screen")), e("TD", t(1, 330, 720, "No"))))
    return pdf.save(folder / "rooms.pdf", table)


def build_untagged_pdf(folder: Path) -> Path:
    """S-18: an untagged PDF with Page Furniture, bold body-size section titles and a bordered table.

    The table runs over pages 2-4 and repeats its header row at the same height
    on each, as Page Furniture would.
    """
    from reportlab.pdfgen import canvas

    path = folder / "project-plan.pdf"
    pdf = canvas.Canvas(str(path), invariant=1)

    def furniture(number: int) -> None:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(250, 810, "CONFIDENTIAL DRAFT")
        pdf.drawString(230, 30, f"Part 2 - Appendix A - {number}")

    def line(x: float, y: float, text: str, font: str = "Helvetica", size: float = 11) -> None:
        pdf.setFont(font, size)
        pdf.drawString(x, y, text)

    furniture(1)
    line(72, 740, "PROJECT PLAN", "Helvetica-Bold", 16)
    line(72, 700, "BACKGROUND", "Helvetica-Bold")
    line(72, 680, "1. This plan describes the work on the new club")
    line(72, 666, "website.")
    line(72, 630, "SCHEDULE", "Helvetica-Bold", 11.4)  # a touch larger, as some exports set it
    line(72, 610, "2. The team will meet every week.")
    line(72, 580, "The schedule is in the table that follows.")
    # A table whose borders split each column in two, putting header and value in different halves.
    pdf.grid([72, 140, 250, 280, 400], [520, 500, 480])
    line(146, 506, "Item", "Helvetica-Bold")
    line(286, 506, "Cost", "Helvetica-Bold")
    line(78, 486, "Laptop")
    line(256, 486, "900")
    # A diagram: two filled boxes joined by a curved arrow, with steps between them and labels inside.
    pdf.setFillColorRGB(0.2, 0.4, 0.8)
    pdf.rect(72, 330, 100, 50, fill=1, stroke=0)
    pdf.rect(300, 330, 100, 50, fill=1, stroke=0)
    for step in range(6):
        pdf.rect(180 + step * 20, 350, 8, 8, fill=1, stroke=0)
    arrow = pdf.beginPath()
    arrow.moveTo(172, 380)
    arrow.curveTo(220, 430, 260, 430, 300, 380)
    pdf.drawPath(arrow, stroke=1, fill=0)
    head = pdf.beginPath()
    head.moveTo(300, 380)
    head.lineTo(290, 392)
    head.lineTo(286, 380)
    head.close()
    pdf.drawPath(head, stroke=0, fill=1)
    pdf.setFillColorRGB(1, 1, 1)
    line(90, 350, "Draft site")
    line(320, 350, "Live site")
    pdf.setFillColorRGB(0, 0, 0)
    line(72, 300, "The release process is shown above.")
    # Not a diagram: a borderless table whose rows are told apart by shaded bands, and an underline.
    for row in range(12):
        shade = 0.85 if row % 2 else 0.93
        pdf.setFillColorRGB(shade, shade, shade)
        pdf.rect(72, 262 - row * 14, 300, 14, fill=1, stroke=0)
        pdf.setFillColorRGB(0, 0, 0)
        line(78, 266 - row * 14, f"Week {row + 1} planning meeting")
        line(300, 266 - row * 14, "Room B")
    pdf.line(72, 80, 200, 80)
    pdf.showPage()
    for number, (serial, activity) in enumerate([("1", "Draft"), ("2", "Review"),
                                                 ("3", "Publish")], start=2):
        furniture(number)
        pdf.grid([72, 140, 400], [780, 760, 740])
        line(78, 766, "No.", "Helvetica-Bold")
        line(146, 766, "Task", "Helvetica-Bold")
        line(78, 746, serial)
        line(146, 746, activity)
        pdf.showPage()
    pdf.save()
    return path


BUILDERS = [
    build_csv, build_json, build_xml, build_text_docx, build_text_pdf, build_encrypted_pdf,
    build_encrypted_docx, build_damaged_docx, build_xls, build_msg, build_zip, build_text_epub,
    build_pdf_with_images, build_pdf_with_vector_chart, build_scanned_pdf,
    build_pdf_with_undecodable_image, build_tagged_pdf, build_untagged_pdf, build_word_with_images, build_word_with_charts,
    build_slides, build_slides_with_chart, build_workbook, build_html_with_images,
    build_epub_with_images,
]


def build_full_library(folder: Path) -> Path:
    """S-16 in full: every sample spread over a folder tree, for the acceptance run."""
    root = build_folder_tree(folder)
    for index, build in enumerate(BUILDERS):
        destination = root / ("documents" if index % 2 else "archive 2026") / build.__name__
        destination.mkdir(parents=True, exist_ok=True)
        build(destination)
    collision = root / "collision"
    collision.mkdir()
    build_name_collision(collision)
    return root


def build_all(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    built = [build(folder) for build in BUILDERS]
    built.append(build_folder_tree(folder))
    return built


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python tests/sample_set.py <output-folder>")
    for built in build_all(Path(sys.argv[1])):
        print(built)
