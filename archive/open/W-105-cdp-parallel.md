---
type: OpenItem
id: W-105
title: "W-105 — make cdp.py genuinely parallel, then let fux.toml set each fetcher's ceiling"
description: "`MAX_PARALLEL = 1` in cdp.py is honest today, but its stated reason is stale: `fetch_resource` already opens a fresh WebSocket per call. What is actually shared is the id counter, the two message queues (cleared at the top of every fetch) and the page target — two threads drive ONE Chrome tab. Fix the sharing, give each worker its own tab, then raise the declaration and make it settable from fux.toml through a key both shipped fetchers accept."
status: open
lane: agent
timestamp: 2026-09-01T00:00:00Z
---

# W-105 — cdp parallelism, and the ceiling as a knob

**Model: Opus** for the session refactor. This is a concurrency change to a
protocol client whose failure mode is *plausible documents attributed to the
wrong URLs, in the committed index, passing every determinism check* — the one
place in this repo where a plausible-looking diff is not evidence.
**Sonnet** for the config plumbing and the ADR edits once the shape is fixed.

## The ruling this implements

**Arpit, 2026-09-01**, choosing between three shapes: *make cdp genuinely
parallel first*, then the configurability on top. The alternative — a
per-fetcher policy key that is still `min()`'d against a declared `1` — was
rejected as configuring nothing.

## The records

[ADR-FETCHER](../../docs/adr/0019_fetcher.md) — the `MAX_PARALLEL` contract and
*declared, never detected*.
[ADR-CDP-FETCHER](../../docs/adr/0020_cdp-fetcher.md) — the shipped template.
[ADR-HTTP-FETCHER](../../docs/adr/0021_http-fetcher.md) — the other one.
[ADR-CONFIG](../../docs/adr/0014_config.md) — `[sources.url.config]` and the
verbatim-passthrough rule.

## 🔴 What is actually unsafe, re-derived rather than read

The comment on `MAX_PARALLEL = 1` says *"`connect()` sets a module-global
`_session` holding ONE WebSocket that every `fetch()` reuses."* **That sentence
is stale.** `CdpSession.fetch_resource()` opens `WebSocket(target[...])` per
call and closes it in a `finally`. The socket is not shared.

What **is** shared across concurrent `fetch()` calls on one `CdpSession`:

| shared thing | what two threads do to it |
|---|---|
| `self._msg_id` | non-atomic `+= 1`; two commands get one id and `_call` returns the wrong reply |
| `self._results` / `self._events` | `fetch_resource` **clears both at the top of every fetch** — one thread wipes the other's pending replies and paused requests mid-flight |
| `self._page_target()` | returns the **first** page target found, so two threads `Page.navigate` the *same tab* |
| `self.chrome` / `ensure_chrome()` | two threads can race to launch Chrome |

⚠ **The third row is the one that produces the documented corruption.** Two
navigations on one tab, two `Fetch.requestPaused` streams into two queues that
are being cleared under each other: the bytes that come back are a real
response to a real request, just not the one the caller asked for. Note that
the *first* two rows would produce the same class of wrong answer on their own.

**So the declaration was right and its reason was wrong**, which is worse than
either — a reader fixing the WebSocket would have concluded the hazard was
gone. Record that; do not just delete the sentence.

## Definition of done

### Part A — the session refactor (this is the item)

- [ ] Per-fetch protocol state stops living on the shared session. `_msg_id`,
      `_results` and `_events` move onto a per-connection object created inside
      `fetch_resource` (or onto `threading.local()`), so no `clear()` can reach
      another thread's queues. **The `clear()` calls go away entirely** — fresh
      state per fetch is what they were approximating.
- [ ] **Each worker gets its own page target.** A worker acquires a tab on
      first use (`PUT /json/new`) and keeps it for its lifetime;
      `close()` closes every tab this module opened, and only those.
- [ ] ⚠ **A tab this module opened is a tab this module closes.** Leaking one
      per URL into a human's signed-in Chrome across a 500-URL run is a worse
      bug than the one being fixed. The set of opened target ids is explicit,
      not inferred by diffing `/json`.
- [ ] `ensure_chrome()` is guarded by a `threading.Lock` — one launch, whoever
      gets there first, everyone else waits.
- [ ] ⚠ **Behaviour change worth naming: fux stops driving a tab the human had
      open.** `_page_target()` currently returns the first existing page target
      and navigates it. Opening our own tab is strictly better and it is still
      the same Chrome profile, so the sign-in this fetcher exists for is
      unaffected. It goes in ADR-CDP-FETCHER as a decision, not a footnote.
- [ ] `MAX_PARALLEL` in `cdp.py` is raised to a **defensible** number with the
      reason written beside it — each tab is a renderer process, so this is a
      memory statement about the human's machine, not a protocol one. The
      comment stops claiming a shared WebSocket and states what was actually
      shared and what now is not.
- [ ] 🔴 **`connect()`/`close()` stay once per group, never once per worker.**
      That is `fetch_all`'s contract in
      [`urlsrc.py`](../../src/fux/ingest/urlsrc.py) and this change must not
      quietly need it loosened.

### Part B — the ceiling as a knob

- [ ] `[sources.url.config] fetcher_max_parallel` is read by **both** shipped
      templates and overrides each module's own `MAX_PARALLEL`.
- [ ] ⚠ **It has to be a key both fetchers know, and that is not a style
      choice.** `[sources.url.config]` is passed **verbatim to every fetcher**
      and each `configure()` raises on an unknown key — so a `cdp_`-prefixed
      key breaks any repo that also uses `http.py`. `cdp.py` already carries
      the warning that made its later tunables module constants; this key is
      the exception because it is the one tunable *both* files have.
- [ ] The name is **not** `max_parallel`. `[sources.url] max_parallel` is
      policy and `[sources.url.config] fetcher_max_parallel` is capability;
      two nested keys with one name is how they get confused in a bug report.
- [ ] `configure()` runs **before** `resolve_parallel()` — verified: `fetch_all`
      calls `configure_fetcher(module, config)` at the top of each fetcher
      group and `resolve_parallel(module, max_parallel)` further down the same
      block. So a `configure()` that sets the module global is picked up by
      `getattr(module, "MAX_PARALLEL", …)`. **Assert this with a test**; it is
      an ordering the two files do not state to each other.
- [ ] `resolve_parallel`'s semantics are **unchanged**: still
      `min(declared, configured)`, still clamping down loudly when policy
      exceeds capability, still `min(declared, DEFAULT_MAX_PARALLEL)` on
      silence (W-83). What changed is only where `declared` comes from.
- [ ] `fux.toml`'s comment block on `max_parallel` — which names *"1 for cdp.py
      because it reuses one WebSocket"* — is corrected. It is a shipped file and
      it will be read as authority.
- [ ] ADR-CDP-FETCHER: the sharing analysis, the own-tab decision, the new
      declared number and why. ADR-FETCHER: `MAX_PARALLEL` may be set from
      `[sources.url.config]`, still declared by the fetcher, still never
      detected by fux.

## Hazards

- 🔴 **Nothing in the test suite can catch the failure this fixes.** The
  corruption is a real response attributed to the wrong URL; the index sort
  still runs, determinism still holds, every mechanical check stays green. The
  only proof is a run against a real Chrome with several URLs at once,
  asserting each record's `loc` matches its content. **File that run** — a
  green suite is not evidence here and this file is on record saying so.
- **Do not raise `MAX_PARALLEL` in the same commit as Part A.** Land the
  sharing fix at `1`, prove it changed nothing, then raise it. A refactor and a
  concurrency increase in one diff have no bisect point between them.
- **Chrome's own limits are not fux's to know.** A number that is fine on a
  32 GB laptop opens a swap storm on a CI box. That is precisely why the
  declaration becomes settable rather than merely larger.
- ⚠ **`validate()` uses the same session** (`want_body=False`) and runs in
  `validate_group` *before* the pool. It is sequential today; keep it that way
  unless a separate item says otherwise.

## Out of scope

Any change to `resolve_parallel`'s policy/capability split, to the W-83
silence rule, or to the `[sources.url] max_parallel` required-key ruling
(W-85). Per-host rather than per-fetcher-group bounds — named as the shape of
the thing in `urlsrc.py` and not a defect in it.
