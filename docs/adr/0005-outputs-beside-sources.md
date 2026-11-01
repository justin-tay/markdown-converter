# Converted Documents sit beside their Source Files, keeping the extension only on Name Collisions

By default each Converted Document is written next to its Source File as `<name>.md`, with its Assets Folder as `<name>_assets/`, so a converted folder reads naturally and links stay short. When two Source Files in one folder would produce the same name (e.g. `report.pdf` and `report.docx`), *both* keep their extension (`report.pdf.md`, `report.pdf_assets/`) rather than one silently winning or getting a numeric suffix, so neither name depends on which file was converted first. A separate output folder that mirrors the source tree is available via `--output` for read-only sources.

## Consequences

- Adding a new file that collides with an existing one changes the output name of the file already converted; the Run Summary reports every collision so users notice.
