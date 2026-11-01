from __future__ import annotations

import sample_set


def test_nonexistent_target_is_invalid_usage(run, tmp_path):
    result = run(tmp_path / "missing.pdf")

    assert result.exit_code == 2
    assert "missing.pdf" in result.output
    assert "does not exist" in result.output


def test_help_describes_the_target_and_each_option(run):
    result = run("--help")

    assert result.exit_code == 0
    assert "file or folder to convert" in result.output
    assert "--no-front-matter" in result.output
    assert "front matter" in result.output.split("--no-front-matter", 1)[1]


def test_single_unsupported_file_is_invalid_usage_listing_supported_formats(run, tmp_path):
    target = tmp_path / "song.mp3"
    target.write_bytes(b"ID3")

    result = run(target)

    assert result.exit_code == 2
    assert "song.mp3" in result.output
    assert "PDF" in result.output and "DOCX" in result.output
    assert not (tmp_path / "song.md").exists()


def test_unknown_option_is_invalid_usage(run, tmp_path):
    target = sample_set.build_csv(tmp_path)

    result = run(target, "--frobnicate")

    assert result.exit_code == 2
    assert "--frobnicate" in result.output
