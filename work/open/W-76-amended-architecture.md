# W-76 — the amended architecture: nine steps, both forks ruled

> ## Build status, 2026-08-23 (Cowork, in Arpit's absence)
>
> | | |
> |---|---|
> | **[W-73](W-73-weighted-scores-vs-pruning-bound.md)** | **BUILT and proven.** `query/rank.py::Weighting`; weighted `theta`; ceiling scaled by the configuration's supremum. The adversarial test fails without the fix at `w = 500` and passes with it — verified by reverting. Differential harness sweeps weights. **A second divergence was found on the way**: the doc table did not carry `archived`, so the two paths could disagree on the FLAG even at weight 1.0. |
> | **Phase 0** | **BUILT.** stderr nudge on `ask`/`find`/`answer`/`graph`, 5 tests, ADR-GRAPH amended. |
> | **Phase 1 — analyzer** | **BUILT.** `query/analyzer.py` + `query/stem.py`; `ANALYZER_VERSION` -> `v2`; **75/75 published Porter vectors**. |
> | **Phase 1 — record shape** | **BUILT.** Five fields `(body, heading, title, path, ctx)`, **body first** — measured **-36.7 %** on tf vectors *while adding three fields*. `flen` replaces `wlen`, so **field weights are tunable**. `code` dropped (91 % of ingest). Per-field block extrema. `SCHEMA_ID` -> `fux.index.v2`, `RUNTIME_SCHEMA` -> `fux.runtime.v3`. |
> | **fork 3** | **MEASURED FREE.** [`regression/2026-08-23-fork3-per-field-bound`](../regression/2026-08-23-fork3-per-field-bound/report.md) — warm p95 **64.54 ms vs the 150 ms bar**, **+0.0 %** extra blocks read against an oracle tight bound. The zero was checked rather than trusted: bounds differ on 66/101 blocks by a median **1.005**. |
> | **Phase 2 — priors** | **BUILT.** `supersedes:` frontmatter edges (declared, repo-root relative), git commit timestamps in **one** subprocess for the whole corpus, both applied through `Weighting` so the accelerator's bound sees them. 9 tests. |
> | Phase 3 — delta hooks | **not started.** Independent of everything above. |
> | Phase 5 — MCP + line ranges | **not started.** Unblocked now that the record shape is settled. |
> | Phases 6-9 | **not started.** |
> | tests | **1166 unit pass, 0 fail**; **68 e2e pass** (4 fail identically on pristine `HEAD`) |
> | ⚠ | **Nothing is committed** (the concurrent session was mid-flight) and **`fux ingest --full` is owed** — analyzer v2 changes every term hash, so this repo's own v1 index is refused. |
>
> **The gate this was all for:** [`tests/query/test_tunable_weights.py`](../../tests/query/test_tunable_weights.py)
> holds three properties at once — a weight change moves the ranking, touches
> no committed byte, and needs no rebuild. That is ADR-TUNE decision 1's
> membership test made executable.
>
> Every autonomous call: **[`W-76-DECISIONS.md`](W-76-DECISIONS.md)** (D1-D18).

**Status:** OPEN — **STARTABLE.** Both forks were ruled by Arpit on 2026-08-23,
so nothing here waits on a human. Phased; each phase has its own gate.
**Lane:** `agent`
**Filed:** 2026-08-23 (Cowork), from a session that re-argued the parked ideal
set against four rulings
**Spec:** [`../proposals/ideal/07-rulings.amendment.md`](../proposals/ideal/07-rulings.amendment.md)
— the four rulings and what each one amends
**Set:** [`../proposals/ideal/`](../proposals/ideal/README.md) — the six compare
docs the amendment sits on top of
**Ordering dependency:** **[W-73](W-73-weighted-scores-vs-pruning-bound.md) lands
before or with Phase 1** — see §Hazards.

---

## The four rulings, and what each one settles

| # | Arpit's ruling (2026-08-23) | what it settles |
|---|---|---|
| 1 | *"A fresh clone not having an index does not work for me. That part is a big no. You should be able to clone and run the query."* | doc 01's committed/derived split is **refused**; L3's relaxation to result-determinism is **refused** |
| 2 | Analyzer v2 proceeds; its index cost is stated, not assumed | the format bump, and the encoding decided inside it |
| 3 | Enrichment is **partial by declaration** — `enrich=true` on a source line | partial is the steady state, not a degraded mode |
| 4 | *"Enrich should work like a skill in the chat — that way we don't need to integrate the API in the code."* | **L1 and L4 restored**; `fux enrich` keeps only its deterministic halves |

### Fork A — RULED: everything committed

> *"I would like everything committed. … I don't want to run `fux build`. I want
> it committed. I'm going to clone the repo and run the query. That's all."*

**Per-chunk `int8` vectors are COMMITTED.** The 256-bit sign codes become the
**derived accelerator** over them — same results, faster, and `fux build` stays
what it already is: a speed step that never changes an answer. This maps onto
the scan-vs-accelerator split the repo already enforces with a differential law.

Rejected on the way: committing only sign codes and deriving the `int8` rescore.
It is 6× cheaper but a clone would still need `fux build` to match a warm
machine, which is the thing the ruling refuses.

### Fork B — RULED: `ctx` is a BM25F field, with tuning

> *"If it is a small tilt, then go with the first option, and keep the tuning
> parameters as well. We'll build it out. Let's see how it works."*

`ctx` enters ranking as a normal weighted field — the variant with the published
**−49 % top-20 failure** result. Two consequences the ruling carries with it:

1. **`w_ctx` must be a tune key**, which is impossible while field weights are
   baked into the committed `wlen`. **Phase 1 must absorb ADR-TUNE's `wlen`
   fix** — it is no longer optional. See §Hazards.
2. **"If it is a small tilt" is a condition, not an aside.** It becomes veto
   condition 3 below, with a measurement that decides it.

---

## The law the rulings imply

> **Sufficiency.** The committed plane must be sufficient to answer. The derived
> plane may make an answer faster or better — **never possible.**

Arpit's call: **stays proposal-level, not promoted to L8.** It is recorded here
because it is what stopped doc 01, and because Phase 7's design follows from it.
It binds nothing on its own; the ruling is what binds.

---

## The measurements this item is built on

All taken 2026-08-23 on this repo's committed index (411 documents), method
stated per row. **None is a prediction; none is above the 10 000-document
ceiling.**

| quantity | value | method |
|---|---|---|
| committed index | 5 118 359 B | sum of record lines in `.fux/index/*.jsonl` |
| source bytes indexed | 4 861 067 B | `getsize` of each record's `loc` |
| **index : source ratio** | **1.053×** | the two above |
| `terms` share | **91.5 %** | per-key JSON size summed per record |
| `edges` · `phrases` · `code` | 3.7 % · 2.2 % · **0.4 %** | same |
| **postings that are body-only** | **92.5 %** | `[0,b]` vs `[h,0]` vs `[h,b]` over 186 799 postings |
| heading-only · both | 2.4 % · 5.1 % | same |
| **tf bytes, body-first sparse** | **−36.7 %** | 941 130 B → 595 492 B, trailing zeros omitted, *with five fields* |
| identifier splitting, tokens | ×1.03 | 546 142 → 563 296 |
| identifier splitting, posting rows | ×1.02 | 190 512 → 193 884 distinct-per-doc |
| heading sections | 9.8 /doc (max 216) | 4 042 across 411 documents |
| full enrichment cost | ~$1.24 | ~1.22 M input tokens @ $1.02/M cached |

### The size consequence of the rulings, assembled

| | delta | running total |
|---|---|---|
| today | — | 5.12 MB |
| tf vectors → body-first sparse | −345 KB | 4.78 MB |
| identifier splitting (+2 % rows) | +94 KB | 4.87 MB |
| `code` field deleted | −22 KB | 4.85 MB |
| **analyzer v2 subtotal** | **−5 %** | **the index gets smaller** |
| per-chunk `int8`, committed (fork A) | +1.39 MB | **6.24 MB** |
| `ctx` postings for enriched scopes | *unmeasured* | measured in Phase 8 |
| **net** | **+22 %** | **~152 MB at 10 000 docs of this density** |

**152 MB is the largest single consequence of these rulings** and Arpit accepted
it on sight. It is recorded here so no later session treats it as a surprise.

---

## Phases

Each phase is independently gateable. **Phases 1–3 and 5 need no new dependency
and no law change.** Phases 6–8 add optional runtime dependencies, each behind a
stdlib fallback.

### Phase 0 — the `fux build` nudge · **Model: Sonnet** · *ships independently, today*

**Arpit, 2026-08-23: `fux build` STAYS.** It is not deleted and not made
implicit. What was missing is that nothing ever tells a fresh clone it exists.

- Trigger, and only this: **committed shards present, no accelerator built** —
  a clone, a merge, a checkout. Not after `fux setup`, which runs before there
  is an index and would fire for people who never clone anything.
- Surface: the read verbs — `ask`, `find`, `answer`, `graph`.
- Rules, inherited verbatim from W-66 Phase 3's `_declare_pending`:
  **stderr never stdout** (so `--json` stays a contract and `fux find | xargs`
  does not swallow it as a filename), **ASCII only** (a Windows codepage cannot
  encode a fancy arrow and the process dies on `print()`), and it **declares,
  never gates**.
- Every invocation, not once — `_declare_pending` prints every time, and "once"
  needs state to remember, which is a new thing to get wrong.
- The text must carry **"results are identical either way"**. Without it a
  reader assumes building might change their answers, which is precisely the
  promise the differential law exists to make.

**Gate:** the stdout bytes of every read verb are unchanged, asserted the way
the W-64 progress plane's stdout comparison already is.

### Phase 1 — analyzer v2 + the format bump · **Model: Opus**

The encoding and the `wlen` migration are arguments, not typing; the rest is
mechanical.

- Split identifiers (camelCase · snake_case · kebab), **before lowercasing** —
  the current order destroys camelCase irrecoverably.
- Porter/Snowball stemming. **Hash the final analyzed token**: split → lower →
  stopword → stem → *then* `blake2b`. Reversed, ingest and query hash different
  strings and nothing matches.
- Fields 2 → 5: **`body` first**, then `heading`, `title`, `path`, `ctx`.
  Field order is load-bearing: body-first plus trailing-zero omission is what
  produces the measured −36.7 %.
- Heading/title bigram shingles.
- **Absorb ADR-TUNE's `wlen` fix**: commit the five per-field token counts,
  derive `wlen` at query time. Forced by fork B (see §Hazards).
- **Delete the `code` field — for time, not bytes.** It is 0.4 % of the index
  and **91 % of every full ingest**: the filed cost profile puts 3.996 s of a
  4.38 s 1 000-doc ingest, and 21.41 s of 23.30 s at 5 000, inside
  `_fuxvec_code`. Dropping it here makes ingest and every hook run **~11×
  faster** until Phase 7 puts per-chunk vectors back.
- **`--hybrid` has no lane to fuse between Phase 1 and Phase 7.** Keep the
  flag accepted and make it **fail loudly**, naming Phase 7 — the
  `ingest --refresh-urls` precedent (hide-and-error) rather than the
  `fux url` one (delete outright), because 1.0.0 is on PyPI. It is deleted
  for real when Phase 7's `[dense] mode` lands. A flag that silently becomes
  a no-op is worse than one that errors.
- `analyzer` v1 → v2 in the shard header; **a full re-ingest is owed.**
  Per ADR-INDEX-LIFECYCLE decision 9 the value-encoding change alone bumps
  neither `_format` nor `analyzer` — the field-set change is what bumps
  `analyzer`, and `tf_fields` in the header changes with it.

**Gate:** hit@5 and MRR on the 50 goldens, ≥ today. Index size delta stated
against the table above. A one-line equality gate on `wlen` derived-vs-committed.

### Phase 2 — supersession offset + recency prior · **Model: Sonnet**

Port is already present (`rrf(offsets=)`); archived ADR-0015 calibrated offset 15.
Recency from `git log -1 --format=%ct` per document.

**Gate:** goldens ≥ Phase 1, and the "retired ADR outranks live" class → 0.

### Phase 3 — delta hooks · **Model: Sonnet**

`git diff --name-only` for the walk; a `target → {referencing doc ids}` reverse
index in the derived plane for edges; additive statistics. **This is now the only
fix for R5** — ruling 1 removed the index-relocation alternative.

**Gate:** re-run R5. Add `fux doctor --verify-delta` (full ingest, assert
equality) to CI nightly.

### Phase 4 — *deleted by ruling 1*

Was "split committed/derived". Cancelled. The number is retained rather than
renumbering the rest.

### Phase 5 — MCP server + line-range citations · **Model: Sonnet**

`fux_search` · `fux_passage` · `fux_related` · `fux_path` over stdio, warm
process. `loc#p3` → `path:L12-L40` everywhere (text, `--json`, MCP); passage
ordinal kept as a secondary field.

**Gate:** an agent completes the playground tasks in fewer tool calls and fewer
tokens than grep. Both counted.

### Phase 6 — reranker at refer time · **Model: Sonnet**

17–32 M cross-encoder over the top-50 fetched passages. Optional dependency
(`onnxruntime`) with a BM25F-passage-rescore fallback and a differential test.
Records `reranker_sha` in the bundle.

**Gate:** failure rate on the goldens, top-20 → top-5.

### Phase 7 — per-chunk vectors, COMMITTED · **Model: Opus**

Fork A's ruling lands here.

- Chunk on headings (reuse `refer/chunk.py`).
- Embed per chunk; **commit `int8`**; derive the 256-bit Hamming prefilter as
  the accelerator, under the existing differential law.
- Query: Hamming prefilter → exact `int8` rescore → max-sim per document.
- **The `code` field is promoted, not replaced.** Today's 256-bit sign code
  *is* the dense lane; here the same Hamming scan returns as the **derived
  prefilter** over the committed `int8` vectors — per chunk instead of per
  document, and a fast first pass instead of the answer. The unit changes
  (document → chunk, ~9.8×) and the precision changes (1 bit/dim → 8), but
  the algorithm is the one already in `derive/dense.py`.
- **Gated fusion**, not unconditional RRF.
- Keep the embedding path **pure Python**. ADR-GRAPH proved fux's float maths is
  byte-identical across x86-64 Linux and arm64 macOS; a numpy fast path would
  put that at risk, and under ruling 1 these bytes are committed.

**Gate:** the current 3-fixed/9-broken result must become **≥ 3-fixed / 0-broken**.
Plus: ingest wall-clock stated. Embedding is already **92 % of a full ingest** at
one vector per document; this is ~9.8×.

### Phase 8 — `fux enrich` + the `fux-enrich` skill · **Model: Opus**

- `enrich=true` attribute on `.fux/sources/dirs`, same closed grammar as
  `archived=true`.
- `fux enrich --plan` (worklist) and `--check` (validate + coverage). **No
  `--model` flag** — there is no networked path to fence.
- Generation is a **skill**, not code: `.claude/skills/fux-enrich/SKILL.md` plus
  the Copilot and Kiro renderings, installed from `[agents] install`.
- Frontmatter: fux **verifies** `source_sha` (it can compute it) and **records**
  `model` (it cannot verify it). A sha mismatch means stale; ingest ignores it.
- `ctx` field statistics computed **over enriched documents only** — counting
  un-enriched docs as ctx-length-0 collapses `avglen_ctx` and spuriously
  down-weights every enriched document.
- `w_ctx` ships as a **`.fux/tune.toml`** key under `[ranking]` — the file is
  already specified by [ADR-TUNE](../../docs/adr/0038_tuning.md) (committed,
  written once by `fux setup`, never rewritten, **never read on the ingest
  path**). Depends on Phase 1's `wlen` fix; ADR-TUNE itself is blocked by
  W-73.
- Orphaned enrichment is **not** auto-deleted; `--prune` is explicit, so a
  reverted document recovers its enrichment for free.

**Gate:** failure-rate delta with and without. **Plus the tilt measurement** —
see veto 3.

### Phase 9 — `refs/fux/<tree>` · **Model: Sonnet** · *optional, lowest priority*

**Demoted by ruling 1 to derived-cache warmth only.** It can never be a
correctness path: a fresh `git clone` neither runs hooks (they live in `.git/`,
which is not cloned) nor fetches custom refs. Its only remaining value is
arriving with a warm accelerator.

**Gate:** clone → `--fast` warm without a local build.

---

## Hazards

1. **W-73 must land before or with Phase 1.** The accelerator prunes on
   *unweighted* bounds; Phase 1 takes the number of field weights from two to
   five. Building analyzer v2 on an unfixed pruning bound multiplies exactly the
   defect W-73 exists to close.
2. **The `wlen` fix is mandatory, not opportunistic.** ADR-TUNE decision 6 —
   *no committed field may be a function of a tunable* — already has one
   violation (`HEADING_WEIGHT` baked into committed `wlen`). Phase 1 takes that
   from one field to five. ADR-TUNE's own remedy is *"commit the token counts
   and derive `wlen` at query time when the format next moves"*; Phase 1 **is**
   that move, and fork B's ruling (keep the tuning parameters) is unbuildable
   without it.
3. **`fux-enrich` must be explicitly invoked, never ambient.** Two of the three
   shipped agent renderings are ambient (`applyTo: "**"`, `inclusion: always`)
   and enter every request for every developer in the repo. **An ambient skill
   that writes into a committed directory is a different risk class.** This is
   veto condition 4, not a note.
4. **Provenance downgrades from measured to declared.** With an SDK call fux
   would know which model ran; with a skill, an agent is asked to stamp it.
   Shape validation plus PR review is the mitigation — a *different* guarantee,
   and the record must not describe it as the same one.
5. **Phase 7 has no batch loop for enrichment and Phase 8 needs one.** 4 042
   chunks here; one agent session grinding all of them drifts and half-finishes.
   The scope-by-scope design is the answer — `docs/adr` is 41 documents, one
   comfortable session — and `--plan`/`--check` make it resumable.

---

## Veto conditions

1. **Phase 1 ships without the `wlen` fix.** Then `w_ctx` is hardcoded, fork B's
   ruling is unimplementable, and ADR-TUNE's violation has quintupled. Return
   to Phase 1.
2. **A phase makes the committed plane insufficient to answer.** Any change
   after which `git clone && fux ask` needs a build, a fetch, or a network call
   before it returns an answer violates ruling 1 directly.
3. **The tilt is not small.** Fork B was ruled *conditionally*. The measurement:
   run the 50 goldens at `w_ctx = 0` and `w_ctx = 1`; report (a) the fraction of
   goldens whose top-5 **mixes** enriched and un-enriched documents — the only
   ones that can tilt at all — and (b) within that fraction, how many change
   rank. **Proposed threshold: if (b) exceeds 10 % of the graded set, the field
   variant returns to Arpit** with the gated variant and a contribution cap as
   the alternatives. *The threshold is proposed, not ruled — Arpit owns it.*
4. **An ambient rendering of `fux-enrich` reaches a consumer repo.** Checked the
   way ADR-AGENT-POLICY veto 5 already checks the ambient renderings.
5. **Phase 7 introduces numpy or any non-stdlib maths on the committed
   embedding path.** Ruling 1 makes those bytes committed; ADR-GRAPH's
   cross-architecture result is what makes committing them safe, and it was
   proved for pure Python only.

---

## What is owed, and is not discharged here

- **The 10 000-document re-weighting.** The ideal set's README banner still
  stands: several proposed verdicts are keyed to sizes fux is not built for and
  **cannot fire as written** — doc 02's engine-replacement trigger at 2×10⁵,
  doc 05's 100k cost table, doc 01's 100k hook row. The rulings re-decided the
  architecture on grounds independent of corpus size, so this does **not** block
  Phases 1–3; it blocks any phase that wants to cite one of those verdicts as a
  reason.
- **A `work/DOC-REGISTRY.md` bump** on the `proposals/` row for the amendment
  and on `OPEN-WORK.md`'s row.
- **No ADR is amended by this item.** ADR-TUNE, ADR-INDEX-LIFECYCLE,
  ADR-T1-ACCELERATOR, ADR-CLI, ADR-DIR-LIST and ADR-AGENT-POLICY all take
  amendments **on the phase that builds the change**, never in advance.
