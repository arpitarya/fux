---
type: Verdict
name: VERDICT-P3-SANITIZED-SHA-STABILITY
prediction: P3
pre_registration: work/open/W-87-what-good-means.md
verdict: PASS
description: "19/19 = 100 % against a frozen >= 80 % threshold. Fork 3 clears the gate; it is not thereby decided, and the interval the spec never named is the named limit on what this licenses."
timestamp: 2026-08-27T17:26:30Z
---

# P3 — PASS. Fork 3 clears its gate.

**Prediction:** W-87 P3 (= W-82 §3.0), the sanitized-sha stability measurement.
**Ruled against:** the frozen threshold table in
[`work/open/W-87-what-good-means.md`](../../open/W-87-what-good-means.md) §P3,
**unedited**.

## The ruling

**`PASS`. 19/19 = 100 %, against a frozen `≥ 80 %`.**

Per the frozen table: **fork 3 is *yes* — the fetcher contract may gain an
optional `validate`.** P4 is unblocked; it was gated on this number.

## What PASS licenses, and what it does not

**It licenses fork 3 being taken.** It does not take it. The frozen table says
the gate clears; **whether to spend a fifth function on the contract is still a
design call**, and ADR-FETCHER decision 3's argument against composition is
untouched by this number.

⚠ **It does not license a sweep-interval claim.** The spec says *"run `fux
update` twice"* and **names no interval**. These runs are **12 seconds** apart.

- At that interval the measurement is about **server-side determinism** — does a
  server return bytes that sanitize identically for an unchanged document? That
  is a real and non-trivial precondition for any validator, and **none of 19
  real pages failed it**, including a live status page.
- It is **not** a measurement of how often documents actually change between
  sweeps, which is the other half of what `validate` would be worth.
- **A later run at a realistic interval is a new measurement with a new
  pre-registration**, not a re-reading of this one.

## Why this is not a null result dressed up

A 100 % with no control is the M1 failure — a treatment that touched nothing,
reported as a null effect. **A control arm was run**: two known-volatile URLs
added, the pair repeated, and `https://en.wikipedia.org/wiki/Special:Random`
changed while the 19 documentation URLs did not. **The instrument detects
change.**

## Disclosures carried into the verdict

- **`informed`**, as the spec anticipated. No blind arm exists and none is
  pretended; nothing here is compared against a blind number.
- **The corpus was chosen by the session that ran it**, and corpus choice
  determines this number entirely. Volatile endpoints were kept out of the
  headline arm and put in the control arm; an all-archival corpus would have
  been the opposite thumb on the scale. Composition is in the report.
- ⚠ **ADR-RS decision 12's conflict is disclosed, not narrowed** — and this is
  the **fourth** writing of that disclosure, which **fires decision 12's own
  reopen trigger**. See [`ANALYSIS.md`](ANALYSIS.md) §3.
- **19 URLs on the public internet** is three orders of magnitude below the
  10 000-document design point and says nothing about a corporate wiki, where
  editable pages are the norm.
