# W-44 — Decide how retired content is signalled in results

**Status:** **PARTLY UNPARKED, 2026-08-22 (Arpit).** The demotion half is
startable now; the signal half is still gated.

| half | state |
|---|---|
| **the demotion weight** — configurable, **default `1.0`** ([ADR-DIR-LIST](../../docs/adr/0022_dir-list.md) decision 11) | **LANDED 2026-08-22.** `[ranking] archived_weight` in `fux.toml`, applied in the one shared `rank()`. At the default nothing reorders (asserted); the actual default stays `1.0` — moving it is still W-52's gate, unchanged by landing the capability |
| **the disclaimer** — response-level, fires when any archived document is returned (decision 12) | **gated** by decision 10's sentence — *"changing what a verb says about a document is a claim that needs an instrument"*. It says **more** than the marker, so it cannot be less gated. **Arpit's to lift** |
| **the marker** — `[archived]` per result (decisions 5, 7) | **gated**, unchanged |
| **moving the default off `1.0`** | **gated harder** — the query set **plus a second corpus**, per [W-52](W-52-df-over-the-union.md) |

**Trigger (for the gated halves):** a frozen query set with expected
live-vs-archived answers exists. Parked with a trigger, never ambient — it does
not resume because it looks ready.

> **The 2026-08-22 ruling, so nobody re-litigates it.** Arpit asked for archived
> documents to be scored normally, demoted, and disclaimed — and the demotion
> reversed the "never reorder" half of a decision he had accepted on 2026-08-19.
> **Making the weight configurable with a no-op default is what reconciled the
> two**: the capability ships, the ranking change does not, and the measurement
> still decides the default. That reconciliation is the reason this item moved
> at all; an unconditional demotion would have stayed fully parked.
**Model:** **Opus** for the pre-registration, Sonnet to build it once frozen
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

> **2026-08-19 — the finding moved; re-derived against the repo.** Three
> things changed on 2026-08-18 and none is reflected below.
> **(1) The problem is wider than `archive/`.** `work/` joined
> `[sources] dirs`, so the corpus now carries `WORKLOG.md` (1 400+ lines,
> including decisions later reversed) and `compare/` docs that argue *rejected*
> options at length. Option B annotates a *source*; it cannot reach retired
> claims inside a live document.
> **(2) The problem is also narrower.** Everything under `archive/` is already
> out of the corpus — `dirs` names exactly one archive path,
> `archive/v0.26-docs`, deliberately (W-42). **Archiving is already the
> retirement signal** for everything else; closed work items left the index by
> being moved. That strengthens **A**, and makes **C** a narrowing of one
> deliberate exception rather than the arbitrary line this file calls it.
> **(3) The probe is not reproducible as written.** It ran against an index
> whose records still point at `docs/open/…`, `docs/conformance/…`,
> `work/adr/0011_fux-dir-layout.md` — paths the restructure removed. The
> committed index has not been re-ingested since. Any instrument built for the
> DoD below has to be built against a corpus the probe never saw.
> **(4) The config surface is shared with [W-45](../../archive/open/W-45-source-exclusion.md).**
> `[sources] dirs` is a flat list of strings; declaring a source `archived`
> needs the same schema change W-45 needs for exclusion. Decided apart, the
> second re-litigates the first.

> **2026-08-19 — DECIDED: option B.** Arpit chose *annotate, never reorder*.
> The decision is recorded in
> [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md), which is
> **accepted and unbuilt**: a record under `archive/` carries `archived: true`,
> every verb surfaces it, and **the ranking is byte-identical**.
>
> **Two things changed on the way in.** *(1)* B needs **no config key** — the
> one-archive law makes `loc.startswith("archive/")` a complete test, so this is
> decoupled from [W-45](../../archive/open/W-45-source-exclusion.md) after all. *(2)* The `df`
> contamination is **not** part of B and is filed separately as
> [W-52](W-52-df-over-the-union.md), because excluding archived documents from
> `df` moves 42% of live terms and that is a ranking change requiring its own
> pre-registration.
>
> **Superseded record, 2026-08-19.** ADR-ARCHIVED-SIGNAL was archived the same
> day it was written: Arpit moved source directories into their own committed
> file, which made `archived` a **declaration on a line** rather than something
> derived from `loc.startswith("archive/")`. That fixes the weak point the
> original recorded — the derivation was exact for this repo and a silent
> convention for anyone else. The live record is
> [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md), and **the file itself now
> exists**: `.fux/sources/dirs` shipped 2026-08-19, and `archived=` is parsed
> and validated — see the [run](../regression/2026-08-19-w54/report.md).
>
> **This item stays open in the agent lane, and it got narrower.** The
> declaration is built; what is left is exactly the half ADR-DIR-LIST decision
> 10 gates — the record property, the marker in every verb, and the
> pre-registered query set that has to exist before either lands. Nothing in
> `src/` reads `archived` today, on purpose.

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

- [x] ~~Arpit picks A, B or C~~ — **B**, 2026-08-19.
- [x] ~~An ADR, with a reference~~ —
      [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md), accepted.
- [ ] **The instrument, before the mechanism** — a pre-registered query set with
      expected live-vs-archived answers, frozen first. Five hand-picked probes
      is not a measurement, and the playground goldens are a different corpus
      and cannot see this. This is ADR-DIR-LIST decision 10's gate.
- [ ] Build it: the property at ingest, the three verbs agreeing, and a test
      asserting **no archived document is ever returned unmarked**.
- [x] **The demotion weight** — `fux.toml`, default `1.0`, keyed off the
      declaration and never a path. **Two tests, not one**: scores and order
      byte-identical at the default, *and* the weight demonstrably applied when
      set. A knob that silently does nothing is the failure mode ADR-REFER
      already refused once with `max_age_seconds`. **Landed 2026-08-22** —
      `src/fux/config.py` (`archived_weight`), `src/fux/ingest/gitdir.py`
      (`archived_dirs`), `src/fux/query/rank.py` (the multiply, skipped
      outright at the default). Both tests exist:
      `tests/query/test_scan.py` and `tests_e2e/test_verbs.py::test_archived_weight_demotes_only_when_configured`.
- [ ] **The disclaimer** — response-level, conditional, carrying the rule rather
      than a hedge. **stdout must stay byte-identical**; whether it is a new
      `--json` key or stderr-only is [ADR-CLI](../../docs/adr/0002_cli-surface.md)'s
      call, taken there.
- [ ] Assert the ranking did not move — scores and order identical with and
      without the property (decision 4).
- [ ] `CHANGELOG.md` under `[Unreleased] → Added`.

## Hazard

**Do not build B because it is the recommendation.** The recommendation is
about shape. Shipping a ranking or annotation change off a five-query
post-hoc probe on one corpus is the exact thing CLAUDE.md's "never ship a
ranking change off a single corpus" rule forbids, and the v0.26 line
already paid for learning it once.
