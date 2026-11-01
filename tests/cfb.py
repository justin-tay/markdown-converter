"""Minimal Compound File Binary (OLE) writer, enough to build Outlook .msg samples.

Writes a version 3 file (512-byte sectors). Every stream must be smaller than
4096 bytes so it lives in the mini stream. Paths use "/" for storages, e.g.
"__attach_version1.0_#00000000/__substg1.0_3707001F".
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

SECTOR = 512
MINI_SECTOR = 64
MINI_CUTOFF = 4096
FREESECT = 0xFFFFFFFF
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
NOSTREAM = 0xFFFFFFFF
STORAGE, STREAM, ROOT = 1, 2, 5


class _Entry:
    def __init__(self, name: str, kind: int, data: bytes = b""):
        self.name, self.kind, self.data = name, kind, data
        self.children: list[_Entry] = []
        self.id = 0
        self.left = self.right = self.child = NOSTREAM
        self.start, self.size = ENDOFCHAIN, 0

    def sort_key(self):
        return (len(self.name), self.name.upper())


def write(path: Path, streams: dict[str, bytes]) -> None:
    root = _Entry("Root Entry", ROOT)
    for stream_path, data in streams.items():
        if len(data) >= MINI_CUTOFF:
            raise ValueError(f"{stream_path} is too large for this minimal writer")
        *storages, name = stream_path.split("/")
        parent = root
        for storage in storages:
            match = next((c for c in parent.children if c.name == storage), None)
            if match is None:
                match = _Entry(storage, STORAGE)
                parent.children.append(match)
            parent = match
        parent.children.append(_Entry(name, STREAM, data))

    entries = _flatten(root)

    # Mini stream: every stream, padded to whole mini sectors, chained in the MiniFAT.
    mini_stream, minifat = bytearray(), []
    for entry in entries:
        if entry.kind != STREAM:
            continue
        count = max(1, math.ceil(len(entry.data) / MINI_SECTOR))
        entry.start, entry.size = len(minifat), len(entry.data)
        minifat.extend(range(entry.start + 1, entry.start + count))
        minifat.append(ENDOFCHAIN)
        mini_stream += entry.data.ljust(count * MINI_SECTOR, b"\0")

    directory = b"".join(_directory_entry(e) for e in entries)
    directory = directory.ljust(math.ceil(len(directory) / SECTOR) * SECTOR, b"\0")
    minifat_bytes = _pad(b"".join(struct.pack("<I", v) for v in minifat), FREESECT)
    mini_bytes = mini_stream.ljust(max(SECTOR, math.ceil(len(mini_stream) / SECTOR) * SECTOR), b"\0")

    regions = [len(directory) // SECTOR, len(minifat_bytes) // SECTOR, len(mini_bytes) // SECTOR]
    fat_sectors = 1
    while fat_sectors * (SECTOR // 4) < sum(regions) + fat_sectors:
        fat_sectors += 1

    fat, starts, next_sector = [], [], 0
    for size in regions:
        starts.append(next_sector)
        fat.extend(range(next_sector + 1, next_sector + size))
        fat.append(ENDOFCHAIN)
        next_sector += size
    fat_start = next_sector
    fat.extend([FATSECT] * fat_sectors)
    fat.extend([FREESECT] * (fat_sectors * (SECTOR // 4) - len(fat)))
    fat_bytes = b"".join(struct.pack("<I", v) for v in fat)

    # The root entry owns the mini stream; rewrite its record now its start is known.
    root.start, root.size = starts[2], len(mini_stream)
    directory = _directory_entry(root) + directory[128:]

    header = bytearray(SECTOR)
    header[0:8] = bytes.fromhex("D0CF11E0A1B11AE1")
    struct.pack_into("<HHHHH", header, 24, 0x3E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<IIIIIIIII", header, 40,
                     0, fat_sectors, starts[0], 0, MINI_CUTOFF,
                     starts[1], len(minifat_bytes) // SECTOR, ENDOFCHAIN, 0)
    difat = [fat_start + i for i in range(fat_sectors)] + [FREESECT] * (109 - fat_sectors)
    struct.pack_into("<109I", header, 76, *difat)

    path.write_bytes(bytes(header) + directory + minifat_bytes + mini_bytes + fat_bytes)


def _flatten(root: _Entry) -> list[_Entry]:
    """Number entries and link each storage's children as a right-leaning chain."""
    entries, pending = [root], [root]
    while pending:
        storage = pending.pop(0)
        children = sorted(storage.children, key=_Entry.sort_key)
        for child in children:
            child.id = len(entries)
            entries.append(child)
        if children:
            storage.child = children[0].id
            for current, following in zip(children, children[1:]):
                current.right = following.id
        pending.extend(c for c in children if c.kind == STORAGE)
    return entries


def _directory_entry(entry: _Entry) -> bytes:
    name = entry.name.encode("utf-16-le") + b"\0\0"
    record = bytearray(128)
    record[0:len(name)] = name
    struct.pack_into("<HBB", record, 64, len(name), entry.kind, 1)  # 1 = black
    struct.pack_into("<III", record, 68, entry.left, entry.right, entry.child)
    struct.pack_into("<II", record, 116, entry.start, entry.size)
    return bytes(record)


def _pad(data: bytes, filler: int) -> bytes:
    sectors = max(1, math.ceil(len(data) / SECTOR))
    return data + struct.pack("<I", filler) * ((sectors * SECTOR - len(data)) // 4)
