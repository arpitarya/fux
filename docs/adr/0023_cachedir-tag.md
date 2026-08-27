---
type: ADR
name: ADR-CACHEDIR-TAG
title: ADR-CACHEDIR-TAG (0023) — CACHEDIR.TAG marks a derived directory disposable
description: A cache-directory tag written once into every derived .fux/ directory, per the bford.info/cachedir spec, so backup and archive tools skip it without Fux-specific configuration.
status: accepted
date: 2026-08-19
feature: the `CACHEDIR.TAG` file written into every derived `.fux/` subdirectory
owns: []
laws: [L3]
timestamp: 2026-08-19T00:00:00Z
---

# ADR-CACHEDIR-TAG — CACHEDIR.TAG marks a derived directory disposable

## §1 — For humans

Every derived directory under `.fux/` — today `.fux/runtime/`, which nests the
fetch cache at `.fux/runtime/fetch-cache/` rather than a separate top-level
directory — carries a small marker file, `CACHEDIR.TAG`, the first time it is
created. It is not Fux's own invention: it is a fixed, published convention that
backup tools, archivers, and IDE indexers already know how to read, so the
directory is skipped by every one of them **without a single line of
Fux-specific configuration anywhere**.

The file is written once and never touched again. Its bytes are pinned by the
spec, byte for byte — no version string, no timestamp, nothing that would make
two builds produce different tag files.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    A["fux build / fux ingest<br/>calls derived_dir()"] --> B{"CACHEDIR.TAG<br/>already exists?"}
    B -->|yes| C["left untouched"]
    B -->|no| D["written once,<br/>byte-exact per spec"]
    D --> E["backup/archive/indexer<br/>tools skip the directory"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   fux build / fux ingest calls derived_dir()
              |
              v
   CACHEDIR.TAG already exists? --yes--> left untouched
              |
              no
              v
   written once, byte-exact per the bford.info/cachedir spec
              |
              v
   backup / archive / IDE-indexer tools skip the directory, unconfigured
```

</details>

### Examples

The full, real content of `.fux/runtime/CACHEDIR.TAG` in this repo — three
lines, nothing else:

```console
$ cat .fux/runtime/CACHEDIR.TAG
Signature: 8a477f597d28d172789f06886806bc55
# This file is a cache directory tag created by fux.
# For information about cache directory tags, see https://bford.info/cachedir/
```

---

## §2 — For agents

### Context

`.fux/runtime/` is regenerated on every `fux build` and can be sizable. Nothing
about it should ever be swept into a backup, a `tar` archive, or an editor's
file index — those tools would spend real time and space on bytes that a single
command reproduces. Reinventing a Fux-specific exclusion convention would mean
every backup tool, archiver and IDE needs its own configuration line; a
*published, adopted* convention needs none.

### Decision

**1. Byte-exact per the spec.** `CACHEDIR_TAG` in
[`store/fuxdir.py`](../../src/fux/store/fuxdir.py) is a fixed constant — the
signature line plus two comment lines — with **no interpolated value of any
kind**.

**2. Written once, by `derived_dir()`.** The same function that creates
`.fux/runtime/` writes the tag immediately if it is absent, and never overwrites
it once present. The nested fetch cache does not call it directly — it lives
inside the already-tagged `runtime/`.

**3. ASCII, explicit `\n`.** Consistent with every other file `fux` generates at
the top level of `.fux/` — no locale dependency, no console-encoding surprise on
Windows.

**4. One tag per derived directory, never at `.fux/` itself.** The tag's job is
to mark the *specific* directory that is safe to skip. ⚠ **`.fux/index/` is
committed and must never carry one** — a tag there would make backup tools
silently skip the product, which is exactly the failure
[ADR-DOTFUX](0003_fux-directory.md)'s committed/derived split exists to prevent.

### Consequences

- Backup and archive tooling, and IDE file indexers that already honor the
  convention, skip `.fux/runtime/` for free — no Fux-specific configuration to
  write or maintain anywhere.
- A tool that has never heard of the convention just sees one small extra file;
  there is no correctness cost either way.
- **The tag's presence is not itself what makes `.fux/runtime/` safe to
  delete** — that property comes from
  [ADR-T1-ACCELERATOR](0011_accelerator.md)'s *pure function of the committed
  shards* guarantee. The tag only tells other tools about a fact that is already
  true.

### Alternatives considered

- **A Fux-specific marker filename.** Rejected: no third-party tool would
  recognize it, which defeats the entire point of using a shared convention.
- **Rely on `.fux/.gitignore` alone.** Rejected: `.gitignore` governs `git`, not
  OS-level backup tools, `tar --exclude-caches`, or IDE indexers — a different
  audience than the one this file addresses.
- **Regenerate the tag on every build.** Rejected: unnecessary I/O for a file
  whose entire value is being static; a changing mtime on a file that should
  never change is itself a small signal-noise cost.
- **Tag `.fux/` itself, once.** Rejected under decision 4 — it would mark the
  committed index skippable, which is a silent data loss dressed as tidiness.

### Reference (required)

- The generator — [`src/fux/store/fuxdir.py`](../../src/fux/store/fuxdir.py)
  (`CACHEDIR_TAG`, `derived_dir()`).
- The spec — https://bford.info/cachedir/
- The parent record — [ADR-DOTFUX](0003_fux-directory.md) decision 5.
- The directory this tags — [ADR-T1-ACCELERATOR](0011_accelerator.md).

### Veto condition

**Reopen this decision if** a widely-used backup or archive tool is found not to
honor the CACHEDIR.TAG convention, or if `.fux/index/` is ever found carrying
one.

**How to check it:**

```bash
find .fux/index -name CACHEDIR.TAG
# expect: no output — a tag here means the committed index is being marked skippable
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-DOTFUX](0003_fux-directory.md) ·
[ADR-T1-ACCELERATOR](0011_accelerator.md)

**Code**

- [`src/fux/store/fuxdir.py`](../../src/fux/store/fuxdir.py)

**Papers and specifications**

- The `CACHEDIR.TAG` specification — cache-directory tagging
  <https://bford.info/cachedir/>
