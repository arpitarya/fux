---
type: Pre-Registration
description: "The bars, metrics and slices for the five-item measurement campaign on the golden ladder: the four ranking priors, the knob sweep, the heading control, table flen, and W-115's headroom."
items: W-143, W-97, W-142, W-144, W-115
run: 2026-09-12-priors-and-tables
classification: informed
engine: fux-engine 2.0.0-alpha.7
engine_sha: 676e973
filed: 2026-09-12
---

# Pre-registration — priors, tables and headroom, on the golden ladder

⚠ **Read §0 first. It says what git can and cannot prove about this file.**

---

## 0. The ordering claim, stated exactly — because one half of it is weaker

**The 2026-09-12 golden-ladder run could prove its ordering**: the ladder was
committed (`92f5bff`) before the questions were opened, and `git log` shows it.
**This run cannot make the same claim, and pretending otherwise would be worse
than the gap.**

| what | when it was fixed | can git prove it? |
|---|---|---|
| **The `0 broken` bar for the four priors** | **Arpit, 2026-09-11**, recorded in [W-143](../../open/W-143-four-no-op-priors.md) | ✅ **yes** — it predates this session entirely |
| **The intent-split requirement** | same ruling, same file | ✅ yes |
| The probe set (`priors-probes.jsonl`) | authored this session, **before the first sweep ran** | 🔴 **no** — committed after the numbers |
| The pairwise criterion, the grids | same | 🔴 **no** |
| W-144's and W-115's headroom questions | this session | 🔴 no |

**Why the gap does not sink the priors result, and where it would.** The probe
wording was written by a session that had read the documents, so favourable
wording is a live risk. **That bias can manufacture a pass. It cannot
manufacture a failure.** The pre-registered question is *"does any single global
value clear `0 broken`?"* and the answer this run reports is **no** — which is
the direction the bias pushes against. A **yes** from this probe set would need
independent probes before anyone believed it, and §6 says so as a standing
condition rather than as a caveat added afterwards.

---

## 1. Classification

**`informed`**, every arm, for two independent reasons:

1. The probe authors read the documents (§0).
2. Three arms run on the golden ladder, whose answer key is the Claude-authored
   stopgap ([W-145](../../open/W-145-codex-regenerates-the-key.md)) — though
   note that **no arm in this run reads the key**. Every endpoint below is
   key-free by construction, which is why these results do not wait on W-145.

**No delta against another run is stated anywhere.** Within-run arm comparisons
are the measurement and are reported as such.

---

## 2. Corpus

The frozen golden ladder, `rung-seed` · `rung-00100` · `rung-01000`, verified
against `work/golden/ladder/*.sha256`. **Frozen rungs are never mutated**: every
arm runs on a scratch copy under `corpora/golden-sweep/`, and only `.fux/tune.toml`
differs between arms. `rung-02000` and above do not exist.

---

## 3. W-143 / W-97 — the four ranking priors

**The question, Arpit's, 2026-09-11, not restated in looser words:** *does **any
single global value** clear a `0 broken` bar?*

- **Probe set:** [`tools/quality-controls/priors-probes.jsonl`](../../../tools/quality-controls/priors-probes.jsonl),
  26 probes, **balanced by intent**: 13 *current-seeking* and 13
  *history-seeking*. A set holding only the first kind clears any bar and proves
  nothing, which is why the balance is a pre-registered property and not a
  convenience.
- **Truth is mechanical.** For a `supersedes:` pair, *current* = the superseder,
  *history* = the retired document. For an archived document, *current* = the
  live one, *history* = the one under `seed/archive/`. Both read off a
  **declaration**; nothing is judged, so nothing can be fitted.
- **Criterion, per probe:** `correct` outranks `competitor`, in `fux ask --top 20`.
  Pairwise rather than `hit@1`, because the pair is what the prior acts on.
  Absent from the window scores wrong; both absent scores wrong and is kept as a
  row rather than dropped.
- **`broken`** = right at the shipped default, wrong at the candidate.
  **`fixed`** = the reverse. The bar is **0 broken**.
- **Grids, fixed here:** `superseded_weight` and `archived_weight`
  `[1.0, 0.9, 0.75, 0.5, 0.25, 0.1, 0.0]`; `recency_half_life_days`
  `[0, 730, 365, 180, 90, 30]`; `rerank_weight` `[0, 0.25, 0.5, 1.0, 2.0]`.
  `0.0` is the sharp column — a knob that moves nothing there reaches nothing.
- 🔴 **A candidate must clear the bar on EVERY rung it is run on.** A value that
  clears on one rung and breaks on another has not cleared; it has found a
  corpus. This is fixed here because it is exactly the loophole a post-hoc
  reading would take.
- 🔴 **The resolution floor still applies** (ADR-RS decision 19): a net below 6
  is *no detected change* at any discordant count, so a candidate clearing
  `0 broken` with a net of 1 or 2 is **not** a result.

**W-97's frozen `PRE-REGISTRATION-TUNER.md` (T0–T5) is superseded by this
section for `superseded_weight` and `rerank_weight`.** Its corpus was the
playground, which [L9](../../../docs/adr/0011_LAW-9-environments.md) removed as an
instrument, and its T2 leg was measured to be a no-op there. Nothing from it is
re-used except its scope: **the output is a candidate table with no
recommendation**, and any default change stays Arpit's ADR-TUNE amendment.

---

## 4. W-142 — the `heading` negative control

**What C4 got wrong:** it asked a yes/no about an event that never happens and
got 0 in both arms. A boolean pinned at zero cannot be a control.

- **Endpoint:** the number of `ext/sibling/` documents in the top-5, per query,
  over all 124 released questions. A count, not a boolean.
- **Arms:** `bm25f.heading` ∈ `[3.0, 1.0, 0.0]`. `0.0` means *ignore this
  field*, so the control carries its own feature-off arm — what ADR-RS decision
  22c(a) requires before headroom may be called **proven**.
- **Headroom is proven** iff the paired discordant count over queries has a
  **net ≥ 6** between the on and off arms. Below that the floor applies and the
  mechanism is **not established** — reported as such, never as a null.
- 🔴 **`rung-seed` is not a valid rung for this control** and the tool refuses
  it: it holds no `ext/` document, so the count is 0 for a reason that has
  nothing to do with headings. That is the 2026-08-28 saturation exactly.

---

## 5. W-144 — does a table inflate `flen`?

**The claim:** table cells are tokenized into `body`, so BM25F's length
normaliser reads a table-heavy document as denser than it is.

- **Headroom first.** Per document, the share of body tokens that are markdown
  table rows, and `Δwlen` if those tokens left the body length. The population
  reported is the documents **above a 10 % table share**, never a corpus-wide
  mean — an aggregate over an untreated population is the M1 pruning error.
- **Verification gate:** the tool's recomputed `flen[body]` must equal the
  committed one for **every** document, or it is measuring a different pipeline
  and the run is void. (It applies PII redaction before extraction, as ingest
  does; skipping that showed up immediately as a 48-token gap on the `.eml`.)
- **Ranking arm:** every released question ranked twice — `flen` as shipped, and
  `flen` with table tokens out of the body. 🔴 **Corpus statistics are
  recomputed in both arms, never borrowed** — borrowing `avg_wlen` makes the
  scores line up while measuring a system nobody can ship.
- **Direction:** the proposal predicts a table-heavy document **rises**. Reported
  as the share of top-1 changes where the new winner is more table-heavy. This
  establishes the **mechanism**, and explicitly not that the new order is better.
- **Quality endpoint, key-free:** a query built from a `df == 1` term in a
  table-heavy document's **prose**, so the document is the only possible answer.
  `hit@1` in both arms. **If both arms saturate the endpoint is Inconclusive**
  (22d), and dilution with the document's commonest prose terms is the declared
  attempt to create headroom before that is concluded.

---

## 6. W-115 — did the chunking change get a corpus that can see it?

Two attempts have picked a corpus that could not. **This asks first and measures
nothing else.**

- **Arms:** `extract_fields` + `parse_document` at `94231b2` (pre-W-115) and at
  `676e973` (HEAD), over the **same** golden-ladder documents.
- **Endpoint:** per document, does `title`, `phrases`, `flen`, the `terms` hash
  or the term count differ.
- 🔴 **Two confounds are controlled, and both are declared here rather than
  discovered later.** (a) PII redaction — the old tree cannot read today's
  `pii.toml`, so the comparison runs only over the documents where HEAD's
  redaction is a no-op. (b) `max_phrases` — the old tree hard-codes 12 and HEAD
  defaults to 32, which is W-116's change and not W-115's, so a `phrases`
  difference that is a pure prefix of the longer list is **attributed to
  `max_phrases` and not counted**.
- **A near-zero difference does not close W-115.** It closes *"is the golden
  ladder the instrument?"* with a **no**, and names what a corpus would need.

---

## 7. What would make this run invalid

Fixed now, so it cannot be decided afterwards:

1. A rung's documents do not match its frozen manifest.
2. `table_flen.py` fails its committed-`flen` verification on any document.
3. A frozen rung is written to, rather than a scratch copy.
4. A grid point is added, removed or re-run after its number exists.
5. Any question or answer from `work/golden/golden-answer/` reaches a Claude
   session's context.
6. A probe's `correct`/`competitor` is changed after a sweep has run.

---

## Reference

- The ruling this run answers: [W-143](../../open/W-143-four-no-op-priors.md),
  Arpit 2026-09-11
- The corpus: [`work/golden/README.md`](../../golden/README.md) ·
  [the ladder run](../2026-09-12-golden-ladder/report.md)
- Headroom, per-query rows, classification, resolution floor, test-data coverage:
  [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 13, 15, 19, 22, 23
- The proposal W-144 graduates:
  [`structure-aware-extraction.md`](../../proposals/structure-aware-extraction.md)
