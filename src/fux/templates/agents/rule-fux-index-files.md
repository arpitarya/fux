---
paths:
  - ".fux/index/**"
  - ".fux/runtime/**"
  - ".fux/acquired/**"
---

# Fux index files - do not hand-edit

`.fux/index/*.jsonl` is written by `fux ingest` only. `.fux/runtime/` is derived
and `.fux/acquired/` holds fetched source bytes; both are gitignored.

- **Never edit, splice or reformat a shard.** Change the source, then run
  `fux ingest`.
- **Merge conflict in a shard:** resolve the content conflicts, check out one
  side of each conflicted shard whole, then `fux ingest` (skill `fux-maintain`).
- **Never commit `.fux/runtime/` or `.fux/acquired/`**, and never ignore `.fux/`
  wholesale.
- **Do not delete `.fux/index/` to clear an error** when URL sources exist -
  those records cannot be rebuilt offline.
- `graph`, `explain` and `path` need `fux build`.

Full procedure: the `fux-index` skill.
