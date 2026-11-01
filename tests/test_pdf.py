"""PDF pages and images (ticket 07)."""

from __future__ import annotations

import sample_set


def _page(text, number):
    return text.split(f"## Page {number}\n", 1)[1].split("## Page ", 1)[0]


def test_each_pdf_page_gets_its_own_section(run, tmp_path):
    source = sample_set.build_text_pdf(tmp_path)

    run(source)

    text = (tmp_path / "brief.md").read_text(encoding="utf-8")
    assert "Project brief page one" in _page(text, 1)
    assert "Project brief page two" in _page(text, 2)
    assert "\x0c" not in text


def test_pdf_images_are_saved_and_linked_after_their_page_text(run, tmp_path):
    source = sample_set.build_pdf_with_images(tmp_path)

    run(source)

    text = (tmp_path / "annual-report.md").read_text(encoding="utf-8")
    assets = tmp_path / "annual-report_assets"
    names = sorted(p.name for p in assets.iterdir())
    # Images within a page follow the PDF's resource order, not drawing order.
    assert sorted(n[:-4] for n in names) == ["p001-img01", "p001-img02", "p001-img03"]
    assert sorted(n[-4:] for n in names) == [".jpg", ".png", ".png"]
    page_one = _page(text, 1)
    first_link = page_one.index("](annual-report_assets/")
    assert page_one.index("Annual report page one") < first_link
    for name in names:
        assert f"](annual-report_assets/{name})" in page_one


def test_logo_repeated_on_every_page_is_stored_once(run, tmp_path):
    source = sample_set.build_pdf_with_images(tmp_path)

    run(source)

    text = (tmp_path / "annual-report.md").read_text(encoding="utf-8")
    page_two_links = [line for line in _page(text, 2).splitlines() if line.startswith("![](")]
    assert len(page_two_links) == 1
    assert page_two_links[0] in _page(text, 1)
    assert len(list((tmp_path / "annual-report_assets").iterdir())) == 3


def test_page_snapshots_render_each_page_at_150_dpi_linked_first(run, tmp_path):
    source = sample_set.build_pdf_with_vector_chart(tmp_path)

    run(source, "--pdf-page-images")

    from PIL import Image

    text = (tmp_path / "sales-chart.md").read_text(encoding="utf-8")
    assets = tmp_path / "sales-chart_assets"
    for number in (1, 2):
        snapshot = assets / f"p00{number}-page01.png"
        with Image.open(snapshot) as image:
            width, height = image.size
        # A4 (595.3 x 841.9 pt) at 150 DPI is about 1240 x 1754 px, give or take rounding.
        assert abs(width - 1240) <= 1 and abs(height - 1754) <= 1
        assert _page(text, number).lstrip().startswith(f"![](sales-chart_assets/p00{number}-page01.png)")


def test_no_page_snapshots_without_the_option(run, tmp_path):
    source = sample_set.build_pdf_with_vector_chart(tmp_path)

    run(source)

    assert not (tmp_path / "sales-chart_assets").exists()


def test_image_in_an_undecodable_encoding_is_saved_raw_with_a_warning(run, tmp_path):
    source = sample_set.build_pdf_with_undecodable_image(tmp_path)

    result = run(source)

    assert result.exit_code == 0
    assert (tmp_path / "fax_assets" / "p001-img01.jb2").read_bytes() == sample_set.JBIG2_PAYLOAD
    assert "saved raw (.jb2)" in result.output.split("Warnings:", 1)[1]


def test_scanned_pdf_warns_about_missing_text_layer_but_keeps_its_images(run, tmp_path):
    source = sample_set.build_scanned_pdf(tmp_path)

    result = run(source)

    assert result.exit_code == 0
    assert "scanned.pdf: no text layer found" in result.output.split("Warnings:", 1)[1]
    assert (tmp_path / "scanned_assets" / "p001-img01.png").exists()
