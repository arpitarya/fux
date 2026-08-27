---
type: Report
title: The daemon against five real external URLs — TLS, DNS, CDN, a real 404 and a real 429
description: "start -> sweep -> a page that genuinely changed, picked up unassisted one interval later -> stop. The clause localhost could not cover, covered. A SURFACE CAPTURE: no threshold, no delta."
classification: surface capture
timestamp: 2026-08-27T16:53:50Z
---

# The daemon against real external URLs — 2026-08-27

> **A SURFACE CAPTURE.** It states no delta, gates no prediction and
> pre-registers no threshold, so the blind/informed rule does not reach it
> ([ADR-RS](../../../docs/adr/0036_predictions.md) decision 11).

## Why it exists

**`OPEN-WORK.md` hands item 1**, which held [W-82](../../OPEN-WORK.md) ruling 3.
[The earlier capture the same day](../2026-08-27-daemon-lifecycle/report.md)
proved the lifecycle against a **local** HTTP server and named the gap it could
not close: *"no proxy, no TLS, no SSO, no rate limit, no DNS."*

**Arpit authorised this run.** It closes that gap for TLS, DNS, CDN, a real
`404` and a real `429`. **It does not cover a proxy or SSO** — see §What it
still does not establish.

## The environment

`~/my_programs/fux-lab/2026-08-27-daemon-real-url/repo` — a new environment
inside the lab, never a rebuild of it (lab README §Standing rule). One local
Markdown document plus **five, later seven, real external URLs**.
`[sources.url] sweep_minutes = 1`.

| URL | why it is in the set |
|---|---|
| `https://example.com/` | the canonical stable page — TLS + DNS, tiny |
| `https://www.rfc-editor.org/rfc/rfc7231.txt` | `text/plain` over TLS, 235 KB — a real document |
| `https://docs.python.org/3/library/pathlib.html` | `text/html` behind a CDN, 267 KB — the decoder path |
| `https://httpbin.org/uuid` | `application/json` **whose body changes every fetch** |
| `https://example.com/definitely-not-there` | a **real 404** — the skip path |
| `https://en.wikipedia.org/wiki/Special:Random` | **content genuinely differs between sweeps**, on a server nobody here controls |
| `https://httpbin.org/status/429` | a **real 429** — the rate-limit path, never previously exercised |

## What was run

| # | command | result |
|---|---|---|
| 1 | `fux ingest` | `ingested 1 docs` — **URLs untouched.** `ingest` is offline; only the sweep passes `refresh_urls=True` |
| 2 | `fux find "hypertext transfer protocol semantics"` | `0 results` — the **baseline of the positive control** |
| 3 | `fux daemon start`, `16:48:07Z` | `sweeping every 1 min`, pid 15646 |
| 4 | `fux daemon status --json`, +6 s | `{"last": {"outcome": "ok"}, "running": true}` |
| 5 | the same `find` | **2 results** — `rfc7231.txt` and `pathlib.html`, fetched over TLS from two different hosts |
| 6 | the index | 4 records: 1 file + **3 URLs** (`example.com`, `rfc-editor.org`, `docs.python.org`) |
| 7 | restart with 7 URLs, `16:51:29Z` | — |
| 8 | poll the Wikipedia record's title | `16:51:55Z` **Laurence Bennett** → `16:52:55Z` **Bargilt Iron Ore Mine** |
| 9 | `fux doctor` | `rate-limited by httpbin.org x8` |
| 10 | `fux daemon stop`, `16:53:50Z` | `daemon: stopped` |
| 11 | `fux daemon status --json` | `{"last": {"outcome": "stopped"}, "pid": null, "running": false}` |
| 12 | `ps -p 16075` | **gone** |
| 13 | `fux doctor --json` → `runner` | `lock: "free"`, `pending: 0` |

## What this establishes that localhost could not

- **TLS, DNS and a CDN, on the sweep path.** Three hosts, two CDNs, 500 KB of
  real payload, inside a detached process on a 1-minute clock.
- **The freshness loop closes over the real internet.** Step 8 is the whole
  point of the URL tail: `Special:Random` served a **different article**, and
  the daemon re-fetched, re-decoded and re-indexed it **unassisted**, one sweep
  interval later, with nobody typing a command. Wikipedia is not a server this
  repository controls, so the change was genuinely external.
- ⚠ **The rate-limit path fired for the first time, against a real `429`.**
  `fux doctor` reports `rate-limited by httpbin.org x8` — W-82 ruling 12's
  cumulative count, persisted and reachable **through its only reader**. That
  reader had a bug fixed hours earlier without ever being run against a real
  refusal; it now has been.
- **A real `404` is a recorded skip, not a crash**, and the prior record is
  kept: `! https://example.com/definitely-not-there — fetch failed: HTTPError:
  HTTP Error 404: Not Found; prior record kept`.

## Two defects found by doing it

Both are in [`ANALYSIS.md`](ANALYSIS.md); both are fixed and gated.

1. **A skip said `no decoder for application/json` when the decoder existed,
   claimed the type, and ran.**
2. **Consumer decoders never applied to URL content** — `decode()` was called
   without `root`.

## What it still does NOT establish

- ⚠ **No proxy and no SSO.** Two of the five conditions the earlier capture
  named are still uncovered, and they are the two that need a corporate network
  rather than the public internet.
- ⚠ **`max_parallel` was 4 against 7 URLs** and concurrency was never
  stressed.
- ⚠ **macOS only.** Windows is untested, and detached-process mechanics are
  where it is most likely to differ.
- ⚠ **A sweep still reports `"failed"` with no reason.** Nothing failed a sweep
  here, so this run says nothing about it; it remains the open decision in
  `OPEN-WORK.md`.

## Authorship

Not required — a surface capture is exempt — and recorded anyway.

| artifact | author | could reach |
|---|---|---|
| the lab environment, the URL set, the commands | Claude Code (Opus 5), 2026-08-27 | the repo; no evaluation queries or judgments exist for this run |
| this report | the same session | its own transcript and `evidence/` |

## Reproduce

`evidence/environment.txt` holds the URL list and `fux doctor` output verbatim;
`evidence/sweep-poll.txt` is the raw 15-second poll, including the title change
at `16:52:55Z`.

```bash
cd ~/my_programs/fux-lab/2026-08-27-daemon-real-url/repo
fux ingest && fux find "hypertext transfer protocol semantics" --json   # 0 results
fux daemon start && sleep 90 && fux daemon status --json                # outcome: ok
fux find "hypertext transfer protocol semantics" --json                 # 2 results
fux doctor | grep rate-limited                                          # httpbin.org xN
fux daemon stop
```
