"""Numbered lists and headings keep their real labels, e.g. 1.2.4.a."""

from __future__ import annotations

import re

import sample_set


def _word(run, tmp_path):
    source = sample_set.build_numbered_word(tmp_path)
    run(source, "--no-front-matter")
    return (tmp_path / "contract.md").read_text(encoding="utf-8")


def _lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def test_word_legal_numbering_keeps_its_labels(run, tmp_path):
    lines = _lines(_word(run, tmp_path))

    expected = [
        "1\\. Scope", "1.1. Definitions", "1.2. Services", "1.2.1. Delivery", "1.2.2. Support",
        "1.2.3. Hours", "1.2.4. Response times", "1.2.4.a Priority 1", "1.2.4.b Priority 2", "2\\. Payment",
    ]
    start = lines.index(expected[0])
    assert lines[start:start + len(expected)] == expected


def test_word_numbered_headings_keep_their_numbers(run, tmp_path):
    text = _word(run, tmp_path)

    assert "# 1 Introduction" in text
    assert "## 1.1 Purpose" in text
    assert "# 2 Terms" in text
    assert "# 3 Schedules" in text


def test_word_roman_numerals_restarts_and_bullets(run, tmp_path):
    lines = _lines(_word(run, tmp_path))

    assert ["I. Pricing", "(i) Discounts", "(ii) Rebates", "II. Penalties"] == lines[
        lines.index("I. Pricing"):lines.index("I. Pricing") + 4
    ]
    assert "5\\. Fifth step" in lines
    assert "6\\. Sixth step" in lines
    assert any(re.fullmatch(r"[*-] Apples", line) for line in lines)


def test_clause_styles_are_numbered_once_with_their_real_labels(run, tmp_path):
    source = sample_set.build_clause_styled_word(tmp_path)

    run(source, "--no-front-matter")

    lines = _lines((tmp_path / "clauses.md").read_text(encoding="utf-8"))
    assert lines == [
        "17 Warranties", "17.5 Scope", "17.5.1 Hardware", "17.5.2 Software", "18 Liability",
    ]


def test_styles_linked_only_from_the_list_side_are_numbered(run, tmp_path):
    source = sample_set.build_clause_styled_word(tmp_path, styles_name_the_list=False)

    run(source, "--no-front-matter")

    lines = _lines((tmp_path / "clauses.md").read_text(encoding="utf-8"))
    assert lines == [
        "17 Warranties", "17.5 Scope", "17.5.1 Hardware", "17.5.2 Software", "18 Liability",
    ]


def test_hidden_and_empty_numbered_paragraphs_leave_no_stray_labels(run, tmp_path):
    source = sample_set.build_chapter_clauses_word(tmp_path)

    run(source, "--no-front-matter")

    lines = _lines((tmp_path / "specification.md").read_text(encoding="utf-8"))
    chapter_three = lines[lines.index("3\\. **HARVEST**"):]
    assert chapter_three == [
        "3\\. **HARVEST**",
        "3.1 **Garden layout** follows the plan in this chapter.",
        # 3.2 is the empty clause: counted, but there's nothing to show.
        "3.3 **Watering** happens twice a week.",
    ]
    assert not any(re.fullmatch(r"[\d.\\]+", line) for line in lines)


_OUTLINE = [
    "1 Planting", "1.1 Soil", "1.1.1 Beds are dug in spring.", "A note between clauses.",
    "1.1.2 Compost is added each autumn.", "1.2 Seeds", "2 Harvest", "2.1 Picking",
]


def _outline_lines(run, source):
    run(source, "--no-front-matter")
    lines = _lines(source.with_suffix(".md").read_text(encoding="utf-8"))
    return [line for line in lines if not line.startswith("|")]  # the interrupting table


def test_items_before_the_first_top_level_item_count_it_as_used(run, tmp_path):
    source = sample_set.build_list_starting_below_its_top_level_word(tmp_path)

    run(source, "--no-front-matter")

    lines = _lines((tmp_path / "early.md").read_text(encoding="utf-8"))
    assert lines == [
        "1.1 Tools 30", "1.2 Gloves 30", "2 Sowing 30", "2.1 Seeds 30", "3 Weeding 30",
        "3.1 Tools 31", "3.2 Gloves 31", "4 Sowing 31", "4.1 Seeds 31", "5 Weeding 31",
    ]


def test_letters_after_z_repeat_as_word_shows_them(run, tmp_path):
    source = sample_set.build_long_lettered_list_word(tmp_path)

    run(source, "--no-front-matter")

    lines = _lines((tmp_path / "lettered.md").read_text(encoding="utf-8"))
    for expected in ["(z) Item 26", "(aa) Item 27", "(bb) Item 28", "(zz) Item 52", "(aaa) Item 53"]:
        assert expected in lines


def test_styles_that_set_only_their_level_inherit_the_list_from_their_base_style(run, tmp_path):
    assert _outline_lines(run, sample_set.build_inherited_outline_styles_word(tmp_path)) == _OUTLINE


def test_lists_reaching_their_outline_through_a_numbering_style_keep_their_labels(run, tmp_path):
    assert _outline_lines(run, sample_set.build_outline_through_numbering_style_word(tmp_path)) == _OUTLINE


def test_labels_that_look_like_markdown_list_numbers_are_kept_literal(run, tmp_path):
    lines = _lines(_word(run, tmp_path))

    # "2. Payment" would be a Markdown list item that viewers renumber; "2\." is shown as written.
    assert "2\\. Payment" in lines
    assert "5\\. Fifth step" in lines
    assert "1.2.4.a Priority 1" in lines  # can't be read as a list, so left alone


def test_pdf_clause_labels_stay_with_their_text_in_order(run, tmp_path):
    source = sample_set.build_numbered_pdf(tmp_path)

    run(source, "--no-front-matter")

    lines = _lines((tmp_path / "contract.md").read_text(encoding="utf-8"))
    expected = [
        "1\\. Scope", "1.1. Definitions", "1.2. Services", "1.2.4. Response times",
        "1.2.4.a Priority 1", "1.2.4.b Priority 2", "2\\. Payment",
    ]
    start = lines.index(expected[0])
    assert lines[start:start + len(expected)] == expected


def test_pdf_numbered_lines_are_separate_paragraphs_but_wrapped_lines_stay_together(run, tmp_path):
    source = sample_set.build_numbered_pdf(tmp_path)

    run(source, "--no-front-matter")

    text = (tmp_path / "contract.md").read_text(encoding="utf-8")
    # A blank line between clauses, so Markdown doesn't run them into one paragraph...
    assert "1.2.4.a Priority 1\n\n1.2.4.b Priority 2" in text
    # ...while a paragraph's wrapped lines stay in one paragraph.
    assert "long enough\nto need one" in text
