---
id: files-max-100-lines
domain: code-quality
type: convention
status: active
created: 2026-06-01
updated: 2026-06-01
aliases: [file-size, small-files, line-limit]
keywords: [length, split, module, refactor]
---
**Convention:** Source files stay ≤ **100 lines** (≤ **50** for files whose name
marks them as utilities, e.g. `*_utils.py` / `*.utils.ts`).

**Why:** A file you can read top-to-bottom in one screen is a file you can hold
in your head. The limit is a forcing function for single-responsibility modules
and clean seams — when a file wants to grow past it, that is the signal to split.

**How to apply:** When an edit pushes a file over the limit, extract the most
cohesive cluster of functions into a new sibling module rather than trimming
comments. Generated files and long-form `narrative`/`memory` entries are exempt.
