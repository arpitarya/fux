---
type: Analysis
title: What P3's PASS unblocks, the interval its spec never named, and a reopen trigger that has now fired
description: Fork 3 clears its gate. Two process findings come with it — a threshold whose spec omits the variable that determines the answer, and ADR-RS decision 12's disclosure written for the fourth time.
timestamp: 2026-08-27T17:26:30Z
---

# Analysis — P3, sanitized-sha stability

## 1 · Fork 3 is unblocked; P4 can start

**19/19 = 100 %** against a frozen `≥ 80 %`. Per W-87 P3's table, **fork 3 is
*yes***: the fetcher contract may gain an optional `validate`.

**The specific improvement:** W-87 **P4** was gated on this number and is not
gated any more. Its two forks can be taken —

- **Fork 3** — amend the four-function contract with `validate`. ⚠ **Cleared, not
  decided.** ADR-FETCHER decision 3's argument against anything that composes is
  independent of this measurement, and a fifth function is a design call.
- **Fork 4** — where the validation token lives. `.fux/runtime/url-state.json`
  costs L3 nothing, and W-87 already fixes the shape: **store `sha256(token)`,
  never the token**, so L5 is untouched.

**Repro:** `evidence/compare.py evidence/run1-url-shas.json evidence/run2-url-shas.json`.

## 2 · The spec omitted the variable that determines the answer

**P3 says *"run `fux update` twice"* and names no interval.** The answer depends
on it completely: seconds apart, a static corpus is trivially near-100 %; a week
apart, the same corpus could be anything.

**This is not a reason to withhold the verdict** — the threshold is frozen, 100 %
is unambiguously above 80 %, and re-reading a frozen rule to make a result
harder is the moving-threshold failure with the sign flipped. It **is** a reason
to say precisely what the number measures, which the report does.

⚠ **And on inspection the spec is sounder than it first looks.** At a short
interval the measurement isolates **server-side nondeterminism** — timestamps,
ad slots, CSRF tokens, session ids, rotating banners — which is exactly the
thing that would make a validator useless no matter how stable the underlying
documents are. **None of 19 real pages exhibited it, including a live status
page.** That is the precondition, and it is now measured.

**The improvement, for the next threshold of this shape:** a pre-registration
that measures a rate over time must state the interval, in the same sentence as
the threshold. **This is the second pre-registration defect found today** — R10's
was two rules that contradict each other. Both were invisible until real data
arrived, which is the argument *for* freezing documents early, not against.

## 3 · 🔴 ADR-RS decision 12's reopen trigger has FIRED

Decision 12 carries its own trigger:

> **Reopen when** the disclosure has been written three times — at that point
> the repetition is itself the argument that the wording, not the runs, is what
> costs effort.

**It has now been written four times**, in four separate runs:

| run | where |
|---|---|
| `2026-08-22-archived-signal` | `ANALYSIS.md` |
| `2026-08-25-model-removal` | `report.md` (×2) and `ANALYSIS.md` |
| `2026-08-25-supersession-and-reranker-default` | `ANALYSIS.md` |
| `2026-08-27-p3-sha-stability` | `report.md`, and this file |

**The condition is met and is recorded here rather than acted on.** Decision 12
is Arpit's — its own text says *"Arpit ruled the text stands unchanged"* and
⚠ *"do not narrow decision 12. Disclose."* **A session that reopened it would be
doing the exact thing the block forbids**, so this names the fired trigger and
stops.

**What reopening would consider**, stated so the next reader does not re-derive
it: decision 12's wording forbids an informed run from *"stating a difference
between arms"* without qualifying that contamination requires an **evaluation
set** to exist. A control arm proving an instrument works is a difference
between arms with nothing to have been contaminated by.

## 4 · Unresolved, and stated as unresolved

- **Whether fork 3 should be taken.** Cleared ≠ decided.
- **The realistic-interval question.** How often documents actually change
  between sweeps is unmeasured and needs a new pre-registration with an interval
  in it. **Not owed by this run.**
- **A corporate corpus.** Nineteen public documentation pages say nothing about
  an internal wiki, where editable pages are the norm rather than the exception,
  and where the proxy/SSO layer that
  [the daemon run](../2026-08-27-daemon-real-url/ANALYSIS.md) could not cover
  sits in front of every fetch.
