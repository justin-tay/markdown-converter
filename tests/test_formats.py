"""Every Supported Format without Assets converts to a Converted Document."""

from __future__ import annotations

import pytest
import sample_set


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (sample_set.build_xls, "| Laptops | 1200 |"),
        (sample_set.build_msg, "**Subject:** Budget review"),
        (sample_set.build_zip, "| North | 10 | 12 |"),
        (sample_set.build_xml, '<item sku="B2">Gadget</item>'),
        (sample_set.build_text_epub, "It was a quiet quarter."),
        (sample_set.build_text_pdf, "Project brief page two"),
    ],
)
def test_format_converts(run, tmp_path, build, expected):
    source = build(tmp_path)

    result = run(source)

    assert result.exit_code == 0
    assert expected in source.with_suffix(".md").read_text(encoding="utf-8")


def test_zip_output_does_not_reveal_the_users_folder_names(run, tmp_path):
    source = sample_set.build_zip(tmp_path)

    run(source)

    assert str(tmp_path) not in source.with_suffix(".md").read_text(encoding="utf-8")
