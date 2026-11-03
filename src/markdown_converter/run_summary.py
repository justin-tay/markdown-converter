"""The Run Summary of one Conversion Run: progress lines, final counts and the log file."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from markdown_converter import __version__


class RunSummary:
    def __init__(self, stdout: TextIO, total: int):
        self._stdout = stdout
        self._total = total
        self._position = 0
        self._lines: list[str] = []
        self.converted = self.up_to_date = self.skipped = self.failed = self.ignored = 0
        self._problems: list[str] = []
        self._warnings: list[str] = []
        self._notes: list[str] = []

    def converted_file(self, name: str) -> None:
        self.converted += 1
        self._progress(name, "ok")

    def up_to_date_file(self, name: str) -> None:
        self.up_to_date += 1
        self._progress(name, "up to date")

    def skipped_file(self, name: str, reason: str) -> None:
        self.skipped += 1
        self._problems.append(f"{name}: {reason}")
        self._progress(name, f"skipped ({reason})")

    def failed_file(self, name: str, reason: str) -> None:
        self.failed += 1
        self._problems.append(f"{name}: {reason}")
        self._progress(name, f"failed ({reason})")

    def warn(self, name: str, message: str) -> None:
        self._warnings.append(f"{name}: {message}")

    def note(self, name: str, message: str) -> None:
        """Something worth recording in the log but not showing on screen."""
        self._notes.append(f"{name}: {message}")

    def finish(self, log_path: Path) -> bool:
        """Print the Run Summary and write the log. True when every file converted."""
        self._say("")
        self._say("Run Summary")
        self._say(f"Converted: {self.converted}")
        self._say(f"Up To Date: {self.up_to_date}")
        self._say(f"Skipped: {self.skipped}")
        self._say(f"Failed: {self.failed}")
        self._say(f"Ignored: {self.ignored}")
        for heading, entries in (("Failed or skipped:", self._problems), ("Warnings:", self._warnings)):
            if entries:
                self._say("")
                self._say(heading)
                for entry in entries:
                    self._say(f"  {entry}")
        self._write_log(log_path)
        return not (self.failed or self.skipped)

    def _progress(self, name: str, outcome: str) -> None:
        self._position += 1
        self._say(f"[{self._position}/{self._total}] {name} … {outcome}")

    def _say(self, line: str) -> None:
        self._lines.append(line)
        self._stdout.write(line + "\n")

    def _write_log(self, log_path: Path) -> None:
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        header = f"Markdown Converter {__version__}, run finished {started}\n\n"
        notes = ["", "Notes:", *(f"  {note}" for note in self._notes)] if self._notes else []
        try:
            log_path.write_text(header + "\n".join(self._lines + notes) + "\n", encoding="utf-8")
        except OSError as error:
            self._stdout.write(f"\nWarning: could not write the log file {log_path} ({error.strerror or error}).\n")
