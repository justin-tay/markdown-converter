"""Entry point for a Conversion Run: the launchers and the tests both call `main`."""

from __future__ import annotations

import argparse
import logging
import warnings
from pathlib import Path
from typing import Sequence, TextIO

from markdown_converter import offline

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2


def main(argv: Sequence[str], stdin: TextIO, stdout: TextIO) -> int:
    # The Offline Guard goes in before any converter library is imported (ADR 0001).
    offline.install()
    # Library deprecation notices and parser chatter (e.g. pdfminer's "CropBox
    # missing") mean nothing to a Document User; real problems reach the Run Summary.
    warnings.simplefilter("ignore")
    for library in ("pdfminer", "pypdf", "pdfplumber", "markitdown"):
        logging.getLogger(library).setLevel(logging.ERROR)
    from markdown_converter.discovery import LOG_FILE_NAME, Discovery, discover
    from markdown_converter.documents import SkippedError, convert_document
    from markdown_converter.options import ConversionOptions
    from markdown_converter.formats import SUPPORTED_FORMAT_NAMES, is_supported
    from markdown_converter.planner import plan_outputs
    from markdown_converter.prompt import ask_for_target, confirm_folder
    from markdown_converter.run_summary import RunSummary

    parser = _parser()
    try:
        options = parser.parse_args(argv)
    except _UsageError as error:
        stdout.write(f"Error: {error}\n")
        return EXIT_USAGE
    if options.help:
        stdout.write(parser.format_help())
        return EXIT_OK
    if options.selftest_offline:
        if offline.self_test():
            stdout.write("PASS: network access is blocked during conversion\n")
            return EXIT_OK
        stdout.write("FAIL: a network connection was not blocked\n")
        return EXIT_FAILED
    prompted = options.target is None
    if prompted:
        options.target = ask_for_target(stdin, stdout)
        if options.target is None:
            stdout.write("Error: no file or folder to convert was given. See --help.\n")
            return EXIT_USAGE
    if offline.is_web_address(options.target):
        stdout.write(f"Error: {options.target} is a web address; the converter accepts local files only.\n")
        return EXIT_USAGE
    target = Path(options.target)
    if not target.exists():
        stdout.write(f"Error: {target} does not exist.\n")
        return EXIT_USAGE
    output = Path(options.output) if options.output else None
    if output is not None:
        try:
            output.mkdir(parents=True, exist_ok=True)
        except OSError:
            stdout.write(f"Error: the output folder {output} can't be created (is it a file?).\n")
            return EXIT_USAGE

    neighbours: list[Path] = []
    if target.is_dir():
        found = discover(target, options.recurse, is_supported, exclude=output)
        root = target
        # Only a folder typed at the prompt is confirmed; arguments (and drag-and-drop) are not.
        if prompted and not confirm_folder(stdin, stdout, len(found.source_files)):
            stdout.write("Nothing was converted.\n")
            return EXIT_OK
    elif is_supported(target):
        found, root = Discovery(source_files=[target]), target.parent
        # Name Collisions depend on the files beside a single-file Target too.
        neighbours = [p for p in discover(root, False, is_supported).source_files if p != target]
    else:
        stdout.write(
            f"Error: {target.name} is not a Supported Format. "
            f"Supported Formats: {', '.join(SUPPORTED_FORMAT_NAMES)}.\n"
        )
        return EXIT_USAGE

    conversion = ConversionOptions(options.front_matter, options.min_image_size, options.pdf_page_images)
    summary = RunSummary(stdout, total=len(found.source_files))
    summary.ignored = len(found.ignored)
    for plan in plan_outputs(found.source_files, root, output, neighbours):
        name = plan.source.relative_to(root).as_posix()
        if plan.collides_with:
            summary.warn(name, f"Name Collision with {', '.join(plan.collides_with)}, so outputs keep their extension")
        if plan.up_to_date and not options.force:
            summary.up_to_date_file(name)
            continue
        try:
            plan.converted.parent.mkdir(parents=True, exist_ok=True)
            file_warnings = convert_document(plan.source, plan.converted, conversion)
        except SkippedError as skip:
            summary.skipped_file(name, str(skip))
        except Exception as error:  # any library failure fails only this Source File
            summary.failed_file(name, _reason(error))
        else:
            summary.converted_file(name)
            for warning in file_warnings:
                summary.warn(name, warning)
    return EXIT_OK if summary.finish((output or root) / LOG_FILE_NAME) else EXIT_FAILED


def _reason(error: Exception) -> str:
    lines = str(error).strip().splitlines()
    return lines[0] if lines else type(error).__name__


class _UsageError(Exception):
    pass


def _pixels(value: str) -> int:
    if not value.isdigit() or int(value) < 1:
        raise argparse.ArgumentTypeError(f"expected a whole number of pixels, got {value!r}")
    return int(value)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        raise _UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="convert",
        description="Convert documents to Markdown, entirely offline.",
        add_help=False,
    )
    parser.add_argument("target", nargs="?", help="file or folder to convert")
    parser.add_argument(
        "--output",
        metavar="FOLDER",
        help="write Converted Documents to FOLDER, mirroring the Target's subfolders",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="reconvert every file, even ones that are Up To Date",
    )
    parser.add_argument(
        "--no-recurse",
        dest="recurse",
        action="store_false",
        help="convert only the files directly in the folder, not its subfolders",
    )
    parser.add_argument(
        "--no-front-matter",
        dest="front_matter",
        action="store_false",
        help="leave out the front matter header describing the Source File",
    )
    parser.add_argument(
        "--min-image-size",
        type=_pixels,
        metavar="PX",
        help="skip images narrower or shorter than PX pixels (e.g. icons)",
    )
    parser.add_argument(
        "--pdf-page-images",
        action="store_true",
        help="also save a 150 DPI picture of every PDF page, capturing vector charts",
    )
    parser.add_argument(
        "--selftest-offline",
        action="store_true",
        help="check that network access is blocked during conversion, then exit",
    )
    parser.add_argument("--help", action="store_true", help="show this help and exit")
    return parser
