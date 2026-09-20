---
type: OpenItem
id: W-203
title: "W-203 — the two analyzer defects behind identifier tokenisation, and which family fixes them"
description: "Graduated from proposals/identifier-exact-match.md. D1: _WORD_RE's class holds `_` and not `-`, `.` or `/`, so the analyzer's own whole-AND-parts promise is kept for snake_case and broken for every other separator. D2: should_stem protects digits and underscores but not all-letter acronyms, so Porter takes `kfs` to `kf`. Four shipped families are set out cheapest-first; (a) preserve-original is a PRECONDITION of (c) the separate field, not an alternative. Held: the 2026-09-18 headroom run measured 3-4 of 33, below the floor of 6, so no ranking verdict is reachable on this corpus."
status: open
lane: agent
timestamp: 2026-09-20T00:00:00Z
filed: 2026-09-20
ball: agent
---

# W-203 — what actually breaks an identifier, and the four ways it has been fixed

**Model: Opus** — it edits the one module ingest and query both import, and a
one-step divergence between the two sides is a silent no-match with no error to
see.

**Graduated 2026-09-20 from
[`proposals/identifier-exact-match.md`](../proposals/identifier-exact-match.md)**,
filed 2026-09-18 on Arpit's ask for how this is solved elsewhere. **FILED, NOT
RATIFIED AND NOT BUILT.**

🔴 **Waiting on [W-168](W-168-search-improvements.md)** — not on a design
question, on a corpus. See §*Why this is held*.

## 1 · The cause, at line level

Reproduced against the shipped code, 2026-09-18:

| input | analyzed to | |
|---|---|---|
| `ERR_2031` | `['err_2031', 'err', '2031']` | whole **and** parts |
| `RF-118` | `['rf', '118']` | **D1** — no whole form exists |
| `SKU.4471` | `['sku', '4471']` | **D1** |
| `KFS-2014` | `['kf', '2014']` | **D1**, then **D2** |
| `DAIRY-2` | `['dairi', '2']` | **D1**, then **D2** |
| `QCL-OPS-DOCK-03` | `['qcl', 'op', 'dock', '03']` | **D1**, then **D2** |

**D1 — the character class, not the splitter.** `_WORD_RE = [A-Za-z0-9_]+` runs
over the original text. `_` is inside the class and `-`, `.`, `/` are not, so
`ERR_2031` arrives as **one** raw token that `split_identifier` emits whole and
in parts, while `RF-118` arrives as **two** and no whole form is ever produced.
[`query/analyzer.py`](../../src/fux/query/analyzer.py)'s own docstring promises
*"whole AND parts are both emitted"* — kept for `snake_case` and `camelCase`,
silently not kept for every other separator. **That is the underscore/hyphen
asymmetry the survival run found, stated as code.**

**D2 — `should_stem` is an under-specified keyword marker.** It refuses tokens
under three characters and tokens that are not `isalpha()`, so `kfs`, `ops` and
`dairy` all reach Porter. Porter cannot know it holds a fragment of an id,
because **case — the only signal that it does — is discarded one step earlier**,
by design.

## 2 · ⚠ What is NOT wrong — and it changes the goal

**A mangled identifier is reachable.** `analyze()` is imported by both ingest and
query, so `DAIRY-2` typed as a query produces the same `['dairi', '2']` the
document wrote. The [headroom run](../regression/2026-09-18-identifier-headroom/report.md)
measured **30/33 top-3 at rung 100, 29/33 at 1 000, 30/33 at 10 000**.

**What is lost is precision, three ways:**

1. **One rare term becomes several common ones.** `KFS-2014` is high-`idf`;
   `kf` and `2014` are not.
2. **Siblings collide.** `RF-118`, `RF-119`, `RF-120` share `rf` and differ only
   in a bare number.
3. **The diagnostics lie.** A band reporting `confidence.missing: dairi` names a
   string in no document and in nobody's vocabulary — the failure
   `analyze_pairs` exists to prevent, still reachable through the fragments.

⚠ **(3) is the one harm that does not depend on ranking headroom**, and it is
the argument for doing D2 even if D1 is descoped. It is named, not ruled.

## 3 · The four families, cheapest first

*Shipped prior art, not sketches. Rows in [BIBLIOGRAPHY](../../records/BIBLIOGRAPHY.md) §1b under **[3]**.*

| | what it does | cost |
|---|---|---|
| **(a)** Lucene `WordDelimiterGraphFilter` — `PRESERVE_ORIGINAL` + `CATENATE_ALL` | re-emit the undelimited original beside the parts | **fux already does this for `camelCase`**; (a) is that rule extended to `-`, `.`, `/`. No new field, no field weight |
| **(b)** Lucene `KeywordRepeatFilter` (+ `RemoveDuplicatesTokenFilter`) | index the stemmed **and** unstemmed form in the same field | one branch in `analyze()`; removes D2's judgement call — emit both, let `idf` decide |
| **(c)** Elasticsearch multi-fields — `body` + `body.exact`, `quote_field_suffix` | a separate un-analyzed field | **this is step 2 as written.** The only family that can *weight* exact above stemmed; the only one needing committed postings and a [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md) 9.1 decision |
| **(d)** trigram / sparse-gram planes — Cox, zoekt, GitHub Blackbird | drop tokens, index n-grams; buys substring, punctuation and regex | a second index plane, far larger. **Out of scope for 3.0**, recorded so it is not re-invented |

🔴 **(a) is a PRECONDITION of (c), not an alternative to it.** A separate field
still has to be fed, and it is fed by a tokenizer that cannot see past a hyphen.
**The current framing of step 2 has that ordering backwards**, and any
pre-registration that picks (c) without (a) measures an empty field.

## 4 · Why this is held, and what lifts it

**Not a design question — a corpus.** The headroom run measured the gap between
today and a perfect identifier retriever at **3–4 of 33 on every rung**, against
[SR-RS](../../records/0133_predictions.md) decision 19's floor of **6 net flips**.
**No arm on this corpus can return a verdict, whatever is built and whatever
questions are written** — which is why prompt 8 was withdrawn as the unblock.

**What lifts it, either one:**

1. **A seed carrying the failing shape** — a shared prefix plus a short number
   (`PROJ-123`, `RF-118`), which is where D1 actually costs precision. That is a
   Codex corpus-prompt note and it sits inside W-168.
2. **A ruling from Arpit to descope** the ranking half and take D2 alone as a
   correctness fix, on the §2(3) argument. ⚠ **Not asked here** — it is named so
   the next session does not mistake silence for a decision.

## Definition of done — when it is lifted

1. Family chosen and written into a **frozen pre-registration** before a line is
   changed, with (a) included whatever else is.
2. **Gate A ([W-202](W-202-identifier-analyzer-gate.md)) exists and is green
   before**, and its diff is part of the evidence after. A change that moves the
   fixture without the item saying which rows move is the failure.
3. **Both readers.** ⚠ The Node bundle transcribes the analyzer; a fix in Python
   alone ships `--fast`/scan drift, and a differential arm is the only thing that
   catches a forgotten transcription — step 1's obligation 7 is the precedent.
4. **The token-count cost is measured**, the way splitting was (546 142 → 563 296,
   ×1.03 on this repo), and reported whether or not it is small.
5. `_format` / analyzer-version handling decided **in the pre-registration**, not
   in the diff.
6. Records amended in the same change: SR-INGEST, SR-RANKING, SR-INDEX-LIFECYCLE
   at minimum — the step 1 list is the template.

## Out of scope

- **Frontmatter.** [W-201](W-201-frontmatter-scalars-not-indexed.md) owns the
  meta/body split; three of the absolute misses are its defect, not this one.
- **Family (d).** Recorded and refused for 3.0.
- **Writing the fixture.** W-202.
