"""tools/check_numbering.py: the converter's Word labels against a reference rendering."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

import sample_set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import check_numbering  # noqa: E402

OUTLINE = """\
    1 Planting
        1.1 Soil
            1.1.1 Beds are dug in spring.
A note between clauses.
            1.1.2 Compost is added each autumn.
Bed sizes
        1.2 Seeds
    2 Harvest
        2.1 Picking
"""


def _check(*args) -> tuple[int, str]:
    stdout = io.StringIO()
    return check_numbering.main([str(a) for a in args], stdout), stdout.getvalue()


def _reference(tmp_path, text: str, encoding: str = "utf-8") -> Path:
    path = tmp_path / "reference.txt"
    path.write_bytes(text.encode(encoding))
    return path


def test_labels_matching_the_reference_pass(tmp_path):
    source = sample_set.build_inherited_outline_styles_word(tmp_path)

    exit_code, output = _check(source, "--reference", _reference(tmp_path, OUTLINE))

    assert exit_code == 0
    assert "outline.docx against reference.txt: 7 labels checked, 0 finding(s)" in output


def test_a_label_the_reference_shows_differently_is_reported(tmp_path):
    source = sample_set.build_inherited_outline_styles_word(tmp_path)
    reference = _reference(tmp_path, OUTLINE.replace("1.2 Seeds", "1.3 Seeds"))

    exit_code, output = _check(source, "--reference", reference)

    assert exit_code == 1
    assert "paragraph 7: converter '1.2', reference '1.3': Seeds" in output  # the table cell is paragraph 6


def test_the_same_text_elsewhere_under_another_label_is_not_a_finding(tmp_path):
    source = sample_set.build_inherited_outline_styles_word(tmp_path)
    reference = _reference(tmp_path, OUTLINE + "    7 Planting\n        7.4 Seeds\n")

    exit_code, _ = _check(source, "--reference", reference)

    assert exit_code == 0


def test_numbering_the_converter_missed_is_reported():
    paragraphs = [("1", "Planting"), ("", "Beds are dug in spring.")]
    lines = ["1 Planting", "1.1 Beds are dug in spring."]

    findings = check_numbering.check(paragraphs, lines)

    assert [(f.converter_label, f.reference_labels) for f in findings] == [("", ["1.1"])]


def test_table_cells_and_bullets_are_not_mistaken_for_labels():
    paragraphs = [("", "Bed number"), ("", "Beds are dug in spring."), ("", "Water the seedlings daily.")]
    lines = check_numbering._text_lines("4\tBed number\tBeds are dug in spring.\n• Water the seedlings daily.\n")

    assert check_numbering.check(paragraphs, lines) == []


def test_without_a_reference_it_renders_with_libreoffice(tmp_path):
    source = sample_set.build_inherited_outline_styles_word(tmp_path)
    script = Path(__file__).with_name("fake_soffice.py")
    if sys.platform == "win32":
        soffice = tmp_path / "soffice.cmd"
        soffice.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
    else:
        soffice = tmp_path / "soffice"
        soffice.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
        soffice.chmod(0o755)
    rendered = tmp_path / "rendered.txt"
    rendered.write_text("Café notes\n" + OUTLINE, encoding="utf-8")  # the stand-in writes cp1252
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("FAKE_SOFFICE_TEXT", str(rendered))
        exit_code, output = _check(source, "--libreoffice", soffice)

    assert exit_code == 0, output
    assert "against LibreOffice: 7 labels checked, 0 finding(s)" in output


@pytest.mark.skipif(check_numbering.find_libreoffice() is None, reason="LibreOffice is not installed")
@pytest.mark.parametrize("build", [
    sample_set.build_numbered_word,
    sample_set.build_inherited_outline_styles_word,
    sample_set.build_outline_through_numbering_style_word,
    sample_set.build_chapter_clauses_word,
    sample_set.build_list_starting_below_its_top_level_word,
    sample_set.build_long_lettered_list_word,
])
def test_the_samples_match_real_libreoffice(tmp_path, build):
    exit_code, output = _check(build(tmp_path))

    assert exit_code == 0, output


def test_table_row_numbers_in_a_pdf_are_not_taken_for_missed_numbering():
    paragraphs = [("", "Beds are dug in spring."), ("", "Compost is added each autumn.")]
    lines = ["12 Beds are dug in spring.", "86. Plot B Compost is added each autumn."]

    assert check_numbering.check(paragraphs, lines, multi_level_only=True) == []
    assert [f.reference_labels for f in check_numbering.check(paragraphs, lines)] == [["12"]]


def test_text_stops_at_a_footnote_reference_whose_number_renderers_print():
    from lxml import etree

    w = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    paragraph = etree.fromstring(
        f'<w:p {w}><w:r><w:t xml:space="preserve">⟦label:2.1⟧ Seeds are sown</w:t></w:r>'
        f'<w:r><w:footnoteReference w:id="1"/></w:r><w:r><w:t> in rows.</w:t></w:r></w:p>'
    )

    assert check_numbering._label_and_text(paragraph) == ("2.1", " Seeds are sown")
