---
type: Report
name: enrich-pii-leak-2026-09-02
title: "W-102 — an address in enrichment prose became a committed index term, reproduced and closed"
description: "Two arms of the real CLI on one scratch repo. Before W-102, `fux find` returns the document for an email address that appears only in its enrichment body — a document whose own body was redacted. After, it does not, and enrichment vocabulary still ranks. One flipping query and three controls that hold."
classification: informed
timestamp: 2026-09-02T00:00:00Z
---

# W-102 — the enrichment plane was outside the redaction boundary

**The claim being checked.** W-102 says redaction runs over `parsed[doc_id].body`
and that `_enrichment_for()` reads the enrichment file **after** that phase,
handing its text straight to `extract_fields` as `ctx` — so **a PII value in
enrichment prose becomes a committed index term** on a document whose own body
was redacted.

**Why it needed a run.** The unit tests added for this change assert the code
does the right thing; they cannot show that the *old* code did the wrong thing
through the real CLI, and "a leak that was never demonstrated" is a repair
nobody can check. Both arms below are `python -m fux`, end to end.

## Method

- **A scratch repo, 3 documents**, `docs/` declared `enrich=true`, `notes/` not.
- **`.fux/pii.toml` with one `email` rule.**
- **Two enrichment files.** `docs/a.md`'s carries `ops-oncall@corp.example` in
  its **body**; `docs/b.md`'s carries `reviewer@audit.invalid` in its
  **frontmatter** only — a deliberately different domain, so the two cannot
  match each other's queries.
- **Two arms, one repo, one index wiped between them**: `pre-w102` is the
  package at `0840b52` via `PYTHONPATH` (stdlib-only, so no second venv is
  needed — L1 paying off); `head` is the working tree.
- **Four queries**: one designed to flip, three designed to hold.

`evidence/repro.sh` is the whole thing; `evidence/*.md` and `evidence/pii.toml`
are the fixture verbatim.

## Result

Per-query rows: `evidence/per-query-rows.jsonl`, 8 rows.

| # | query | what it tests | expected | pre-W-102 | HEAD |
|---|---|---|---|---|---|
| q1 | `ops-oncall corp.example` | the address, in the enrichment **body** | no match | 🔴 **`docs/a.md`** | ✅ *No confident matches.* |
| q2 | `escalate restart window` | vocabulary that exists **only** in the enrichment body | match | ✅ `docs/a.md` | ✅ `docs/a.md` |
| q3 | `reviewer audit.invalid` | the address, in the enrichment **frontmatter** | no match | ✅ *No confident matches.* | ✅ *No confident matches.* |
| q4 | `alpha service restarts nightly` | the document's own body | match | ✅ both docs | ✅ both docs |

**Term counts corroborate it independently of ranking**: the same corpus
produces **31 terms** pre-fix and **29** after. The two that disappear are the
address's tokens.

Three things this settles:

- **The leak was real, and `fux find` was the whole surface.** q1 is the defect
  as W-102 described it — the document comes back, nothing says why, and the
  document's own body had been redacted one phase earlier.
- **The feature is not broken by the fix.** q2 is the positive control: a phrase
  that appears nowhere but the enrichment body still ranks its document. A pass
  that also killed enrichment would look identical on q1 alone.
- **The frontmatter line held before and holds now.** q3 never leaked, because
  the block is stripped before indexing ([ADR-ENRICH](../../../docs/adr/0040_enrich.md)
  decision 8) — which is why the new pass deliberately does not run rules over
  it, and why `--check` draws the same line.

`fux enrich --check` on the same fixture refuses `a.md`'s file by name, reports
`1/2  1 carrying PII`, exits **1**, and **rewrites nothing** — and does not
refuse `b.md`, whose address is frontmatter.

## What this does NOT show

- **Four queries are not a sample.** This is a deterministic reproduction, not a
  graded comparison: the same script gives the same rows every time, `b`/`c`
  and a p-value would be meaningless here, and **no statistical claim is made**.
  The resolution floor governs paired *effect* estimates; there is no effect
  being estimated.
- **One rule, one PII class.** Nothing here says anything about the shipped
  starter ruleset's coverage.
- **Nothing about re-ingest cost at scale.** Three documents. The upgrade
  consequence — one full pass for any repo with both enrichment and a firing
  rule — is an argument from where the digest is keyed, not a measurement.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the fixture, the enrichment files, the four queries | Claude Opus 5, this session | the defect description in W-102 and ADR-PII — **written to expose a known defect** |
| the `head` arm's code | the 2026-09-01 session | the same |
| the `pre-w102` arm's code | frozen at `0840b52` | n/a |
| this report and ANALYSIS.md | Claude Opus 5, this session | both arms' output |

**`informed`.** The queries were written by someone holding the defect
description, which is the definition. It matters less than usual here because
nothing is being estimated — q1 either returns the document or it does not — but
the label is applied by the rule, not by how much it seems to matter.
