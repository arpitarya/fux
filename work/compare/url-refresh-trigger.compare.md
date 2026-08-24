---
type: Compare Doc
title: URL Refresh Trigger — what supplies the clock a URL has and a file does not
description: A file change is an event; a URL change is not. Compares manual, the post-commit hook, a local daemon, a CI schedule, and query-driven detection — and rules that detection and clock are two roles, not one fork.
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# URL refresh trigger — Comparison

> **Verdict: E always, B narrowly, and C-or-D as the deployment's clock —
> proposed, not ruled.**
> **The fork's premise is wrong as stated**, and naming that is half this
> document: *detector* and *clock* are two roles, and only the clock is a
> genuine either/or. **E — query-driven detection** (the refer plane records
> a `url:` doc dirty when `fetched_sha != indexed_sha`) is not a trigger at
> all, conflicts with nothing, and should be built whatever else is ruled.
> **B — the post-commit hook** is admissible **only** for the commit that
> changes `.fux/sources/urls`, which is the one commit causally connected to
> URL freshness; a hook that refreshes *stale* URLs on every commit turns
> every developer's `git commit` into network traffic and is L4 dead.
> **C — a local daemon** and **D — a CI schedule** are the same role for
> different deployments, and the design point decides: **D where CI can reach
> the sources, C where it cannot.** CLAUDE.md's litmus says air-gapped fleets
> are a design input, and in an air-gapped estate with an intranet Confluence,
> **D does not exist and C is the only clock there is.** That is a *different*
> argument from the one that lost in 2026-08-20 and it should not inherit that
> loss.
> **Status:** ⏳ awaiting Arpit (2026-08-22). **Confidence:** high that
> detector ≠ clock and that E is unconditional; high on B's narrow scoping;
> **medium** on shipping C now rather than parking it again — that is the
> call this document most wants ruled.
> **Reopen when:** any of — a consumer is found whose URL corpus has a real
> push feed (webhooks, Atom, a CQL cursor), which makes every clock here a
> fallback rather than the mechanism; **or** [W-75](../open/W-75-url-freshness.md)'s
> Phase 1 measurement shows the query-driven detector (E) already covering
> ≥ 90 % of documents that actually get retrieved, which would make the clock
> a long-tail concern and shrink C/D to a quarterly sweep; **or** a fetcher
> is shipped whose `validate` is cheap enough that a full sweep costs less
> than the coordination any clock needs.

## Context

**A file change is an event. A URL change is not.** That single asymmetry is
the whole problem, and it is why
[`maintenance-trigger`](maintenance-trigger.compare.md) — accepted
2026-08-20, verdict **A, git hooks + delta ingest** — does not settle this
one. That document's scope is stated in its own frontmatter: *source docs →
committed index*, where "source doc" means a file on disk that git can
observe changing. It compares the same four shapes this document does and
reaches a different answer, **because for files the event already exists and
the only question was who listens for it.**

For URLs there is no event to listen for. `post-commit` fires when a human
commits, which is uncorrelated with whether `https://wiki.corp/handbook`
changed. `fswatch` cannot watch a URL at all. So the options here are not
"who listens" but **"what supplies a clock"** — a genuinely different fork,
which is why this is a sibling document rather than a reopen of that one.

**What exists today.** Nothing. `fux update` fetches every listed URL when a
human types it ([ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision
3, one of L4's two fenced networked paths). Between those runs the index's
`url:` half is a mosaic of whenever each URL last happened to be fetched, and
nothing reports how old any of it is.

**What is already solved, and must not be re-solved here.** *Answer*
freshness. The refer plane fetches a cited URL and compares `fetched_sha`
against `indexed_sha`, returning `current` / `stale` / `unverified` /
`cached` ([`refer/freshness.py`](../../src/fux/refer/freshness.py),
[`refer-fetch-cache`](refer-fetch-cache.compare.md)). **A stale URL record
therefore costs recall, not correctness** — a document whose content changed
cannot be mis-answered, but it can fail to surface at all, because ranking
runs on the terms the index recorded. Every option below is buying recall,
and that is a weaker good than correctness. It should be priced accordingly.

## The law in the way

**L4 — offline by default.** *Network access only inside explicit, fenced,
opt-in paths.* Every option here except A and E asks fux to reach the network
without a human typing a networked command, so each has to answer the same
question: **where is the opt-in?** The answers differ in quality, and that is
the axis the matrix weights highest:

- **B** — the opt-in is `fux hooks --install`, a one-time act whose
  consequence (network on every commit, forever) is invisible at the moment
  of consent. **This is the weakest opt-in of the four**, and it is why B is
  scoped down rather than accepted whole.
- **C** — the opt-in is starting the daemon, and it stays visible for as long
  as it runs.
- **D** — the opt-in is a workflow file, committed, reviewed, and readable by
  anyone in the repo. **The strongest opt-in available**, and it is not close.

## Options

**A — manual only (status quo).** A human runs `fux update`. Zero cost, zero
new surface, and the failure mode is the one that motivated the question: an
index silently behind what everyone believes it reflects, with no report of
by how much.

**B — the post-commit hook, extended to URLs.** The hook exists
([`maintain/hooks.py`](../../src/fux/maintain/hooks.py)) and already defers:
`post-commit` runs `fux ingest --spawn-runner`, which records a dirty list
and spawns a detached one-shot runner, per
[`hook-at-scale`](hook-at-scale.compare.md) verdict B (built 2026-08-22,
W-66). Two sub-shapes, and they are not equally defensible:

- **B1 — refresh URLs the commit itself added or changed.** A commit that
  edits `.fux/sources/urls` *is* a real change event with a causal link to
  URL freshness: new lines have no record at all. Narrow, bounded by the
  diff, and it fires only on commits that touch one specific file.
- **B2 — opportunistically refresh the N stalest URLs on every commit.**
  Uses developer commits as a sampling clock. Superficially clever — an
  active repo refreshes often, an idle one does not need to — and **it makes
  every `git commit` in the repo issue network requests to third-party
  hosts.** That is L4 inverted, not L4 satisfied.

**C — a local daemon.** `fux watch`, or the existing runner looping. **The
build is smaller than it sounds**, and this is the strongest fact in C's
favour: [`maintain/runner.py`](../../src/fux/maintain/runner.py) is already a
detached process with a PID lock, a stop protocol (`request_stop`,
`take_over`), liveness detection and a status file that `fux doctor` and
`fux ask` already read. A daemon is that process with a sleep and a loop.

**D — a CI schedule opening a PR.** A scheduled workflow runs `fux update`
and opens a pull request carrying the index diff. **The URL path then reduces
to the git path**, which is already solved: same review, same hooks, same
audit trail.

⚠ **`maintenance-trigger` rejected CI (its option B)** — *"a bot commits over
the human's diff, defeating the doc-major diffable design the committed index
exists for."* **That rejection does not transfer intact, and the reason is
narrow**: it was aimed at a bot **committing back** to a branch a human is
also committing to. A bot opening a **PR** does not race a human's next
commit; a human merges it, and the merge is the review. What *does* transfer
is the warning — if D is ever implemented as push-and-commit rather than
PR-and-merge, it becomes the option that was already rejected.

**E — query-driven detection.** The refer plane already fetches cited URLs
and computes `fetched_sha`. When it differs from `indexed_sha`, record that
doc id in the dirty list. **The file already exists**
([`maintain/dirty.py`](../../src/fux/maintain/dirty.py)) and so does the
narrowing parameter that consumes it (`ingest.run(only_urls=…)`,
[`ingest/run.py`](../../src/fux/ingest/run.py) line 107). Detection becomes
free, paid for by traffic already being generated, and prioritisation is
**usage-weighted at no cost** — popular documents get verified constantly
because they are cited, and staleness in a document nobody retrieves is
staleness nobody pays for.

## Matrix

| criterion (weight) | A manual | B1 hook, added lines | B2 hook, stalest N | C daemon | D CI → PR | E query-driven |
|---|---|---|---|---|---|---|
| **quality of the L4 opt-in (H)** | n/a — human typed it | one-time install, bounded by a diff | **one-time install, unbounded network** | visible while running | **committed, reviewed workflow** | n/a — no new network |
| covers URLs nobody queries (H) | yes, when run | no — only new lines | yes | **yes** | **yes** | **no — this is E's whole limit** |
| works air-gapped / no CI (H) | yes | yes | yes | **yes** | **no** | yes |
| always-on process (M) | no | no | no | **yes** | no | no |
| index churn reviewable by a human (M) | yes | yes | no — lands silently | no — lands silently | **yes, it is a PR** | yes |
| cost to build (M) | none | small | small | **medium, but runner.py is 80 % of it** | small — a workflow file and docs | **small — dirty.py + only_urls exist** |
| makes `git commit` slower (M) | no | no — the hook defers (W-66) | no — defers | no | no | no |
| net new engine surface (L) | none | a hook branch | a hook branch | **a verb, a loop, a lifecycle** | none — a workflow file, not fux code | one call site in `refer/` |

## Why the losers lose

**B2 is the trap, and it is the appealing one.** Commits as a sampling clock
is a real technique and it fits the repo's grain — until you write down what
a colleague experiences: they clone the repo, run one `fux hooks --install`
because the README said to, and from then on every commit they make sends
requests to hosts they never chose, on a schedule they cannot see, from a
machine that may be on a customer's network. **The failure is not technical,
it is that the consent does not match the consequence.** B1 keeps the good
half — a commit that edits the URL list is a real event — and discards the
half that has no causal story.

**A loses on one property only, and it is worth naming precisely**: not that
it is stale, but that it is **silently** stale. Half of A's failure is
recoverable for near-zero cost by reporting rather than refreshing — a
`fux doctor` line and a count on `fux ask`, in the shape ADR-MAINTENANCE
decision 1b already established for pending re-index. **That reporting should
ship regardless of which clock wins**, and if Arpit rules "nothing automatic",
it is what ships instead.

**E cannot be the answer alone**, and its limit is exact: it only ever sees
documents someone retrieved. The long tail is never validated, and the tail
is where a corpus of 100k URLs mostly lives. **E covers the head; a clock
covers the tail.** They are complements, which is why the verdict takes both.

**D's weakness is not technical, it is that it assumes a CI runner that can
reach the sources.** For a public-docs corpus that is free. For the design
point in CLAUDE.md's litmus — an air-gapped estate whose Confluence lives on
the intranet — **the CI runner that can reach those URLs may not exist**, and
if it does, giving it those credentials is its own security conversation. D
is the best option in the deployments where D is available, and unavailable
in the deployment the architecture was drawn for.

**C's cost is a real one and should not be minimised by pointing at
`runner.py`.** A daemon is a lifecycle: start, stop, restart on crash, log
somewhere, survive a laptop sleeping, not run twice, not run as a stale build
after an upgrade. `runner.py` solves the *locking* half and none of the
*operations* half. The honest version of C's pitch is: **the hard part is
already built, and the tedious part is not.**

## Consequences

- **E is unconditional.** It does not add a networked path (the refer plane
  already fetches under its own `always` policy), it does not touch committed
  bytes, and its consumer already exists. If exactly one thing is built from
  this document, it is E.
- **The dirty list's own contract needs a sentence, and this is the crux
  W-75 carries.** [`dirty.py`](../../src/fux/maintain/dirty.py) says it is
  *"advisory, never authoritative"* — the sentence that keeps L3 true,
  because `fux ingest` re-walks the whole corpus regardless. A URL refresh
  driven by that list **is** authoritative for the URLs it names, since the
  whole point is not to fetch the rest. The defence, which must be written
  down rather than assumed: **the `url:` half of the index is already a
  mosaic of different moments** — each record carries whatever its last
  fetch produced — so a partial refresh changes the *spread* of those
  moments, not the kind of object the index is. L3 is *same sources → same
  bytes*, and a URL is not the same source twice. ⚠ This must not be
  confused with *"just index the delta"*, which was ruled **not** the fix for
  R5 on the git path; that argument was about an offline walk that is already
  cheap, and it does not reach a networked path that is not.
- **B1 implies a hook that can touch the network**, which is new. It must
  inherit ADR-MAINTENANCE decision 3 (best-effort, cannot block anything) and
  the defer shape from `hook-at-scale` verdict B, and it needs its own
  config gate — installed hooks that fetch must be opt-in **separately** from
  installed hooks that index.
- **Whatever wins, the reporting half is separable and cheaper**, and should
  land first.

## Reopen trigger

Stated in the verdict block. In short: **a real push feed anywhere in a
consumer's corpus** demotes every option here to a fallback; **E measured at
≥ 90 % coverage of retrieved documents** shrinks the clock to a sweep; **a
cheap enough `validate`** makes a full sweep cheaper than any coordination.

## References

- [`maintenance-trigger`](maintenance-trigger.compare.md) — the accepted
  sibling fork for *files*, whose scope this document deliberately does not
  overlap; its option C is *"not eliminated forever … would be its own
  proposal if revisited"*, and this is that revisit for a different reason
  than the one it anticipated
- [`hook-at-scale`](hook-at-scale.compare.md) — verdict B, the deferring
  hook, built 2026-08-22 (W-66)
- [`refer-fetch-cache`](refer-fetch-cache.compare.md) — the TTL cache and the
  `cached` verdict state, which is why E's fetches are already happening
- [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) — decision 3 (two named
  fenced paths), decision 4 (a failed fetch keeps the prior record)
- [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) — decisions 1a (the hook
  defers), 1b (`fux ask` declares the pending count), 3 (hooks are
  best-effort)
- [`maintain/dirty.py`](../../src/fux/maintain/dirty.py) ·
  [`maintain/runner.py`](../../src/fux/maintain/runner.py) ·
  [`ingest/run.py`](../../src/fux/ingest/run.py) `only_urls`
- [`proposals/knowledge-ci.md`](../proposals/knowledge-ci.md) — part (a) is
  option D's staleness gate, sketched 2026-08-09
- [`proposals/url-freshness.md`](../proposals/url-freshness.md) — the
  proposal this fork belongs to
