---
type: ADR
name: ADR-PORT-LIST
title: ADR-PORT-LIST (0015) — port, don't rewrite, and this is the complete list
description: "Named modules come forward from the archived engine, each with its tests, when its milestone needs them. Nothing else does, and the list is closed."
status: accepted
date: 2026-08-18
feature: the boundary between the archived engine and this one
owns: []
laws: [L1, L3]
timestamp: 2026-08-18T00:00:00Z
---

# ADR-PORT-LIST — port, don't rewrite, and this is the complete list

## §1 — For humans

The v0.19–0.26 engine is archived at [`archive/v0.26/`](../../archive/v0.26/),
runnable and reference-only. It contains working, tested code for problems this
build still has: a frontmatter parser, an analyzer, BM25F, a chunker.

Rewriting those from scratch would be waste. Copying the whole engine forward
would be worse — it is a *substrate* engine, and this one is index-and-refer.
Its architecture is the thing that was reset.

So: **a named list, and nothing else comes back.** Each module arrives with its
tests, and only when the milestone that needs it arrives. **The list being
closed is the point** — an open list is how a rewrite quietly becomes a port of
the thing you were trying to leave.

**Diagram — Mermaid and its ASCII twin. Update both, always, together.**

```mermaid
flowchart LR
    A["archive/v0.26/<br/>reference-only, never imported"] -->|"named module<br/>+ its tests"| N["the live engine"]
    A -.->|"everything else"| X["stays archived"]
    N --> M{"needed by<br/>this milestone?"}
    M -->|no| W["wait — porting early<br/>is porting speculatively"]
    M -->|yes| P["port it, with its tests"]
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
   archive/v0.26/          only NAMED modules, each with its tests
   reference-only,   -------------------------------------------->  the live engine
   never imported                                                        ^
        |                                                                |
        +-- everything else --> stays archived                    needed by THIS
                                                                  milestone? --no--> wait
   The list is closed. An open list is how a rewrite
   becomes a port of the thing you were leaving.
```

</details>

*No Examples or Charts section: this record governs provenance, not a
user-visible surface.*

---

## §2 — For agents

### Context

The second reset archived a working engine. Some of its code solves problems
that did not change with the architecture — analysing text, scoring BM25F,
parsing frontmatter — and that code is already tested and already correct
against recorded numbers.

Two failure modes sit either side of the decision. Rewrite everything and you
burn months re-earning tested behaviour, and lose the archived engine's recorded
numbers as a cross-check. Port freely and the substrate architecture comes back
a module at a time, which is exactly what the reset was for.

### Decision

**1. Port only from this list.** Anything not named here does not come forward;
reviving it needs its own record and Arpit's sign-off.

| module | used by | ported for |
|---|---|---|
| frontmatter parser | ingest, snapshot mode | the committed record |
| analyzer chain | ingest, query | the shared analyzer ([ADR-RANKING](0012_ranking.md)) |
| BM25F scoring math + exact-`df` discipline | the scorer | the scan, then the accelerator |
| PPR-lite + edge extraction | the graph lane | [ADR-GRAPH](0029_graph.md) |
| chunker (heading-aware) | passage re-score | [ADR-REFER](0030_refer-plane.md) |
| converters (fidelity tiers) | bytes → Markdown | [ADR-DECODE](0042_decode.md) |
| CLI verb surface | the UX contract | [ADR-CLI](0002_cli-surface.md) |

**2. Each module arrives with its tests.** A port without its tests is a
rewrite wearing the old code's name.

**3. Port when the milestone needs it, not before.** Porting early is porting
speculatively, and speculative ports are how the list grows.

**4. The archive is never modified and never imported.** Wrap it if you need
its behaviour in a harness; look for an existing seam before concluding an
archived module has to change.

**5. The archived engine's recorded numbers are a free correctness check.** The
gate harness reproduced the archived lexical eval exactly (hit@5 0.952 /
MRR 0.833, orbit 0.887) — which is what makes *"we varied only the index"* a
verified fact rather than an intention.

**6. A port earns its place by having a live consumer, not by having been
ported.** This is the rule two retirements were decided under, and it is the
one most likely to be needed again: a module kept *for what it pins* is a module
a reader will believe is live. When the last call site in `src/` goes, the row
goes and the module goes with it. **A retired row is not a standing licence** —
reviving one needs a new record and Arpit's sign-off, exactly as rule 1 says.

**7. Explicitly out of scope**, and named so nobody re-proposes them casually:
the SQLite substrate, the per-file cache, the lean profile, the state plane,
`fux.lock`, adapters beyond the capped three, and every deferred item.

### Consequences

- **The list is auditable.** "Where did this come from?" has a table for an
  answer rather than an archaeology exercise.
- **Ports are cheap and dated.** Each lands inside a milestone that needed it,
  so the reason is on the record.
- **Some duplication is accepted.** A ported module may look near-identical to
  the archived one; that is the point — the *architecture* was reset, not the
  arithmetic.
- **Un-ported archive code stays runnable**, so the baselines it establishes
  stay available even for modules never ported.
- **The list shrinks as well as grows.** Decision 6 has fired twice, and both
  times the module was deleted rather than left as reference — the alternative
  leaves a live-looking constant in a file nothing calls, which has already
  misled a reader once.

### Alternatives considered

- **Rewrite everything from scratch.** Rejected: it forfeits tested behaviour
  *and* the archived numbers that make the harness verifiable rather than merely
  plausible.
- **Import the archived package as a dependency.** Rejected: it makes a
  reference-only artifact load-bearing, and it would drag the substrate
  architecture in through its own imports.
- **Leave the list open, decide per module.** Rejected — that is the failure
  mode. A closed list makes each addition a visible decision.
- **Keep a ported module with no caller, for what it pins.** Rejected under
  decision 6: what such a module pins is usually a constant calibrated on the
  archived engine, and archive-is-not-evidence means it pins nothing a live
  decision may rest on.

### Reference (required)

- The archived engine — [`archive/v0.26/`](../../archive/v0.26/); the archive
  map — [`archive/README.md`](../../archive/README.md).
- Ports already landed, with their modules named in docstrings —
  [`src/fux/frontmatter.py`](../../src/fux/frontmatter.py),
  [`src/fux/query/tokenize.py`](../../src/fux/query/tokenize.py),
  [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py).
- The archived baselines this rests on —
  [`work/regression/README.md`](../../work/regression/README.md) §Archived runs.

### Veto condition

**Reopen this decision if** a module not on the list is proposed for porting,
or if `src/` ever imports the archive.

**How to check it:**

```bash
# 1. the archive is still never imported by live code
grep -rn 'archive' src/fux/ --include='*.py' | grep -E '^\S+:\s*(import|from)'
# expect: no output

# 2. the archive is still unmodified
git log --oneline -- archive/v0.26/ | head -3
# expect: nothing since it was archived

# 3. a port names where it came from
grep -rln 'archive/v0.26' src/fux/
# expect: docstrings in the ported modules, and only those
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-CLI](0002_cli-surface.md) ·
[ADR-RANKING](0012_ranking.md) · [ADR-GRAPH](0029_graph.md) ·
[ADR-REFER](0030_refer-plane.md) · [ADR-DECODE](0042_decode.md)

**Code**

- [`src/fux/frontmatter.py`](../../src/fux/frontmatter.py)
- [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py)
- [`src/fux/query/tokenize.py`](../../src/fux/query/tokenize.py)

**Measured evidence**

- [`work/regression/README.md`](../../work/regression/README.md)
