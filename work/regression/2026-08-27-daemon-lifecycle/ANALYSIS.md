---
type: Analysis
title: What the daemon capture changes, and the one thing it deliberately does not
description: The sweep is proven to reach ingest and close the freshness loop on a real clock; W-82 ruling 3's hold is narrowed to the public-network clause alone.
timestamp: 2026-08-27T15:13:00Z
---

# Analysis — the daemon lifecycle capture

## 1 · The dead sweep is dead, and the proof is a positive control

**The defect:** `_sweep` did `from ..ingest import run as ingest_run`, which
binds the re-exported **function**, so `ingest_run.run(...)` raised
`AttributeError` into the broad handler that keeps a daemon alive. Every sweep,
in every repository, returned `"failed"` and indexed nothing.

**Why the fix needed this run.** The unit gate
(`tests/maintain/test_daemon_sweep_reaches_ingest.py`) monkeypatches — and the
test that should have caught the original bug *patched the same wrong object*
and failed on its own `monkeypatch` line. A mock cannot distinguish "the sweep
called ingest" from "the sweep called the mock." **Step 6 of the report can**:
`daemonsweepterm` exists only in the fetched page, was absent from the index
before `daemon start`, and was present after.

**Repro:** `work/regression/2026-08-27-daemon-lifecycle/report.md` §Reproduce.

## 2 · W-82 ruling 3's hold is NARROWED, not lifted

Hands item 6 asked for *"a detached process, a real clock and a real network."*

| clause | status |
|---|---|
| a detached process | ✅ pid 10514, reaped on `stop`, `ps` confirms |
| a real clock | ✅ page edited `15:11:21Z`, indexed by `15:12:04Z` — one declared interval, unassisted |
| a real network | ⚠ **localhost only.** No proxy, no TLS, no SSO, no rate limit, no DNS |

**The recommendation is that ruling 3 stays held**, and this is a judgement a
session should not make alone: the third clause is the one that carries the
enterprise failure modes, and narrow-by-default is precisely the change whose
blast radius is *URLs that stop being swept*. **Arpit's call.** What has changed
is the size of what is being asked for — a single run against one real external
URL, not a rebuild of confidence in the daemon.

## 3 · Two specific improvements this run surfaced

1. **`fux setup` writes a `[sources.url]` table, and the obvious way to add
   `sweep_minutes` breaks the file.** Appending

   ```toml
   [sources.url]
   sweep_minutes = 1
   ```

   to a `fux.toml` that already has that table is a TOML **duplicate-table
   error**, and the message is `Cannot declare ('sources', 'url') twice (at line
   68, column 13)` — accurate, and it names the *appended* line rather than the
   original. This is the first thing anyone enabling the daemon will do.
   **Repro:** `printf '\n[sources.url]\nsweep_minutes = 1\n' >> fux.toml && fux ingest`.
   ⚠ **Not filed as an item and not fixed**: whether the specimen should carry a
   commented `sweep_minutes` line (as the tunables specimen now carries live
   lines) is an [ADR-CONFIG](../../../docs/adr/0014_config.md) question, and
   `fux setup` is write-if-missing so it would not reach an existing repo
   anyway — the same freeze ADR-DOTFUX decision 6 already names.

2. **`fux find` on a fresh daemon-written index prints the no-accelerator
   notice** — `fux: no fresh accelerator - this query used the reference scan.`
   The sweep runs `ingest`, not `build`, so the derived plane goes stale on
   every sweep and every query after one pays the reference scan.
   **Unresolved, and stated as unresolved**: it may be correct (the differential
   law says results are identical either way, and `build` is not free), or the
   sweep may owe a `build`. Deciding it needs a measurement of sweep cost against
   query cost at 10 000 documents, which is an item nobody has filed.

## 4 · What was NOT diagnosed

- The daemon's status still carries **no reason** on `"failed"`. Nothing failed
  in this run, so the run says nothing about it; it remains the open decision in
  `OPEN-WORK.md` §Blocked on Arpit.
- Windows. The detached-process mechanics are the part most likely to differ and
  this is a macOS run.
