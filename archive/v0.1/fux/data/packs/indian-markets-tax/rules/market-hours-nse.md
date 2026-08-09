---
id: market-hours-nse
domain: market-structure
type: regulatory
status: active
created: 2026-06-01
updated: 2026-06-01
aliases: [trading-hours, nse, bse, session-timings, ist]
keywords: [market, open, close, pre-open, holiday, IST]
---
**Rule (external):** NSE/BSE equity continuous trading runs **09:15–15:30 IST**
on business days, preceded by a pre-open session **09:00–09:15 IST**. Markets are
closed on declared exchange holidays (distinct from bank holidays).

**Source:** NSE/BSE published trading schedule. The holiday list changes yearly —
treat it as data to refresh, not a constant to hard-code.

**Applies to:** "is the market open right now?" checks, day-change/last-price
freshness logic, and any scheduling of fetches. Always compare in **IST**; a
naive server-local or UTC comparison will misjudge the session near the
boundaries and during DST shifts elsewhere.
