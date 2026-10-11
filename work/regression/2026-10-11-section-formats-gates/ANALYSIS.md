---
type: Analysis
description: "What W-273 phase 1's gates leave: nothing to fix. The ladder cannot exercise option (b), so its coverage comes from the unit test and this repository's own index; the engine to pin for W-270 is b4d961cd."
run: 2026-10-11-section-formats-gates
item: W-273
---

# ANALYSIS — W-273 phase 1's gates

## 1 · Every gate is an identity, and that is the expected result

**Finding.** G0, G1 and G3 reproduce W-269's outputs byte for byte, and the
re-ingested `rung-01000` index equals W-269's.

**Cause.** The ladder has no `.csv`, `.json` or `.jsonl` document, so the
closed list touches no ladder document. The rest of the diff is a constant
and a comment.

**What covers option (b), then.** Two things, neither on the ladder:

- `tests/query/test_sections.py::test_decoded_record_formats_are_sectionless`
  — each of the three formats with four records gets no `nsec` and no section
  line, and a Markdown control still splits. **It fails with the list emptied**
  (checked before the commit).
- this repository's own index (report §3): `.jsonl` 79 611 → 0 sections,
  `.json` 4 522 → 0, ratio 8.0× → 1.756×.

**Change: none.** Repro:

```bash
bash work/regression/2026-10-11-section-formats-gates/evidence/gates.sh
bash work/regression/2026-10-11-section-formats-gates/evidence/g1own.sh
```

(both expect the pinned worktree at the scratch path they name; recreate it
with `git worktree add --detach <path> b4d961cd` and a venv).

## 2 · The engine handed to W-270

**`b4d961cd`.** W-270's bar pins it. A later commit that changes `src/` or
`node/` before W-270's capture would need a new G0.

## 3 · Unresolved

- The 588 s base re-ingest (6 s CPU) on a loaded machine is not diagnosed.
  It is not a gate, and W-269 measured 4.2 s on the same corpus.
