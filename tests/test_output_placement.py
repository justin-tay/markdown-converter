"""Output placement and re-runs (ticket 04, ADR 0005)."""

from __future__ import annotations

import os

import sample_set


def test_name_collisions_keep_both_extensions(run, tmp_path):
    sample_set.build_name_collision(tmp_path)

    result = run(tmp_path)

    assert (tmp_path / "report.pdf.md").exists()
    assert (tmp_path / "report.docx.md").exists()
    assert (tmp_path / "report.docx_assets" / "img01.png").exists()
    assert "![](report.docx_assets/img01.png)" in (tmp_path / "report.docx.md").read_text(encoding="utf-8")
    assert not (tmp_path / "report.md").exists()
    warnings = result.output.split("Warnings:", 1)[1]
    assert "report.docx: Name Collision with report.pdf" in warnings


def test_collision_outputs_are_not_converted_again(run, tmp_path):
    sample_set.build_name_collision(tmp_path)
    run(tmp_path)

    result = run(tmp_path)

    assert "Converted: 0" in result.output
    assert not (tmp_path / "report.docx_assets" / "img01.md").exists()


def test_output_folder_mirrors_the_target_and_leaves_it_untouched(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    before = sorted(p.relative_to(library) for p in library.rglob("*"))
    out = tmp_path / "converted"

    result = run(library, "--output", out)

    assert result.exit_code == 0
    assert sorted(p.relative_to(library) for p in library.rglob("*")) == before
    assert (out / "sales.md").exists()
    assert (out / "reports" / "deep" / "project.md").exists()
    assert (out / "Q3 résumé files" / "inventory.md").exists()
    assert (out / "markdown-converter.log").exists()


def test_output_folder_inside_the_target_is_not_scanned(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    out = library / "converted"
    run(library, "--output", out)

    result = run(library, "--output", out)

    assert "Converted: 0" in result.output
    assert not (out / "converted").exists()


def test_second_run_skips_up_to_date_files(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    run(library)

    result = run(library)

    assert result.exit_code == 0
    assert "Converted: 0" in result.output
    assert "Up To Date: 4" in result.output
    assert "sales.csv … up to date" in result.output


def test_changed_source_file_is_reconverted_alone(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)
    run(library)
    source = library / "sales.csv"
    later = (library / "sales.md").stat().st_mtime + 10
    os.utime(source, (later, later))

    result = run(library)

    assert "Converted: 1" in result.output
    assert "sales.csv … ok" in result.output


def test_force_reconverts_everything_and_leaves_no_stale_assets(run, tmp_path):
    sample_set.build_word_with_images(tmp_path)
    run(tmp_path)
    stale = tmp_path / "site-report_assets" / "img99.png"
    stale.write_bytes(b"left over")

    result = run(tmp_path, "--force")

    assert "Converted: 1" in result.output
    assert not stale.exists()
    assert (tmp_path / "site-report_assets" / "img01.png").exists()
