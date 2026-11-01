"""Folder Targets and batch reporting (ticket 03)."""

from __future__ import annotations

import hashlib
import os

import pytest
import sample_set


def test_folder_target_converts_every_source_file_at_every_depth(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(library)

    assert result.exit_code == 0
    assert (library / "sales.md").exists()
    assert (library / "reports" / "memo.md").exists()
    assert (library / "reports" / "deep" / "project.md").exists()
    assert (library / "Q3 résumé files" / "inventory.md").exists()


def test_progress_lines_show_position_and_path_within_the_target(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(library)

    assert "[1/4] Q3 résumé files/inventory.xml … ok" in result.output
    assert "[4/4] sales.csv … ok" in result.output


def test_no_recurse_converts_only_the_top_folder(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    run(library, "--no-recurse")

    assert (library / "sales.md").exists()
    assert not (library / "reports" / "memo.md").exists()


def test_unsupported_files_are_ignored_and_counted(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(library)

    assert not (library / "notes.md").exists()
    assert "Ignored: 1" in result.output


def test_hidden_folders_are_skipped(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    run(library)

    assert not (library / ".hidden" / "sales.md").exists()


def test_converter_output_is_never_converted_again(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    (library / "old.md").write_text("# Converted earlier\n", encoding="utf-8")
    assets = library / "old_assets"
    assets.mkdir()
    sample_set.build_csv(assets)
    own_folder = library / "client_assets"
    own_folder.mkdir()
    sample_set.build_json(own_folder)

    result = run(library)

    assert not (assets / "sales.md").exists()
    assert (own_folder / "project.md").exists()
    assert "Ignored: 1" in result.output


def test_symbolic_links_are_not_followed(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    sample_set.build_json(elsewhere)
    try:
        os.symlink(elsewhere, library / "linked", target_is_directory=True)
    except OSError:
        pytest.skip("creating symbolic links needs extra privileges on this machine")

    run(library)

    assert not (elsewhere / "project.md").exists()


def test_a_damaged_file_fails_with_a_reason_and_the_run_continues(run, tmp_path):
    sample_set.build_damaged_docx(tmp_path)
    sample_set.build_csv(tmp_path)

    result = run(tmp_path)

    assert result.exit_code == 1
    assert (tmp_path / "sales.md").exists()
    assert "broken.docx … failed (" in result.output
    assert "Converted: 1" in result.output
    assert "Failed: 1" in result.output


@pytest.mark.parametrize("build", [sample_set.build_encrypted_pdf, sample_set.build_encrypted_docx])
def test_encrypted_files_are_skipped_as_encrypted(run, tmp_path, build):
    source = build(tmp_path)
    sample_set.build_csv(tmp_path)

    result = run(tmp_path)

    assert f"{source.name} … skipped (encrypted)" in result.output
    assert "Skipped: 1" in result.output
    assert not source.with_suffix(".md").exists()
    assert result.exit_code == 1


def test_run_summary_lists_each_failure_and_skip_with_its_reason(run, tmp_path):
    sample_set.build_damaged_docx(tmp_path)
    sample_set.build_encrypted_pdf(tmp_path)

    result = run(tmp_path)

    summary = result.output.split("Run Summary", 1)[1]
    assert "broken.docx: " in summary
    assert "locked.pdf: encrypted" in summary


def test_log_file_is_written_to_the_target_folder(run, tmp_path):
    sample_set.build_csv(tmp_path)

    result = run(tmp_path)

    log = (tmp_path / "markdown-converter.log").read_text(encoding="utf-8")
    assert "[1/1] sales.csv … ok" in log
    assert "Converted: 1" in log
    assert result.exit_code == 0


def test_log_file_for_a_single_file_target_goes_beside_it(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    run(source)

    assert (tmp_path / "markdown-converter.log").exists()


def test_run_continues_with_a_warning_when_the_log_cannot_be_written(run, tmp_path):
    sample_set.build_csv(tmp_path)
    (tmp_path / "markdown-converter.log").mkdir()  # makes the log path unwritable

    result = run(tmp_path)

    assert result.exit_code == 0
    assert (tmp_path / "sales.md").exists()
    assert "could not write the log file" in result.output


def test_source_files_are_never_modified(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    before = _fingerprints(library)

    run(library)

    after = {path: print_ for path, print_ in _fingerprints(library).items() if path in before}
    assert after == before


def _fingerprints(folder):
    return {
        path: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in folder.rglob("*")
        if path.is_file() and path.suffix != ".md" and path.name != "markdown-converter.log"
    }
