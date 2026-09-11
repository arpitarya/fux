---
inclusion: fileMatch
fileMatchPattern: [".fux/enrich/**"]
---

# Editing Fux enrichment

Files in `.fux/enrich/` are committed and change search ranking.

- **Only when a human asked to enrich** a named document or scope.
- **The body is five to ten questions a searcher would type, one per line** -
  never a summary.
- **The file name is the full document sha from `fux enrich --plan`.**
- **`superseded_by:` retires the named document in the ranking.** Write it only
  when a successor is declared, never casually.
- **Never paste a value `.fux/pii.toml` would redact.**
- Before finishing: `fux enrich --check <document>` must pass.

Full procedure: the `fux-enrich` skill.
