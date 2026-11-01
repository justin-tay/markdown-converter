"""The Offline Guard (ADR 0001): no network access during a Conversion Run."""

from __future__ import annotations

import socket
import subprocess
import sys

import pytest
import sample_set
from markitdown import DocumentConverter, DocumentConverterResult

from markdown_converter import formats


class _PhoningHomeConverter(DocumentConverter):
    """Test-only converter that tries to reach the internet mid-conversion."""

    def convert(self, file_stream, stream_info, **kwargs):
        socket.create_connection(("example.com", 443), timeout=5)
        return DocumentConverterResult(markdown="should never be written")


def test_selftest_reports_that_network_access_is_blocked(run):
    result = run("--selftest-offline")

    assert result.exit_code == 0
    assert "PASS: network access is blocked during conversion" in result.output


def test_network_attempt_fails_that_source_file(run, tmp_path, monkeypatch):
    monkeypatch.setitem(formats._CONVERTER_BY_EXTENSION, ".csv", _PhoningHomeConverter)
    source = sample_set.build_csv(tmp_path)

    result = run(source)

    assert result.exit_code == 1
    assert "[1/1] sales.csv … failed (network access blocked)" in result.output
    assert not (tmp_path / "sales.md").exists()


def test_network_attempt_fails_the_file_even_if_the_library_swallows_the_error(
    run, tmp_path, monkeypatch
):
    class _SwallowingConverter(DocumentConverter):
        def convert(self, file_stream, stream_info, **kwargs):
            try:
                socket.getaddrinfo("example.com", 443)
            except OSError:
                pass
            return DocumentConverterResult(markdown="converted anyway")

    monkeypatch.setitem(formats._CONVERTER_BY_EXTENSION, ".csv", _SwallowingConverter)
    source = sample_set.build_csv(tmp_path)

    result = run(source)

    assert result.exit_code == 1
    assert "failed (network access blocked)" in result.output


@pytest.mark.parametrize(
    "url", ["https://example.com/a.pdf", "http://intranet/report.docx", "ftp://host/file.csv"]
)
def test_web_address_target_is_refused(run, url):
    result = run(url)

    assert result.exit_code == 2
    assert "local files only" in result.output


def test_guard_is_in_place_before_markitdown_is_imported():
    """Importing the entry point must not import markitdown, so main can guard first."""
    probe = (
        "import sys, markdown_converter.cli; "
        "sys.exit('markitdown' in sys.modules)"
    )
    completed = subprocess.run([sys.executable, "-c", probe])

    assert completed.returncode == 0
