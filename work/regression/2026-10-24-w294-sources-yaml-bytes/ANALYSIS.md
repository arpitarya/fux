---
type: Analysis
run: 2026-10-24-w294-sources-yaml-bytes
---

# Analysis — W-294 acceptance

**Diagnosis:** none needed — the index is byte-identical (0 diff lines after a
`--full` rebuild by the new engine). No change follows from this run.

- **Why `--full` as well as incremental:** the incremental run carried every
  document forward from runtime state, which only proves the reuse key agreed.
  `--full` re-extracted all 2453 documents and still wrote no shard. Repro:
  `evidence/acceptance.sh`.
- **What this does not show:** a consumer repo with URL entries — this
  repository lists none. URL conversion is covered by
  `tests/test_setup.py` (both lists convert, attributes intact) and the reader
  agreement by `tests/test_sources_yaml_differential.py`.
