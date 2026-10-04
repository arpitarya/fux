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
