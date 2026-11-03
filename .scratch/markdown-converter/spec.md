# Spec: Offline Markdown Converter

Status: ready-for-agent

Requirements source: `docs/requirements/stakeholder-requirements-specification.md` (StR-nnn IDs referenced below). Vocabulary: `GLOSSARY.md`. Decisions: `docs/adr/0001`–`0005`.

## Problem Statement

People hold large collections of PDFs, Word, PowerPoint and Excel files (and similar) whose content they want to read, search, diff, or feed to AI models and RAG pipelines. Converting them by hand is slow; existing tools either lose the images and charts, or send confidential documents to online services. Non-programmers also need to be able to run the conversion by double-clicking or dragging a folder, on both Windows and macOS, without admin rights.

## Solution

A local converter, built on markitdown, that takes a Target (one file or a folder tree) and produces, beside each Source File, a Converted Document (`<name>.md`) and, when there is anything to save, an Assets Folder (`<name>_assets/`) holding its Embedded Images, Chart Definitions and optional Page Snapshots. Charts also appear in the Converted Document as Chart Data Tables. An Offline Guard guarantees no network traffic during a Conversion Run. Launcher scripts for Windows (`convert.cmd`) and macOS/Linux (`convert.sh`, `convert.command`) take the Target as their first argument or prompt for it, perform one-time Setup automatically (online, or from an Offline Bundle), and end every run with a Run Summary.

## User Stories

### Starting a Conversion Run

1. As a Document User, I want to double-click `convert.cmd` on Windows and be asked which file or folder to convert, so that I don't need to use a terminal.
2. As a Document User, I want to drag a file or folder onto `convert.cmd`, so that I can convert it in one gesture.
3. As a Document User on macOS, I want to double-click `convert.command` in Finder, so that I get the same prompt-driven experience as on Windows.
4. As a Document User comfortable with a terminal, I want to pass the Target as the first argument to `convert.cmd` or `convert.sh`, so that I can script conversions.
5. As a Document User, I want to paste a path with or without surrounding quotes at the prompt, so that copying a path from Explorer or Finder just works.
6. As a Document User, I want to be asked again when the path I typed doesn't exist, so that a typo doesn't end the session.
7. As a Document User who typed a folder at the prompt, I want to be told how many Supported Files were found and asked to confirm, so that I don't accidentally convert a huge folder.
8. As a Document User who started the tool by double-click or drag-and-drop, I want the window to stay open at the end until I press a key, so that I can read the Run Summary.
9. As a Document User, I want `--help` to list every option with a one-line explanation, so that I can discover features without reading the source.
10. As a Document User, I want any option I give a launcher script passed straight through to the converter, so that scripts and direct use behave identically.

### Choosing what gets converted

11. As a Document User, I want to convert a single Source File by naming it, so that I can convert just what I need.
12. As a Document User, I want naming a folder to convert every Source File in it and its subfolders, so that I can convert a whole document library at once.
13. As a Document User, I want `--no-recurse` to limit conversion to the folder's own files, so that I can avoid subfolders when I need to.
14. As a Document User, I want PDF, DOCX, PPTX, XLSX, XLS, HTML/HTM, CSV, JSON, XML, EPUB, MSG and ZIP files converted, so that my usual document types are covered.
15. As a Document User, I want other files in a folder ignored and counted, so that the run isn't cluttered with errors about files I never expected to convert.
16. As a Document User, I want a clear message listing the Supported Formats if I name a single unsupported file, so that I understand why nothing happened.
17. As a Document User, I want hidden folders, Assets Folders, the converter's own Converted Documents and log file skipped, so that re-running never converts its own output.
18. As a Document User, I want symbolic links not followed, so that a link loop or a link to a huge share can't run away.
19. As a Document User, I want paths with spaces and non-English characters to work, so that real-world folder names don't break conversion.
20. As a Data Owner, I want a web address given as the Target refused, so that the tool can never be used to fetch content online.

### Converted Documents and where they go

21. As a Document User, I want each Converted Document written next to its Source File as `<name>.md`, so that I find it where I expect.
22. As a Document User, I want an Assets Folder only when there are Assets, so that simple files like CSVs don't leave empty folders.
23. As a Document User, I want both `report.pdf` and `report.docx` in the same folder to produce `report.pdf.md` and `report.docx.md`, so that neither silently overwrites the other.
24. As a Document User, I want Name Collisions listed in the Run Summary, so that I notice when output names include the extension.
25. As a Document User with read-only sources, I want `--output <folder>` to write everything to a separate folder that mirrors the Target's structure, so that I can convert from a share I can't write to.
26. As a Downstream Consumer, I want each Converted Document to keep the source's headings, lists and tables in UTF-8 Markdown, so that structure survives conversion.
27. As a Downstream Consumer, I want a short front-matter header giving source file name, source format, conversion date and converter version, so that I can trace every Converted Document back to its origin.
28. As a Document User, I want `--no-front-matter` to remove that header, so that I can produce clean Markdown when I don't want metadata.
29. As a Downstream Consumer, I want every Asset link to be relative, so that a Converted Document and its Assets Folder can be moved together without breaking links.

### Re-running

30. As a Document User, I want Source Files that are Up To Date skipped, so that re-running on a growing folder is fast.
31. As a Document User, I want `--force` to reconvert everything and replace each Converted Document and its whole Assets Folder, so that no stale Assets remain.
32. As a Document User, I want the converter never to modify, move, rename or delete a Source File, so that my originals are always safe.

### Images

33. As a Document User, I want Embedded Images in PDF, DOCX, PPTX and XLSX files saved into the Assets Folder in their original format, so that no visual content is lost or re-encoded.
34. As a Downstream Consumer, I want Word and PowerPoint image links placed where the image appeared, so that images keep their context in the text.
35. As a Downstream Consumer, I want PDF image links placed where their figure is tagged (or after the text of their page in untagged PDFs), so that images stay near the content they illustrate.
36. As a Downstream Consumer, I want Excel image links placed within the sheet's section, so that I know which sheet an image came from.
37. As a Document User, I want each Asset's name to say where it came from (`p003-img01.png`, `slide02-img01.png`, `sheet-Sales-chart01.xml`, `img01.png`), so that I can find the source location of any Asset at a glance.
38. As a Document User, I want an image that repeats with identical content (like a logo on every page) saved once and linked from every place, so that the Assets Folder isn't flooded with copies.
39. As a Document User, I want `--min-image-size <px>` to drop tiny icons and decorations, so that I can keep only meaningful images.
40. As a Document User, I want EMF/WMF images saved as-is with a warning that some viewers can't show them, so that nothing is lost and I know why an image may not display.

### Charts

41. As a Downstream Consumer, I want each Chart in a DOCX, PPTX or XLSX file to appear as a heading with its title and type followed by a Chart Data Table of its values, so that the chart's information is readable as text.
42. As a Document User, I want each Chart's original XML saved as a Chart Definition and linked, so that the chart can be re-rendered or inspected later.
43. As a Document User, I want a Chart whose values can't be read to still appear with its heading, a "data not extracted" note and its Chart Definition link, so that I know it existed.
44. As a Document User, I want `--pdf-page-images` to save a 150 DPI PNG Page Snapshot of every PDF page, linked straight after each Page Marker, so that vector charts in PDFs are captured visually.

### HTML, EPUB and other formats

45. As a Document User, I want images bundled in an EPUB copied into the Assets Folder and linked, so that e-book illustrations are kept.
46. As a Document User, I want images an HTML file references from my local disk copied into the Assets Folder with links rewritten, so that the Converted Document is self-contained.
47. As a Data Owner, I want images an HTML file references from the web left as text links and never downloaded, so that converting HTML can't leak anything.
48. As a Document User, I want the number of remote images not fetched reported in the Run Summary, so that I know some images are missing.
49. As a Document User, I want each ZIP converted into a single Converted Document, so that archives are still searchable.
50. As a Document User, I want an Outlook MSG's message body converted, so that emails are searchable.
51. As a Document User, I want a legacy XLS's cell data converted, so that old spreadsheets are usable even without their charts.

### Offline operation and data protection

52. As a Data Owner, I want every network connection blocked during a Conversion Run by the Offline Guard, not just by configuration, so that confidential content can't leave the machine even through a dependency.
53. As a Document User, I want a Source File whose conversion attempts a network connection to fail with "network access blocked" while the rest of the run continues, so that one bad file doesn't stop the batch.
54. As a Data Owner, I want markitdown's online features (URL/YouTube inputs, Azure services, AI image descriptions and OCR plugins, audio transcription) disabled, so that nothing in the toolchain is configured to go online.
55. As an Installer, I want `--selftest-offline` to show a clear PASS/FAIL that network access is blocked, so that I can prove offline operation to a Data Owner.
56. As a Data Owner, I want the documentation to say that speaker notes, hidden slides and hidden sheets appear in Converted Documents, so that I can judge what confidential content the output contains.

### Batch handling and reporting

57. As a Document User, I want one progress line per Source File (`[12/37] report.pdf … ok`), so that I can see the run advancing.
58. As a Document User, I want a failure on one Source File not to stop the run, so that a single damaged file doesn't waste the whole batch.
59. As a Document User, I want a Run Summary with counts of converted, Up To Date, failed and ignored files, each failure or skip reason, and all warnings, so that I know exactly what happened.
60. As a Document User, I want encrypted files skipped with the reason "encrypted", so that I know to unlock them rather than suspecting a bug.
61. As a Document User, I want damaged files reported as failed with a reason, so that I can find and fix them.
62. As a Document User, I want a "no text layer found" warning for scanned PDFs, with their page images still extracted, so that I know OCR would be needed.
63. As a Document User or script author, I want exit code 0 when everything converted or was Up To Date, 1 when any file failed, and 2 for invalid usage, so that scripts can react.
64. As a Document User, I want a `markdown-converter.log` written to the output root, so that I have a record after the window closes.
65. As a Document User converting a read-only folder without `--output`, I want the run to continue with a warning when the log can't be written, so that a log problem never blocks conversion.

### Setup and distribution

66. As an Installer, I want a friendly message explaining how to install Python 3.12–3.14 when it's missing, so that a non-programmer isn't faced with a cryptic error.
67. As a Document User, I want the first run to perform Setup automatically, so that I don't need separate install steps.
68. As a Document User, I want later runs to skip Setup, so that they start quickly.
69. As an Installer, I want to build an Offline Bundle for Windows x64, macOS arm64 and macOS x64 on an internet-connected machine, so that I can set up air-gapped machines.
70. As an Installer, I want Setup to complete from the Offline Bundle with networking disabled, so that air-gapped machines are supported.
71. As a Maintainer, I want every dependency version pinned, so that every installation produces the same output.
72. As an Installer, I want to get the tool by cloning the repo or downloading a ZIP, so that no package registry account is needed.
73. As an Installer, I want neither Setup nor conversion to need administrator rights, so that standard users can run it.
74. As a Maintainer, I want only permissively licensed dependencies, with any exception recorded and justified, so that the tool can be shared or embedded freely.
75. As a Document User on Linux, I want `convert.sh` to work, so that I can use it on Linux too.

## Implementation Decisions

### Shape

- Python package (`markdown_converter`), Python 3.12–3.14, run as `python -m markdown_converter`. Launchers are thin wrappers that ensure Setup and forward all arguments.
- A single in-process entry point — `main(argv, stdin, stdout) -> exit code` — owns the whole Conversion Run. The launchers and the test suite both call exactly this. This is the primary test seam.

### Modules (deep, small interfaces)

- **Offline Guard** — `install()` and `self_test() -> bool`. Installed as the first action of `main`, *before* markitdown or any converter library is imported. Replaces socket connect / connect_ex / create_connection / getaddrinfo (and equivalents) so that any non-loopback connection or DNS lookup raises a dedicated "network access blocked" error. Sets library offline flags (e.g. `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`) and clears proxy variables. Loopback/AF_UNIX stays allowed so local IPC doesn't break. (ADR 0001)
- **Target Resolver / Discovery** — turns the Target into an ordered list of Source Files, applying: Supported Format by extension, recursion vs `--no-recurse`, skipping hidden folders, Assets Folders, Converted Documents and the log file, not following symlinks, refusing URL Targets, and counting ignored files.
- **Output Planner** — for each Source File decides the Converted Document path and Assets Folder path: beside the source by default or mirrored under `--output`; detects Name Collisions per folder and gives *every* colliding file its extension in the output name (ADR 0005); marks files Up To Date when the Converted Document's modification time is newer than the Source File's, unless `--force`.
- **Document Converter** — `convert(source, plan, options) -> ConversionResult` (status: converted / failed / skipped-encrypted; reason; warnings; Assets written). Runs markitdown with all online features off (no LLM client, no Azure endpoints, plugins disabled, no URL inputs) and `keep_data_uris` on, then hands the Markdown plus the Source File to a format-specific Asset Extractor. Writes the Converted Document only after extraction succeeds; on `--force` the Assets Folder is removed and rebuilt.
- **Asset Extractors** (one per format family, same interface):
  - *PDF* — one continuous document with hidden Page Markers, its structure taken from a Tagged PDF's tags or, failing that, from layout rules, with Page Furniture left out (ADR 0008); Embedded Images via pypdf, linked where their figure is tagged or else after their page's text; Figure Snapshots of tagged vector figures; Page Snapshots via pypdfium2 at 150 DPI when `--pdf-page-images`, linked straight after each Page Marker; "no text layer found" warning when no page has text; encrypted PDFs reported as skipped-encrypted. (ADR 0003)
  - *DOCX / PPTX* — markitdown's inline data-URI images are replaced by Asset links at the same position (giving inline placement); images missing from markitdown's output are taken from the package's media parts; Charts are read from the package's chart parts.
  - *XLSX* — images and Charts read from the package's drawing and chart parts and linked within the owning sheet's section.
  - *HTML* — local image references copied into Assets and rewritten; remote references left untouched and counted.
  - *EPUB* — bundled images copied into Assets and links rewritten.
  - *XLS, CSV, JSON, XML, MSG, ZIP* — markitdown output only, no Assets.
  - Encrypted Office files (which are not ZIP packages) are detected and reported as skipped-encrypted.
- **Chart Reader** — parses a chart XML part into title, chart type and a table of category × series values; on any parse failure returns "data not extracted" with title/type when available. The raw chart XML is always saved as the Chart Definition. If markitdown already emitted a chart table (PPTX), the Chart Reader's output replaces it so all formats look identical. (ADR 0002)
- **Asset Store** — one per Converted Document. Accepts bytes plus a location hint, dedupes by content hash (identical content → one file, every link points at it), applies `--min-image-size`, keeps the original extension, and generates Asset Names: `p{page:03}-img{n:02}`, `slide{n:02}-img{n:02}` / `slide{n:02}-chart{n:02}`, `sheet-{SheetName}-img{n:02}` / `-chart{n:02}`, `img{n:02}` / `chart{n:02}` for Word. Sheet names are sanitised for file systems. Returns relative links. Flags EMF/WMF Assets for a warning.
- **Markdown Assembler** — prepends YAML front matter (`source`, `format`, `converted` as ISO 8601, `converter_version`) unless `--no-front-matter`, and lays out per-sheet sections, PDF Page Markers and Chart blocks:
  ```
  **Chart: <title> (<type> chart)**
  | <category> | <series 1> | … |
  [Chart definition](<name>_assets/<asset-name>.xml)
  ```
- **Run Reporter** — prints progress lines `[i/N] <relative path> … ok|skipped (<reason>)|failed (<reason>)`, accumulates warnings, prints the Run Summary, writes `markdown-converter.log` (overwritten each run) to the output root (the `--output` folder, else the Target folder, else the single file's folder), and falls back to screen-only with a warning if the log can't be written. Computes exit code 0 / 1 / 2.
- **Interactive Prompt** — used only when no Target argument is given: reads a path from `stdin`, strips surrounding quotes, re-prompts on nonexistent paths, and for folders shows "Found N supported files, convert? [Y/n]". Folders given as an argument (including drag-and-drop) are not confirmed.

### Options

`--output <folder>`, `--force`, `--no-recurse`, `--pdf-page-images`, `--min-image-size <px>`, `--no-front-matter`, `--selftest-offline`, `--help`. Invalid usage → exit 2.

### Launchers and Setup

- `convert.cmd` (Windows), `convert.sh` (macOS/Linux), `convert.command` (macOS Finder double-click, delegates to `convert.sh`).
- Each checks for Python 3.12–3.14 (friendly install guidance if missing), creates a private virtual environment inside the repo on first run, and installs pinned dependencies — from the Offline Bundle with no index access when one is present, otherwise from the internet. Setup is skipped once the environment matches the pinned dependency list.
- When launched without a terminal session (double-click / drag-and-drop), the launcher pauses at the end for a key press.
- A separate script builds the Offline Bundle (pre-downloaded wheels) per platform: Windows x64, macOS arm64, macOS x64.
- All dependency versions pinned, including markitdown at the latest release at implementation time; markitdown installed with only the extras needed for the Supported Formats (pdf, docx, pptx, xlsx, xls, outlook) — never the Azure, audio or YouTube extras.
- Dependencies limited to permissive licences, with exceptions recorded in ADR 0003 (currently certifi, MPL-2.0): markitdown, pypdf, pypdfium2, plus markitdown's own extras.

### Documentation

- README covering: install, double-click / drag-and-drop / terminal usage, options, offline guarantee and self-test, Offline Bundle, output layout and Name Collisions, hidden content disclosure (speaker notes, hidden slides and sheets included; Word comments/tracked changes not specifically handled), EMF/WMF caveat, and the known limitations from StRS Section 5.

## Testing Decisions

- **What makes a good test:** exercise the converter only through its public entry point and observe only what a user sees — files and folders on disk, Converted Document contents (links, Chart Data Tables, front matter, section layout), Run Summary and progress text, log file and exit code. No tests against internal module functions; refactoring internals must not break tests.
- **Seam 1 (primary) — `main(argv, stdin, stdout)` in-process:** each test copies the relevant Sample Set files into a temporary folder, calls `main`, and asserts on outcomes. Covers StR-001…StR-055 except launcher-only behaviour. The Interactive Prompt is tested by feeding `stdin`.
- **Seam 2 — Offline Guard via the same entry point:** `--selftest-offline` must report PASS. For StR-041, a test registers a test-only converter for one sample that attempts a socket connection, then asserts that file is reported "network access blocked", the others convert, and the exit code is 1. A whole-Sample-Set run asserts no connection attempt succeeded.
- **Seam 3 — launcher smoke tests:** run `convert.cmd` (on Windows) and `convert.sh` (on macOS/Linux) as subprocesses with a path and an option, assert the converter ran and the exit code propagated. Double-click, drag-and-drop, Finder launch and pause-at-end remain manual demonstrations per the StRS.
- **Sample Set (StRS §6.2, S-01…S-16):** a script generates samples deterministically using permissively licensed dev-only libraries (DOCX/PPTX/XLSX with images and charts, PDFs including vector-chart, scanned and encrypted, HTML, EPUB, CSV/JSON/XML, ZIP, damaged DOCX, the Name Collision pair and the S-16 folder tree with a hidden folder, an unsupported file and a subfolder with spaces and non-ASCII characters). Samples that can't be generated cleanly — Outlook MSG, legacy XLS, an EMF image — are committed as small binaries.
- **Platforms:** the full suite runs on Windows and macOS in CI (StR-070); Linux runs it as a Should.
- **Licence check:** an automated licence report over installed dependencies fails on any non-permissive licence (StR-072).
- **Prior art:** none — the repo has no code yet. These tests establish the pattern.

## Out of Scope

- Audio/video files, standalone image files, URLs and YouTube.
- OCR of scanned documents; AI-generated image descriptions; Azure Document Intelligence / Content Understanding.
- Rendering Office Charts as pictures (data + definition only).
- Assets from files inside ZIP archives; Outlook MSG attachments.
- Charts and images in legacy `.xls`.
- Choosing individual pages for Page Snapshots.
- The data behind PDF charts; finding figures, and tables without borders, in untagged PDFs; converting PDFs through Word or LibreOffice (ADR 0008).
- Converting EMF/WMF to PNG (StR-029, a Could — later).
- Special handling of Word comments and tracked changes.
- Graphical file picker; parallel conversion; per-file size limits or timeouts; non-English UI.

## Further Notes

- StRS open issues: minimum macOS version assumed 13; folder confirmation applies only to prompted Targets; pypdf's handling of unusual PDF image encodings (JBIG2, CCITT) must be checked against real samples — if unsupported, save the raw stream with a warning rather than failing the file.
- markitdown's internal output (PDF page handling, data-URI behaviour, PPTX chart tables) should be verified against the pinned version before relying on it; the extractors are designed so markitdown supplies text and the converter owns all Asset handling.
- Any feature needing the network is incompatible with the Offline Guard by design (ADR 0001) and must not become a default.
