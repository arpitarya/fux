---
inclusion: auto
name: fux-search-guide
description: Searching the Fux index with fux ask or fux find - flags, the confidence band, --why ranking, -q fusion, --expand for vocabulary gaps, folder and phrase filters. Use when asked to search the docs, find where something is documented, or explain why a result ranked.
---

# Searching with fux ask / fux find

- **Run `fux ask "<q>" --json --band`** when you will act on the result.
- **`answerable: false` or band `none`: abstain.** `partial`: answer and name
  every term in `confidence.missing`, or retry with the corpus's own word or
  `--expand`. `weak`: report candidates, not a conclusion.
- **Scores compare only within one result list**; a fused (`-q`) score is a
  different quantity.
- `find` filters (`--under`, `--phrase`, `--all`) never add results - raise
  `--top`.
- A missing `confidence` key means you did not pass `--band`.

Full procedure: the `fux-search` skill.
