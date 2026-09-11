---
name: fux-maintain
description: Keep a Fux index current — `fux hooks` and the fux-merge-index driver, `fux daemon start|stop|status`, `fux update --check`, the background re-index, and resolving a merge conflict in .fux/index without hand-editing. Use for "keep the fux index up to date automatically", "install fux hooks", "are hooks wired", "start the freshness daemon" or "merge conflict in .fux/index". Installing hooks or starting the daemon — only when explicitly asked.
---

# Keeping the Fux index current

The committed index goes stale the moment content changes, and conflicts
whenever two branches touch the same shard. **Hooks** handle local edits,
**the daemon** handles URLs nobody queries, and **the merge driver** handles
branches.

Resolve the `fux` command first — see the `fux-usage` skill (`fux` → `uv run fux` → `./.venv/bin/fux`, on Windows `.venv\Scripts\fux.exe` → `python -m fux`).

> ⚠ **`fux hooks` writes into `.git/hooks/`, `.git/config` and `.gitattributes`;
> `fux daemon start` leaves a process running that fetches every listed URL.**
> Only when a human asked. Status reads (`--json`) are always safe.

---

## 1 · Pick the job

| the ask | what to do |
|---|---|
| "are hooks wired" | `fux hooks --json` — §2 |
| "install fux hooks" / "keep it up to date automatically" | `fux hooks`, then verify with `--json` — §2, §3 |
| "start the freshness daemon" | `fux daemon start` — §4 |
| "is the index stale" | `fux update --check` — §5 |
| "merge conflict in .fux/index" | §6. Never edit the JSONL |
| "check it in CI" | §7 |

---

## 2 · `fux hooks` — the wiring

| command | does |
|---|---|
| `fux hooks` · `fux hooks --install` | writes the three hooks and registers the merge driver |
| `fux hooks --status` | prints what is wired |
| `fux hooks --json` | the same, machine-readable — **and installs nothing** |
| `fux hooks --uninstall` | removes only what fux wrote |

| hook | runs | effect |
|---|---|---|
| `post-commit` | `fux ingest --spawn-runner` | records the commit's changed paths, spawns a detached re-index, **returns at once** |
| `post-merge` | `fux ingest` inline | re-derives the index from the merged content |
| `post-checkout` | `fux build` | refreshes only the derived accelerator |

**Plus the merge driver:** `merge.fux-index.driver = fux-merge-index %O %A %B`
in the repo's **local** git config, and this line appended to `.gitattributes`:

```
.fux/index/*.jsonl merge=fux-index
```

```json
{"gitattributes": true, "hooks": {"post-checkout": "fux", "post-commit": "fux", "post-merge": "fux"}, "merge_driver": "fux-merge-index %O %A %B"}
```

**Wired means all three hooks are `"fux"`, `merge_driver` is not
`"unregistered"`, and `gitattributes` is `true`.** A hook reads `"other"` when
a file exists that fux did not write.

- **Never clobbers.** A hook without fux's marker line is left alone and
  printed as `REFUSED <hook>`; **exit is still 0**, so check `--json`. Ask
  the user: move their hook aside and re-run, or call `fux ingest` from it.
- **`--uninstall`** deletes marked hooks and the `merge.fux-index` config
  section, and **leaves `.gitattributes` alone**.
- **Nothing here is cloned.** Every teammate runs `fux hooks` once; commit the
  `.gitattributes` line so their merges use the driver.

⚠ **Hooks do nothing when `fux` is not on the PATH git runs them with.** Each
starts `command -v fux >/dev/null 2>&1 || exit 0`, so a fux inside an
unactivated `.venv/` gives hooks that silently skip. Same for the driver: the
merge prints `fux-merge-index: not found` and falls back to a plain conflict.

⚠ **If `.fux/output.toml` turns JSON on by default** (`[cli.json] enabled = true`),
a bare `fux hooks` only reports. Use `fux hooks --install --no-output-config`.

---

## 3 · What happens after each commit

1. `git commit` → stderr: `fux: re-indexing in the background (N changed path(s) pending)`.
   **No such line means the hook did not run** — see the PATH pitfall above.
2. The detached runner takes `.fux/runtime/write.lock`, re-ingests, and exits.
   **It rewrites `.fux/index/` in the working tree and commits nothing.**
3. **Commit `.fux/index/`, `.fux/.fuxignore` and `.fux/enrich/` as a follow-up commit.** The
   index lags content by one commit on purpose: a `post-commit` index never
   captures half-staged work.
4. **The background run does not rebuild the accelerator** — run `fux build`
   (`ask` stays correct meanwhile; `graph`/`explain`/`path` need it).

**Watch it with `fux doctor --json`** — the `runner` block:

| field | values |
|---|---|
| `running` · `pid` | a live re-index and its pid |
| `lock` | `free`, `held`, or `stale` — a killed runner left its lock |
| `pending` | changed paths not yet re-indexed |
| `last_run` | `null` or `{outcome: ok\|stopped\|failed, …}`; `failed` carries `error` |

- **`fux ask` says so on stderr** while work is pending: `fux: N changed path(s) pending re-index`.
- **An explicit write wins.** `fux ingest`, `add`, `remove` and `update` stop a
  live runner cooperatively, then run. `fux ingest --stop` stops it without
  running and clears a stale lock.
- **`fux answer` remembers what it cited.** A repeat prints
  `note: nothing has changed since you last asked this.` or which sources moved.
  A report on stderr, never a replayed answer.
- **No hook ever touches the network.** A URL line added by hand waits for
  `fux update` or the daemon.

---

## 4 · `fux daemon` — the URL freshness clock

**Answer-time checks only reach URLs someone asks about. The daemon re-fetches
the rest on a timer.** It lives in the repo — started with the current
interpreter, never installed as a service, never started by setup or hooks.

| command | does | exit |
|---|---|---|
| `fux daemon start` | spawns it; sweeps now, then every `[sources.url] sweep_minutes` (default 60) | 0, also when already running |
| `fux daemon` · `fux daemon status` | what it is doing; add `--json` | 0 |
| `fux daemon stop` | asks it to stop at a safe point — never kills | 0; **1 if it has not exited within 30 s** |

```json
{"running": true, "pid": 4242, "last": {"outcome": "ok", "fetched": 5, "skipped": 2, "reason": "2 skipped, first: ..."}}
```

- **`last.outcome`** is `ok`, `busy` (another writer held the lock — not an
  error), `failed` (`reason` carries the exception) or `stopped`. `last` is
  `null` before the first sweep.
- ⚠ **`skipped` is not a failure count** — it includes files the lists exclude and
  pinned URLs. For URLs that failed, read `reason` and the `url sources` row of
  `fux doctor --json`.
- Each sweep takes the same `write.lock`, re-fetches every listed URL except
  `update=never` lines, and **writes `.fux/index/` directly** — commit it like
  a hook's output. Sweeps do not rebuild the accelerator.

---

## 5 · `fux update --check` — drift, read-only

```bash
fux update --check            # or: fux update --check docs/rollback.md
fux update --check --json     # {"drifted": [...], "fresh": N, "unchecked_urls": N}
```

**Offline, and it writes nothing.** Each indexed file's bytes are compared with
its record: `stale <loc> index xxxx… · disk yyyy…`, `gone <loc> indexed, not on disk`,
then `N stale.` or `nothing has drifted.` URL documents are counted on stderr, not checked.

⚠ **Always exit 0 — in `--json` too — and blind to files not yet indexed.**
Exit 0 is deliberate: drift is a fact, and a non-zero exit would make *your docs
changed* look like a broken command to every script that checks status. **Read
`drifted` in the JSON**, or treat any `stale`/`gone` line as drift; for a yes/no
gate use §7.

**Reconcile with `fux update`** — it re-ingests and re-fetches only URLs
recorded as changed (every URL when nothing is recorded yet); `--all` fetches
all. It touches the network — see `fux-sources`.

---

## 6 · Merge conflict in `.fux/index/`

**The driver merges shards record by record:** one-sided adds union, a
deletion beats an untouched side, a side identical to the ancestor yields,
higher `ver` wins. **It refuses** — conflict markers, exit 1,
`fux: cannot merge <shard>` — when one document changed on both sides at the
same `ver`, a delete races an edit, or both added it differently. A shard also
conflicts when the driver is unregistered, not on PATH, or both branches
created the same shard file.

⚠ **`fux ingest` cannot read a shard with conflict markers** — it stops with
`carries unresolved merge conflict markers`, which is what the driver's own
refusal tells you to expect. **Take one side whole first**, then let ingest
re-derive:

```bash
# 1. resolve and `git add` the content conflicts (docs, .fux/sources/*) first
shards=$(git diff --name-only --diff-filter=U -- .fux/index)
git checkout --ours -- $shards && git add $shards
# 2. conclude the merge when the human is ready — ingest AFTER the merge commit,
#    so record mtimes see history from both branches
fux ingest                      # rewrites every record from the merged content
git add .fux/index .fux/.fuxignore .fux/enrich   # commit when asked
```

- **Which side you keep does not matter for file documents** — ingest
  re-derives them. For a `url:` record the kept side stands until the next `fux update`.
- **`post-merge` does not run on a conflicted merge** — the manual `fux ingest` is the only re-index.

---

## 7 · CI — prove the committed index is current

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0            # record mtimes come from git history
# install the fux-engine package the way this repo installs its other tools
- run: fux ingest --no-accelerator --no-progress
- run: test -z "$(git status --porcelain -- .fux/index .fux/.fuxignore .fux/enrich)"
```

- **A shallow clone changes every record's `mtime`** and fails this check falsely.
- **Commit content first, then the index** — the order §3 produces. An index
  ingested before the content commit is one commit behind and fails too.
- **CI never installs hooks or starts the daemon.** Nothing in CI needs the network.

---

## Don't

- **Don't hand-edit or line-splice `.fux/index/*.jsonl`** — a spliced record is one no ingest produced.
- **Don't run `fux ingest` on a shard that still holds conflict markers** — check out a side first.
- **Don't install hooks or start the daemon unasked.**
- **Don't trust `fux hooks` exit 0** — `REFUSED` lines exit 0 too. Read `--json`.
- **Don't delete `write.lock` while a runner or daemon is alive** — `fux ingest --stop` is the safe clear.
- **Don't kill the daemon** — a kill mid-write can leave a partial shard. Use `fux daemon stop`.
- **Don't gate CI on `fux update --check`'s EXIT CODE** — it is always 0. Gate
  on `--json`'s `drifted` being empty, or use §7.

Related skills: fux-usage, fux-search, fux-answer, fux-graph, fux-sources, fux-index, fux-config, fux-mcp, fux-fetcher, fux-pii, fux-decoder, fux-enrich, fux-archived-results.
