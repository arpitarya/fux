---
type: Report
title: The daemon's whole lifecycle, against a real detached process, a real clock and a real HTTP server
description: "start -> sweep -> a changed page picked up on the next interval -> stop -> nothing resident. A SURFACE CAPTURE: no threshold, no delta, no prediction gated."
classification: surface capture
timestamp: 2026-08-27T15:13:00Z
---

# The daemon's lifecycle — 2026-08-27

> **This is a SURFACE CAPTURE, not a measurement.** It states no delta, gates no
> prediction and pre-registers no threshold, so the blind/informed rule does not
> reach it ([ADR-RS](../../../docs/adr/0036_predictions.md) decision 11). Its
> whole content is *"the commands were run and this is what came back."*

## Why it exists

**`work/OPEN-WORK.md` hands item 6 held W-82 ruling 3.** Narrow-by-default was
not to land until the daemon was proven to run in a real repository — *"a
detached process, a real clock and a real network"* — because `_sweep` had been
returning `"failed"` on every sweep in every repository and the broad
`except Exception` made it look healthy.

**One clause is NOT satisfied here and the hold is not discharged by this run:**
the network was a **`python3 -m http.server` on `127.0.0.1`**, not the public
internet. No proxy, no TLS, no SSO, no rate limit, no DNS. Those are exactly the
failure modes an enterprise URL corpus has and this run cannot see.

## What was run

A scratch git repository outside this one: `fux setup`, one local Markdown
document, and **one URL line** pointing at a local HTTP server.
`[sources.url] sweep_minutes = 1`, `max_parallel = 2`.

| # | command | result |
|---|---|---|
| 1 | `fux ingest` | `ingested 1 docs` — **the URL is not fetched**, which is correct: `ingest` is offline, and only the sweep passes `refresh_urls=True` |
| 2 | `fux find daemonsweepterm --json` | `{"results": []}` — **the positive control's baseline.** The term exists only in the served page |
| 3 | `fux daemon start` | `daemon: started — sweeping every 1 min.` |
| 4 | `fux daemon status --json` | `{"last": null, "pid": 10514, "running": true}` |
| 5 | `fux daemon status --json`, +1 s | `{"last": {"outcome": "ok"}, "pid": 10514, "running": true}` |
| 6 | `fux find daemonsweepterm --json` | **1 result**, `id: url:http://127.0.0.1:8731/runbook.html`, title `Oncall runbook` |
| 7 | *the served page is edited*, `15:11:21Z` | a second term, `secondsweepterm`, added to the HTML |
| 8 | `fux find secondsweepterm --json`, polled | `hits=0` at `15:11:27` … `15:11:58`; **`hits=1` at `15:12:04`** — one `sweep_minutes` interval later, on the wall clock |
| 9 | `fux daemon stop` | `daemon: stopped` |
| 10 | `fux daemon status --json` | `{"last": {"outcome": "stopped"}, "pid": null, "running": false}` |
| 11 | `ps -p 10514` | **gone** |
| 12 | `fux doctor --json` → `runner` | `lock: "free"`, `pending: 0`, `running: false` |

## What this establishes

- **The sweep reaches ingest.** Step 6 is a **positive control**, not a status
  read: the term was absent from the index before the daemon started and present
  after, and it exists nowhere except the fetched page. A sweep reporting `"ok"`
  while doing nothing cannot produce it — which is precisely how the dead sweep
  hid, since it reported `"failed"` into a status file nobody diffed.
- **The freshness loop closes on a real clock**, unassisted. Step 8 is the
  URL-tail behaviour W-82 exists for: content changed under fux, and fux noticed
  within one declared interval with no human command.
- **Nothing resident survives the stop** — ADR-MAINTENANCE veto condition 6:
  the pid is reaped, the status file records `stopped`, and the write lock is
  free rather than held by a corpse.
- **Nothing was installed outside the repository**, as `start` claims.

## What it does NOT establish

- ⚠ **Not the public internet.** Localhost has no proxy, no TLS handshake, no
  SSO redirect, no rate limit and no DNS. The rate-limit path
  (`is_rate_limited(exc)`) was never exercised.
- ⚠ **One URL, one fetcher, one sweep interval.** `max_parallel` was set to 2
  and never had two URLs to run against.
- ⚠ **macOS only.** The detached-process mechanics are the part most likely to
  differ on Windows, and this says nothing about it.
- ⚠ **It does not answer the open decision** in `OPEN-WORK.md`: `_sweep` still
  returns a bare `"failed"` with no reason, and this run never produced one,
  because nothing failed.

## Authorship

Not required — a surface capture is exempt from the classification rule — and
recorded anyway, because the exemption is about *deltas*, not about who ran a
command.

| artifact | author | could reach |
|---|---|---|
| the scratch repo, the served page, the commands | Claude Code (Opus 5), 2026-08-27 | the repo; no evaluation queries, judgments or prior scores exist for this run |
| this report | the same session | its own transcript |

## Reproduce

```bash
mkdir -p /tmp/site && cd /tmp/site
cat > runbook.html <<'HTML'
<html><head><title>Oncall runbook</title></head><body>
<h1>Oncall runbook</h1><p>daemonsweepterm alpha the paging rotation</p></body></html>
HTML
python3 -m http.server 8731 &

mkdir -p /tmp/daemonrepo && cd /tmp/daemonrepo && git init -q
git config user.email t@t.test && git config user.name T
mkdir docs && printf -- '---\ntitle: local\n---\n# local\n\nlocal body\n' > docs/local.md
fux setup
echo docs >> .fux/sources/dirs
printf 'http://127.0.0.1:8731/runbook.html  fetch=http meta=plain\n' >> .fux/sources/urls
# add `sweep_minutes = 1` under the EXISTING [sources.url] table -- a second
# `[sources.url]` header is a TOML duplicate-table error, which is how this run
# first failed.
fux ingest
fux find daemonsweepterm --json     # {"results": []}
fux daemon start
sleep 5 && fux daemon status --json # {"last": {"outcome": "ok"}, ...}
fux find daemonsweepterm --json     # 1 result
fux daemon stop
```
