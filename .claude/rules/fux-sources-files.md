---
paths:
  - ".fux/sources.yaml"
  - ".fux/config/formats.toml"
  - ".fux/.fuxignore"
---

# Editing Fux source lists

These files decide what Fux indexes. They are committed, so an edit changes the
index every teammate clones.

- **Change them only when a human asked.** Prefer `fux add` / `fux remove` over a
  hand edit: they validate the entry and re-ingest.
- **`fux remove X --dry-run` first** - it says whether it deletes an entry or adds
  an anchored `/X` exclusion to `.fux/.fuxignore`.
- **`archived` is declared, never inferred** from a path or a title.
- **Exclusion lives only in `.fux/.fuxignore`**, where `!path` RE-INCLUDES; `.fux/sources.yaml` refuses a `!` entry.
- **A URL record commits a readable title and headings** for anyone who clones the repo. (`meta` used to control this and was removed in fux 3.x; an entry still carrying it will not load.)
- After a hand edit, run `fux ingest` and commit `.fux/` in the same change.

Full procedure: the `fux-sources` skill.
