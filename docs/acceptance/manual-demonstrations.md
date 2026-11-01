# Manual demonstrations

Some requirements depend on how a person starts the converter, which automated
tests can't reproduce. Perform these on each platform before a release and
record the result. Build the Sample Set first:

```bash
python tests/sample_set.py samples
```

## Windows 10 / 11

| # | Steps | Expected result | Requirement | Result |
|---|---|---|---|---|
| W1 | Double-click `convert.cmd`. At the prompt, paste the `samples\library` folder path (with quotes) and press Enter twice. | Prompt appears; "Found N supported files, convert? [Y/n]"; files convert; Run Summary shows; window waits for a key press. | StR-031, StR-032, StR-033, StR-035 | |
| W2 | Drag `samples\annual-report.pdf` onto `convert.cmd`. | Converts without asking; `annual-report.md` and `annual-report_assets\` appear; window waits for a key press. | StR-033, StR-035 | |
| W3 | Drag the `samples\library` folder onto `convert.cmd`. | Converts the whole folder without a confirmation question. | StR-032, StR-033 | |
| W4 | In a `cmd` window, run `convert.cmd samples\sales.csv`. | Converts; the window does **not** pause at the end. | StR-030 | |
| W5 | On a machine (or user account) without Python, double-click `convert.cmd`. | Friendly message explaining how to install Python 3.12-3.14; window waits for a key press; no stack trace. | StR-060 | |
| W6 | Under a standard (non-administrator) account, delete `.venv` and double-click `convert.cmd`. | Setup completes and conversion runs without an elevation prompt. | StR-061, StR-065 | |

## macOS 13 or later (Apple silicon and Intel)

| # | Steps | Expected result | Requirement | Result |
|---|---|---|---|---|
| M1 | Double-click `convert.command` in Finder (the first time, Control-click > Open). Drag the `samples/library` folder into the Terminal window and press Enter twice. | Prompt accepts the dragged (backslash-escaped) path; folder converts; window waits for Enter. | StR-031, StR-032, StR-034, StR-035 | |
| M2 | In Terminal, run `./convert.sh samples/sales.csv`. | Converts; exit code 0. | StR-030 | |
| M3 | On a Mac without Python 3.12-3.14, run `./convert.sh`. | Friendly message explaining how to install Python. | StR-060 | |
| M4 | As a standard user, delete `.venv` and run `./convert.sh samples/sales.csv`. | Setup completes without `sudo`. | StR-061, StR-065 | |

## Offline Bundle (all platforms)

| # | Steps | Expected result | Requirement | Result |
|---|---|---|---|---|
| B1 | On an internet-connected machine, build the bundle for the target platform (see README). Copy the repository and bundle to the target machine, disable networking, delete `.venv`, run the launcher with `samples/sales.csv`. | Setup installs from the bundle and conversion succeeds with networking disabled. | StR-062 | |
| B2 | With networking enabled, run `--selftest-offline`. | `PASS: network access is blocked during conversion`. | StR-043 | |
