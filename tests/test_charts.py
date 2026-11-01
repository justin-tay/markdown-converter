"""Charts as data and definition (tickets 09 and 10, ADR 0002)."""

from __future__ import annotations

import sample_set

REVENUE_TABLE = (
    "| Category | 2025 | 2026 |\n"
    "| --- | --- | --- |\n"
    "| Q1 | 10 | 12 |\n"
    "| Q2 | 20 | 25 |"
)


def test_word_chart_appears_as_heading_table_and_definition_link(run, tmp_path):
    source = sample_set.build_word_with_charts(tmp_path)

    run(source)

    text = (tmp_path / "dashboard.md").read_text(encoding="utf-8")
    expected = (
        "Revenue chart:\n\n"
        "**Chart: Revenue by Quarter (column chart)**\n\n"
        f"{REVENUE_TABLE}\n\n"
        "[Chart definition](dashboard_assets/chart01.xml)"
    )
    assert expected in text
    assert (tmp_path / "dashboard_assets" / "chart01.xml").read_bytes() == sample_set.REVENUE_CHART_XML


def test_unreadable_chart_still_appears_with_a_note_and_its_definition(run, tmp_path):
    source = sample_set.build_word_with_charts(tmp_path)

    run(source)

    text = (tmp_path / "dashboard.md").read_text(encoding="utf-8")
    after_intro = text.split("Legacy chart:", 1)[1]
    assert "**Chart: Untitled (line chart)**" in after_intro
    assert "data not extracted" in after_intro
    assert "[Chart definition](dashboard_assets/chart02.xml)" in after_intro
    assert (tmp_path / "dashboard_assets" / "chart02.xml").read_bytes() == sample_set.BROKEN_CHART_XML
    assert "End of dashboard." in after_intro


def _sheet(text, name):
    return text.split(f"## {name}\n", 1)[1].split("\n## ", 1)[0]


def test_excel_images_and_charts_are_linked_within_their_sheet(run, tmp_path):
    source = sample_set.build_workbook(tmp_path)

    run(source)

    text = (tmp_path / "finance.md").read_text(encoding="utf-8")
    assets = tmp_path / "finance_assets"
    assert sorted(p.name for p in assets.iterdir()) == [
        "sheet-Sales-Costs-chart01.xml", "sheet-Sales-Costs-img01.png", "sheet-Trend-chart01.xml",
    ]
    sales = _sheet(text, "Sales & Costs")
    assert "![](finance_assets/sheet-Sales-Costs-img01.png)" in sales
    assert "**Chart: Revenue by Quarter (column chart)**" in sales
    assert REVENUE_TABLE in sales
    assert "[Chart definition](finance_assets/sheet-Sales-Costs-chart01.xml)" in sales
    trend = _sheet(text, "Trend")
    assert "**Chart: Visitors (line chart)**" in trend
    assert "| Jan | 100 |" in trend


def test_hidden_sheets_are_included(run, tmp_path):
    source = sample_set.build_workbook(tmp_path)

    run(source)

    assert "Internal only" in _sheet((tmp_path / "finance.md").read_text(encoding="utf-8"), "Hidden Notes")


def test_powerpoint_chart_is_named_by_slide_and_replaces_markitdowns_table(run, tmp_path):
    source = sample_set.build_slides_with_chart(tmp_path)

    run(source)

    text = (tmp_path / "metrics.md").read_text(encoding="utf-8")
    slide_two = text.split("<!-- Slide number: 2 -->", 1)[1]
    assert "**Chart: Revenue by Quarter (column chart)**" in slide_two
    assert REVENUE_TABLE in slide_two
    assert "[Chart definition](metrics_assets/slide02-chart01.xml)" in slide_two
    assert "### Chart" not in text
    assert "\nSource: finance" in slide_two
    assert (tmp_path / "metrics_assets" / "slide02-chart01.xml").exists()
