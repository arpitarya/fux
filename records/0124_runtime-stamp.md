---
type: Standing Record
kind: component
name: SR-RUNTIME-STAMP
title: SR-RUNTIME-STAMP (0124) — stamp.json, the cheap pre-check ahead of the manifest
description: A deliberately non-reproducible per-shard size/mtime snapshot that short-circuits manifest.json's content-hash check on the common unchanged case, and is never itself proof of freshness.
status: accepted
amended: 2026-10-05
date: 2026-08-19
feature: "`.fux/runtime/stamp.json` — the cheap staleness pre-filter, and its deliberate exclusion from the determinism set"
owns: [node/src/derive/stamp.mjs@e54866f6479b, src/fux/derive/stamp.py@4ed944c99464]
laws: [L4]
timestamp: 2026-08-19T00:00:00Z
content_sha: 3fa9425f233986f6b0adcf52ccf0ca7a74096fd7f8395bec95c56b62bba23fd2
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`node/src/derive/stamp.mjs`](../node/src/derive/stamp.mjs) · file
- [`src/fux/derive/stamp.py`](../src/fux/derive/stamp.py) · file

**Describes** — reaches into, does not own:

- [`src/fux/derive/_build.py::_read_committed`](../src/fux/derive/_build.py) · owned by [SR-T1-ACCELERATOR](0110_accelerator.md)
- [`src/fux/derive/format.py`](../src/fux/derive/format.py) · owned by [SR-T1-ACCELERATOR](0110_accelerator.md)

<!-- COMPONENTS-END -->

# SR-RUNTIME-STAMP — stamp.json, the cheap pre-check ahead of the manifest

## §1 — For humans

`stamp.json` records, per committed shard, its `[size, mtime_ns]` at the
moment the accelerator was last built. It exists for one reason: an
`os.stat()` per shard is far cheaper than a content hash per shard, and most
of the time nothing changed at all. A size-and-mtime match is a strong
"probably unchanged" signal that lets `fux` skip
[`manifest.json`](0123_runtime-manifest.md)'s real content-hash check on the
common path.

It is deliberately excluded from the set of files that must be byte-identical
across two builds — filesystem timestamps are not reproducible, by
construction, so this file is volatile on purpose rather than by oversight.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    A["fux build reads each shard:<br/>os.stat() -> size, mtime_ns"] --> B["stamp.json:<br/>{shard: [size, mtime_ns]}"]
    B -->|"next invocation"| C{"size+mtime unchanged<br/>for every shard?"}
    C -->|yes| D["skip the manifest<br/>sha recompute"]
    C -->|no| E["fall through to<br/>manifest.json's content check"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   fux build reads each committed shard: os.stat() -> size, mtime_ns
              |
              v
   stamp.json: {shard filename -> [size_bytes, mtime_ns]}
              |
              |  next fux build / doctor invocation
              v
   size+mtime unchanged for every shard? --yes--> skip the manifest's
              |                                    content-sha recompute
              no
              v
   fall through to manifest.json's real content-hash check
```

</details>

### Examples

Two real entries from this repo's `.fux/runtime/stamp.json`:

```json
{
  "shards": {
    "01.jsonl": [4353, 1786519644986538882],
    "05.jsonl": [10764, 1786519644987126840]
  }
}
```

---

## §2 — For agents

### Context

`manifest.json`'s content-hash check is correct but not free — it costs one
hash over every committed shard's bytes. On the overwhelmingly common case
(nothing changed since the last build), that cost is avoidable if a cheaper
signal can rule out a change first.

### Decision

**0. This record owns [`src/fux/derive/stamp.py`](../src/fux/derive/stamp.py) and its Node twin [`node/src/derive/stamp.mjs`](../node/src/derive/stamp.mjs)** since 2026-10-05 ([SR-WORK-OWNERSHIP](0054_WORK-ownership.md) decision 11, W-261 — Arpit's ruling that every `kind: component` record owns a file). The stamp's writer is a pure move out of `derive/_build.py` (and `build.mjs`): `write` — `[size_bytes, mtime_ns]` per shard, byte-identical. `_build.py` still decides **when** it is written, in `build()`'s order, and computes its inputs in `_read_committed`; `format.py` keeps the constants and `write_json`, the serializer every runtime JSON file shares — both [SR-T1-ACCELERATOR](0110_accelerator.md)'s, both reached by this record's `describes` rows. ⚠ **This decision read *owns nothing, case (a)* until W-261, arguing that carving the file out would give one plane two owners for one pass.** The ruling answered it: the build orchestrates, this record owns the bytes of its one file.

**1. Fields: per committed shard, `[size_bytes, mtime_ns]`.** Captured in the
same pass `build()` already makes over `.fux/index/*.jsonl`, at no extra I/O.

**2. Deliberately excluded from `DETERMINISTIC_FILES`.** mtimes are not
reproducible across two checkouts of byte-identical content — a fresh clone,
a CI runner, or a different machine all produce different mtimes for the same
bytes. This file is volatile by design, and its absence from the determinism
set says so explicitly rather than leaving it to be discovered.

**3. It is a filter, never the final word.** A size+mtime match is a strong
hint that nothing changed; it is not proof. Only
[`manifest.json`](0123_runtime-manifest.md)'s content-sha map is the record of
truth for actual staleness.

**4. Unchanged by W-168 step 4 (2026-09-27).** `mined.json` is derived in the
same build and is covered by the same staleness check.

<!-- L12-VALUES-START -->

**Where this record's fixed values live — [L12](0014_LAW-12-values-live-in-config.md), W-225, 2026-09-27.**
Each name below keeps its spelling in code and holds no literal: it is read from
[`src/fux/constants.toml`](../src/fux/constants.toml), and a missing key stops the
process naming it ([SR-CONSTANTS](0159_constants.md)). **The values are unchanged** —
this moved where they are written, not what they are.

- `src/fux/derive/format.py` — `RUNTIME_DIR` ← `[runtime] dir`, `BLOCK_SIZE` ← `[runtime] block_size`, `RUNTIME_SCHEMA` ← `[runtime] schema`, `DOCS_FIELDS` ← `[runtime] docs_fields`, `DOCS_NAME` ← `[runtime] docs`, `ANCHORS_DIR` ← `[runtime] anchors_dir`, `STATS_NAME` ← `[runtime] stats`, `MINED_NAME` ← `[runtime] mined`, `MANIFEST_NAME` ← `[runtime] manifest`, `STAMP_NAME` ← `[runtime] stamp`, `POSTINGS_DIR` ← `[runtime] postings_dir`, `DETERMINISTIC_FILES` ← `[graph] file`

<!-- L12-VALUES-END -->

**No decision here moved** ([L12](0014_LAW-12-values-live-in-config.md) decision 6a, W-225 stage 5c, 2026-09-28). A component this record owns or describes lost a numeral — to `constants.toml` ([SR-CONSTANTS](0159_constants.md)) or to a refactor that removed it — and behaves byte-identically; JSON it prints is indented by `[json] indent`.

**No decision here moved** ([L12](0014_LAW-12-values-live-in-config.md) decision 6a R8, W-225 stage 6, 2026-09-28). A function this record owns or describes lost a boolean or value parameter default; every caller now passes the value the default had, so behaviour is unchanged.

**No decision here moved** ([L12](0014_LAW-12-values-live-in-config.md), W-225 stage 7, 2026-09-28). A component this record owns or describes now reads an artefact name or a format value from `constants.toml` that it spelled in code; every value is unchanged. The veto test `tests/test_l12_values_live_in_config.py` now holds the rest of its literals to `tests/l12_allow.toml`.


**W-236 — section records (2026-10-10; built on branch `w236-sections`, unmerged until [its run](../work/regression/2026-10-10-section-records/PRE-REGISTRATION.md) passes).** `stamp.json` stamps every **section shard** too, under `sections/<name>`, and `accel.is_fresh` compares the document and section shard lists together ([SR-SECTIONS](0161_sections.md) decision 7).

### Consequences

- **The deep check exists in `doctor`** (W-246, 2026-10-04): the `accelerator` row re-hashes each committed shard against the sha `manifest.json` recorded at build time, so a same-size, same-mtime byte flip warns even though `is_fresh` cannot see it. It runs off the query path, which is why R3's budget is untouched.
- The common case — nothing changed since the last build — is answered by an
  `os.stat()` per shard instead of a content hash per shard, which is
  materially cheaper at corpus scale.
- A false "unchanged" verdict from a size+mtime match without a content check
  is possible only if a shard's bytes changed while both its size and its
  mtime happened to be preserved exactly — which is why the content-sha check
  remains the real guarantee, never something this file makes redundant.
- Because it sits outside the determinism set, two byte-identical
  `.fux/runtime/` builds made on two different machines or at two different
  times can carry different `stamp.json` bytes. That is expected, not a
  defect, and `stamp.json` must never be read as a correctness signal on its
  own.

### Alternatives considered

- **Skip `stamp.json`; always check `manifest.json`'s content hashes.**
  Rejected on cost at scale: re-hashing every committed shard on every
  `fux doctor`/`ask` invocation, even when nothing changed, is wasted work.
- **Use only mtimes, drop the content-hash check entirely.** Rejected:
  mtimes are exactly the non-reproducible signal Law L4 keeps out of any
  correctness claim — fine as a hint, never as proof.
- **Fold `stamp.json`'s fields into `manifest.json` itself.** Rejected: would
  pull a non-reproducible field into the one file whose whole contract is
  byte-identical reproducibility, breaking that guarantee for the rest of the
  file too.

### Reference (required)

- Generator — [`src/fux/derive/_build.py`](../src/fux/derive/_build.py)
  (`build()`, the `shard_stamp` collection, the write to `fmt.STAMP_NAME`).
- The set it is excluded from —
  [`src/fux/derive/format.py`](../src/fux/derive/format.py)
  (`DETERMINISTIC_FILES`).
- The parent record — [SR-T1-ACCELERATOR](0110_accelerator.md), decision 9.

### Veto condition

**Reopen this decision if** a real workflow is found where `stamp.json`'s
size+mtime match masks an actual content change that should have been caught
immediately.

**How to check it:**

```bash
# after editing a committed shard, the manifest check must still catch it
# even if stamp.json's fields happen to look unchanged
fux doctor
# expect: [OK]/[WARN] accelerator: stale, driven by manifest.json's content
# hashes, not by stamp.json alone
```
---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [SR-LAWS](0001_LAWS.md) ·
[SR-T1-ACCELERATOR](0110_accelerator.md) ·
[SR-RUNTIME-MANIFEST](0123_runtime-manifest.md)

**Code**

- [`src/fux/derive/_build.py`](../src/fux/derive/_build.py)
- [`src/fux/derive/format.py`](../src/fux/derive/format.py)
