---
type: Analysis
description: "W-256 section 8 - what the split says: a delta ingest at 10 000 documents is 10 s of corpus-wide work that no content-sha reuse removes, and the largest piece (57 percent) is the PII redact pass, not walk or parse. What is post-hoc, what it does not license, and what Arpit is asked."
run: 2026-10-04-ingest-split
item: W-256
classification: informed
filed: 2026-10-04
---

# ANALYSIS - the cost B-002 asked about is not the one it guessed

## What is measured

An unchanged delta at the design point costs **about 10 s**, none of it
extraction. B-002's hypothesis (walk + parse dominate, so a content-sha parse
cache would pay) is **not what the instrument shows**: walk + parse is 24-30 %
of the non-extract time (2.3-3.2 s). The heaviest segment on every delta is the
`redact` phase, 5.85-6.01 s.

## Post-hoc (kept out of the verdict)

- The engine's own comment at the redact loop says it *"walks every parsed
  document on every ingest, reused or not"*: it is a corpus-wide pass because
  redaction counts feed a census. The delta therefore pays it in full.
- ⚠ **W-239 measured `redact` at 0.97 s on the same rung.** This copy's is
  about 6x that. The difference is the configuration under it - W-239's copies
  carried that day's setup and this copy was migrated by `fux doctor --fix`
  from the lab's v5 `fux.toml`, which wrote `.fux/pii.toml` from the shipped
  template - so the rule set run over 10 000 documents is probably not the
  same. **I did not isolate this**; whether it is the rule count, a regex, or a
  genuine regression since 2026-09-29 is a question for a follow-up, not a
  claim here. It matters: if the 6 s is an artefact of the template rule set,
  N falls toward 4 s and the rule would read differently - which is exactly
  why the frozen rule hands a split to a person.
  ⚠ **Answered 2026-10-05 by W-264 DoD 1 (below): neither guess was right —
  it is a regression, introduced on 2026-10-04 by W-255.** The rule sets are
  byte-identical.
- The `before:write` gap (0.68 s delta, 1.84 s full) is edges/provenance work
  between phases; not decomposed here.

## What this does and does not license

- Does **not** close B-002: N is 2x over the bar.
- Does **not** file the parse-cache item: walk + parse were 0.235-0.299 of N.
  Building it would remove at most about 1.4 s of the 10.
- SR-INGEST section 1's *23x* is wrong now and is restated as a measurement
  (that sentence is not a decision of the rule and is corrected on the data);
  the record rewrite says the ratio is 1.45x at 10 000 documents and that the
  rule's outcome is with Arpit.

## For Arpit

Which of: (1) the redact pass is the item - a content-sha-keyed redaction
result cache, or dropping the per-delta census for reused documents; (2) first
find out why `redact` is 6 s on this copy against 0.97 s in W-239 (rule set vs
regression), then re-run the same pre-registration; (3) accept 10 s as the
delta's floor at 10 000 documents and close B-002 anyway - which would be
moving the bar, so it needs your ruling, not a runner's.

Reproduce: scratch copy as in the report's setup, then
`ingest_split.py run <copy> --repeats 3 --out <dir>`.

## Addendum, 2026-10-05 — why `redact` read 6 s here and 0.97 s in W-239 (W-264 DoD 1)

**The 6 s is real engine time, and it is a regression, not the corpus or the
rule set.** Post-hoc to this run's verdict, which it does not change: the
frozen rule was applied to the engine as it stood at `a935d511`, and that
engine did spend 6 s. Evidence in [`evidence/w264/`](evidence/w264/microbench.txt).

- **The rule set is the same.** W-239's own scratch copy
  (`fux-lab/scratch/w239/rung-10000`, read-only) and this run's generation-3
  copy carry byte-identical `.fux/pii.toml` (10 rules, the shipped template,
  unchanged since 2026-09-13). The guess in the bullet above is wrong.
- **The corpus is the same cost.** Body-only redaction over the two
  generations: 3.09 s (gen 2) against 3.43 s (gen 3), 8.81 M and 8.88 M
  characters, six documents with a hit in each.
- **The cause: W-255 (`f3524f32`, 2026-10-04) put `_lint` inside `_compile`,
  and `Rule.apply` calls `_compile` on every string.** `re.compile` caches;
  `_lint` re-parses the pattern through `re._parser` on every call and does
  not. `run()`'s redact phase redacts each document's body, its frontmatter
  title and its own path, ten rules each: **260 180 `_compile` calls** at
  rung-10000, about 20–30 µs of parsing each. Landed after W-239
  (2026-09-29), before this run's freeze (2026-10-04 23:31).
- **Measured, same parsed documents, same process:** the run.py loop shape
  costs **6.27 s as shipped and 0.97 s with the compiled pattern memoised per
  rule** — W-239's figure to the hundredth.
- **End to end, interleaved A B B A × 2, fresh process each, identical root
  sha `6dfae254…` on all eight:** shipped `redact` 6.38–8.26 s (delta total
  10.40–14.12 s); memoised `redact` 1.03–1.09 s (delta total 5.08–6.94 s,
  median 5.16 s). Shared machine: load average 4.6–5.3 during these runs,
  three other agents running suites and a ladder rebuild; the arms were
  interleaved so drift hit both.

**What it means for W-264:** with the regression fixed, the whole `redact`
phase is about **1.0 s** of a ~5.2 s delta. A redaction cache can save at most
that, less the cost of reading and verifying 10 000 entries — not the ~6 s the
item was sized against. **W-264 stopped at DoD 1 and went to Arpit**
([`W-264`](../../open/W-264-redaction-cache.md)). The memoisation itself is a
one-decorator fix (`functools.cache` on `pii._compile`; a `Rule` is a frozen
value, the lint still runs once per rule at load, and a refused rule still
refuses on every call) with a test that fails if the lint runs per apply.

**What it does not do:** it does not re-adjudicate B-002. The memoised delta's
5.08–6.94 s sits on the 5 s bar this pre-registration froze, and a re-run on a
fixed engine is a new run under a new freeze, ruled by Arpit — not this
addendum's call.
