# Markdown Converter

Turns documents (PDF, Word, PowerPoint, Excel and more) into Markdown files,
and saves the images and charts inside them alongside each Markdown file. It
runs on Windows, macOS and Linux, and **never uses the internet while
converting**, so confidential documents stay on your computer.

It is built on Microsoft's [markitdown](https://github.com/microsoft/markitdown).

## What you need

- **Python 3.12, 3.13 or 3.14** from <https://www.python.org/downloads/>.
  On Windows, tick **"Add python.exe to PATH"** during installation.
  On Intel Macs, use **Python 3.12 or 3.13** (see [Known limitations](#known-limitations)).
- No administrator rights are needed.

Get the converter by cloning this repository or downloading it as a ZIP and
unpacking it anywhere you like.

## Converting documents

The first time you run it, the converter spends a few minutes setting itself
up (it creates a private `.venv` folder and downloads its components). After
that it starts straight away. If the computer has no internet access, see
[Offline Bundle](#machines-without-internet-access-offline-bundle).

### Windows

- **Double-click `convert.cmd`**, then paste the path of a file or folder and
  press Enter. (In Explorer, Shift + right-click a file or folder and choose
  *Copy as path*; the quotes are fine.) For a folder, it tells you how many
  files it found and asks before converting.
- **Drag a file or folder onto `convert.cmd`** to convert it straight away.
- Or, in a terminal: `convert.cmd "C:\Reports" --pdf-page-images`

When started by double-click or drag-and-drop, the window waits for a key
press at the end so you can read the summary.

### macOS

- **Double-click `convert.command`** in Finder. The first time, macOS may
  refuse to open it: Control-click it, choose **Open**, then **Open** again.
  Drag a file or folder into the Terminal window that appears and press Enter.
- Or, in Terminal: `./convert.sh ~/Documents/Reports`

### Linux

`./convert.sh <file-or-folder> [options]`, or `./convert.sh` on its own to be asked.

### Options

| Option | What it does |
|---|---|
| `--output FOLDER` | Write everything to `FOLDER`, copying the source folder structure, instead of beside the originals. Useful for read-only folders. |
| `--force` | Convert every file again, even ones already converted and unchanged. |
| `--no-recurse` | Convert only the files directly in the folder, not its subfolders. |
| `--no-front-matter` | Leave out the short header describing where each file came from. |
| `--min-image-size PX` | Skip images narrower or shorter than `PX` pixels, such as icons. |
| `--pdf-page-images` | Also save a picture of every PDF page (150 DPI), which captures charts drawn as vector graphics. |
| `--selftest-offline` | Check that network access is blocked during conversion, then exit. |
| `--help` | List the options. |

## What you get

For each document, a Markdown file appears next to it, plus an `_assets`
folder when the document had images or charts:

```
Reports/
├── annual-report.pdf
├── annual-report.md
└── annual-report_assets/
    ├── p001-img01.png       image from page 1
    ├── p001-page01.png      picture of page 1 (with --pdf-page-images)
    └── p002-img01.jpg
```

- **Images** are saved in their original format and linked where they
  appeared: in place for Word and PowerPoint, after the page's text for PDFs,
  in the sheet's section for Excel. Asset names say where each came from:
  `p003-img01` (PDF page 3), `slide02-img01`, `sheet-Sales-img01`, `img01`
  (Word). An image repeated many times, like a logo, is saved once.
- **Charts** in Word, PowerPoint and Excel appear as a heading with the
  chart's title and type, a table of its values, and a link to its *chart
  definition* (the chart's original XML), so it can be redrawn later:

  ```
  **Chart: Revenue by Quarter (column chart)**

  | Category | 2025 | 2026 |
  | --- | --- | --- |
  | Q1 | 10 | 12 |

  [Chart definition](report_assets/chart01.xml)
  ```

- **Numbering** keeps the labels the document shows, such as `1.2.4.a`,
  `(ii)` or numbered headings like `## 1.2 Services`, so cross-references
  ("see clause 1.2.4.a") still make sense. Word's numbered lists therefore
  become one line per item rather than nested Markdown lists; bullet lists
  stay as lists. A label such as `3.` at the start of a line is written `3\.`
  so Markdown viewers show it as written instead of renumbering it.
- **Same name, different type**: if `report.pdf` and `report.docx` are in the
  same folder, both keep their extension (`report.pdf.md`, `report.docx.md`)
  so neither overwrites the other. The summary lists these.
- **Moving files**: links are relative, so move a `.md` file together with its
  `_assets` folder and everything still works.
- **Front matter**: each file starts with a short header giving the source
  file name, format, conversion date and converter version.
- **Re-running** on the same folder only converts new or changed files.

Supported formats: PDF, DOCX, PPTX, XLSX, XLS, HTML/HTM, CSV, JSON, XML,
EPUB, MSG (Outlook) and ZIP. Other files in a folder are ignored and counted.

### The summary and the log

Every run ends with a **Run Summary**: how many files were converted, already
up to date, skipped, failed or ignored, with the reason for each problem and
any warnings. The same report is saved as `markdown-converter.log` in the
folder you converted (or the `--output` folder).

- **Encrypted** (password-protected) files are skipped: remove the password
  and run again.
- **Damaged** files fail with a reason; the rest of the folder still converts.
- **Exit codes** for scripts: `0` everything converted or was up to date,
  `1` some files failed or were skipped, `2` the command was used incorrectly.

## Offline guarantee

Converting never sends or receives anything over a network. This is enforced
inside the converter: before any document is opened, it blocks every network
connection, so even a component that tried to go online could not. If that
ever happened, the file concerned is reported as failed with
"network access blocked". Web addresses are refused as input, and images that
a web page links to on the internet are left as links, never downloaded.

To check it for yourself:

```bash
./convert.sh --selftest-offline
```

(`convert.cmd --selftest-offline` on Windows) prints
`PASS: network access is blocked during conversion`.

Only the one-time setup uses the internet, to download the converter's
components, and an Offline Bundle removes even that.

## Machines without internet access (Offline Bundle)

On a computer **with** internet access and Python, build a bundle for the
target platform:

```bash
python tools/build_offline_bundle.py windows-x64
```

Platforms: `windows-x64`, `macos-arm64` (Apple silicon), `macos-x64` (Intel),
`linux-x86_64`; run with no platform to build them all. This fills
`offline-bundle/<platform>/`. Copy the whole converter folder, including
`offline-bundle/`, to the offline computer and run it as usual: setup installs
from the bundle without going online.

## What ends up in the Markdown

Converting keeps **all** the text a document holds, including parts you may
not see when viewing it:

- PowerPoint **speaker notes** and **hidden slides** are included.
- Excel **hidden sheets** are included.
- Word **comments and tracked changes** are not specially handled: the
  document's current text is converted.

Check the output before sharing it if your documents hold confidential notes.

## Known limitations

- **EMF/WMF images** (common in older Office files) are saved as they are;
  many Markdown viewers can't display them. The summary warns about each one.
- **Scanned PDFs** have no text to extract (OCR isn't included). Their page
  images are still saved, and the summary warns "no text layer found".
- PDF images in unusual encodings (such as JBIG2) are saved in their raw form
  with a warning.
- **Intel Macs** need Python 3.12 or 3.13: a component the converter relies on
  (onnxruntime) publishes no Intel-Mac builds for Python 3.14.
- Not converted: audio and video, standalone image files, web pages by
  address, YouTube. No AI image descriptions or cloud services are used.
- Charts are captured as data and definition, not redrawn as pictures (use
  `--pdf-page-images` for PDFs).
- Files inside **ZIP** archives become one Markdown file without their images;
  **Outlook** attachments are not extracted.
- Charts and images in legacy **`.xls`** files are not extracted; save as
  `.xlsx` to capture them.
- Started from **PowerShell**, `convert.cmd` pauses at the end as if it had
  been double-clicked. Use `cmd`, or set `MARKDOWN_CONVERTER_NO_PAUSE=1`.

## For developers

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock -r requirements-dev.txt   # Windows
.venv/bin/python -m pip install -r requirements.lock -r requirements-dev.txt       # macOS/Linux
.venv/Scripts/python -m pip install --no-deps -e .
.venv/Scripts/python -m pytest
```

- Tests drive the converter through its single entry point,
  `markdown_converter.cli.main(argv, stdin, stdout)`, the same one the
  launchers use. `tests/test_launchers.py` runs the launcher scripts themselves.
- `python tests/sample_set.py <folder>` builds the Sample Set: deterministic
  sample documents covering every format and edge case.
- `python tools/check_numbering.py document.docx [--reference word.pdf]`
  compares the converter's Word numbering labels with a PDF that Word
  rendered, or with LibreOffice's rendering when no reference is given
  ([ADR 0006](docs/adr/0006-numbering-checked-by-a-developer-tool.md)). Use it
  when a new kind of document comes in.
- `python tools/check_licences.py` fails if any dependency is not permissively
  licensed (ADR 0003).
- Dependencies are pinned in `requirements.lock` (`requirements-macos-x64.lock`
  for Intel Macs).

Project documents:

- [Stakeholder Requirements Specification](docs/requirements/stakeholder-requirements-specification.md)
- [Glossary](GLOSSARY.md) and [architecture decisions](docs/adr/)
- [Acceptance record](docs/acceptance/strs-acceptance.md) and
  [manual demonstrations](docs/acceptance/manual-demonstrations.md)
