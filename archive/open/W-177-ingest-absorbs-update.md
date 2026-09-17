---
type: Handoff
name: W-177
description: "`fux update` is deleted and its whole surface moves onto `fux ingest`: one verb for the first ingest and every re-ingest, dirs and URLs alike. A bare `fux ingest` fetches stale URLs (Arpit, 2026-09-15), so the default verb becomes networked; the daemon fetches and the git hooks do not; `--all` is renamed `--refetch-all` to stop it reading as a synonym of `--full`. Reverses W-63 decision 3."
item: W-177
filed: 2026-09-15
ball: agent
---

# W-177 — `fux ingest` absorbs `fux update`; the verb is deleted

**Model: Opus.** Same three reasons W-63 carried, all still true: it **moves the
L4 fence** onto the default verb; it **retires a shipped verb from a released
package** (`fux-engine` 2.0.0 is on PyPI and npm); and the
bare-`ingest`-fetches call is a judgement no test catches if it is decided
wrongly. The flag renames are Sonnet work once the seam is cut.

## The ruling (Arpit, 2026-09-15, Cowork)

> *"Remove `fux update` completely. I want `--check` to be there in ingest as
> well. `--all`, `--failed`. Everything that is there in update, move it to
> ingest. The first time you ingest something you'll be using `fux ingest`; next
> time when you're trying to update something you'll still be using `fux
> ingest`, be it for directories, be it for URLs."*

Three forks put to him in the same exchange and ruled:

1. **A bare `fux ingest` goes to the network** and fetches the URLs known to be
   stale. Narrow-by-default survives the move — W-82 ruling 3 is about which
   URLs, not which verb, and nothing here reopens it.
2. **The daemon fetches; the git hooks do not.** Split by caller, not by flag
   default: the freshness daemon is the thing whose job *is* freshness; a commit
   hook stays local-only. The hook's invocation names its own opt-out
   explicitly — see open question 1.
3. **`--all` is renamed `--refetch-all`.** On `update` it sat alone; on `ingest`
   it lands beside `--full`, and *all* and *full* read as synonyms while one
   selects URLs and the other re-extracts documents.

## What this reverses, and why that is legal

[W-63](../../archive/open/W-63-source-verbs.md) **decision 3** (Arpit,
2026-08-21) folded `fux ingest --refresh-urls` into `fux update` so the engine
would have exactly two networked paths, *both explicitly named*. This reverses
that: the paths become `fux add <URL>` and `fux ingest`.

**No law changes.** [SR-LAW-4](../../records/0006_LAW-4-offline-by-default.md)
says *paths*, plural, and states in terms that **the count was never part of the
law** — its own §"The narrowing that already happened once" is the record of
exactly this mistake being made before. So:

- ⚠ **Do not edit the law block.** `CLAUDE.md` §Non-negotiable constraints is
  generated; if a diff appears there, something has gone wrong.
- **Do edit SR-LAW-4 §1's two-row table**, which names `fux update` as a path.
  That is rationale prose, not the law.

⚠ **What the move does cost:** `fux ingest` is today offline *by construction*
and the import fence asserts the modules on its path cannot import a transport.
After this it cannot be. The fence does not disappear — it moves to whatever
`ingest` calls when it is **not** fetching, and the item is not done until a
test pins that a hook-invoked ingest opens no socket.

## Definition of done

1. **`fux update` is gone** — parser, `_cmd_update`, and the row in
   [SR-CLI](../../records/0101_cli-surface.md) §1's **sources** group. No
   deprecation alias: W-63 deleted `fux url` outright and kept
   `--refresh-urls` only because it was older and likelier to be in CI; this
   verb is three weeks old and the same argument does not reach it.
   ⚠ **`ingest --refresh-urls`** (hidden, `argparse.SUPPRESS`, kept one release)
   is now the *default behaviour* of the verb it sits on. Delete it; a hidden
   flag that silently means "what already happens" is worse than none.
2. **Every `update` flag lands on `ingest`**, with its record:
   | on `update` today | on `ingest` | owned by |
   |---|---|---|
   | *(bare)* | *(bare)* — fetch stale URLs | SR-INGEST, SR-URL-INGEST |
   | `--all` | **`--refetch-all`** | SR-URL-INGEST |
   | `--failed` | `--failed` (`fail_streak > 0`; still beats `--refetch-all`) | [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) |
   | `--check` | `--check` — read-only, offline, exit 0 always | SR-INGEST |
   | `--json` | `--json` (drift report) | SR-OUTPUT decision 15 |
   | `<entry>` | positional `<entry>`, one listed entry | SR-CLI |
3. **`--check` and `--list-skipped` are now two exit-early flags on one verb.**
   Both are read-only and offline and both print-then-exit. Rule which wins when
   both are given, in SR-INGEST, and test it — *do not leave it to argparse
   order*.
4. **The hook/daemon split is structural, not conventional.** `fux hooks`
   writes the offline invocation; `fux daemon` writes the fetching one; a test
   asserts a hook-path ingest opens no socket. `--spawn-runner` / `--runner`
   inherit whichever side spawned them.
5. **Pinned lines still never fetch.** `update=never` is a property of the line
   ([SR-URL-LIST](../../records/0116_url-list.md) decision 14), so it survives
   the verb change untouched — including under `--refetch-all`. Keep the test.
6. **The transient-failure guarantee survives.** A listed URL whose fetch fails
   keeps its prior record; exit is `0`; stderr carries
   `! <url> — <reason>; prior record kept`.
7. **A surface capture** filed under [`../regression/`](../regression/README.md),
   the way W-63's was, and **both suites green, whole**.

## Blast radius (measured 2026-09-15, not estimated)

- **13 modules** name `fux update`: `cli.py`, `config.py`, `sources.py`,
  `doctor.py`, `setup.py`, `ingest/{run,urlsrc,skipnotice,__init__}.py`,
  `maintain/{dirty,urlstate,daemon}.py`, `store/fuxdir.py`.
- **11 test files**, including `tests/test_update_narrow.py` and
  `tests/test_url_update_policy.py` (whose names go with the verb) and
  `tests/maintain/test_daemon_sweep_reaches_ingest.py` (which is now the
  hook/daemon split's test, not a smoke test).
- **17 records**, of which four carry more than a mention: SR-CLI (0101),
  SR-INGEST (0106), SR-URL-INGEST (0107), SR-URL-FRESHNESS (0147). Then
  SR-LAW-4 (0006) §1's table, SR-MAINTENANCE (0129), SR-URL-LIST (0116),
  SR-INDEX-LIFECYCLE (0108) — whose repair message names `fux update` as *"the
  only thing that can rebuild them"* — SR-DOTFUX, SR-CONFIG, SR-DOCTOR,
  SR-FETCHER, SR-CDP-FETCHER, SR-HTTP-FETCHER, SR-OUTPUT, SR-AGENT-POLICY,
  SR-ACQUIRED.
- **6 shipped agent skills** — `fux-sources` (§1 table and all of §5),
  `fux-maintain` (§5 is `update --check`), `fux-index`, `fux-config`,
  `fux-fetcher`, `fux-pii` — plus `docs/GLOSSARY.md` and `docs/handbook.html`.
- ⚠ **`fux-sources` and `fux-maintain` are split along the seam this deletes.**
  `update` is a sources verb in one and a maintenance verb in the other. Once
  it is `ingest`, ask whether the two skills still divide where they should —
  that is a question for Arpit, not a rewrite to perform.

## ✅ Open questions RULED 2026-09-15 (Arpit, Cowork)

1. **The hook's offline invocation is `fux ingest --no-fetch`** — option (b).
   Same flag, same meaning as `fux add --no-fetch`; one SR row covers both. It
   is a public surface flag, so CI and air-gapped clones can ask for an offline
   ingest by hand. `fux hooks` writes it; `fux daemon` writes the bare verb. The
   L4 fence test asserts an ingest invoked with `--no-fetch` imports no transport
   and opens no socket. No `--offline` alias.
2. **`fux doctor` remediation strings are reworded to name `fux ingest`**
   (`fux ingest --check` for the freshness row). The report shape is unchanged.
3. **The rename rides 3.0**, not a 2.1 patch — 3.0 is already the breaking
   release. CHANGELOG carries a breaking-change block naming `fux update` →
   `fux ingest` and `--all` → `--refetch-all`.

The three questions as originally filed are kept below for the record.

## Open questions as filed — now ruled above

1. **What does the hook's offline invocation look like?** `fux ingest
   --offline`, `--no-fetch` (which `fux add` already uses for a URL line), or a
   non-surface flag like the runner pair. `--no-fetch` reads best and is the
   name already in the surface; it is still a ruling.
2. **Does `fux doctor` still report URL freshness the same way** when the verb
   it points at is the one that also re-indexes? Its remediation strings name
   `fux update`.
3. **`fux ingest --check` vs `fux update --check` in CI.** The skills tell
   people to gate on the *output*, never the exit code, and that does not
   change — but anyone's pipeline breaks on the verb rename. Does this ride a
   `2.1.0` with a CHANGELOG breaking-change block, or wait for `3.0`?

## Out of scope

- Which URLs count as stale. W-82 ruling 3 stands untouched.
- `fux add`'s one fetch. Unchanged; it stays the second named networked path.
- `fux build`. Offline, derived, unaffected.
- Any change to `.fux/sources/*` grammar. Nothing here needs one.
