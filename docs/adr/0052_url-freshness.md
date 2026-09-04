---
type: ADR
name: ADR-URL-FRESHNESS
title: "ADR-URL-FRESHNESS (0052) — six verdicts, and a per-URL ttl that can only narrow"
description: "How fresh a url: citation is, said in six positions that never collapse into each other; and ttl= as a per-URL bound that narrows the caller's policy and can never widen it."
status: accepted
date: 2026-09-01
feature: the freshness verdict vocabulary and the per-URL check interval
owns: [src/fux/refer/freshness.py]
laws: [L2, L3, L4]
timestamp: 2026-09-01T00:00:00Z
---

# ADR-URL-FRESHNESS: what a citation may claim, and how often it has to earn it

## §1 — For humans

When fux quotes a `url:` document, the honest question is *how do you know that
is still what the source says?* — and there is more than one true answer. Fux
just looked and it matched. Fux just looked and it did **not** match. Fux looked
recently. Fux could not look at all.

Each of those is a different strength of claim, and the failure this record
exists to prevent is a weaker one being reported as a stronger one. So they are
six distinct labels and nothing ever folds one into another:

| label | what it means |
|---|---|
| `current` | fetched now; the source matches the index |
| `stale` | fetched now; the source has changed |
| `cached` | a copy fetched within the ttl matched; **we looked recently, not now** |
| `as-ingested` | the source was unreachable, but the passage still matches the exact bytes the record was built from, held in `.fux/acquired/` |
| `unverified` | we did not look, and have nothing to compare |
| `as-ingested` *(mismatched)* | the retained bytes disagree with the index — an **index defect**, not a stale source |

`ttl=` on a URL line says how long that URL may go unchecked. It is a **bound
that narrows**: it can make a URL checked more often than the caller's policy
asks, never less. With the default policy — caching off — no line can turn
caching on.

```mermaid
flowchart TD
    P{"policy<br/>never?"} -- yes --> AQ1{"retained<br/>bytes?"}
    AQ1 -- yes --> AI["as-ingested"]
    AQ1 -- no --> UV["unverified"]
    P -- no --> T{"within<br/>min(policy, ttl)?"}
    T -- yes --> CA["cached"]
    T -- no --> F{"fetch<br/>succeeds?"}
    F -- yes --> CU["current / stale"]
    F -- no --> AQ2{"retained<br/>bytes?"}
    AQ2 -- yes --> AI
    AQ2 -- no --> UV
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  policy=never ---------------> retained bytes? -- yes --> as-ingested
                                       |  no
                                       +--------------> unverified

  policy=always --> inside min(policy, ttl)? -- yes --> cached
                              |  no
                              v
                        fetch succeeds? -- yes --> current | stale
                              |  no
                              v
                        retained bytes? -- yes --> as-ingested
                              |  no
                              +-----------------> unverified
```

</details>

### Examples

The six verdicts, from the constructors that build them:

```console
constructor                  label         current  note
----------------------------------------------------------------------------
verify('a','a')              current       True     source matches the index
verify('a','b')              stale         False    source has changed since ingest
verify('a', None)            unverified    None     not fetched
cached('a','a', 30, 300)     cached        True     served from the local fetch cache, 30s old
as_ingested('a','a')         as-ingested   True     source unreachable; matches the bytes it was ingested from
as_ingested('a','b')         as-ingested   False    source unreachable, AND the index disagrees with the …
```

---

## §2 — For agents

### Context

Before this record, a `url:` citation could say four things, and the fourth was
doing too much work. `unverified` meant *"we did not look"* — and it was also
what fux said when it **tried** to look and could not: signed out, offline, the
host unreachable, the share link expired. Those are not the same, and the
difference is not academic. A corpus where every URL sits behind a session
degrades wholesale to `unverified` the moment that session lapses, and an agent
reading the bundle cannot distinguish *"nobody asked me to check"* from *"I
tried and the world would not answer"*.

[ADR-ACQUIRED](0050_acquired-plane.md) put the fetched bytes on disk, which made
a third thing possible: compare the passage against the exact input the record
was built from. That is a **real comparison** — it catches an index that has
drifted from its own source bytes — and it is strictly more than `unverified`
has ever been able to say. It needed a name that was neither `current` nor
`unverified`, because it is neither.

Separately, `ttl=` was added to the URL line grammar in the same work item, and
**nothing consumed it.** It parsed, it validated, it round-tripped through `fux
update`, and no code path turned it into a bound. That is precisely the failure
[`freshness.py`](../../src/fux/refer/freshness.py) refused `max_age_seconds` over
— *a knob that silently does nothing is the worst available outcome, because a
caller passing it reasonably believes they bounded their staleness* — and
shipping it that way would have contradicted the argument in the module's own
docstring.

### Decision

1. **Six labels, and `label` is the only thing that computes one.** Nothing
   downstream re-derives a verdict from `current`; the ordering lives in one
   property, in one module.

2. **A weaker claim never collapses into a stronger one.** `cached` is not
   `current`: *we looked recently* is a different claim from *we just looked*.
   `as-ingested` is not `current` either: it says nothing about the world right
   now. A caller that wants to treat them alike may; the engine will not do it
   on their behalf.

3. **`as-ingested` outranks `unverified` and is outranked by everything that
   reached the source.** The precedence in `Verdict.label` is `cached` →
   `as-ingested` → `unverified` → `current`/`stale`. `cached` sits above
   `as-ingested` because a TTL hit means fux went out within the window; the
   retained-bytes comparison never went out at all.

4. **`current` still records whether the shas agreed, on every verdict.** Both
   `cached` and `as_ingested` keep the comparison result alongside the fact that
   it was not a fresh look. Dropping either would make the verdict a smaller
   claim than the truth.

5. **A mismatch against retained bytes is an index defect, not staleness.** The
   source did not change; the record disagrees with the bytes it was built from.
   The note says `rebuild this record` rather than `source has changed`, and the
   label stays `as-ingested` rather than becoming `stale` — reporting it as
   `stale` would send a reader to the wrong system.

6. **The retained-bytes path decodes through the SAME functions ingest used.**
   `from_acquired` imports `_decode_fetched` and `sanitize` from
   `ingest/urlsrc.py` rather than reimplementing them.
   ⚠ **This is the property the whole fallback rests on.** A verify-time sha is
   compared against an ingest-time sha; if the two pipelines diverge by one
   line, every retained document is `as-ingested` with `current=False` forever —
   a defect that presents as a working feature.
   `tests/refer/test_refer_acquired.py::test_the_sha_matches_what_ingest_would_have_recorded`
   is the assertion, and it exists because the failure would otherwise be silent.

7. **A blob that is missing, deleted by hand, or no longer decodes yields
   `None`, which is `unverified`.** *We have nothing to compare* must not be
   dressed up as a comparison that happened.

8. **Only `url:` documents take this path.** A `file:` document is on disk
   already; reading the checkout is not a fetch and never was.

9. **`ttl=` is a duration on the URL line, defaulting to `24h`, resolved through
   the same three layers as `keep` and `meta`** — built-in default, then
   `[sources.url] ttl`, then the line. The grammar is `0` or
   `<integer><s|m|h|d>`. It is stored **verbatim** as written: `1h` round-trips
   as `1h`, never as `3600`, because the value goes back into a committed file.

10. **`ttl` is the first typed attribute in the source-list grammar.** Every
    attribute before it was a closed enum, which a duration cannot be; the
    `Attribute` record gained an optional `validate` callable rather than a
    second parser. **`--ttl` on the CLI is validated by that same callable**, so
    `--ttl 1x` and a hand-written `ttl=1x` fail identically. Two validators
    would drift.

11. **The effective interval is `min(policy.cache_ttl_seconds, declared)` — a
    line may narrow it and can never widen it.** Both halves answer a different
    failure:

    - **Cannot widen**, so a URL line can never serve a cached byte to a caller
      who did not ask for caching. The policy default is `0`, and `min(0,
      86400)` is `0` — W-60 verdict F holds by arithmetic rather than by a rule
      somebody has to remember. This matters because `ttl` defaults to `24h` on
      *every* line: without the bound, adding a URL would quietly switch
      caching on.
    - **Can narrow**, so `ttl=0` means *always go out for this one*, whatever
      the caller's policy says. That is the case a per-URL attribute exists for:
      a runbook that must never be answered from a cached copy sits in the same
      corpus as a spec that may.

    The same `min(configured, declared)` shape as `max_parallel`, and for the
    same reason: a declaration may lower a bound, never raise it.

12. **A `ttl` of 0 also suppresses the cache WRITE, not just the read.** A copy
    that is written and never read is a copy of an access-controlled document
    sitting on disk for no benefit — which is the L2 cost with none of the L2
    payoff.

13. **The URL list is read only when the caller has already opted into
    caching.** With the default policy nothing is opened, so the common path
    costs no file read and gains no new failure mode. When the caller *has*
    opted in, a malformed URL list raises exactly as it does in `fux ingest` —
    a file that exists and is wrong is the case a loader refusal is for
    ([ADR-DOTFUX](0003_fux-directory.md)).

14. **`.fux/refusals.toml` and `.fux/acquired/` do not participate in a
    verdict.** A refusal is caught before the bytes are retained, so a refusal
    page can never become an `as-ingested` comparison.

**Output — the same query, the same offline fetcher, with and without the
retained bytes.** This is the whole record in one block:

```console
$ # with .fux/acquired/ populated
  verdict : as-ingested
  current : True
  note    : https://intranet/deploy-runbook: fetcher raised RuntimeError: could not resolve host …
  quoted  : 1 citation(s) quoted

$ # with the plane empty
  verdict : unverified
  current : None
  note    : https://intranet/deploy-runbook: fetcher raised RuntimeError: could not resolve host …
  quoted  : 0 citation(s) quoted
```

The second is what every offline citation used to be. The first is a citation
that can still be quoted, with an honest label on how much it is worth.

**Output — decision 11's arithmetic, every case:**

```console
    policy   line ttl=   effective   what it means
--------------------------------------------------------------------------
         0           -           0   default policy, no line   -> cache off
         0       86400           0   default policy, ttl=24h   -> STILL off (cannot widen)
      3600           -        3600   opted in, no line         -> policy stands
      3600         900         900   opted in, ttl=15m         -> narrowed
      3600           0           0   opted in, ttl=0           -> this URL always goes out
       300       86400         300   opted in, ttl=24h         -> capped at the policy
```

⚠ **A per-document verdict is now the COMMON case on `answer`, not the edge
(W-108, 2026-09-05).** `refer()` is called with three candidates instead of
one, and `_obtain`'s two `as-ingested` fallback points and its `unverified`
degradation now run **per candidate within a single answer**. One `url:`
citation that cannot be fetched costs its own citation; the other two documents
still answer. Nothing in this record's arithmetic changed — `min(policy,
declared)` and the six labels are untouched — but the vocabulary is now used
several times per answer, and a bundle can carry three different labels at once.

🔴 **Consequence a caller must not get wrong:** `citation.freshness` in
`--json` is the verdict for **the winning passage's** document. It was
`documents[0]`'s until W-108, which was the same object while there was one
candidate and is routinely a *different* one now. Reporting candidate one's
`current` beside candidate two's passage would be exactly the collapse these
six labels exist to prevent, and `query/__init__.py::_freshness_of` is where it
is prevented.

### Consequences

**Easier.** An offline or signed-out corpus keeps answering, with citations that
say exactly what they are worth. A per-document check interval becomes a
one-word edit on a line in a committed file, reviewable in a diff, rather than a
caller-side argument nobody can see.

**Harder.** Six labels is more than four, and every consumer of the bundle —
`ask --why`, `answer --receipt`, `fux verify`, the MCP result, `output.schema.json`
— has to know all six. The schema's enum is the machine-checked half of that;
`tests/refer/test_refer_acquired.py::test_the_output_schema_carries_the_sixth_verdict`
asserts the prose no longer says *four-state*.

**Owed, and filed in [`work/OPEN-WORK.md`](../../work/OPEN-WORK.md):**

- **`fux doctor` does not report the `as-ingested` share**, which is
  [ADR-ACQUIRED](0050_acquired-plane.md)'s veto check as well as a useful
  number in its own right. Until it does, neither record's veto can be run.
- **`ttl=` bounds the TTL fetch cache and nothing else.** It does not yet
  influence which URLs `fux daemon` sweeps first, which is the other place a
  per-URL interval obviously belongs.

### Alternatives considered

- **Reuse `unverified` for the retained-bytes case.** The cheapest option, and
  wrong under decision 2: it would report a real comparison as no comparison,
  and the whole point of the plane is that the comparison happened.
- **Report the retained-bytes match as `current`.** Rejected harder, and in the
  other direction. It is the exact failure the three-state shape was built to
  prevent — a claim about the world made from bytes that never left the disk.
- **A mismatch against retained bytes reported as `stale`.** Rejected by
  decision 5. It reads naturally and sends the reader to the wrong system: the
  source is fine, the record is not.
- **`ttl=` overrides the caller's policy outright.** The obvious reading of "a
  line wins", and it silently defeats W-60 verdict F: `ttl` defaults to `24h` on
  every line, so a caller who never opted into caching would start being served
  cached bytes as soon as anyone added a URL. Rejected by decision 11 — and the
  `min` is why the default value is harmless rather than load-bearing.
- **`max_age_seconds` on the policy.** Rejected before this record, and the
  argument still stands: the committed record carries no ingest time, so an age
  bound could not be honoured. `ttl=` is not that knob wearing a new name — it
  bounds *how long a check may be skipped*, which is a wall-clock question the
  TTL store is already the one place allowed to answer.
- **Storing `ttl` resolved to seconds on `UrlEntry`.** Rejected by decision 9:
  the value round-trips into a committed file, and rewriting a consumer's `1h`
  as `3600` behind their back is the kind of diff that makes people stop
  trusting the tool.

### Reference (required)

- [`src/fux/refer/freshness.py`](../../src/fux/refer/freshness.py) — the six labels, and the `max_age_seconds` refusal this record does not undo
- [`src/fux/refer/source.py`](../../src/fux/refer/source.py) — `from_acquired`, and decision 6's imported-never-reimplemented rule
- [`tests/refer/test_freshness_ttl.py`](../../tests/refer/test_freshness_ttl.py) · [`tests/refer/test_refer_acquired.py`](../../tests/refer/test_refer_acquired.py) · [`tests/refer/test_ttl_resolution.py`](../../tests/refer/test_ttl_resolution.py) — 45 tests, including the four that pin decision 11's arithmetic
- [ADR-ACQUIRED](0050_acquired-plane.md) — the plane the fourth verdict reads from
- [ADR-CACHE](0034_cache.md) — the TTL store `ttl=` bounds, and the argument for keeping two caches provably separate

### Veto condition

**Reopen this decision if:** `as-ingested` exceeds a quarter of verified `url:`
citations on a corpus whose sources are all reachable. That would mean the
verdict is masking a broken fetch path rather than covering a rare one, and the
fix is the fetch path, not a wider vocabulary.

**How to check it:** `fux doctor --json` — the `as-ingested` count against total
verified citations.

> ⚠ **No output block for this check yet, and that is a debt rather than an
> oversight.** `fux doctor` does not report the count, so the check cannot be
> run today; it is filed in *Consequences* above and shares its fix with
> [ADR-ACQUIRED](0050_acquired-plane.md)'s identical veto.
> [`docs/adr/TEMPLATE.md`](TEMPLATE.md) is explicit that an invented transcript
> is worse than none — capture it when doctor reports the number.

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-DOTFUX](0003_fux-directory.md) ·
[ADR-URL-LIST](0018_url-list.md) · [ADR-FETCHER](0019_fetcher.md) ·
[ADR-REFER](0030_refer-plane.md) · [ADR-CACHE](0034_cache.md) ·
[ADR-PROVENANCE](0046_provenance.md) · [ADR-ACQUIRED](0050_acquired-plane.md) ·
[ADR-REFUSAL](0051_refusals.md)

**Code**

- [`src/fux/refer/freshness.py`](../../src/fux/refer/freshness.py)
- [`src/fux/refer/source.py`](../../src/fux/refer/source.py)
- [`src/fux/refer/__init__.py`](../../src/fux/refer/__init__.py)
- [`src/fux/ingest/sourcelist.py`](../../src/fux/ingest/sourcelist.py)
- [`src/fux/ingest/urlsrc.py`](../../src/fux/ingest/urlsrc.py)
- [`src/fux/config.py`](../../src/fux/config.py)
- [`src/fux/query/output.schema.json`](../../src/fux/query/output.schema.json)

**Tests**

- [`tests/refer/test_freshness_ttl.py`](../../tests/refer/test_freshness_ttl.py)
- [`tests/refer/test_refer_acquired.py`](../../tests/refer/test_refer_acquired.py)
- [`tests/refer/test_ttl_resolution.py`](../../tests/refer/test_ttl_resolution.py)

**Work**

- [`archive/open/W-98-acquired-plane.md`](../../archive/open/W-98-acquired-plane.md) — the item that produced this record, **named and not cited**: it was archived on 2026-09-01 when all four phases landed, and two of its own claims were wrong
