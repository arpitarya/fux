---
type: Report
description: "W-256 section 4, lab-side loopback halves - B-102 and B-124 on 127.0.0.1. B-102: 14 of 14 observations hold on the third attempt (the first two were script defects, filed). B-124: 13 of 13 hold at the first attempt. B-103 (Windows daemon e2e) excluded, not measured."
run: 2026-10-04-loopback-network
item: W-256
classification: informed
filed: 2026-10-04
---

# Report: the loopback halves

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`a935d511`. **Script:** `tools/quality-controls/loopback_network.py`. Everything
ran on 127.0.0.1 in temporary repositories, the shipped `.fux/fetchers/http.py`,
real `fux` verbs as subprocesses of this tree. Python 3.14, macOS, 10 cores.
Load average before each scenario: **2.36-2.79** (under half the cores, so
the timing bar was not under pressure). Engine values read from
`constants.toml`: `rate_limit_retries = 3`, `rate_limit_backoff_s = 1.0`,
`as_ingested_veto_share = 0.25`. No real host was contacted.

## B-102 loopback - 429: 14 of 14 hold (final attempt)

| id | observed |
|---|---|
| R1 | requests: flaky-1 3, flaky-2 3, always 4, ok 1 |
| R2 | `fux ingest` exit 0; flaky-1, flaky-2, ok indexed; always not indexed (by record id) |
| R3 | backoff gaps on the server's own clock: flaky 1.01 s, 2.0-2.01 s; always 1.01, 2.01, 4.01 s - inside `[b*2^i, +1.5 s]` |
| R4 | `url-state.json` `rate_limited["127.0.0.1:<port>"] == 8` (2+2+4) |
| R5 | doctor's `url sources` row contains `rate-limited by 127.0.0.1:<port> x8` |

The engine also printed `127.0.0.1:<port> rate-limited this run 8 times; fux
backed off and retried ... fux will not change it for you`.

### Deviations (script only; no bar moved)

Three attempts, **all filed** under `evidence/`:

1. `ratelimit-attempt-1-script-defects` - 12 of 14. Two defects in the
   *fixture and check*, neither an engine fact: (a) the documents were small
   enough (< 1024 bytes, an extensionless path) to trip the shipped
   `suspiciously-small-document` refusal in `refusals.toml`, so the `ok` control
   was refused for that reason and not indexed; (b) "in index" was a substring
   test over the shard text. Fixed: documents enlarged (80 to 200 terms), the
   check reads record `id`s.
2. `ratelimit-attempt-2-inverted-negative-check` - 13 of 14; the one failure
   (`R2-always`) was an inverted boolean in the script's negative check (the
   index ids, in `raw.json`, show `/always` was not indexed). Fixed.
3. `ratelimit` - the final attempt, 14 of 14. R1, R3, R4 and R5 held on all three
   attempts with identical values, so the fixes did not change those facts.

The `R2-always` row's `observed` text still reads `/always in index` - a label,
not a value; `ok` carries the result and `raw.json` carries `indexed_ids`.

## B-124 loopback - as-ingested: 13 of 13 hold (first attempt)

8 documents, `keep=true`, `ttl 0`; 16 answers up, 4 down, 4 more down; each
answer produced 3 journalled verdicts.

| stage | cumulative verdicts | doctor's `freshness` | veto row |
|---|---|---|---|
| up | `current` 48 | equal | silent |
| down-1 | `current` 48, `as-ingested` 12 (20 %) | equal | silent |
| down-2 | `current` 48, `as-ingested` 24 (33 %) | equal | **warns** (`reopen condition`) |

A1: 10 files retained in `.fux/acquired/`. A2: every verdict while up was
`current`. A3: every verdict while down was `as-ingested`, none `unverified` or
`stale`, each with `fetched_sha == indexed_sha` (match = true). A4/A5/A5-fires
as in the table.

## B-103 - excluded

Not measured, as pre-registered section 0 (needs a `windows-latest` run and a
push). SR-MAINTENANCE 9c-i is unchanged.

Verdicts and reading: [`VERDICT.md`](VERDICT.md), [`ANALYSIS.md`](ANALYSIS.md).

## Headroom

Not a paired run: behavioural observations with a stated value each, no arms, no score. Per-observation expected and observed values are in `evidence/*/observations.jsonl`.

## Authorship

No question set or key was used. The engine, fetcher and doctor are earlier sessions' and Arpit's; the script, pre-registration and report are Claude Code, one session. `informed`: agreement shows the mechanism is wired, not that the design is right.
