---
type: Evidence
run: 2026-09-21-golden-three-engines
description: "The arms manifest for W-204 phase B. Written before any A-vs-B row, per PRE-REG-BENCH-V1-V2-HEAD §6: venv, interpreter, resolved dependencies, wheel hash or git sha, and the exact command line per arm."
filed: 2026-09-21
---

# ARMS — `1.0.0` · `2.0.1` · `HEAD`, exactly as installed and invoked

🔴 **Written before the first A-vs-B row**
([PRE-REG-BENCH-V1-V2-HEAD](../../../benchmark/PRE-REGISTRATION-V1-V2-HEAD.md) §6).
An arm nobody can rebuild is an anecdote with three decimal places.

## The three engines

| | **v1** | **v2** | **HEAD** |
|---|---|---|---|
| version string | `fux 1.0.0` | `fux 2.0.1` | `fux 3.0.0-alpha.1` |
| released | 2026-08-22, tag `v1.0.0` | tag `v2.0.1` | not released |
| install | `uv pip install fux-engine==1.0.0` | `uv pip install fux-engine==2.0.1` | this working tree, editable |
| venv | `~/my_programs/fux-lab/arms/v1` | `~/my_programs/fux-lab/arms/v2` | `~/my_programs/fux/.venv` |
| interpreter | **CPython 3.11.15** | **CPython 3.11.15** | **CPython 3.14.3** |
| wheel sha256 | `a29844a3fb35677f38fd313738cf0b51ecde76433fd2cc56ffa83fc4057652fc` | `df5df4aa61cda46f08fdec63212597a150e175dad8d3603889e3c8a307f8e5fd` | git `7a88a1657a183157a1cd842e5d392d55f65823f2` |
| index format written | `fux.index.v1` | `fux.index.v2` | **`fux.index.v4`**, analyzer `v2` |
| runtime dependencies | **none** | **none** | **none** (`pytest` and its chain are dev-only) |

⚠ **The interpreters differ, and it is recorded rather than equalised.** `uv`
resolves `fux-engine==1.0.0` on 3.11 and the working tree runs on 3.14. Holding
all three on one interpreter would be the cleaner experiment; **it is not
available**, because a released wheel's `Requires-Python` is part of what was
released. The macOS system `python3` here is **3.9.6**, below fux's floor of 3.11
([L7](../../../../records/0008_LAW-7-python-311.md)) — which is why
`python3 -m venv` + `pip install fux-engine==1.0.0` fails with *"No matching
distribution found"*, a message that reads exactly like *the version was never
published*. It was published; the interpreter was too old.

⚠ **All three carry no runtime dependency.** v1 and v2 predate the 2026-09-06
amendment to [L1](../../../../records/0003_LAW-1-zero-cost.md) that withdrew the
zero-dependency guarantee, and HEAD has not yet taken one. So **this benchmark
does not price that amendment**, and no row in it may be read as doing so.

## 🔴 Two asymmetries measured on a smoke arm BEFORE the run, not discovered in it

### 1 · v1.0.0 cannot see four of the twenty-eight seed documents

`fux-engine 1.0.0` has **no `.fux/formats.toml`** and indexes `.md` and `.txt`
only. On `rung-seed` it reports:

```
ingested 24 docs (24 changed, 0 carried forward), 4 skipped, 23 shards written
  skip seed/02-sensor-thresholds.yaml: not an indexed file type
  skip seed/06-re-fw-telematics-cutover.eml: not an indexed file type
  skip seed/09-dock-scheduling-wiki-export.html: not an indexed file type
  skip seed/archive/a03-dock-scheduling-wiki-2021.html: not an indexed file type
```

v2.0.1 on the same bytes: `ingested 28 docs … 0 not indexed, 0 skipped`.

🔴 **This is part of the arm, and it is classified as such HERE, before any row**
(pre-registration §7). Reading `.yaml`, `.eml` and `.html` is a capability later
versions added; there is no way to give it to v1 because the mechanism that
carries it does not exist in v1. Forcing it would measure an engine nobody
shipped.

⚠ **The consequence for every v1 comparison, stated once:** a question whose
answer lives in one of those four documents is a **structural miss for v1, not a
ranking difference**, and `02-sensor-thresholds.yaml` is the primary target of
**8 of the 43 id-queries**. So a `v1 → v2` figure is dominated by *v2 can read
four more file types*, which is a real product difference and **is not a ranking
result**. Every claim in this run's report must be worded end to end, and any
sentence of the form *"v2 ranks better than v1"* is wrong on its face.

### 2 · v1.0.0's `ask` has no `--band`

v1's parser is `[--json] [--fast | --scan] [--top N] [--explain] [--hybrid]`.
**argparse exits `2` on an unknown flag**, so a harness that hardcoded `--band`
would record an empty result for every v1 call — thousands of them — and they
would read as a catastrophic ranking collapse rather than a flag error.

**So the invocation is per arm:**

| | `ask` | `answer` | ingest |
|---|---|---|---|
| **v1** | `ask "<q>" --json --top 10` | `answer "<q>" --json` | `ingest --full --no-progress` |
| **v2** | `ask "<q>" --json --band --top 10` | `answer "<q>" --json` | `ingest --full --no-progress` |
| **HEAD** | `ask "<q>" --json --band --top 10` | `answer "<q>" --json` | `ingest --full --no-progress` |

🔴 **Capture 2's band column therefore exists for two arms of three.** Every
statement about the confidence band in this benchmark is a **`v2 → HEAD`**
statement, and `band`/`answerable` are `null` on every v1 row — **recorded as
null, never as `weak`.**

## 🔴 Each arm's own ranking defaults — read this before any `v2 → HEAD` number

Printed from each arm's own `.fux/tune.toml`, written by that arm's own
`fux setup` on its own corpus copy:

| | `[bm25f] k1` | **`[bm25f] b`** | body · heading · title · path · ctx |
|---|---:|---:|---|
| **v1** | — | — | — · **no `tune.toml` at all**: v1.0.0 has no ranking knobs |
| **v2** | 1.2 | 🔴 **0.75** | 1.0 · 3.0 · 2.0 · 1.5 · 1.0 |
| **HEAD** | 1.2 | 🔴 **0.15** | 1.0 · 3.0 · 2.0 · 1.5 · 1.0 |

🔴 **`b` is the single largest difference between v2 and HEAD, and it is a
MEASURED default change rather than a new algorithm.**
[W-144](../../2026-09-16-b-sweep-2/VERDICT.md) took `b` from `0.75` to `0.15` on
2026-09-16 — the first ranking default in
[SR-RANKING](../../../../records/0111_ranking.md) that is measured rather than
inherited.

**So when capture 2 reports that `v2 → HEAD` changes the ranked list on 125 of
125 queries, the honest reading is *one knob moved and it reorders everything*,
not *the engine was rewritten*.** The pre-registration's rule — *"the `[bm25f]`
`b` default differs between arms; that IS the arm, not a knob to equalise"* —
is what makes those rows legitimate, and this table is what stops them being
read as something they are not.

⚠ **This is not a confound to correct.** Equalising `b` would measure a version
of HEAD nobody ships against a version of v2 nobody shipped. It is a fact to
state, and it is stated here rather than in the report's conclusion.

## The corpus each arm gets

[`arm_corpus.py`](../../../../tools/quality-controls/arm_corpus.py), one copy per
arm per rung under `~/my_programs/fux-lab/arms/runs/<arm>/<rung>/`.

- **Same document bytes**, copied from the frozen rung; `seed/` and `ext/` only.
- **Its own `git init`** and **its own `fux setup`**, so every default is that
  arm's. `[bm25f] b` differing between arms **is** the arm.
- **Identical source declarations** — `seed`, `seed/archive archived=true`,
  `ext`, `ext/archive archived=true`.
- 🔴 **Nothing writes into `fux-lab/corpora/golden/rung-*/`.** Those are frozen,
  and `corpora/` is kept, not scratch.

🔴 **Every document is committed at one stamp, not at its own date — and that
is sharper than it first looks.** The frozen rungs commit each file at its own
date; an `arm_corpus.py` copy commits everything at one.

**`mtime` is not a weight in v2 or HEAD — it is a TIE-BREAK.** `query/rank.py`
sorts `superseded → recency → priority → id`, and its own comment says the three
`[ranking]` priors were removed so *"`superseded` and `mtime` reach ranking here
and nowhere else"*. So a flat-`mtime` corpus does not shift scores; **it changes
which of two exactly-tied documents comes first**, by collapsing the recency
tie-break into the `id` tie-break.

| pair | affected? | why |
|---|---|---|
| **v1 → v2** | **no** | both arms are flat-`mtime` copies — symmetric, so the tie-break is the same on both sides |
| **v2 → HEAD** | 🔴 **YES** | HEAD's rows come from the **frozen, dated** rung and v2's from a flat copy, so tied documents can order differently for a reason that is not the engine |
| **v1 → HEAD** | 🔴 **YES** | same asymmetry |

**The remedy, named rather than left implicit:** re-run HEAD through
`arm_corpus.py` so all three arms share a flat-`mtime` corpus. It costs 5 984
calls and it is the methodologically clean choice; it was **not** taken up front
because HEAD's 5 984 rows already exist from phase A at this exact sha.

🔴 **So the rule for this run:** any `v2 → HEAD` or `v1 → HEAD` result that lands
**within the tie-break's reach** — a net near decision 19's floor, or a flip list
whose rows are `tie: true` — is **not reported as a version difference** until
HEAD has been re-run flat. A `v1 → v2` result carries no such caveat.

## HEAD's rows are not re-run

HEAD's rankings and answers are
[`2026-09-21-golden-ladder-outputs-set-3`](../../2026-09-21-golden-ladder-outputs-set-3/report.md),
produced at `7a88a165` — the sha this manifest names. Re-running HEAD would spend
6 000 calls to reproduce a file that already exists and would introduce a second
engine state to reconcile.

⚠ **HEAD's rows came from the FROZEN RUNG, not from an `arm_corpus.py` copy**,
so HEAD's corpus carries per-document commit dates and v1's and v2's do not.
🔴 **That is a real asymmetry and it is declared here rather than found later:**
it does not affect BM25F ranking, which reads no `mtime`, and it **would** affect
any recency-weighted comparison. None is made, and a later reader who wants one
must re-run HEAD through `arm_corpus.py` first.
