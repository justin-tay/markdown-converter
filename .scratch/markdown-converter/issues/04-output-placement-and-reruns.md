# 04: Output placement and re-runs

**What to build:** Converted Documents and Assets Folders land in predictable places (ADR 0005): Name Collisions keep both files' extensions, `--output` mirrors the Target into a separate folder, Up To Date files are skipped on re-runs, and `--force` reconverts cleanly.

**Blocked by:** 03 (Folder Targets and batch reporting), 05 (Asset Store and Word images)

**Status:** ready-for-agent

- [x] S-14 (`report.pdf` + `report.docx`) produces `report.pdf.md` and `report.docx.md` with matching `_assets` folders; the Run Summary lists the collision (StR-011)
- [x] `--output <folder>` mirrors the Target's subfolder structure and writes nothing inside the Target; log goes to the output folder (StR-012, StR-053)
- [x] A second run on S-16 converts nothing and reports files as Up To Date; touching one Source File reconverts only it (StR-013)
- [x] `--force` reconverts all and replaces each Assets Folder entirely, leaving no stale Assets (StR-013)
