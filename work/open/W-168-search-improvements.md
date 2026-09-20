---
type: Handoff
name: W-168
description: "The ten ranking improvements of proposals/search-improvements-v3.md, promoted as one program with ten gated steps: anchor text, corpus-mined expansion, unstemmed identifier field, RM3, supersession-aware ranking, SDM proximity, MMR diversification, git authority prior, intent → doc-type prior, section-level units. Each step is its own golden question → pre-registration → build → measure → keep/remove; never two in one arm."
item: W-168
filed: 2026-09-14
ball: agent
---

## ✅ RULED 2026-09-20 (Arpit, Cowork) — step 2 leaves this item

*"W-168 — I agree, let's go with the recommended approach."* So: **Codex adds
identifiers of the failing shape** (shared prefix + short number — `RF-118 /
RF-119 / RF-120`, `PROJ-123 / PROJ-124`) **to the seed with W-191's link-bearing documents, so the ladder is rebuilt
once. Later the same day: Claude authors both as set 3** — W-204 input **I-2** —
and no step here waits on Codex.

**Step 2 (the exact identifier field) is no longer here** — it is part 2 of
[W-205](W-205-identifiers-reachable-and-whole.md), merged with the frontmatter
and analyzer defects on Arpit's ruling that they are one subject. Steps 3–10
stay. **Ball → 🟡, waiting on W-204** (every remaining step needs a golden
question or document that only that item's inputs produce).


# W-168 — the ten search improvements, one program

**Model: Opus for #4, #8, #9, #10 (drift, bias, a plane change); Sonnet for the rest once
a golden question and a pre-registration exist.**

**Promoted 2026-09-14 by Arpit** from
[`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md), which
stays the spec (the per-idea table in its §1 and §3b is the definition of done here, not
repeated). **W-156 ruled 2026-09-14:** every step is a ranking change and lands under
[SR-RS](../../records/0133_predictions.md) decision 19's paired floor on golden data —
the single-corpus sentence is gone ([SR-LAW-0](../../records/0002_LAW-0-authority.md)
decision 2a). Nothing agent-side waits.

## ✅ MEASURED 2026-09-18 — step 2's stopping reason was wrong, and so was the premise's consequence

**Arpit, 2026-09-18:** *"Codex is not going to run it. You go ahead and run it."*
So this session wrote the 33 id-queries (one per identifier, targets by grep
over the seed, no key) and ran the baseline on rung-00100, 01000 and 10000:
[the run](../regression/2026-09-18-identifier-headroom/report.md) · `informed`.

| rung | primary hit@3 | headroom |
|---|---:|---:|
| 100 | **30/33** | 3 |
| 1 000 | 29/33 | 4 |
| 10 000 | **30/33** | 3 |

- 🔴 **Mangling is symmetric.** `dairi` IS in the index — the document is
  analyzed by the same analyzer. Split identifiers retrieve at ~90 % top-3 at
  every rung. The survival report compared query tokens to raw text.
- 🔴 **Headroom is 3–4 of 33, below the floor of 6 flips, on every rung.**
  Step 2 cannot be given a verdict on this corpus **whatever questions are
  written** — prompt 8 does not unblock it. What is missing is identifiers of
  the failing shape (a shared prefix + short number, `PROJ-123`) in the seed.
- 🔴 **The absolute misses are frontmatter-only identifiers**, unindexed by
  `parse.py`'s meta/body split — a different defect, filed as
  [W-201 → W-205](W-205-identifiers-reachable-and-whole.md).

**Step 2 stays stopped, for the corrected reason.** Prompt 8 is withdrawn as
the unblock; the unblock is a seed with the failing shape, which is a Codex
corpus-prompt note, or a ruling to descope the field until a consumer corpus
shows the shape.

## 🔴 Step 2 is STOPPED BEFORE IT STARTS (2026-09-16) — by this item's own rule

[The survival check](../regression/2026-09-16-identifier-survival/report.md).

**The proposal's §0: *"Build the golden question before the feature, or the
verdict is theatre."*** Measured:

| question set | questions | carrying an identifier |
|---|---:|---:|
| set 1 | 125 | **4** |
| set 2 | 124 | **0** |

**4 is below the floor of all floors.** A net of 6 is the minimum that clears α at
*any* discordant count, and 4 questions cannot produce 6 flips — so **no arm on
this set can return a result**, whatever the field does. A **data defect
(d23b), fixed in the data, never a null.**

🔴 **This is [W-191 → W-204](W-204-golden-outputs-scoring-and-version-benchmark.md)'s lesson applied one
step earlier.** There, a link feature was built and measured on a corpus with 0
`ref` edges, and `0 of 124 flips` was filed as a number before anybody counted
the input. Here the counting came first, at the cost of a few seconds.

### ✅ The premise is TRUE, and worse than the proposal stated

**0 of 33 distinct identifiers survive the analyzer whole.** Not *some* — zero.
**3 are MANGLED rather than split**, producing a string no document contains:

| identifier | tokens | |
|---|---|---|
| `DAIRY-2` | `['dairi', '2']` | `dairi` is nowhere in the corpus |
| `KFS-2014` | `['kf', '2014']` | the `S` is gone |
| `QCL-OPS-DOCK-03` | `['qcl', 'op', 'dock', '03']` | `OPS` became `op` |

🔴 **And the SEPARATOR decides the outcome** — `ERR_2031` survives whole,
`RF-118` does not. Coverage today is an accident of punctuation, and the
underscore case **already half-works**, which is the more dangerous state: a
build measured only on those would show a small gain from a field that changes
nothing for them.

### What step 2 needs before it may start

1. 🔴 **Id-queries — [prompt 8](../golden/prompts/8-codex-identifier-questions.md),
   Codex's.** ⚠ **Unlike W-191, the documents are fine** (51 tokens across all
   20); only the questions are missing, which is a smaller ask.
2. ⚠ **A design decision, named and NOT taken:** an unstemmed field needs
   **committed postings**, so unlike step 1's anchor field it cannot fold at read
   time and cannot avoid a `_format` change
   ([SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 9.1).
   **Whether it rides 3.0's existing unreleased bump belongs in the build's own
   pre-registration.**

### ✅ Research filed 2026-09-18, GRADUATED 2026-09-20 — [`proposals/identifier-exact-match.md`](../proposals/identifier-exact-match.md)

🔴 **It is now two items, and neither is step 2.** [W-203 → W-205](W-205-identifiers-reachable-and-whole.md)
carries the two analyzer defects and the four families, **waiting on this item** — not on a
design question, on a seed corpus of the failing shape. [W-202](W-202-identifier-analyzer-gate.md)
is 🟢 and waits on nothing: freeze what the analyzer does to the 33 ids as a test, so any
later change shows as a diff. ⚠ **Step 2 as written picks family (c), the separate field —
and (a) preserve-original is a PRECONDITION of it, not an alternative.**

**Arpit asked 2026-09-18 how this is solved elsewhere, and for a before/after
test either side of the build.** Filed, not decided. Three things in it change
what step 2 is:

1. **The cause is two lines in [`query/analyzer.py`](../../src/fux/query/analyzer.py),
   and neither is a missing field.** **D1** — `_WORD_RE`'s class holds `_` and
   not `-`, `.` or `/`, so the module's own *"whole AND parts are both emitted"*
   is kept for `snake_case` and silently broken for every other separator; that
   **is** the underscore/hyphen asymmetry. **D2** — `should_stem` protects
   digits and underscores but not all-letter acronyms, so Porter takes `kfs` to
   `kf` and `dairy` to `dairi`. Reproduced against the shipped code.
2. ⚠ **A correction to the survival run.** Its §1 says a mangled id *"cannot be
   reached at all"*. **Ingest and query import the same `analyze()`**, so
   `DAIRY-2` typed as a query produces the same `['dairi', '2']` the document
   wrote and **does** match. What is lost is **precision** — one rare term
   becomes two common ones, sibling ids collide on `rf`, and the band reports
   `missing: dairi`. Step 2 is a ranking fix, not a recall fix, which is what
   keeps [SR-RS](../../records/0133_predictions.md) d19's paired floor the right bar.
3. 🟢 **Gate A — a before/after that does NOT wait on Codex.** Re-run
   `tools/quality-controls/identifier_survival.py` against the 33 frozen rows:
   before is measured (0 of 33), after must be 33 of 33 with 0 mangled. It
   falsifies a broken fix in seconds. ⚠ **It is a mechanism probe, never a
   ranking verdict** — only prompt 8's gate B can say the corpus got better.

⚠ **The four families are ordered cheapest-first in the proposal, and (a)
preserve-original is a PRECONDITION of (c) the separate field**, not an
alternative to it: a new field still has to be fed by a tokenizer that cannot
see past a hyphen. **The current framing of step 2 has that ordering backwards.**

---

## ✅ Step 1 BUILT 2026-09-15 — obligations 1–7 and 9 shipped; 8 and 10 are Codex's

**Claude Code, 2026-09-15.** The mechanism is in both readers, behind
`[bm25f] anchor`, **default `0.0`**. ⚠ **No claim about ranking quality is made
or may be made** — the frozen bar is
[`2026-09-15-anchor-text`](../regression/2026-09-15-anchor-text/PRE-REGISTRATION.md)
and it has no `VERDICT.md`.

| # | obligation | state |
|---|---|---|
| 1 | `_LINK_RE` captures the text; `DocScan.links` is `(text, target)` | ✅ |
| 2 | the SOURCE edge carries it; the record schema amended | ✅ **as `at` (hashed terms) + `al`, not the string — see below** |
| 3 | a reverse map in `.fux/runtime/` | ✅ `anchors/<prefix>.json` + `alen` + `total_anchor_len`, `fux.runtime.v6` |
| 4 | **retrieval**: an anchor match makes the `dst` a candidate | ✅ both generators, and `Expansion.matches` had to move with it |
| 5 | the fold lands **once**, in the shared read path | ✅ in `rank()`; **5 536 byte-identical comparisons at `anchor = 2.0`, 0 mismatches** |
| 6 | a `tune.toml` key, default 0 | ✅ `[bm25f] anchor` |
| 7 | the Node reader folds identically | ✅ with its own fixture — the differential arm could not have caught a forgotten transcription |
| 8 | 🔴 **link-bearing DOCUMENTS first, then golden question(s)** | 🔴 **Codex's** — and the reason here was wrong. The ladder carries **0 `ref` edges on all eight rungs** and `work/golden/seed/` has no link syntax at all ([measured](../regression/2026-09-15-anchor-mechanism/report.md)), so **no question can exercise this field** — SR-RS d23a wants the *input*, not the query. Key access was never the blocker |
| 9 | frozen pre-registration | ✅ [filed](../regression/2026-09-15-anchor-text/PRE-REGISTRATION.md) |
| 10 | measure → verdict → default on only on PASS | 🔴 **blocked on 8.** ⚠ The arms have still never run; a [mechanism probe](../regression/2026-09-15-anchor-mechanism/report.md) measured **0 of 124 flips at every weight on four rungs**, which is a **data defect (23b), not a null**, and rules nothing |

### Three decisions the build made that the ruling did not

1. 🔴 **The edge carries hashed TERMS, not the anchor string.** Link text is a
   verbatim fragment of the source's prose, so committing it plainly is content
   in the index ([L2](../../records/0004_LAW-2-content-never-durable.md)) and
   would need L5's hashed-meta branch on top. A hash is a statistic, and it is
   the currency `terms` already uses — so the scan's byte prefilter finds an
   anchor source by the substring check it already runs, free. **The ruling was
   about WHERE the byte lives; this is about what it is.** Flagged rather than
   assumed: if Arpit wants the readable string for `fux explain`, it is a
   second field and a second decision.
2. **`_format` bumped to `fux.index.v3`**, because a property appeared and
   [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 9.1 says
   that bumps. Cost: a whole-corpus diff and `fux ingest --full` for every
   consumer. ⚠ **The vendored Node bundle had to be rebuilt in the same change
   or it refuses the new index outright** — and that rebuild carried W-161's and
   W-176's bundle output too, which had not been regenerated.
3. **`alen` joins `wlen`.** Anchor tf is **unbounded in the number of linkers**
   where body tf is bounded by one document's length, so a linked-to document is
   priced as a longer document. It is the only guard against the hub failure the
   pre-registration names, which is why that is clause 3 of the decision rule.

### What it cost, and what it did not

- **Off costs nothing.** `0.0` is not weight zero — every anchor branch tests it
  and is skipped, so an unconfigured corpus does the float arithmetic it did
  before the field existed. Asserted, and measured: 5 536 byte-identical
  comparisons at the default.
- **On costs the reference scan one byte regex per line**, because a document's
  anchor length belongs in its `wlen` whether or not it matches.
- ⚠ **`tools/differential/run.py` could not run on this repository** —
  `queryset.py` decodes every walked file as UTF-8 and ten are not. Pre-existing,
  unrelated, filed as W-184 (closed 2026-09-15); the evidence
  was gathered through an ad-hoc copy of the same harness and is named as such.

### Records amended

[SR-INGEST](../../records/0106_ingest.md) 17 · [SR-EXTRACTED](../../records/0115_extracted-mode.md) 10 ·
[SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) 14 · [SR-RANKING](../../records/0111_ranking.md) 12 ·
[SR-T1-ACCELERATOR](../../records/0110_accelerator.md) 15 · [SR-TUNE](../../records/0135_tuning.md) 17 ·
[SR-GRAPH](../../records/0126_graph.md) 18 · [SR-ASK](../../records/0103_ask.md) 13 ·
[SR-EXPAND](../../records/0149_expand.md) 15 · [SR-CONFIDENCE](../../records/0141_confidence.md) 16 ·
[SR-PII](../../records/0148_pii.md) 21 · [SR-ARCHIVED-CONTENT](../../records/0134_archived-content.md) 9 ·
[SR-NODE-SEARCH](../../records/0153_node-search.md) 19.

⚠ **SR-CONFIDENCE 16 is a finding, not a fix:** a document ranked #1 purely on
what its linkers call it reports **coverage 0** and names the query's word in
`confidence.missing`. That is the honest answer to *what does the top document
itself say?* — and whether it pushes a class of answers into `partial` is
**unmeasured and not in the decision rule**.

---

## ✅ Step 1 RULED 2026-09-15 by Arpit — option (c), the edge carries the text

> **Arpit, 2026-09-15:** *"ratify go with option C"*, on three options put to him
> in chat after the finding below. **Ratified, not built.**

### What was found first, 2026-09-15, before step 1 was built

**1 · Link TEXT is not extracted today, and edges do not carry it.**
[`ingest/edges.py`](../../src/fux/ingest/edges.py)'s `_LINK_RE` is
`\[[^\]]*\]\(([^)\s]+)…\)` — the anchor text sits in a **non-capturing**
class and is discarded; only the target is kept. `DocScan.links` is a list of
targets. So the proposal's *"cost: small — edges are already extracted"* is
half true: the **edges** are, the **words** are not, and `DocScan.links` has to
change shape. This is implementation, and it is unchanged by the ruling.

**2 · The field as SPECIFIED would have made a document's committed bytes a
function of OTHER documents.** If `A`'s `anchor` field is built from the link
text of every document pointing at `A`, then editing `B` changes `A`'s
committed bytes while [`maintain/runner.py`](../../src/fux/maintain/runner.py)
marks only `B` dirty — a full `fux ingest` and an incremental re-index would
produce **different indexes from the same sources**.

⚠ **That is [L3](../../records/0005_LAW-3-deterministic.md) failing on the
incremental path only, which is the worst shape for it**: the full-ingest path
stays byte-reproducible, so every test and every CI check that rebuilds from
scratch passes, and the drift appears only in a working repository that has
been edited over time. **Nothing in this repo would catch it.**

⚠ **Two corrections to that finding, both in fux's favour, both load-bearing
for the ruling:**

- **It is not reachable today.** `runner.py`'s `record_head` says in terms that
  *"`fux ingest` re-indexes the whole corpus regardless of what the list
  says"*, and **`B-002`** records that the dirty list's input is unused. There
  is no incremental path yet to disagree with the full one. The hazard is
  **B-002's inheritance**, not step 1's alone — but building step 1 first
  plants it where nothing would find it.
- **"Cross-document" is not what makes it wrong.** `df` and `avg_wlen` are
  corpus-wide too and cost nothing, because they are **counted at read time**:
  [`store/format.py`](../../src/fux/store/format.py) has `query/scan.py` find a
  term's `df` by scanning raw record bytes, and
  [`derive/accel.py`](../../src/fux/derive/accel.py) folds `idf(df, n)` and
  `avg_wlen` in the derived plane, which
  [`derive/__init__.py`](../../src/fux/derive/__init__.py) calls *"rebuildable
  from the committed shards and never committed"*.

**So the invariant this ruling protects is narrower and sharper than "no
cross-document dependencies":**

> **A committed per-document byte is a function of that document alone.
> Everything corpus-wide is a read-time fold.**

The anchor field as specified would have been the **first** thing ever to break
it. That is the whole reason the specified form was refused.

### The three options put to Arpit, and what he took

| | what it does | the invariant | cost |
|---|---|---|---|
| (a) | a changed document also dirties the targets of its out-edges | **stays broken, patched** | a change to SR-MAINTENANCE's re-index contract + a new equality test; every future cross-document field re-opens it |
| (b) | do not build step 1 (step 5's inheritance goes with it) | safe | loses the highest-value idea in the ten |
| **(c)** | **the text lives on the EDGE, folded in at read time** | **intact** | candidate generation must also retrieve via in-edges |

**He took (c).** `Edge(src=B, dst=A, text=…)` is a pure function of `B`'s own
bytes, which is exactly what `Edge` already is — the edge list is already
written onto the **source** document's committed record. Editing `B` rewrites
`B`'s edges and moves no other document's bytes. The re-index contract does not
change and L3 never enters the conversation.

**Step 5 is covered by the same mechanism** rather than inheriting the problem:
*"the successor inherits the target's anchor text"* becomes a second read-time
fold over the same in-edge map, not a second cross-document committed byte.

⚠ **Option (a) is refused here, not deferred.** The out-edge invalidation is
still probably owed — but as **its own `W-nn` under SR-MAINTENANCE, sequenced
with `B-002`**, with *edit a linker → incremental re-index → assert equal to a
full ingest* as its definition of done. That assertion is worth having whether
or not anchor text is ever built. **It is not this item's, and nothing in W-168
waits on it now.**

### Definition of done — step 1 under (c)

**Model: Opus** — a plane change and a retrieval change in one step.

| # | what | why it is in the list |
|---|---|---|
| 1 | `_LINK_RE` captures the anchor text; `DocScan.links` carries `(text, target)`; every caller updated | the words are not extracted anywhere today |
| 2 | the edge on the **source** document's committed record carries `text`; `index-record.schema.json` amended | this is the whole ruling — the byte stays with the document that wrote it |
| 3 | a reverse map `dst → [(src, text, grade)]` built in `.fux/runtime/`, by `fux build` and by `runner.py`'s post-pass | derived, gitignored, rebuilt whole — free under L3 |
| 4 | candidate generation: a query term matching anchor text makes the `dst` a candidate | ⚠ **this is a RETRIEVAL change, not a scoring one** — without it the document is never a candidate and no fold can rescue it |
| 5 | the fold lands **once, in the shared read path** — never in the accelerator alone | [`query/rank.py`](../../src/fux/query/rank.py) states the contract: *"the accelerator's build asserts it reproduces the same statistics"*; one-sided and `--fast` drifts from the scan |
| 6 | `anchor` is a BM25F field whose weight is a `tune.toml` key, **default 0** | SR-RS d19: behind a tunable, default off |
| 7 | the Node reader folds anchors identically | the differential law's third arm; L10 |
| 8 | golden question(s): a document findable **only** via a linker's wording | SR-RS decision 23 — the data must contain the input the feature acts on |
| 9 | frozen pre-registration, both directions, the SR-RS d19 paired floor | a threshold may never move |
| 10 | measure → verdict under `work/regression/` → **default on only on PASS** | on FAIL the tunable stays at 0 and the record names the failed direction |

**Anchor terms do NOT enter the committed postings.** Saying so is part of the
done-ness: it is what distinguishes (c) from the specified form, and a build
that quietly adds them has shipped (a) under (c)'s name.

### The tests, and the one that proves this is (c)

- 🔴 **`test_edge_text_is_a_function_of_its_source_alone`** — write `A` and `B`
  where `B` links to `A`; re-index `B` alone; assert **`A`'s committed bytes are
  byte-identical**. **This is the test the ruling exists for.** If it ever goes
  red, the build has drifted back into (a).
- `test_anchor_text_is_captured` — the link text survives `_LINK_RE` and reaches
  the record.
- differential: the scan and the accelerator return the same ranking for an
  anchor-matched query (obligation 5, made checkable).
- the Node twin for the same query (obligation 7).
- ⚠ **A general `full == incremental` test is NOT owed here** — it belongs to
  the out-edge `W-nn`/`B-002`, and claiming it here would be this item taking
  credit for a gate it does not build.

### Records to amend in the same change

[SR-INGEST](../../records/0106_ingest.md) (the record shape `edges.py` writes) ·
[SR-EXTRACTED](../../records/0115_extracted-mode.md) (its `edges` bullet, and
the same-sources-same-bytes guarantee now covers the text) ·
[SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) (the record schema) ·
[SR-GRAPH](../../records/0126_graph.md) (edge kinds; the derived adjacency
carries text, and the reverse map is its neighbour) ·
[SR-RANKING](../../records/0112_postings.md)'s scorer records — the field and
its weight, **plus the sentence that anchor terms are not in the postings** ·
[SR-TUNE](../../records/0135_tuning.md) (the new key) ·
[SR-RS](../../records/0133_predictions.md) (one prediction id).

## Definition of done — per step, in this order

| step | idea | golden prerequisite (Codex's hands where the sealed key is involved) |
|---|---|---|
| 1 | #1 anchor-text field | documents findable only via a linker's wording |
| 2 | #3 identifier field | id-queries |
| 3 | #5 supersession-aware ranking | a superseded/successor pair |
| 4 | #2 corpus-mined expansion | acronym / house-term questions |
| 5 | #4 RM3 (drift bound pre-registered) | under-specified questions |
| 6 | #6 SDM proximity in refer | phrase-sensitive questions |
| 7 | #7 community MMR (after W-161) | multi-facet questions |
| 8 | #8 git authority prior — **starts with a corpus that has history, or does not start** | none in golden |
| 9 | #9 intent → doc-type prior | intent-labelled questions |
| 10 | #10 section units — its own compare doc first | long-document questions |

For every step: golden question(s) → frozen pre-registration (both directions, SR-RS
d19 floor) → build behind a tunable, default off → measure → verdict under
`work/regression/` → default on **only on PASS**; on FAIL the tunable stays at 0 and the
record names the failed direction. **One step per measurement.** Ambiguous → Arpit with
per-query rows.

## Out of scope

The graph-composed `ask` (W-161) and `fux correct` (W-162) — separate items.

## Records this will touch

Per step, as the proposal's §3 table lists: SR-RANKING · SR-POSTINGS · SR-EXTRACTED ·
SR-EXPAND · SR-GRAPH · SR-ARCHIVED-CONTENT · SR-REFER-PLANE · SR-CHUNKING · SR-ASK ·
SR-INDEX-RECORD · SR-TYPES-LIST · SR-RS (one prediction id per step).
