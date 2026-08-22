---
type: Proposal
title: Put the process on a diet
description: PRIORITY.md P7 — four candidate cuts to session-discipline overhead, each put to Arpit for a verdict rather than assumed.
status: graduated
timestamp: 2026-08-21T00:00:00Z
---

# Put the process on a diet — PRIORITY.md P7

> **GRADUATED and ARCHIVED 2026-08-22.** Graduated same-session on 2026-08-21
> (PRIORITY P7) — the `Cost:` line was dropped from the WORKLOG format after
> 58/58 entries had said `unmeasured`, and the standing obligations were
> trimmed. **The change is live in the process itself**, which is why this no
> longer sits among live ideas.
> **Archive is not evidence** — may be named, never cited.

**Why this exists as a proposal, not a compare doc:** P7's own row is
explicit — *"Arpit decides scope; agent proposes the diff, does not apply."*
An agent choosing its own governance cuts is exactly the kind of
self-amendment CLAUDE.md's §Documentation discipline already forbids for
agent-steering files. This doc is the proposed diff; the verdict below is
Arpit's, given directly in the session that filed it (2026-08-21); what he
accepted was applied in the same change.

**Context (from the independent audit that produced PRIORITY.md, 2026-08-20):**
15 of the last 20 sessions shipped no engine code; prose:code ratio 3.2:1;
"30% of tests guard prose"; both prior resets were followed by more
governance, not less.

## Candidate 1 — drop the WORKLOG `Cost:` line

**Finding:** every WORKLOG entry carries a mandatory `Cost:` line (CLAUDE.md
§The three-file session discipline). Recounted fresh on 2026-08-21: **58 of
58 entries say `unmeasured`** — not 49/49 as the original audit had it; the
count only grew. In roughly two months of entries, the field has never once
carried a real number.

**Verdict: drop it.** A field that has never been filled with real data
across 58 consecutive entries is not measurement discipline, it is ritual —
and CLAUDE.md itself distinguishes the two (§Documentation style: "lead with
the takeaway," not with unfilled ceremony). Applied: the `Cost:` requirement
removed from CLAUDE.md's entry-format description and from
`work/WORKLOG.md`'s own template.

## Candidate 2 — merge `work/NOW.md` into `work/INTERVIEW.md`

**Finding:** `NOW.md` is one line, overwritten at every transition.
`INTERVIEW.md` is 1121 lines, the state-of-play doc. Folding the former into
the latter would remove one file from the three-file discipline's surface.

**Verdict: keep them separate.** `NOW.md`'s whole value is being trivially
greppable/readable in one line — by the `UserPromptSubmit` hook, or by a
human glancing at the file — without reading or searching a 1121-line
document. The two serve different read patterns (a hook reads `NOW.md`
unconditionally on every prompt; `INTERVIEW.md` is read deliberately, once,
at the start of a session), not just different content volumes. Folding
them would make the hook's job harder for no real reduction in what a
session has to maintain. **Not applied.**

## Candidate 3 — cap the doc-meta test suite to tests that guard a correctness property

**Finding, corrected on contact:** the original audit's "~30% of tests guard
prose" does not reproduce at file granularity. The dedicated governance/meta
test files — ADR ownership, freshness, frontmatter, owns-consistency,
doc-registry, archive-law, setup-docs, regression-run contracts — total
**35 tests out of 836 in the suite (≈4%)**, not 30%. (`tests/test_frontmatter.py`,
14 tests, was excluded from this count on inspection — it tests the
hand-rolled stdlib frontmatter *parser*, `src/fux/frontmatter.py`, which is
core engine code under L1, not a governance/prose check.) The 30% figure may
have been computed differently (assertion-level rather than file-level, or a
broader definition of "guards prose") — this doc does not know which, and
does not assume.

**Verdict: audit anyway, cut what's purely decorative.** All 35 tests
across all 8 files were read in full for this proposal. **Finding: none are
purely decorative.** Every one guards a real, narrow, mechanical property —
several caught genuine historical bugs before this check existed (three
ownership-drift cases in `test_adr_owns_consistency.py`'s own docstring; two
distinct frontmatter breaks, one invisible to every tool but fux's own
parser, in `test_adr_frontmatter.py`'s). Two are narrower than the rest and
worth naming honestly as borderline: `test_records_do_not_restate_the_laws`
(`test_adr_ownership.py`) catches exactly two hardcoded phrases, not law
restatement in general — real but brittle; `test_mermaid_diagrams_carry_a_
collapsed_ascii_twin` checks a rendering/formatting convention rather than
decision content. Both still guard something real (a specific historical
failure mode, and a diagram that silently fails to render), so neither
qualifies as "purely decorative" under the bar this candidate set.
**No tests cut.** Deleting real regression coverage against an unverified
30%-of-the-suite premise would have been the mistake here, not the fix.

## Candidate 4 — stop superseding an ADR the same day it is written

**Finding:** this session alone produced two same-day supersessions —
ADR-CACHE carved out of ADR-REFER two days after ADR-REFER was written (a
prior session), and ADR-ANSWER needing a substantial rewrite the same day
PRIORITY.md's P6 shipped it (this session). A blanket "no same-day
supersession" rule would have blocked both.

**Verdict: skip.** Every same-day supersession audited this session was
caused by a genuinely new fact surfacing while building — not carelessness,
not churn for its own sake. ADR-ANSWER's rewrite happened because its own
written-down veto condition ("reopen if the disclaimer stops matching what
the verb actually does") *fired*, which is the check working as designed,
not a process failure to prevent. A rule against this would trade honest,
fast correction for artificial delay. **Not adopted.**

## Applied

Candidate 1 only. `CLAUDE.md` §The three-file session discipline and
`work/WORKLOG.md`'s entry-format template both drop the `Cost:` requirement,
in the same commit that files this proposal as `graduated`.

## Found after this round, not litigated here

A concurrent Cowork session filed [`work/governance.md`](../governance.md) —
a governance map of ~90 process files — the same day, independently, and
raised two further diet ideas this proposal's four candidates did not cover:
a yearly (or v-major) archive-and-truncate for `WORKLOG.md` (305 KB and
growing forever, nothing reads old entries back); and scoping
`DOC-REGISTRY.md` to only the docs nothing else already tests. Neither was
put to Arpit in this round — recorded here so they are findable, not lost,
rather than folded silently into this already-decided change. Either would
graduate into its own proposal if picked up.

## Reference

- The audit PRIORITY.md was built from — cited in PRIORITY.md's own
  Maintenance section, 2026-08-20.
- [`work/WORKLOG.md`](../WORKLOG.md), [`work/INTERVIEW.md`](../INTERVIEW.md) —
  the files candidates 1–2 touch.
- [`tests/test_adr_ownership.py`](../../tests/test_adr_ownership.py) ·
  [`tests/test_adr_freshness.py`](../../tests/test_adr_freshness.py) ·
  [`tests/test_adr_frontmatter.py`](../../tests/test_adr_frontmatter.py) ·
  [`tests/test_adr_owns_consistency.py`](../../tests/test_adr_owns_consistency.py) ·
  [`tests/test_doc_registry.py`](../../tests/test_doc_registry.py) ·
  [`tests/test_archive_law.py`](../../tests/test_archive_law.py) ·
  [`tests/test_setup_docs.py`](../../tests/test_setup_docs.py) ·
  [`tests/test_regression_runs.py`](../../tests/test_regression_runs.py) —
  candidate 3's full audit set.

## Graduation trigger

Already graduated — Arpit ruled on all four candidates directly, in the
session that filed this proposal. Nothing here is still parked.
