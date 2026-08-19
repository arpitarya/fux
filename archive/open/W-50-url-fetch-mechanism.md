# W-50 — should a URL declare how it is fetched?

**Status:** OPEN (Lane A — agent-executable **as of 2026-08-19**; every decision
is made, what remains is building)
**Model:** **Opus** — it writes a record for a new verb and amends three others;
the code is small and the record surface is not
**Blocked by:** — · **Blocks:** nothing, but see [W-49](W-49-url-fragment-truncation.md)'s hazard
**Opened by:** Arpit, 2026-08-19, during the [W-31](../IMPLEMENTATION.md) *(ratified 2026-08-19)* ratification review
**Records affected:** [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)
decisions 1–2 · [ADR-URL-LIST](../../docs/adr/0018_url-list.md) decisions 2–3
(its veto condition fires on this) · [ADR-CONFIG](../../docs/adr/0014_config.md)
decision 5

> **2026-08-19 — Arpit's ruling. The item changed shape rather than closing.**
>
> **(a) The URL list becomes tool-managed, not hand-maintained.** A CLI command
> fetches a URL and then **writes the URL and its attributes into
> `.fux/sources/urls`**. The file is *"not to be edited manually"*. That makes
> it a **lockfile**: generated, committed, reviewed in a diff, never typed. It
> is a bigger change than the grammar it consumes, and it reaches
> [ADR-URL-LIST](../../docs/adr/0018_url-list.md) (written for a
> human-maintained file), [ADR-CLI](../../docs/adr/0002_cli-surface.md) (six
> verbs, and this is a seventh) and
> [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision 3 (*fetching
> happens only under `--refresh-urls`* — this command fetches too).
>
> **(b) CLI flags and per-URL attributes are two different things**, and the
> flags feed the file rather than replacing it: you pass `--cdp` / `--hash`
> once, at record time, and the attribute is written down. **This resolves the
> per-run-bytes objection entirely** — the flag never decides a fetch at ingest
> time, it decides what gets *written*, and what gets written is reviewed.
>
> **(c) `plain` is the writer's default, and L5 is untouched.** Arpit,
> 2026-08-19: *"in the sources file every attribute should be defined — if
> nothing is passed in the CLI it should still say `meta=plain`."* **Every
> written line states both attributes explicitly**, so there is no such thing as
> an undeclared line in a generated file, and L5 keeps its job unchanged: it is
> what a **missing** attribute means, which a correctly written file never
> exercises. No law changes. Recorded as
> [ADR-URL-LIST](../../docs/adr/0018_url-list.md) decisions 12–13.
>
> **(d) Every decision in this item is now made.** What remains is building, so
> the item **moves to the agent lane**.

## What Arpit asked for

> Whether a URL should be fetched using fetcher or not is optional. By
> default it should be fetched without CDP; in case it doesn't work, only then
> using CDP (fetcher) — so explicitly maintain what can be fetched using the
> default mechanism vs the CDP mechanism.

## The tension inside the ask, and the resolution

Two mechanisms are described, and they are not the same:

- *"in case it doesn't work, only then CDP"* — **automatic fallback.** Which
  fetcher ran depends on network conditions at that instant. Same URL, two runs,
  different bytes, no record of why. That is L3 lost on the one path that is
  already the exception.
- *"explicitly maintain what uses default vs CDP"* — **declaration.**
  Deterministic, reviewable, diffable.

**They reconcile if fallback is a discovery step that writes its verdict down.**
The first `--refresh-urls` on an undeclared URL tries the default mechanism; if
it fails the bar, it retries via the fetcher and, on success, **rewrites that
line as declared**. The change appears in `git diff` as a line a human reviews.
Detection happens once per URL, ever, inside the already-fenced networked path;
every later run reads a declaration and is deterministic.

## The real decision: where does "the default mechanism" live?

This is the part that is not a detail. [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)
decision 1 is *"Fux never fetches. A consumer-owned fetcher file does"*, and
`src/fux/` holds zero network lines. A built-in fetcher would use `urllib`, so
**L1 and L4 both survive** — what it spends is the **adapter cap**, which is the
record's central promise and is load-bearing for M4
([W-24](W-24-m4-refer-plane.md): *"HTTP+Confluence — that cap is a decision"*).

| where | what it costs |
|---|---|
| **in core** (`urllib` inside `--refresh-urls`) | simplest for a consumer; **spends the adapter cap**, and the cap is the thing that has kept `src/fux/` dependency-free through two rebuilds |
| **a generated default fetcher** *(recommended shape)* | fux writes `.fux/fetchers/http.py` **write-if-missing**, exactly as [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) decision 6 already does for `.fux/README.md` and `.fux/.gitignore`. Core ships a *template*, never a fetch path. The file is consumer-owned from birth — committed, editable, lintable — and the cap survives intact |
| **a chained fetcher list** (`fetcher = ["http.py", "cdp.py"]`) | core still never fetches, but core now owns fallback *policy*, which is the cap leaking somewhere harder to see |

> **2026-08-19 — the grammar left this item.** Arpit decided the per-URL
> attribute syntax in [ADR-URL-LIST](../../docs/adr/0018_url-list.md)
> decisions 7–11 (`<url> key=value …`, one form, unknown key is an error, line
> beats source, duplicate-with-conflict is an error, `fetch=` reserved).
> **Decided, not built.** What is left here is narrower and entirely about
> fetching: *what values `fetch=` may take*, *where the default fetcher lives*,
> and *what "doesn't work" means as a checkable condition*.

## What the file would look like

`.gitattributes` is the closest prior art — a line-oriented committed file of
`pattern attr1 attr2…`, attributes set / unset / valued.

```text
# .fux/sources/urls — unmarked means fetch=http (the default)

https://example.com/handbook/oncall
https://example.com/docs/api                 meta=plain
https://wiki.corp/display/ENG/Runbook        fetch=cdp
https://app.corp/reports/q3                  fetch=cdp meta=plain
```

**The grammar above is now decided** (ADR-URL-LIST decisions 7–11); only the `fetch=` column is open. Every property [ADR-URL-LIST](../../docs/adr/0018_url-list.md) bought survives:
one URL per line, line-wise merge at 5 000 entries, `#` comments, loader-sorted
so file order stays presentation-only. It is a parser change, not a format
change — and it resolves that record's named limit, that `meta` is per *source*
and cannot differ per URL.

Rejected shapes, recorded so they are not re-argued: **sections**
(`[http]` / `[cdp]`) reintroduce order significance and make a mechanism change
a two-line diff; **a file per mechanism** (`urls`, `urls.cdp`) needs no parser
change but multiplies files the moment a second attribute exists — and one
already does.

## The question that has to be answered before any of it

**"In case it doesn't work" is not yet checkable**, and a veto written as an
event never fires. Non-2xx is easy. The hard case is a `200` returning an empty
client-rendered shell — which is the case CDP exists for. Fux already computes
`wlen` after conversion, so the cheapest honest bar is **non-2xx, or `wlen`
below a threshold**. Richer signals (empty app root, hydration payload with no
prose) are a classifier, and a classifier that misfires silently indexes a
navigation bar as a runbook.

## Definition of done

- [ ] ~~The file grammar~~ — **decided 2026-08-19**, [ADR-URL-LIST](../../docs/adr/0018_url-list.md) decisions 7–11.
- [ ] A compare doc, per the standing rule — this is a fork with real options.
      **Fold in [W-45](W-45-source-exclusion.md)**: both change the same
      `[sources]` schema, and decided apart the second re-litigates the first.
- [ ] Arpit's verdict on **(a)** declaration vs auto-fallback vs
      detect-once-then-declare, **(b)** where the default mechanism lives, and
      **(c)** the checkable definition of "doesn't work".
- [ ] If it lands: [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)
      amended or superseded, [ADR-URL-LIST](../../docs/adr/0018_url-list.md)
      likewise — its veto condition fires by design — and
      [ADR-CONFIG](../../docs/adr/0014_config.md) decision 5 revisited.
- [ ] **Fold in [W-49](W-49-url-fragment-truncation.md)**: it rewrites the same
      parser and must answer the same question about where a comment begins.
- [ ] Whether the record carries which mechanism produced it (a `fetch`
      property beside `mode` and `meta`) — an `_format` bump if yes, same class
      as the `enriched` shape.

## Hazard

**This is a change request against a shipped, accepted record.** Per
[W-31](../IMPLEMENTATION.md) *(ratified 2026-08-19)*'s own definition of done, that makes it a
new item rather than a reason to withhold ratification — *"the built code is not
silently left contradicting an unratified ADR."* Ratifying W-31 and opening this
are compatible; leaving W-31 open until this is settled is the alternative, and
it costs another week of shipped code under an unratified decision.

## Reference

- `scrapy-playwright` — per-request opt-in, **no automatic fallback**:
  https://github.com/scrapy-plugins/scrapy-playwright
- The crawler-vendor consensus on static-first-then-render, and the five signals
  it classifies on:
  https://webclaw.io/blog/javascript-rendering-api-browser-fallback-web-scraping
- `gitattributes(5)`, the per-entry attribute grammar:
  https://git-scm.com/docs/gitattributes


---

## The L5 question — answered 2026-08-19

**L5:** *"Hashed meta is the default for non-git sources, enforced at write
time. It closes an ACL-mismatch leak, so it is not a configuration
preference."*

The question was whether "`plain` should be default" flipped the engine's
default (a law change) or only the writer's (not one). **Arpit's answer removed
the fork**: every written line states every attribute, so the engine's default
governs only lines nobody wrote.

- **L5 stands, unamended.** It is now the meaning of a *missing* attribute — a
  hand-added line, a merge that dropped a key, a file written by an older fux.
  Those should resolve strict, because strict is the safe reading of a line no
  one authored.
- **`plain` is what the command writes** unless `--hash` is passed, and it
  writes it *visibly*, so the policy is in the diff rather than in the absence
  of a key.
- **The completeness rule is enforceable**, which is the part worth keeping: a
  line missing an attribute was not written by fux, so `fux doctor` can report
  it. That turns *"the list is not edited manually"* from a policy into an
  observation — the same move this repo already made with `git check-ignore`
  rather than reading `.gitignore`'s text.

**The residual exposure, stated once:** the command defaulting to `plain` means
an internal page gets readable display text in the committed index unless the
operator passes `--hash`. Arpit's to accept, and accepted — but it is now a
default on a reviewed command, visible on the line it wrote, rather than a
property of every line nobody wrote.

## Definition of done — revised 2026-08-19

- [x] ~~The file grammar~~ — [ADR-URL-LIST](../../docs/adr/0018_url-list.md) 7–11.
- [x] ~~Declaration vs auto-fallback~~ — **declaration**, and flags feed the
      declaration rather than competing with it (ruling b).
- [x] ~~Where the default fetcher lives~~ —
      [ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md): generated
      write-if-missing, core keeps zero network lines.
- [x] ~~A checkable definition of "doesn't work"~~ — **moot.** There is no
      automatic escalation, so nothing needs to detect failure.
- [x] ~~The L5 question~~ — **answered**: L5 stands; every written line states every attribute ([ADR-URL-LIST](../../docs/adr/0018_url-list.md) 12–13).
- [ ] **A record for the managing command** — the verb, its flags, what it
      writes, and whether it fetches at record time or only validates.
      [ADR-CLI](../../docs/adr/0002_cli-surface.md) gains a verb;
      [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision 3 gains a
      second networked path.
- [ ] **[ADR-URL-LIST](../../docs/adr/0018_url-list.md) amended**: it is written
      for a file a human maintains — comments "are the reason a human can
      maintain the file at all", duplicates are "merge artefacts". Under a
      lockfile those sentences change meaning. Canonical ordering moves from the
      loader to the writer, and the file needs a do-not-edit header.
- [ ] Fold in [W-49](W-49-url-fragment-truncation.md) — a writer that quotes
      correctly is most of that fix — and [W-45](W-45-source-exclusion.md),
      still the same `[sources]` schema.
