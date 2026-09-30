---
type: Analysis
description: "Why ingest's extract phase slowed down, the three fixes, and what is left."
---

# W-239 — analysis

## Diagnosis

The Cowork micro-timings (see the W-239 item) located all three costs, and
the 1 000-document profile confirms them. Together they were 9.7 s of a 13.8 s
profiled ingest.

- **The decoder registry was rebuilt on every call.** `registry(root)` is
  called by `decode()`, by `claims()` (from the walk and from
  `parse_document`) and by `extract._decoder_for()`: 3 410 calls for 1 000
  documents. Each call ran `exec_module` on all 17 consumer decoders in
  `.fux/decoders/`. This arrived with W-205 part 1, when `_decoder_for` added a
  third call site; the first two were already uncached.
- **The identifier-family matcher tried 103 alternatives at every character.**
  The combined pattern starts with two lookbehinds, which stops Python's `re`
  from using its prefix scan, so every position paid for the whole
  alternation. This arrived with W-233.
- **`meta_bindings()` re-read `.fux/formats.toml` once per document.**
  `_declared_bindings`, right beside it, had been cached from the start. This
  one was not. It arrived with W-205 part 1.

## Changes, each with a repro command

1. **Cache `registry()`** (`src/fux/decode/__init__.py`, SR-DECODE decision 22).
   The key covers every `.py` in `.fux/decoders/`, the types file and the
   legacy flag. Failures are not cached, and callers get a copy.

   ```bash
   .venv/bin/python -m pytest -q tests/decode/test_registry_cache.py
   ```

2. **Cache `meta_bindings()`** on the types file's stat, the same way
   `_BINDINGS` is keyed. Tested in the same file.

3. **Gate the family scan** (`src/fux/query/identifiers.py`, SR-IDENTIFIERS
   decision 13):
   - A candidate is a template's first letter where `_LEAD` holds. The gate
     pattern is `[letters](?<!EDGE.)(?<![A-Za-z0-9]\..)`, which is `_LEAD`
     shifted one character left.
   - At a candidate, only the families sharing that letter are tried, in the
     original order.
   - A `[user]` regex disables the gate.

   ```bash
   .venv/bin/python -m pytest -q tests/query/test_identifiers_gated.py
   .venv/bin/python work/regression/2026-09-29-w239-extract-speed/evidence/matcher_sweep.py
   ```

`extract.RULES_VERSION` is **not** bumped. None of the three changes can move
what `extract_fields` returns, and the unchanged root hash on both rungs is
the evidence for that.

## What is left

- **`stem()` is now the largest single cost**: 2.2 s of a 4.6 s profiled
  1 000-document ingest, 250 000 calls. Speeding it up would be a separate
  item, and the analyzer is shared with the Node reader. It is not filed,
  because nobody has asked for more speed yet.
- `_registry_key` stats every consumer decoder on each call, about 75 µs,
  which comes to 0.26 s per 1 000 documents. Resolving the registry once per
  ingest run would remove that, but it would need a second mechanism beside
  the cache. At this size it is not worth one.
- **`fux doctor` and `fux identifiers` are slow for a different reason**
  (W-238): `inspect/idfamilies.detect()` calls `_is_candidate` 25 million
  times on this repo (30 s under the profiler). W-238 gave both verbs a
  progress bar. Making detection itself faster is not in either item.
