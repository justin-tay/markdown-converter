"""Launcher smoke tests (ticket 13, Seam 3).

These run the real launcher scripts as subprocesses. The first run performs
Setup (creating .venv from requirements.lock), so they can be slow. Double-click,
drag-and-drop and Finder launches are manual demonstrations (see
docs/acceptance/manual-demonstrations.md).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import sample_set

REPO = Path(__file__).resolve().parent.parent

if sys.platform == "win32":
    LAUNCHER = [str(REPO / "convert.cmd")]
else:
    LAUNCHER = ["bash", str(REPO / "convert.sh")]


def _launch(*args, stdin: str = ""):
    env = {**os.environ, "MARKDOWN_CONVERTER_NO_PAUSE": "1"}
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [*LAUNCHER, *map(str, args)],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=900,
    )


@pytest.mark.launcher
def test_launcher_converts_the_target_and_passes_options_through(tmp_path):
    folder = tmp_path / "folder with spaces"
    folder.mkdir()
    source = sample_set.build_csv(folder)

    completed = _launch(source, "--no-front-matter")

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert source.with_suffix(".md").read_text(encoding="utf-8").startswith("| Region |")


@pytest.mark.launcher
def test_launcher_returns_the_converters_exit_code(tmp_path):
    completed = _launch(tmp_path / "missing.pdf")

    assert completed.returncode == 2, completed.stdout + completed.stderr
    assert "does not exist" in completed.stdout


@pytest.mark.launcher
def test_launcher_asks_for_a_target_when_none_is_given(tmp_path):
    source = sample_set.build_csv(tmp_path)

    completed = _launch(stdin=f"{source}\n")

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "File or folder to convert:" in completed.stdout
    assert source.with_suffix(".md").exists()
