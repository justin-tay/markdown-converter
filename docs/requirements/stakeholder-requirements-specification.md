# Markdown Converter — Stakeholder Requirements Specification (StRS)

| | |
|---|---|
| **Document** | Stakeholder Requirements Specification (StRS) |
| **Standard** | Structured after ISO/IEC/IEEE 29148:2018 (Stakeholder Requirements Specification) |
| **Product** | Markdown Converter |
| **Version** | 0.2 (Draft) |
| **Date** | 2026-11-03 |
| **Status** | For review |

This is the user-facing requirements document for the Markdown Converter. It describes *what* stakeholders need and *why*, in language intended for people to read and approve. It deliberately avoids prescribing *how* the software is built; design detail belongs in a future Software Requirements Specification (SRS) and in the architecture decision records (ADRs).

---

## 1. Introduction

### 1.1 Purpose

This document states the needs of everyone with a stake in the Markdown Converter, so that they can agree on what will be delivered and so that the delivered tool can be checked against it.

### 1.2 Scope

The Markdown Converter turns local documents (PDF, Word, PowerPoint, Excel and similar) into Markdown files, and saves the images and charts inside them alongside each Markdown file. It runs on Windows and macOS, is started by double-clicking, dragging and dropping, or from a terminal, and **never contacts the internet while converting**.

It is built on Microsoft's open-source *markitdown* library.

Out of scope items are listed in [Section 5](#5-out-of-scope-and-known-limitations).

### 1.3 Definitions

Domain terms used in this document (**Target**, **Source File**, **Supported Format**, **Converted Document**, **Assets Folder**, **Asset**, **Asset Name**, **Embedded Image**, **Chart**, **Chart Data Table**, **Chart Definition**, **Page Snapshot**, **Figure Snapshot**, **Tagged PDF**, **Page Furniture**, **Page Marker**, **Name Collision**, **Conversion Run**, **Run Summary**, **Up To Date**, **Setup**, **Offline Bundle**, **Offline Guard**) are defined in the project [GLOSSARY.md](../../GLOSSARY.md). They are capitalised wherever they carry that defined meaning.

| Abbreviation | Meaning |
|---|---|
| StRS | Stakeholder Requirements Specification |
| SRS | Software Requirements Specification |
| ADR | Architecture Decision Record |
| RAG | Retrieval-Augmented Generation (feeding documents to an AI model) |
| OCR | Optical Character Recognition |
| EMF / WMF | Windows vector picture formats often found in older Office files |
| MoSCoW | Must / Should / Could / Won't prioritisation |

### 1.4 References

| Ref | Document |
|---|---|
| [R1] | ISO/IEC/IEEE 29148:2018 — Systems and software engineering — Life cycle processes — Requirements engineering |
| [R2] | markitdown — <https://github.com/microsoft/markitdown> |
| [R3] | [GLOSSARY.md](../../GLOSSARY.md) |
| [R4] | [ADR 0001 — In-process Offline Guard](../adr/0001-in-process-offline-guard.md) |
| [R5] | [ADR 0002 — Charts as data, not pictures](../adr/0002-charts-as-data-not-pictures.md) |
| [R6] | [ADR 0003 — Permissive licences only](../adr/0003-permissive-licences-only.md) |
| [R7] | [ADR 0004 — StRS per ISO/IEC/IEEE 29148](../adr/0004-stakeholder-requirements-specification.md) |
| [R8] | [ADR 0005 — Outputs beside sources](../adr/0005-outputs-beside-sources.md) |
| [R9] | [ADR 0006 — Numbering checked by a developer tool](../adr/0006-numbering-checked-by-a-developer-tool.md) |
| [R10] | [ADR 0007 — Numbering labels computed, not taken from Word](../adr/0007-numbering-labels-computed-not-taken-from-word.md) |
| [R11] | [ADR 0008 — PDF structure from tags, not page layout](../adr/0008-pdf-structure-from-tags-not-page-layout.md) |

### 1.5 Document conventions

- Each requirement has a unique, permanent identifier `StR-nnn`. Identifiers are never reused; withdrawn requirements are marked *Withdrawn*.
- **shall** = mandatory, **should** = strongly desired, **may** = optional.
- Priority uses MoSCoW: **Must**, **Should**, **Could** (Won't items appear in Section 5).
- Each requirement lists its **acceptance criteria** and **verification method**: **T** = Test, **D** = Demonstration, **I** = Inspection, **A** = Analysis.
- Sample files used for verification are identified `S-nn` (see [Section 6.2](#62-sample-set)).

---

## 2. Business context

### 2.1 Business purpose

Organisations hold large collections of documents in formats that AI tools, search systems and plain-text workflows handle poorly. Converting them to Markdown makes their content easy to read, search, diff and feed into AI models (for example RAG pipelines). Existing conversion options either lose images and charts, or send documents to online services — unacceptable when documents are confidential.

### 2.2 Business scope

The converter provides a simple, offline, repeatable way to turn a single file or an entire folder tree into Markdown with its images and chart data preserved, on the ordinary Windows and Mac machines people already use, without needing administrator rights.

### 2.3 Business goals

| ID | Goal |
|---|---|
| G1 | Make document content usable by AI models and plain-text tools. |
| G2 | Keep confidential documents on the user's machine — no data leaves during conversion. |
| G3 | Preserve visual content (images) and chart information, not just text. |
| G4 | Usable by non-programmers via double-click or drag-and-drop. |
| G5 | Repeatable results that can be re-run cheaply over growing folders. |

### 2.4 Stakeholders

| Stakeholder | Interest |
|---|---|
| **Document User** — knowledge worker comfortable with double-clicking or a basic terminal | Converts files or folders; needs it to be simple, safe and to tell them clearly what happened. |
| **Installer** — developer or IT person | Sets the tool up, including on machines without internet access; needs predictable setup and no admin rights. |
| **Data Owner** — owner of the confidential documents (may be the Document User or their organisation) | Needs assurance that document content never leaves the machine. |
| **Downstream Consumer** — AI/RAG pipeline, search index or person reading the Markdown | Needs consistent, well-structured Markdown with working image links and source information. |
| **Maintainer** | Needs pinned, permissively licensed dependencies and verifiable requirements. |

---

## 3. Operational concept

### 3.1 System context

```
                 ┌──────────────────────────── User's computer (no internet during conversion) ───┐
 Document User ──►  convert.cmd / convert.sh / convert.command                                      │
   (path arg,      │        │                                                                      │
   prompt, or      │        ▼                                                                      │
   drag-and-drop)  │  Markdown Converter ──reads──►  Source Files (PDF, DOCX, PPTX, XLSX, …)        │
                   │   [Offline Guard]   ──writes─►  Converted Documents (.md) + Assets Folders     │
                   │                     ──writes─►  Log file + Run Summary                         │
                   └───────────────────────────────────────────────────────────────────────────────┘
 Installer ──► Setup (one-time; online, or from an Offline Bundle)
```

### 3.2 User roles

- **Document User** runs Conversion Runs.
- **Installer** performs Setup and, where needed, builds/installs the Offline Bundle.

### 3.3 Operational scenarios

**OS-1 — Convert a folder on Windows by double-click.**
The Document User double-clicks `convert.cmd`. The window asks for a file or folder; they paste `"C:\Documents\Reports"` (quotes included). The tool reports "Found 37 supported files, convert? [Y/n]". They press Enter. Progress lines appear (`[12/37] pricing.xlsx … ok`). At the end a Run Summary shows 35 converted, 1 skipped (encrypted), 1 failed (damaged), and the window waits for a key press. Each document now has a `.md` beside it and, where it had images or charts, a `_assets` folder.

**OS-2 — Convert one file by drag-and-drop.**
The Document User drags `report.pptx` onto `convert.cmd` (Windows) or runs `./convert.sh report.pptx` (macOS). `report.md` and `report_assets/` appear; slide images are linked where they appeared on each slide, and each chart appears as a titled table with a link to its Chart Definition.

**OS-3 — Re-run on a growing folder.**
A week later the Document User runs the tool on the same folder. Only the 4 new or changed files are converted; the rest are reported as Up To Date. Running with `--force` reconverts everything.

**OS-4 — Set up on an air-gapped machine.**
The Installer builds an Offline Bundle on an internet-connected machine for the target platform, copies the repository and bundle across, and runs Setup, which completes without network access.

**OS-5 — Prove the tool is offline.**
The Data Owner asks for evidence. The Installer runs `convert --selftest-offline`, which shows that network connections are blocked during conversion.

**OS-6 — Capture vector charts in PDFs.**
A PDF's charts are vector drawings rather than images. In a Tagged PDF each chart is already captured as a Figure Snapshot where it sits. For an untagged PDF, the Document User re-runs with `--pdf-page-images`; after each Page Marker the Converted Document now links to a picture of the whole page.

**OS-7 — Read-only source share.**
Source files are on a read-only network share. The Document User runs with `--output D:\converted`; the output folder mirrors the source folder structure and the log file is written there.

### 3.4 Operational constraints

- Conversion happens entirely on the local machine with no internet access.
- The user may not have administrator rights.
- Source folders may be large, deeply nested, read-only, and contain paths with spaces or non-English characters.

---

## 4. Stakeholder requirements

### 4.1 Inputs and selecting what to convert

**StR-001 — Convert a single file** · Must
The Document User shall be able to convert one Source File by naming it as the Target.
*Acceptance:* Given S-05 as the Target, a Converted Document is produced for it and nothing else is converted. · *Verify:* T

**StR-002 — Convert a folder tree** · Must
The Document User shall be able to convert every Source File in a folder, including its subfolders, by naming the folder as the Target.
*Acceptance:* Given S-16 as the Target, every Source File at every depth gets a Converted Document. · *Verify:* T

**StR-003 — Limit to the top folder** · Should
The Document User should be able to convert only the files directly in the Target folder (`--no-recurse`).
*Acceptance:* With `--no-recurse` on S-16, files in subfolders are not converted. · *Verify:* T

**StR-004 — Supported Formats** · Must
The converter shall accept PDF, DOCX, PPTX, XLSX, XLS, HTML/HTM, CSV, JSON, XML, EPUB, MSG and ZIP files. When the Target is a folder, other files shall be ignored and counted as "ignored" in the Run Summary. When the Target is a single file of another format, the run shall stop with a clear message listing the Supported Formats.
*Acceptance:* S-01…S-15 all convert; the unsupported file in S-16 is reported as ignored; a single `.mp3` Target gives the unsupported-format message and exit code 2. · *Verify:* T

**StR-005 — Skip the converter's own output and hidden folders** · Must
When scanning a folder, the converter shall skip hidden folders, Assets Folders, its own Converted Documents and its log file, and shall not follow symbolic links.
*Acceptance:* Running twice on S-16 never converts a `.md` or anything inside a `_assets` or hidden folder. · *Verify:* T

**StR-006 — Refuse web addresses** · Must
The converter shall refuse a Target that is a web address (URL), including YouTube links.
*Acceptance:* `convert https://example.com/a.pdf` stops with a "local files only" message and exit code 2, without network access. · *Verify:* T

**StR-007 — Awkward paths** · Must
The converter shall handle paths containing spaces and non-English characters, with or without surrounding quotes.
*Acceptance:* All files in the S-16 subfolder named with spaces and non-ASCII characters convert successfully. · *Verify:* T

### 4.2 Converted Documents

**StR-010 — Output beside the source** · Must
By default, each Converted Document shall be written next to its Source File as `<name>.md`, and its Assets as `<name>_assets/`. An Assets Folder shall only be created when there are Assets. *(ADR 0005)*
*Acceptance:* Converting `report.pdf` produces `report.md` and `report_assets/` in the same folder; converting `data.csv` produces no Assets Folder. · *Verify:* T

**StR-011 — Name Collisions** · Must
When two Source Files in one folder would produce the same output name, both shall keep their extension in their output names (`report.pdf.md`, `report.docx.md`, and matching `_assets` folders), and the Run Summary shall list the collision. *(ADR 0005)*
*Acceptance:* S-14 produces `report.pdf.md` and `report.docx.md` and the summary reports one collision. · *Verify:* T

**StR-012 — Separate output folder** · Should
The Document User should be able to send all output to a separate folder (`--output <folder>`) that mirrors the Target's folder structure.
*Acceptance:* With `--output` on S-16, the output folder contains the same subfolder structure and no files are written inside the Target. · *Verify:* T

**StR-013 — Skip Up To Date files** · Must
A Source File whose Converted Document is newer than it shall be skipped and reported as Up To Date. With `--force`, it shall be reconverted and its Converted Document and entire Assets Folder replaced.
*Acceptance:* A second run on S-16 converts nothing; touching one source converts only that file; `--force` reconverts all and leaves no stale Assets. · *Verify:* T

**StR-014 — Content fidelity** · Must
Each Converted Document shall contain the Source File's text with its structure (headings, lists, tables) as produced by markitdown, encoded as UTF-8. For PDFs, structure is recovered as StR-017 describes.
*Acceptance:* Inspection of S-05, S-06 and S-07 output shows headings, lists and tables preserved; files are valid UTF-8. · *Verify:* I, T

**StR-017 — PDF document structure** · Must
A PDF's Converted Document shall be one continuous document with the PDF's own headings, paragraphs, lists, tables and links, not one section per page. For a Tagged PDF these shall come from its tags, in the tags' reading order, with heading levels as tagged; a section title the contents list names but the tags don't mark as a heading (a paragraph, or the opening paragraph of a full-width table row) shall also be a heading, matched in the contents list's order, at the level its indentation there gives: list labels (`1.`, `(a)`, `1.2.4.a`) appear as written and bullets as Markdown list items; a table running across pages is one table; the contents list is kept without dot leaders or page numbers; web links are Markdown links and links to other pages of the same PDF are plain text. A PDF whose tags reach less than 80% of its non-furniture text shall instead have its headings and bordered tables recovered from layout: a short line that is wholly bold or larger than body text, at the left margin with space above it, is a heading, with larger text taking higher levels. The log shall say which way each PDF was read. *(ADR 0008)*
*Acceptance:* S-17's tagged headings, lists, table, contents list and link appear as Markdown with the tagged levels and labels, and there are no `## Page` headings; S-18's bold section titles are headings and its bordered table is a Markdown table. · *Verify:* T

**StR-018 — No Page Furniture** · Must
A PDF's Page Furniture shall not appear in its Converted Document. In a Tagged PDF it is whatever the tags leave outside the content; otherwise it is a line in the top or bottom 12% of the page whose text, ignoring digits, recurs at the same height on three or more pages, except inside a bordered table. *(ADR 0008)*
*Acceptance:* S-17's and S-18's headers, footers and page numbers are absent from their output, and S-18's repeated table header row is kept. · *Verify:* T

**StR-019 — Page Markers** · Must
Each PDF page boundary shall be marked by a Page Marker (`<!-- page 3 -->`) before the first block that starts on that page, so a reader can find the place in the PDF while the marker stays invisible when the Markdown is viewed. A paragraph or table that runs across pages stays whole, with the marker before the next block. *(ADR 0008)*
*Acceptance:* S-17's output has a Page Marker for each page, and none inside its two-page table. · *Verify:* T

**StR-015 — Source information header** · Should
Each Converted Document should begin with a short header (YAML front matter) giving the source file name, source format, conversion date and converter version. `--no-front-matter` should turn it off.
*Acceptance:* S-01 output begins with front matter containing these four fields; with `--no-front-matter` it does not. · *Verify:* T

**StR-016 — Portable links** · Must
All links from a Converted Document to its Assets shall be relative, so that moving a Converted Document together with its Assets Folder keeps every link working.
*Acceptance:* After moving S-06's `.md` and `_assets` folder elsewhere, every image link still resolves. · *Verify:* T

### 4.3 Images and charts

**StR-020 — Extract Embedded Images** · Must
The converter shall save the Embedded Images in PDF, DOCX, PPTX and XLSX files into the Assets Folder, each in its original image format.
*Acceptance:* Every picture in S-01, S-05, S-06 and S-07 appears in the matching Assets Folder in its original format. · *Verify:* T

**StR-021 — Place image links sensibly** · Must
Image links shall appear where the image was in Word and PowerPoint documents and, for Tagged PDFs, where the image's figure is tagged; after the text of the page the image is on for other PDFs; and within the sheet's section for Excel workbooks.
*Acceptance:* Inspection of S-01, S-05, S-06 and S-07 output confirms the placement rules. · *Verify:* I

**StR-022 — Meaningful Asset Names** · Must
Each Asset's name shall say where it came from in the Source File: PDF page (`p003-img01.png`, or `p003-fig01.png` for a Figure Snapshot), slide (`slide02-img01.png`, `slide02-chart01.xml`), sheet (`sheet-Sales-chart01.xml`) or document order for Word (`img01.png`).
*Acceptance:* Asset names in S-01, S-05, S-06 and S-07 output follow the pattern. · *Verify:* I

**StR-023 — No duplicate images** · Should
An image that appears many times with identical content (e.g. a logo on every page) should be saved once, with every link pointing to that single file.
*Acceptance:* S-01's repeated logo produces one file referenced from every page. · *Verify:* T

**StR-024 — Skip tiny images** · Could
The Document User may choose to skip images smaller than a given size (`--min-image-size <pixels>`).
*Acceptance:* With `--min-image-size 32` on S-01, images smaller than 32×32 px are not saved or linked. · *Verify:* T

**StR-025 — Charts as data and definition** · Must
For each Chart in a DOCX, PPTX or XLSX file, the Converted Document shall contain a heading with the chart's title and type, a Chart Data Table of its values, and a link to its Chart Definition (the original chart XML) saved in the Assets Folder. When the values cannot be read, the heading and link shall still appear with the note "data not extracted". *(ADR 0002)*
*Acceptance:* Every chart in S-05, S-06 and S-07 appears with title, type, table and a working link to its `.xml` file. · *Verify:* T, I

**StR-026 — PDF Page Snapshots** · Should
With `--pdf-page-images`, every PDF page should be rendered as a 150 DPI PNG Page Snapshot, linked straight after that page's Page Marker. Page Snapshots are off by default.
*Acceptance:* With the option on S-02, one PNG per page exists and is linked straight after each Page Marker; without it, none. · *Verify:* T

**StR-046 — PDF Figure Snapshots** · Should
In a Tagged PDF, each figure containing vector drawing or more than one image should be rendered at 150 DPI as one Figure Snapshot of just the figure's area, linked where the figure is tagged with the figure's alternative text. A figure holding a single image and nothing else is saved as that Embedded Image instead. Figures that are mostly text already in the Converted Document (text boxes, callouts), or smaller than `--min-image-size`, are skipped. Figure Snapshots are always on. *(ADR 0008; numbered after StR-045 because StR-020…029 are taken.)*
*Acceptance:* S-17's vector chart becomes one `p00N-fig01.png` linked at its place with its alternative text; its single-image figure is saved in its original format; its text box produces no picture. · *Verify:* T

**StR-027 — Images in HTML and EPUB** · Should
Images bundled in an EPUB, and images an HTML file references from the local disk, should be copied into the Assets Folder with links rewritten to them. Images referenced from the web shall be left as text links, never downloaded, and counted in the Run Summary.
*Acceptance:* S-10 and S-09's local images appear in their Assets Folders; S-09's remote image link is unchanged and reported as "remote image not fetched". · *Verify:* T

**StR-028 — Warn about hard-to-view images** · Should
EMF/WMF images should be saved as-is, and the Run Summary should warn that some Markdown viewers cannot display them.
*Acceptance:* S-05's EMF image is saved and a warning names it. · *Verify:* T

**StR-029 — Convert EMF/WMF to PNG** · Could
The converter may additionally provide PNG versions of EMF/WMF images.
*Acceptance:* If implemented, S-05's EMF also has a PNG version that is linked. · *Verify:* T

### 4.4 Running the tool

**StR-030 — Path as first argument** · Must
The Document User shall be able to start a Conversion Run by giving the Target as the first argument to the launcher script on Windows and macOS.
*Acceptance:* `convert.cmd <path>` and `./convert.sh <path>` both convert the Target without further prompts. · *Verify:* D

**StR-031 — Ask for the path when none is given** · Must
When started without a Target, the launcher shall ask for one, accept it with or without quotes, and ask again if it does not exist.
*Acceptance:* Starting without arguments shows the prompt; entering a nonexistent path re-prompts; entering a quoted valid path proceeds. · *Verify:* D

**StR-032 — Confirm before converting a prompted folder** · Must
When the Target was entered at the prompt and is a folder, the converter shall show how many Supported Files it found and ask for confirmation before converting.
*Acceptance:* Entering S-16 at the prompt shows "Found N supported files, convert? [Y/n]"; answering `n` converts nothing. · *Verify:* D

**StR-033 — Windows double-click and drag-and-drop** · Must
On Windows, the Document User shall be able to start the converter by double-clicking `convert.cmd`, or by dragging a file or folder onto it.
*Acceptance:* Both actions start a Conversion Run on Windows 10 and 11. · *Verify:* D

**StR-034 — macOS double-click** · Should
On macOS, the Document User should be able to start the converter by double-clicking `convert.command` in Finder.
*Acceptance:* Double-clicking opens Terminal with the path prompt. · *Verify:* D

**StR-035 — Keep the window open** · Must
When started by double-click or drag-and-drop, the window shall stay open at the end until the user presses a key, so the Run Summary can be read.
*Acceptance:* After OS-1, the window waits for a key press. · *Verify:* D

**StR-036 — Progress** · Must
The converter shall show one progress line per Source File, e.g. `[12/37] report.pdf … ok`.
*Acceptance:* Converting S-16 shows a line per file with its position and outcome. · *Verify:* D

**StR-037 — Help and options** · Must
`--help` shall list every option with a one-line description. The launcher scripts shall pass any options through unchanged. Options: `--output`, `--force`, `--no-recurse`, `--pdf-page-images`, `--min-image-size`, `--no-front-matter`, `--selftest-offline`, `--help`.
*Acceptance:* `--help` lists all eight options; each option works when passed through either launcher. · *Verify:* T, I

**StR-038 — Language** · Must
All prompts, messages and documentation shall be in English.
*Verify:* I

### 4.5 Offline operation and data protection

**StR-040 — No internet during conversion** · Must
A Conversion Run shall never send or receive data over a network. This shall be actively enforced by the Offline Guard, not merely by configuration. *(ADR 0001)*
*Acceptance:* Converting all of S-01…S-16 while monitoring network traffic shows no outbound connections; an attempted connection from within a conversion is blocked (see StR-041). · *Verify:* T

**StR-041 — Blocked attempts fail safely** · Must
If anything attempts a network connection during a Conversion Run, that Source File shall fail with the message "network access blocked", and the run shall continue with the remaining files.
*Acceptance:* A test that forces a connection attempt during one file's conversion reports that file as failed with the message; other files convert. · *Verify:* T

**StR-042 — Online features disabled** · Must
markitdown features that require the internet — URL and YouTube inputs, Azure Document Intelligence, Azure Content Understanding, AI-model image descriptions and OCR plugins, audio transcription — shall be disabled.
*Acceptance:* Code inspection confirms none is enabled; StR-040 test passes. · *Verify:* I, T

**StR-043 — Offline self-test** · Must
`--selftest-offline` shall demonstrate that the Offline Guard blocks network connections, reporting a clear pass or fail.
*Acceptance:* On a networked machine, the self-test reports "PASS: network access is blocked during conversion". · *Verify:* D

**StR-044 — Source Files untouched** · Must
The converter shall never modify, move, rename or delete a Source File.
*Acceptance:* Checksums and timestamps of all S-16 Source Files are unchanged after a run. · *Verify:* T

**StR-045 — Hidden content disclosure** · Should
The user documentation should state that speaker notes, hidden slides and hidden sheets are included in Converted Documents, and that Word comments and tracked changes are not specifically handled, so users can judge what confidential content will appear.
*Acceptance:* The README states this. S-06 output includes speaker notes and the hidden slide; S-07 output includes the hidden sheet. · *Verify:* I, T

### 4.6 Batch handling and reporting

**StR-050 — Keep going after a failure** · Must
A failure converting one Source File shall not stop the Conversion Run.
*Acceptance:* S-15 (damaged) fails while the rest of S-16 converts. · *Verify:* T

**StR-051 — Run Summary** · Must
Every Conversion Run shall end with a Run Summary giving counts of converted, Up To Date (skipped), failed and ignored files, the reason for each failure or skip, and any warnings (Name Collisions, EMF/WMF images, remote images not fetched, PDFs without a text layer).
*Acceptance:* The summary after converting S-16 matches the expected outcome for each sample. · *Verify:* T

**StR-052 — Exit codes** · Must
The converter shall finish with exit code 0 when every Source File converted or was Up To Date, 1 when any failed, and 2 for invalid usage (bad path, unsupported single file, URL Target, bad option).
*Acceptance:* Each case returns the stated code. · *Verify:* T

**StR-053 — Log file** · Must
The converter shall write a log file (`markdown-converter.log`) to the output root: the `--output` folder if given, otherwise the Target folder, or the file's folder when the Target is a single file. If the log cannot be written, the run shall continue and say so.
*Acceptance:* The log appears in each location for each case; on a read-only Target without `--output`, the run completes with a warning. · *Verify:* T

**StR-054 — Encrypted and damaged files** · Must
Password-protected or encrypted Source Files shall be skipped with the reason "encrypted". Damaged files shall be reported as failed with a reason.
*Acceptance:* S-04 is skipped as "encrypted"; S-15 fails with a reason. · *Verify:* T

**StR-055 — Scanned PDF warning** · Should
A PDF with no text layer should produce the warning "no text layer found", with its page images still extracted.
*Acceptance:* S-03 converts with the warning and its page images in the Assets Folder. · *Verify:* T

### 4.7 Setup and distribution

**StR-060 — Python check** · Must
The launcher scripts shall check for Python 3.12 to 3.14 (3.12 or 3.13 on Intel Macs, see open issue 4) and, if no suitable version is found, show a friendly message explaining how to install it.
*Acceptance:* On a machine without Python, the script prints install guidance and exits without a stack trace. · *Verify:* D

**StR-061 — Automatic first-run Setup** · Must
On first use, the launcher shall perform Setup automatically, creating the converter's private environment and installing its dependencies. Setup is the only stage permitted to use the internet.
*Acceptance:* On a clean machine with Python, the first run completes Setup and converts; later runs skip Setup. · *Verify:* D

**StR-062 — Offline Bundle** · Must
The Installer shall be able to build an Offline Bundle on an internet-connected machine for Windows x64, macOS arm64 and macOS x64, and complete Setup from it with no internet access.
*Acceptance:* OS-4 completes on a machine with networking disabled for each platform. · *Verify:* D

**StR-063 — Pinned versions** · Must
All dependency versions, including markitdown, shall be pinned so every installation produces the same results.
*Acceptance:* The dependency list specifies exact versions. · *Verify:* I

**StR-064 — Distribution** · Must
The converter shall be obtainable by cloning its git repository or downloading it as a ZIP; no package registry is required.
*Verify:* D

**StR-065 — No administrator rights** · Must
Setup and Conversion Runs shall not require administrator rights.
*Acceptance:* OS-1 and OS-4 succeed under a standard user account. · *Verify:* D

### 4.8 Platform and constraints

**StR-070 — Windows and macOS** · Must
The converter shall run on Windows 10 and 11 (x64) and on macOS 13 or later (Apple silicon and Intel).
*Acceptance:* The full verification suite passes on each platform. · *Verify:* T

**StR-071 — Linux** · Should
The converter should run on mainstream Linux distributions via `convert.sh`.
*Verify:* T

**StR-072 — Permissive licences only** · Must
Every dependency shall be under a permissive licence (e.g. MIT, BSD, Apache-2.0, ISC, PSF); strong copyleft licences such as GPL, LGPL and AGPL shall not be used. Any other licence shall be an exception recorded with its reason in ADR 0003. *(ADR 0003)*
*Acceptance:* A licence report of all installed dependencies shows only permissive licences or exceptions recorded in ADR 0003. · *Verify:* A

---

## 5. Out of scope and known limitations

The following are explicitly **Won't** for this version:

| Item | Note |
|---|---|
| Audio and video files | markitdown's transcription uses an online service. |
| Standalone image files | Without online AI or OCR, only metadata could be produced. |
| Web pages, URLs and YouTube | Conflicts with offline operation (StR-006). |
| OCR of scanned documents | Images are still extracted; StR-055 warns. |
| AI-generated image descriptions, Azure services | Require the internet. |
| Rendering Office Charts as pictures | Charts are captured as data and definition instead (ADR 0002). |
| Images, charts and Assets from files inside ZIP archives | Each ZIP becomes one Converted Document. |
| Outlook MSG attachments | The message body is converted; attachments are not extracted. |
| Charts and images in legacy `.xls` | Cell data only; resave as `.xlsx` to capture charts. |
| Choosing individual pages for Page Snapshots | All pages or none. |
| The data behind charts in PDFs | A PDF stores only the drawing; Figure Snapshots capture the picture (ADR 0008). |
| Finding figures in untagged PDFs | Loose lines and boxes are too easily mistaken for figures; use Page Snapshots (ADR 0008). |
| Tables without drawn borders in untagged PDFs | Their text is kept as paragraphs. |
| Converting PDFs through Word or LibreOffice | Platform-bound or lower quality (ADR 0008). |
| Word comments and tracked changes | Not specifically handled; current text is converted. |
| Graphical file picker | The launcher prompts for a typed or pasted path. |
| Parallel conversion, per-file size limits or timeouts | Files are converted one at a time. |
| Languages other than English | — |

---

## 6. Verification

### 6.1 Approach

Each requirement is verified by the method stated against it:

- **Test (T)** — automated tests run against the Sample Set on each supported platform.
- **Demonstration (D)** — a person performs the scenario and observes the result.
- **Inspection (I)** — review of the output, code or documentation.
- **Analysis (A)** — e.g. a dependency licence report.

Acceptance of this version requires every **Must** requirement to pass on Windows 11 and macOS.

### 6.2 Sample Set

The repository includes a Sample Set covering every Supported Format and edge case:

| ID | Sample | Exercises |
|---|---|---|
| S-01 | PDF with text, raster images, a logo repeated on every page and tiny icons | StR-020, 021, 022, 023, 024 |
| S-02 | PDF with vector charts | StR-026 |
| S-03 | Scanned PDF (no text layer) | StR-055 |
| S-04 | Password-protected PDF | StR-054 |
| S-05 | DOCX with images (including EMF) and a chart | StR-014, 020, 021, 025, 028 |
| S-06 | PPTX with images, a chart, speaker notes and a hidden slide | StR-002, 016, 020, 021, 025, 045 |
| S-07 | XLSX with several sheets, an image, a chart and a hidden sheet | StR-020, 021, 025, 045 |
| S-08 | Legacy XLS | StR-004 |
| S-09 | HTML with local and remote images | StR-027 |
| S-10 | EPUB with images | StR-027 |
| S-11 | CSV, JSON and XML files | StR-004, 010 |
| S-12 | Outlook MSG with an attachment | StR-004 |
| S-13 | ZIP containing mixed files | StR-004 |
| S-14 | `report.pdf` and `report.docx` in one folder | StR-011 |
| S-15 | Damaged DOCX | StR-050, 054 |
| S-16 | Folder tree containing S-01…S-15 across subfolders, plus a hidden folder, an unsupported file, and a subfolder with spaces and non-ASCII characters in its name | StR-002, 003, 005, 007, 012, 013, 044, 051 |
| S-17 | Tagged PDF over three pages: running header and footer, page numbers, two heading levels, a contents list, a numbered and a bulleted list, a table running across two pages, a web link, a vector chart figure, a single-image figure and a text box | StR-017, 018, 019, 021, 022, 046 |
| S-18 | Untagged PDF: a running header, footers whose page numbers change, bold body-size section titles, a larger title, and a bordered table whose header row repeats on its second page | StR-017, 018 |

---

## 7. Traceability

| Requirement | Priority | Goal | Scenario | ADR | Method |
|---|---|---|---|---|---|
| StR-001 | Must | G1 | OS-2 | | T |
| StR-002 | Must | G1, G5 | OS-1 | | T |
| StR-003 | Should | G1 | | | T |
| StR-004 | Must | G1 | OS-1 | | T |
| StR-005 | Must | G5 | OS-3 | | T |
| StR-006 | Must | G2 | | 0001 | T |
| StR-007 | Must | G4 | OS-1 | | T |
| StR-010 | Must | G4 | OS-1, OS-2 | 0005 | T |
| StR-011 | Must | G5 | | 0005 | T |
| StR-012 | Should | G4 | OS-7 | 0005 | T |
| StR-013 | Must | G5 | OS-3 | | T |
| StR-014 | Must | G1 | | | I, T |
| StR-015 | Should | G1 | | | T |
| StR-016 | Must | G1 | | | T |
| StR-017 | Must | G1 | | 0008 | T |
| StR-018 | Must | G1 | | 0008 | T |
| StR-019 | Must | G1 | | 0008 | T |
| StR-020 | Must | G3 | OS-2 | | T |
| StR-021 | Must | G3 | OS-2 | | I |
| StR-022 | Must | G3 | | | I |
| StR-023 | Should | G3 | | | T |
| StR-024 | Could | G3 | | | T |
| StR-025 | Must | G3 | OS-2 | 0002 | T, I |
| StR-026 | Should | G3 | OS-6 | 0002, 0003 | T |
| StR-027 | Should | G2, G3 | | 0001 | T |
| StR-028 | Should | G3 | | | T |
| StR-029 | Could | G3 | | | T |
| StR-030 | Must | G4 | OS-2 | | D |
| StR-031 | Must | G4 | OS-1 | | D |
| StR-032 | Must | G4 | OS-1 | | D |
| StR-033 | Must | G4 | OS-1, OS-2 | | D |
| StR-034 | Should | G4 | | | D |
| StR-035 | Must | G4 | OS-1 | | D |
| StR-036 | Must | G4 | OS-1 | | D |
| StR-037 | Must | G4 | | | T, I |
| StR-038 | Must | G4 | | | I |
| StR-040 | Must | G2 | OS-5 | 0001 | T |
| StR-041 | Must | G2 | | 0001 | T |
| StR-042 | Must | G2 | | 0001 | I, T |
| StR-043 | Must | G2 | OS-5 | 0001 | D |
| StR-044 | Must | G2 | | | T |
| StR-045 | Should | G2 | | | I, T |
| StR-046 | Should | G3 | OS-6 | 0008 | T |
| StR-050 | Must | G5 | OS-1 | | T |
| StR-051 | Must | G4, G5 | OS-1 | | T |
| StR-052 | Must | G5 | | | T |
| StR-053 | Must | G5 | OS-7 | | T |
| StR-054 | Must | G5 | OS-1 | | T |
| StR-055 | Should | G3 | | | T |
| StR-060 | Must | G4 | | | D |
| StR-061 | Must | G4 | | 0001 | D |
| StR-062 | Must | G2 | OS-4 | 0001 | D |
| StR-063 | Must | G5 | | | I |
| StR-064 | Must | G4 | | | D |
| StR-065 | Must | G4 | OS-1, OS-4 | | D |
| StR-070 | Must | G4 | | | T |
| StR-071 | Should | G4 | | | T |
| StR-072 | Must | — | | 0003 | A |

---

## 8. Open issues and assumptions

| # | Item | Status |
|---|---|---|
| 1 | Minimum macOS version assumed to be 13; confirm against the target fleet. | Assumption |
| 2 | Confirmation prompt (StR-032) applies only when the folder was typed at the prompt; drag-and-drop and command-line folders convert without asking. | Assumption |
| 3 | pypdf's handling of unusual PDF image encodings (e.g. JBIG2, CCITT) to be checked against real-world samples. Images it can't decode are saved raw with a warning. | Open |
| 4 | onnxruntime (needed by markitdown's file-type detection) publishes no Intel-Mac builds for Python 3.14 or after version 1.23.2, so Intel Macs use Python 3.12 or 3.13 with older pins in `requirements-macos-x64.lock`. Intel Mac support may end when Python 3.13 does. | Constraint |
