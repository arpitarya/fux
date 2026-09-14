---
type: Handoff
name: W-174
description: "`[sources.url] fetch_at_answer` — a fux.toml boolean that pins every URL citation to `.fux/acquired/` at answer time. No socket opens, refer stays on, the verdict is `as-ingested`. The engine already has the mode; nothing can select it."
item: W-174
filed: 2026-09-14
ball: agent
---

# W-174 — `fetch_at_answer = false`: answer from retained bytes, never from the source

**Model: Sonnet.** A written DoD against code that already exists; the
judgment was spent naming the key, not building it.

**Ratified:** Arpit, 2026-09-14 — *"a flag in fux.toml which never reaches to
the source system, specifically for the URLs and just fetches from acquired
data. A true/false kind of configuration."* Ratified, not built.

## What is already there, and what is missing

**The mode is built.** `refer/freshness.py` ships `Policy(mode=NEVER)` —
*"do not fetch. Deterministic-replay mode"* — and `refer/__init__.py::_obtain`
already has the branch this item wants: policy forbids going out, so it calls
`from_acquired(root, doc_id, loc)` and, when the bytes are there, returns
`as-ingested` against them. That is exactly *"never reach the source, answer
from acquired"*, and it has a test.

**Nothing can select it.** `query/refer_answer.py` constructs
`Policy(mode=ALWAYS, cache_ttl_seconds=…)` literally. `NEVER` is reachable
from the Python API and from nowhere a consumer configures.

⚠ **`freshness.py`'s own docstring names three callers and the third —
*"CI, or a replayed `--audit` bundle: never"* — shipped with no way to ask for
it.** This item closes that, and the closure is a config key rather than a
flag because the caller who wants it wants it for every answer in the repo.

## The two things this is NOT, and both are already recorded

| not this | why not |
|---|---|
| **`--no-refer`** | turns the refer plane **off**: no passage re-scoring, no line ranges, no verification at all. This key keeps refer **on** and points it at `.fux/acquired/`. Opposite intent, same-sounding words |
| **`update=never`** | the **update-time** clock. [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) decision 15 states it outright: *"`update=never` still does not keep `answer` offline, and that is decision 15 working, not a defect"* |

## Definition of done

1. **New key: `[sources.url] fetch_at_answer`, boolean, default `true`.**
   `true` is today's behaviour exactly — no repo changes meaning on upgrade.
   `false` builds `Policy(mode=NEVER)` for every `url:` citation.
2. **The name states its clock**, which is the whole reason it is three words
   and not one. Decision 15 separates two clocks on one line; this is the
   missing cell of that table, and the table gains a third row:

   | attribute | when it acts | what it decides |
   |---|---|---|
   | `ttl=` | ask time | how long a citation may go **unchecked** |
   | `update=` | update time | whether fux goes back **at all** |
   | **`fetch_at_answer`** | **ask time** | whether a socket may open **at all** |

   Rejected names, recorded so they are not re-proposed: `offline` (collides
   with L4's own vocabulary and implies the whole engine), `pinned` (one word
   over both clocks — precisely the merge decision 15 exists to prevent).
3. **`fux.toml`, not `.fux/output.toml`.** [SR-OUTPUT](../../records/0143_output-defaults.md)'s
   rule holds: `[cli.*]` chooses rendering and may never decide what a verb
   does. And not `tune.toml` — it changes no committed byte, but it is policy
   about **reaching** sources, which is [SR-ACQUIRED](../../records/0145_acquired-plane.md)
   decision 8a's own test for `fux.toml`, beside `fetcher`, `meta` and
   `max_parallel`.
4. **URLs only, and `file:` is untouched.** The key sits on `[sources.url]`.
   `_obtain`'s never-branch already states why: reading the local checkout is
   not a fetch, and refusing it would make `--audit` unable to quote the
   repository it audits.
5. **Source-wide only — no line attribute, no CLI flag, in this item.**
   `UrlEntry` does not grow a sixth resolved field. Out of scope below.
6. **No retained bytes → `unverified`, disclosed and never refused**
   (Arpit's ruling, 2026-09-14). Loading `fetch_at_answer = false` in a repo
   with `keep = false` is **legal**; it is the same shape as
   SR-ACQUIRED's lossy `update=never keep=false` pair, which that record
   already resolves as a warning rather than an error.
7. **`fux doctor` row.** When `fetch_at_answer = false`, count URL lines with
   no entry in `acquired/manifest.json` and warn with the count: *every
   citation from these will be `unverified`.* Beside `_acquired_health`, which
   already reads the manifest.
8. **`--cache-ttl` becomes inert and must say so.** With no socket, the TTL
   cache can never be written or read. Passing `--cache-ttl` under
   `fetch_at_answer = false` **warns**; it does not error and does not
   silently do nothing — W-140 row 6 is the case for that, where `ttl=` was
   dead at ask time in every repo and nothing said so.
9. **The verdict matrix, as shipped:**

   | state | verdict |
   |---|---|
   | blob present, sha matches the record | `as-ingested` |
   | blob present, sha differs | `as-ingested`, with the drift in the note — the record is not what these bytes say |
   | no blob | `unverified` |
   | `file:` / git citation | unchanged — read from the checkout, `current` |

10. **The receipt and `--json` carry it.** `Policy.as_record()` already
    travels with the bundle; assert `mode == "never"` appears in the receipt
    and in `--audit`, because a replay that silently used a different policy is
    the failure that module exists to close.
11. **Records, in the same change** (Law zero):
    [SR-CONFIG](../../records/0113_config.md) decision 13's key block — the key
    is **declared** or it does not exist, and `tests/test_sr_config_keys.py`
    binds that block to `config.py`'s `KNOWN_KEYS` in **both** directions;
    SR-URL-FRESHNESS decision 15 (the third row above);
    [SR-REFER](../../records/0127_refer-plane.md) (the policy is now
    config-derived, not literal); SR-ACQUIRED (the pairing table gains the
    repo-wide form); [SR-DOCTOR](../../records/0152_doctor.md) (row 7).
12. **Both suites.** `tests/` for resolution and the doctor row; `tests_e2e/`
    for the real CLI: a repo with retained bytes, network unplugged, `fux
    answer` returns `as-ingested` and opens no socket.
13. `docs/GLOSSARY.md` and the `fux-config` / `fux-answer` guide skills.

## Open question for the builder

**The Node reader has a `refer/` plane** (`node/src/refer/freshness.mjs`,
`source.mjs`) **and its config layer reads `tune.toml` and `output.toml`, not
`fux.toml`.** Whether Node's refer path fetches at all decides whether this is
a two-reader change or a Python-only one. Settle it against
[SR-NODE-SEARCH](../../records/0153_node-search.md) before writing code, and
record the answer either way — digest-equality is the standing claim.

## Out of scope

- **A per-line `fetch_at_answer=` attribute.** SR-ACQUIRED's own test decides
  it: a source-wide layer means something when the attribute answers *"how do
  I reach these pages?"*, and this one does — so the source-wide layer is the
  right and sufficient home. A line layer needs its own argument.
- **A CLI flag that puts the socket back** (`--fetch`, `--online`). Widening
  at the call site is a different decision from narrowing in config, and
  SR-OUTPUT's rule does not settle it. **Reopen trigger:** a caller needs one
  repo to answer both ways in one session.
- **`max_age_seconds`** — still W-58, still unimplementable: the committed
  record carries no ingest time.
