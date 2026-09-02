---
type: Analysis
name: cdp-parallel-2026-09-02-analysis
title: "What the W-105 run changes, and the three things it leaves open"
description: "The diagnosis: the fix holds at 2, 4 and 6, the pre-fix code fails silently at every one of them, and the shipped ceiling of 1 was never itself unsafe. Three follow-ups, each with a repro command."
timestamp: 2026-09-02T00:00:00Z
---

# Analysis — 2026-09-02, cdp under concurrency

## Diagnosis

**1. The fix is real and the defect was real.** Not one of the eight
pre-fix/post-fix cells is ambiguous: below the change, every parallelism above 1
mis-attributes or errors; above it, all four are clean. Nothing about the
harness distinguishes the arms except the module under test.

**2. The old ceiling was correct; the old *reason* was the defect.** Both arms
pass at parallel 1. The comment in the shipped file said the constraint was one
shared WebSocket that every `fetch()` reuses — false since `fetch_resource`
started opening a socket per call. **A reader who checked that claim would have
found it untrue and raised the ceiling**, and the run above is what that reader
would then have shipped. The hazard was the explanation, not the number.

**3. `validate()` is the sharper edge, and it is the one a reader skips.**
`fetch` corruption puts a wrong body in the index, which a person may eventually
notice reading an answer. `validate` corruption returns a wrong opaque token,
and a wrong token that happens to match makes fux **skip a document that
changed** — a staleness that no surface reports, because from fux's side nothing
happened. It shares the session, so it inherited the same bug and the same fix.

**4. Tab hygiene holds.** `close()` returned the browser to its starting tab set
in all eight runs, including the pre-fix runs that errored 11 of 12 URLs. The
`_opened` set — rather than diffing `/json` — is why an error path does not leak.

## Improvements

### 1 · Fold the harness into a marked live test rather than leaving it as evidence

It is currently a file under `evidence/`, which means it runs when somebody
remembers it. The failure it catches is the one CI structurally cannot see, so
"remembered" is the weakest possible place for it.

- **Not resolved here, and deliberately not rushed.** It needs Chrome on the
  runner, a served fixture, and a marker (`@pytest.mark.live`) that keeps it out
  of the default run — otherwise `uv run pytest -q tests` starts requiring a
  browser, which is a worse trade than the gap it closes.
- Repro today:
  `ARM=head ROWS=/tmp/rows.jsonl .venv/bin/python work/regression/2026-09-02-cdp-parallel/evidence/harness-live.py 4`
  (run it from a directory holding `old-cdp.py.txt` for the `-old` variant).

### 2 · Decide the ceiling deliberately, with this run in hand

`MAX_PARALLEL` ships at `1` and `fetcher_max_parallel` is the knob. **This run
does not raise it and should not be read as recommending a number** — it shows
`6` is *correct* on loopback, which is not the same as *polite* to a corporate
wiki. Politeness is `[sources.url] max_parallel`, and it is a consumer's call.

### 3 · Unresolved: no evidence at all for a signed-in, real-world target

Every page here is loopback HTML with no auth, no redirects, no CDN hop and no
download. The cdp fetcher exists precisely for the opposite of that. **This is
stated as unresolved rather than papered over:** the concurrency claim is
grounded, the *fetcher's own reason for existing* is exercised by nothing in
this run. Closing it needs a real signed-in target and therefore a human.

## What is NOT concluded

- No rate, frequency or probability. The counts are a property of this harness's
  jitter (see the report's *What this does NOT show*).
- Nothing about `loc` as a record field — this is one layer below ingest.
- No threshold was pre-registered and none is created retroactively. This is a
  correctness run, not a gate: there is no `VERDICT.md` because there was no
  prediction to rule on.
