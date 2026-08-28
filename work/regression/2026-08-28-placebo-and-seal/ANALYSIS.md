---
type: Analysis
run: 2026-08-28-placebo-and-seal
date: 2026-08-28
---

# What to do about it

## Finding 1 — source bias is ruled out, and that is a *clearing*, not a fix

**Diagnosed, confident.** Matched-length content-free enrichment moved **one**
query (`n_d = 1`, `p = 1.0000`). The KDD-2024 concern — that retrievers reward
the *presence* of fluent LLM prose independently of what it says — **does not
explain enrichment's lift on this corpus.**

This is the one outcome a control can produce that feels like nothing happening
and is actually the point: **an alternative explanation was available, was
tested, and did not survive.** The `real` arm's content is doing the work,
whatever else is also true of it.

### What it does NOT clear, and this is the part that matters

⚠ **The placebo controls SOURCE BIAS. It does not control CONTAMINATION.** The
`real` arm's author had read the queries. Those are two separate confounds and
only the first is now closed. **The `+9` stays `informed` and stays
"not a generalisation estimate"** (decision 12).

**The cross-run observation is the one to keep in view**: 2026-08-24 measured
*blind* enrichment at 33/50 — the same integer the content-free placebo scores
here. If it holds, enrichment written without sight of the queries is worth
about what meaningless text is worth. 🔴 **It cannot be tested**: the two numbers
are from different runs (not paired), and **no run before 2026-08-28 filed
per-query rows**, so the discordant count is unrecoverable. **The way to settle
it is one paired run** — blind enrichment and placebo, same harness, same day,
per-query rows — and that run is proposed, not performed.

## Finding 2 — a queue item asserted an impossibility that cost one command

OPEN-WORK carried *"impossible to check, impossible to re-run (the corpora went
in the 2026-08-20 wipe)"* about the `+9`. The wipe took `acme` and `orbit`; the
`+9` was measured on **`fux-playground`**, which was never wiped. Re-running
reproduced `32 → 41` exactly and filed the missing count: **`n_d = 9`,
`b = 0`, `c = 9`, `p = 0.0039` — it clears the floor.**

**This is queue rule 4 (re-derive, do not read) with a receipt.** It is now the
**fourth** recorded instance of a blocker filed by a session that could not look
being dissolved by a session that could. ⚠ **CLAUDE.md's two-strikes rule is
worth pointing at here**: the class *"a queue item asserts an environmental
impossibility that is false"* has now recurred well past twice. **A mechanical
check is not obviously available** — the assertion is prose — which is exactly
why the rule's own escape hatch (state it out loud) is being used rather than
quietly satisfied.

## Finding 3 — the seal ran and is EXERCISED, not PROVEN

**Diagnosed, confident, and it is a chronology problem, not a design problem.**
`seal.py` postdates the `real` enrichment by four days. Its author saw all 50
queries, so the "sealed" 15 were never hidden from anyone. **A post-hoc split of
a fully-seen set cannot test contamination**, however deterministic the split.

The visible/sealed lift split (+8 vs +1) *looks* like a contamination signature
and **must not be read as one**, for two further reasons beyond chronology:

1. **`n_d = 1` in the sealed half.** Nothing is resolvable there.
2. **The sealed half is harder by construction** — ADR-RS decision 15 records
   5 of 9 `known_failure` goldens landing in the sealed 15 (33 % vs 11 %). A
   smaller lift is the expected observation before contamination is invoked.

### Proposed work

**The seal's first adjudicating use requires an artifact authored after the seal
existed.** Concretely: enrich the corpus with an author who is given the
**visible 35 only**, then score both halves. Until such a run exists,
**`BUILT IS NOT PROVEN` stands for the sealed subset** and the marker should not
be moved.

## Two harness lessons, both nearly silent

1. 🔴 **`ingest` carried the copied index forward** — *"0 changed, 10 carried
   forward"* — and produced **three identical 827-term indexes for three
   different enrichment arms.** A three-arm comparison where every arm is the
   same index reports plausible numbers and measures nothing. Caught only
   because term counts were printed. **Wipe `.fux/index` and `.fux/runtime` per
   arm, and assert the term counts DIFFER**, which the reproduce block now does.
2. **The harness reproduced two previously-filed integers exactly** (32 and 41).
   That check is what separates "a comparison" from "a different experiment",
   and it cost nothing.

## Unresolved

- **Whether blind enrichment beats placebo** — see Finding 1; needs one paired
  run, and is the most valuable measurement this analysis can name.
- **Whether the `real` arm's `+9` generalises at all.** Contamination is
  untested and the placebo does not reach it.

## Reproduce

In the [report](report.md), including the index-wipe step whose absence produced
the silent-null above.
