# StRS acceptance record

Evidence for each requirement in the
[Stakeholder Requirements Specification](../requirements/stakeholder-requirements-specification.md),
version 0.1. Release acceptance needs every **Must** requirement to pass on
Windows 11 and macOS (StRS section 6.1).

| Status | Meaning |
|---|---|
| **Pass (Windows)** | Automated tests pass locally on Windows 11, Python 3.14. |
| **Pending CI** | Covered by the same tests in CI on macOS (Apple silicon and Intel) and Linux; not yet run because nothing has been pushed. |
| **Manual** | A person must perform the demonstration in [manual-demonstrations.md](manual-demonstrations.md). Not yet done. |

Recorded 2026-10-29 at converter version 0.1.0, 107 automated tests passing on Windows.

## Must requirements

| Requirement | Evidence | Windows | macOS / Linux |
|---|---|---|---|
| StR-001 Convert a single file | `test_single_file.py` | Pass | Pending CI |
| StR-002 Convert a folder tree | `test_folder_target.py::test_folder_target_converts_every_source_file_at_every_depth`, `test_acceptance.py` | Pass | Pending CI |
| StR-004 Supported Formats | `test_formats.py`, `test_usage.py::test_single_unsupported_file_is_invalid_usage_listing_supported_formats`, `test_folder_target.py::test_unsupported_files_are_ignored_and_counted` | Pass | Pending CI |
| StR-005 Skip own output and hidden folders | `test_folder_target.py` (hidden folders, converter output, symbolic links) | Pass | Pending CI |
| StR-006 Refuse web addresses | `test_offline_guard.py::test_web_address_target_is_refused` | Pass | Pending CI |
| StR-007 Awkward paths | `test_folder_target.py` (`Q3 résumé files`), `test_word_images.py::test_asset_links_are_url_safe_for_names_with_spaces`, `test_launchers.py` (folder with spaces) | Pass | Pending CI |
| StR-010 Output beside the source | `test_single_file.py`, `test_word_images.py::test_no_assets_folder_when_there_is_nothing_to_save` | Pass | Pending CI |
| StR-011 Name Collisions | `test_output_placement.py::test_name_collisions_keep_both_extensions` | Pass | Pending CI |
| StR-013 Skip Up To Date files | `test_output_placement.py` (second run, changed file, `--force`) | Pass | Pending CI |
| StR-014 Content fidelity | `test_single_file.py::test_word_document_keeps_headings_lists_and_tables`, `test_formats.py`, `test_numbering.py` (Word and PDF numbering labels) | Pass | Pending CI |
| StR-016 Portable links | `test_word_images.py::test_links_keep_working_when_document_and_assets_move_together` | Pass | Pending CI |
| StR-020 Extract Embedded Images | `test_word_images.py`, `test_powerpoint.py`, `test_pdf.py`, `test_charts.py::test_excel_images_and_charts_are_linked_within_their_sheet` | Pass | Pending CI |
| StR-021 Place image links sensibly | Same tests, which check positions | Pass | Pending CI |
| StR-022 Meaningful Asset Names | Same tests, which check names | Pass | Pending CI |
| StR-025 Charts as data and definition | `test_charts.py` (Word, PowerPoint, Excel, unreadable chart) | Pass | Pending CI |
| StR-030 Path as first argument | `test_launchers.py::test_launcher_converts_the_target_and_passes_options_through`; demonstrations W4, M2 | Pass | Pending CI, Manual |
| StR-031 Ask for the path | `test_prompt.py`, `test_launchers.py::test_launcher_asks_for_a_target_when_none_is_given`; demonstrations W1, M1 | Pass (automated); Manual | Pending CI, Manual |
| StR-032 Confirm a prompted folder | `test_prompt.py`; demonstration W1 | Pass (automated); Manual | Pending CI, Manual |
| StR-033 Windows double-click and drag-and-drop | Demonstrations W1-W3 | Manual | n/a |
| StR-035 Keep the window open | Demonstrations W1, W2, M1 | Manual | Manual |
| StR-036 Progress | `test_folder_target.py::test_progress_lines_show_position_and_path_within_the_target` | Pass | Pending CI |
| StR-037 Help and options | `test_usage.py::test_help_describes_the_target_and_each_option`; launcher option pass-through test; README lists all eight options | Pass | Pending CI |
| StR-038 Language | Inspection: all messages, `--help` and README are in English | Pass | Pass |
| StR-040 No internet during conversion | `test_offline_guard.py`; `test_acceptance.py` checks no connection was attempted across the full Sample Set; `test_html_epub.py` (remote image never fetched). A packet-capture run is not automated. | Pass | Pending CI |
| StR-041 Blocked attempts fail safely | `test_offline_guard.py::test_network_attempt_fails_that_source_file` and the swallowed-error variant | Pass | Pending CI |
| StR-042 Online features disabled | Inspection: each format routes to one markitdown converter; no LLM client, Azure, plugins, audio or YouTube extras (`formats.py`, `requirements.lock`) | Pass | Pass |
| StR-043 Offline self-test | `test_offline_guard.py::test_selftest_reports_that_network_access_is_blocked`; demonstration B2 | Pass | Pending CI |
| StR-044 Source Files untouched | `test_folder_target.py::test_source_files_are_never_modified` | Pass | Pending CI |
| StR-050 Keep going after a failure | `test_folder_target.py::test_a_damaged_file_fails_with_a_reason_and_the_run_continues`, `test_acceptance.py` | Pass | Pending CI |
| StR-051 Run Summary | `test_folder_target.py::test_run_summary_lists_each_failure_and_skip_with_its_reason`, `test_acceptance.py` | Pass | Pending CI |
| StR-052 Exit codes | `test_usage.py`, `test_folder_target.py`, `test_launchers.py::test_launcher_returns_the_converters_exit_code` | Pass | Pending CI |
| StR-053 Log file | `test_folder_target.py` (log locations, unwritable log), `test_output_placement.py` (`--output`) | Pass | Pending CI |
| StR-054 Encrypted and damaged files | `test_folder_target.py::test_encrypted_files_are_skipped_as_encrypted` (PDF and Word), damaged-file test | Pass | Pending CI |
| StR-060 Python check | Demonstrations W5, M3 | Manual | Manual |
| StR-061 Automatic first-run Setup | `test_launchers.py` (CI starts with no `.venv`, so Setup runs); demonstrations W6, M4 | Pass (Setup with packages already present) | Pending CI, Manual |
| StR-062 Offline Bundle | Windows bundle built and installed locally with `--no-index`, then converted a sample; CI `offline-bundle` job for every platform; demonstration B1 for networking disabled | Pass (`--no-index`); Manual (networking disabled) | Pending CI, Manual |
| StR-063 Pinned versions | Inspection: `requirements.lock`, `requirements-macos-x64.lock` pin exact versions | Pass | Pass |
| StR-064 Distribution | Inspection: runs from a clone or ZIP, no package registry | Pass | Pass |
| StR-065 No administrator rights | Demonstrations W6, M4 | Manual | Manual |
| StR-070 Windows and macOS | Full suite on Windows (local); CI matrix on macOS Apple silicon and Intel | Pass | Pending CI |
| StR-072 Permissive licences only | `tools/check_licences.py` passes on `requirements.lock`; CI also checks the Intel Mac lock | Pass | Pending CI |

## Should and Could requirements

| Requirement | Evidence | Windows |
|---|---|---|
| StR-003 Limit to the top folder | `test_folder_target.py::test_no_recurse_converts_only_the_top_folder` | Pass |
| StR-012 Separate output folder | `test_output_placement.py` (`--output`, including inside the Target) | Pass |
| StR-015 Source information header | `test_single_file.py` (front matter, `--no-front-matter`) | Pass |
| StR-023 No duplicate images | `test_word_images.py`, `test_pdf.py` | Pass |
| StR-024 Skip tiny images (Could) | `test_word_images.py::test_min_image_size_drops_small_images_and_their_links` | Pass |
| StR-026 PDF Page Snapshots | `test_pdf.py` (snapshots on and off) | Pass |
| StR-027 Images in HTML and EPUB | `test_html_epub.py` | Pass |
| StR-028 Warn about hard-to-view images | `test_word_images.py::test_emf_images_are_kept_with_a_warning` | Pass |
| StR-029 Convert EMF/WMF to PNG (Could) | Not implemented | Not done |
| StR-034 macOS double-click | Demonstration M1 | Manual |
| StR-045 Hidden content disclosure | README "What ends up in the Markdown"; `test_powerpoint.py`, `test_charts.py::test_hidden_sheets_are_included` | Pass |
| StR-055 Scanned PDF warning | `test_pdf.py::test_scanned_pdf_warns_about_missing_text_layer_but_keeps_its_images` | Pass |
| StR-071 Linux | CI on `ubuntu-latest` | Pending CI |

## Gaps

Tracked in `.scratch/markdown-converter/issues/16-manual-demonstrations-and-first-ci-run.md`:

- **Manual demonstrations** W1-W6, M1-M4 and B1 haven't been performed yet.
- **macOS and Linux** results depend on the first CI run.
- **StR-029** (Could) isn't implemented.
