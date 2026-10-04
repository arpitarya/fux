---
type: Pre-registration
name: PRE-REG-LOOPBACK
description: "W-256 section 4, lab-side loopback halves - frozen before any observation: B-102 (a loopback server emitting 429 exercises is_rate_limited, the bounded doubling backoff, url-state.json rate_limited[host] and the doctor row) and B-124 (a keep=true url: corpus journalled with the server up, then down; the as-ingested share against doctor's quarter veto; a taken-down document reports as-ingested with the retained bytes matching the index). B-103, the Windows daemon e2e, is excluded and the reason is stated."
run: 2026-10-04-loopback-network
item: W-256
frozen: 2026-10-04
---

# W-256 section 4 - the loopback halves of the network measurements

**Frozen 2026-10-04, before any observation exists.** The run directory holds
this file and nothing else until the measurement lands. Two behavioural
scenarios, every claim a yes/no stated below; no ranking, no score, no key.
They are **`informed`** (section 7) and that costs nothing, since the endpoint
is *did the engine do what its record says*, not *is it good*.

## 0 - What is excluded, and why

**B-103 (the Windows daemon e2e: start -> sweep -> stop on `windows-latest`,
with the 2026-08-27 positive control) is NOT measured here, and not by this
session.** It needs a `windows-latest` CI run, which needs a push, which this
session cannot make: an unpushed local commit on `main` reds CI until W-240
lands. Windows CI minutes are also the W-243 budget, and the item says the e2e
is to run *once, not per push*. So B-103 stays open on W-256, **SR-MAINTENANCE
9c-i's *"macOS only"* sentence is not rewritten by this run**, and the run's
VERDICT says *B-103 excluded*, never *B-103 passed*. The real-network halves of
B-102 and B-124 are [W-258](../../open/W-258-live-network-captures.md)'s;
loopback shows the mechanism is wired, not that a real host behaves.

## 1 - What loopback can and cannot show

Everything runs on `127.0.0.1` in a temporary repository
(`tools/quality-controls/loopback_network.py`, stdlib `http.server`, the shipped
`.fux/fetchers/http.py`, the real `fux` verbs as subprocesses of this tree).
No real host is contacted; the lab and the playground are not touched
([L9](../../../records/0011_LAW-9-use-record.md), SR-WORK-OPEN-QUEUE rule 53).
Loopback proves the **mechanism is connected end to end** - the fetcher's flag,
the engine's retry, the state file, the doctor row; it cannot show how a real
rate-limiting host behaves, how long a real outage lasts, or what share of a
real corpus's citations are retained. The records' own reopen conditions are
about real corpora and **are not ruled by this run**.

## 2 - B-102 loopback: a 429 on loopback

**Claims under test** ([SR-FETCHER](../../../records/0117_fetcher.md) decision
13, W-82 ruling 12; `src/fux/ingest/urlsrc.py`): the fetcher *declares* a
rate-limit refusal through `is_rate_limited`; fux retries a bounded number of
times with doubling backoff, counts refusals **by host**, reports and persists
them for `fux doctor`, and never lowers `max_parallel`.

**Setup.** Four URLs on one loopback port, `--http --decoder prose --keep
--ttl 0`, listed with `fux add --no-fetch` (no request is made by the adds),
then one networked `fux ingest`:

| path | server behaviour |
|---|---|
| `flaky-1`, `flaky-2` | `429` on the first **2** requests, `200` after |
| `always` | `429` on every request |
| `ok` | `200` (control) |

`RETRIES` and `BACKOFF` are **read from `src/fux/constants.toml [fetch]`**
(`rate_limit_retries`, `rate_limit_backoff_s`), not restated; at freeze they
are 3 and 1.0 s. The scenario's own shape (2 refusals, the four paths, a 1.5 s
timing slack) is fixed in the script and may not change after a number exists.

**Observations, each pre-registered (all must hold):**

| id | what must be observed |
|---|---|
| R1 | server-side request counts: each `flaky-*` path **3** (= refusals + 1); `always` **RETRIES + 1 = 4**; `ok` **1** |
| R2 | `fux ingest` exits **0** (a refused URL does not fail the run - per-URL isolation); `flaky-1`, `flaky-2` and `ok` are **in the committed index**; `always` is **not** |
| R3 | the doubling backoff, measured on the **server's own timestamps**: for each path the gap before retry *i* lies in `[BACKOFF x 2^i, BACKOFF x 2^i + 1.5 s]` (1 s, 2 s for a `flaky-*`; 1, 2, 4 s for `always`) and the number of gaps is exactly the number of retries |
| R4 | `.fux/runtime/url-state.json` `rate_limited["127.0.0.1:<port>"]` equals **2 + 2 + 4 = 8** - refusals counted (SR-FETCHER 13: *refusals, not retries*, by host), persisted |
| R5 | `fux doctor --json`'s `url sources` row contains exactly `rate-limited by 127.0.0.1:<port> x8` |

**What a failure means.** R1 off by one = the retry bound or the counting is
wrong; R3 outside the window = the backoff is not the documented doubling (or a
loaded machine - the run records load and re-takes once, both attempts filed,
before any claim); R4 absent with R1 true = the state file is not wired to the
retry path, which is the item's actual hazard; R5 absent with R4 true = doctor
does not read what the engine wrote. None of these is a threshold to loosen.

## 3 - B-124 loopback: `as-ingested` on a retained corpus

**Claims under test** ([SR-URL-FRESHNESS](../../../records/0147_url-freshness.md),
[SR-ACQUIRED](../../../records/0145_acquired-plane.md),
[SR-PROVENANCE](../../../records/0142_provenance.md) decision 10):
with `keep=true` the fetched bytes are retained in `.fux/acquired/`; an answer
whose source is unreachable verifies against them and reports `as-ingested`;
`--journal` writes the verdicts locally (L9, gitignored); `fux doctor --json`
reports the `as-ingested` count against the total of verified citations and
warns when the share exceeds **a quarter** (`constants.toml [doctor]
as_ingested_veto_share`, read, not restated; 0.25 at freeze).

**Setup.** **8** documents (`doc0`..`doc7`) on one loopback port, `keep=true`,
`ttl 0` (so every answer fetches live while the server is up - no `cached`
verdict can intervene), one networked `fux ingest`. Then, with
`fux answer --journal --json "<docN>-term7 runbook"` (one query aimed at each
document in rotation):

| stage | server | answers | purpose |
|---|---|---:|---|
| `up` | up | **16** | the control: reachable sources |
| `down-1` | **taken down** | **4** | a share designed to sit *under* the quarter |
| `down-2` | down | **4** | a share designed to sit *over* it |

(The designed shares assume a constant number of verdicts per answer; the
**checks below are computed from the journal as observed**, not from the design,
and A5-fires is the guard that the design worked.)

**Observations, each pre-registered (all must hold):**

| id | what must be observed |
|---|---|
| A1 | after the one ingest, `.fux/acquired/` holds retained bytes for the corpus (>= 8 files) |
| A2 | stage `up`: **every** new journalled verdict is `current` - none is `as-ingested` while the source is reachable |
| A3 | stages `down-1` and `down-2`: **every** new verdict is `as-ingested` (never `unverified`, never `stale`), **and** each carries `fetched_sha == indexed_sha` - the taken-down document reports `as-ingested` **with `match=True`** (`Verdict.current`), i.e. the retained bytes agree with the index (the mismatched outcome - an index defect - is the thing this excludes) |
| A4 | at the end of every stage `fux doctor --json`'s `freshness` block **equals** an independent count of the `verdicts` in `.fux/runtime/provenance.jsonl`, label by label |
| A5 | at the end of every stage doctor's `freshness verdicts` row warns (contains `reopen condition`) **if and only if** `as-ingested / total > as_ingested_veto_share`, where the share is computed from the observed journal |
| A5-fires | the veto fires **at least once, and only in a `down` stage** - the check that the share genuinely crossed the quarter, so A5's "not before" is not satisfied vacuously |

**L9, checked.** Everything the scenario writes is `.fux/runtime/` in a
temporary repository that is deleted at the end; nothing committed to this
repository carries a query, an answer or a journal line - only the observation
rows (booleans, counts, shas, labels) and the request log are filed.

## 4 - The record sentences these decide

At filing, **and not before**: SR-ACQUIRED Consequences' *"never had data to run
against"* (the item's wording; the run's report quotes where it actually reads
and says if the sentence has a different home or form), if A1-A5 hold on
loopback, is restated to say the mechanism was **exercised on loopback and the
real-network half is W-258's** - never to say the veto was *ruled on a real
corpus*. A failed observation files a defect first. B-103 changes nothing in
SR-MAINTENANCE 9c-i (section 0).

## 5 - Validity conditions (a failure of any is a VOID run)

- The server binds `127.0.0.1` only; any request recorded from another peer, or
  any DNS lookup of a non-loopback name by the run, voids it.
- The `ratelimit` scenario's request log must start empty at the ingest (the adds
  use `--no-fetch`): a request before the ingest voids it.
- The machine's load average is recorded before each scenario; R3 windows are
  not widened for it. A run whose R3 alone fails under a load above half the
  core count is re-taken once and **both attempts are filed**.
- Python, the engine commit and `src/fux/ingest/urlsrc.py`'s and
  `src/fux/doctor.py`'s sha at run time are recorded; a change to either between
  freeze and run voids the run.

## 6 - The endpoint, and what a result means

**PASS (per scenario)** - every observation of that scenario holds.
**FAIL** - any observation fails for a reason that is not a section 5
condition; the failed id names the mechanism, and it is filed as a defect first,
**never a threshold moved**. A result that is neither ([SR-RS](../../../records/0133_predictions.md)
decision 10b) goes to Arpit. The scenarios are ruled separately: B-102 loopback
can pass while B-124 loopback fails. B-103 carries no verdict (section 0).

## 7 - Classification, authorship, what this cannot show

**`informed`**, permanently - the engine, the fetcher, the scripts and this
document are one model family's, so agreement shows the mechanism is connected,
not that the design is right. The endpoint is behavioural, so this costs nothing.

| artifact | author | could reach |
|---|---|---|
| the engine, fetcher, doctor | earlier sessions and Arpit | - |
| the script and this document | Claude Code, one session family | the code and the records; **no key is read** |

It cannot show: any real host's behaviour, `Retry-After` handling (the engine
deliberately never reads it), real outage durations, real citation mixes, TLS,
redirects, or Windows. **It does not make the real-network halves unnecessary**;
it makes them cheaper to read, because a loopback pass removes "the mechanism
is not wired" from the list of reasons a real run could surprise.

## 8 - What would make this pre-registration wrong

- `fux add --no-fetch` fetching anyway (section 5's empty-log condition).
- The 429 being surfaced by a path other than the shipped `http.py` flag
  (R4 absent with R1 true is that, and is reported as such).
- `provenance.jsonl`'s `verdicts` shape differing from the one `doctor.py`
  reads - A4 would then compare two readings of one file and the run says so.
