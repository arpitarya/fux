---
type: OpenItem
id: W-83
title: "W-83 — the unconfigured fetch ceiling: the knob exists, the default is wrong, and fux.toml never mentions it"
description: "W-82 §3.3 shipped `[sources.url] max_parallel` and it works. Two things it did not do: an unconfigured repo inherits http.py's declared MAX_PARALLEL = 8 rather than the politeness default the code itself documents, and `fux setup` writes a fux.toml that names every other [sources.url] key and omits this one. Arpit, 2026-08-26: the number of parallel requests must be a stated property, or an update over a large URL list is a DDoS with a version number. CLOSED the same day — and the finding that outlives it is that ADR-CONFIG had already specified the right behaviour, in a sentence contradicting another sentence four paragraphs above it."
status: closed
lane: agent
timestamp: 2026-08-26T00:00:00Z
---

# W-83 — the unconfigured fetch ceiling

> ## ✅ CLOSED 2026-08-26. Built, recorded, and one finding revised the item itself.
>
> **The correction that arrived during the build, and it inverts §3's framing.**
> §3 below was written expecting to *change* an accepted record. It did not.
> [ADR-CONFIG](../../docs/adr/0014_config.md)'s W-82 amendment **already said**
> *"default `4` when a fetcher declares more"* — and, four paragraphs earlier,
> *"`None` means whatever the fetcher declares."* **Two sentences in one
> amendment, contradicting each other**, and the code implemented the wrong one.
> So this was not a behaviour change against a record; it was **the code being
> brought into line with a record that already specified it**, plus the repair
> of the sentence that disagreed.
>
> ⚠ **What that says about Law zero.** The freshness gate checks that a record
> was *touched*, never that it is *coherent*. A record can be amended and
> self-contradicting in the same commit and every mechanical check fux has will
> pass. That is a governance gap, it is **not fixed here**, and it is stated so
> a later session finds it rather than rediscovers it.
>
> **Outcome:** [`IMPLEMENTATION.md`](../IMPLEMENTATION.md). **Records:**
> ADR-CONFIG · ADR-FETCHER · ADR-DOTFUX, all amended in the same change.

**Model: Sonnet.** The design call is made below and the definition of done is
mechanical; what is left is an edit to one function, one template, one doctor
line, and the tests and records that go with them. The one judgement — *is the
unconfigured default the fetcher's capability or fux's politeness* — is §2, and
it is decided in this document rather than in the build.

**Records:** [ADR-CONFIG](../../docs/adr/0014_config.md) (the key) ·
[ADR-FETCHER](../../docs/adr/0019_fetcher.md) (the declaration it is combined
with).

---

## 1 · What is already true — reconcile before reading further

**The knob exists and is not the gap.** W-82 §3.3 shipped in `2.0.0-alpha.2`
([commit `8ee9fb8`](../IMPLEMENTATION.md)):

| already shipped | where |
|---|---|
| `[sources.url] max_parallel`, parsed and validated (`< 1` refuses, non-int refuses) | `config.py` |
| `min(declared, configured)`, clamp-down-loudly on capability, warn-never-clamp on policy | `ingest/urlsrc.resolve_parallel` |
| a `ThreadPoolExecutor` bounded by that number, results re-sorted so L3 is untouched | `ingest/urlsrc._fetch_group` |
| `MAX_PARALLEL = 8` on the shipped `http.py`, `MAX_PARALLEL = 1` on `cdp.py` | `templates/*.py.txt` |
| every networked verb routed through it — `fux add <URL>`, `fux update`, `fux ingest --refresh-urls` all call `fetch_all(..., max_parallel=config.url.max_parallel)` | `ingest/run.py:174` |

**`fux build` is not on this list and never will be.** It rebuilds the derived
accelerator from bytes already committed — no socket is opened, so there is no
number to cap. Saying so here is cheaper than a future session re-deriving it.

**The refer plane fetches cited documents one at a time**, in a `for` loop over
candidates (`refer/__init__.py`). That is already the politest possible
behaviour and is out of scope; it is named so nobody "fixes" it into a pool
without a decision.

---

## 2 · The two defects

### 2.1 · The documented default is not the effective default

`ingest/urlsrc.py` carries this, and has since the day §3.3 landed:

```python
#: Politeness default for `[sources.url] max_parallel` (W-82 §3.3).
#: **A judgement, not a measurement** — low enough to be polite to a single
#: intranet host without configuration, high enough that the difference from
#: sequential is immediately visible.
DEFAULT_MAX_PARALLEL = 4
```

**Nothing references it.** `resolve_parallel(module, None)` returns `declared`,
and the shipped `http.py` declares `8`. So the actual behaviour of an
unconfigured repo running `fux update` over 500 URLs is **eight concurrent
connections to one intranet host**, while a constant in the same file states
the default is four and explains why four is the polite number.

This is the failure class [CLAUDE.md](../../CLAUDE.md) §"Ground truth over
prose" names: **a wrong constant that reads as authority.** A session grepping
for the default finds `4`, believes it, and is wrong.

### 2.2 · The knob is not in `fux.toml`

`fux setup` writes a commented `[sources.url]` block naming `fetcher`,
`urls_file`, `meta` and the `[sources.url.config]` pass-through table — every
key **except** this one. `config.py` reads `max_parallel` perfectly well; there
is simply no way to discover it short of reading the engine's source.

Arpit's ask is this sentence exactly: *"expose that property in the fux.toml
file."* A knob nobody can find is not a knob.

---

## 3 · The decision

**Unconfigured means `min(declared, DEFAULT_MAX_PARALLEL)` — fux's politeness
wins over the fetcher's capability when the consumer has said nothing.**

The reasoning, and it is the same shape as the capability/policy split
`resolve_parallel` already makes:

- **`MAX_PARALLEL` answers *what is safe*.** `http.py`'s `8` is a true
  statement about `http.py` — a fresh `Request` per call, no shared
  connection. It is not, and was never meant to be, a claim about what the
  consumer's wiki can absorb.
- **Nobody declared 8 for this repo.** Silence is not consent to the maximum a
  library author found technically sound. The safe reading of silence is the
  polite one.
- **The knob still raises it.** `max_parallel = 8` gets 8, with no warning
  (8 ≤ declared, 8 < the 16-connection note). *State the cost, don't clamp the
  knob* is untouched: what changes is only what **saying nothing** means.
- **It can only ever lower, never raise.** `min(declared, 4)` — a fetcher
  declaring `1` still gets `1`, so `cdp.py`'s one-WebSocket hazard is as
  protected as it was.

⚠ **This is a behaviour change to an accepted record**, not a bug fix dressed
as one. ADR-CONFIG currently says *"`None` means whatever the fetcher
declares"*; that sentence becomes false and is amended in the same change
(Law zero). ADR-FETCHER's `MAX_PARALLEL` section gains the sentence that a
declaration is a **ceiling on what a consumer may ask for**, never a floor on
what fux will do unasked.

### The fork this leaves for Arpit — named, not silently taken

**Is `4` the right number?** It is a judgement with no measurement behind it,
exactly as its own docstring admits, and this item does not pretend otherwise.
It is cheap to change (one constant, one template line). What is *not* free is
the alternative shape — a per-host rather than a global cap — which is a real
design question and is **out of scope here**:

> `max_parallel` bounds concurrent fetches **per fetcher group**, and a group
> is all URLs resolving to one fetcher file — not one host. A list spanning
> twenty hosts through `http.py` gets four in flight *in total*, which is
> politer than necessary; a list of five hundred URLs on **one** host gets
> four, which is the case this bound exists for. The conservative direction is
> the one that is wrong here, so it ships, and per-host stays unbuilt.

---

## 4 · Definition of done

1. `resolve_parallel(module, None)` returns `min(declared, DEFAULT_MAX_PARALLEL)`;
   `resolve_parallel(module, n)` is unchanged.
2. `fux setup` writes `max_parallel` into the commented `[sources.url]` block,
   with the effective default and the one-line reason.
3. `fux doctor`'s URL section states the concurrency policy in force, **without
   importing consumer code** — doctor may not run a fetcher module to read a
   constant off it, so it reports what `fux.toml` says and names `min(...)` as
   the rule rather than computing the product.
4. `tests/ingest/test_url_parallel.py` covers the new unconfigured value; the
   existing assertion `resolve_parallel(_fetcher(declared=8), None) == 8` is
   **updated with a comment saying it changed and why** — a flipped assertion
   with no note is how the next session concludes the test was always wrong.
5. `tests/test_setup.py` asserts the key is in the written `fux.toml`;
   `tests/test_doctor.py` asserts the reported line.
6. ADR-CONFIG and ADR-FETCHER amended **in the same commit**.
7. `uv run pytest -q tests` green.

## 5 · Hazards

- **Do not import a fetcher inside `doctor`.** Consumer code with a
  module-level side effect would run on `fux doctor`, which is meant to be the
  safe command.
- **`_fetch_group` must stay sequential at `workers == 1`.** The `<= 1` branch
  is not an optimisation, it is what keeps a `cdp`-style fetcher off a pool
  entirely.
- **Nothing here may touch the trailing sorts in `fetch_all`.** They are what
  makes concurrency invisible to L3.
