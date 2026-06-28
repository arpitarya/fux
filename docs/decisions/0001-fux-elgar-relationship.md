---
id: adr-fux-elgar-relationship
type: adr
status: active
date: 2026-06-20
decided_by: Arpit (chair)
method: decision-council
---

# ADR 0001 — How fux and elgar relate (custody, not hierarchy)

## Decision
fux and elgar are **aware of each other through a shared contract** (the `elgar://plan/<id>`
link scheme + the shared markdown/frontmatter dialect), and **fux may own the routing
*decision*** (which store a doc belongs in) — **but fux must NEVER retain or derive the
confidential payload.** fux keeps only the `elgar://` link; the money bytes go agent→elgar
directly and never pass through fux's process.

- ❌ Rejected: fux as parent that internally connects to / absorbs elgar as a **data custodian** (Option C).
- ✅ Adopted: constrained front-door — fux decides + link-keeps (Option B), with siblings + Anton-orchestrates (Option A) as the zero-risk floor.
- One-liner: **fux is the front desk that names the vault and writes down the locker number — never the warehouse that holds the gold on the way through.**

## Why
The value of unification (one door, enforced routing) is fully capturable **without** fux
ever touching money bytes. The risk (a money figure leaking into the public tree via a fux
log / temp / derived `out/` / crash dump) **only exists** the moment fux holds or derives
them. Upside survives the safe version; downside is exclusive to the unsafe one → take the
safe version. The real variable is **custody**, not parent-vs-sibling.

## Council
Seats: first-principles-socratic, agentic-builder, steelman (for Option C), devils-advocate, pre-mortem.
Crux surfaced: *does the front-door ever RETAIN/DERIVE the confidential payload, or only FORWARD a pointer?* — which dissolved the parent-vs-sibling framing into a custody question.

## Strongest surviving dissent
A forwarding classifier still holds the bytes transiently in memory en route — one crash dump
leaks. The most conservative position: fux is **decider + link-keeper only** — the agent/Anton
writes to elgar, fux is handed the resulting `elgar://` id and records it, never seeing the
payload. For a money path, that extra step is probably worth it.

## What would reverse this
A concrete need for fux to **transform** confidential content (generate a rule *derived from*
a money doc, not just route it). Then fux must touch the bytes under tightly-bounded custody
(in-memory only, no logging, no `out/`, hard-tested). Absent that need, keep fux out of the bytes.
