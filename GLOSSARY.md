# Markdown Converter

Converts local office documents and similar files into Markdown, with their images and charts saved alongside, without ever contacting the internet during conversion.

## Inputs

**Target**:
The single file or folder the user asks to convert in one run.
_Avoid_: Input path, source path

**Source File**:
A file within the Target whose format is a Supported Format and that will be converted.
_Avoid_: Input file, document

**Supported Format**:
A file type the converter accepts: PDF, DOCX, PPTX, XLSX, XLS, HTML/HTM, CSV, JSON, XML, EPUB, MSG and ZIP.
_Avoid_: Supported extension, file type

## Outputs

**Converted Document**:
The Markdown file produced from one Source File.
_Avoid_: Output, result, markdown file

**Assets Folder**:
The folder holding every Asset of one Converted Document, named after the Source File with an `_assets` suffix.
_Avoid_: Media folder, images folder

**Asset**:
Any file in an Assets Folder that a Converted Document links to: an Embedded Image, a Chart Definition, a Page Snapshot or a Figure Snapshot.
_Avoid_: Attachment, resource

**Embedded Image**:
A picture stored inside a Source File, saved as-is into the Assets Folder.
_Avoid_: Figure, picture

**Chart**:
A native chart inside an Office Source File, stored as data and drawing instructions rather than as a picture.
_Avoid_: Graph, plot

**Chart Data Table**:
The Markdown table in a Converted Document holding the values a Chart plots.

**Chart Definition**:
The original chart XML extracted from an Office Source File into the Assets Folder, kept so the Chart can be re-rendered or inspected later.
_Avoid_: Chart XML, chart file

**Asset Name**:
The file name of an Asset, which says where it came from in the Source File (e.g. `p003-img01.png`, `slide02-chart01.xml`).
_Avoid_: Image-001, sequential name

**Page Snapshot**:
An optional rendered picture of a whole PDF page, used to capture vector graphics that are not Embedded Images.
_Avoid_: Screenshot, page render

**Figure Snapshot**:
A rendered picture of just one tagged figure's area of a PDF page, capturing a vector chart or diagram where it sits in the text.
_Avoid_: Cropped page, figure image

**Tagged PDF**:
A PDF whose accessibility tags record its headings, paragraphs, lists, tables and figures in reading order; the converter takes a PDF's structure from them when they cover most of its text.
_Avoid_: Accessible PDF, structured PDF

**Page Furniture**:
Text repeated on a PDF's pages that is not part of the content: running headers and footers, page numbers and classification lines. It is left out of the Converted Document.
_Avoid_: Header/footer, boilerplate

**Page Marker**:
An HTML comment (`<!-- page 3 -->`) in a PDF's Converted Document marking where a page of the PDF begins; invisible when the Markdown is viewed.
_Avoid_: Page heading, page break

**Name Collision**:
Two Source Files in the same folder that would produce the same Converted Document name (e.g. `report.pdf` and `report.docx`); both then keep their extension in their output names.

## Runs

**Conversion Run**:
One invocation that converts every Source File in a Target and ends with a Run Summary.
_Avoid_: Job, batch

**Run Summary**:
The end-of-run report listing each Source File as converted, skipped or failed, with reasons.
_Avoid_: Report, results

**Up To Date**:
A Source File whose Converted Document is newer than it, and is therefore skipped unless the user forces reconversion.
_Avoid_: Cached, already done

**Setup**:
The one-time preparation of the converter's private environment, the only stage permitted to use the internet.
_Avoid_: Install, bootstrap

**Offline Bundle**:
A pre-downloaded set of dependencies that lets Setup complete on a machine with no internet access.
_Avoid_: Wheelhouse, air-gap package

**Offline Guard**:
The protection that blocks any network connection attempt during a Conversion Run and fails the affected Source File.
_Avoid_: Firewall, sandbox, network block

## Project documents

**Stakeholder Requirements Specification (StRS)**:
The human-readable statement of what stakeholders need from the converter, following ISO/IEC/IEEE 29148.
_Avoid_: User requirements specification, URS
