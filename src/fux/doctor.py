"""`fux doctor` — install/environment health check.

Checks today: python version, repo root found, `.fux/` writable, and the two
layout assertions from ADR-DOTFUX — the committed index is not git-ignored, and
nothing undeclared sits at the top level of `.fux/`.

The index check exists because the failure it catches is silent: a `.fux/*`
line in any `.gitignore` up the tree, or a consumer-edited `.fux/.gitignore`,
drops the committed index out of git with no error anywhere. Doctor stays
offline — it never touches the fetcher or the network.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import DEFAULT_DIRS_FILE, DEFAULT_TYPES_FILE, find_root
from .errors import FuxError
from . import output_config
from .store import fuxdir

PY_MIN = (3, 11)


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    level: str = "error"  # "error" fails the command; "warn" only reports


#: The committed index, parsed once per `run()`. Three checks need per-record
#: fields (`mtime` for the recency prior, `loc` for the decoder bindings, the
#: `url:` prefix for URL health) and a 10 000-document corpus parsed three
#: times is a diagnostic command that feels broken. Reset at the top of every
#: `run()` rather than memoized forever: `doctor` is called twice in one
#: process by the test suite, and a cache that outlived a re-ingest would
#: report the previous index.
_RECORDS: dict[str, dict] | None = None


def _records(root: Path) -> dict[str, dict]:
    """Every committed record, or `{}` when the index is absent or unreadable.

    **Never raises**, exactly like every other reader on this path: an index
    that cannot be read is another check's finding, and a traceback out of a
    health command is the worst possible answer to *"what is wrong"*.
    """
    global _RECORDS
    if _RECORDS is None:
        try:
            from .store import reader

            _RECORDS = reader.read_index(root)
        except Exception:
            _RECORDS = {}
    return _RECORDS


def run(start: Path | None = None) -> list[Check]:
    global _RECORDS
    _RECORDS = None
    checks = [_python_version(), *_repo_root(start)]
    return checks


def _background_runner(root: Path) -> Check:
    """The deferred re-index, reported and never repaired (W-66 Phase 4).

    ADR-MAINTENANCE decision 1c: `post-commit` spawns a detached process that
    exits, so without this the whole maintenance path is invisible — a runner
    that died leaves the dirty list intact and says nothing at all. Four
    questions, one line: is one live and which pid, how many documents are
    pending, is the lock held or stale, and did the last run fail.

    **Read-only, and that is the decision rather than an omission.** A stale
    lock is *named* along with the command that clears it; this never clears
    it. Clearing a lock whose owner is actually alive puts two runners inside
    `.fux/index/` at once, which is the single failure the lock exists to
    prevent — decision 1c's veto 7. The logic lives in `maintain/runner.py`
    (ADR-MAINTENANCE's component); this function only renders it.

    A **warning**, never an error: a pending re-index means the index is late,
    which is the deferring hook working as designed, not a broken repo.
    """
    from .maintain import runner

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


def _daemon(root: Path) -> Check | None:
    """The resident clock's last sweep — `None` when it has never run.

    **Added 2026-08-28 with the widened status shape.** Before it, the daemon's
    only surface was `fux daemon status`, which a person runs when they already
    suspect something. `doctor` is what they run when they do not.

    ⚠ **The case this exists for is `outcome: "ok"` with `skipped > 0`** — a
    sweep that looked healthy and did not index everything. Two of seven URLs
    were skipped in the 2026-08-27 real-network run and nothing said so outside
    a foreground `fux update`.
    """
    from .maintain import daemon as daemon_mod

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
            f"({reason}) - run `fux update` to see them all",
            level="warn",
        )
    detail = f"{where}; last sweep {outcome}"
    if last.get("fetched") is not None:
        detail += f", {last['fetched']} document(s)"
    return Check("url daemon", True, detail, level="warn")


def _python_version() -> Check:
    ok = sys.version_info[:2] >= PY_MIN
    have = f"{sys.version_info.major}.{sys.version_info.minor}"
    return Check(
        "python version",
        ok,
        f"{have} (need >= {'.'.join(map(str, PY_MIN))})" if not ok else f"{have}, fux {__version__}",
    )


def _repo_root(start: Path | None) -> list[Check]:
    root = find_root(start)
    if root is None:
        return [Check("repo root", False, "no fux.toml or .git found above the current directory")]
    checks = [Check("repo root", True, str(root))]
    fux_dir = root / ".fux"
    try:
        fux_dir.mkdir(exist_ok=True)
        probe = fux_dir / ".doctor-probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        checks.append(Check(".fux/ writable", True, str(fux_dir)))
    except OSError as exc:
        checks.append(Check(".fux/ writable", False, str(exc)))
    checks.extend(_layout(root))
    return checks


def _layout(root: Path) -> list[Check]:
    """ADR-DOTFUX: the index must not be ignored; `.fux/` holds only declared entries."""
    checks: list[Check] = []
    ignored = _is_git_ignored(root, root / fuxdir.FUX_DIR / "index")
    if ignored is None:
        checks.append(Check("index not gitignored", True, "skipped (not a git checkout)"))
    else:
        checks.append(
            Check(
                "index not gitignored",
                not ignored,
                ".fux/index is committed, not derived - remove the ignore rule "
                "(a `.fux/*` blanket is the usual cause)"
                if ignored
                else "the committed index is tracked",
            )
        )

    fux_dir = root / fuxdir.FUX_DIR
    extras = sorted(p.name for p in fux_dir.iterdir() if p.name not in fuxdir.DECLARED) if fux_dir.is_dir() else []
    checks.append(
        Check(
            ".fux/ layout declared",
            not extras,
            f"undeclared entries: {', '.join(extras)} - see .fux/README.md and ADR-DOTFUX"
            if extras
            else "every entry is declared",
            level="warn",
        )
    )
    checks.append(_output_config_health(root))
    checks.append(_types_health(root))
    checks.append(_ignore_health(root))
    checks.append(_fetcher_capabilities(root))
    checks.append(_accelerator(root))
    checks.append(_background_runner(root))
    daemon_check = _daemon(root)
    if daemon_check is not None:
        checks.append(daemon_check)
    checks.append(_url_health(root))
    checks.append(_acquired_health(root))
    checks.append(_pii_health(root))
    checks.append(_refusal_health(root))
    checks.append(_decoder_bindings(root))
    checks.append(_recency_prior(root))
    checks.append(_no_op_priors(root))
    checks.append(_freshness_share(root))
    return checks


#: The four ranking priors that ship at a value which makes them do nothing,
#: with the record that owns each and the record field each one reads.
#:
#: `(key, no-op value, record field, what the field means)`. `None` for the
#: field means the prior is not driven by a per-record declaration.
_NO_OP_PRIORS = (
    ("archived_weight", 1.0, "archived", "declared archived=true"),
    ("superseded_weight", 1.0, "superseded", "superseded by another document"),
    ("rerank_weight", 0.0, None, ""),
    ("recency_half_life_days", 0.0, "mtime", "carrying an mtime"),
)


def _no_op_priors(root: Path) -> Check:
    """Every ranking prior that is BUILT, WIRED and SWITCHED OFF at its default.

    **W-126 part B, on Arpit's ask of 2026-09-11.** Four mechanisms — the
    archived demotion, the supersession demotion, the proximity reranker and
    the recency decay — are each implemented, each read their input, and each
    ship at a value that makes them return the score unchanged. A repo that
    declares `archived=true` on a source line, or writes `supersedes:` in a
    document's frontmatter, gets **exactly nothing** for it and **is not told**.

    ⚠ **This is a DISCLOSURE and not a ranking change**, and the distinction is
    the whole reason it could be built today. Whether any of these defaults
    should move is blocked on a measurement nobody can run yet (the hand-graded
    corpus is uncommitted), and Arpit ruled *remeasure first* on
    `superseded_weight` and `rerank_weight` the same day.

    🔴 **So it REFUSES to recommend a value, deliberately.** Recommending one is
    the remeasure's job. `P-SUPERSEDE` is the standing proof of why: at `0.5`
    the supersession prior fixed two queries and **broke two**, and every
    broken query had the superseded document as its correct answer. A `doctor`
    row that said *"try 0.5"* would be handing out the exact change a frozen
    pre-registration already failed.

    **What it does say is the part nobody could see:** for each dead prior, how
    many documents in THIS corpus declare the thing it would have acted on. A
    repo with 0 archived documents has a knob that is off and irrelevant; a
    repo with 40 has one that is off and costing it something. Those are
    different findings and a flat list of four defaults cannot tell them apart.

    A **warning**, never an error: shipping at a default is not a broken
    install, and every one of these values is a legitimate choice somebody may
    have made on purpose.
    """
    from .tune import DEFAULT_TUNE
    from .tune import load as load_tune

    try:
        tune = load_tune(root)
    except Exception:
        tune = DEFAULT_TUNE

    records = _records(root)
    dead: list[str] = []
    for key, no_op, field, meaning in _NO_OP_PRIORS:
        if getattr(tune, key) != no_op:
            continue
        part = f"{key}={no_op:g}"
        if field is not None and records:
            declared = sum(1 for record in records.values() if record.get(field))
            part += f" ({declared} document(s) {meaning})"
        dead.append(part)

    if not dead:
        return Check(
            "ranking priors",
            True,
            "every ranking prior is set to a value that does something",
        )
    return Check(
        "ranking priors",
        False,
        "BUILT, WIRED AND SWITCHED OFF at these values: "
        + "; ".join(dead)
        + ". Each is implemented and reads its input, and at the value shown it "
        "returns the score unchanged - so a document you declared archived or "
        "superseded ranks exactly as if you had not. fux states this and does NOT "
        "recommend a value: the one change measured so far (superseded_weight 0.5) "
        "fixed two queries and broke two, and every broken one had the superseded "
        "document as its correct answer",
        level="warn",
    )


def _pii_health(root: Path) -> Check:
    """`.fux/pii.toml` — do the rules load, and do the patterns compile?

    ⚠ **Offline and read-only, like every check here: it compiles the patterns
    and never runs them over a corpus.** Compiling catches the fault that
    matters (a rule that would stop an ingest dead), and it costs microseconds.
    Running them would mean reading the whole corpus inside the command a
    person runs *because something is already wrong*.

    **What this check CANNOT tell you** is the failure that actually bites: a
    rule that is well-formed and too broad. That removes real vocabulary from
    the index silently -- nothing errors, documents just stop being findable by
    the words that would have found them. `tools/pii-probe/` is where that is
    visible, and no offline check substitutes for reading what a rule caught.
    """
    from .ingest import pii

    # ADR-PII decision 17: a missing file is an ERROR row -- `load` raises and
    # says what to run. `doctor` is exempt from the CLI gate so that it gets
    # here and names the fix, not so that the fault reads as healthy.
    try:
        rules = pii.load(root)
    except FuxError as exc:
        return Check("pii rules", False, str(exc))
    if not rules:
        return Check(
            "pii rules", True, ".fux/pii.toml declares no rules", level="warn"
        )
    names = ", ".join(rule.name for rule in rules)
    detail = (
        f"{len(rules)} rule(s) compile: {names}. Redaction applies to "
        f".fux/index/ only - acquired bytes and answer quotes are unredacted"
    )
    return Check("pii rules", True, f"{detail}. {_redaction_note(root, rules)}")


def _redaction_note(root: Path, rules) -> str:
    """What the last ingest actually redacted — W-101 item 4.

    `redact()` has always returned per-rule hit counts and `run()` has always
    summed them; **nothing read the sum**, so a consumer could not tell a rule
    that is protecting them from a rule that has never matched anything. The
    counts are now recorded by every ingest (`pii.record_counts`) and this is
    where they surface.

    ⚠ **Absent and zero are different answers and stay apart.** No recorded
    counts means no ingest has run since the counter existed; zero means the
    rules ran and matched nothing. Collapsing them would let a repo whose rules
    have never executed read as a repo whose rules found nothing, which is the
    more dangerous of the two.

    ⚠ **The enrichment half is partial on an incremental ingest** and says so:
    enrichment is redacted inside the extract loop, which a reused document
    skips. The body half is a complete census on every run.

    ⚠ **A large count is a hint, not a finding.** An over-broad rule and a
    correct rule on a corpus that really does contain that much PII produce the
    same number. `tools/pii-probe/` is the instrument; this is the pointer to
    it.
    """
    from .ingest import pii

    counts = pii.read_counts(root)
    if counts is None:
        return "No ingest has recorded redaction counts yet - run `fux ingest`"
    if counts.total == 0:
        return (
            f"The last ingest redacted NOTHING across {counts.documents} document(s): "
            f"every rule compiled and none matched. That is a rule that is not doing "
            f"what it was written for as often as it is a clean corpus"
        )
    body = ", ".join(f"{name} x{n}" for name, n in sorted(counts.body.items()))
    note = (
        f"The last ingest redacted {counts.total} value(s) across "
        f"{counts.documents} document(s)"
    )
    if body:
        note += f" - body: {body}"
    if counts.enrichment:
        enrichment = ", ".join(f"{name} x{n}" for name, n in sorted(counts.enrichment.items()))
        note += f"; enrichment: {enrichment}"
        if counts.partial:
            note += (
                " (enrichment counts cover the documents that run re-extracted, not the "
                "whole corpus - `fux ingest --full` counts all of them)"
            )
    note += ". A big number is a hint, not a finding: see tools/pii-probe/"
    return note


def _acquired_health(root: Path) -> Check:
    """`.fux/acquired/` — how much is retained, and whether it is gitignored.

    ⚠ **Two questions, and the second is the one that matters.** The size is
    housekeeping; whether the plane is ignored by git is a data-exposure
    question, because this directory holds SOURCE BYTES. `_layout` already
    refuses an undeclared child of `.fux/`, and `_ignore_health` checks the
    index is *not* ignored — neither of them asks whether a plane that must be
    ignored actually is. This does.

    **A `warn`, never an `error`, on size.** ADR-ACQUIRED decision 8 bounds the
    store and evicts; a store near its cap is working as designed, not broken.
    An UNIGNORED plane is a different matter and fails.
    """
    from .store import acquired

    plane = acquired.plane(root)
    if not plane.is_dir():
        return Check(
            "acquired plane",
            True,
            "nothing retained (no .fux/acquired/) - `keep=false` on every line, or nothing fetched yet",
            level="warn",
        )

    blobs = acquired.blobs_on_disk(root)
    total = sum(size for _, size in blobs)
    manifest = acquired.read_manifest(root)
    orphans = len(blobs) - len({b.sha for b in manifest.values()} & {p.name.split(".", 1)[0] for p, _ in blobs})

    ignored = _is_git_ignored(root, plane)
    if ignored is False:
        # The one failing case: retained source bytes that git can see.
        return Check(
            "acquired plane",
            False,
            f"{len(blobs)} blob(s), {total:,} bytes - AND .fux/acquired/ IS NOT GITIGNORED. "
            "It holds the bytes fetched from your sources; add `acquired/` to .fux/.gitignore "
            "(fux writes that line, so this means it was edited away)",
        )

    detail = f"{len(blobs)} blob(s), {total:,} bytes, {len(manifest)} in the manifest"
    if ignored is None:
        detail += " (gitignore unchecked: not a git checkout)"
    if orphans > 0:
        detail += f" - {orphans} unreferenced, swept on the next `fux update`"
    cap = acquired.DEFAULT_MAX_BYTES
    if total > cap * 0.8:
        return Check(
            "acquired plane",
            True,
            f"{detail} - past 80% of the {cap:,}-byte cap; eviction will start "
            "dropping the oldest re-acquirable blobs",
            level="warn",
        )
    return Check("acquired plane", True, detail)


def _refusal_health(root: Path) -> Check:
    """`.fux/refusals.toml` — do the rules load, and has any of them ever fired?

    **W-101 item 3.** A refusal rule is the one piece of consumer policy whose
    correct behaviour and whose catastrophic behaviour look identical from
    outside: a rule that matches every response empties the `url:` half of the
    corpus, and an empty corpus looks exactly like a corpus nobody has ingested
    yet. Until now the only surface was a run's own output, which scrolls away.

    Two numbers, and the second is the one that matters:

    * **How many rules load**, which catches the file that was never valid —
      the same thing `_pii_health` catches for `pii.toml`.
    * **How many responses each has refused**, cumulative across networked runs
      from `urlstate.refused`. A rule at zero is a rule that has never done
      anything, which is what a typo'd `body_contains` looks like; a rule whose
      count is the size of the corpus is the over-broad rule.

    ⚠ **Offline, and the count is therefore about the PAST.** Doctor never
    fetches, so it reports what networked runs recorded. A repo that has never
    run `fux update` has nothing here and is told that rather than shown a zero
    it would read as *"nothing was refused"*.

    ⚠ **A warning, never an error.** Refusing sign-in walls is the feature
    working. The one loud shape — refusals recorded and no `url:` document
    surviving — is still a `warn`, because a corpus of only unreachable
    intranet pages is a legitimate state of the world and failing `doctor` on
    it would train people to ignore a red one.
    """
    from .ingest import refusals

    if not refusals.rules_path(root).is_file():
        return Check(
            "refusal rules",
            True,
            "no .fux/refusals.toml - only the always-on magic-byte floor applies",
            level="warn",
        )
    try:
        rules = refusals.load(root)
    except FuxError as exc:
        return Check("refusal rules", False, str(exc))

    try:
        from .maintain import urlstate

        counted = dict(urlstate.read(root).refused)
    except Exception:
        counted = {}

    if not rules:
        return Check(
            "refusal rules", True, ".fux/refusals.toml declares no rules", level="warn"
        )

    total = sum(counted.values())
    parts = [f"{len(rules)} rule(s) load"]
    if not counted:
        parts.append(
            "no networked run has recorded a refusal yet - the count starts at the "
            "next `fux update`"
        )
        return Check("refusal rules", True, ", ".join(parts), level="warn")

    worst = sorted(counted.items(), key=lambda kv: (-kv[1], kv[0]))
    named = ", ".join(f"{name} x{count}" for name, count in worst[:5])
    parts.append(f"{total} response(s) refused across networked runs: {named}")
    silent = [rule.name for rule in rules if rule.name not in counted]
    if silent:
        # Named, not counted: a rule that has never fired is either unneeded or
        # a typo, and only the consumer can tell which — but they need the name
        # to look at the line.
        parts.append(
            f"never fired: {', '.join(sorted(silent))} (unneeded, or a condition that "
            "never matches)"
        )

    indexed_urls = sum(1 for doc_id in _records(root) if doc_id.startswith("url:"))
    if total and indexed_urls == 0:
        return Check(
            "refusal rules",
            False,
            ", ".join(parts)
            + " - AND NO url: DOCUMENT SURVIVED. A rule that matches everything empties "
            "the URL half of the corpus and leaves it looking like a corpus nobody has "
            "ingested; check the rule with the largest count against one real response",
            level="warn",
        )
    return Check("refusal rules", True, ", ".join(parts), level="warn")


def _decoder_bindings(root: Path) -> Check:
    """`[decoders]` in `.fux/types.toml` — does every binding still resolve?

    **W-101 item 2.** `registry()` refuses a binding that names a module which
    does not exist, and one that takes an extension away from the decoder that
    claims it — but it refuses them **on the next `fux ingest`**. A consumer
    who deletes `.fux/decoders/confluence.py` and commits learns about the
    line still naming it when the next person's ingest dies.

    ⚠ **The third fault is one only `doctor` can catch**, and it is why this is
    not simply "call `registry()` early". A binding on an extension **no
    document in the corpus has** — a typo'd `jsno = "json"` — resolves perfectly:
    extending is legal by design (ADR-DECODE, `_bind`), so nothing errors, and
    the line indexes nothing forever. That is deliberately not an ingest
    failure, and a report is the right weight for it.

    ⚠ **Counted against the INDEX, not against a directory walk.** The
    committed index is what fux actually holds; walking the tree would report a
    binding as live because an excluded or ignored file happens to carry the
    extension, which is the opposite of the answer. The cost is stated: a
    binding added before the first ingest reads as matching nothing, which is
    true of the index and is what the line says.
    """
    from . import decode

    try:
        decode.registry(root)
    except FuxError as exc:
        return Check("decoder bindings", False, str(exc))

    bindings = decode.declared_bindings(root)
    if not bindings:
        return Check(
            "decoder bindings",
            True,
            f"none declared in {DEFAULT_TYPES_FILE} - every extension resolves through "
            "the decoder modules themselves",
        )

    records = _records(root)
    if not records:
        return Check(
            "decoder bindings",
            True,
            f"{len(bindings)} binding(s) resolve; no index to check them against yet",
            level="warn",
        )
    present = {
        ("." + str(record.get("loc", "")).rsplit(".", 1)[-1]).lower()
        for record in records.values()
        if "." in str(record.get("loc", ""))
    }
    # ⚠ **Only bindings a HUMAN wrote can be reported**, and this line is the
    # whole difference between a check and a wall. `fux setup` writes the
    # entire built-in table into the generated types file, so on a corpus of
    # markdown 27 of 36 bindings match nothing — every one of them correct and
    # none of them news. A check that fires on a fresh, healthy repo is a check
    # people learn to skip, which is the failure `_url_health` and
    # `_accelerator` both record. A binding that differs from the built-in
    # default for its extension is a line somebody typed, and that is the only
    # place a typo can be.
    default = decode.builtin_bindings()
    unused = sorted(
        ext
        for ext, name in bindings.items()
        if ext not in present and default.get(ext) != name
    )
    generated = len(bindings) - len(unused)
    detail = f"{len(bindings)} binding(s) resolve"
    if not unused:
        return Check("decoder bindings", True, detail)
    listed = ", ".join(f"{ext}={bindings[ext]}" for ext in unused[:5])
    more = f" (+{len(unused) - 5} more)" if len(unused) > 5 else ""
    return Check(
        "decoder bindings",
        False,
        f"{detail}; {len(unused)} that is not the built-in default for its extension "
        f"matches no indexed document: {listed}{more}. Extending a decoder to a new "
        f"extension is legal, so this is not an error - but a typo in the extension "
        f"looks exactly like this and indexes nothing. "
        f"({generated} generated binding(s) not checked: an unused one is what a fresh "
        f"`fux setup` writes)",
        level="warn",
    )


def _recency_prior(root: Path) -> Check:
    """Does any document carry an `mtime` — i.e. is the recency prior alive?

    **Filed 2026-09-05 while checking W-111's tie-break, and it is a silent
    total loss.** `mtime` is written by `ingest/priors.py` from
    `git_commit_times`, which walks git. A corpus **copied out of** its
    repository is a plain directory, so **every** document loses its `mtime`
    and the whole recency prior switches off with nothing anywhere reporting
    it. `fux-benchmark`'s 10 000-document corpus is exactly that, and every
    measurement over it that touched recency measured the prior turned off.

    ⚠ **The severity depends on the knob, and both cases are reported.** With
    `recency_half_life_days = 0` the prior is off anyway and a missing `mtime`
    costs nothing today — but it is still the fact a future sweep of that knob
    has to know, so it is stated rather than suppressed. With the knob **on**,
    a corpus with no `mtime` is a configured prior that is a no-op, which is
    the shape this repo has now recorded three times (`superseded_weight`,
    `rerank_weight`, and now this one arriving from the data side).

    A **warning**, never an error: a corpus with no git history is a legitimate
    corpus, and this is a fact about the input rather than a broken install.
    """
    records = _records(root)
    if not records:
        return Check("recency prior", True, "no readable index", level="warn")
    # ⚠ **The `load` call is guarded and the attribute read is NOT**, and that
    # asymmetry is deliberate. A malformed `tune.toml` is a fact about the repo
    # that another check reports, so it degrades to the engine default here; a
    # renamed field is a bug in *this* function, and wrapping the read would
    # make it silently report `half-life 0 (off)` forever. It did, for the
    # length of one edit — `Tune` is flat, and `tune.ranking.…` raised straight
    # into the `except`.
    from .tune import DEFAULT_TUNE
    from .tune import load as load_tune

    try:
        tune = load_tune(root)
    except Exception:
        tune = DEFAULT_TUNE
    half_life = tune.recency_half_life_days

    with_mtime = sum(1 for record in records.values() if record.get("mtime"))
    total = len(records)
    if with_mtime == total:
        return Check(
            "recency prior",
            True,
            f"every one of {total} document(s) carries an mtime"
            + (f"; half-life {half_life:g} day(s)" if half_life > 0 else "; half-life 0 (off)"),
        )
    if with_mtime == 0:
        note = (
            f"NO document carries an mtime, so the recency prior is off for the whole "
            f"corpus. mtime is derived from git commit times, so a corpus copied out of "
            f"its repository - or one that was never in git - has none"
        )
        if half_life > 0:
            note += (
                f". recency_half_life_days is set to {half_life:g}, so a prior you have "
                f"configured is doing nothing"
            )
        return Check("recency prior", False, note, level="warn")
    return Check(
        "recency prior",
        half_life <= 0,
        f"{with_mtime} of {total} document(s) carry an mtime"
        + (
            f"; the other {total - with_mtime} are outside git history and the "
            f"{half_life:g}-day prior cannot decay them"
            if half_life > 0
            else "; half-life 0 (off)"
        ),
        level="warn",
    )


def freshness_counts(root: Path) -> dict[str, int]:
    """Verified-citation verdicts, by label, from the local receipt journal.

    **This is the veto check for two accepted records** —
    [ADR-ACQUIRED](../../docs/adr/0050_acquired-plane.md) and
    [ADR-URL-FRESHNESS](../../docs/adr/0052_url-freshness.md) both say
    *"reopen this decision if `as-ingested` exceeds a quarter of verified
    citations"* and both name `fux doctor --json` as how to check it. Until
    this existed neither veto could be run at all.

    ⚠ **The journal is the ONLY durable source, and it is opt-in.** A freshness
    verdict is produced at answer time by the refer plane and nothing else
    persists one; `.fux/runtime/provenance.jsonl` holds it only for answers run
    with `--journal`. So a repo that has never journalled has **no** answer
    here, which is reported as *unknown* rather than as a zero share — the two
    are different claims and collapsing them would let a repo that has never
    looked read as a repo that looked and found nothing.

    ⚠ **Local and gitignored (L8).** Everything read here lives under
    `.fux/runtime/`, reaches no committed byte, and goes nowhere.
    """
    try:
        from .query import provenance
    except Exception:  # pragma: no cover - the package is always importable
        return {}
    counts: dict[str, int] = {}
    for entry in provenance.read_journal(root):
        predicate = entry.get("predicate") if isinstance(entry, dict) else None
        if not isinstance(predicate, dict):
            continue
        for verdict in predicate.get("verdicts") or []:
            if not isinstance(verdict, dict):
                continue
            label = verdict.get("freshness")
            if isinstance(label, str) and label:
                counts[label] = counts.get(label, 0) + 1
    return counts


#: The share above which `as-ingested` stops meaning *"a rare unreachable
#: source"* and starts meaning *"the fetch path is broken and the plane is
#: masking it"*. **Not a threshold this check invented** — it is the reopen
#: condition written into ADR-ACQUIRED and ADR-URL-FRESHNESS, quoted here so
#: the number has one home.
AS_INGESTED_VETO_SHARE = 0.25


def _freshness_share(root: Path) -> Check:
    """The `as-ingested` share — ADR-ACQUIRED and ADR-URL-FRESHNESS's veto.

    See `freshness_counts` for where the numbers come from and why the journal
    is the only source. The machine-readable form is `fux doctor --json`'s
    `freshness` block, which is what both records tell a reader to compare.

    A **warning** at the veto share, never an error: crossing it means a
    *decision* should be reopened, which is a person's work and not a broken
    install.
    """
    counts = freshness_counts(root)
    total = sum(counts.values())
    if not total:
        return Check(
            "freshness verdicts",
            True,
            "no receipts journalled - run an answer with `--journal` to record verdicts. "
            "Until then the as-ingested share (ADR-ACQUIRED and ADR-URL-FRESHNESS's veto "
            "condition) cannot be computed",
            level="warn",
        )
    as_ingested = counts.get("as-ingested", 0)
    share = as_ingested / total
    listed = ", ".join(f"{label} {counts[label]}" for label in sorted(counts))
    detail = f"{total} verified citation(s) journalled: {listed}"
    if share > AS_INGESTED_VETO_SHARE:
        return Check(
            "freshness verdicts",
            False,
            f"{detail} - as-ingested is {share:.0%}, past the {AS_INGESTED_VETO_SHARE:.0%} "
            "reopen condition in ADR-ACQUIRED and ADR-URL-FRESHNESS. That reads as a broken "
            "fetch path being masked by the retained bytes, not a rare unreachable source",
            level="warn",
        )
    return Check("freshness verdicts", True, f"{detail} - as-ingested {share:.0%}", level="warn")


def _output_config_health(root: Path) -> Check:
    """`.fux/output.toml` absent — the repo that predates the file.

    ADR-OUTPUT decision 19 made a missing file a hard `FuxError` at load time.
    The file is write-if-missing (ADR-DOTFUX decision 6), so it reaches **new
    repos only** — which made `ask`, `find` and `doctor` exit 1 in every repo
    that predates it, `doctor` included, the verb you would run to find out
    why. Decision 20 ruled the fork: a missing file resolves to the engine
    defaults, and the repo is reached HERE instead.

    ⚠ **This is decision 6's own prescribed mechanism**, the same one
    `_types_health` implements for the types list: *"if a change must reach
    existing repos, the mechanism is a loader refusal or a `doctor` check —
    never a rewrite"*. The refusal is what broke them, so this is the check.

    A **warning**, never an error. Nothing is wrong with a repo that has no
    `.fux/output.toml`: every verb runs, and every default is the engine's
    own. What the consumer loses is the ability to CHANGE one — and the MCP
    surface, which has no flags, cannot be configured at all without it. That
    is worth a line; it is not a broken repo.
    """
    path = root / output_config.OUTPUT_NAME
    if path.is_file():
        return Check("output.toml present", True, f"{output_config.OUTPUT_NAME}: output defaults are configurable")
    return Check(
        "output.toml present",
        False,
        f"{output_config.OUTPUT_NAME} is absent, so every output default is the engine's own "
        f"and none can be changed - run `fux output > {output_config.OUTPUT_NAME}` to write "
        "the current defaults out (this is the only way to configure `fux mcp`, which has no flags)",
        level="warn",
    )


def _types_health(root: Path) -> Check:
    """Will the committed types list load — the shape that stops ingest.

    Three ways it cannot, each of which `read_types` refuses:

    1. **A leftover `.fux/sources/types`.** The list moved to `.fux/types.toml`
       on 2026-09-11 (ADR-TYPES decision 12), and a repo that ran `fux setup`
       before then still has the old file. ADR-DOTFUX decision 6: when a change
       must reach existing repos the mechanism is *a loader refusal or a
       `doctor` check, never a rewrite* — this row is the check, and it names
       the command that converts.
    2. **A file that does not parse or breaks the closed key set.**
    3. **A file that admits nothing.** A present file replaces the built-in
       default entirely (ADR-TYPES decision 2), so an empty one would silently
       empty the index — `fux setup` once wrote exactly that, and **`setup`
       then `ingest` failed on every fresh repo** until 2026-08-27.
    """
    from .ingest import typesfile

    try:
        listed = typesfile.read(root, DEFAULT_TYPES_FILE)
    except FuxError as exc:
        return Check("types list usable", False, str(exc))
    except OSError as exc:
        return Check("types list usable", False, f"{DEFAULT_TYPES_FILE}: {exc}")
    if listed is None:
        return Check("types list usable", True, "absent - the built-in default applies")
    if listed.allow:
        return Check(
            "types list usable",
            True,
            f"{DEFAULT_TYPES_FILE}: {len(listed.include)} include glob(s), "
            f"{len(listed.decoders)} decoder binding(s)",
        )
    return Check(
        "types list usable",
        False,
        f"{DEFAULT_TYPES_FILE} admits nothing - `include` and `[decoders]` are both empty - so "
        "`fux ingest` refuses to run. Delete the file to take the built-in default, or re-run "
        "`fux setup` after deleting it to get the default written out",
    )


def _fetcher_capabilities(root: Path) -> Check:
    """Which optional fetcher functions the consumer's own file implements.

    **The gap this closes, measured 2026-08-28:** a repo created before
    [ADR-FETCHER](../../docs/adr/0019_fetcher.md) decision 12 learned **0 of 7**
    `validate()` tokens until its `http.py` was replaced by hand. `fux setup` is
    write-if-missing and never rewrites a consumer's fetcher — the freeze
    ADR-DOTFUX decision 6 names — so a new optional function reaches new repos
    only, silently, and the optimisation that never runs is indistinguishable
    from one that ran and found nothing.

    ⚠ **A NOTICE, never a rewrite.** ADR-DOTFUX decision 6 names the mechanism
    for a change that must reach an existing repo: *a loader refusal or a
    `doctor` check, never a rewrite.* `_types_health` is the precedent. Rewriting
    a consumer's committed fetcher would be a worse problem than the one it
    solves, which is why the record left this stated-as-a-cost rather than
    proposing a loader that edits their file.

    A **warning**, never an error: every function checked here is optional by
    contract, a fetcher without them is correct and supported, and reporting a
    supported configuration as a failure trains people to ignore a red doctor —
    the same reasoning `_url_health` and `_accelerator` record.
    """
    from .config import load as load_config

    name = "fetcher optional functions"
    try:
        url_source = load_config(root).url
    except FuxError:
        # An unreadable/absent `fux.toml` is `_repo_root`'s business, not this
        # check's. The message is NOT interpolated: a FuxError carries an
        # em-dash, and every detail here is ASCII by invariant.
        return Check(name, True, "skipped (no readable fux.toml)", level="warn")
    if url_source is None:
        # No `[sources.url]` at all: this repo does not fetch, so which
        # optional functions its fetcher implements is not a fact about it.
        return Check(name, True, "skipped (no [sources.url] - this repo does not fetch)", level="warn")
    rel = url_source.fetcher
    path = root / rel
    if not path.is_file():
        return Check(name, True, f"{rel}: absent - run `fux setup` to write the shipped fetchers", level="warn")

    # Read the source; never import it. Importing a consumer's fetcher runs
    # their module-level code, and `doctor` is offline by this module's
    # contract -- a fetcher is free to open a session at import time.
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return Check(name, False, f"{rel}: {exc}", level="warn")

    #: Optional by contract, each with the record that added it and what a
    #: consumer forfeits by not having it. `fetch` is NOT here -- it is
    #: mandatory and `load_fetcher` already refuses without it.
    optional = [
        ("validate", "ADR-FETCHER decision 12", "re-fetches every URL body even when unchanged"),
        ("is_rate_limited", "ADR-FETCHER decision 13", "cannot tell a 429 from a hard failure"),
    ]
    missing = [(fn, rec, cost) for fn, rec, cost in optional if f"def {fn}(" not in text]
    if not missing:
        return Check(name, True, f"{rel}: implements {', '.join(fn for fn, _, _ in optional)}", level="warn")
    return Check(
        name,
        True,  # optional by contract: absence is legal, so this never fails the command
        f"{rel} does not implement "
        + "; ".join(f"`{fn}()` ({rec}) - {cost}" for fn, rec, cost in missing)
        + ". Your fetcher is yours and fux will not rewrite it: copy the function from "
        "`fux setup`'s current template, or ignore this if it does not suit your network",
        level="warn",
    )


def _ignore_health(root: Path) -> Check:
    """`.fux/.fuxignore` parses, and states nothing the old lists also state.

    **Two failures, one check, and neither is fatal to `doctor`'s exit code by
    accident.** A `.fuxignore` that will not parse stops `fux ingest` outright,
    so it is an `error`; a pattern written in both `.fuxignore` and a
    `sources/` `!` line changes nothing today and is a `warn`.

    ⚠ **The duplicate is worth a line precisely because it is currently
    harmless.** `!` subtracts in `sources/` and re-includes in `.fuxignore`, so
    the two copies agree only for as long as nobody edits either one. The day
    someone puts a `!` in front of the `.fuxignore` copy they get the opposite
    of what the other file says, silently. This check is early for that.
    """
    from .ingest import fuxignore

    path = root / fuxignore.IGNORE_FILE
    if not path.is_file():
        return Check("fuxignore usable", True, f"{fuxignore.IGNORE_FILE} absent - nothing ignored")
    try:
        rules = fuxignore.read(root).rules
    except (FuxError, OSError) as exc:
        return Check("fuxignore usable", False, f"{fuxignore.IGNORE_FILE}: {exc}")
    duplicates = fuxignore.duplicate_warnings(root, dirs_file=DEFAULT_DIRS_FILE)
    if duplicates:
        return Check(
            "fuxignore usable",
            False,
            f"{len(duplicates)} pattern(s) stated in both {fuxignore.IGNORE_FILE} and "
            f"{DEFAULT_DIRS_FILE} - run `fux ingest --list-skipped` for the detail",
            level="warn",
        )
    active = sum(1 for r in rules if not r.negate)
    return Check(
        "fuxignore usable",
        True,
        f"{fuxignore.IGNORE_FILE}: {active} ignore rule(s), {len(rules) - active} re-include(s)",
    )


def _url_health(root: Path) -> Check:
    """The `url:` half of the corpus, reported (W-82 §3.1).

    Doctor had **no URL check at all**, which is the defect: a URL that has
    failed every fetch for a month looked exactly like one fetched a minute ago.
    [ADR-URL-INGEST](../../docs/adr/0008_url-ingest.md) decision 4 keeps the
    prior record on a failed fetch — correct, because a flaky network must never
    present as a deletion — and the cost of that rule is that **a permanently
    dead URL lives in the index forever**. This makes the cost visible.

    **Report, never auto-delete**, and **never fetch**: doctor stays offline
    (this module's contract), so every number here comes from the committed
    index and a gitignored counter file. It says what the last networked run
    saw; it does not go looking.

    A **warning**, never an error. A stale or failing URL means the index is
    behind, which is a fact about the world rather than a broken install, and
    reporting it as a failure would train people to ignore a red doctor —
    the same reasoning `_accelerator` records.
    """
    from .maintain import urlstate

    try:
        from .store import reader

        indexed = [doc_id[4:] for doc_id in reader.read_index(root) if doc_id.startswith("url:")]
    except Exception:
        # An unreadable or absent index is another check's business, not this
        # one's. Reporting "cannot tell" beats a traceback on a health command.
        return Check("url sources", True, "skipped (no readable index)", level="warn")

    state = urlstate.read(root)
    summary = urlstate.summarize(state, indexed)
    policy = _parallel_policy(root)

    def _rate_limit_note() -> str | None:
        """W-82 ruling 12, cumulative across runs.

        ⚠ **Reported in BOTH branches, deliberately.** A host refusing you is a
        fact about the host, not about how many URLs are indexed — and the
        no-URLs branch is exactly where a rate limit is most likely to be the
        REASON nothing is indexed.

        ⚠ **Reaching both branches took two fixes, and the second was worse.**
        The note was first built into the populated branch only, so it was
        invisible in the one case that produces it. Adding the empty branch
        then put the caller's `", ".join(parts)` ABOVE the append, which killed
        it in the populated branch instead — a working report in the rare case
        and a dead one in the common case, for a whole release. Neither was
        caught by a test, because until now there was none; both were found by
        reading the code, which is the weakest way to find either.

        **Never names a number to set `max_parallel` to.** That is the
        consumer's call; fux picking it would be the clamping ruling 12
        refused.
        """
        if not state.rate_limited:
            return None
        worst = sorted(state.rate_limited.items(), key=lambda kv: (-kv[1], kv[0]))
        return "rate-limited by " + ", ".join(f"{host} x{count}" for host, count in worst[:3])

    if not summary.has_urls:
        # ⚠ The concurrency belongs in THIS branch above all (W-83). An empty
        # corpus with `[sources.url]` configured is a repo about to run its
        # first `fux add <URL>` — the moment the number matters most and the
        # only moment nobody can look it up from a previous run.
        bits = ["none indexed"]
        if policy is not None:
            bits.append(policy)
        note = _rate_limit_note()
        if note is not None:
            bits.append(note)
        return Check("url sources", True, ", ".join(bits), level="warn")

    parts = [f"{summary.indexed} url: record(s)"]
    if summary.run_seq == 0:
        parts.append("no networked run recorded yet - run `fux update`")
    else:
        parts.append(f"{summary.confirmed_last_run} confirmed by the last run")
    if summary.never_confirmed:
        parts.append(f"{summary.never_confirmed} never re-fetched since first ingest")
    if summary.failing:
        parts.append(f"{summary.failing} failing")
    if policy is not None:
        parts.append(policy)
    note = _rate_limit_note()
    if note is not None:
        parts.append(note)
    # ⚠ The join stays BELOW every append. It sat above the rate-limit
    # append once, and the note was built, appended to a list nothing read
    # again, and silently dropped -- correct in the empty branch, dead here.
    detail = ", ".join(parts)
    if summary.failing_urls:
        # Named, not just counted: a count tells you something is wrong and a
        # name tells you which line of `.fux/sources/urls` to go and look at.
        listed = ", ".join(summary.failing_urls[:5])
        more = f" (+{len(summary.failing_urls) - 5} more)" if len(summary.failing_urls) > 5 else ""
        detail += (
            f" - failed {urlstate.FAILING_STREAK}+ runs in a row: {listed}{more}. "
            "fux never deletes a URL record; remove the line from .fux/sources/urls yourself"
        )
    return Check("url sources", not summary.failing_urls, detail, level="warn")


def _parallel_policy(root: Path) -> str | None:
    """How many URLs a networked verb may open at once — W-83.

    **The number a person needs before running `fux update` over a corporate
    wiki**, said by the one command whose job is to tell them what will happen.
    Without it the only way to learn the concurrency was to read `config.py`.

    ⚠ **This reports POLICY and refuses to compute the product**, and that is a
    constraint rather than laziness. The effective value is
    `min(configured, declared)`, and `declared` lives in a **consumer-owned
    Python file** — reading it means importing it, which runs whatever is at
    that file's module level. `fux doctor` is the command a person runs when
    something is already wrong; it may not be the command that executes their
    fetcher. So it names the rule and lets `fux update` apply it.
    """
    from .config import load

    try:
        url = load(root).url
    except Exception:
        # No readable fux.toml is `_config`'s finding to report, not this
        # function's, and a health command must not raise twice for one cause.
        # ⚠ Since W-85 this also swallows the *missing `max_parallel`* refusal —
        # correctly: that error belongs to whichever command the person actually
        # ran, stated once, not repeated as a doctor line.
        return None
    if url is None:
        # No `[sources.url]` at all: there is no fetching to bound, and a
        # concurrency figure for a source that does not exist is noise on a
        # command whose whole value is that its output is worth reading.
        return None
    # No "unset" branch since W-85: `max_parallel` is required, so a loaded
    # `UrlSource` always carries a real number. A fallback here would be dead
    # code that reads like reassurance.
    return (
        f"fetches <= {url.max_parallel} at a time "
        "(max_parallel; also capped by your fetcher's MAX_PARALLEL)"
    )


def _accelerator(root: Path) -> Check:
    """The derived accelerator: present, fresh, and genuinely not committed.

    A **warning**, never an error. The accelerator is disposable by design —
    `ask` answers correctly from the scan without it — so a missing or stale
    one costs speed, not correctness. Reporting it as a failure would train
    people to ignore a red doctor.
    """
    from .derive import format as derive_fmt
    from .derive.accel import is_fresh

    directory = derive_fmt.runtime_dir(root)
    if not (directory / derive_fmt.STATS_NAME).exists():
        return Check(
            "accelerator",
            True,
            "not built - `ask` uses the reference scan; run `fux build` for the fast path",
            level="warn",
        )

    tracked = _is_git_tracked(root, directory)
    if tracked:
        return Check(
            "accelerator",
            False,
            ".fux/runtime/ is TRACKED by git - it is a derived plane and must not be "
            "committed; check .fux/.gitignore lists `runtime/` (ADR-DOTFUX)",
            level="warn",
        )

    if not is_fresh(root):
        return Check(
            "accelerator",
            True,
            "stale (the committed index changed since it was built) - `ask` falls back "
            "to the scan; run `fux build`",
            level="warn",
        )
    return Check("accelerator", True, f"fresh, derived, untracked ({directory})", level="warn")


def _is_git_tracked(root: Path, path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(path)],
            cwd=root,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _is_git_ignored(root: Path, path: Path) -> bool | None:
    """True/False from `git check-ignore`, or None when git can't answer."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", str(path)],
            cwd=root,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None  # 128: not a repository, or any other git failure


def cmd_doctor(args) -> int:
    checks = run()
    exit_code = 0 if all(c.ok for c in checks if c.level == "error") else 1

    if getattr(args, "json", False):
        # W-66 Phase 4 / ADR-CLI, 2026-08-22: `doctor` had no machine-readable
        # form, and a status an agent cannot parse is not a status for this
        # product's actual audience. The runner block is lifted out beside the
        # checks rather than left as prose inside `detail`, because a caller
        # asking "is a re-index pending" should not have to parse a sentence.
        import json as json_mod

        from .config import find_root

        root = find_root()
        payload = {
            "ok": exit_code == 0,
            "version": __version__,
            "checks": [
                {"name": c.name, "ok": c.ok, "level": c.level, "detail": c.detail} for c in checks
            ],
        }
        if root is not None:
            from .maintain import runner

            payload["runner"] = runner.status(root)
            # ⚠ **Lifted out beside the checks for the runner block's reason,
            # and this one is load-bearing rather than convenient.**
            # ADR-ACQUIRED and ADR-URL-FRESHNESS both say to check their veto
            # with `fux doctor --json` — *"the `as-ingested` count against
            # total verified citations"* — and a caller doing that must not
            # have to parse an English sentence out of `detail`. An empty
            # object means no receipts are journalled, which is *unknown* and
            # not a zero share; `freshness_counts` says why they are different.
            payload["freshness"] = freshness_counts(root)
        print(json_mod.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    for check in checks:
        # ASCII only — Windows' default console codepage (cp1252/"charmap")
        # can't encode U+2714/U+2717 and the process crashes on print()
        # rather than degrading; caught by CI's windows runners.
        mark = "OK" if check.ok else ("WARN" if check.level == "warn" else "FAIL")
        print(f"[{mark}] {check.name}: {check.detail}")
    return exit_code
