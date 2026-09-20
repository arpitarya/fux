---
type: Proposal
title: "Exact identifier match — the two analyzer defects behind it, and the four ways the field has been solved elsewhere"
description: "Research for W-168 step 2. Names the line-level cause of the 0-of-33 survival result, corrects the claim that a mangled identifier is unreachable (query and index run the same analyzer, so the loss is PRECISION, not recall), sets out the four solution families used in practice cheapest-first, and proposes an analyzer-level before/after gate that does not wait on Codex."
status: graduated
timestamp: 2026-09-18T00:00:00Z
---

# Exact identifier match — what actually breaks, and what everyone else does about it

✅ **GRADUATED 2026-09-20 into [`W-203` → `W-205`](../open/W-205-identifiers-reachable-and-whole.md)
(the two defects and the four families) and [`W-202`](../open/W-202-identifier-analyzer-gate.md)
(gate A, the frozen fixture).** This file stays because it is the reasoning the
two items cite rather than repeat — the option set, the prior art and the
correction. **The items are the state; this is the argument.**

⚠ **One thing in it was overtaken the same week.** §5's gate B said prompt 8
would unblock the ranking verdict. The
[headroom run](../regression/2026-09-18-identifier-headroom/report.md) of
2026-09-18 measured the gap at **3–4 of 33 on every rung**, below the floor of 6,
so **no questions can unblock it** — what is missing is a seed corpus carrying the
failing shape. W-203 carries the corrected version; §5 below is left as written
rather than silently repaired.

**Scope.** Research only. Nothing here is built, and
[SR-RS](../../records/0133_predictions.md) decision 19's paired floor still
governs any ranking claim.

---

## 1 · The cause is two lines, and neither of them is "there is no unstemmed field"

[The survival run](../regression/2026-09-16-identifier-survival/report.md) measured
the outcome — **0 of 33 survive whole, 3 mangled** — and named the symptom (*the
separator decides*). It did not name the cause. Reproduced 2026-09-18 against
[`query/analyzer.py`](../../src/fux/query/analyzer.py) and
[`query/stem.py`](../../src/fux/query/stem.py):

| input | analyzed to | why |
|---|---|---|
| `ERR_2031` | `['err_2031', 'err', '2031']` | **D1 does not apply** — `_` is inside the token class |
| `RF-118` | `['rf', '118']` | **D1** — the hyphen ends the token, so no whole form exists |
| `SKU.4471` | `['sku', '4471']` | **D1** — same, for `.` and `/` |
| `KFS-2014` | `['kf', '2014']` | **D1 then D2** — `kfs` is all letters, so Porter strips the `s` |
| `DAIRY-2` | `['dairi', '2']` | **D1 then D2** — Porter's step 1c turns `y` into `i` |
| `QCL-OPS-DOCK-03` | `['qcl', 'op', 'dock', '03']` | **D1 then D2** — `ops` → `op` |

**D1 — the tokenizer's character class, not the splitter.**
`_WORD_RE = [A-Za-z0-9_]+` runs over the original text. `_` is in the class and
`-`, `.`, `/` are not, so `ERR_2031` arrives as **one** raw token that
`split_identifier` then emits **whole and in parts**, while `RF-118` arrives as
**two** raw tokens and no whole form is ever produced. The module docstring's own
promise — *"whole AND parts are both emitted"* — is kept for `snake_case` and
`camelCase` and silently not kept across every other separator. **That is the
underscore/hyphen asymmetry, exactly.**

**D2 — `should_stem` protects digits and underscores, but not acronyms.**
It refuses tokens under three characters and tokens that are not `isalpha()`.
`kfs`, `ops` and `dairy` are three or more characters and all letters, so Porter
runs on them. Porter cannot know it was handed a fragment of an id, because
**case — the one signal that it was — is discarded one step earlier**, by design
(splitting happens before lowercasing; the lowered token is what reaches `stem`).

> **Both defects are inside one file.** Neither is an argument for or against a
> new field.

## 2 · ⚠ Correction — a mangled identifier is NOT unreachable

The run's §1 says *"a query spelled the way a person spells it cannot reach that
piece at all"*. **That overstates it, and the overstatement changes what step 2
is for.**

`analyze()` is imported by **both** ingest and query — the module docstring says
so in terms, and `rerank.py`, `provenance.py` and `refer/_rescore.py` all route
through it. So `DAIRY-2` typed as a query analyzes to `['dairi', '2']`, which is
exactly what the document wrote. **It matches.** The recall claim is symmetric and
holds.

**What is actually lost is precision, and it is lost three ways:**

1. **One rare term becomes several common ones.** `KFS-2014` is a high-`idf`
   term; `kf` and `2014` are not. Every document mentioning the year 2014 now
   competes with the one document the id names.
2. **Sibling ids collide.** `RF-118`, `RF-119` and `RF-120` share the term `rf`
   and differ only in a bare number, so ranking cannot tell them apart on the
   identifier alone.
3. **The diagnostics lie.** A band reporting `confidence.missing: dairi` — a
   string in no document and in nobody's vocabulary — is the failure
   [`analyze_pairs`](../../src/fux/query/analyzer.py) exists to avoid, and it is
   still reachable through the fragments.

**So the honest statement of the problem is:** *an identifier is currently priced
as two or three ordinary words instead of one rare one.* That is a ranking defect,
which is what makes it a W-168 step and what makes
[SR-RS](../../records/0133_predictions.md) d19's paired floor the right bar.

## 3 · The four families, cheapest first

*Each is prior art that shipped, not a sketch. Sources in §6.*

### (a) Keep the original alongside the parts — Lucene `WordDelimiterGraphFilter`

`PRESERVE_ORIGINAL` re-emits the undelimited input and `CATENATE_ALL` emits the
joined form (`wi-fi-4000` → `wifi4000`), so one token yields parts **and** a whole.
**fux already does this for `camelCase` and `snake_case`; (a) is that same rule
extended to `-`, `.` and `/`.** No new field, no new field weight, no plane change.

### (b) Index the stemmed and unstemmed form in the same field — Lucene `KeywordRepeatFilter`

Emits every token twice, once marked keyword, and a stemmer that honours the
keyword attribute skips the marked copy; duplicates are dropped afterwards. The
stdlib equivalent here is one branch in `analyze()`. **`should_stem` is already
fux's `KeywordMarkerFilter`** — under-specified, not absent — so (b) is either
"protect acronyms" (a judgement call: `OPS` the id vs `ops` the word, with case
already gone) or "emit both and let `idf` decide" (no judgement needed).

### (c) A separate un-analyzed field — Elasticsearch multi-fields

`body` analyzed, `body.exact` not, with `quote_field_suffix` routing a quoted
query to the exact subfield. **This is W-168 step 2 as written.** It is the only
option that can *weight* an exact hit above a stemmed one — which BM25F already
gives fux the knob for — and the only one that needs committed postings and
therefore a `_format` decision
([SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) decision 9.1).

### (d) Abandon tokens — n-gram / trigram indexes

Russ Cox's trigram index, Sourcegraph's zoekt, and GitHub's Blackbird, which
states outright that code search *"doesn't want stemming"* and *"doesn't want stop
words stripped"*. Blackbird replaces fixed trigrams with **sparse grams** because
`for` produced too many false positives at scale. This is what buys substring,
punctuation and regex search. **Cost: a second index plane and a much larger
index.** Named here so it is not re-invented; **out of scope for 3.0.**

## 4 · What this suggests, and what it does not

- **(a) and (b) are the same file and the same afternoon**, and between them they
  cover all 33 identifiers — (a) the 30 split ones, (b) the 3 mangled ones.
- **(c) is not a substitute for (a).** A separate field still has to be *fed*, and
  it is fed by a tokenizer that today cannot see past a hyphen. **(a) is a
  precondition of (c), not an alternative to it.** ⚠ This is the ordering the
  current framing of step 2 gets backwards.
- ⚠ **(a) and (b) enlarge the index and are not free.** The analyzer docstring
  measures splitting on this repo at 546 142 → 563 296 tokens (×1.03). The same
  count must be produced for (a) and (b) before either is defended.
- ⚠ **Whether adding terms to an existing field is a `_format` change is NOT
  settled here.** Decision 9.1 bumps on a new *property*; these are new *terms*
  under the same one, and [`store/format.py`](../../src/fux/store/format.py)
  versions the analyzer separately. **That question belongs in the
  pre-registration**, with (c)'s heavier answer already known.
- **Nothing here claims a ranking gain.** No arm has run.

## 5 · The before/after gate — two of them, at two costs

Arpit, 2026-09-18: *run test cases before it gets implemented and after it gets
implemented.* There are two separable gates and **only one of them waits on
Codex**, which is the unblock this file exists to produce.

| | gate A — survival | gate B — ranking |
|---|---|---|
| what it asks | does the id reach a posting whole? | does the corpus rank better? |
| unit | one row per identifier (33) | paired flips over golden questions |
| bar | 33 of 33 survive, 0 mangled | SR-RS d19's paired floor, ≥6 net flips |
| needs | 🟢 **nothing — the fixture exists today** | 🔴 [prompt 8](../golden/prompts/8-codex-identifier-questions.md), **Codex's** |
| before | ✅ already run, 2026-09-16 — 0 of 33 | ✅ already counted — 4 of 249, below the floor |

**Gate A is runnable now, against the existing instrument**
(`tools/quality-controls/identifier_survival.py`) and the 33 frozen rows in that
run's `evidence/`. Re-running it after a change is the literal before/after asked
for, and it **falsifies a broken fix in seconds** without spending a benchmark.

⚠ **Gate A is not a ranking verdict and must never be reported as one.** It proves
the term exists; only gate B can say the corpus is better. The two are filed
separately for the same reason [W-191 → W-204](../open/W-204-golden-outputs-scoring-and-version-benchmark.md)
is a lesson: a mechanism probe is not an arm.

## 6 · References

*All read 2026-09-18. Engineering prior art, not papers — graded as such.*

- Elastic, *Mixing exact search with stemming* — the multi-field `.exact` pattern
  and `quote_field_suffix`. Grounds **(c)**.
- Apache Lucene, `KeywordRepeatFilter` (+ `RemoveDuplicatesTokenFilter`) — index
  the stemmed and unstemmed form of a term into the same field. Grounds **(b)**.
- Apache Lucene, `WordDelimiterGraphFilter` — `PRESERVE_ORIGINAL`,
  `CATENATE_WORDS`, `CATENATE_ALL`, `SPLIT_ON_NUMERICS`. Grounds **(a)**.
- Russ Cox, *Regular Expression Matching with a Trigram Index* (2012). Grounds **(d)**.
- GitHub Engineering, *The technology behind GitHub's new code search* (Blackbird,
  sparse grams). Grounds **(d)** and is the clearest published statement that code
  search wants no stemmer.

⚠ **The software-engineering identifier literature (identifier splitting and
expansion, and vocabulary-normalization studies) was NOT read for this file** —
only located. Nothing above depends on it, and it is not cited as if it did.
