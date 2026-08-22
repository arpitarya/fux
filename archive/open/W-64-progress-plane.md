# W-64 — a progress plane for every verb that writes

**Status:** OPEN · **Filed:** 2026-08-21 · **Lane:** `agent`
**Decided by:** Arpit, 2026-08-21 — "show progress when add, remove or update is
triggered", then "add loading for ingest and build too".
**Blocked by:** nothing, but **lands after [W-63](W-63-source-verbs.md)** —
both change `run()`'s signature and sequencing them avoids a needless conflict.
It is otherwise independent and would be worth building even if W-63 were
abandoned.
**Closes with:** [ADR-CLI](../../docs/adr/0002_cli-surface.md) updated in the
same change (a new decision on the stdout/stderr split, plus the ownership row
for `src/fux/progress.py`), and a capture filed under
[`../regression/`](../regression/README.md).
**Model:** **Sonnet.** The design decisions are made and written down below, the
definition of done is mechanical, and the one invariant that matters is
assertable in a test. Borderline only because a progress bar that leaks into
stdout would corrupt the `--json` contract — but that is exactly what the test
catches, which is what makes it Sonnet work rather than Opus work.

---

## Why this exists

R5 measured the commit-path ingest at **44.4 s at 100 000 documents**
([R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md)). Forty-four
seconds of total silence is what people report as *"git is hung"*. The engine
prints nothing between invocation and completion, at any corpus size.

**Progress belongs to the two functions that do the work** — `ingest.run()` and
`derive.build()` — not to the verbs. Every verb that calls them inherits it, and
`add`/`remove`/`update` stop being special cases.

## The four rules that decide the design

1. **stderr only, never stdout.** stderr is currently errors-only across all of
   `src/` (`cli.py:210`, `mergedriver.py:174/203`). Making it *"ephemeral UI +
   errors"* keeps stdout meaning *"the answer"*, so `--json` and every piped
   invocation stay **byte-identical** with the bar on or off. This is the
   invariant; everything else is presentation.
2. **Off when stderr is not a TTY, automatically.** Not politeness: this repo
   captures verbatim CLI transcripts as ADR evidence
   ([`../regression/2026-08-18-cli-surface/`](../regression/2026-08-18-cli-surface/report.md)).
   A bar painting into a capture would make that evidence unreproducible.
   TTY-gating means CI logs, pipes and captures are exactly what they are today
   with no flag anywhere.
3. **Counts, not clocks.** No ETA, no elapsed, no rate. CLAUDE.md's standing
   line is *"no wall-clock output anywhere on the maintenance path"* — aimed at
   committed bytes, but a bar printing `00:14 elapsed · 87 docs/s`
   re-litigates it for nothing. `412/1 203` tells a person everything they need.
4. **A count threshold, not a delay onset.** Engage a phase's bar only when its
   total exceeds ~200. A threshold needs **no timer in the code path**, which
   keeps the whole feature clock-free — and it is what stops `fux remove` (where
   almost every document is carried forward) from flashing a bar and killing it.

## Phases, and where the totals come from

Every total is knowable before its phase starts, so **no spinners are needed
anywhere** — `walk` is the only one that counts up without a denominator.

| function | phase | total from | notes |
|---|---|---|---|
| `ingest.run` | `walk` | none until done | count up; `walk_sources` returns the list |
| | `extract` | documents not in `reusable` | **the one that matters** |
| | `edges` | `len(parsed)` | re-resolved every run |
| | `write` | `len(by_shard)` ≤ 256 | |
| `derive.build` | `read` | `len(iter_shard_paths())` ≤ 256 | parse + `_assert_invariants` per line |
| | `codes` | `len(docs)` | `dense.build_codes` |
| | `graph` | `len(edges)` | `build_plane`; label propagation is the iterative one |
| | `postings` | `len(sorted(postings))` | the big one — 41 k terms at 1.2 k docs |

**`extract` is where the bar earns its place.** Profiled at 1 000 documents,
**92 % of a full ingest is `_fuxvec_code`**, the dense embedding inside
extraction ([the cost profile](../regression/2026-08-20-ingest-cost-profile/report.md)).
`fetch` earns it for a different reason: it is network-blocked and unbounded.

## One `Progress`, created in `main`

`fux ingest` already calls `build` at the end unless `--no-accelerator`. Two
independently-created bars would fight over the same terminal line and
interleave. **`main` constructs one `Progress` and passes it to both.**

```python
run(root, *, refresh_urls=False, full=False, progress=None)   # ingest/run.py
build(root, *, progress=None)                                  # derive/build.py
```

`None` means silent, so **every existing caller and test is unchanged** — which
is what keeps this item small. `ingest/` and `derive/` never import the CLI;
ADR-CLI decision 3's *"`main` is the only boundary"* stays intact.

## The surface

**Verbatim, from [the capture](../regression/2026-08-21-progress-plane/report.md)**
— 1 203 documents. Each line below is a phase's final committed frame; between
them the line is repainted in place with `\r`.

```console
$ fux ingest
  walk     [████████████████████] 1203/1203
  extract  [████████████████████] 1203/1203  docs/doc1202.md
  edges    [████████████████████] 1203/1203
  write    [████████████████████] 252/252 shards
  read     [████████████████████] 252/252 shards
  codes    [████████████████████] 1203/1203
  postings [████████████████████] 1251/1251 terms
ingested 1203 docs (1203 changed, 0 carried forward), 0 skipped, 252 shards written
accelerator: 1251 terms, 1314 blocks, 10827 postings (derived, not committed)

$ fux build
  read     [████████████████████] 252/252 shards
  codes    [████████████████████] 1203/1203
  postings [████████████████████] 1251/1251 terms
accelerator rebuilt from the committed index: 1203 docs, 1251 terms, 1314 blocks, 10827 postings
```

Mid-run:

```text
  extract  [██████░░░░░░░░░░░░░░] 412/1203  docs/doc0411.md
  postings [█████████░░░░░░░░░░░] 600/1251 terms
```

**Two things the capture changed from the sketch above it.** A phase whose
count is not documents **names its unit** (`252/252 shards`) — without it the
drop from `edges`' 1 203 to `write`'s 252 reads as loss. And `graph` painted
nothing, correctly: the fixture's documents link to nothing, so its total was
0, under the threshold.

```console
$ fux ingest | tee log.txt     # not a TTY -> no bar, byte-identical to today
$ fux ask "…" --json           # stdout is pure JSON; a bar would still be on stderr
```

## The decision this item needed from Arpit — taken on the stated default

**Do the git hooks show the bar? — yes, and explicitly.** The handoff's stated
default ("show it") was applied rather than stalling the build: `_PREAMBLE` in
`maintain/hooks.py` now exports **`FUX_NO_PROGRESS=0`**, so the bar paints
inside a commit by decision rather than by accident of TTY detection. R5's
44.4 s of silence is the reported symptom and a commit is where a person is
most likely to think fux has hung. Recorded in
[ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) §Consequences and
[ADR-CLI](../../docs/adr/0002_cli-surface.md) decision 9.

**Still Arpit's to reverse, cheaply.** If [W-61](W-61-maintenance-measurement.md)'s
fork resolves to **B — the hook defers**, commit cost becomes 0.34 s and
constant, and a bar that flashes for a third of a second is noise — though the
~200 threshold suppresses it in most repos anyway. Reversing it is a one-line
change to `_PREAMBLE`.

**`fux-merge-index` stays silent regardless** — git owns that stdio contract
and the driver is per-shard fast.

## Hard constraints

- **L1** — hand-rolled, stdlib only. No `tqdm`, no `rich`.
- **Use `\r` plus trailing spaces, not `\x1b[2K`.** The litmus names
  Windows-first fleets and old conhost has no ANSI by default. `\r` works
  everywhere.
- **`try`/`finally` that clears the line.** Ctrl-C already exits 130; it must
  not leave a half-painted bar on the user's terminal.
- **ADR-CLI decision 7** — `fux --version` stays instant. `progress.py` must not
  be imported at `cli.py` module level.
- **`src/fux/progress.py` is a component**, so it needs an ownership row in
  [`docs/adr/README.md`](../../docs/adr/README.md) and a matching edit to
  [`tests/test_adr_ownership.py`](../../tests/test_adr_ownership.py) **in the
  same change**. Owned by ADR-CLI.

## Definition of done

- [x] `src/fux/progress.py` exists: TTY-gated, stderr-only, count-based,
      threshold-gated, clock-free.
- [x] `run()` and `build()` take `progress=None` and report every phase in the
      table above. No existing caller changed.
- [x] `main` creates one `Progress` and passes it to both, so an `ingest` that
      also builds shows one continuous sequence.
- [x] `--no-progress`, `--progress`, and `FUX_NO_PROGRESS=1` all work.
- [x] **The test that matters:** every write verb run twice, with and without
      `--progress`, asserting **stdout is byte-identical** —
      `tests_e2e/test_progress_surface.py`, parametrized over both verbs.
- [x] Ctrl-C during each phase leaves no partial line — `_Phase.__exit__`
      clears on any exception; covered in both suites. **This needed a second
      fix to be true**: `\r` cannot erase a line that *wrapped*, so an
      unbounded document path in `extract`'s detail broke the guarantee for
      deep paths. Lines are capped at 80 columns, the detail truncated from
      the left with a leading `…`, and non-printables stripped.
- [x] The hook decision is recorded: **show it**, `FUX_NO_PROGRESS=0` in
      `_PREAMBLE`.
- [x] ADR-CLI updated: decision 9, the ownership row, `test_adr_ownership.py`,
      and veto checks 5 and 6. ADR-INGEST, ADR-T1-ACCELERATOR and
      ADR-MAINTENANCE updated in the same change.
- [x] A capture is filed at
      [`work/regression/2026-08-21-progress-plane/`](../regression/2026-08-21-progress-plane/report.md),
      and the transcripts above are its verbatim output.
- [x] `OPEN-WORK.md`, `DOC-REGISTRY.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`
      and `WORKLOG.md` true at the end.

**One thing the capture did not test**, named rather than left to be
discovered: repaint cost at R5's 100 000 documents. This ran at 1 203. The bar
is one write + one flush per document, which is not free.
[W-26](W-26-m6-scale-t2.md) is where that gets measured.

---

## The Claude Code prompt

**Model: Sonnet** — the design is decided and written above; the definition of
done is mechanical and the central invariant is a test.

```text
Read CLAUDE.md, then work/open/W-64-progress-plane.md end to end. That file is
the spec; this prompt is only how to execute it.

EXPLORE (do not write yet)
- Read src/fux/cli.py, src/fux/ingest/run.py, src/fux/derive/build.py,
  src/fux/ingest/__init__.py, src/fux/maintain/hooks.py,
  src/fux/maintain/mergedriver.py.
- Confirm in the code that nothing in src/ writes to stderr except the three
  error sites the handoff names. If something else does, STOP and say so —
  the whole design rests on stderr being free.
- Read docs/adr/0002_cli-surface.md, especially decisions 3 and 7 and the veto
  checks, and docs/adr/README.md's ownership table.

PLAN
- TodoWrite the phases and keep it current DURING the work.
- Three commits: (1) progress.py + its unit tests; (2) the run()/build() seams
  and the CLI wiring; (3) ADR-CLI + ownership + the capture.

IMPLEMENT
1. src/fux/progress.py — stdlib only, stderr only, TTY-gated, count-based, a
   ~200 threshold per phase, `\r` + trailing spaces (NOT \x1b[2K), try/finally
   that clears the line. No timers, no rates, no ETA anywhere in the file.
2. Add `progress=None` to ingest.run() and derive.build(); report each phase in
   the handoff's table. Do not change any existing call site's behaviour.
   `main` constructs ONE Progress and passes it to both so an ingest that also
   builds is one continuous sequence.
3. Wire --no-progress / --progress / FUX_NO_PROGRESS. Keep the import of
   progress.py lazy (ADR-CLI decision 7) and verify with ADR-CLI's veto check 3.

VERIFY — the first item is the point of the whole change
- For EVERY write verb: run twice, once with --progress and once with
  --no-progress, and assert stdout is byte-identical. Paste the diff (empty).
- `fux ask --json | jq .` still parses with progress forced on.
- Piped and non-TTY invocations produce today's exact output.
- Ctrl-C mid-phase leaves no partial line (test with a SIGINT, per phase).
- uv run pytest -q tests && uv run pytest -q tests_e2e
- Capture the surface into work/regression/<date>-progress/ and replace the
  invented transcripts in work/open/W-64-progress-plane.md.

CONSTRAINTS
- L1: no new dependency. Hand-rolled.
- Nothing about progress may reach stdout, ever, under any flag.
- No wall-clock anywhere: no elapsed, no ETA, no rate, no time import for
  display purposes.
- src/fux/progress.py needs an ownership row in docs/adr/README.md AND an edit
  to tests/test_adr_ownership.py in the same commit.

STOP AND ASK, do not choose a default, if:
- the git-hook question at the foot of the handoff is not answered and you
  cannot proceed reversibly;
- making the bar work would require any write to stdout;
- an existing golden file changes and you cannot articulate why.
Write work/BLOCKED.json with decision ASK and stop.

FINISH
- Update OPEN-WORK.md, IMPLEMENTATION.md, DOC-REGISTRY.md, CHANGELOG.md,
  INTERVIEW.md, NOW.md and append a WORKLOG.md entry.
- Do not merge on red; read `gh pr checks <n>` yourself.
```

## Reference

- The silence this fixes — [R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md),
  44.4 s at 100 000 documents on the commit path.
- Where the time actually goes —
  [the ingest cost profile](../regression/2026-08-20-ingest-cost-profile/report.md):
  92 % of a full ingest is the dense embedding.
- The evidence a bar must not corrupt —
  [the CLI surface capture](../regression/2026-08-18-cli-surface/report.md).
- The convention for progress on stderr and TTY detection: POSIX's separation of
  stdout (data) from stderr (diagnostics) —
  https://pubs.opengroup.org/onlinepubs/9699919799/functions/stderr.html
