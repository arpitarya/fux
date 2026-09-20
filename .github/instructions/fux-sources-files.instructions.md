---
applyTo: ".fux/sources/**,.fux/formats.toml,.fux/.fuxignore"
---

# Editing Fux source lists

These files decide what Fux indexes. They are committed, so an edit changes the
index every teammate clones.

- **Change them only when a human asked.** Prefer `fux add` / `fux remove` over a
  hand edit: they validate the line and re-ingest.
- **`fux remove X --dry-run` first** - it says whether it deletes a line or adds a
  `!X` exclusion.
- **`archived=true` is declared, never inferred** from a path or a title.
- **`!path` excludes in `.fux/sources/dirs` but RE-INCLUDES in `.fux/.fuxignore`.**
- **A URL record commits a readable title and headings** for anyone who clones the repo. (`meta=` used to control this and was removed in fux 3.x; a line still carrying it will not load.)
- After a hand edit, run `fux ingest` and commit `.fux/` in the same change.

Full procedure: the `fux-sources` skill.
