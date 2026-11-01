"""Edge cases found in the final review of tickets 02-15."""

from __future__ import annotations

import io
import socket

import pytest
import sample_set

from markdown_converter import offline


def test_collision_across_stems_keeps_every_output_distinct(run, tmp_path):
    sample_set.build_csv(tmp_path).rename(tmp_path / "report.csv")
    sample_set.build_json(tmp_path).rename(tmp_path / "report.json")
    sample_set.build_xml(tmp_path).rename(tmp_path / "report.csv.json")

    result = run(tmp_path)

    assert "Converted: 3" in result.output
    assert "| Region | Q1 | Q2 |" in (tmp_path / "report.csv.md").read_text(encoding="utf-8")
    assert "Apollo" in (tmp_path / "report.json.md").read_text(encoding="utf-8")
    assert "Widget" in (tmp_path / "report.csv.json.md").read_text(encoding="utf-8")


def test_single_file_target_still_respects_name_collisions_with_its_neighbours(run, tmp_path):
    sample_set.build_csv(tmp_path).rename(tmp_path / "data.csv")
    sample_set.build_json(tmp_path).rename(tmp_path / "data.json")

    run(tmp_path / "data.csv")
    result = run(tmp_path / "data.json")

    assert "data.json … ok" in result.output
    assert (tmp_path / "data.csv.md").exists()
    assert "Apollo" in (tmp_path / "data.json.md").read_text(encoding="utf-8")
    assert not (tmp_path / "data.md").exists()


def test_udp_datagrams_to_other_machines_are_blocked(run, tmp_path):
    run(sample_set.build_csv(tmp_path))  # installs the Offline Guard
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        with pytest.raises(offline.NetworkBlockedError):
            udp.sendto(b"leak", ("192.0.2.1", 53))


def test_loopback_names_still_resolve(run, tmp_path):
    run(sample_set.build_csv(tmp_path))

    assert socket.gethostbyname("localhost") in ("127.0.0.1", "::1")


def test_word_chart_whose_part_name_has_an_underscore(run, tmp_path):
    source = sample_set.build_word_with_charts(tmp_path)
    _rename_part(source, "word/charts/chart1.xml", "word/charts/chart_one.xml")

    result = run(source)

    assert result.exit_code == 0
    text = (tmp_path / "dashboard.md").read_text(encoding="utf-8")
    assert "**Chart: Revenue by Quarter (column chart)**" in text


def test_html_image_names_with_brackets_and_file_urls_are_copied(run, tmp_path):
    (tmp_path / "pic (1).png").write_bytes(sample_set.LOGO_PNG)
    (tmp_path / "abs.png").write_bytes(sample_set.CHART_PNG)
    file_url = (tmp_path / "abs.png").as_uri()
    source = tmp_path / "page.html"
    source.write_text(f'<p><img src="pic (1).png" alt="One"><img src="{file_url}" alt="Abs"></p>', encoding="utf-8")

    result = run(source)

    text = (tmp_path / "page.md").read_text(encoding="utf-8")
    assert "![One](page_assets/img01.png)" in text
    assert "![Abs](page_assets/img02.png)" in text
    assert "not fetched" not in result.output


def test_output_that_is_a_file_is_invalid_usage(run, tmp_path):
    source = sample_set.build_csv(tmp_path)
    clash = tmp_path / "not-a-folder.txt"
    clash.write_text("x", encoding="utf-8")

    result = run(source, "--output", clash)

    assert result.exit_code == 2
    assert "not-a-folder.txt" in result.output


def test_leftover_staging_from_an_interrupted_run_is_discarded(run, tmp_path):
    source = sample_set.build_word_with_images(tmp_path)
    leftover = tmp_path / ".site-report_assets.partial"
    leftover.mkdir()
    (leftover / "img99.png").write_bytes(b"stale")

    run(source)

    assert not (tmp_path / "site-report_assets" / "img99.png").exists()
    assert not leftover.exists()


def test_word_header_images_that_markitdown_drops_are_still_saved(run, tmp_path):
    source = sample_set.build_word_with_header_logo(tmp_path)

    run(source)

    text = (tmp_path / "letter.md").read_text(encoding="utf-8")
    assets = tmp_path / "letter_assets"
    assert (assets / "img01.png").read_bytes() == sample_set.LOGO_PNG
    assert "## Other images\n\n![](letter_assets/img01.png)" in text


def test_end_of_input_at_folder_confirmation_converts_nothing(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(stdin=f"{library}\n")

    assert "Nothing was converted." in result.output
    assert not (library / "sales.md").exists()


def _rename_part(package, old, new):
    import zipfile

    with zipfile.ZipFile(package) as source:
        members = {item.filename: source.read(item) for item in source.infolist()}
    members[new] = members.pop(old)
    old_target, new_target = old.split("word/", 1)[1], new.split("word/", 1)[1]
    rels = "word/_rels/document.xml.rels"
    members[rels] = members[rels].replace(old_target.encode(), new_target.encode())
    members["[Content_Types].xml"] = members["[Content_Types].xml"].replace(old.encode(), new.encode())
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as target:
        for name, data in members.items():
            target.writestr(name, data)
    package.write_bytes(buffer.getvalue())
