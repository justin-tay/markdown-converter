"""Build an Offline Bundle so Setup can run on a machine with no internet access.

Run on an internet-connected machine (any platform can build any bundle):

    python tools/build_offline_bundle.py                      # every platform
    python tools/build_offline_bundle.py windows-x64          # one platform
    python tools/build_offline_bundle.py macos-arm64 --python 3.13

Each bundle is a folder of wheels under offline-bundle/<platform>/ covering
every package in that platform's lock file, for each supported Python version
(or the versions given). Copy the repository together with offline-bundle/ to
the target machine; the launchers install from the bundle automatically.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUNDLE_ROOT = REPO / "offline-bundle"


@dataclass(frozen=True)
class Target:
    lock_file: Path
    python_versions: tuple[str, ...]
    # pip doesn't widen --platform to older compatible tags, so list them all.
    tags: tuple[str, ...]


def _mac_tags(machine: str, oldest: tuple[int, int]) -> tuple[str, ...]:
    versions = [(15, 0), (14, 0), (13, 0), (12, 0), (11, 0)]
    versions += [(10, minor) for minor in range(15, oldest[1] - 1, -1)] if oldest[0] == 10 else []
    tags = [f"macosx_{major}_{minor}_{machine}" for major, minor in versions]
    return tuple(tags + [f"macosx_{major}_{minor}_universal2" for major, minor in versions])


TARGETS = {
    "windows-x64": Target(REPO / "requirements.lock", ("3.12", "3.13", "3.14"), ("win_amd64",)),
    "macos-arm64": Target(REPO / "requirements.lock", ("3.12", "3.13", "3.14"), _mac_tags("arm64", (11, 0))),
    # onnxruntime has no Intel-Mac wheels for Python 3.14 (see requirements-macos-x64.lock).
    "macos-x64": Target(REPO / "requirements-macos-x64.lock", ("3.12", "3.13"), _mac_tags("x86_64", (10, 9))),
    "linux-x86_64": Target(
        REPO / "requirements.lock",
        ("3.12", "3.13", "3.14"),
        tuple(f"manylinux_2_{minor}_x86_64" for minor in range(39, 4, -1)) + ("manylinux2014_x86_64",),
    ),
}


def build(platform: str, python_versions: list[str] | None) -> Path:
    target = TARGETS[platform]
    destination = BUNDLE_ROOT / platform
    destination.mkdir(parents=True, exist_ok=True)
    for version in python_versions or target.python_versions:
        print(f"Downloading wheels for {platform}, Python {version}...", flush=True)
        command = [
            sys.executable, "-m", "pip", "download",
            "--disable-pip-version-check", "--quiet",
            # The lock file pins every package, so no resolving is needed. Resolving
            # would also judge version markers by this machine's Python, not the target's.
            "--no-deps",
            "--requirement", str(target.lock_file),
            "--dest", str(destination),
            "--only-binary=:all:",
            "--implementation", "cp",
            "--python-version", version,
        ]
        for tag in target.tags:
            command += ["--platform", tag]
        subprocess.run(command, check=True)
    return destination


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("platforms", nargs="*", metavar="PLATFORM",
                        help=f"one or more of: {', '.join(TARGETS)} (default: all)")
    parser.add_argument("--python", nargs="+", metavar="VERSION",
                        help="Python versions the target machines use (default: every supported one)")
    options = parser.parse_args(argv)
    unknown = [p for p in options.platforms if p not in TARGETS]
    if unknown:
        parser.error(f"unknown platform {', '.join(unknown)}; choose from {', '.join(TARGETS)}")
    for platform in options.platforms or list(TARGETS):
        folder = build(platform, options.python)
        print(f"  {len(list(folder.glob('*.whl')))} wheels in {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
