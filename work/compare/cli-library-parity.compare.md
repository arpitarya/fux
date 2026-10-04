---
type: Compare Doc
title: "CLI ↔ library parity — four places the two surfaces disagree and nobody decided"
description: "Backlog B-146, B-147, B-148, B-151 as one fork: `under` semantics, the graph verbs' `--json` shape, the changed-since line, and the order of `confidence`/`fused`. Options: freeze the divergence, converge on the library, or converge on the CLI. Recommended: converge on the library inside the already-breaking 3.0."
status: proposed (W-251 §3 #4 — Arpit's ruling)
timestamp: 2026-10-03T00:00:00Z
filed: 2026-10-03
---

# CLI ↔ library parity

> **Verdict: PROPOSED — converge on the library surface, in 3.0.** Component-boundary
> `under` on both surfaces (and in `Weighting.priority_for`); CLI `--json` for
> `explain`/`graph`/`path` adopts the library/Node payload; `changed_since`
> becomes a `--json` field; `confidence` precedes `fused` in both verbs.
> **Confidence: high on three, medium on the `--json` shape** (a documented
> contract moves). **Reopen-trigger:** a consumer reports scripting the pre-3.0
> `--json` shape of a graph verb, or `fux.api` is unfrozen (SR-API d1).

**Model: Sonnet** for the build — every change is parity-testable by the
existing differential arm.

## Context

[SR-API](../../records/0154_api.md) froze the library surface (d1) and then
recorded, honestly, four places where the CLI and the library say different
things for the same question. Each was *"stated rather than fixed, because it is
a ruling"* (d6) — and the ruling was never asked for as one question. The
backlog carried them as four rows for three weeks.

| row | the divergence | where |
|---|---|---|
| B-146 | `find(under=…)` applies a **component boundary** in the library (`docs/a` does not match `docs/ab.md`) and a **bare prefix** on the CLI | SR-API d6; [SR-FIND](../../records/0104_find.md) d7 — the CLI matches *"the same way `Weighting.priority_for` does … inventing a component boundary here would disagree with the resolver"*. **So the resolver must move with it**, or SR-FIND d7's argument stands and O2 is wrong |
| B-147 | `explain`, `graph`, `path` return **different payloads** on the library than on either CLI; Node mirrors the **library** | SR-API d6 |
| B-148 | the changed-since line is **stderr** on the CLI; promoting it to a `--json` field *"would be additive but would move a documented surface"* | [SR-ANSWER](../../records/0105_answer.md) d10 |
| B-151 | `find` emits `fused` before `confidence`; `ask` the reverse — *"not a decision anybody took"* | SR-FIND Consequences |

3.0 is already a breaking release by ruling (`fetch=` mandatory, `fux update`
deleted, Python 3.12 / Node 22 floors, L12's hard errors). A parity change that
would need a deprecation cycle in 3.1 is free in 3.0.

## Options

- **O1 — freeze the divergence.** Write each difference into SR-CLI as a
  documented, deliberate asymmetry. Zero code. Cost: two readers of one index
  answering `under` differently forever, and Node agreeing with one of them.
- **O2 — converge on the library** (recommended). The CLI adopts the library's
  semantics and shapes. Node already mirrors the library and the differential
  arm already tests that pair, so the CLI is the odd one out and the only thing
  that moves.
- **O3 — converge on the CLI.** The library (frozen, d1) and Node both change
  to match the CLI's prefix match and payloads. Two surfaces move, one of them
  frozen, to preserve the shape nobody chose.

## Matrix

| | O1 freeze | O2 → library | O3 → CLI |
|---|---|---|---|
| surfaces that change | 0 | 1 (CLI) | 2 (library, Node) |
| breaks SR-API d1's freeze | no | no | **yes** |
| differential arm covers the result | n/a | yes (CLI vs Node added) | yes |
| `--under docs/a` matching `docs/ab.md` | stays | fixed | stays |
| documented CLI `--json` contract moves | no | **yes** (graph verbs; key order; `+changed_since`) | no |
| cost to a scripted consumer | none | one 3.0 line in CHANGELOG | none |

## Consequences of O2

- `Weighting.priority_for` adopts the component boundary too, so `[priority]`
  keys spelled without a trailing slash stop prefix-matching siblings — the
  same fix, the same release.
- `--json` key order becomes **documented** in SR-CLI (`confidence`, then
  `fused`) and tested, rather than incidental.
- `changed_since` as a field is additive; stderr keeps the line for prose mode.
- The differential arm gains the CLI as a third column for the three graph
  verbs; `tools/differential/node_arm.py` already parses the library shape.
- [W-247](../open/W-247-api-renderer-split.md) must land **first**: once the CLI
  renders what `fux.api` builds, B-147 and B-151 become one-line changes, and
  byte-equality there is what keeps the two changes separable.

## References

- SR-API d1, d6, d7 · SR-FIND Consequences · SR-ANSWER d10 · SR-CLI (the
  `--json` contract) · `tools/differential/node_arm.py`.
- W-251 §3 #4 — the inbox line that carries this fork.

## Reopen-trigger

A consumer reports scripting the pre-3.0 `--json` shape of a graph verb; or
SR-API d1 is reopened and the library surface moves.
