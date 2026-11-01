"""Fail when any runtime dependency is not permissively licensed (StR-072, ADR 0003).

Checks the packages pinned in a lock file (requirements.lock by default), as
installed in the current environment:

    python tools/check_licences.py [requirements-macos-x64.lock]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_LOCK_FILE = Path(__file__).resolve().parent.parent / "requirements.lock"

PERMISSIVE = re.compile(
    r"MIT|BSD|0BSD|Apache|ISC|Zlib|CC0|PSF|Python Software Foundation|MIT-CMU|HPND",
    re.IGNORECASE,
)

# Non-permissive packages accepted in ADR 0003, each with the reason it
# is accepted. Keep this list short and explained.
REVIEWED_EXCEPTIONS = {
    # Transitive dependency of markitdown via requests. MPL-2.0 is file-level
    # copyleft: only changes to certifi's own files must be shared.
    "certifi": "MPL-2.0, unmodified transitive dependency of markitdown (requests)",
}


def pinned_packages(lock_file: Path) -> list[str]:
    names = []
    for line in lock_file.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.append(re.split(r"[=<>;\s]", line, maxsplit=1)[0])
    return names


def is_permissive(licence: str) -> bool:
    """True when every alternative ("OR") or component ("AND") is permissive."""
    licence = licence.replace("dependency licenses", "")
    parts = [p for p in re.split(r"\s+(?:AND|OR)\s+|[;,]", licence) if p.strip()]
    return bool(parts) and all(PERMISSIVE.search(part) for part in parts)


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main(lock_file: Path) -> int:
    packages = pinned_packages(lock_file)
    report = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json", "--packages", *packages],
        check=True,
        capture_output=True,
        text=True,
    )
    entries = json.loads(report.stdout)
    reported = {_normalise(entry["Name"]) for entry in entries}
    problems = [
        f"{name}: not installed, so its licence could not be checked"
        for name in packages
        if _normalise(name) not in reported
    ]
    for entry in entries:
        name, licence = entry["Name"], entry["License"]
        if name.lower() in REVIEWED_EXCEPTIONS:
            print(f"accepted   {name}: {REVIEWED_EXCEPTIONS[name.lower()]}")
        elif is_permissive(licence):
            print(f"permissive {name}: {licence}")
        else:
            problems.append(f"{name}: {licence}")
    for problem in problems:
        print(f"NOT ALLOWED {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LOCK_FILE))
