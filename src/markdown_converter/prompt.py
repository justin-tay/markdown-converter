"""The Interactive Prompt, used when the converter is started without a Target."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from markdown_converter.offline import is_web_address

QUESTION = "File or folder to convert: "


def ask_for_target(stdin: TextIO, stdout: TextIO) -> str | None:
    """Ask until the answer is an existing path; None if input ends first.

    Accepts paths pasted with surrounding quotes (Windows "Copy as path") and
    with backslash-escaped spaces (dragging into macOS Terminal).
    """
    while True:
        stdout.write(QUESTION)
        stdout.flush()
        line = stdin.readline()
        if not line:
            stdout.write("\n")
            return None
        answer = _clean(line)
        if not answer:
            continue
        if is_web_address(answer) or Path(answer).exists():
            return answer  # web addresses are refused with a clear message later
        stdout.write(f"{answer} does not exist. Please try again.\n")


def confirm_folder(stdin: TextIO, stdout: TextIO, count: int) -> bool:
    files = "file" if count == 1 else "files"
    stdout.write(f"Found {count} supported {files}, convert? [Y/n] ")
    stdout.flush()
    answer = stdin.readline()
    if not answer:
        stdout.write("\n")
        return False  # input ended: don't convert without a yes
    return answer.strip().lower() not in ("n", "no")


def _clean(line: str) -> str:
    answer = line.strip()
    if len(answer) >= 2 and answer[0] == answer[-1] and answer[0] in "\"'":
        answer = answer[1:-1].strip()
    if not Path(answer).exists() and "\\ " in answer:
        answer = answer.replace("\\ ", " ")
    return answer
