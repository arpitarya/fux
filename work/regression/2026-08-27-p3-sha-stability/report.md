---
type: Report
title: W-87 P3 — sanitized-sha stability against a real URL corpus
description: "19/19 documentation URLs returned a byte-identical sanitized sha on an immediate re-fetch. The frozen threshold is >= 80 %, so fork 3 clears it. A control arm proves the instrument can detect change."
classification: informed
timestamp: 2026-08-27T17:26:30Z
---

# W-87 P3 — sanitized-sha stability

**Adjudicates:** W-87 P3 (= W-82 §3.0), whose threshold table is frozen in
[`work/open/W-87-what-good-means.md`](../../open/W-87-what-good-means.md) §P3.
**Result:** [`VERDICT.md`](VERDICT.md).

## ⚠ Disclosures, before the number

**Classification: `informed`.** The spec was read before the run, exactly as
W-87 P3 anticipated (*"that is the correct label, not a reason to delay"*).

**This report collides with [ADR-RS](../../../docs/adr/0036_predictions.md)
decision 12** — *"an informed run … is never used to state a difference between
arms"* — and P3's spec ruled in advance: **disclose the conflict; do not
self-exempt and do not narrow decision 12.** So:

- **The headline number is a fraction within one arm**, not a delta between
  arms: *how many of N URLs returned the same sha as themselves*.
- **The control arm below IS a comparison between two arms**, and it is reported
  anyway, because without it a 100 % result is indistinguishable from a broken
  instrument. **That is the conflict, stated rather than routed around.**
- ⚠ **This is the fourth time decision 12's disclosure has been written**
  (`2026-08-22-archived-signal`, `2026-08-25-model-removal`,
  `2026-08-25-supersession-and-reranker-default`, and here). Decision 12's own
  reopen trigger is *"when the disclosure has been written three times."*
  **It has now been. The trigger has fired** — see [`ANALYSIS.md`](ANALYSIS.md) §3.

**The corpus was chosen by this session**, and corpus choice determines this
number entirely. §The corpus states exactly what was picked and why, because
*"an aggregate delta of zero over an untreated population is not evidence"*
(CLAUDE.md, the M1 lesson).

## The corpus

`~/my_programs/fux-lab/2026-08-27-p3-sha-stability` — a **new** lab environment,
never a rebuild of the lab. One local Markdown file plus **19 real external
documentation URLs**, verbatim in [`evidence/corpus.txt`](evidence/corpus.txt).

| class | n | examples |
|---|---:|---|
| frozen archival | 7 | RFC 7231 / 2616 / 3986 / 6265, PEP 8 / 20 / 484 |
| live project docs | 4 | `docs.python.org` pathlib · json · subprocess · tutorial/errors |
| encyclopedic, editable | 3 | Wikipedia HTTP · SRE · Runbook |
| a live status page | 1 | `githubstatus.com` |
| misc stable | 4 | `example.com`, IANA example-domains, `httpbin.org/html`, `go.dev/doc/faq` |

**Deliberately excluded from the headline arm:** endpoints that change on every
fetch. Including them would have stacked the deck toward failure exactly as an
all-archival corpus would have stacked it toward success. They appear in the
control arm instead, where their job is to change.

## The measurement

`fux update`, twice. `.fux/runtime/url-shas.json` is url → **sanitized** sha and
is copied after each run; [`evidence/compare.py`](evidence/compare.py) diffs two
copies and calls no fux code.

**Run 1 `17:25:41Z` · Run 2 `17:25:53Z` — 12 seconds apart.**

```
n = 19 fetched URLs present in both runs
sanitized sha UNCHANGED: 19/19 = 100.0%
changed: none
```

`0 skipped` in both runs; 19 of 19 listed URLs fetched.

## The control arm — the instrument can detect change

A 100 % result with no control is the M1 failure: a treatment that touched
nothing, reported as a null effect. Two known-volatile URLs were added and the
pair of runs repeated.

```
n = 20 fetched URLs present in both runs
sanitized sha UNCHANGED: 19/20 = 95.0%
changed:
   https://en.wikipedia.org/wiki/Special:Random
```

**`Special:Random` changed and the 19 documentation URLs did not.** The
comparison is live, the sanitizer is not flattening everything to a constant,
and the 100 % above is a property of the corpus rather than of the harness.

⚠ **`httpbin.org/html` was in the list twice** — once in the corpus, once
mistakenly re-added as a control — and fux **deduplicated it correctly**
(`sorted(set(...))` in `_fetch_group`). 21 listed lines, 20 unique URLs, 20
shas. Recorded because the discrepancy looked like a silently dropped URL for
several minutes and was not one.

## Against the frozen threshold

| frozen row | this run |
|---|---|
| **≥ 80 %** → fork 3 is **yes**, the contract gains an optional `validate` | **100 %** — clears it |
| ≤ ~40 % → the contract stays at four functions | — |
| between → ambiguous, to Arpit | — |

**The threshold was not moved, restated, or re-binned.**

## ⚠ What the number does NOT mean

**The spec names no interval, and the answer depends on it completely.** These
runs are **12 seconds** apart.

- **What 12 seconds measures is server-side determinism**: does a server return
  bytes that sanitize identically when nothing about the document changed?
  Timestamps, ad slots, CSRF tokens, session ids, randomized element ids and
  rotating banners all break it. **None of 19 real pages did** — including a
  live status page — and that is the precondition for a validator to mean
  anything.
- **What it cannot measure is document churn over a sweep interval**, which is
  the other half of what `validate` would be worth. That needs runs hours or
  days apart and **is not what this number is.**
- **19 URLs, one session, public internet.** Three orders of magnitude below the
  10 000-document design point, and nothing here generalises to a corporate
  wiki, where editable pages are the norm rather than the exception.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the URL corpus and its classes | Claude Code (Opus 5), 2026-08-27 | the P3 spec including its frozen threshold |
| the two runs, the control arm, `compare.py` | the same session | the same |
| this report and the verdict | the same session | the same |

**No blind arm exists and none is pretended.** Nothing here is compared against
a blind number.

## Reproduce

```bash
cd ~/my_programs/fux-lab/2026-08-27-p3-sha-stability/repo
fux update && cp .fux/runtime/url-shas.json /tmp/a.json
fux update && cp .fux/runtime/url-shas.json /tmp/b.json
python3 <fux>/work/regression/2026-08-27-p3-sha-stability/evidence/compare.py /tmp/a.json /tmp/b.json
```
