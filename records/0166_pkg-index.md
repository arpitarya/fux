---
type: Standing Record
kind: component
name: SR-PKG-INDEX
title: "SR-PKG-INDEX (0166) — a package that ships a fux index: the segment, its pin, its runtime"
description: "A package may ship a built fux index — a segment of shards, its identifiers.toml and a fux-index.json manifest, data and never code. A consumer pins it with one `kind = \"index\"` row in `.fux/config/plugins.toml` (name, version, segment digest, npm and PyPI names); both runtimes locate it by module resolution from the repository root, verify the digest and the header, refuse loudly when it is missing, other or drifted, and inflate it into the gitignored `.fux/runtime/pkg/<name>@<version>/` with the builder the repository's own runtime uses."
status: accepted
date: 2026-10-25
amended: 2026-10-25
feature: index packages — a shipped fux index segment, pinned, verified and inflated in both runtimes
owns: [src/fux/derive/segments.py@b7f3a78a5705, src/fux/schemas/fux-index.schema.json@281aee116429, node/src/derive/segments.mjs@9cf5f4542b9b, node/src/config/plugins.mjs@3735dbe4973d, node/test/plugins-index.test.mjs@10cf624c880c, tests/test_pkg_index.py@df16fe5c2820, tests/fixtures/pkg-index@eb97fc679bf1]
laws: [L2, L3, L4, L5, L12]
timestamp: 2026-10-25T00:00:00Z
content_sha: 783e17ded8c29a83bd2dd3580d8e09bea072590e1d60e3d4e45e1c2ff057daa8
ratifies: "Arpit, 2026-10-25 (Cowork), on W-298's forks: 'plugins.toml, kind = \"index\"' for the pin's home; the three open questions accepted as a set — scope = repo|packages|all, default all · wire compat = lockstep · 10k ceiling counts the merged corpus — 'Yes, all three as recommended.' Then: 'file the work items for all.' (W-299, W-300, W-301, W-302)"
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`node/src/config/plugins.mjs`](../node/src/config/plugins.mjs) · file
- [`node/src/derive/segments.mjs`](../node/src/derive/segments.mjs) · file
- [`node/test/plugins-index.test.mjs`](../node/test/plugins-index.test.mjs) · file
- [`src/fux/derive/segments.py`](../src/fux/derive/segments.py) · file
- [`src/fux/schemas/fux-index.schema.json`](../src/fux/schemas/fux-index.schema.json) · file
- [`tests/fixtures/pkg-index/`](../tests/fixtures/pkg-index) · dir
- [`tests/test_pkg_index.py`](../tests/test_pkg_index.py) · file
- [`tests/test_pkg_merged_query.py`](../tests/test_pkg_merged_query.py) · file

<!-- COMPONENTS-END -->

# SR-PKG-INDEX — a package that ships a fux index

## §1 — For humans

**A library can ship its documentation already indexed.** The library's author runs
`fux ingest` on the docs and packs the result — a few shard files, the
`identifiers.toml` they were built under and a small manifest — into a package
published on npm, on PyPI, or both. A consumer who wants those docs searchable
beside their own declares the package once, in the committed
`.fux/config/plugins.toml`, at one version and one digest. There is no ingest on
the consumer's side, so an npm-only machine with no Python gets the package's docs
too.

**The package is data, never code.** fux reads its files and runs nothing from it.
**And it is pinned exactly like a decoder package** ([SR-PLUGINS](0165_plugins.md)
P4): a pinned index that is not installed, is installed at another version, or
whose shard bytes differ from the pin stops fux with the one line that fixes it —
in Python and in Node alike, so two machines on one repository can never search
different things.

**Once verified, the segment is inflated** into `.fux/runtime/pkg/<name>@<version>/`
— gitignored and rebuilt only when the pin changes — by the same builder that
fills `.fux/runtime/` for the repository itself.

```mermaid
flowchart LR
    A["author: fux ingest → fux pack"] --> P["npm tarball / wheel<br/>index/*.jsonl · identifiers.toml · fux-index.json"]
    T[".fux/config/plugins.toml<br/>kind = &quot;index&quot; · name · version · digest · npm · pypi"] --> R{"resolved from the repo root,<br/>version, digest, header equal?"}
    P --> R
    R -->|no| E["FuxError<br/>+ the install line"]
    R -->|yes| I[".fux/runtime/pkg/&lt;name&gt;@&lt;version&gt;/<br/>(derived, gitignored)"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  author: fux ingest -> fux pack
        |
        v
  npm tarball / wheel: index/*.jsonl, identifiers.toml, fux-index.json
        |
        v
  resolved from the repo root; version, digest, header equal?  <-- .fux/config/plugins.toml
        |                                                            kind = "index", name, version,
        | no --> FuxError + the install line                         digest, npm, pypi
        | yes
        v
  .fux/runtime/pkg/<name>@<version>/   (derived, gitignored)
```

</details>

---

## §2 — For agents

### Context

Ingest is Python-only, so a consumer on an npm-only install can never ingest a
package's docs. A segment built where the package is built needs no ingest at all.
The pin machinery already exists ([SR-PLUGINS](0165_plugins.md) P2–P4, P7): a
shipped index is one more declared, pinned, refused-loudly thing rather than a
second mechanism. W-298 step 1 measured the shape before it was built (19 of 20
against a bar of 16, 2026-10-25), which opened the gate for the four items this
record serves: W-299 (the pin and the runtime), W-300 (the merged query), W-301
(`pkg:` locations) and W-302 (`fux pack`).

### Decision

**1. A shipped index is a segment, and a segment is data.** A segment is a
directory holding exactly:

| file | what it is |
|---|---|
| `index/*.jsonl` | the document shards, byte for byte what `fux ingest` committed |
| `identifiers.toml` | the identifier rules the shards were built under |
| `fux-index.json` | the manifest — decision 3 |

An index row loads no module and runs nothing, which is why it is not an entry
point and why SR-PLUGINS P10's isolation is moot for it. **Where the segment sits in
a distribution:** on npm, at the package root (beside `package.json`); on PyPI, as
the import package named by the distribution's normalised name (`acme-docs-index` →
`acme_docs_index/`), which needs no `__init__.py` — a namespace package resolves.
The file names and the segment-file set are `src/fux/constants.toml
[plugins.index]` (L12).

**2. The pin is one `[[package]]` row with `kind = "index"` in
`.fux/config/plugins.toml`** (Arpit, 2026-10-25: *"plugins.toml, kind = \"index\""*,
over a `packages:` section in `sources.yaml`). Its keys are exactly `name`,
`version`, `digest`, `kind`, `npm`, `pypi` (`[plugins.index] keys`):

- `name` — the pin's own name, the directory name under `runtime/pkg/`; lowercase,
  matching `[plugins.index] name_pattern`.
- `version` — the index package's version; both distributions carry the same one.
- `digest` — decision 4.
- `npm`, `pypi` — the index package's name on each registry; **at least one**.

**Refused by name**: an unknown key, a `suffixes` key (an index reads no format),
a name declared twice — across decoder and index rows alike — and a row with
neither `npm` nor `pypi`. **`fux setup` never proposes an index row on its own**
(SR-PLUGINS P6): it scans sources, and no source names an index nobody declared.
`fux setup --index <pypi name> [--index-npm <npm name>]` writes one when told,
from what is installed; `fux setup --pin` re-pins every index row whose PyPI
distribution is installed, and leaves an npm-only row as written.

**3. The manifest `fux-index.json`** carries `fux_version` (the engine that packed
it), `index_header` (the shards' header line, parsed), `content` (`npm`, `pypi`,
`version` — the **docs** package the index describes, which W-301 reads), `docs`
(the document count) and `digest` (decision 4). Its declared shape is
[`src/fux/schemas/fux-index.schema.json`](../src/fux/schemas/fux-index.schema.json),
owned here; W-302 writes it and validates against it. **The pin never trusts the
manifest's numbers**: the reader checks the manifest's `digest` against the digest
it computes, refuses on disagreement, and reads the header off the shards
themselves (decision 6).

**4. The digest covers the segment files only** — `sha256:` over every file
`[plugins.index] segment` names (`index/*.jsonl`, `identifiers.toml`), relative to
the segment root, in SR-PLUGINS P4's RECORD-line form (`<path>,sha256=<urlsafe
b64>`, sorted, CRLF read as LF). **Never the wheel or the tarball**: those differ
between pip, uv and npm for identical segments — P4's `RECORD` lesson applied.
One digest therefore covers both registries, and anyone reproduces it from the
same docs (L4). `plugins.segment_digest` is the one Python implementation and
`node/src/config/plugins.mjs::segmentDigest` its twin; `fux pack` imports the
Python one.

> ⚠ **A deviation from W-299's step 2, flagged for Arpit's ratification — NOT yet
> ratified.** The item names `fux-index.json` among the files the digest covers.
> It cannot be: the manifest *carries* the digest, and a file cannot contain its
> own hash. The manifest is therefore outside the digest, and what it could vouch
> for is checked independently — its `digest` against the computed one, the
> header against the shards. A manifest edited to carry other `content` or `docs`
> values verifies; W-301's version check on the docs package (its step 4) is what
> catches a lying `content.version`.

**5. Located by module resolution, never by a path.** Python: the PyPI
distribution's version from `importlib.metadata`, its segment from
`importlib.util.find_spec(<import name>)`, which must resolve to exactly one
directory holding the manifest. Node: `createRequire(<repo root>/package.json)`,
then the first `<dir>/<npm>/package.json` along `require.resolve.paths(<npm>)` —
**from the repository root, never from fux's own install**, so two consumers
sharing one global fux resolve their own packages. Neither imports or executes
anything.

**6. Lockstep header compatibility** (Arpit, 2026-10-25, *"wire compat =
lockstep"*). Every shard's header must carry the reader's own `_format`,
`analyzer` and `tf_fields` (`[plugins.index] header_keys` against `[index]`); a
segment with any other is **foreign** and refused by name, never scored and never
skipped. **The `identifiers` digest MAY differ** — a package built under other
identifier rules is legal, and W-300 hashes the query once per distinct digest.

**7. Missing or drifted is a hard error, verb-wide** — SR-PLUGINS P4 extended to
index rows. In this order, each a `FuxError` naming the package and the install
line (`pip install <pypi>==<version>` or `npm install <npm>@<version>`, printed
and never run, L5):

1. the row has no name for this runtime's registry (`pypi` for Python, `npm` for
   Node) — this runtime cannot read the package, so it would search something the
   other does not;
2. not installed; 3. installed at another version; 4. pinned without a digest;
5. installed but resolving to no segment (no manifest); 6. drifted — the computed
digest is not the pin's; 7. the manifest's `digest` disagrees with the shards;
8. a foreign header (decision 6).

Python runs it inside `plugins.require` (so `cli._require_plugins` refuses every
verb outside `PLUGINS_EXEMPT`); Node runs `requireIndexPackages` before every verb,
beside the PII gate. **The texts are one set of words in both runtimes**, held by a
differential test.

**8. The runtime: `.fux/runtime/pkg/<name>@<version>/`** — a derived, gitignored
child of `.fux/runtime/` ([SR-DOTFUX](0102_fux-directory.md)), named by
`[plugins.index] runtime_child`. It is laid out as a repository: the verified shards
in `.fux/index/`, the segment's `identifiers.toml` in `.fux/config/`, and
`.fux/runtime/` built from them by the repository's own builder (`derive.build` in
Python, `derive/build.mjs` in Node — byte-identical output, the W-242 law), so
every root-keyed reader opens a pinned package as it opens a repository. A
`[plugins.index] pin_stamp` file holds the pin digest it was built from, written
last: **rebuilt when the pin digest changes, untouched when it does not**, and a
directory no pin names is removed. `fux build` and every runtime rebuild do it, in
both runtimes, after verification — so a drifted segment is refused before a byte
of it is read for the build.

**9. The scale ceiling counts the merged corpus** (Arpit, 2026-10-25, *"10k
ceiling counts the merged corpus"*; [SR-WORK-SCALE](0057_WORK-scale.md)): the
repository's documents plus every pinned segment's. `fux doctor` prints one `index
packages` row per pin and one `merged corpus` row with the total, which warns above
10 000 ([SR-DOCTOR](0152_doctor.md)).

**10. The merged query** (Arpit, 2026-10-25, *"scope = repo|packages|all, default
all"*) — one ranking over the repository and every pinned segment, statistics
summed, with `scope` choosing the segments. **Built by W-300**, in both runtimes:

- **The segments.** `scope` is `repo`, `packages` or `all`
  (`constants.toml [scope]`, L12). `scan.segments_for` (Node: `run.mjs::segmentsFor`)
  returns the repository first, then every pin **sorted by name**; each pin is
  **verified and, when its pin digest moved, inflated before a byte of it is
  read** (`segments.inflate` → `plugins.locate_index`), so a foreign or drifted
  segment stops the query by name (decisions 6–7) — never scored, never skipped.
- **The query, hashed once per distinct `identifiers` digest** (`merged_hashes`):
  each segment's own `identifiers.toml` analyzes the question; term keys are
  unsalted `blake2b(term)`, so equal tokens meet. The **union**, in segment order,
  is the one hash list every segment is scanned for and `rank()` sums over —
  scanning every segment for the union keeps `df` exact for every hash in every
  segment. `--expand` is hashed the same way; the mined table is the union of
  every segment's own pairs (`mined.merge_tables`).
- **The statistics, summed, weighted once** (`merged_candidates`): each segment's
  raw B2 pass (`scan._scan_segment`) returns candidates, `df`, `n`, the five RAW
  `total_flen` fields and the anchor total; they are summed and `derive_wlen` is
  applied **once**, so the merged corpus has one `avg_wlen` and a shared `idf`.
  **Anchor text folds within a segment only** — each pass resolves its own edges'
  targets against its own records.
- **One `rank()` call** over every segment's candidates (`merged_ask`). Each
  candidate from a pin carries `package = <pin name>`, which `rank()` copies onto
  the hit (`AskResult.package`) and nothing scores or sorts. Scores from separate
  corpora are never fused (`fuse.py` is refused for this by design).
- **Always the scan.** The accelerator's block-max skipping bounds a document
  against one segment's statistics; the merged answer is defined by the summed
  ones, so a merged query reports `ranked_by: scan` whatever `--fast` says.
- **After `rank()`, the repository's stages run unchanged** — the pin, the graph
  tier (a package hit is a node the repository's graph has no edge to), the band.
  The proximity reranker **declines** a package hit (its bytes are not in the
  repository, W-301 reads them in place) and its score passes through. Display
  reads a package hit's own record from its segment (`segments.root_for`).
- **Who merges.** `fux ask` (`--scope`, default `all`) and `fux_search` (`scope`,
  default `all`). **Every other verb ranks the repository alone** — `lexical` is
  the frozen baseline, `answer` refers its winner from the source that owns it
  (W-301's `pkg:` is what makes a package winner referable), and `find`,
  `enrich`, `lsp` call `run_query` with no scope. With no pin, `all` **is** the
  repository alone on the unchanged code path, and `scope = repo` is byte-equal
  to the engine before W-300 — the L13 run's gates G0a–c
  ([`work/regression/2026-10-25-w300-merged-query/`](../work/regression/2026-10-25-w300-merged-query/VERDICT.md)).
- **A hit names its segment only by `package`**, present on a package hit and
  absent on a repository hit (so a repository-only payload is byte-equal). Its
  `id` stays the segment's record id; an id a package shares with the repository
  is a known hazard of the window's id-keyed stages (`in_window`, `sections`) that
  W-301's `pkg:` location is what disambiguates.

**The L13 verdict is INCONCLUSIVE → Arpit** (2026-10-25): the table reads PASS
on the fixture (slice `hit@1` 16–0, nothing outside it moved, every gate
byte-identical), filed INCONCLUSIVE by the pre-registration's own rule because
the builder decided its own run (SR-RS d6), golden G0 was not run, and two
guardrails are unmeasurable on a 9-document fixture.

**11. `pkg:` locations** — a hit in a segment names the docs package from the
manifest's `content`, and the passage is read inside the installed package.
**Ratified, built by W-301**, which states its mechanism here when it lands.

### Consequences

- **A package's docs become searchable on a Node-only machine** — the consumer
  never ingests them.
- **Every reading verb now hashes each pinned segment's shards**, the cost P4
  already pays for a declared decoder package. A segment is small (one package's
  docs) and the hash is over files, not a walk.
- **Both runtimes must hold the package.** A row with only `npm` refuses every
  Python verb, and one with only `pypi` every Node verb: answering from a smaller
  corpus on one machine would be the divergence the pin exists to stop.
- **The section plane is not part of a segment.** `[plugins.index] segment` is
  `index/*.jsonl`, which does not reach `index/sections/`; a segment whose records
  declare sections fails the build's own `nsec` check when inflated. A packer built
  without `[index] section_records` produces none.
- **A segment pinned under a different `_format` or analyzer is refused** — the
  price of lockstep: an author re-packs on every analyzer or format bump.

### Alternatives considered

- **A `packages:` section in `.fux/sources.yaml`** — lost to Arpit's ruling: the
  pin is a dependency of the index, and `plugins.toml` is where dependencies are
  declared, pinned and refused.
- **A digest over the whole distribution** — differs between pip, uv and npm for
  identical segments (SR-PLUGINS' `RECORD` lesson).
- **Locating the package by a path in the row** — a path is a function of the
  machine; module resolution is a function of what the repository's own install
  declares.
- **A per-segment compatibility matrix instead of lockstep** — refused with the
  ruling; the reader would need to understand every older format.

### Reference (required)

- [`work/open/W-299-index-package-pin.md`](../work/open/W-299-index-package-pin.md)
- [`work/open/W-300-merged-query-over-segments.md`](../work/open/W-300-merged-query-over-segments.md)
- [`work/regression/2026-10-25-w300-merged-query/VERDICT.md`](../work/regression/2026-10-25-w300-merged-query/VERDICT.md)
  — the ruling quoted above and the steps this record states.
- [`src/fux/plugins.py`](../src/fux/plugins.py) — the row, the digest, the checks.
- [`src/fux/derive/segments.py`](../src/fux/derive/segments.py) — the inflation.

### Veto condition

**Reopen this decision if any of these becomes true:**

1. **A pinned segment is read** — searched or inflated — **while its computed digest
   differs from the pin.**
2. **Python and Node disagree** on whether a pin verifies, or on the refusal's text.
3. **The same pin inflates to different bytes** in Python and in Node.

4. **A merged query scores a segment it did not verify**, or answers
   `scope = repo` with anything but the engine's repository-alone bytes.

**How to check it:** `.venv/bin/python -m pytest -q tests/test_pkg_index.py
tests/test_pkg_merged_query.py` and `node --test node/test/plugins-index.test.mjs`.

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [SR-PLUGINS](0165_plugins.md) · [SR-DOTFUX](0102_fux-directory.md) · [SR-WORK-SCALE](0057_WORK-scale.md) · [SR-DOCTOR](0152_doctor.md)

**Code**

- [`src/fux/plugins.py`](../src/fux/plugins.py)
- [`src/fux/derive/segments.py`](../src/fux/derive/segments.py)
- [`src/fux/schemas/fux-index.schema.json`](../src/fux/schemas/fux-index.schema.json)
- [`src/fux/constants.toml`](../src/fux/constants.toml)
- [`node/src/config/plugins.mjs`](../node/src/config/plugins.mjs)
- [`node/src/derive/segments.mjs`](../node/src/derive/segments.mjs)
- [`tests/test_pkg_index.py`](../tests/test_pkg_index.py)
- [`node/test/plugins-index.test.mjs`](../node/test/plugins-index.test.mjs)
- [`src/fux/query/scan.py`](../src/fux/query/scan.py)
- [`node/src/query/run.mjs`](../node/src/query/run.mjs)
- [`tests/test_pkg_merged_query.py`](../tests/test_pkg_merged_query.py)

**Project docs**

- [`work/open/W-299-index-package-pin.md`](../work/open/W-299-index-package-pin.md)
