---
type: Report
name: cdp-parallel-2026-09-02
title: "W-105 — the cdp fetcher under real concurrency, before and after"
description: "Real Chrome, real CDP, a real thread pool, over 12 locally-served pages that each state their own path. The pre-W-105 fetcher attributes a real response to the wrong URL at every parallelism above 1; HEAD is clean at 1, 2, 4 and 6 and leaks no tabs. The only evidence that can exist for this change, because no test in the repo can see the failure."
classification: informed
timestamp: 2026-09-02T00:00:00Z
---

# W-105 — cdp.py under real concurrency

**The claim being checked.** W-105 says the pre-fix `cdp.py` shares `_msg_id`,
`_results`, `_events` and one page target across threads, and that the
consequence is **a real response filed under the wrong URL** — in the committed
index, past every determinism check, with a human reading an answer as the only
detector.

**Why it needed a live run.** The work document and
[ADR-CDP-FETCHER](../../../docs/adr/0020_cdp-fetcher.md) both say plainly that
**no test in this repo can catch it.** The fake-Chrome tests drive one thread
through a scripted peer; the failure only exists when two threads share one
browser. So the check is a browser.

## Method

- **12 pages served from `127.0.0.1:8781`**, each carrying `[MARKER:pN]` and
  nothing else that looks like a marker. **A response filed under the wrong URL
  is therefore visible as a mismatch** — that is the whole design.
- **Per-request jitter** (50–350 ms, keyed off the path) so workers interleave
  rather than completing in issue order, which is what makes the race reachable.
- **Real Chrome**, headless, its own throwaway profile, on port 9223, so the
  human's browser is untouched.
- **Two arms, one harness**: `pre-w105` is `cdp.py.txt` at
  `0840b52`; `head` is the working tree. Both driven by the same
  `ThreadPoolExecutor` at parallel 1, 2, 4 and 6.
- **Three checks per arm per parallelism**: does each `fetch` return **its own**
  page · does each `validate` return **its own** ETag · does `close()` leave the
  browser with exactly the tabs it started with.

`evidence/harness-live.py` is the harness verbatim; `harness-live-old.py` is the
same file with the module path swapped and `MAX_PARALLEL` set directly (the old
module has no `fetcher_max_parallel` key — W-105 added it).

## Result

Per-URL rows: `evidence/per-url-rows.jsonl`, 200 rows — one per URL per check
per arm per parallelism, plus a tab row per run.

| parallel | arm | fetch: own page | validate: own ETag | tabs leaked | verdict |
|---:|---|---:|---:|---:|---|
| 1 | pre-w105 | **12 / 12** | **12 / 12** | 0 | PASS |
| 1 | head | **12 / 12** | **12 / 12** | 0 | PASS |
| 2 | pre-w105 | **0 / 12** | 0 / 12 | 0 | **FAIL** |
| 2 | head | **12 / 12** | **12 / 12** | 0 | PASS |
| 4 | pre-w105 | **1 / 12** | 1 / 12 | 0 | **FAIL** |
| 4 | head | **12 / 12** | **12 / 12** | 0 | PASS |
| 6 | pre-w105 | **0 / 12** | 0 / 12 | 0 | **FAIL** |
| 6 | head | **12 / 12** | **12 / 12** | 0 | PASS |

**The two rows that matter most are the parallel-1 rows.** Both arms pass. The
old code was never broken at the ceiling it shipped at — decision 7b's claim,
measured. What was broken is **raising it**, which is the thing the old comment
told a reader was safe for the wrong reason.

### 🔴 Seven of the failures are SILENT

An error is loud: fux skips the URL and keeps the previous record. A **mismatch**
is not — a real page, decoded, indexed, attributed to a URL it did not come from.

| arm · parallel | URL asked for | got |
|---|---|---|
| pre-w105 · 2 | `/p2` `/p3` `/p5` `/p7` `/p11` | another page's body, 200 OK |
| pre-w105 · 4 | `/p7` | another page's body, 200 OK |
| pre-w105 · 6 | `/p2` | another page's body, 200 OK |

`validate()` fails the same way and is worse, because its output is an opaque
token nobody eyeballs: at parallel 4 the pre-fix arm returned `"etag-p6"` for
`/p4`, `"etag-p8"` for `/p6` and `/p7`, and `"etag-p12"` for `/p9`. **A wrong
ETag that happens to match makes fux skip a document that did change.**

### The errors are the same bug, wearing a louder coat

`Fetch.getResponseBody failed: Can only get response body on requests captured
after headers received` is one thread resolving another thread's request id.
`CDP connection died waiting for Fetch.requestPaused` is one thread's
`_results.clear()` deleting the reply another thread was blocked on. Both are
the shared-state half of W-105; the mismatches are the shared-tab half.

## What this does NOT show

- **Nothing about real sites.** Twelve pages on loopback with synthetic jitter
  are a race amplifier, not a corpus. The failure counts here are a property of
  this harness's timing, not a rate anyone should quote.
- **Nothing about a signed-in wiki**, which is what the cdp fetcher exists for.
  Loopback pages need no auth and the profile is throwaway.
- **No ranking, no index, no `loc` field.** This runs the fetcher module
  directly. The claim it grounds is *"the bytes returned for a URL are that
  URL's bytes"* — which is the input `loc` correctness rests on, one layer down.
- **`MAX_PARALLEL` still ships at `1`.** This run is what makes raising it a
  decision someone can take, not the taking of it.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the harness, the 12 pages, the jitter | Claude Opus 5, this session | the defect description in W-105 and ADR-CDP-FETCHER — **full knowledge of what it was built to expose** |
| the `head` arm's code | the 2026-09-01 session | the same |
| the `pre-w105` arm's code | frozen at `0840b52` | n/a |
| this report and ANALYSIS.md | Claude Opus 5, this session | both arms' output |

**`informed`, and the label is doing real work here.** A harness written by
someone who knows the failure is a harness aimed at it: the jitter exists
*because* the race needs interleaving, and a different jitter would give
different counts. What the run supports is the **direction** — pre-fix
corrupts above parallel 1, HEAD does not, at four settings — and it is
**not a generalisation estimate** of how often this would bite in production.

Both arms are informed and were graded by one harness on one set, so nothing
here is compared against a blind run.
