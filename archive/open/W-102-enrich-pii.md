---
type: OpenItem
id: W-102
title: "W-102 — enrichment prose is committed unredacted, and it also reaches the index unredacted"
description: "ADR-PII decision 1 says redaction covers `.fux/index/` and every committed byte in it. Two things break that today: the enrichment file itself is committed with whatever the model wrote, and — the sharper half, which no record names — `_enrichment_for()` hands the enrichment body straight to `extract_fields` AFTER the redact phase has run, so an email address in enrichment prose becomes a committed term. Close the index leak in `run.py`; make `fux enrich --check` refuse a file that matches a rule, naming it, and never rewrite it."
status: open
lane: agent
timestamp: 2026-09-01T00:00:00Z
---

# W-102 — the enrichment plane is outside the redaction boundary

**Model: Sonnet** for the wiring and the tests — the shape is decided below and
each step has a mechanical check. **Opus** only if the `--check` verdict turns
out to interact with `_enrichment_for`'s validate-then-ignore path in a way
this file did not predict.

## The record this implements

[ADR-PII](../../docs/adr/0053_pii.md) decision 1 — *"Redaction applies to
`.fux/index/` and to nothing else"* — and the Consequences block that already
files half of this as owed. [ADR-ENRICH](../../docs/adr/0040_enrich.md)
decision 8 (frontmatter is stripped before indexing) is the sentence the fix
sits beside. Nothing here restates either.

## Goal

Make ADR-PII decision 1 true. Right now it is a claim the code does not
satisfy, and one of the two ways it fails is not written down anywhere.

## The two holes, and which one is worse

**1. The committed file.** A model handed a document writes prose into
`.fux/enrich/<sha>.md`, and that file is committed. Nothing reads it for PII.
This is the hole [ADR-PII](../../docs/adr/0053_pii.md) names under
*Consequences* — *"the one known hole in the rule this record states"*.

**2. 🔴 The committed index — and this one is NOT in any record.** Redaction
runs in [`run.py`](../../src/fux/ingest/run.py) over `parsed[doc_id].body`
(the block whose comment says *"everything downstream of this line … is built
from redacted text"*). Enrichment does not go through it:
`_enrichment_for(root, sha)` reads the file, strips the frontmatter, and its
return value is passed **directly** as `extract_fields`' third argument — the
`ctx` field. So an email address written in enrichment prose becomes a term in
`.fux/index/`, on a document whose own body was redacted, and the block comment
one screen above says it cannot happen.

⚠ **Hole 2 is the priority.** Hole 1 leaks a value into a file a reviewer reads
in a diff. Hole 2 leaks it into the artifact ADR-PII exists to protect, and it
is invisible: `fux find <the value>` returns the document and no surface
anywhere says why.

## Definition of done

- [ ] `run.py` redacts the enrichment body **before** it reaches
      `extract_fields`, under the same `pii_rules` the document body used, with
      its hits folded into the same `pii_hits` total. The redaction happens at
      the call site or inside `_enrichment_for`; either is fine, but the reason
      goes in a comment beside it, because the next reader's default assumption
      is the one that produced this defect.
- [ ] ⚠ **The sha is untouched.** Enrichment is keyed by the *source
      document's* content sha and the enrichment file's own name is that sha.
      Nothing in this change may recompute, re-derive or redact anything that
      feeds a sha — ADR-PII decision 3's ordering hazard applies here verbatim,
      and the failure would present as every enriched document reporting
      `stale` against its own unchanged source.
- [ ] `fux enrich --check` loads `pii.load(root)` once, runs `redact()` over
      each enrichment **body** (not the frontmatter — a `model:` value is not
      corpus text), and **refuses** any file with a hit: the file is listed
      under the existing `refused:` line with the rule names that fired, and
      `--check` exits 1.
- [ ] 🔴 **`--check` reports; it never repairs.** No file is rewritten. That is
      ADR-MAINTENANCE veto 7's discipline applied to a second surface, and here
      it is stronger than there: the enrichment file is prose a human reviews
      in a diff, and a silent rewrite makes that diff lie.
- [ ] The refusal message says what to do — rewrite the prose without the
      value, do not add a `pii.toml` rule to hide it. A redacted enrichment
      body would index `[PII:email]` as vocabulary, which is worse than useless.
- [ ] `--check`'s summary line carries the redaction count for the run, so
      *"0 redacted"* is a statement rather than an absence.
- [ ] Tests: an enrichment body containing a value the shipped starter matches
      (a) does not put that term in the index, and (b) is refused by `--check`
      with the rule named. Plus the negative: a repo with **no** `pii.toml`
      behaves byte-for-byte as it does today.
- [ ] [ADR-PII](../../docs/adr/0053_pii.md) — the *Consequences* bullet is
      **deleted**, not ticked, and decision 1 gains the sentence that says the
      enrichment body is inside the boundary. Hole 2 is written into the record
      as the thing that was actually wrong, not folded into hole 1.
- [ ] [ADR-ENRICH](../../docs/adr/0040_enrich.md) — a decision saying the body
      is redacted before it becomes `ctx` and that `--check` refuses rather
      than rewrites.

## Hazards

- 🔴 **Redacting the enrichment body changes committed index bytes** for any
  repo that has both enrichment and a firing rule. That is correct and it is a
  re-ingest, exactly like ADR-PII decision 11's ruleset move. It is **not**
  covered by `pii-digest` today, because that file tracks the ruleset and this
  change alters what the ruleset *reaches*. Whoever lands this says so in the
  commit message; a consumer sees one full pass.
- **Do not put the enrichment file's text through `content_sha`.** See the
  second checkbox. The temptation is a "did the enrichment change" check, which
  is W-104's problem and is answered by the filename already.
- **The frontmatter is out of scope on purpose.** `model:` and `generated:`
  are provenance, already stripped before indexing (ADR-ENRICH decision 8), and
  running a PII pass over them would refuse a file for a value that never
  reaches the index.

## Out of scope

`fux doctor`'s redaction counts — that is W-101 item 4 and it is one pass at
`doctor.py`, not this file. The `pii-digest` question above is stated, not
solved: if it turns out a consumer needs the enrichment reach in the digest,
that is a new row against ADR-PII decision 11, not a widening of this one.
