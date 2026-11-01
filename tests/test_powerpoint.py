"""PowerPoint images, speaker notes and hidden slides (ticket 06)."""

from __future__ import annotations

import sample_set


def _convert(run, tmp_path):
    source = sample_set.build_slides(tmp_path)
    run(source)
    return (tmp_path / "results.md").read_text(encoding="utf-8"), tmp_path / "results_assets"


def _slide(text, number):
    return text.split(f"<!-- Slide number: {number} -->", 1)[1].split("<!-- Slide number:", 1)[0]


def test_slide_images_are_saved_and_named_by_slide(run, tmp_path):
    _, assets = _convert(run, tmp_path)

    assert sorted(p.name for p in assets.iterdir()) == [
        "slide01-img01.png", "slide02-img01.jpg", "slide02-img02.png",
    ]
    assert (assets / "slide01-img01.png").read_bytes() == sample_set.LOGO_PNG


def test_image_links_appear_within_their_slide(run, tmp_path):
    text, _ = _convert(run, tmp_path)

    assert "results_assets/slide01-img01.png)" in _slide(text, 1)
    assert "results_assets/slide02-img01.jpg)" in _slide(text, 2)
    assert "results_assets/slide02-img02.png)" in _slide(text, 2)
    assert "data:image" not in text


def test_speaker_notes_and_hidden_slides_are_included(run, tmp_path):
    text, _ = _convert(run, tmp_path)

    assert "Mention the delayed delivery." in _slide(text, 2)
    assert "Backup Figures" in _slide(text, 3)
