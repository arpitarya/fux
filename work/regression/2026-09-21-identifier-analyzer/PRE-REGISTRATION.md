---
type: Pre-Registration
description: "W-205 part 2: the analyzer keeps an identifier whole. Family (a) — `-`, `.` and `/` become identifier separators exactly as `_` already was — measured against HEAD on the set-3 ladder, both directions, SR-RS decision 19's paired floor. Family (b) is conditional on (a) leaving headroom, and (c) on (b) leaving it."
run: 2026-09-21-identifier-analyzer
item: W-205
status: frozen
filed: 2026-09-21
---

# PRE-REGISTRATION — W-205 part 2, the analyzer families

🔴 **FROZEN, and committed before any number exists**
([SR-RS](../../../records/0133_predictions.md) decision 10b). **No arm has run.**
The headroom this run has is **not yet known** and is disclosed in §7 from the
before-arm, per decision 22 — it is not a number anyone looked at first.

---

## 1 · The defect, in one line each

| | what happens today (analyzer `v2`) |
|---|---|
| **D1** | `_WORD_RE` is `[A-Za-z0-9_]+`. `_` is in the class; `-`, `.` and `/` are not. So `ERR_2031` arrives as **one** token and the splitter emits **whole and parts**; `RF-118` arrives as **two** tokens and **no whole form ever exists**. The module's own docstring promises whole-and-parts and keeps it for `snake_case` alone. |
| **D2** | `should_stem` protects digits and underscores, not all-letter fragments. `kfs` → Porter → `kf`; `dairy` → `dairi`; `ops` → `op`. |

🔴 **The separator decides the outcome, and that is the whole defect.** Coverage
today is an accident of punctuation: the underscore case already half-works,
which is the more dangerous state, because a change measured only on those would
show a small gain from a mechanism that changes nothing for them.

⚠ **It is a PRECISION defect, not a recall one.** `analyze()` is imported by
ingest **and** query, so `DAIRY-2` typed as a query produces the same
`['dairi','2']` the document wrote and **does** match — the
[2026-09-18 headroom run](../2026-09-18-identifier-headroom/report.md) measured
30/33 top-3 at every rung while an earlier report had claimed a mangled
identifier *"cannot be reached at all"*. What is lost is that `RF-118`, `RF-119`
and `RF-120` share their only distinguishing term.

## 2 · The arms, and why an arm is an ENGINE BUILD rather than a tunable

| arm | what it is |
|---|---|
| **before** | `HEAD` at `7a88a165`, analyzer `v2` |
| **(a)** | analyzer `v3` — `-`, `.` and `/` join `_` in `_WORD_RE` and `_BOUNDARY_RE` |
| **(b)** | `v3` **plus** the unstemmed form emitted beside the stemmed one |
| **(c)** | a separate exact field — **only if (a) and (b) leave headroom** |

🔴 **SR-RS decision 19's *"behind a tunable, default off"* does not apply, and
the reason is structural rather than convenient.** That clause governs a
**ranking knob** — a weight read at query time, where one index serves both arms.
An analyzer change rewrites the committed postings, so the two arms are two
indexes; and `store/format.py`'s header pins `analyzer` **precisely so that two
indexes carrying different terms cannot both claim to be the same one**.
`store/reader.py` refuses a shard written by another analyzer. A `tune.toml`
boolean is not in that header, so a configurable analyzer would make two corpora
indistinguishable at exactly the point the header exists to distinguish them —
*"two analyzers in one index is undetectable at query time and corrupts every
df"*.

**So: `ANALYZER_VERSION` moves `v2` → `v3`, and the arm is which engine built the
index.** This is the same shape as W-204 phase B's arms and needs no new concept.

⚠ **`_format` does NOT bump, and that is a decision.** No property appeared and
no field changed meaning; every record has the shape it had. The header carries
`analyzer` as its own field with its own refusal, and bumping `_format` too would
claim a schema change that did not happen.
[SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) decision 9.1 is
about a property appearing. ⚠ [W-168](../../open/W-168-search-improvements.md)
step 2's note that this *"cannot avoid a `_format` change"* was written about
family **(c)**, which adds a field; it does not reach (a).

## 3 · Both readers, and the differential arm is mandatory

**The Node bundle transcribes this analyzer.** A Python-only change ships
`--fast`/scan drift and a silent no-match with no error to see, so
`node/src/query/analyzer.mjs` and `node/src/store/format.mjs` move in the same
change, and **`tests/query/identifier-fixture.json` is read by both readers'
fixtures from one file** — two copies would let one be updated and the other
forgotten, which is the precise failure the fixture exists to catch.

**Gate, before any ranking arm runs:** the two readers must produce
byte-identical token lists for every row of the fixture and for the contrast set.
A divergence stops the run.

## 4 · The endpoint, the population, and the floor

**Instrument:** [`identifier_probe.py`](../../../tools/quality-controls/identifier_probe.py),
over **43 id-queries** in `evidence/id-queries.jsonl` — the 33 of 2026-09-18 plus
**10 authored from set 3's documents by grep, with no key**.

🔴 **One target was repointed and it is declared here, not in the results.**
`idq-21` (`RF-118`) was targeted at the telematics mail thread in 2026-09-18,
because that was the only document naming it; set 3 gave `RF-118` its own asset
file, which is now unambiguously the primary. **Both arms use the same targets**,
so the repoint cannot create a flip.

**Primary endpoint: `rank_primary_bare` — the rank of the primary document for
the BARE identifier**, `hit@1`, paired per query, per rung.

⚠ **The bare form is the endpoint and the question form is reported beside it,
never averaged with it.** Surrounding words rescue a mangled identifier; the
question form is where this defect hides, and reporting it as the endpoint is how
the 2026-09-16 survival run reached a wrong conclusion.

**Rungs: `rung-00100`, `rung-01000`, `rung-10000`** — the three the 2026-09-18
headroom run used, so the *shape* of the population is comparable even though its
numbers are not (the corpus changed).

🔴 **The floor is [SR-RS](../../../records/0133_predictions.md) decision 19's: a
net of 6 flips, per rung.** Nets of 1–5 cannot clear α at **any** discordant
count. **It tracks the flips, never the 43.**

**Both directions, stated now:**

- **PASS** — a net of **≥ 6** in favour of the arm on at least one rung, **and no
  rung with a net of ≥ 6 against**. `ANALYZER_VERSION` ships at `v3`.
- **FAIL** — a net of ≥ 6 against on any rung. The change is reverted; the record
  names the failing direction.
- **INCONCLUSIVE** — every rung's net is in ±5. **The change does not ship on an
  inconclusive**, and the arm is reported as *not distinguishable at this N*,
  never as *no difference*.

## 5 · 🔴 Two absolute conditions, conjunctions and NOT trades

A mechanism that fixes identifiers by reordering the corpus is a regression with
a good anecdote. Both must hold for a PASS:

1. **No `ref`-edge or coverage count on any rung may move.** The analyzer does not
   touch edge extraction, and a change here would mean it did.
2. **The non-identifier control must not degrade.** A sample of **60 questions
   drawn from set 1 alone** (the externally-authored set), fixed by a rule and
   frozen before the sample is drawn, is run on `rung-01000` in both arms. **A
   net of ≥ 6 against on that sample is a FAIL of the whole run**, whatever the
   identifier endpoint says.

   🔴 **CORRECTED 2026-09-21, before any arm ran and before the sample was
   drawn.** This clause was drafted as *"every fourth id in file order"* and as
   *"60 questions"*, and **set 1 has 125 questions, so every fourth is 32.** The
   two halves of one sentence disagreed. The rule executed is **every OTHER id in
   file order, capped at 60** — `s1-001` … `s1-119`.

   ⚠ **The correction is recorded rather than quietly applied, and it is legal
   only because of where it sits in time:** no arm had run, no number existed, and
   **the reading taken is the stricter of the two** — 60 questions can detect a
   degradation that 32 cannot, so the correction can only make a PASS harder to
   reach, never easier. A threshold may never move
   ([SR-RS](../../../records/0133_predictions.md) decision 10b); this is a
   contradiction resolved in the direction that costs the arm more, stated in the
   frozen document so the resolution is auditable rather than inferred.

⚠ **Why set 1 and not a mixture:** the control exists to catch collateral damage
to ordinary prose queries, and set 1 is the only set this model family did not
write. Its answers are not needed — the control's endpoint is **rank stability**
(does the top-1 document change), which needs no key.

## 6 · Cost, measured rather than asserted

**Reported for every arm, on `rung-10000` and on fux's own repository:**

- total analyzed tokens and distinct postings per document, before and after;
- committed `.fux/index/` bytes;
- ingest wall-clock.

⚠ **Family (a) adds one token and one `flen` slot per hyphenated identifier —
and per hyphenated PROSE compound.** `one-off`, `cold-chain` and `night-shift`
each gain a term. English prose is full of them, so the cost is **not** bounded by
the identifier count, and the v2 measurement (×1.03 for `camelCase` splitting on
a prose corpus) is **not** a guide to it. This is the number most likely to
surprise, which is why it is pre-registered as a reported quantity rather than a
footnote.

🔴 **No cost threshold is set, deliberately.** A bar invented here would be a
threshold nobody ratified; the number goes to the verdict and, if it is large, to
Arpit.

## 7 · Headroom — disclosed from the before-arm, per decision 22

**Not known at freezing time, and that is the point.** The before-arm's
`hit@1` on `rank_primary_bare` is the headroom for the improving direction, per
rung; the 43 minus that is the headroom for the degrading one. Both are reported
in the verdict **before** any net is quoted.

⚠ **If the before-arm's headroom is below 6 on every rung, the run cannot return
a verdict and says so.** That is what happened to
[W-168 step 2 on 2026-09-18](../2026-09-18-identifier-headroom/report.md) —
3–4 of 33, below the floor, *"whatever questions are written"* — and it is the
reason set 3 exists. It may happen again: **set 3 added 10 id-queries and four
sibling families, which is not obviously 6 flips of headroom.** Filed as
`unmeasurable` in that case, never as a null
([SR-RS](../../../records/0133_predictions.md) decision 23b).

## 8 · What this run may never do

- Ship (b) or (c) without its own pass. **(a) is a precondition of (c)** — a
  separate field is still fed by the tokenizer.
- Change a stopword. `QCL-IT-ADR-08` loses `IT` to the stopword list and
  `TSL-RF-118-A` loses `A`; that is a **third** defect class
  ([W-202](../../../archive/open/W-202-identifier-analyzer-gate.md)) and it is
  out of scope here.
- Claim that `QCL-IT-ADR-08` is now findable. **It is frontmatter-only**, so it is
  absent from the index entirely until **W-205 part 1** ships, and no analyzer
  change reaches a document that was never read. `idq-43` (`QCL-QA-MAP-01`) is in
  the query set **to make that class visible**, not to be fixed.
- Pool the rungs, pool the families, or average the bare and question forms.

## 9 · Classification

**`informed`.** The id-queries were authored by the measurer's family, from the
seed, on Arpit's 2026-09-18 instruction after Codex declined; the corpus is one
this session rebuilt. **No arm of this run is `blind` and none may be labelled
so.** ⚠ **No golden answer is used, needed, or reachable** — an id-query set
carries no answer and never enters `work/golden/`, which is the property that
lets this be measured at all while L11 stands.
