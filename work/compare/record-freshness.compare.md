---
type: Compare Doc
title: Record Freshness
description: Whether a committed record needs a timestamp so an age bound can be honoured — and if so, where a deterministic one comes from.
status: accepted
timestamp: 2026-08-20T00:00:00Z
---

# Bounding staleness without a clock — Comparison

> **Verdict: D — no age bound. Content verification is the answer, and
> `max_age_seconds` is struck from the proposal.**
> The engine already ships **both endpoints of the freshness axis** —
> `never` (don't revalidate) and `always` (revalidate every time). `max_age` is
> the *middle*, and in HTTP — where this whole vocabulary comes from — the
> middle exists to **avoid the fetch**, not to make the answer more correct.
> Nobody has measured that fetch cost yet: **R4 is unmeasured**
> ([W-59](../../archive/open/W-59-refer-plane-measurement.md)). Deciding a cost
> optimisation before measuring the cost is backwards.
> **Status:** ✅ decided 2026-08-20 — Arpit: **D**. **Confidence:** high on
> rejecting B (mtimes), high on A/C collapsing into one option, medium on D
> over E — D is a bet that the cost never bites.
> **Reopen when:** R4's measurement shows warm-path fetch cost dominating and a
> caller willing to trade staleness for latency. Then build **E**, not A/B/C.


> ## ⚠ THE PREMISE OF THIS VERDICT IS DEAD, 2026-08-25 — and the ruling is Arpit's
>
> This doc was decided **D — no age bound**, on the ground that *"none of a
> committed record's fields is temporal"* and therefore *"that provenance does
> not exist"*. **Every committed record now carries `mtime`**, a git commit
> timestamp written by `ingest/run.py` from `priors.git_commit_times` — which
> is exactly the provenance the verdict said was absent.
>
> **This is not an agent's to re-decide.** It is filed as
> [W-82 §5.3](../open/W-82-the-consolidated-build.md) ruling 1, in the `arpit` lane:
> *"ADR-REFER decision 4 is currently **standing but unargued**, which is the
> one state a record should never be in."*
>
> **Four further claims in the body are now false**, listed so a reader does
> not act on them:
>
> - *"fields are `id · src · loc · sha · ver · mode · meta · title · phrases ·
>   terms · wlen · edges`. **None is temporal.**"* — `wlen` became `flen`, and
>   `mtime` is temporal.
> - the matrix's *"one git call per file"* cost for option C — `priors.py` does
>   the whole corpus in **one** invocation, and its docstring says a per-file
>   call was rejected precisely because it would be 10 000 spawns.
> - the matrix's *"A and C break byte-reproducibility"* — contradicted by the
>   shipped code, which commits a **git commit timestamp** specifically so the
>   value does not vary by machine, and does so without breaking write-if-different.
>
> ⚠ The same dead premise is recited in `src/fux/refer/freshness.py`'s module
> docstring.

## Context

A committed record's fields are `id · src · loc · sha · ver · mode · meta ·
title · phrases · terms · wlen · edges`. **None is temporal.** `ver` is a
revision counter — it increments when the content sha changes — and says
nothing about *when*.

[`caller-set-freshness-policy.md`](../../archive/proposals/caller-set-freshness-policy.md)
specified `{max_age_seconds, timeout_seconds}`, with age measured against
recorded provenance. **That provenance does not exist**, so
[ADR-REFER](../../docs/adr/0030_refer-plane.md) decision 4 refused to ship the
knob: a caller passing `max_age_seconds=60` would reasonably believe they had
bounded their staleness. **A knob that lies is worse than a missing knob.**

`.fux/runtime/stamp.json` holds mtimes and is **excluded** from
`DETERMINISTIC_FILES` for exactly this reason.

## What the field already worked out

**HTTP separates the two mechanisms this item conflates.** *Freshness lifetime*
(`max-age`, `Expires`) says how long a response may be reused **without
contacting the server**. *Validators* (`ETag`, `Last-Modified`) enable a
conditional request that returns `304` when nothing changed. RFC 9110 prefers
**`ETag` over `Last-Modified`** because content-based validation beats
timestamps: no clock synchronisation, and it catches changes a timestamp
misses.

**Fux's content verification is an `ETag`.** Comparing the fetched sha against
the recorded one is `If-None-Match`, and it is *strictly more precise* than any
age. So the question is not "how do we bound staleness" — that is solved — but
**"do we want to skip the check to save the fetch."** That is `max-age`'s only
job.

**And the reproducible-builds world already solved the timestamp half.**
`SOURCE_DATE_EPOCH` exists because build tools embedding wall-clock time break
bit-for-bit reproducibility. The conventional value in a git repository is
**the last commit date** — `git log -1 --pretty=%ct`. Which means **options A
and C are the same option**: "derive a deterministic stamp" and "use the git
commit date" are the same answer, and it is standardised.

## Options

- **A — a `SOURCE_DATE_EPOCH`-derived stamp per record.**
- **B — the source file's mtime**, floored to a coarse unit.
- **C — the git commit date of each file.**
- **D — no age, ever** *(proposed verdict)*: content verification is the
  answer; `max_age_seconds` is struck.
- **E — one corpus-level stamp**, not per record: a single committed
  `.fux/index/STAMP` holding the `SOURCE_DATE_EPOCH` of the ingest, by
  convention the HEAD commit date.

## Matrix

| criterion (weight) | A per-record epoch | B mtime | C per-file git date | **D none** | E corpus stamp |
|---|---|---|---|---|---|
| survives a clone (H) | yes | **no** | yes | n/a | yes |
| byte-reproducible index (H) | **no** — see below | no | **no** — see below | **yes** | **yes** |
| answers "how old is *this document*" (M) | yes | yes | **yes** | no | **no** — index age only |
| cost at ingest (M) | one call | free | **one git call per file** | free | one git call per run |
| `_format` bump (M) | yes | yes | yes | **no** | yes, header only |
| honest about what it measures (H) | *build* time, not source time | source time | **source time** | n/a | index time |

## Why the losers lose

**B is the trap, and it is the intuitive answer.** **Filesystem mtimes do not
survive a clone.** A fresh CI checkout resets every one, so the whole corpus
would read as written seconds ago — the age resets exactly when you most want
it. It is also the reason `stamp.json` is already excluded from the
deterministic set. **Naming this loudly is half the value of this document.**

**A and C break byte-reproducibility in a way that is easy to miss.** A
per-record timestamp is a field inside a shard. Re-ingesting after any commit
changes that field, so **write-if-different rewrites every shard on every
run** — and `git status` clean after an unchanged re-ingest is the guarantee
[ADR-INGEST](../../docs/adr/0007_ingest.md) rests on. C additionally asks the
git-dir walker to read git *objects*; it deliberately reads bytes.

**E is the right shape if an age is ever wanted**, and it is why D is a bet
rather than a refusal. One committed `STAMP` file, outside the shards, so no
record changes and no shard is rewritten. **Its weakness is real and
disqualifying today**: it dates the *index*, not the *document*. A file
untouched for a year in an index rebuilt yesterday reads as fresh — which is
the same approximation that made `max_age` worse than verification in the
first place.

**D's cost is honest**: the proposal's row for *"an agent mid-loop wants a
generous `max_age`"* is served by `never` instead — no fetch, no verification,
explicitly stale. That is a coarser instrument, and it is the instrument that
exists.

## Consequences

- **`max_age_seconds` is struck** from the proposal, and
  [ADR-REFER](../../docs/adr/0030_refer-plane.md) records the closure — its
  veto condition 3 is exactly this question, so it fires and is answered rather
  than left open.
- **No `_format` bump, no ADR-RECORD change, nothing rewritten.** D is the only
  option that costs nothing, which matters when the need is unmeasured.
- **The refer plane keeps two modes**, `never` and `always`, and they remain
  the endpoints. If E ever lands, it slots between them without changing
  either.
- **This decision is measurable later and not now.** R4 has not run
  ([W-59](../../archive/open/W-59-refer-plane-measurement.md)), so the cost `max_age`
  would avoid is unknown. Under the repo's own rule — never ship off an
  unmeasured hunch — that settles it for today.

## Reopen trigger

**R4 measures the warm path and the fetch dominates it**, and a caller states
they would accept bounded staleness to avoid it. At that point build **E** — a
corpus-level committed stamp — and not A, B or C. The trigger is a filed run
under [`work/regression/`](../regression/README.md), not an opinion.

## References

- HTTP caching: freshness lifetime vs validators, and why `ETag` is preferred
  over `Last-Modified` — https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching
- `SOURCE_DATE_EPOCH`, and the git-commit-date convention —
  https://reproducible-builds.org/docs/source-date-epoch/
- Why timestamps break reproducibility —
  https://reproducible-builds.org/docs/timestamps/
- The refusal this doc either confirms or overturns —
  [ADR-REFER](../../docs/adr/0030_refer-plane.md) decision 4.
- The finding — [W-58](../../archive/open/W-58-no-recorded-ingest-time.md).
