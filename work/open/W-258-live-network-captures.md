---
type: Handoff
name: W-258
description: "One hands-on session on Arpit's machine for the three captures only a real network and his credentials can produce: B-124 live (a journalled answer whose source then disappears), B-102 (a real 429 against a real host), B-101 (CDP `MAX_PARALLEL` in signed-in Chrome against session-gated sources). Checklist, instruments and bars written so the session is twenty minutes of typing, not design. Filed 2026-10-04 (W-251 §3 #24)."
item: W-258
filed: 2026-10-04
ball: arpit
---

# W-258 — the live-network captures

**Model: NONE — Arpit's hands.** The three captures need egress, a signed-in
Chrome and his credentials; an agent writes the harness and reads the result,
and does neither of those. Filed 2026-10-04 by delegation
([W-251](W-251-backlog-audit-rulings.md) §3 #24). The loopback halves of B-102
and B-124 and the Windows daemon e2e (B-103) are **agent** work and live in
[W-256](W-256-no-key-measurements.md).

**Order, by cost to him:** B-124 live (≈ 20 min, no credentials) → B-102 (a
public rate-limiting host) → B-101 (Chrome signed in; the long one).

## 1 · B-124 live — `as-ingested` on a source that disappears

- **Record:** SR-ACQUIRED Consequences — the share is computed *"over
  journalled answers … a repo that has never journalled reports unknown"*; veto:
  `as-ingested` *"exceed a quarter of verified citations on a corpus whose
  sources are all reachable"*; the check is `fux doctor --json`'s freshness
  block.
- **Needs:** a `url:` corpus of real, reachable sources with `keep=true`
  (the default); `fux answer --journal` run N ≥ 20 times; then one source made
  unreachable (a page he controls taken down, or a URL to a host that is
  offline) and `answer` run again.
- **Bar:** `as-ingested` share **< `AS_INGESTED_VETO_SHARE`** (¼) while every
  source is reachable; the taken-down document reports `as-ingested` with
  `match=True` against the acquired bytes; `doctor` names it.
- **Files:** the journal is `.fux/runtime/` (gitignored, L9); the run's report
  copies the freshness block and the doctor row, never the journal.

## 2 · B-102 — a real rate limit

- **Record:** SR-MAINTENANCE 9c-i — *"The network was `127.0.0.1`. No proxy, no
  TLS, no SSO, no rate limit, no DNS — so the rate-limit path was never
  exercised."*
- **Needs:** `fux daemon start` on a repo whose URL list has > 60 lines against
  an unauthenticated GitHub API endpoint (its 60/h limit returns 429), or any
  public host known to rate-limit; the shipped `http.py`'s `is_rate_limited`.
- **Bar:** `url-state.json` shows `rate_limited[host] > 0`; the retries and the
  doubling back-off are visible in the daemon log; the sweep **completes with no
  wrong-body document indexed** (a 429 page never becomes a document);
  `fux doctor` names the host. The *letter vs spirit* trap W-245 records
  (httpbin's always-429 endpoint) is why the host must be real.

## 3 · B-101 — CDP `MAX_PARALLEL` against session-gated sources

- **Record:** SR-CDP-FETCHER 7c — *"It does not justify a number. Every page
  was loopback HTML with no auth, no redirect, no CDN hop … `MAX_PARALLEL`
  stays `1`."* 7b: the lever is `[sources.url.config] fetcher_max_parallel`.
- **Needs:** Chrome signed in, CDP enabled, the consumer copy of `cdp.py`;
  **≥ 12 real session-gated URLs** (SSO intranet, a paywalled site he has
  access to, pages behind redirects); the instrument is
  `work/regression/2026-09-02-cdp-parallel/evidence/harness-live.py` at
  parallel 1 / 2 / 4 / 6.
- **Bar:** at every arm, n/n pages return **their own** content (no
  cross-tab bleed) **and** `validate()`'s ETag matches per URL; no tab leaked
  after the run. The outcome is a **consumer-config number** for 7b's key; the
  template's `1` does not move unless 7c is amended with the capture.

## Definition of done

1. 🔴 Arpit runs the three (or any subset) and drops the raw outputs into
   `work/regression/2026-MM-DD-live-captures/evidence/`.
2. An agent writes PRE-REGISTRATION *before* reading the outputs (the bars
   above, frozen), then the report and VERDICT; every number `informed`
   (his machine is the sample).
3. Record sentences rewritten and restamped on the numbers: SR-ACQUIRED
   Consequences (B-124), SR-MAINTENANCE 9c-i (B-102), SR-CDP-FETCHER 7c
   (B-101). `BACKLOG.md`: B-101 gone (promoted here); B-102/B-124 rows gone
   when both halves (this and W-256) are filed.
4. A WORKLOG entry.

## Out of scope

- B-093 (ARC vs LRU on a real trace) — it waits on a real usage journal, which
  is W-251 §4 #14's *not now*; it stays in the backlog.
- Changing any template default.

## Hazards

- ⚠ Never on `fux-playground` as a measurement surface (L9) — a scratch repo on
  his machine is fine; the *environment* rule is about what is measured where.
- ⚠ The journal and `url-state.json` are gitignored by design (L9); the report
  quotes shares and host names, never a query.
