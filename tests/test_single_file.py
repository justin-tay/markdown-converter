from __future__ import annotations

from datetime import datetime

import pytest
import sample_set

from markdown_converter import __version__


def test_csv_source_file_becomes_converted_document_beside_it(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    result = run(source)

    converted = tmp_path / "sales.md"
    assert result.exit_code == 0
    assert "| Region | Q1 | Q2 |" in converted.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("build", "converted_name", "expected"),
    [
        (sample_set.build_json, "project.md", '"project": "Apollo"'),
        (sample_set.build_xml, "inventory.md", '<item sku="A1">Widget</item>'),
    ],
)
def test_structured_text_formats_convert_utf8(run, tmp_path, build, converted_name, expected):
    source = build(tmp_path)

    result = run(source)

    assert result.exit_code == 0
    assert expected in (tmp_path / converted_name).read_text(encoding="utf-8")


def test_word_document_keeps_headings_lists_and_tables(run, tmp_path):
    source = sample_set.build_text_docx(tmp_path)

    run(source)

    text = (tmp_path / "memo.md").read_text(encoding="utf-8")
    assert "# Quarterly Memo" in text
    assert "* Revenue grew" in text or "- Revenue grew" in text
    assert "| Revenue | 120 |" in text


def test_converted_document_starts_with_source_front_matter(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    run(source)

    lines = (tmp_path / "sales.md").read_text(encoding="utf-8").splitlines()
    end = lines.index("---", 1)
    assert lines[0] == "---"
    fields = dict(line.split(": ", 1) for line in lines[1:end])
    assert fields["source"] == "sales.csv"
    assert fields["format"] == "csv"
    assert fields["converter_version"] == __version__
    assert datetime.fromisoformat(fields["converted"]).tzinfo is not None


def test_progress_line_and_run_summary_are_shown(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    result = run(source)

    assert "[1/1] sales.csv … ok" in result.output
    assert "Converted: 1" in result.output
    assert "Failed: 0" in result.output


def test_damaged_source_file_fails_with_reason_and_exit_code_1(run, tmp_path):
    source = tmp_path / "broken.docx"
    source.write_bytes(b"PK\x03\x04 this is not really a Word document")

    result = run(source)

    assert result.exit_code == 1
    assert "[1/1] broken.docx … failed (" in result.output
    assert "Failed: 1" in result.output
    assert not (tmp_path / "broken.md").exists()


def test_no_front_matter_option_omits_the_header(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    run(source, "--no-front-matter")

    text = (tmp_path / "sales.md").read_text(encoding="utf-8")
    assert text.startswith("| Region | Q1 | Q2 |")
