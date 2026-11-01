# 14: Offline Bundle

**What to build:** An Installer builds an Offline Bundle on an internet-connected machine for Windows x64, macOS arm64 and macOS x64, copies it with the repo to an air-gapped machine, and Setup completes from it without network access.

**Blocked by:** 13 (Launchers and automatic Setup)

**Status:** ready-for-agent

- [x] A build script produces a bundle per platform containing all pinned dependencies (StR-062)
- [x] With the bundle present, Setup installs only from it and never contacts a package index
- [ ] Demonstrated on each platform with networking disabled (StR-062, OS-4) — Windows bundle verified locally with `--no-index`; the CI `offline-bundle` job covers the others once pushed; a true networking-disabled run is manual demonstration B1
