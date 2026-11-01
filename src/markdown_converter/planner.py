"""The Output Planner: where each Converted Document goes, and whether it's Up To Date."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Plan:
    source: Path
    converted: Path
    collides_with: list[str]

    @property
    def up_to_date(self) -> bool:
        # ">=": a quick conversion can land in the same timestamp tick as its source.
        return self.converted.exists() and self.converted.stat().st_mtime >= self.source.stat().st_mtime


def plan_outputs(
    source_files: list[Path],
    root: Path,
    output: Path | None,
    neighbours: list[Path] | None = None,
) -> list[Plan]:
    """Plan a Converted Document path per Source File (ADR 0005).

    Outputs sit beside their Source File, or under `output` mirroring the folders
    below `root`. Source Files that would share an output name (a Name Collision)
    all keep their extension: report.pdf -> report.pdf.md. `neighbours` are other
    Source Files in the same folders that aren't being converted this run (e.g.
    beside a single-file Target) but whose names must still be respected.
    """
    names = _output_names([*source_files, *(neighbours or [])])
    plans = []
    for source in source_files:
        folder = source.parent if output is None else output / source.parent.relative_to(root)
        name, others = names[source]
        plans.append(Plan(source, folder / name, others))
    return plans


def _output_names(sources: list[Path]) -> dict[Path, tuple[str, list[str]]]:
    """Each Source File's output name, and the files it collided with.

    Starts from <stem>.md and gives every file in a clash its extension
    (<name>.md) until no two files in a folder share a name. Full names can't
    clash, since no two files in a folder have the same name, so this ends.
    """
    names = {source: f"{source.stem}.md" for source in sources}
    collided: dict[Path, set[str]] = defaultdict(set)
    while True:
        # Lower-case: Windows and macOS file systems treat Report and report alike.
        by_name: dict[tuple[Path, str], list[Path]] = defaultdict(list)
        for source, name in names.items():
            by_name[(source.parent, name.lower())].append(source)
        clashes = [group for group in by_name.values() if len(group) > 1]
        if not clashes:
            break
        for group in clashes:
            for source in group:
                names[source] = f"{source.name}.md"
                collided[source].update(other.name for other in group if other != source)
    return {source: (names[source], sorted(collided[source])) for source in sources}
