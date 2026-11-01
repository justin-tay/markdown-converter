"""Check the converter's Word numbering labels against a reference rendering (ADR 0006).

    python tools/check_numbering.py DOCUMENT.docx [--reference FILE] [--libreoffice SOFFICE]

The reference is, best, a PDF that Word itself rendered (File > Save As > PDF),
or a text or PDF file from another renderer. Without --reference, the document
is rendered to text with LibreOffice, if it can be found.

Each numbered paragraph passes when the reference shows its label followed by
the start of its text, anywhere in the document, so repeated text elsewhere
doesn't cause false alarms. Paragraphs the converter left unnumbered are
reported when the reference only ever shows their text after a number.
Exits 1 when anything is reported. Developer tool: it runs LibreOffice, which
the converter's Offline Guard doesn't cover.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lxml import etree  # noqa: E402

from markdown_converter.word_numbering import _LABEL_MARKER, _W, _is_on, label_numbered_paragraphs  # noqa: E402

# How much of a paragraph's text must follow its label in the reference.
_TEXT_START = 30
# Shorter unnumbered paragraphs ("Yes", "Total") recur too often to judge.
_MIN_UNNUMBERED_TEXT = 20
_TIMEOUT_SECONDS = 300
_NUMBER_LABEL = re.compile(r"[(\[]?\d+(?:[.)]\d+)*[.)\]]?")
_MULTI_LEVEL_LABEL = re.compile(r"\d+(?:\.\d+)+\.?")
_SPACES = re.compile(r"\s+")
_COMMON_LOCATIONS = [
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "LibreOffice" / "program" / "soffice.exe",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "LibreOffice" / "program" / "soffice.exe",
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
]


@dataclass(frozen=True)
class Finding:
    paragraph: int  # position among the document's paragraphs, from 1
    converter_label: str
    reference_labels: list[str]  # what the reference shows before this text
    text: str

    def describe(self) -> str:
        shown = ", ".join(repr(label) for label in self.reference_labels) or "text not found"
        return (f"paragraph {self.paragraph}: converter {self.converter_label or '(none)'!r}, "
                f"reference {shown}: {self.text[:50]}")


def main(argv: Sequence[str], stdout: TextIO) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("document", type=Path)
    parser.add_argument("--reference", type=Path, help="PDF rendered by Word (best), or a text or PDF file")
    parser.add_argument("--libreoffice", type=Path, help="soffice to render with when there is no --reference")
    options = parser.parse_args(argv)
    if options.reference:
        lines = reference_lines(options.reference)
        reference_name = options.reference.name
    else:
        libreoffice = options.libreoffice or find_libreoffice()
        if libreoffice is None:
            stdout.write("LibreOffice not found: give --reference or --libreoffice.\n")
            return 2
        lines = _text_lines(render_with_libreoffice(libreoffice, options.document))
        reference_name = "LibreOffice"
    # A PDF line runs a table row's cells together, so cells can't be told apart:
    # table paragraphs are skipped, and only labels like 3.1 count as missed numbering.
    pdf = bool(options.reference) and options.reference.suffix.lower() == ".pdf"
    paragraphs, skipped = converter_paragraphs(options.document, skip_tables=pdf)
    findings = check(paragraphs, lines, multi_level_only=pdf)
    labelled = sum(1 for label, text in paragraphs if label and text.strip())
    stdout.write(f"{options.document.name} against {reference_name}: {labelled} labels checked, "
                 f"{len(findings)} finding(s)" + (f", {skipped} table paragraphs skipped" if skipped else "") + "\n")
    for finding in findings:
        stdout.write(f"  {finding.describe()}\n")
    return 1 if findings else 0


def check(paragraphs: list[tuple[str, str]], lines: list[str], multi_level_only: bool = False) -> list[Finding]:
    """Labels the reference doesn't show, and numbering the converter seems to have missed.

    With `multi_level_only`, missed numbering is only reported where the reference
    shows labels like 3.1, which table row numbers can't be mistaken for.
    """
    looks_numbered = _MULTI_LEVEL_LABEL if multi_level_only else _NUMBER_LABEL
    lines = [_normalise(line) for line in lines]
    findings = []
    for number, (label, text) in enumerate(paragraphs, start=1):
        text = _normalise(text)
        start = text[:_TEXT_START]
        if not start:
            continue
        if label:
            if not any(line.startswith(f"{label} {start}") for line in lines):
                findings.append(Finding(number, label, _labels_before(start, lines), text))
        elif len(text) >= _MIN_UNNUMBERED_TEXT:
            shown = _labels_before(start, lines)
            if shown and all(looks_numbered.fullmatch(label) for label in shown):
                findings.append(Finding(number, label, shown, text))
    return findings


def converter_paragraphs(document: Path, skip_tables: bool = False) -> tuple[list[tuple[str, str]], int]:
    """Every paragraph's (label the converter writes, visible text), in document order,
    and how many were skipped: with `skip_tables`, table paragraphs are left empty."""
    with zipfile.ZipFile(document) as package:
        names = set(package.namelist())
        labelled = label_numbered_paragraphs(
            package.read("word/document.xml"),
            package.read("word/numbering.xml") if "word/numbering.xml" in names else None,
            package.read("word/styles.xml") if "word/styles.xml" in names else None,
        )
    paragraphs, skipped = [], 0
    for paragraph in etree.fromstring(labelled).iter(f"{_W}p"):
        if skip_tables and any(ancestor.tag == f"{_W}tc" for ancestor in paragraph.iterancestors()):
            paragraphs.append(("", ""))
            skipped += 1
        else:
            paragraphs.append(_label_and_text(paragraph))
    return paragraphs, skipped


def _label_and_text(paragraph: etree._Element) -> tuple[str, str]:
    """(label, visible text) of a paragraph labelled by label_numbered_paragraphs.

    The text stops at the first footnote or endnote reference, whose number
    renderers print inside the text.
    """
    parts = []
    for run in paragraph.iter(f"{_W}r"):
        if _is_on(run.find(f"{_W}rPr/{_W}vanish")):
            continue
        if run.find(f"{_W}footnoteReference") is not None or run.find(f"{_W}endnoteReference") is not None:
            break
        for child in run.iter(f"{_W}t", f"{_W}tab"):
            parts.append(" " if child.tag == f"{_W}tab" else child.text or "")
    text = "".join(parts)
    marker = _LABEL_MARKER.match(text)
    return (marker.group(1), text[marker.end():]) if marker else ("", text)


def reference_lines(reference: Path) -> list[str]:
    if reference.suffix.lower() == ".pdf":
        import pdfplumber

        with pdfplumber.open(reference) as pdf:
            return [line["text"] for page in pdf.pages for line in page.extract_text_lines()]
    return _text_lines(_decode(reference.read_bytes()))


def find_libreoffice() -> Path | None:
    for name in ("soffice", "libreoffice"):
        if found := shutil.which(name):
            return Path(found)
    return next((path for path in _COMMON_LOCATIONS if path.is_file()), None)


def render_with_libreoffice(libreoffice: Path, document: Path) -> str:
    """The document as LibreOffice's plain text, using a throwaway profile."""
    with tempfile.TemporaryDirectory(prefix="check-numbering-") as folder:
        profile = Path(folder) / "profile"
        subprocess.run(
            [str(libreoffice), "--headless", "--norestore", "--nolockcheck",
             f"-env:UserInstallation={profile.as_uri()}",
             "--convert-to", "txt:Text (encoded):UTF8", "--outdir", folder, str(document)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=_TIMEOUT_SECONDS, check=False,
        )
        output = Path(folder) / f"{document.stem}.txt"
        if not output.is_file():
            raise SystemExit(f"LibreOffice did not render {document.name}")
        return _decode(output.read_bytes())


def _labels_before(start: str, lines: list[str]) -> list[str]:
    """What the reference shows in front of `start`, wherever that text begins."""
    found = []
    for line in lines:
        position = line.find(start)
        if position == 0 or (position > 0 and line[position - 1] == " "):
            label = line[:position].strip()
            if label not in found:
                found.append(label)
    return found


def _text_lines(text: str) -> list[str]:
    # LibreOffice puts a table row's cells on one line, separated by tabs; a tab
    # can also be part of a paragraph, so keep the whole line as well as its cells.
    lines = []
    for line in text.splitlines():
        lines.append(line.replace("\t", " "))
        if "\t" in line:
            lines.extend(line.split("\t"))
    return lines


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")  # older Windows LibreOffice builds


def _normalise(text: str) -> str:
    return _SPACES.sub(" ", text.replace("\u00a0", " ")).strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")  # Windows consoles can't show every symbol
    sys.exit(main(sys.argv[1:], sys.stdout))
