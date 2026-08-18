# W-44 — Decide how retired content is signalled in results

**Status:** OPEN · **human** (Arpit picks the option; the build follows)
**Blocked by:** — (nothing waits on it; it degrades answers every day it is open)
**Evidence:** [`../regression/2026-08-12-r2-close/report.md`](../regression/2026-08-12-r2-close/report.md)
§Finding 2 + [`ANALYSIS.md`](../regression/2026-08-12-r2-close/ANALYSIS.md) §2
**Opened by:** W-42, 2026-08-12

## The finding

Closing R2-Q3 put the frozen v0.19–0.26 documentation set into
`fux.toml`'s configured sources. That was correct and the question passed.

It also made the retired engine's documents rankable for questions about
the **current** engine — and they rank well, because they share its
vocabulary.

**Post-hoc probe, five unregistered queries** (labelled post-hoc; this is a
hypothesis, not a measurement):

| probe query | archived docs in top 5 | #1 result |
|---|---|---|
| *what is the ingest cache* | **5/5** | `archive/v0.26-docs/adr/0002-ingest-cache-chunker.md` |
| *what does fux doctor check* | **3/5** | `archive/v0.26-docs/adr/0012-debug-observability.md` |
| *how does BM25F weighting work* | 2/5 | `archive/v0.26-docs/adr/0008-…` |
| *how do I configure sources* | 1/5 | `archive/v0.31.0-fux-dir-layout-handoff.md` |
| *what is the committed index layout* | 0/5 | `work/adr/0011_fux-dir-layout.md` |

## Why it matters

The per-file cache those top results describe is a subsystem **CLAUDE.md
explicitly forbids porting back**. An agent asking *"what is the ingest
cache"* gets five confident, well-written documents about a deleted design,
and the only signal they are retired is the `archive/v0.26-docs/` prefix on
the `loc` — easy to miss inside a context window.

Nothing in the ranking knows a document is retired. `df` is computed over
the union, so the archived set also shifts the statistics every live
document is scored against.

## The options — Arpit's call

| option | what it does | cost |
|---|---|---|
| **A · accept** | archived docs are legitimately the answer to historical questions; `loc` is the signal | zero |
| **B · annotate, never reorder** *(recommended shape)* | a source declared `archived` stamps its results; `find`/`ask --json` carry the flag; **ranking byte-identical** | a config key + a schema field + its measurement |
| **C · narrow the source** | index only `archive/v0.26-docs/adr/` | one line, but arbitrary — Q3 would have passed under it too |

**B is recommended as a *shape*, not as an approved build.** It is the only
option that cannot regress a ranking, and it is the ruling the v0.26 line
already reached for exactly this failure mode (archived ADR-0013, *annotate,
never reorder*). It still needs its own measurement and its own ADR.

## Definition of done

- [ ] Arpit picks A, B or C.
- [ ] If B or C: an instrument that can actually measure the intrusion
      exists **before** the mechanism ships — five hand-picked probes is not
      a measurement, and the playground goldens live in a sibling repo over
      a different corpus and cannot see this.
- [ ] If A: recorded as a decision with its reasoning, and this item closes.
      "Accepted" is a verdict, not a non-answer.
- [ ] Whichever way: an ADR, with a reference.

## Hazard

**Do not build B because it is the recommendation.** The recommendation is
about shape. Shipping a ranking or annotation change off a five-query
post-hoc probe on one corpus is the exact thing CLAUDE.md's "never ship a
ranking change off a single corpus" rule forbids, and the v0.26 line
already paid for learning it once.
