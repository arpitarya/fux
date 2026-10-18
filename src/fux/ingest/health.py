"""`fux doctor`'s writer rows — hooks, the background runner and daemon, the
register, seeded copies and frozen keys, redaction drift — and a writer-only
doctor, which alone can `--fix`.

Writer layer (W-282). `doctor.py` (the engine) runs these among every other
row; on a `fux-writer` install without the engine, `cmd_doctor` here runs the
core rows and these, in the order `health.ROWS` states
([SR-DOCTOR](../../../records/0152_doctor.md)).
"""

from __future__ import annotations

import json
from pathlib import Path

from ..errors import FuxError
from ..constants import fixed
from ..health import (  # noqa: F401
    Check,
)


def _background_runner(root: Path) -> Check:
    """The deferred re-index, reported and never repaired (W-66 Phase 4).

    SR-MAINTENANCE decision 1c: `post-commit` spawns a detached process that
    exits, so without this the whole maintenance path is invisible — a runner
    that died leaves the dirty list intact and says nothing at all. Four
    questions, one line: is one live and which pid, how many documents are
    pending, is the lock held or stale, and did the last run fail.

    **Read-only, and that is the decision rather than an omission.** A stale
    lock is *named* along with the command that clears it; this never clears
    it. Clearing a lock whose owner is actually alive puts two runners inside
    `.fux/index/` at once, which is the single failure the lock exists to
    prevent — decision 1c's veto 7. The logic lives in `maintain/runner.py`
    (SR-MAINTENANCE's component); this function only renders it.

    A **warning**, never an error: a pending re-index means the index is late,
    which is the deferring hook working as designed, not a broken repo.
    """
    from ..maintain import runner

    state = runner.status(root)
    pending = state["pending"]
    last = state["last_run"] or {}

    if state["lock"] == "stale":
        return Check(
            "background runner",
            False,
            f"a lock is held by pid {state['pid']}, which is not running - a re-index was "
            f"killed. {pending} changed path(s) pending. Run `fux ingest --stop` to clear it, "
            f"or delete {state['lock_path']}",
            level="warn",
        )
    if state["running"]:
        return Check(
            "background runner",
            True,
            f"running (pid {state['pid']}), {pending} changed path(s) pending",
            level="warn",
        )
    if last.get("outcome") == "failed":
        return Check(
            "background runner",
            False,
            f"the last background re-index FAILED ({last.get('error', 'no detail recorded')}). "
            f"{pending} changed path(s) pending - run `fux ingest` to see the error",
            level="warn",
        )
    if pending:
        return Check(
            "background runner",
            True,
            f"idle, {pending} changed path(s) pending - run `fux ingest` to catch up",
            level="warn",
        )
    return Check("background runner", True, "idle, nothing pending", level="warn")


def _git_hooks(root: Path) -> Check:
    """Can the installed hooks reach a `fux`? (W-276, SR-MAINTENANCE decision 3a.)

    A hook resolves `fux` through the interpreter `fux hooks --install` pinned,
    and PATH only after it. **The pinned interpreter gone, or a hook written
    before the pin, is the case this row exists for**: the commit succeeds, the
    hook does nothing or prints one line nobody reads, and the committed index
    falls behind. On this repository that was 39 commits from 2026-10-04.

    Read-only like every row here: it names `fux hooks --install` and runs
    nothing. A **warning** — absent hooks are a choice (decision 5), not a fault.
    """
    from ..maintain import hooks as hooks_mod

    try:
        state = hooks_mod.status(root)
    except Exception as exc:  # no git repository: the hooks have nowhere to live
        return Check("git hooks", True, f"not applicable - {exc}", level="warn")
    ours = sorted(name for name, who in state["hooks"].items() if who == "fux")
    if not ours:
        return Check("git hooks", True, "not installed - `fux hooks --install` re-indexes on commit", level="warn")
    pinned = state["python"]
    broken = [name for name in ours if pinned.get(name) == "missing"]
    if broken:
        return Check(
            "git hooks",
            False,
            f"{', '.join(broken)}: the interpreter they were installed with is gone, so they fall "
            "back to PATH or skip - run `fux hooks --install`",
            level="warn",
        )
    old = [name for name in ours if pinned.get(name) == "unpinned"]
    if old:
        return Check(
            "git hooks",
            False,
            f"{', '.join(old)}: written before W-276 and resolve `fux` on PATH alone, which an IDE "
            "or a shell without the venv may not have - run `fux hooks --install`",
            level="warn",
        )
    return Check("git hooks", True, f"{', '.join(ours)} installed, interpreter pinned", level="warn")


def _daemon(root: Path) -> Check | None:
    """The resident clock's last sweep — `None` when it has never run.

    **Added 2026-08-28 with the widened status shape.** Before it, the daemon's
    only surface was `fux daemon status`, which a person runs when they already
    suspect something. `doctor` is what they run when they do not.

    ⚠ **The case this exists for is `outcome: "ok"` with `skipped > 0`** — a
    sweep that looked healthy and did not index everything. Two of seven URLs
    were skipped in the 2026-08-27 real-network run and nothing said so outside
    a foreground `fux ingest`.
    """
    from ..maintain import daemon as daemon_mod

    state = daemon_mod.status(root)
    last = state.get("last")
    if not state.get("running") and not last:
        return None  # never started here; not a finding

    where = f"running (pid {state['pid']})" if state.get("running") else "not running"
    if not last:
        return Check("url daemon", True, where, level="warn")

    outcome = last.get("outcome")
    reason = last.get("reason")
    skipped = last.get("skipped") or 0

    if outcome == "failed":
        return Check(
            "url daemon",
            False,
            f"{where}; the last sweep FAILED ({reason or 'no reason recorded'})",
            level="warn",
        )
    if skipped:
        return Check(
            "url daemon",
            False,
            f"{where}; the last sweep reported ok but did not index {skipped} document(s) "
            f"({reason}) - run `fux ingest` to see them all",
            level="warn",
        )
    detail = f"{where}; last sweep {outcome}"
    if last.get("fetched") is not None:
        detail += f", {last['fetched']} document(s)"
    return Check("url daemon", True, detail, level="warn")


def _register(root: Path) -> Check:
    """`.fux/index/REGISTER` against the index it claims to describe.

    Drift means **the register was committed from a different ingest than the
    index beside it** — the one thing a committed derived file can get wrong,
    and the one nobody reads closely enough to catch by eye.
    """
    from ..ingest import register as register_mod
    from ..store import reader as reader_mod

    name = "register"
    reg = register_mod.read(root)
    try:
        index = reader_mod.read_index(root)
    except Exception:  # pragma: no cover - no readable index is other rows' business
        return Check(name, True, "skipped (no readable index)", level="warn")
    if not index:
        return Check(name, True, "no index to describe", level="warn")
    # Three states, named (SR-INGEST decision 22c): missing, old format, drift.
    if reg.state == "missing":
        return Check(
            name, False,
            f"no {register_mod.NAME} beside the index - `fux ingest` writes one",
            level="warn",
        )
    if reg.state == "old":
        return Check(
            name, False,
            f"{register_mod.NAME} is in the old format (`{register_mod.HEADER_V1.lstrip('# ')}`) - "
            f"`fux ingest` rewrites it as {register_mod.FORMAT}",
            level="warn",
        )
    from ..ingest.extract import RULES_VERSION

    rows = reg.rows
    by_loc = {r.get("loc", ""): r for r in index.values()}
    missing = sorted(by_loc.keys() - rows.keys())
    extra = sorted(rows.keys() - by_loc.keys())
    moved = sorted(loc for loc in rows.keys() & by_loc.keys() if rows[loc].sha != by_loc[loc].get("sha", ""))
    parts = []
    if reg.rules != RULES_VERSION:
        parts.append(f"written at {register_mod.RULES_KEY}={reg.rules}, this fux extracts at {RULES_VERSION}")
    if missing:
        parts.append(f"{len(missing)} indexed document(s) with no register line ({missing[0]})")
    if extra:
        parts.append(f"{len(extra)} register line(s) for nothing in the index ({extra[0]})")
    if moved:
        parts.append(f"{len(moved)} register line(s) whose sha disagrees with the index ({moved[0]})")
    if not parts:
        return Check(name, True, f"{len(rows)} line(s) ({register_mod.FORMAT}), agreeing with the index")
    return Check(
        name, False,
        "; ".join(parts) + " - the register was committed from a different ingest "
        "than the index beside it; `fux ingest` rewrites it",
        level="warn",
    )


def _meta_fields(root: Path) -> Check:
    """`[meta]` and every decoder's `META_FIELDS` — does each bound key name a
    real field, and does any binding silently override a claim?

    **W-205 part 1**, SR-INGEST decision 23. Load-time validation already
    refuses a `[meta]` value that names no index field, so this row is not about
    that. It is about the two things only `doctor` can see:

    - 🔴 **A claim and a binding on the SAME key is a FINDING, not an error.**
      The binding wins (SR-TYPES decision 13) and that is correct — but a
      consumer who bound `doc_id = "ctx"` and then installed a decoder claiming
      `doc_id = "title"` has two committed files disagreeing, and the one that
      loses is invisible. **Said aloud, never resolved silently.**
    - ⚠ **`none` bindings are reported** because a silenced key looks exactly
      like a key nobody thought about, and only the person who wrote the line
      can tell them apart.
    """
    from ..decode import meta_bindings, registry
    from ..ingest.parse import meta_fields

    try:
        bindings = meta_bindings(root)
        decoders = registry(root)
    except FuxError as exc:
        return Check("meta fields", False, str(exc))

    resolved = meta_fields(None, root)
    silenced = sorted(k for k, v in bindings.items() if v == "none")
    collisions = sorted(
        f"{key} (decoder {d.name} claims {d.meta_fields[key]}, binding says {bindings[key]})"
        for d in dict.fromkeys(decoders.values())
        for key in d.meta_fields
        if key in bindings and bindings[key] != d.meta_fields[key]
    )
    detail = (
        f"{len(resolved)} key(s) indexed: "
        + ", ".join(f"{k}->{v}" for k, v in list(resolved.items())[:6])
        + (f" (+{len(resolved) - 6} more)" if len(resolved) > 6 else "")
    )
    if silenced:
        detail += f"; {len(silenced)} silenced by `none`: {', '.join(silenced)}"
    if not collisions:
        return Check("meta fields", True, detail)
    return Check(
        "meta fields",
        False,
        f"{detail}; {len(collisions)} key(s) where a `[meta]` binding overrides a "
        f"decoder's claim: {'; '.join(collisions[:3])}. The binding wins by design - "
        f"this is reported because two committed files disagree and the loser is "
        f"otherwise invisible (SR-INGEST decision 23a)",
        level="warn",
    )


def _stale_redaction(root: Path) -> Check:
    """`url:` documents the last policy change could not reach (W-166 DoD 3).

    A PII, decoder or extraction-rule change re-derives every `url:` record whose
    bytes are retained in `.fux/acquired/`. One with no retained blob cannot be
    re-derived offline at all, so **its record is left exactly as it is** —
    dropping a document because a policy changed is the one thing a redaction
    change must never do — and it is named here instead.

    ⚠ **`warn`, and the reason is worth stating.** The record is not wrong about
    its source; it is extracted under rules that have since moved. The fix needs
    the network (`fux ingest`), which `doctor` is not going to take on a user's
    behalf, and failing the command for a condition only a fetch can clear would
    make `doctor` red until someone goes online.

    ⚠ **Derived state, so it does not travel with a cloned index** — see
    `run._record_stale_redaction` for what that trade bought. A fresh clone reads
    clean here until its own ingest re-derives the fact.

    **ASCII only** - it is printed, and printed text reaches a Windows console.
    """
    from ..ingest.run import STALE_REDACTION_FILE
    from ..store import fuxdir

    path = fuxdir.fux_dir(root) / "runtime" / STALE_REDACTION_FILE
    try:
        stranded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stranded = []
    if not isinstance(stranded, list) or not stranded:
        return Check(
            "url redaction current",
            True,
            "every url record was re-extracted under the current rules, or none needed to be",
        )
    shown = ", ".join(sorted(str(s) for s in stranded)[:3])
    more = f" and {len(stranded) - 3} more" if len(stranded) > 3 else ""
    return Check(
        "url redaction current",
        False,
        f"{len(stranded)} url document(s) still hold text extracted under the OLD rules "
        f"- no retained bytes to re-extract from: {shown}{more}. "
        "`fux ingest` fetches them; `keep=true` on the line retains the bytes so the next "
        "policy change can reach them offline",
        level="warn",
    )


def _seeded_copies_current(root: Path) -> Check:
    """Every stamped decoder and fetcher copy against the template it came from.

    **W-262 -- Arpit, 2026-10-04, W-251 #2, option B of
    `work/compare/consumer-template-refresh.compare.md`.** `fux setup` seeds
    `.fux/decoders/` and `.fux/fetchers/` once and never again, so an engine fix
    to a shipped template reaches no existing repo on its own (SR-DECODE
    decision 10's accepted cost, SR-FETCHER decision 12's gap). Each copy now
    carries a first-line stamp naming the template's sha256, which separates the
    three cases this row needs:

    | copy | finding |
    |---|---|
    | unedited, stamp = current template | none -- it IS the current template |
    | **unedited, stamp != current template** | **named, with the lever: re-seed it yourself** |
    | edited (body no longer hashes to its stamp) | none -- the consumer owns it |
    | no stamp (seeded before W-262, or hand-written) | counted, never judged |

    🔴 **A notice, never a rewrite.** SR-DOTFUX decision 6 names the mechanism
    for a change that must reach an existing repo -- *a loader refusal or a
    `doctor` check, never a rewrite* -- and option A, which refreshed unedited
    copies on upgrade, was refused in the same ruling. **Re-seeding is the
    consumer's act**: delete the file and run `fux setup`, which writes the
    current template, stamped.

    A **warning**, never an error: a stale unedited copy is a correct, supported
    configuration that is merely missing fixes. Read as bytes; nothing is
    imported (decision 7).
    """
    from ..setup import read_stamp, seeded_copies, template_digest

    name = "seeded copies current"
    dot = fixed("fuxdir", "dir")
    directory = root / dot
    stale: list[str] = []
    unstamped = 0
    edited = 0
    current = 0
    for rel, template in seeded_copies():
        path = directory / rel
        if not path.is_file():
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        stamp, body = read_stamp(raw)
        if stamp is None:
            unstamped += 1
        elif template_digest(body) != stamp:
            edited += 1
        elif stamp != template_digest(template):
            stale.append(f"{dot}/{rel}")
        else:
            current += 1
    tail = (
        f"; {edited} edited (yours, not compared)" if edited else ""
    ) + (
        f"; {unstamped} unstamped (seeded before the stamp, or written by hand - "
        "cannot be judged)" if unstamped else ""
    )
    if not stale:
        return Check(
            name,
            True,
            f"{current} unedited copy(ies) match the current template{tail}",
            level="warn",
        )
    return Check(
        name,
        False,
        f"{len(stale)} unedited copy(ies) whose template has changed since they were "
        "seeded: "
        + ", ".join(stale[:4])
        + (f" and {len(stale) - 4} more" if len(stale) > 4 else "")
        + f"{tail}. fux will not rewrite them - re-seed it yourself: delete the file "
        "and run `fux setup`, which writes the current template, stamped",
        level="warn",
    )


def _frozen_keys(root: Path) -> list[Check]:
    """Every mandatory config file against the template it was written from.

    **A key the engine gained is a key the consumer's file does not carry**,
    and because each file is write-if-missing it never gains it on its own.
    Since L12 there is no engine default to read in its place, so the verb that
    needs the key stops; this row names every missing key in one pass, and the
    remedy, `fux doctor --fix`, which writes exactly those keys.

    **The comparison is the writer's own** — `setup.missing_config_keys`, the
    function `--fix` uses — so the row and the fix cannot disagree about what is
    missing. ⚠ **Absent is the file's own `loads`/`present` row's to report**,
    not this one's: one fault, one row.
    """
    from .. import setup as setup_mod

    checks: list[Check] = []
    for rel, template, present_only, never, _whole in setup_mod._mandatory_config():
        name = f"{Path(rel).name} current"
        path = root / rel
        if not path.is_file():
            checks.append(Check(name, True, f"{rel} absent - see its own `loads`/`present` row"))
            continue
        try:
            missing = setup_mod.missing_config_keys(
                path.read_bytes().decode("utf-8-sig"), template, present_only, never
            )
        except Exception:
            # Its own row already reports an unparseable file; saying so twice
            # with two different wordings is how a reader learns to trust neither.
            checks.append(Check(name, True, f"{rel}: not parsed here - see the `loads` row"))
            continue
        if not missing:
            checks.append(Check(name, True, f"{rel}: every key the engine now carries is present"))
            continue
        shown = [f"`[{t}] {k}`" for t, k in missing]
        checks.append(
            Check(
                name,
                False,
                f"{rel} is missing {len(missing)} key(s) the engine now has: "
                + ", ".join(shown[:5])
                + (f" and {len(shown) - 5} more" if len(shown) > 5 else "")
                + ". The verbs that read them stop until they are written - "
                "`fux doctor --fix` writes exactly the missing keys from the template "
                "and touches nothing else",
                level="warn",
            )
        )
    return checks


def _queue_no_decoder(root: Path) -> Check:
    """Queue rows saying *no decoder for X* -- work for a decoder, not a model.

    **W-248 / SR-DECODE decision 12.** `fux ingest` queues two different facts,
    and `fux enrich` takes only one: a format a decoder owns but got nothing out
    of is enrichment work; a format NOTHING claims is not, because the remedy is
    a decoder and a model asked to describe a `.heic` is the wrong tool. This row
    is where that second fact reaches a reader.

    Reads the committed queue only. An absent queue is no rows, so a fresh clone
    that never ingested is `ok`, never an error.
    """
    from collections import Counter

    from ..ingest import queue as queue_mod

    name = "queue: no decoder"
    try:
        rows = queue_mod.read(root)
    except OSError:
        return Check(name, True, "skipped (the queue could not be read)", level="warn")
    counts = Counter(ext for ext in map(queue_mod.no_decoder, rows) if ext)
    if not counts:
        return Check(name, True, "no queued document is waiting on a decoder")
    shown = ", ".join(f"{ext} ({n})" for ext, n in sorted(counts.items()))
    return Check(
        name,
        False,
        f"{sum(counts.values())} queued document(s) have no decoder, by extension: {shown}. "
        "These are not enrichment work: write a decoder (the `fux-decoder` skill, into "
        f"{fixed('decoders', 'consumer_dir')}/), or exclude them in .fux/.fuxignore",
        level="warn",
    )


def _fix() -> None:
    """`fux doctor --fix` — write every missing config key from its template.

    L12 decision 3: `fux setup` and this are the only writers of a missing key.
    It reports each file and key it wrote on stderr, so `--json` stays a pure
    report of the checks that follow.
    """
    import sys

    from .. import setup as setup_mod
    from ..config import find_root

    root = find_root()
    if root is None:
        raise FuxError("fux doctor --fix: not inside a fux repository (no fux.toml above here)")
    changed = setup_mod.fill_missing(root)
    for line in changed:
        print(f"fixed: {line}", file=sys.stderr)
    if not changed:
        print("fixed: nothing - every config file carries every key", file=sys.stderr)


#: This layer's rows, by the name `health.ROWS` gives them.
ROWS = {
    "_stale_redaction": _stale_redaction,
    "_seeded_copies_current": _seeded_copies_current,
    "_frozen_keys": _frozen_keys,
    "_git_hooks": _git_hooks,
    "_background_runner": _background_runner,
    "_daemon": _daemon,
    "_register": _register,
    "_queue_no_decoder": _queue_no_decoder,
    "_meta_fields": _meta_fields,
}


def runner_status(root: Path) -> dict:
    """The `--json` payload's `runner` block."""
    from ..maintain import runner

    return runner.status(root)


def cmd_doctor(args) -> int:
    """`fux doctor` where the writer is installed and the engine is not."""
    if getattr(args, "fix", False):
        _fix()
    from ..health import provenance_counts, render, run_rows

    checks = run_rows(None, ROWS, progress=getattr(args, "progress", None))
    return render(args, checks, {"runner": runner_status, "provenance": provenance_counts})
