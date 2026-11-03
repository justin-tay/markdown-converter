"""PDF structure from tags (ticket 17), the layout fallback (ticket 18) and Figure Snapshots (ticket 19)."""

from __future__ import annotations

import sample_set


def _convert_tagged(run, tmp_path) -> str:
    run(sample_set.build_tagged_pdf(tmp_path))
    return (tmp_path / "handbook.md").read_text(encoding="utf-8")


def test_tagged_headings_keep_their_levels_instead_of_page_sections(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    lines = text.splitlines()
    assert "# Club handbook" in lines
    assert "## Joining" in lines
    assert "## Facilities" in lines
    assert "## Page" not in text
    assert "## \n" not in text  # the empty tagged heading is skipped


def test_tagged_lists_keep_labels_as_written_and_bullets_as_items(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "1\\. Fill in the form at the desk.\n\n2\\. A volunteer checks it." in text
    assert "- Library\n- Workshop\n  - Open on Saturdays\n- [Booking page](https://example.com/booking)" in text


def test_web_links_are_markdown_links_and_links_within_the_pdf_are_plain_text(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert ("Forms are on the [website](https://example.com/forms), and facilities are covered on page 2."
            in text.splitlines())


def test_table_running_across_pages_is_one_table_with_no_page_marker_inside(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "| Room | Seats |\n|---|---|\n| Hall | 80 |\n| Studio | 12 |" in text


def test_merged_table_cells_leave_the_cells_they_cover_blank(run, tmp_path):
    run(sample_set.build_tagged_pdf_with_merged_cells(tmp_path))

    text = (tmp_path / "rooms.md").read_text(encoding="utf-8")
    assert "| Room | Equipment |  |\n|---|---|---|\n| A | Projector | Yes |\n|  | Screen | No |" in text


def test_contents_list_keeps_titles_without_leaders_or_page_numbers(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "- Joining\n- Facilities" in text


def test_page_furniture_is_left_out_and_each_page_gets_a_marker_before_its_first_block(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "Members only" not in text
    assert "of 3" not in text
    assert not any(path.name.startswith(("p001-img", "p002-img")) for path in (tmp_path / "handbook_assets").iterdir())
    body = text.split("---\n\n", 1)[1]
    assert body.startswith("<!-- page 1 -->\n\n# Club handbook")
    assert "<!-- page 2 -->\n\n## Facilities" in body
    assert "| Studio | 12 |\n\n<!-- page 3 -->\n\nBook rooms a week ahead." in body


def test_single_image_figure_is_saved_as_is_and_linked_at_its_place_with_its_alt_text(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert ("Book rooms a week ahead.\n\n![Club logo](handbook_assets/p003-img01.png)\n\n"
            "Remember to sign the visitor book.") in text
    from PIL import Image

    with Image.open(tmp_path / "handbook_assets" / "p003-img01.png") as image:
        assert image.size == (48, 24)


def test_log_says_the_pdf_was_read_from_its_tags_without_warning_about_it(run, tmp_path):
    result = run(sample_set.build_tagged_pdf(tmp_path))

    log = (tmp_path / "markdown-converter.log").read_text(encoding="utf-8")
    assert "handbook.pdf: structure read from its tags" in log
    assert "structure read" not in result.output


def test_page_snapshots_follow_each_page_marker(run, tmp_path):
    run(sample_set.build_tagged_pdf(tmp_path), "--pdf-page-images")

    text = (tmp_path / "handbook.md").read_text(encoding="utf-8")
    for number in (1, 2, 3):
        assert f"<!-- page {number} -->\n\n![](handbook_assets/p00{number}-page01.png)\n\n" in text


def test_each_page_marker_appears_once_in_page_order_when_tags_jump_between_pages(run, tmp_path):
    run(sample_set.build_tagged_pdf_out_of_page_order(tmp_path), "--pdf-page-images", "--no-front-matter")

    text = (tmp_path / "leaflet.md").read_text(encoding="utf-8")
    assert text == (
        "<!-- page 1 -->\n\n![](leaflet_assets/p001-page01.png)\n\nOpening paragraph.\n\n"
        "<!-- page 2 -->\n\n![](leaflet_assets/p002-page01.png)\n\n"
        "<!-- page 3 -->\n\n![](leaflet_assets/p003-page01.png)\n\nCallout drawn on page three.\n\n"
        "Rest of page one.\n\n"
        "<!-- page 4 -->\n\n![](leaflet_assets/p004-page01.png)\n\nClosing paragraph.\n"
    )


def _convert_untagged(run, tmp_path) -> str:
    run(sample_set.build_untagged_pdf(tmp_path))
    return (tmp_path / "project-plan.md").read_text(encoding="utf-8")


def test_untagged_page_furniture_is_left_out_but_a_repeated_table_header_row_is_kept(run, tmp_path):
    text = _convert_untagged(run, tmp_path)

    assert "CONFIDENTIAL" not in text
    assert "Appendix A" not in text
    assert text.count("| No. | Task |") == 3


def test_untagged_bold_and_larger_titles_become_headings(run, tmp_path):
    text = _convert_untagged(run, tmp_path)

    lines = text.splitlines()
    assert "# PROJECT PLAN" in lines
    assert "## BACKGROUND" in lines
    assert "## SCHEDULE" in lines
    assert "1\\. This plan describes the work on the new club\nwebsite." in text


def test_untagged_bordered_table_is_a_markdown_table_after_its_page_marker(run, tmp_path):
    text = _convert_untagged(run, tmp_path)

    assert "<!-- page 2 -->\n\n| No. | Task |\n|---|---|\n| 1 | Draft |" in text
    assert "## Page" not in text


def test_untagged_diagram_becomes_one_figure_snapshot_in_place_of_its_labels(run, tmp_path):
    text = _convert_untagged(run, tmp_path)

    assert ("| Laptop | 900 |\n\n![](project-plan_assets/p001-fig01.png)\n\n"
            "The release process is shown above.") in text
    assert "Draft site" not in text and "Live site" not in text
    from PIL import Image

    with Image.open(tmp_path / "project-plan_assets" / "p001-fig01.png") as image:
        width, height = image.size
    # The diagram spans about 328 x 62 pt; at 150 DPI that is roughly 683 x 129 px, plus a little margin.
    assert 660 <= width <= 720 and 120 <= height <= 170


def test_untagged_shaded_rows_and_underlines_are_not_mistaken_for_diagrams(run, tmp_path):
    text = _convert_untagged(run, tmp_path)

    assert "Week 1 planning meeting Room B" in text and "Week 12 planning meeting Room B" in text
    assert not (tmp_path / "project-plan_assets" / "p001-fig02.png").exists()


def test_untagged_table_columns_split_by_extra_borders_are_merged(run, tmp_path):
    text = _convert_untagged(run, tmp_path)

    assert "| Item | Cost |\n|---|---|\n| Laptop | 900 |" in text


def test_log_says_an_untagged_pdf_was_read_from_its_layout(run, tmp_path):
    run(sample_set.build_untagged_pdf(tmp_path))

    log = (tmp_path / "markdown-converter.log").read_text(encoding="utf-8")
    assert "project-plan.pdf: structure read from its layout (no tags)" in log


def test_vector_figure_becomes_one_figure_snapshot_of_its_area_at_its_place(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert ("- [Booking page](https://example.com/booking)\n\n![Visits by quarter](handbook_assets/p002-fig01.png)\n\n| Room | Seats |"
            in text)
    from PIL import Image

    with Image.open(tmp_path / "handbook_assets" / "p002-fig01.png") as image:
        width, height = image.size
    # The figure's tagged BBox is 240 x 165 pt; at 150 DPI that is 500 x 344 px, give or take rounding.
    assert abs(width - 500) <= 2 and abs(height - 344) <= 2


def test_figure_of_an_image_with_drawing_over_it_is_one_snapshot_not_pieces(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "![Annotated sign-up form](handbook_assets/p003-fig01.png)" in text
    names = sorted(p.name for p in (tmp_path / "handbook_assets").iterdir())
    assert names == ["p002-fig01.png", "p003-fig01.png", "p003-fig02.png", "p003-fig03.png", "p003-img01.png"]


def test_diagram_with_a_label_tagged_inside_it_is_still_a_figure_snapshot(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "![Booking flow](handbook_assets/p003-fig03.png)\n\nMember sends the booking to the desk" in text


def test_text_box_figure_gives_its_text_and_no_picture(run, tmp_path):
    text = _convert_tagged(run, tmp_path)

    assert "![Club logo](handbook_assets/p003-img01.png)\n\nRemember to sign the visitor book.\n\n![Annotated" in text


def test_figures_smaller_than_the_minimum_image_size_are_skipped(run, tmp_path):
    run(sample_set.build_tagged_pdf(tmp_path), "--min-image-size", "32")

    text = (tmp_path / "handbook.md").read_text(encoding="utf-8")
    assert "![Tick]" not in text
    figures = sorted(p.name for p in (tmp_path / "handbook_assets").iterdir() if p.name.startswith("p003-fig"))
    assert figures == ["p003-fig01.png", "p003-fig02.png"]  # the annotated form and the diagram only
