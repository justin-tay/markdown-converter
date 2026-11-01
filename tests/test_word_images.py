"""Asset Store and Word images (ticket 05)."""

from __future__ import annotations

import re
import shutil

import sample_set

_LINK = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def _convert(run, tmp_path, *options):
    source = sample_set.build_word_with_images(tmp_path)
    result = run(source, *options)
    return result, (tmp_path / "site-report.md").read_text(encoding="utf-8"), tmp_path / "site-report_assets"


def test_embedded_images_are_saved_in_their_original_formats(run, tmp_path):
    _, _, assets = _convert(run, tmp_path)

    assert sorted(p.name for p in assets.iterdir()) == ["img01.png", "img02.jpg", "img03.png", "img04.emf"]
    assert (assets / "img01.png").read_bytes() == sample_set.LOGO_PNG
    assert (assets / "img04.emf").read_bytes() == sample_set.emf_bytes()


def test_image_links_appear_where_the_image_was(run, tmp_path):
    _, text, _ = _convert(run, tmp_path)

    assert "Company logo:\n\n![](site-report_assets/img01.png)" in text
    assert "Photo of the site:\n\n![](site-report_assets/img02.jpg)" in text
    assert "Floor plan:\n\n![](site-report_assets/img04.emf)" in text
    assert "data:image" not in text


def test_identical_images_are_saved_once_and_linked_from_every_place(run, tmp_path):
    _, text, _ = _convert(run, tmp_path)

    assert "Logo again in the footer:\n\n![](site-report_assets/img01.png)" in text


def test_links_keep_working_when_document_and_assets_move_together(run, tmp_path):
    _, text, assets = _convert(run, tmp_path)
    moved = tmp_path / "moved"
    moved.mkdir()
    shutil.move(str(tmp_path / "site-report.md"), moved)
    shutil.move(str(assets), moved)

    for link in _LINK.findall((moved / "site-report.md").read_text(encoding="utf-8")):
        assert (moved / link).is_file(), link


def test_min_image_size_drops_small_images_and_their_links(run, tmp_path):
    _, text, assets = _convert(run, tmp_path, "--min-image-size", "32")

    assert sorted(p.name for p in assets.iterdir()) == ["img01.png", "img02.jpg", "img03.emf"]
    assert "Status icon:\n\nFloor plan:" in text


def test_emf_images_are_kept_with_a_warning(run, tmp_path):
    result, _, _ = _convert(run, tmp_path)

    warnings = result.output.split("Warnings:", 1)[1]
    assert "site-report.docx: img04.emf is EMF/WMF" in warnings


def test_no_assets_folder_when_there_is_nothing_to_save(run, tmp_path):
    sample_set.build_csv(tmp_path)

    run(tmp_path)

    assert not (tmp_path / "sales_assets").exists()


def test_asset_links_are_url_safe_for_names_with_spaces(run, tmp_path):
    source = sample_set.build_word_with_images(tmp_path)
    renamed = source.rename(tmp_path / "site report.docx")

    run(renamed)

    text = (tmp_path / "site report.md").read_text(encoding="utf-8")
    assert "![](site%20report_assets/img01.png)" in text
    assert (tmp_path / "site report_assets" / "img01.png").exists()
