"""HTML and EPUB images (ticket 11)."""

from __future__ import annotations

import socket

import sample_set

from markdown_converter import offline


def test_local_html_images_are_copied_and_relinked(run, tmp_path):
    source = sample_set.build_html_with_images(tmp_path)

    run(source)

    text = (tmp_path / "page.md").read_text(encoding="utf-8")
    assert "![Sales chart](page_assets/img01.png)" in text
    assert (tmp_path / "page_assets" / "img01.png").read_bytes() == sample_set.CHART_PNG


def test_remote_html_images_are_left_as_links_and_reported(run, tmp_path):
    source = sample_set.build_html_with_images(tmp_path)
    blocked_before = offline.blocked_attempts()

    result = run(source)

    text = (tmp_path / "page.md").read_text(encoding="utf-8")
    assert f"![Partner]({sample_set.REMOTE_IMAGE_URL})" in text
    assert "page.html: 1 remote image not fetched" in result.output.split("Warnings:", 1)[1]
    assert offline.blocked_attempts() == blocked_before  # never even tried
    assert result.exit_code == 0


def test_bundled_epub_images_are_saved_and_linked(run, tmp_path):
    source = sample_set.build_epub_with_images(tmp_path)

    run(source)

    text = (tmp_path / "atlas.md").read_text(encoding="utf-8")
    assert "![Map](atlas_assets/img01.png)" in text
    assert (tmp_path / "atlas_assets" / "img01.png").read_bytes() == sample_set.CHART_PNG


def test_offline_guard_stays_installed_after_a_run(run, tmp_path):
    run(sample_set.build_html_with_images(tmp_path))

    try:
        socket.getaddrinfo("example.com", 443)
    except offline.NetworkBlockedError:
        return
    raise AssertionError("network lookups should be blocked once the converter has run")
