<!-- golden-ext: filler 2026-02-28 ext/filler/a15-release-notes-tilecutter.md -->
# Tilecutter — release notes

*Maintained by the core team. Newest first.*

## 4.2.0 — 2026-02-28

### Added
- Keyboard navigation across the results list, including type-ahead.
- An offline cache so the last query survives a reload.
- `--format=ndjson` on the export command.

### Fixed
- A crash when the filter box was emptied while a request was still in flight.
- Dates rendered in the server's timezone rather than the reader's.
- The progress bar reaching 100% before the last chunk was written.

### Changed
- Exports are streamed. A very large export no longer holds the whole result in
  memory, which is what the 3.x memory reports were.

### Deprecated
- The `v1` endpoint. It keeps working for two more minor releases and then
  returns 410 with a link to the migration note.

## 4.1.3 — 2026-01-14

### Fixed
- Regression from 4.1.0: a filter with a trailing space matched nothing.
- Windows paths with a drive letter were rejected by the config loader.

## 4.1.0 — 2025-12-02

### Added
- Config file support, searched upward from the working directory.
- `--dry-run` on every destructive subcommand.

### Security
- Dependency bump for a transitive parser advisory. No exploit path was found
  in Tilecutter itself; the bump is precautionary and is recorded because
  "precautionary" is a claim somebody will check.
