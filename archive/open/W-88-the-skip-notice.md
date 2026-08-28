---
type: Handoff
status: implemented
item: W-88
opened: 2026-08-27
closed: 2026-08-27
record: ADR-INGEST (0007_ingest.md) decision 4 — amended
successor: ADR-INGEST decision 4's W-88 amendment; `src/fux/ingest/skipnotice.py`
---

# W-88 — the skip notice: a skip is news once, not every run

**Opened and closed on 2026-08-27, in one session.** It never held a row in
[`OPEN-WORK.md`](../../work/OPEN-WORK.md): nothing was pending between the ask
and the landing, and a row added and deleted in the same change would have
said nothing to anybody. Kept here for the reasoning, which is the part worth
keeping.

## What was asked

Arpit, 2026-08-27, verbatim in substance:

> *"Whenever I run `fux ingest`, it gives me a huge list of skip files.
> Showing it the first time is okay. Showing it again and again is not okay.
> Display it the first time. Save that list in a gitignored file."*

## The problem, stated precisely

[ADR-INGEST](../../docs/adr/0007_ingest.md) decision 4 requires every skipped
file to be reported with a reason, *always* — because **a silently dropped
file is indistinguishable from a file that was never there.**

The rule is right. Its unconditional implementation is not:

- On any real corpus the list is **tens to hundreds of identical lines, on
  every single run**, and `fux ingest` runs on a hook.
- **A wall nobody reads is the same failure the rule exists to prevent**,
  arrived at from the other side. The signal was drowned by its own repetition.

**So the rule stays and the repetition goes.** That framing is the whole
design: nothing is suppressed that has not already been shown.

## What was built

| piece | where |
|---|---|
| the already-reported set | `.fux/runtime/skipped` — derived, gitignored, sorted `path: reason`, **no wall clock** |
| the module | [`src/fux/ingest/skipnotice.py`](../../src/fux/ingest/skipnotice.py) — `read` · `unseen` · `write` · `render` |
| the one call site | `ingest/__init__.py::ingest_and_report` — the single seam every verb already prints through |
| the tests | [`tests/ingest/test_skipnotice.py`](../../tests/ingest/test_skipnotice.py) — 12 cases |

**Behaviour:**

```console
$ fux ingest                       # first run — unchanged, every skip printed
  skip docs/empty.md: empty
  skip docs/logo.png: not an indexed file type

$ fux ingest                       # second run
  (2 skipped, unchanged since the last run - .fux/runtime/skipped; 'fux ingest --list-skipped' lists them all)

$ printf '' > docs/late.md && fux ingest
  skip docs/late.md: empty
  (2 more skipped, unchanged since the last run - .fux/runtime/skipped; 'fux ingest --list-skipped' lists them all)
```

## The five judgement calls

Each is a place a later session would otherwise change in the wrong direction.

**1. The key is `(path, reason)`, not the path.** A file whose reason moves
from `empty` to `not an indexed file type` is **news**, and prints again. So
does a fetch failure whose exception text changes. Keying on the path alone
would suppress a genuinely new fact about a file already on the list.

**2. An offline run does not replace the URL entries.** A plain `fux ingest`
consults no URL, so it learns nothing about that plane and must not forget
what a networked run recorded — otherwise the next `fux update` re-prints
every URL failure as though it were new. This is `_observe_url_health`'s rule
([ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md)) applied to the printer.
The partition is **exact, not a guess**: a URL skip's `rel_path` *is* the URL,
and a repo-relative path can never carry a `scheme://`.

**3. A missing or corrupt notice reads as *nothing reported yet*.** The safe
direction to fail in is **printing again**; failing the other way would
suppress a skip that was never shown. `rm -rf .fux/runtime` therefore costs
one repeat of the list and nothing else, which is the disposability contract
[ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) already promises.

**4. The last skip going away deletes the notice.** A corpus whose final skip
was just fixed must not leave a file claiming otherwise.

**5. The suppressed line names both escape hatches, on screen.** `fux ingest
--list-skipped` (walks and prints everything, writes nothing) and the notice
file's own path. **A way out that lives only in a record is not a way out** —
the person reading the console is the one who needs it.

## What was deliberately not touched

- **The skip rules and the reasons** — `gitdir.py::_skip_reason` is untouched.
- **`--list-skipped`** — still a full walk, still writes nothing.
- **The summary count.** `N skipped` is still *every* skip, not the new ones.
  The count is the honest number; only the enumeration is suppressed.
- **Any committed byte.** Asserted directly rather than argued:
  `test_suppression_never_moves_a_committed_byte` digests the shards either
  side of a suppressed run.
- **L3.** The notice is derived, gitignored and carries no clock. Console
  output has never been a determinism surface — the index bytes are — but the
  file is written to the same standard anyway, because a derived file that
  would break the law *if* it were ever committed is a trap left for someone
  else.

## Records amended in the same change

| record | why |
|---|---|
| [ADR-INGEST](../../docs/adr/0007_ingest.md) | **owns `src/fux/ingest/`** — decision 4 gains the W-88 amendment plus a second-run capture |
| [ADR-DOTFUX](../../docs/adr/0003_fux-directory.md) | every child of `.fux/` is declared there; `runtime/` gains a third derived file |
| [ADR-CLI](../../docs/adr/0002_cli-surface.md) | describes but does not own — its `fux ingest` captures show the un-suppressed shape and are now annotated as first runs (W-77's governance gap, met deliberately) |

## Verification

12 cases in `tests/ingest/test_skipnotice.py`, all green. ⚠ **Run through a
stdlib harness, not `pytest`** — the build sandbox is Python 3.10 with no
`pytest` and no network, so a `tomllib` shim outside the repo stood in. **The
`pytest` file itself is unverified on a real 3.11+ install** and someone must
run `uv run pytest -q tests` before release. The same caveat W-86 filed, for
the same reason.
