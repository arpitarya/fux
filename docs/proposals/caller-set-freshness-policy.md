---
type: Proposal
title: Caller-set freshness policy — staleness tolerance as a per-query parameter
description: Make the refer plane's index-vs-live-fetch decision a caller-supplied bound (max_age + timeout) rather than a system-wide policy. Parallel ships exactly this shape; it costs Fux nothing architecturally and turns an implicit rule into a contract.
status: proposed
timestamp: 2026-08-10T00:00:00Z
tags: [refer-plane, m4, api-surface]
---

# Caller-set freshness policy

**The idea.** The refer plane already decides, per citation, whether to trust
the index or fetch the source. **Make that decision a parameter the caller
supplies, not a policy the engine owns.**

```
fetch_policy: { max_age_seconds: <int>, timeout_seconds: <int> }
```

Below the age bound, answer from the index. Above it, fetch live — bounded by
`timeout_seconds`, so a slow or unreachable source degrades into an honest
stale-with-disclosure answer instead of an unbounded hang.

## Why it is worth filing

**Parallel ships this exact shape**, and it is the clearest architectural
signal in their whole API surface: the committed index is explicitly a **cache
tier with a TTL**, and the caller declares staleness tolerance per request.
Evidence and context in
[`agent-search-landscape.md`](agent-search-landscape.md) §1.

Two distinct callers want two different answers from the same index:

| caller | wants |
|---|---|
| an agent mid-loop, 10+ retrievals | `max_age` generous, `timeout` tight — latency dominates |
| a human asking "is this runbook still true" | `max_age` ~0 — a live fetch is the whole point |
| CI / a deterministic replay | `max_age` = ∞ — **never** fetch; the index at that commit *is* the answer |

Today all three get whatever the engine's fixed policy says. That third row is
the one that matters most: an explicit *never-fetch* bound is what makes a
replayed answer reproducible.

## Sketch

- Config default in `fux.toml` under the refer section; per-query override on
  `fux ask` / `fux answer` (`--max-age`, `--fetch-timeout`) and on the library
  call.

- `max_age_seconds = 0` forces live fetch; a sentinel (`never`) forbids it
  outright. **The sentinel is the deterministic-replay mode** and should be
  what CI and `--audit` bundles use.

- Age is measured against the ledger's recorded `sha@index` provenance, **not
  wall clock at query time** — the no-wall-clock law
  ([`../../CLAUDE.md`](../../CLAUDE.md)) still binds. The comparison input is a
  source mtime / `SOURCE_DATE_EPOCH`-derived stamp, so the same query at the
  same commit with the same policy is byte-identical.

- The answer carries which branch it took per citation: `from-index@sha` vs
  `fetched@sha`. This is already close to what the refer plane must emit; the
  proposal makes it explicit and testable.

## Why not now

**M4 has not been built** ([`../OPEN-WORK.md`](../OPEN-WORK.md) W-24). Adding a
knob to a plane that does not exist is exactly the "build the fun part first"
failure the plan exists to avoid.

It also carries one real design question worth deciding deliberately: **does a
fetch that times out fail the query or degrade it?** Degrading is almost
certainly right for agents and almost certainly wrong for `--audit`, which
means the answer is "policy, per caller" — and that is the same argument as the
proposal itself, one level down.

## Graduation trigger

**When W-24 (M4, the refer plane) starts.** Fold into the M4 handoff as a
first-class part of the refer API rather than a later addition — retrofitting a
freshness contract onto shipped call sites is the expensive version.

Its DoD rides on **R4** (cold k=10 ≤ 3 s / warm ≤ 300 ms): the same bench, run
at three `max_age` settings, should show the policy actually moving the
index-vs-fetch mix. If it does not, the knob is decoration and should be
dropped.

## Risks to hold

- **Determinism.** A caller-set knob is an input; the same inputs must still
  produce the same output. That is fine — but it means the policy must be
  **recorded in the answer bundle**, or a replay silently uses a different one.
  Non-negotiable for `--audit`
  ([`audit-evidence-trail.md`](audit-evidence-trail.md)).

- **Offline-by-default.** `max_age_seconds` low enough to force a fetch must
  still respect the fence — offline mode reports honestly that it *could not*
  meet the requested freshness, never silently serves stale bytes as fresh.

- **Knob sprawl.** Two integers is the whole surface. If it grows a third, that
  is the signal the policy belongs in config, not in the query.

## References

[`agent-search-landscape.md`](agent-search-landscape.md) (the evidence base) ·
Parallel `fetch_policy` — [Search best practices](https://docs.parallel.ai/search/best-practices) ·
[Search API reference](https://docs.parallel.ai/api-reference/search-beta/search) ·
Perplexity's ML-predicted re-index scheduling, the same problem solved
engine-side — [architecting an AI-first search API](https://research.perplexity.ai/articles/architecting-and-evaluating-an-ai-first-search-api) ·
[`../compare/cache-policy.compare.md`](../compare/cache-policy.compare.md)
(ARC — the layer below this one) ·
[`../PLAN.md`](../PLAN.md) §M4 · [`../paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md) §refer
