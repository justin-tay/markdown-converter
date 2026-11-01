from __future__ import annotations

import io
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from markdown_converter.cli import main  # noqa: E402


@dataclass
class RunResult:
    exit_code: int
    output: str


@pytest.fixture
def run():
    """Call the converter's entry point in-process, as the launchers do."""

    def _run(*args: str | Path, stdin: str = "") -> RunResult:
        stdout = io.StringIO()
        exit_code = main([str(a) for a in args], io.StringIO(stdin), stdout)
        return RunResult(exit_code, stdout.getvalue())

    return _run
