---
type: Proposal
title: Query-log-informed pruning (query views)
description: Keep the terms agents actually ask for. The strongest strategy in the pruning literature uses query views; a per-repo agent query log is an asset Fux accumulates for free and no general search engine has.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# Query-log-informed pruning ("query views")

**The idea.** In the Bilkent comparative study, every pruning strategy
improved when combined with **query views** — knowledge of which terms
real queries actually use — with gains of 44–127 % at high pruning levels,
and the best overall strategy was a query-view combination. Fux accumulates
exactly this signal for free: every `fux ask` from an agent or a human is a
query against one repo's corpus.

**Why Fux is unusually well placed.** A web search engine's query log is
huge, noisy, and privacy-loaded. A repo's log is small, on-topic, and
belongs to the team that owns the repo. It is also *stable* — the questions
agents ask about a codebase repeat heavily (architecture, ownership,
"why was this decided"), which is precisely the distribution pruning wants
to protect.

**Sketch.** A committed `.fux/query-views.jsonl` (tiny: term → count,
capped, sorted, no query text, no timestamps — determinism and privacy both
require this). The selector gains **Rule D**: terms appearing in the query
view are exempt from the budget, bounded to a fixed share of it so a heavy
query pattern cannot consume the whole index. Cold-start behaviour is
today's behaviour — an empty view file changes nothing.

**Why not now.** It requires the engine to exist and be used before it has
data, so it cannot inform the first index build. It also opens two
questions worth deciding deliberately rather than in passing: whether the
view file is committed (shared across the team, and visible in review) or
local-only, and whether recording it is opt-in. Both are policy, not code.

**Graduation trigger.** After M7, once the engine has served real queries in
the Anton and fux repos for long enough to have a non-trivial view file —
then re-run the pruning-criterion arms with Rule D added, against the same
pre-registered retention rungs.

**Risks to hold.** A query log is a usage record; even term-only, it reveals
what a team investigates. Committed-by-default is likely wrong for the same
reason `meta = hashed` is the default
([`../compare/meta-privacy.compare.md`](../compare/meta-privacy.compare.md)).
Determinism also forbids the index depending on *when* the log was read, so
the view file must be an explicit, versioned input to a build, never a live
counter.

**References.** Altingovde, Ozcan, Ulusoy, *Static Index Pruning in Web
Search Engines: Combining Term and Document Popularities with Query Views*,
TOIS 30(1), 2011 — https://dl.acm.org/doi/10.1145/2094072.2094074 ·
[`../compare/pruning-criterion.compare.md`](../compare/pruning-criterion.compare.md)
(the selector this extends) · [P1-GATE](../regression/2026-08-09-pruning-eval/VERDICT.md).
