---
type: Standing Record
kind: component
name: SR-CONSTANTS
title: SR-CONSTANTS (0159) — the engine's fixed values live in one TOML file both planes read
description: "src/fux/constants.toml holds every fixed engine value — schema ids, format and rules versions, artefact names, decoder versions, and the numbers a file format or protocol defines. One Python loader and one Node loader read it; the Node bundle carries it inlined; a missing table or key stops the process naming it."
status: accepted
date: 2026-09-27
feature: "`src/fux/constants.toml` and its two loaders"
owns: [node/src/config/constants.mjs@916abe09cc01, src/fux/constants.py@660979af88ee, src/fux/constants.toml@8ec5ecd36b1b]
laws: [L10, L12]
timestamp: 2026-09-27T00:00:00Z
content_sha: e8306ec7d46089f32a90127e13ba25b958e66ed8dcaf6f23be70783c29b016da
ratifies: "W-225 — Arpit, 2026-09-27: fixed values go to 'another internal-to-code file for the rest of the values like SCHEMA, RULES_VERSION'; on the R5 scan the same day, a number fixed by a file format, protocol or algorithm is a fixed value too (R7)"
---

<!-- COMPONENTS-START — GENERATED from records/README.md's OWNERSHIP and DESCRIBES tables by scripts/gen-components.py. Do not edit by hand: change the table, then run `python scripts/gen-components.py --write`. -->

**Owns** — the components this record decides:

- [`node/src/config/constants.mjs`](../node/src/config/constants.mjs) · file
- [`src/fux/constants.py`](../src/fux/constants.py) · file
- [`src/fux/constants.toml`](../src/fux/constants.toml) · file

<!-- COMPONENTS-END -->

# SR-CONSTANTS — the engine's fixed values live in one TOML file both planes read

## §1 — For humans

**Law [L12](0013_LAW-12-values-live-in-config.md) gives every value one home.**
A *tunable* value — one a person could choose differently — lives in the
consumer's own TOML. A *fixed* value is different: changing it changes what a
committed byte means. `fux.index.v5`, the name `graph.json`, a decoder's
`VERSION`, the eight bytes of a PNG chunk header. Nobody should edit those per
repository, and both runtimes must agree on every one.

**This record decides where the fixed ones live: `src/fux/constants.toml`.** It
ships inside the wheel, and the Node bundle carries it inlined as a string. The
engine code keeps readable names — `SCHEMA_ID`, `GRAPH_NAME` — but each one is
*read* from this file, never written as a literal.

```mermaid
flowchart LR
    K["src/fux/constants.toml"]
    P["fux/constants.py<br/>fixed(table, key)"]
    N["node/src/config/constants.mjs<br/>fixed(table, key)"]
    B["the Node bundle<br/>(file inlined at publish)"]
    E["missing table or key<br/>→ FuxError naming it"]
    K --> P
    K --> N
    N -->|"@fux-inline"| B
    P -.-> E
    N -.-> E
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
                     src/fux/constants.toml
                       |                  |
                       v                  v
        fux/constants.py         node/src/config/constants.mjs
        fixed(table, key)        fixed(table, key)
                       :                  |
                       :                  | @fux-inline (the bundler)
                       :                  v
                       :          the Node bundle -- the file's text inlined
                       v
        missing table or key -> FuxError naming the file, table and key
```

</details>

---

## §2 — For agents

### Context

Before W-225 every fixed value was a module literal, and the ones shared by the
two runtimes were spelled twice — `SCHEMA_ID` in `store/format.py` and in
`store/format.mjs` — held equal by tests that grepped the Node source for the
literal. Law L12 (decisions 2 and 4) requires one home read by both planes, and
decision 6a (R7) widens *fixed* to the numbers a file format, a protocol or the
algorithm defines.

### Decision

1. **One file, `src/fux/constants.toml`, holds every fixed engine value.** It is
   organised in tables by subject — `[index]`, `[graph]`, `[files]`,
   `[runtime]`, `[decoders.<name>]`, `[receipt]`, `[fuse]`, `[versions]`,
   `[templates]`, `[schema_files]`, … — and each key carries the comment that
   explains it. `[schema_files] package` names the one package every declared
   shape ships in, `fux.schemas` ([SR-LAWS](0001_LAWS.md) decision 6, W-226).
   Three
   of its values are algorithm bounds a record already ruled NOT tunable, which
   is what makes them fixed rather than a `tune.toml` key: `fux path`'s work
   budget (`[graph] path_expansion_budget`), the community sweep cap that runs
   in `fux build` (`[graph] community_max_sweeps`), and RRF's published `k`
   (`[fuse] rrf_k`). The explanation of *why a value is what it is*
   stays beside the code that uses it.

2. **Two loaders, one sentence.** [`src/fux/constants.py`](../src/fux/constants.py)
   and [`node/src/config/constants.mjs`](../node/src/config/constants.mjs)
   expose `fixed(table, key)` and `table(name)`. A missing table or key raises
   `FuxError` reading `src/fux/constants.toml: [<table>] <key> is missing` in
   both runtimes — the repository path, because the bundle has no path of its
   own.

3. **A module binds a name at import.** `SCHEMA_ID = fixed("index", "schema")`
   is the pattern: the name keeps its spelling for every caller, and a hot loop
   reads a module attribute, not a dictionary.

4. **The wheel ships the file beside the loader** (hatch packages
   `src/fux/**`). **The Node bundle carries it inlined:** the loader reads it
   with `/* @fux-inline src/fux/constants.toml */ readFileSync(...)`, and
   [`store/nodebundle.py`](../src/fux/store/nodebundle.py) replaces that
   expression with the file's text as a string literal
   ([L10](0011_LAW-10-bundled-output.md)). A named file that does not exist
   fails the bundle.

5. **Built-in decoders import the loader absolutely** — `from fux.constants
   import fixed` — because `fux setup` copies them into a consumer's
   `.fux/decoders/`, where a relative import has no package to resolve against
   ([SR-DECODE](0139_decode.md) decision 11).

6. **Python's `constants.py` imports only the standard library and `.errors`.**
   `hatch_build.py` loads the bundler inside an isolated build, and the bundler
   reads its artefact names through this module.

7. **A consumer never sees this file and cannot change it.** A value a consumer
   may choose is not fixed, and belongs in their `fux.toml` or a `.fux/*.toml`
   ([L12](0013_LAW-12-values-live-in-config.md) decision 1).

<!-- L12-NOTE-START -->

**W-225 stage 3a (2026-09-27)** added `[templates] output` — the output
template's file name — and `[answer] candidates`, the number of documents
`fux answer` hands the refer plane. The count stays fixed because every extra
candidate is a real fetch against someone's source system.

**W-225 stage 3b (2026-09-27)** added `[index] shards` — `256`, because
`shard = blake2b(id, digest_size=1)`. `fux.toml [index] shards` is a check that
refuses any other number, never a setting ([SR-CONFIG](0113_config.md)
decisions 3 and 17; SR-LAW-12 decision 9a).

<!-- L12-NOTE-END -->

<!-- L12-VALUES-START -->
<!-- L12-VALUES-END -->

**W-225 stage 4a (2026-09-27)** added `[templates] formats_limits` — the file name of the decoder-caps template appended to a seeded `formats.toml`.

### Consequences

- **Parity between the runtimes holds by construction** for every shared fixed
  value. The parity tests that grepped Node source for a literal now evaluate
  the Node export instead (`tests/test_node_config_parity.py::_node_export`).
- **A fixed value changes in one line**, and the change lands in both runtimes
  and the next bundle together.
- **The file grows with R7.** Byte offsets and protocol codes are named keys
  rather than inline numbers; the binary decoders read more names and fewer
  digits.

### Alternatives considered

- **Keep fixed values as code constants.** Rejected by Arpit, 2026-09-27
  (SR-LAW-12 §Alternatives): Node and Python must not each carry one.
- **A JSON file.** Rejected: every other config file fux reads is TOML, both
  runtimes already carry a TOML reader, and JSON carries no comments — the
  comment on a key is half of why it is safe to leave alone.
- **Generate a `.mjs` from the TOML at build time.** Rejected: a second
  generated artefact in the checkout, and a Node test run against `node/src/`
  would need the generator to have run first. Inlining at bundle time needs
  neither.

### Reference (required)

- [SR-LAW-12](0013_LAW-12-values-live-in-config.md) decisions 2, 4, 6a — the law this implements.
- [W-225](../work/open/W-225-values-live-in-config.md) — the migration.
- [L12 classify](../work/compare/l12-classify.compare.md) — which values are fixed, and R7–R10.
- [SR-LAW-10](0011_LAW-10-bundled-output.md) — why the bundle carries the file inlined.

### Veto condition

**Reopen if** a fixed engine value is found as a literal in `src/fux/**` or
`node/src/**` outside `setup.py` and `templates/`, or if the two loaders print
different sentences for the same missing key.

**How to check it:**

```bash
.venv/bin/python -m pytest -q tests/test_l12_values_live_in_config.py
# expect: passed — the AST test fails on any literal not in its reviewed allow-list
```

---

## References

**Records** — [SR-LAW-10](0011_LAW-10-bundled-output.md) ·
[SR-LAW-12](0013_LAW-12-values-live-in-config.md) · [SR-DECODE](0139_decode.md)

**Work** — [W-225](../work/open/W-225-values-live-in-config.md) ·
[L12 classify](../work/compare/l12-classify.compare.md)
