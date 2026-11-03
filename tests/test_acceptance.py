"""Acceptance run over the full Sample Set (ticket 15, StRS section 6)."""

from __future__ import annotations

import sample_set

from markdown_converter import offline


def test_full_library_converts_with_the_expected_outcome_per_sample(run, tmp_path):
    library = sample_set.build_full_library(tmp_path)
    blocked_before = offline.blocked_attempts()

    result = run(library, "--pdf-page-images")

    output = result.output
    summary = output.split("Run Summary", 1)[1]
    # Two encrypted samples are skipped and the damaged one fails; the rest convert.
    assert "Skipped: 2" in summary
    assert "Failed: 1" in summary
    assert "broken.docx: " in summary
    assert "locked.pdf: encrypted" in summary
    assert "locked.docx: encrypted" in summary
    assert "Ignored: 2" in summary  # notes.txt, and the HTML page's own image file
    assert result.exit_code == 1
    assert offline.blocked_attempts() == blocked_before

    converted = int(summary.split("Converted: ", 1)[1].split("\n", 1)[0])
    total = int(output.split("[1/", 1)[1].split("]", 1)[0])
    assert converted == total - 3

    # Spot-check one Converted Document per extractor.
    expectations = {
        "build_word_with_images/site-report.md": "site-report_assets/img01.png",
        "build_word_with_charts/dashboard.md": "**Chart: Revenue by Quarter (column chart)**",
        "build_slides/results.md": "results_assets/slide01-img01.png",
        "build_slides_with_chart/metrics.md": "metrics_assets/slide02-chart01.xml",
        "build_pdf_with_images/annual-report.md": "<!-- page 2 -->",
        "build_pdf_with_vector_chart/sales-chart.md": "sales-chart_assets/p001-page01.png",
        "build_workbook/finance.md": "finance_assets/sheet-Trend-chart01.xml",
        "build_html_with_images/page.md": "page_assets/img01.png",
        "build_epub_with_images/atlas.md": "atlas_assets/img01.png",
        "build_msg/budget-email.md": "**Subject:** Budget review",
        "build_xls/legacy.md": "| Laptops | 1200 |",
    }
    for relative, expected in expectations.items():
        matches = list(library.glob(f"*/{relative}"))
        assert len(matches) == 1, relative
        assert expected in matches[0].read_text(encoding="utf-8"), relative
    assert (library / "collision" / "report.pdf.md").exists()
    assert (library / "collision" / "report.docx.md").exists()
    assert (library / "markdown-converter.log").exists()


def test_full_library_rerun_is_all_up_to_date_apart_from_unconvertible_files(run, tmp_path):
    library = sample_set.build_full_library(tmp_path)
    run(library)

    result = run(library)

    assert "Converted: 0" in result.output
    assert "Skipped: 2" in result.output
    assert "Failed: 1" in result.output
