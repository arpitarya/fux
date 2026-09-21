"""`fux doctor` — install/environment health check.

Checks today: python version, repo root found, `.fux/` writable, which `fux`
PATH resolves (SR-NODE-SEARCH R1a), and the two
layout assertions from SR-DOTFUX — the committed index is not git-ignored, and
nothing undeclared sits at the top level of `.fux/`.

The index check exists because the failure it catches is silent: a `.fux/*`
line in any `.gitignore` up the tree, or a consumer-edited `.fux/.gitignore`,
drops the committed index out of git with no error anywhere. Doctor stays
offline — it never touches the fetcher or the network.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .config import DEFAULT_DIRS_FILE, DEFAULT_TYPES_FILE, FETCHERS_DIR, find_root
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
    a foreground `fux ingest`.
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
            f"({reason}) - run `fux ingest` to see them all",
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
    checks = [Check("repo root", True, str(root)), _config_loads(root)]
    fux_dir = root / ".fux"
    # 🔴 **This CREATED `.fux/` until 2026-09-12** (W-140 row 7). `doctor` is
    # read-only by contract — it is the first line of this record and of the
    # README — and a health command that materialises the directory it is
    # reporting on has already changed the answer. On a repo with no `.fux/` it
    # left `.fux/` behind, and (through `maintain/daemon.py`'s path helper)
    # `.fux/runtime/CACHEDIR.TAG` with it.
    #
    # **The writability question is still answered**, on the directory that
    # would have to be written: `.fux/` when it exists, the repo root when it
    # does not — which is exactly what `fux setup` or the next `ingest` needs.
    # The probe file is removed on every path, including failure.
    target = fux_dir if fux_dir.is_dir() else root
    note = "" if target == fux_dir else " (.fux/ absent — probing the repo root)"
    probe = target / ".doctor-probe"
    try:
        probe.write_text("", encoding="utf-8")
        checks.append(Check(".fux/ writable", True, str(target) + note))
    except OSError as exc:
        checks.append(Check(".fux/ writable", False, str(exc)))
    finally:
        try:
            probe.unlink()
        except OSError:
            pass
    checks.extend(_layout(root))
    return checks


def _config_loads(root: Path) -> Check:
    """Does `fux.toml` actually load? An **error**, and the loader's own message.

    🔴 **Without this row, `fux doctor` reported `[OK]` for a repo where every
    other verb exits 1.** A `fux.toml` the loader refuses — an unknown key, a
    missing `max_parallel`, malformed TOML — takes `ingest`, `ask` and the rest
    out, while `doctor` printed `fetcher optional functions: skipped (no
    readable fux.toml)` at **warn** level and called the run green. The one verb
    whose job is to name the fix was the one verb that did not name it.

    - **The loader's message is reproduced verbatim, not paraphrased.** It
      already names the key and what is wrong with it; a second wording of the
      same failure is a restatement that can drift from the thing enforcing it.
    - **`error`, not `warn`.** Every downstream check that touches config
      degrades to a skipped warning by design — each is individually correct to
      do so, and collectively they made the whole command green. This row is
      what makes the *cause* fail, so the skips can stay warnings.
    - **A missing `fux.toml` is NOT this check's failure.** `find_root` accepts
      a `.git`-only directory, and a repo with no `fux.toml` has nothing to
      refuse — that is `repo root`'s finding, and `fux setup`'s job.
    """
    from .config import load as load_config

    name = "fux.toml loads"
    if not (root / "fux.toml").is_file():
        # `find_root` accepts a bare `.git` checkout. Nothing to load, nothing
        # to refuse — reporting a failure here would fire on every repo that
        # simply has not run `fux setup` yet.
        return Check(name, True, "no fux.toml (run `fux setup` to write one)", level="warn")
    try:
        load_config(root)
    except FuxError as exc:
        # Verbatim, and the only place doctor renders a loader error. It may
        # carry an em-dash, which is why nothing here interpolates it into an
        # ASCII-by-invariant string.
        return Check(name, False, str(exc))
    return Check(name, True, "fux.toml")


def _layout(root: Path) -> list[Check]:
    """SR-DOTFUX: the index must not be ignored; `.fux/` holds only declared entries."""
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

    checks.append(_index_temp_ignored(root))

    fux_dir = root / fuxdir.FUX_DIR
    extras = sorted(p.name for p in fux_dir.iterdir() if p.name not in fuxdir.DECLARED) if fux_dir.is_dir() else []
    checks.append(
        Check(
            ".fux/ layout declared",
            not extras,
            f"undeclared entries: {', '.join(extras)} - see .fux/README.md and SR-DOTFUX"
            if extras
            else "every entry is declared",
            level="warn",
        )
    )
    checks.append(_output_config_health(root))
    checks.append(_tune_config_health(root))
    checks.append(_types_health(root))
    checks.append(_ignore_health(root))
    checks.append(_dirs_exclusions_migrated(root))
    checks.append(_stale_redaction(root))
    # W-163 — the setup-drift rows. Grouped here, after the files they read
    # have each had their own "does it load" row: a stale key set is only worth
    # reporting about a file that parses, and two rows saying different things
    # about one broken file is how a reader learns to trust neither.
    checks.append(_retired_agent_folders(root))
    checks.append(_readme_current(root))
    checks.append(_starter_refusals_untouched(root))
    checks.extend(_frozen_keys(root))
    checks.append(_unbound_types(root))
    checks.append(_listed_dirs_exist(root))
    checks.append(_thin_urls(root))
    checks.append(_confidence_floors(root))
    checks.append(_fetcher_capabilities(root))
    checks.append(_accelerator(root))
    checks.append(_node_reader(root))
    checks.append(_fux_on_path())
    checks.append(_background_runner(root))
    daemon_check = _daemon(root)
    if daemon_check is not None:
        checks.append(daemon_check)
    checks.append(_url_health(root))
    checks.append(_acquired_health(root))
    checks.append(_pinned_without_bytes(root))
    checks.append(_fetcher_config_tables(root))
    checks.append(_fetcher_bindings(root))
    checks.append(_fetcher_routes(root))
    checks.append(_pinned_fetchers(root))
    checks.append(_register(root))
    checks.append(_suspended_pins(root))
    checks.append(_observers(root))
    checks.append(_pii_health(root))
    checks.append(_refusal_health(root))
    checks.append(_decoder_bindings(root))
    checks.append(_meta_fields(root))
    checks.append(_provenance(root))
    checks.append(_recency_prior(root))
    checks.append(_no_op_priors(root))
    checks.append(_freshness_share(root))
    return checks


#: The ranking priors that ship at a value which makes them do nothing, with
#: the record field each one reads.
#:
#: `(key, no-op value, record field, what the field means)`. `None` for the
#: field means the prior is not driven by a per-record declaration.
#:
#: ⚠ **There were FOUR until 2026-09-13 and there is ONE.** Arpit ruled all
#: three DOCUMENT priors closed that day on VERDICT-W143's evidence —
#: `superseded_weight` (W-151), then `archived_weight` and
#: `recency_half_life_days` (W-152). A prior no single global value can set
#: correctly is not a prior waiting for a number, and disclosing it as one was
#: misleading. **The facts they read all survive and all reach a caller.**
#:
#: `rerank_weight` is the survivor and was never the same question: it ships
#: **off** rather than neutral, acts on refer-plane passage proximity rather
#: than a document flag, and its open question is cost, not which value (W-154).
_NO_OP_PRIORS = (
    ("rerank_weight", 0.0, None, ""),
)


def _no_op_priors(root: Path) -> Check:
    """Every ranking prior that is BUILT, WIRED and SWITCHED OFF at its default.

    **W-126 part B, on Arpit's ask of 2026-09-11.** Four mechanisms — the
    archived demotion, the supersession demotion, the proximity reranker and the
    recency decay — were each implemented, each read their input, and each
    shipped at a value that made them return the score unchanged, with nothing
    telling the repo that declared `archived=true` it was getting nothing.

    🔴 **THREE OF THE FOUR WERE REMOVED ON 2026-09-13** rather than tuned
    (W-151, W-152; SR-TUNE decision 15), which is the disclosure working: once
    a dead knob is visible, *"what value should it be?"* turns out to be the
    wrong question, and **no single global value clears the bar for any of them**
    (`work/regression/2026-09-12-priors-and-tables/VERDICT-W143.md`).

    **What is left is `rerank_weight`**, which ships **off** rather than neutral
    and whose open question is cost, not which value. This row keeps disclosing
    it, and keeps refusing to recommend one.

    ⚠ **This is a DISCLOSURE and not a ranking change**, and the distinction is
    the whole reason it could be built today. Whether any of these defaults
    should move is blocked on a measurement nobody can run yet (the hand-graded
    corpus is uncommitted), and Arpit ruled *remeasure first* on
    `superseded_weight` and `rerank_weight` the same day.

    🔴 **So it REFUSES to recommend a value, deliberately.** Recommending one is
    the remeasure's job. `P-SUPERSEDE` is the standing proof of why: at `0.5`
    the supersession prior fixed two queries and **broke two**, and every
    broken query had the superseded document as its correct answer. A `doctor`
    row that said *"try 0.5"* would have been handing out the exact change a
    frozen pre-registration already failed — and in the end that knob, and the
    two beside it, were deleted rather than given a number.

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
            # 🔴 **SWITCHED OFF and UNREACHABLE are different problems with
            # different remedies, and printing the count alone left a reader to
            # notice the zero.** Changing the value fixes the first and does
            # nothing whatever about the second. Measured 2026-09-11: three of
            # the four priors returned BYTE-IDENTICAL results at every value
            # including 0.0 on a corpus that declares none of what they read,
            # and the premise that they were testable there had stood in the
            # queue for two weeks because the documents discuss supersession in
            # PROSE while declaring none of it.
            #
            # ⚠ **It states a fact and still recommends nothing.** *"0 documents,
            # so this knob is inert here"* is derived from data already in hand;
            # *"0 documents, so set it to X"* would be the R10 failure this row
            # exists to refuse.
            if declared == 0:
                part += " - so changing this value would change NOTHING in this repository"
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
        "returns the score unchanged. fux states this and does NOT recommend a "
        "value: the one change ever measured (superseded_weight at 0.5, a knob "
        "since REMOVED) fixed two queries and broke two, and every broken one had "
        "the superseded document as its correct answer",
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

    # SR-PII decision 17: a missing file is an ERROR row -- `load` raises and
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
    # ⚠ **`tools/pii-probe/` is in the fux REPOSITORY, not in the wheel**
    # (W-140 row 18): `packages = ["src/fux"]`. Pointing a consumer at a path
    # they do not have is worse than pointing at nothing, so this names the
    # skill `fux setup` wrote into their repo, which carries a copy.
    note += ". A big number is a hint, not a finding: probe it (the `fux-pii` skill carries the script)"
    return note


def _fetcher_config_tables(root: Path) -> Check:
    """`[sources.url.config.<name>]` sub-tables that name no fetcher file.

    **The whole point of the two-level table is that a key reaches exactly one
    fetcher** — so a sub-table whose name matches no `.py` in the fetchers
    directory reaches *none*, silently. That is the defect
    [SR-CONFIG](../../records/0113_config.md) decision 14 exists for, one level
    down: a setting its author believes is in force.

    ⚠ **A row here rather than a refusal in `config.load`**, and the reason is
    which module may touch the disk. The loader parses a file; deciding whether
    `[sources.url.config.wiki]` is a typo means listing
    `.fux/fetchers/` — a filesystem question, in a function whose job is TOML.
    `doctor` is the module that already asks filesystem questions about config.
    """
    from .config import load as load_config

    name = "fetcher config tables"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "no readable fux.toml - another check owns that")
    if config.url is None or not config.url.config:
        return Check(name, True, "no [sources.url.config] to check")

    named = sorted(k for k, v in config.url.config.items() if isinstance(v, dict))
    if not named:
        return Check(name, True, "only shared keys - every fetcher gets them")

    fetchers_dir = root / FETCHERS_DIR
    try:
        stems = {p.stem for p in fetchers_dir.glob("*.py")}
    except OSError:
        stems = set()
    orphans = [n for n in named if n not in stems]
    if not orphans:
        return Check(name, True, f"{len(named)} per-fetcher table(s), each naming a fetcher on disk")
    return Check(
        name,
        False,
        f"[sources.url.config.{orphans[0]}]"
        + (f" and {len(orphans) - 1} more" if len(orphans) > 1 else "")
        + f" name(s) no fetcher: {fetchers_dir}/ has {sorted(stems) or 'nothing'}. "
        "These keys reach NO fetcher and nothing else says so - rename the table "
        "to the fetcher's filename without .py, or delete it",
    )


def _fetcher_routes(root: Path) -> Check:
    """The host-to-fetcher map — SR-FETCHER decision 16's three faults.

    🔴 **Offline, and it never imports a fetcher.** `ROUTES` is read with `ast`
    (`ingest/routes.claims`), for the reason `_fetcher_capabilities` reads a
    fetcher as text: importing consumer Python on `doctor`'s path is L4 lost
    where nothing would notice — a fetcher is free to open a session at import.

    Three faults, and the levels differ because the costs do:

    - **failure** — a route naming no file on disk. Every URL it matches is
      unfetchable and `fux add` will refuse.
    - **failure** — a claim collision: two `ROUTES` patterns matching one host.
      There is no non-arbitrary order between two regexes, and guessing one
      builds a **plausible index retrieved by the wrong fetcher**, which nothing
      downstream detects.
    - **finding** — a route matching no listed URL. Usually a typo, occasionally
      a table written before the URLs are added, so it is never an error alone.
    """
    from .config import load as load_config
    from .ingest import routes as routes_mod
    from .ingest import sourcelist

    name = "fetcher routes"
    try:
        config = load_config(root)
    except FuxError:
        # ⚠ **The exception is NOT quoted into the detail.** A `FuxError`'s
        # message is prose written for a person and may hold an em dash, and a
        # detail must be ASCII for a Windows console
        # (`test_every_check_detail_is_ascii_in_every_branch`). The `fux.toml
        # loads` row already prints the real message, so quoting it here would
        # be a second copy that can crash the command exactly when the repo is
        # already broken.
        return Check(name, True, "skipped (fux.toml does not load - see that row)", level="warn")
    if config.url is None:
        return Check(name, True, "skipped (no [sources.url] - this repo does not fetch)", level="warn")

    table = dict(getattr(config.url, "routes", {}) or {})
    fetchers_dir = root / FETCHERS_DIR
    try:
        claimed = routes_mod.claims(fetchers_dir)
    except FuxError as exc:
        return Check(name, False, str(exc))
    if not table and not claimed:
        return Check(name, True, "no routes and no ROUTES claim - every line is a pin", level="warn")

    try:
        stems = {p.stem for p in fetchers_dir.glob("*.py")}
    except OSError:
        stems = set()

    dangling = sorted(
        f"{pattern} -> {stem}"
        for pattern, stem in list(table.items()) + [(p, s) for p, (s, _) in claimed.items()]
        if stem not in stems
    )
    if dangling:
        return Check(
            name, False,
            f"{len(dangling)} route(s) name a fetcher that is not in {FETCHERS_DIR}/: "
            f"{', '.join(dangling)}. Every URL they match is unfetchable",
        )

    try:
        entries = sourcelist.parse(
            (root / config.url.urls_file).read_text(encoding="utf-8"),
            sourcelist.URLS, origin=config.url.urls_file,
        )
    except (OSError, FuxError):
        entries = []

    hosts = {routes_mod.normalise_host(e.value) for e in entries if not e.exclude}
    merged = {**{p: s for p, (s, _) in claimed.items()}, **table}
    try:
        compiled = routes_mod.validate(merged, where=f"{root}: routes")
    except FuxError as exc:
        return Check(name, False, str(exc))
    for host in sorted(hosts):
        try:
            routes_mod.resolve(host, compiled, where=f"{root}: routes")
        except FuxError as exc:
            return Check(name, False, str(exc))

    unused = sorted(
        pattern for pattern, (_, compiled_re) in compiled.items()
        if not any(routes_mod._matches(pattern, compiled_re, h) for h in hosts)
    )
    total = len(compiled)
    if not unused:
        return Check(name, True, f"{total} route(s), each matching a listed URL")
    return Check(
        name, False,
        f"{total} route(s); {len(unused)} match no listed URL: {', '.join(unused)}. "
        f"Usually a typo, occasionally a table written before the URLs",
        level="warn",
    )


def _pinned_fetchers(root: Path) -> Check:
    """Lines whose `fetch=` pin disagrees with what the routes table now says.

    🔴 **The whole cost of SR-URL-LIST decision 16, made visible.** Arpit ruled
    that every line states a resolved stem, so a route changed later moves
    nothing — this row is the only thing that tells a consumer their table and
    their list have drifted apart, and it names the one-line fix per line.

    ⚠ **It reports and never rewrites.** fux editing the meaning of a committed
    file is what this repository refused when it declined an
    `ingest --unpin-default`.
    """
    from .config import load as load_config
    from .ingest import routes as routes_mod
    from .ingest import sourcelist

    name = "pinned fetchers"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "skipped (fux.toml does not load)", level="warn")
    if config.url is None:
        return Check(name, True, "skipped (no [sources.url])", level="warn")
    table = dict(getattr(config.url, "routes", {}) or {})
    if not table:
        return Check(name, True, "no routes table - nothing for a pin to disagree with", level="warn")
    try:
        entries = sourcelist.parse(
            (root / config.url.urls_file).read_text(encoding="utf-8"),
            sourcelist.URLS, origin=config.url.urls_file,
        )
        compiled = routes_mod.validate(table, where="fux.toml: [sources.url.routes]")
    except (OSError, FuxError):
        return Check(name, True, "skipped (the list or the table does not read)", level="warn")

    drifted = []
    for entry in entries:
        if entry.exclude:
            continue
        pinned = entry.attrs.get("fetch")
        try:
            routed = routes_mod.resolve(
                routes_mod.normalise_host(entry.value), compiled,
                where="fux.toml: [sources.url.routes]",
            )
        except FuxError:
            continue
        if routed is not None and pinned != routed:
            drifted.append(f"{entry.value} pins {pinned}, routes say {routed}")
    if not drifted:
        return Check(name, True, f"{len(entries)} line(s), every pin agreeing with the routes table")
    return Check(
        name, False,
        f"{len(drifted)} line(s) pin a fetcher the routes table would now resolve differently: "
        f"{'; '.join(drifted[:5])}"
        f"{'' if len(drifted) <= 5 else f', and {len(drifted) - 5} more'}. "
        f"Every line is a pin by design - edit the line, or leave it",
        level="warn",
    )


def _register(root: Path) -> Check:
    """`.fux/index/REGISTER` against the index it claims to describe.

    Drift means **the register was committed from a different ingest than the
    index beside it** — the one thing a committed derived file can get wrong,
    and the one nobody reads closely enough to catch by eye.
    """
    from .ingest import register as register_mod
    from .store import reader as reader_mod

    name = "register"
    rows = register_mod.read(root)
    try:
        index = reader_mod.read_index(root)
    except Exception:  # pragma: no cover - no readable index is other rows' business
        return Check(name, True, "skipped (no readable index)", level="warn")
    if not index:
        return Check(name, True, "no index to describe", level="warn")
    if not rows:
        return Check(
            name, False,
            f"no {register_mod.NAME} beside an index of {len(index)} document(s) - "
            f"run `fux ingest` to write one",
            level="warn",
        )
    locs = {r.get("loc", "") for r in index.values()}
    missing = sorted(locs - set(rows))
    extra = sorted(set(rows) - locs)
    if not missing and not extra:
        return Check(name, True, f"{len(rows)} line(s), agreeing with the index")
    parts = []
    if missing:
        parts.append(f"{len(missing)} indexed document(s) with no register line ({missing[0]})")
    if extra:
        parts.append(f"{len(extra)} register line(s) for nothing in the index ({extra[0]})")
    return Check(
        name, False,
        "; ".join(parts) + " - the register was committed from a different ingest "
        "than the index beside it; `fux ingest` rewrites it",
        level="warn",
    )


def _fetcher_bindings(root: Path) -> Check:
    """`fetch=<name>` on a URL line that names no fetcher file.

    **W-178, the mirror of `_decoder_bindings`.** Since `fetch=` became a typed
    attribute the grammar accepts any module-stem name, which is what lets a
    consumer drop `.fux/fetchers/glassbox.py` in and write `fetch=glassbox`. The
    price of an open set is that a **typo** now parses: `fetch=glasbox` is a
    perfectly legal line naming a file nobody wrote.

    🔴 **Without this row, that line is discovered by the next person's ingest
    dying.** `urlsrc._fetcher_path()` raises with a clear message — at fetch
    time, on somebody else's machine, mid-run. **Exactly the argument W-101
    item 2 made for `_decoder_bindings`**, and the reason the two are a pair.

    ⚠ **It reads the LIST, not the index**, which is the opposite choice from
    `_decoder_bindings` and is right for a different reason. A binding is
    interesting when it matches no *document*; a fetcher name is wrong when it
    matches no *file*, and that is true the moment the line is written — before
    any ingest, which is the moment a person can still fix it cheaply.

    ⚠ **Offline, like every doctor check.** It lists a directory and never
    imports a fetcher: importing one runs consumer code that may `connect()`,
    and [SR-DOCTOR](../../records/0152_doctor.md) is the command somebody runs
    when something is already wrong.
    """
    from .config import load as load_config
    from .ingest import sourcelist, urlsrc

    name = "fetcher bindings"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "no readable fux.toml - another check owns that")
    if config.url is None:
        return Check(name, True, "no [sources.url] - no URL lines to resolve")

    path = root / config.url.urls_file
    if not path.is_file():
        return Check(name, True, f"no {config.url.urls_file} yet")
    try:
        entries = sourcelist.parse(
            path.read_text(encoding="utf-8"), sourcelist.URLS, origin=config.url.urls_file
        )
    except (FuxError, OSError) as exc:
        return Check(name, False, f"{config.url.urls_file}: {exc}")

    resolved = urlsrc.resolve_urls(entries, config.url)
    if not resolved:
        return Check(name, True, "no URL lines listed")

    fetchers_dir = root / FETCHERS_DIR
    try:
        stems = {p.stem for p in fetchers_dir.glob("*.py")}
    except OSError:
        stems = set()

    wanted = sorted({e.fetch for e in resolved})
    missing = [n for n in wanted if n not in stems]
    if not missing:
        return Check(
            name,
            True,
            f"{len(wanted)} fetcher name(s) in use, each resolving to a file in "
            f"{fetchers_dir.name}/",
        )
    shown = ", ".join(missing[:3])
    more = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
    return Check(
        name,
        False,
        f"{len(missing)} URL line(s) name a fetcher with no file: {shown}{more}. "
        f"{fetchers_dir}/ has {sorted(stems) or 'nothing'}. Every fetch through one of "
        "these fails at ingest time - write the module, or fix the `fetch=` name",
    )


def _pinned_without_bytes(root: Path) -> Check:
    """`fetch_at_answer = false` with URLs that have no retained bytes.

    **The disclosure SR-URL-FRESHNESS decision 16 chose over a refusal**
    (Arpit, 2026-09-14). `[sources.url] fetch_at_answer = false` says *never
    open a socket at answer time*; a URL with nothing in `.fux/acquired/` then
    has nothing to verify against, and every citation from it comes back
    `unverified` — honest, and silently much weaker than the consumer thinks.

    ⚠ **Refusing at load would have been the wrong shape**, and the precedent
    is this plane's own: [SR-ACQUIRED](../../records/0145_acquired-plane.md)
    resolves the equally lossy `update=never keep=false` pair as *disclosed,
    never refused*, because the combination is coherent for a document that
    genuinely never changes and merely surprising to have chosen by accident.
    A repo mid-migration — `fetch_at_answer` set before a re-ingest with
    `keep=true` — would be locked out by a refusal for no benefit.

    **Silent when the flag is on**, which is the default: there is nothing to
    warn about while fux may still go and look.
    """
    from .config import load as load_config
    from .ingest import urlsrc
    from .store import acquired

    name = "pinned url bytes"
    try:
        config = load_config(root)
    except FuxError:
        return Check(name, True, "no readable fux.toml - another check owns that")
    if config.url is None or config.url.fetch_at_answer:
        return Check(name, True, "fetch_at_answer is on - answers may verify against the source")

    try:
        entries = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
    except (FuxError, OSError):
        return Check(name, True, "no readable url list - another check owns that")
    if not entries:
        return Check(name, True, "fetch_at_answer is off, and no url is listed")

    try:
        manifest = acquired.read_manifest(root)
    except (FuxError, OSError):
        manifest = {}
    missing = sorted(e.url for e in entries if e.url not in manifest)
    if not missing:
        return Check(
            name,
            True,
            f"fetch_at_answer is off; all {len(entries)} url(s) have retained bytes - "
            "citations verify as `as-ingested`",
        )
    # 🔴 **`ok=False`, or this row renders `[OK]`** — see `_suspended_pins`.
    # It shipped as `ok=True, level="warn"` on 2026-09-14 and printed `[OK]`
    # beside *every citation from these will be `unverified`*, which is the
    # disclosure decision 16 chose over a refusal saying nothing at all.
    return Check(
        name,
        False,
        f"fetch_at_answer is off and {len(missing)} of {len(entries)} url(s) have NO retained "
        f"bytes: {', '.join(missing[:3])}"
        + (f" (+{len(missing) - 3} more)" if len(missing) > 3 else "")
        + " - every citation from these will be `unverified`. Set keep = true and re-ingest",
        level="warn",
    )


def _observers(root: Path) -> Check:
    """W-170. What is in `.fux/observers/`, and whether each one fired.

    🔴 **A present-but-never-firing observer is the failure this row exists
    for**, and it is silent by construction: the dispatcher is fail-open, so an
    observer that raises on every run is skipped on every run and fux answers
    normally. Without this row a consumer's analytics can be dead for weeks
    while every query looks perfect — the same shape as a suspended pin, and
    the same remedy: say so, and let a person decide.

    ⚠ **`warn`, never `error`.** A broken observer answers no question wrongly.
    The repository is not broken; somebody's telemetry is, and conflating the
    two would make `fux doctor` exit non-zero in CI over a consumer's own file.

    ⚠ **The liveness file describes the LAST run, so a first-ever `doctor` in a
    repo that has never answered a query reports `not yet observed`** — which
    is true and is not a finding. Reporting it as one would make every fresh
    clone look broken.
    """
    name = "observers"
    try:
        from . import observe
    except Exception:  # pragma: no cover - a check must not take out the command
        return Check(name, True, "not available in this build")
    try:
        present = [p.name for p in observe.observers_in(root)]
    except Exception:
        return Check(name, True, "could not read .fux/observers/")
    if not present:
        return Check(name, True, "none installed")
    state = observe.liveness(root)
    if not state:
        return Check(name, True, f"{len(present)} installed; not yet observed a run")
    fired = set(state.get("fired", ()))
    silent = sorted(n for n in present if n not in fired)
    if not silent:
        return Check(name, True, f"{len(present)} installed, all fired on the last run")
    return Check(
        name,
        False,
        f"{len(silent)} of {len(present)} observer(s) did NOT fire on the last run: "
        f"{', '.join(silent)} - they raised or exceeded [observe] max_ms, and a "
        "failing observer is skipped silently by design. Re-run with FUX_DEBUG=1 "
        "to see which",
        level="warn",
    )


def _suspended_pins(root: Path) -> Check:
    """W-162. A `fux correct --pin` whose document has moved under it.

    **A suspended pin is silent at query time, deliberately** — the query
    simply ranks normally — so without this row a person who pinned a question
    months ago has no way to learn that their pin stopped applying. That is the
    exact shape of failure `fux doctor` exists for: something that *was* true,
    is not, and says nothing.

    ⚠ **`warn`, never `error`.** A stale pin answers correctly — it answers
    with the ranking — so the repository is not broken. And the remedy needs a
    human to read the document and decide, which `doctor` must not do for them.
    """
    name = "correction pins"
    try:
        from .correct import load_corrections, suspended_pins
    except Exception:  # pragma: no cover - a check must not take out the command
        return Check(name, True, "not available in this build")
    try:
        rows = load_corrections(root)
    except Exception:
        return Check(name, True, "no readable corrections file")
    pins = [c for c in rows if c.pin]
    if not rows:
        return Check(name, True, "no corrections filed")
    if not pins:
        return Check(name, True, f"{len(rows)} correction(s), no pins")
    try:
        stale = suspended_pins(root)
    except Exception:
        return Check(name, True, f"{len(pins)} pin(s); could not read the index to check them")
    if not stale:
        return Check(name, True, f"{len(pins)} pin(s), all applying")
    shown = "; ".join(f"{c.loc} ({why})" for c, why in stale[:3])
    more = f" (+{len(stale) - 3} more)" if len(stale) > 3 else ""
    # 🔴 **`ok=False` with `level="warn"` is what renders `[WARN]`.** `cmd_doctor`
    # reads `ok` for the mark and `level` for the exit code, so `ok=True,
    # level="warn"` prints `[OK]` — which is right for an informational row
    # (*idle, nothing pending*) and wrong for a finding. The first cut of this
    # row had it that way and disclosed a suspended pin as `[OK]`.
    return Check(
        name,
        False,
        f"{len(stale)} of {len(pins)} pin(s) SUSPENDED and silently not applying: {shown}{more}"
        " - read the document, then `fux correct --reaffirm \"<question>\" <doc>`,"
        " or `--no-pin` to keep the correction without the pin",
        level="warn",
    )


def _acquired_health(root: Path) -> Check:
    """`.fux/acquired/` — how much is retained, and whether it is gitignored.

    ⚠ **Two questions, and the second is the one that matters.** The size is
    housekeeping; whether the plane is ignored by git is a data-exposure
    question, because this directory holds SOURCE BYTES. `_layout` already
    refuses an undeclared child of `.fux/`, and `_ignore_health` checks the
    index is *not* ignored — neither of them asks whether a plane that must be
    ignored actually is. This does.

    **A `warn`, never an `error`, on size.** SR-ACQUIRED decision 8 bounds the
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
        detail += f" - {orphans} unreferenced, swept on the next `fux ingest`"
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
    run `fux ingest` has nothing here and is told that rather than shown a zero
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
            "next `fux ingest`"
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




def provenance_counts(root: Path) -> dict:
    """`{rows, stale_decoders}` for `doctor --json`, or `{}` when no ledger exists.

    ⚠ **`{}` means UNKNOWN, not clean**, and that distinction is the whole
    reason this is a block rather than two keys that default to zero. A repo
    that has not ingested since W-200 landed has no ledger, and a caller told
    `stale_decoders: 0` there would be told something nothing checked.

    **Never raises.** A caller reading `doctor --json` in CI must not have its
    pipeline broken by an advisory, derived file.
    """
    from .ingest import decoderdigest, ingestlog

    try:
        if not ingestlog.path_for(root).is_file():
            return {}
        return {
            "rows": len(ingestlog.read(root)),
            "stale_decoders": ingestlog.stale_decoder_count(
                root, decoderdigest.binding_digests(root)
            ),
        }
    except (OSError, FuxError):
        return {}


def _provenance(root: Path) -> Check:
    """Do the records in the index still match the decoders that made them? (W-200)

    Reads `.fux/runtime/provenance.jsonl` — one row per document the last
    ingest consumed, naming the decoder digest that produced it — and compares
    each row against the digest that decoder carries **now**.

    🔴 **This is the case a plain `fux ingest` does NOT fix, which is the whole
    reason for the row.** The reuse key catches a decoder whose digest *moved*
    since the last run ([W-166](../../archive/open/W-166-decoder-digest.md)) and
    re-extracts its documents. It cannot catch a record written **before the
    binding existed**, or one carried through a run where the digest map could
    not be read: those records agree with nothing and no delta run will look at
    them again. `fux ingest --full` is the fix, and the row says so.

    ⚠ **Absent is not a finding.** A repo that has not ingested since this
    landed has no ledger, and reporting that as a problem would put a warning
    in front of every consumer on upgrade for a file that is advisory, derived
    and one `fux ingest` from existing. **`warn`, never `error`**, for the same
    reason: nothing about the index is wrong, only possibly stale.

    Read-only and offline. It opens two runtime files and imports no decoder.
    """
    from .ingest import decoderdigest, ingestlog

    if not ingestlog.path_for(root).is_file():
        return Check(
            "provenance",
            True,
            "no ledger yet - `.fux/runtime/provenance.jsonl` is written by the next "
            "`fux ingest`. Advisory and derived; nothing reads it at query time",
            level="warn",
        )
    try:
        current = decoderdigest.binding_digests(root)
    except FuxError as exc:
        return Check("provenance", False, f"decoder bindings do not resolve: {exc}")

    stale = ingestlog.stale_decoder_count(root, current)
    if stale:
        return Check(
            "provenance",
            False,
            f"{stale} record(s) were produced by a decoder whose digest differs from "
            "the tree's - run `fux ingest --full` to re-extract them. A plain "
            "`fux ingest` will NOT: the reuse key only catches a decoder that moved "
            "since the last run",
            level="warn",
        )
    rows = len(ingestlog.read(root))
    return Check(
        "provenance",
        True,
        f"{rows} record(s) match the decoders that produced them",
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
    from .decode import meta_bindings, registry
    from .ingest.parse import DEFAULT_META_FIELDS, meta_fields

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


def _decoder_bindings(root: Path) -> Check:
    """`[decoders]` in `.fux/formats.toml` — does every binding still resolve?

    **W-101 item 2.** `registry()` refuses a binding that names a module which
    does not exist, and one that takes an extension away from the decoder that
    claims it — but it refuses them **on the next `fux ingest`**. A consumer
    who deletes `.fux/decoders/confluence.py` and commits learns about the
    line still naming it when the next person's ingest dies.

    ⚠ **The third fault is one only `doctor` can catch**, and it is why this is
    not simply "call `registry()` early". A binding on an extension **no
    document in the corpus has** — a typo'd `jsno = "json"` — resolves perfectly:
    extending is legal by design (SR-DECODE, `_bind`), so nothing errors, and
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

    ⚠ **The knob this used to be about is GONE, and the check is not.**
    `recency_half_life_days` was removed on 2026-09-13 (W-152), so a missing
    `mtime` no longer switches a configured prior off. What it still costs is
    real and now MORE visible, not less:

    - **`mtime` reaches the caller**, on every `ask` hit (W-153) — so a corpus
      with none hands every consumer a null date and no way to sort by age.
    - **`mtime` is the second key of the declared tie-break** in
      `query/rank.py`, which is now one of only two routes by which a document
      fact reaches ranking at all. With no `mtime` anywhere, that key is inert
      and ties fall through to `priority` and then `id`.

    A **warning**, never an error: a corpus with no git history is a legitimate
    corpus, and this is a fact about the input rather than a broken install.
    """
    records = _records(root)
    if not records:
        return Check("recency prior", True, "no readable index", level="warn")
    with_mtime = sum(1 for record in records.values() if record.get("mtime"))
    total = len(records)
    if with_mtime == total:
        return Check(
            "recency prior", True, f"every one of {total} document(s) carries an mtime"
        )
    if with_mtime == 0:
        return Check(
            "recency prior",
            False,
            "NO document carries an mtime, so no date reaches a caller and the "
            "tie-break's date key is inert for the whole corpus. mtime is derived "
            "from git commit times, so a corpus copied out of its repository - or "
            "one that was never in git - has none",
            level="warn",
        )
    return Check(
        "recency prior",
        True,
        f"{with_mtime} of {total} document(s) carry an mtime; the other "
        f"{total - with_mtime} are outside git history and reach a caller with no date",
        level="warn",
    )


def freshness_counts(root: Path) -> dict[str, int]:
    """Verified-citation verdicts, by label, from the local receipt journal.

    **This is the veto check for two accepted records** —
    [SR-ACQUIRED](../../records/0145_acquired-plane.md) and
    [SR-URL-FRESHNESS](../../records/0147_url-freshness.md) both say
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
#: condition written into SR-ACQUIRED and SR-URL-FRESHNESS, quoted here so
#: the number has one home.
AS_INGESTED_VETO_SHARE = 0.25


def _freshness_share(root: Path) -> Check:
    """The `as-ingested` share — SR-ACQUIRED and SR-URL-FRESHNESS's veto.

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
            "Until then the as-ingested share (SR-ACQUIRED and SR-URL-FRESHNESS's veto "
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
            "reopen condition in SR-ACQUIRED and SR-URL-FRESHNESS. That reads as a broken "
            "fetch path being masked by the retained bytes, not a rare unreachable source",
            level="warn",
        )
    return Check("freshness verdicts", True, f"{detail} - as-ingested {share:.0%}", level="warn")


def _output_config_health(root: Path) -> Check:
    """`.fux/output.toml` absent — the repo that predates the file.

    SR-OUTPUT decision 19 made a missing file a hard `FuxError` at load time.
    The file is write-if-missing (SR-DOTFUX decision 6), so it reaches **new
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


def _tune_config_health(root: Path) -> Check:
    """Will `.fux/tune.toml` load — the file whose breakage doctor could not see.

    ⚠ **A broken tune file left `doctor` green** until 2026-09-11 (W-140 row
    13), and that is the worst shape for this particular file: `fux ingest`
    reads only `[index]` through `index_limits`, so a bad ranking knob **does
    not stop an ingest by design** ([SR-TUNE](../../records/0135_tuning.md)
    decision 13) — while `ask`, `find` and `answer` refuse. So the repo indexes
    cleanly, doctor says every row is fine, and every query fails.

    **A hard error, not a warning**, unlike `output.toml` being absent. An
    absent tune file is a repo running engine defaults, which is legitimate and
    common; a tune file that does not load is a file somebody wrote and nothing
    reads, and every query in the repo is already failing.

    The check calls `tune.load` itself rather than re-parsing: a second parser
    would answer a question the real one does not ask.
    """
    from . import tune as tune_mod

    path = root / tune_mod.TUNE_NAME
    if not path.is_file():
        return Check("tune.toml loads", True, f"{tune_mod.TUNE_NAME} is absent - engine defaults")
    try:
        tune_mod.load(root)
    except FuxError as exc:
        return Check(
            "tune.toml loads",
            False,
            f"{exc} - `ask`, `find` and `answer` refuse while this stands; "
            "`fux tune > .fux/tune.toml` rewrites the defaults, and `--no-tune` "
            "skips the file for one command",
        )
    return Check("tune.toml loads", True, f"{tune_mod.TUNE_NAME}: parsed, every key valid")


def _types_health(root: Path) -> Check:
    """Will the committed types list load — the shape that stops ingest.

    Three ways it cannot, each of which `read_types` refuses:

    1. **A leftover `.fux/sources/types`.** The list moved to `.fux/formats.toml`
       on 2026-09-11 (SR-TYPES decision 12), and a repo that ran `fux setup`
       before then still has the old file. SR-DOTFUX decision 6: when a change
       must reach existing repos the mechanism is *a loader refusal or a
       `doctor` check, never a rewrite* — this row is the check, and it names
       the command that converts.
    2. **A file that does not parse or breaks the closed key set.**
    3. **A file that admits nothing.** A present file replaces the built-in
       default entirely (SR-TYPES decision 2), so an empty one would silently
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
    [SR-FETCHER](../../records/0117_fetcher.md) decision 12 learned **0 of 7**
    `validate()` tokens until its `http.py` was replaced by hand. `fux setup` is
    write-if-missing and never rewrites a consumer's fetcher — the freeze
    SR-DOTFUX decision 6 names — so a new optional function reaches new repos
    only, silently, and the optimisation that never runs is indistinguishable
    from one that ran and found nothing.

    ⚠ **A NOTICE, never a rewrite.** SR-DOTFUX decision 6 names the mechanism
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
    # ⚠ **`[sources.url] fetcher` is deleted** (W-199 D2), so there is no one
    # fetcher to read any more. This row reports the optional functions of the
    # fetchers actually on disk, and names the shipped plain-GET one when it is
    # there, because that is the file a consumer is most likely asking about.
    rel = f"{FETCHERS_DIR}/http.py"
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
        ("validate", "SR-FETCHER decision 12", "re-fetches every URL body even when unchanged"),
        ("is_rate_limited", "SR-FETCHER decision 13", "cannot tell a 429 from a hard failure"),
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
    from .ingest.run import STALE_REDACTION_FILE
    from .store import fuxdir

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


def _dirs_exclusions_migrated(root: Path) -> Check:
    """`!` lines still in `.fux/sources/dirs`, and the one-line move for each.

    **`fux remove` stopped writing them on 2026-09-14** (W-165 fix 1): the
    exclusion goes to `.fux/.fuxignore`, which SR-FUXIGNORE made the one place a
    path is kept out of the index. The `!` lines already written keep being read
    — SR-DIR-LIST decision 2a, and breaking them would be a silent re-inclusion,
    which is the worse direction — so this is a `warn` and never an error.

    ⚠ **Not the same finding as `_ignore_health`'s duplicate.** That one fires
    when a pattern is in *both* files and is about the two spellings drifting
    apart. This fires on *every* survivor, duplicated or not, because the
    migration is owed for the ones nothing duplicates too — and those are the
    ones no other check would ever mention.

    **ASCII only** - it is printed, and printed text reaches a Windows console.
    """
    from .ingest import fuxignore

    try:
        notes = fuxignore.dirs_exclusion_notes(root, dirs_file=DEFAULT_DIRS_FILE)
    except (FuxError, OSError) as exc:
        return Check("dirs exclusions migrated", False, f"{DEFAULT_DIRS_FILE}: {exc}", level="warn")
    if not notes:
        return Check(
            "dirs exclusions migrated",
            True,
            f"no `!` lines in {DEFAULT_DIRS_FILE} - exclusions live in {fuxignore.IGNORE_FILE}",
        )
    return Check(
        "dirs exclusions migrated",
        False,
        f"{len(notes)} `!` line(s) left in {DEFAULT_DIRS_FILE}. " + " ".join(notes),
        level="warn",
    )


# -- W-163: the setup-drift rows -------------------------------------------
#
# 🔴 **One cause, eight rows.** `fux setup` writes once and NEVER rewrites
# ([SR-DOTFUX](../../records/0102_fux-directory.md) decision 6), so everything
# that ships in a template **freezes in every repo that ran setup before the
# template changed**, and nothing tells the repo. Five records each named
# `fux doctor` as the place that should say so and none was built; three more
# name checks doctor can run today over declarations it already reads.
#
# ⚠ **Report-only, every one of them.** Decision 1 of SR-DOCTOR: doctor names,
# it never rewrites. A row that grew a `--fix` would be taking decision 6's fork
# without anybody ruling it.
#
# ⚠ **`warn`, every one of them.** None of these stops a verb. A frozen tunable
# is a repo running an older default, a missing directory is a line somebody
# has yet to create — these are drift, not breakage, and an error here would
# make `doctor` red on working repos, which is how people learn to ignore it.


#: Skill directories a vendor stopped reading. `(path, why, what to do)`.
#:
#: SR-AGENT-POLICY decision 16 (2026-09-12): Codex and Copilot both read
#: `.agents/skills/`, so the two vendor-specific copies were retired. A repo set
#: up before that still has them, and **Copilot then sees two copies of every
#: skill** — the duplicate is the defect, not the folder.
_RETIRED_AGENT_DIRS = (
    (".codex/skills", "Codex reads `.agents/skills/` now"),
    (".github/skills", "Copilot reads `.agents/skills/` now, and sees DUPLICATES while this exists"),
)


def _retired_agent_folders(root: Path) -> Check:
    """Skill folders a vendor stopped reading, left behind by an older `setup`.

    **The duplicate is the defect.** `.github/skills/` is not merely unread —
    Copilot reads `.agents/skills/` *and* it, so every skill appears twice, with
    the older copy free to disagree with the newer one while both look correct.

    **Delete is the whole remedy**, which is why this is a row and not a rewrite:
    the folder may hold a consumer's own files, and `fux setup` removing a
    directory it did not write is not a thing it has ever been allowed to do.
    """
    present = [(rel, why) for rel, why in _RETIRED_AGENT_DIRS if (root / rel).is_dir()]
    if not present:
        return Check("retired agent folders", True, "none - skills live in `.agents/skills/`")
    return Check(
        "retired agent folders",
        False,
        "; ".join(
            f"`{rel}` still exists ({why}); delete it - `fux setup` will not, "
            "because it may hold files fux did not write"
            for rel, why in present
        ),
        level="warn",
    )


def _readme_current(root: Path) -> Check:
    """`.fux/README.md`'s section set against the template's.

    **Sections, not bytes.** The file is a consumer's to annotate — SR-DOTFUX
    decision 6 is write-if-missing precisely so their edits survive — so a byte
    comparison would fire on every repo where someone added a note, which is a
    row that is wrong more often than it is right. A **missing section** is the
    thing that means "this predates a change to what `.fux/` holds".

    ⚠ **Extra sections are NOT reported.** A consumer heading fux never wrote is
    the feature, not drift.
    """
    from .store import fuxdir

    path = root / ".fux" / "README.md"
    if not path.is_file():
        return Check("README.md current", True, "absent - nothing to be stale")
    builder = getattr(fuxdir, "_readme", None)
    if builder is None:  # pragma: no cover - the template is not optional today
        return Check("README.md current", True, "no template to compare against")
    try:
        template = builder()
    except Exception:  # pragma: no cover - a template that will not build is its own bug
        return Check("README.md current", True, "the template did not build")
    missing = sorted(_headings(template) - _headings(path.read_text(encoding="utf-8", errors="replace")))
    if not missing:
        return Check("README.md current", True, "every section the template carries is present")
    return Check(
        "README.md current",
        False,
        f"{len(missing)} section(s) the current template carries are absent: "
        + ", ".join(f"`{m}`" for m in missing[:4])
        + (f" and {len(missing) - 4} more" if len(missing) > 4 else "")
        + ". `fux setup` writes this file once and never rewrites it, so it froze when "
        "this repo was set up; copy the missing sections in, or delete the file and "
        "re-run `fux setup` to get the current one",
        level="warn",
    )


def _headings(text: str) -> set[str]:
    """Markdown ATX headings, normalised. Shared by the README row and its test."""
    return {
        line.lstrip("#").strip()
        for line in text.splitlines()
        if line.startswith("#") and line.lstrip("#").strip()
    }


#: sha256 of every refusal starter fux has SHIPPED AND REPLACED.
#:
#: 🔴 **Append the outgoing digest here in the same change that edits
#: `templates/refusals.toml.txt`.** That is the whole mechanism, and without it
#: this row cannot fire: fux ships exactly one starter, so *"byte-equal to a
#: PREVIOUS starter"* — the condition SR-REFUSAL names — is unanswerable from
#: the tree alone. A repo whose file matches the current starter is **new**, not
#: frozen, and reporting the two alike would make the row wrong on every fresh
#: `fux setup`.
#:
#: ⚠ **Empty today, and that is correct rather than unfinished.** The starter
#: has not been replaced since it shipped, so there is no superseded digest to
#: hold. `tests/test_doctor.py::test_the_current_refusal_starter_is_not_listed_as_retired`
#: fails if the current one is ever added here by mistake, which would report
#: every repo in the world as frozen.
RETIRED_REFUSAL_STARTERS: tuple[str, ...] = ()


def _starter_refusals_untouched(root: Path) -> Check:
    """`.fux/refusals.toml` byte-equal to a starter fux has since replaced.

    **Byte equality is the right test here, and the opposite call from the
    README row above.** These are rules that decide what enters the index,
    shipped as a starting point for a consumer to adapt to their own sign-in
    pages. A file identical to a *retired* starter is one nobody ever looked at,
    still refusing by rules fux itself stopped shipping.

    ⚠ **Matching the CURRENT starter is not a finding.** A repo set up yesterday
    is supposed to look exactly like that. The row fires only on a digest in
    `RETIRED_REFUSAL_STARTERS`, which is the only shape that means *frozen* as
    opposed to *new* — and which is why that tuple has to be appended to by
    hand when the starter changes.
    """
    import hashlib

    path = root / ".fux" / "refusals.toml"
    if not path.is_file():
        return Check("refusal rules current", True, "`.fux/refusals.toml` absent")
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        return Check("refusal rules current", True, f"`.fux/refusals.toml`: {exc}")
    if digest not in RETIRED_REFUSAL_STARTERS:
        return Check(
            "refusal rules current",
            True,
            "`.fux/refusals.toml` is not a starter fux has retired",
        )
    return Check(
        "refusal rules current",
        False,
        "`.fux/refusals.toml` is byte-identical to a starter fux has since REPLACED - "
        "it has never been edited, and the rules it carries are ones fux stopped "
        "shipping. Compare it against `fux setup`'s current starter and take what "
        "applies to your sign-in pages; `fux setup` will not rewrite it",
        level="warn",
    )


def _frozen_keys(root: Path) -> list[Check]:
    """`.fux/tune.toml` and `.fux/output.toml` against the keys the engine now has.

    **A key the engine gained is a key the consumer's file does not mention**,
    and because both files are write-if-missing it will never gain it. Reading
    resolves to the engine default, so nothing is broken — what is lost is that
    the consumer cannot SEE the knob exists, in the one file whose whole purpose
    is to show them.

    ⚠ **Absent is not frozen.** A repo with no `tune.toml` is running engine
    defaults deliberately and `_tune_config_health` already says so. This row is
    about a file that exists and is incomplete.
    """
    return [
        _frozen_one(
            root,
            ".fux/tune.toml",
            "tune.toml current",
            _tune_expected_keys(),
            "`fux tune > .fux/tune.toml` rewrites it with every current key "
            "(NOTE: it rewrites VALUES too - diff before you keep it)",
        ),
        _frozen_one(
            root,
            ".fux/output.toml",
            "output.toml current",
            _output_expected_keys(),
            "`fux output > .fux/output.toml` rewrites it with every current key "
            "(NOTE: it rewrites VALUES too - diff before you keep it)",
            by_name=True,
        ),
    ]


def _frozen_one(
    root: Path, rel: str, name: str, expected: set[str], remedy: str, *, by_name: bool = False
) -> Check:
    """One file's key set against the engine's. `by_name` compares LEAF NAMES.

    🔴 **`by_name` exists because the path comparison was a false positive on
    fux's own repository**, caught by W-163's own keep-call before the row
    shipped. `.fux/output.toml` is deliberately NESTED PER VERB — `explain`
    lives under `[cli.ask]`, `hops` under `[cli.path]`, `no_refer` and `journal`
    under `[cli.answer]`, `enabled` under `[cli.json]` — because a rendering
    default means different things to different verbs (SR-OUTPUT). Expecting
    `cli.explain` reported six keys missing from a file that carries all of
    them, in the right places.

    **So the question this row asks is "does the file MENTION this knob", not
    "at this exact path".** Looser, deliberately: the cost is that a key moved
    between tables would not be flagged, and the benefit is that the row is not
    wrong on every correctly-written file.

    `.fux/tune.toml` keeps the path comparison. Its schema *is* `table.key` with
    no nesting choice to make, so the exact path is answerable there and a
    tighter check is free.
    """
    path = root / rel
    if not path.is_file():
        return Check(name, True, f"{rel} absent - engine defaults, nothing to freeze")
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        # Its own row already reports an unparseable file; saying so twice with
        # two different wordings is how a reader learns to trust neither.
        return Check(name, True, f"{rel}: not parsed here - see the `loads` row")
    present = _leaf_keys(data)
    if by_name:
        # ⚠ **Every segment, not just the last.** `json` is a knob whose value
        # lives at `[cli.json] enabled` — the TABLE carries the name and the leaf
        # is `enabled`. Comparing final segments alone reported `json` missing
        # from a file that configures it, which is the same false positive as
        # the path comparison wearing a different hat. Caught by running the row
        # on this repository, which is what W-163's keep-call is for.
        present = {segment for path in present for segment in path.split(".")}
    missing = sorted(expected - present)
    if not missing:
        return Check(name, True, f"{rel}: every key the engine now carries is present")
    return Check(
        name,
        False,
        f"{rel} is missing {len(missing)} key(s) the engine now has: "
        + ", ".join(f"`{m}`" for m in missing[:5])
        + (f" and {len(missing) - 5} more" if len(missing) > 5 else "")
        + f". They resolve to the engine default, so nothing is broken - but this file "
        f"is where you would change them and it does not mention them. {remedy}",
        level="warn",
    )


def _leaf_keys(data: dict, prefix: str = "") -> set[str]:
    """`{"cli": {"top": 5}}` -> `{"cli.top"}`. Tables are paths, leaves are keys."""
    out: set[str] = set()
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out |= _leaf_keys(value, f"{path}.")
        else:
            out.add(path)
    return out


def _tune_expected_keys() -> set[str]:
    """Every `table.key` the current tune schema carries — **derived, not listed**.

    A hand-written list here would be a second statement of the schema, free to
    disagree with it while both look correct. That is the restatement L0 forbids,
    and the failure mode is silent: the row stops reporting a key nobody added.
    """
    from . import tune as tune_mod

    return {
        f"{table}.{key}"
        for table, keys in tune_mod._SCHEMA.items()
        for key in keys
    }


def _output_expected_keys() -> set[str]:
    """Every knob name the output schema carries — **names, not paths**.

    See `_frozen_one`'s `by_name`: this file nests per verb on purpose, so a
    path is the wrong unit of comparison and asking for one reported fux's own
    correctly-written `output.toml` as missing six keys.

    **Derived from `BUILT_IN`, never listed here.** A second copy of the key set
    is free to disagree with the schema while both look correct, and the failure
    is silent — the row simply stops reporting a knob nobody remembered to add.
    """
    return set(output_config.BUILT_IN) | set(output_config.MCP_KEYS)


def _unbound_types(root: Path) -> Check:
    """A declared type that resolves to no decoder at all.

    ⚠ **Not the same finding as SR-DECODE's `decoder bindings` row**, which
    fires on a `[decoders]` binding whose extension no indexed document has.
    This one fires on a **declared include glob** that reaches a format nothing
    can read: the documents match, get walked, and are skipped or indexed as raw
    bytes — with the type list saying, in a committed file, that they are
    documents.

    **Markdown and plain text are exempt and always will be.** They are read by
    `extract.py`, not by a decoder, so *having no decoder* is their normal state
    rather than a fault.
    """
    from . import decode as decode_mod
    from .ingest import typesfile

    try:
        listed = typesfile.read(root, DEFAULT_TYPES_FILE)
    except (FuxError, OSError):
        return Check("declared types are readable", True, "types list not parsed here - see its own row")
    if listed is None or not listed.allow:
        return Check("declared types are readable", True, "no declared types to check")

    try:
        known = set(decode_mod.registry(root)) | _PROSE_SUFFIXES
    except (FuxError, OSError):
        # A binding naming a module that does not exist, or a consumer decoder
        # that will not import. **`decoder bindings` is the row for that** — it
        # names the module and the fix. Reporting it here as well, in different
        # words, is how a reader learns to trust neither row.
        return Check(
            "declared types are readable",
            True,
            "the decoder registry did not build - see the `decoder bindings` row",
        )
    unbound = sorted(
        {
            suffix
            for glob in listed.include
            if (suffix := _glob_suffix(glob)) and suffix not in known
        }
    )
    if not unbound:
        return Check(
            "declared types are readable",
            True,
            f"every declared type resolves to a decoder or is prose ({len(listed.include)} glob(s))",
        )
    return Check(
        "declared types are readable",
        False,
        f"{len(unbound)} declared type(s) resolve to no decoder and are not prose: "
        + ", ".join(f"`{s}`" for s in unbound[:6])
        + (f" and {len(unbound) - 6} more" if len(unbound) > 6 else "")
        + ". Matching documents are walked and then indexed as raw bytes or skipped, "
        "while `.fux/formats.toml` says they are documents. Write a decoder in "
        "`.fux/decoders/`, or drop the glob",
        level="warn",
    )


#: Read by `extract.py` rather than by a decoder, so having none is correct.
_PROSE_SUFFIXES = frozenset({".md", ".markdown", ".txt", ".rst", ".adoc", ".org"})


def _glob_suffix(glob: str) -> str:
    """`*.pdf` -> `.pdf`. `""` for a glob that names no single extension.

    A glob like `docs/**` or `*` claims no extension, so there is nothing to
    resolve and nothing to report — reporting one would be inventing a claim the
    consumer did not make.
    """
    name = glob.rsplit("/", 1)[-1]
    if not name.startswith("*.") or "*" in name[2:] or "?" in name or "[" in name:
        return ""
    return name[1:].lower()


def _listed_dirs_exist(root: Path) -> Check:
    """A line in `.fux/sources/dirs` naming a path that is not on disk.

    🔴 **This is not cosmetic: `walk_sources` RAISES on it**, so the next
    `fux ingest` in this repo exits 1 — which is why `fux add` refuses a path
    that does not exist. A line that got there another way (a hand edit, a
    branch switch, a directory someone moved) has nothing checking it until the
    ingest fails.

    **Still a `warn`.** Doctor reports; the ingest is where it stops, and it
    already says so clearly. Making this an error would mean `doctor` and
    `ingest` both refuse on a branch where a documented directory is simply not
    checked out, which is a legitimate state to be in for an afternoon.

    ⚠ **Exclusions are not checked.** A `!` line names a pattern, not a path,
    and a pattern matching nothing today is exactly what a pattern is for.
    """
    from .ingest import sourcelist

    path = root / DEFAULT_DIRS_FILE
    if not path.is_file():
        return Check("listed directories exist", True, f"{DEFAULT_DIRS_FILE} absent")
    try:
        entries = sourcelist.parse(
            path.read_text(encoding="utf-8"), sourcelist.DIRS, origin=str(path)
        )
    except (FuxError, OSError) as exc:
        return Check("listed directories exist", False, f"{DEFAULT_DIRS_FILE}: {exc}", level="warn")

    gone = [e.value for e in entries if not e.exclude and not (root / e.value).exists()]
    if not gone:
        return Check(
            "listed directories exist",
            True,
            f"every listed path is on disk ({len(entries)} entr(y/ies))",
        )
    return Check(
        "listed directories exist",
        False,
        f"{len(gone)} listed path(s) are not on disk: "
        + ", ".join(f"`{g}`" for g in gone[:5])
        + (f" and {len(gone) - 5} more" if len(gone) > 5 else "")
        + f". `fux ingest` RAISES on this, so the next one will exit 1 - "
        f"`fux remove <path>` drops the line, or restore the directory",
        level="warn",
    )


#: A `url:` record whose extracted text is below this share of its retained
#: bytes is *suspiciously thin* — almost certainly a page whose real content
#: arrived by JavaScript the `http` fetcher does not run.
#:
#: ⚠ **Advisory, and a SHARE rather than a byte count.** A genuinely short page
#: is fine; a 400 KB HTML document that extracted 300 characters is a sign-in
#: wall or an app shell. The floor is deliberately generous: this row exists to
#: surface the obvious case, never to adjudicate extraction quality, and a
#: tighter number would need evidence nobody has gathered.
THIN_URL_SHARE = 0.01
#: Below this many characters, the share is meaningless and the absolute number
#: is the signal.
THIN_URL_CHARS = 200


def _thin_urls(root: Path) -> Check:
    """`url:` documents that extracted almost nothing from a large fetch.

    **The shape it catches:** the `http` fetcher runs no JavaScript, so a
    single-page app returns a full-size HTML shell and decodes to a nav bar.
    The document indexes, the run reports success, and the page is in the corpus
    answering nothing — [SR-HTTP-FETCHER](../../records/0119_http-fetcher.md)
    named `doctor` as where that should be visible.

    **Read from the committed index and `.fux/acquired/`**, both already on
    disk. No fetch, no network, no second opinion about the page.

    ⚠ **Advisory and deliberately loose.** It reports; `cdp.py` is the remedy
    for a page that needs a browser, and whether a given page needs one is the
    consumer's call about their own wiki.
    """
    from .store import acquired

    try:
        manifest = acquired.read_manifest(root)
    except (FuxError, OSError):
        return Check("url extraction depth", True, "no acquired plane to compare against")
    if not manifest:
        return Check("url extraction depth", True, "no retained url bytes to compare against")

    thin: list[str] = []
    for doc_id, record in _records(root).items():
        if not doc_id.startswith("url:"):
            continue
        blob = manifest.get(record.get("loc", ""))
        if blob is None:
            continue
        raw = getattr(blob, "bytes", None) or getattr(blob, "size", 0)
        extracted = sum(record.get("flen", ())) if record.get("flen") else 0
        if not raw or extracted >= THIN_URL_CHARS:
            continue
        if extracted / raw < THIN_URL_SHARE:
            thin.append(record.get("loc", doc_id))

    if not thin:
        return Check("url extraction depth", True, "no url document extracted suspiciously little")
    return Check(
        "url extraction depth",
        False,
        f"{len(thin)} url document(s) extracted almost nothing from a full-size fetch: "
        + ", ".join(sorted(thin)[:3])
        + (f" and {len(thin) - 3} more" if len(thin) > 3 else "")
        + ". The `http` fetcher runs no JavaScript, so an app shell decodes to its nav bar. "
        "`fux add <url> --cdp` fetches through a signed-in Chrome instead",
        level="warn",
    )


def _confidence_floors(root: Path) -> Check:
    """A confidence floor tuned to zero — the knob that turns a band OFF silently.

    🔴 **SR-CONFIDENCE decision 13's own words, about itself:** *"A consumer can
    set `separation_floor = 0.0` and no answer is ever `weak` again. That is
    tuning away the SIGNAL rather than the ranking, it is silent, and **nothing
    mechanical catches it.**"* This is the mechanical catch (W-164 gate 4).

    **It reports; it never refuses.** Decision 13 reversed a prohibition on
    exactly the reasoning that fux states costs rather than clamping knobs, and a
    row that refused the value would be decision 7 coming back in a new costume.
    Zero is a legal value; what it is not is a value a reader of the band should
    have to discover.

    ⚠ **`doc_coverage_floor = 0.0` is the ENGINE DEFAULT and is not reported.**
    That clause ships off — decision 13's own comment says `0.0 = the clause is
    OFF` — so firing on it would fire on every repo in the world. Only
    `separation_floor` has a non-zero default to be tuned away from, and only a
    `doc_coverage_floor` that was raised and then returned to zero would be
    interesting, which is not something the file can tell us.
    """
    from . import tune as tune_mod

    path = root / tune_mod.TUNE_NAME
    if not path.is_file():
        return Check("confidence floors", True, "engine defaults - no floor is tuned off")
    try:
        resolved = tune_mod.load(root)
    except (FuxError, OSError):
        return Check("confidence floors", True, "tune.toml not parsed here - see its own row")
    if getattr(resolved, "separation_floor", None) != 0.0:
        return Check(
            "confidence floors",
            True,
            f"separation_floor = {getattr(resolved, 'separation_floor', '?')} - "
            "`weak` can still be reached",
        )
    return Check("confidence floors", False, FLOOR_OFF_NOTE, level="warn")


#: The one sentence both surfaces print. **One string, two callers** — `doctor`'s
#: row and `ask`'s first-of-process note would otherwise drift into two accounts
#: of one fact. **ASCII only**: it is printed, and printed text reaches a Windows
#: console.
FLOOR_OFF_NOTE = (
    "`[confidence] separation_floor = 0.0` in .fux/tune.toml: NO answer in this repo "
    "can ever be `weak` again. That tunes away the SIGNAL, not the ranking - a "
    "`grounded` here does not mean what a `grounded` elsewhere means. The band "
    "publishes the floor it was judged under (`--band`, or the `confidence` block in "
    "`--json`), which is the only way a reader can tell. Raise it, or keep it and "
    "know what the band is worth"
)


def _url_health(root: Path) -> Check:
    """The `url:` half of the corpus, reported (W-82 §3.1).

    Doctor had **no URL check at all**, which is the defect: a URL that has
    failed every fetch for a month looked exactly like one fetched a minute ago.
    [SR-URL-INGEST](../../records/0107_url-ingest.md) decision 4 keeps the
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
        # ⚠ This branch above all: "none indexed" with five URLs listed is a
        # repo whose whole corpus is waiting on a fetch nobody has run, and it
        # read as an empty, healthy configuration.
        bits.extend(_unfetched_note(root, indexed))
        if policy is not None:
            bits.append(policy)
        note = _rate_limit_note()
        if note is not None:
            bits.append(note)
        return Check("url sources", True, ", ".join(bits), level="warn")

    parts = [f"{summary.indexed} url: record(s)"]
    if summary.run_seq == 0:
        parts.append("no networked run recorded yet - run `fux ingest`")
    else:
        parts.append(f"{summary.confirmed_last_run} confirmed by the last run")
    if summary.never_confirmed:
        parts.append(f"{summary.never_confirmed} never re-fetched since first ingest")
    if summary.failing:
        parts.append(f"{summary.failing} failing")
    if policy is not None:
        parts.append(policy)
    parts.extend(_unfetched_note(root, indexed))
    parts.extend(_pinned_note(root))
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


def _unfetched_note(root: Path, indexed: list[str]) -> list[str]:
    """URLs listed in `.fux/sources/urls` that have never produced a record.

    🔴 **[SR-MAINTENANCE](../records/0129_hooks.md) decision 5a leaned on this
    and it did not exist** (W-140 row 13, built 2026-09-12). 5a refuses to let
    any git hook touch the network, and pays for that refusal with one sentence:
    *"URLs added by hand-editing `.fux/sources/urls` are not fetched at commit
    time… That is a delay, not a silence — `fux doctor` reports them."* **It did
    not report them.** Every other row of `url sources` is computed from `url:`
    records **in the index**, and a line that has never been fetched has no
    record — so the one case the law's cost depends on was the one case the
    check could not see. The silence 5a promised was not a silence was a
    silence.

    **Listed minus indexed**, read off the committed list. No network, like
    everything else here.
    """
    from .config import load as load_config
    from .ingest import urlsrc

    try:
        config = load_config(root)
        if config.url is None:
            return []
        listed = [e.value for e in urlsrc.read_urls(root, config.url.urls_file)]
    except Exception:
        # The list or the config is another row's finding — `fux.toml loads`
        # and `url sources` both name it. Never two reports for one cause.
        return []
    have = set(indexed)
    missing = sorted(url for url in listed if url not in have)
    if not missing:
        return []
    shown = ", ".join(missing[:3])
    more = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
    return [
        f"{len(missing)} listed URL(s) have never been fetched, so they are not in "
        f"the index at all: {shown}{more} - run `fux ingest` (no hook will do it: "
        f"SR-MAINTENANCE decision 5a)"
    ]


def _pinned_note(root: Path) -> list[str]:
    """`update=never` lines, counted — and the lossy pair named (W-113).

    A pinned URL is a URL `fux ingest` will never go out for again, which is a
    fact somebody looking at a stale corpus needs and could otherwise learn only
    by reading every line of `.fux/sources/urls`.

    ⚠ **`update=never` + `keep=false` is legal and lossy, so it is DISCLOSED
    and never refused.** With no retained bytes there is nothing for `fux
    answer` to verify a citation against and nothing to re-derive from: the
    document is frozen at whatever statistics its last ingest produced. That is
    a coherent thing to want for a document that genuinely never changes, and a
    surprising thing to have chosen by accident — which is exactly the shape
    that belongs in a warning rather than in a refusal.

    Reads the committed list, never the network, and resolves through the same
    three layers everything else does so a source-wide `update = "never"` is
    counted too.
    """
    from .config import load as load_config
    from .ingest import urlsrc

    try:
        config = load_config(root)
        if config.url is None:
            return []
        resolved = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
    except Exception:
        # The list or the config is another row's finding -- `fux.toml loads`
        # and `url sources` both name it. Never two reports for one cause.
        return []
    pinned = [e for e in resolved if e.update == "never"]
    if not pinned:
        return []
    parts = [f"{len(pinned)} pinned (update=never; never re-fetched)"]
    lossy = sorted(e.url for e in pinned if not e.keep)
    if lossy:
        shown = ", ".join(lossy[:3])
        more = f" (+{len(lossy) - 3} more)" if len(lossy) > 3 else ""
        parts.append(
            f"{len(lossy)} of them keep=false, so there are no retained bytes to verify "
            f"a citation against: {shown}{more}"
        )
    return parts


def _parallel_policy(root: Path) -> str | None:
    """How many URLs a networked verb may open at once — W-83.

    **The number a person needs before running `fux ingest` over a corporate
    wiki**, said by the one command whose job is to tell them what will happen.
    Without it the only way to learn the concurrency was to read `config.py`.

    ⚠ **This reports POLICY and refuses to compute the product**, and that is a
    constraint rather than laziness. The effective value is
    `min(configured, declared)`, and `declared` lives in a **consumer-owned
    Python file** — reading it means importing it, which runs whatever is at
    that file's module level. `fux doctor` is the command a person runs when
    something is already wrong; it may not be the command that executes their
    fetcher. So it names the rule and lets `fux ingest` apply it.
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


def _node_reader(root: Path) -> Check:
    """`.fux/node/` is present, matches the engine, and is in a state that RUNS.

    A **warning**, never an error: Python answers without it, so a missing or
    stale reader costs a Node-only clone, not this machine. But it is the one
    drift `doctor` can still see -- the vendored copy is overwritten on a
    version difference by `fux setup`/`fux ingest`, and a repo whose owner has
    not run either since upgrading ships a reader that may not understand the
    `_format` of the index sitting beside it.

    Three things beyond the version since 2026-09-12 (SR-NODE-SEARCH
    decisions 13-16):

    - **Which shape**, because the two fail differently. Shape A cannot be
      half-configured; shape C can.
    - **Whether shape C is actually installed.** A manifest declaring
      `fux-engine` with no `node_modules` anywhere above it is exactly
      decision 15's *"half-configured is not a state"*, and `doctor` is where
      the record says it gets said.
    - **Whether a stale module tree is still sitting there.** `.fux/node/src/`
      is fux's own source in a consumer's repository, which L10 forbids; it
      means `fux setup` has not run since the prune shipped.
    """
    from .store import fuxdir

    directory = fuxdir.fux_dir(root)
    found = fuxdir.node_version(directory)
    if found is None:
        return Check("node reader", True, "absent - `fux setup` writes it", level="warn")

    shape = fuxdir.node_shape(directory)
    where = f".fux/{fuxdir.NODE_DIR}/"
    if found != __version__:
        return Check(
            "node reader",
            False,
            f"{where} is {found}; the engine is {__version__} - run `fux setup`",
            level="warn",
        )
    if (directory / fuxdir.NODE_DIR / "src").is_dir():
        return Check(
            "node reader",
            False,
            f"{where} still holds fux's source tree (src/) beside the bundle - run "
            "`fux setup` to prune it (L10)",
            level="warn",
        )
    if shape == fuxdir.SHAPE_WORKSPACE and _installed_reader(root) is None:
        return Check(
            "node reader",
            False,
            f"{where} is a workspace member declaring fux-engine {found}, but no "
            "node_modules/.bin/fux resolves - run your package manager's install",
            level="warn",
        )
    kind = "a workspace member" if shape == fuxdir.SHAPE_WORKSPACE else "the vendored bundle"
    return Check("node reader", True, f"{where} is {found}, {kind}", level="warn")


def _installed_reader(root: Path) -> "Path | None":
    """The installed `fux` bin the shim's rungs 2 and 3 would find, or `None`.

    The rungs are the shim's, in the shim's order, because a check that looked
    somewhere else would pass on a repository the shim cannot run
    (SR-NODE-SEARCH decision 16).
    """
    from .store import fuxdir

    member = fuxdir.fux_dir(root) / fuxdir.NODE_DIR / "node_modules" / ".bin" / "fux"
    if member.exists():
        return member
    directory = fuxdir.fux_dir(root)
    for parent in [directory, *directory.parents]:
        candidate = parent / "node_modules" / ".bin" / "fux"
        if candidate.exists():
            return candidate
    return None


#: Extensions a launcher shim can have, across the platforms fux ships on.
#:
#: ⚠ **`.exe` is deliberately absent, and that is a correctness fix, not tidying**
#: (W-159). The classifier read whatever `shutil.which` returned as text with
#: `errors="replace"` and asked whether the word `node` appeared in the first
#: 512 bytes. A Windows console script IS a `.exe` — a small binary launcher —
#: and three letters occurring by chance in its bytes would have reported a
#: perfectly ordinary Python `fux` as the Node reader. A compiled binary is not
#: a shim and is never read.
_SHIM_SUFFIXES = frozenset({"", ".cmd", ".bat", ".ps1", ".mjs", ".js", ".sh"})


def _is_node_shim(path: Path) -> bool:
    """Does this launcher hand off to node? **Read, never run** (W-159).

    Doctor never executes a binary it found on PATH — that is an arbitrary
    executable chosen by the environment, and shelling out to ask what it is
    would be the diagnostic tool doing the unsafe thing it exists to warn about.

    **Two shapes, because npm writes two.** On Unix the bin is a symlink to a
    `#!/usr/bin/env node` script; on Windows it is a `fux.cmd` whose body names
    `node` — *there is no shebang there at all*, which is why "look for a
    shebang" was never the rule, only ever the Unix half of one.

    **Split out of `_fux_on_path` so it can be tested on every platform.** The
    end-to-end row needs `shutil.which` to resolve a shim, and `which` honours
    PATHEXT — so an extensionless `fux` is invisible on Windows and a `fux.cmd`
    is invisible to a Unix lookup of `fux`. Neither shape can be exercised
    end-to-end on both platforms, and the classification is the part that was
    actually wrong.
    """
    try:
        target = path.resolve()
    except OSError:
        return False
    suffix = target.suffix.lower()
    if suffix == ".mjs":
        return True
    if suffix not in _SHIM_SUFFIXES:
        return False  # a compiled launcher; not a shim, and not read as text
    try:
        head = target.read_text(encoding="utf-8", errors="replace")[:512]
    except OSError:
        return False
    return "node" in head


def _fux_on_path() -> Check:
    """Which `fux` does this shell resolve -- Python's, or the Node reader's?

    **SR-NODE-SEARCH R1a mitigation 3.** `npm i -g fux-engine` puts a `fux` on
    PATH beside Python's, **with a different verb set**, and whichever resolves
    first wins. So `fux ingest` can answer *"this only reads"* on a machine
    where Python fux is installed and would have worked.

    ⚠ **This row was deferred, and the reason it was deferred is gone.** R1a
    originally ruled *"No global bin ships in the first npm release"*, and the
    row was left unbuilt because nothing would shadow Python's `fux`.
    `fux-engine` 2.0.0-alpha.7 went to npm on 2026-09-12 **carrying the bin**,
    and Arpit ruled the bin stays -- so the shadowing is real and this is the
    only one of R1a's three mitigations that speaks to a person who has both
    installed and cannot tell which one they are typing. The other two
    (`--version` naming the runtime, an unsupported verb signposting) live in
    the Node half and cannot report on a Python that is not running.

    A **warning**, never an error, on the `_node_reader` precedent: having both
    installed is a legitimate setup, not a broken repo.

    **No subprocess.** Doctor never runs a binary it found on PATH -- that is
    an arbitrary executable chosen by the environment, and shelling out to it
    to ask what it is would be the diagnostic tool doing the unsafe thing it
    exists to warn about. `_is_node_shim` reads the launcher instead.

    ⚠ **Amended 2026-09-14 (W-159): this said "the shebang answers the
    question", and on Windows there is no shebang.** npm writes a `fux.cmd`
    whose body names `node`; `shutil.which` finds it, because PATHEXT is exactly
    what it resolves through. **So the row does fire on Windows for the real npm
    shape** — what could not be constructed there was the TEST's extensionless
    shim, and the item that filed this read the skipped test as evidence about
    the row. One of those was broken and it was the fixture.
    """
    import shutil

    found = shutil.which("fux")
    if found is None:
        # Not on PATH at all: someone is running `python -m fux`, or a venv
        # `fux` that PATH does not see. Nothing can shadow what is not there.
        return Check("fux on PATH", True, "no `fux` on PATH - nothing to shadow", level="warn")

    ours = Path(sys.executable).parent / Path(found).name
    try:
        if ours.exists() and Path(found).samefile(ours):
            return Check("fux on PATH", True, f"{found} (this interpreter's)", level="warn")
    except OSError:
        pass

    node_ish = _is_node_shim(Path(found))

    if not node_ish:
        return Check(
            "fux on PATH",
            True,
            f"{found} - not this interpreter's, but not the Node reader either",
            level="warn",
        )

    return Check(
        "fux on PATH",
        False,
        f"{found} is the NODE reader (fux-engine), and it resolves before "
        f"{ours} - it only READS, so write verbs will refuse. Run `fux --version` "
        "to see which you get, or call this one as `python -m fux`",
        level="warn",
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
            "committed; check .fux/.gitignore lists `runtime/` (SR-DOTFUX)",
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


def _index_temp_ignored(root: Path) -> Check:
    """`.fux/index/<shard>.jsonl.tmp` must be gitignored (W-185, 2026-09-15).

    🔴 **Because this row exists for the repositories the fix cannot reach.**
    `.fux/.gitignore` is write-if-missing ([SR-DOTFUX](records/0102) decision
    6a: engine-owned, annotatable), so a repository set up before 2026-09-15 has
    a `.gitignore` without the line and **will never be given one**. A row is
    the only thing that reaches it.

    **What goes wrong without it.** `store/writer.py::_atomic_write` writes the
    temp file beside the shard, inside a committed directory, and `post-commit`
    defers — so a consumer's next `git add -A` overlaps a live writer, lists the
    temp file and cannot stat it::

        fatal: unable to stat '.fux/index/ad.jsonl.tmp': No such file or directory

    Measured at **2 335 failures in 3 933 `git add -A` runs** against a writer
    renaming shards, and **0 in 3 871** with the rule in place.

    ⚠ **`warn`, not `error`.** Nothing is wrong with the index, no answer is
    affected, and the failure needs a concurrent writer — a repository that
    never commits twice in a row will never see it. It is still worth a line,
    because when it does fire the message is about fux's internals and the
    consumer has no way to connect the two.
    """
    name = "index temp files ignored"
    probe = root / fuxdir.FUX_DIR / "index" / "00.jsonl.tmp"
    ignored = _is_git_ignored(root, probe)
    if ignored is None:
        return Check(name, True, "skipped (not a git checkout)")
    if ignored:
        return Check(name, True, "a write in flight cannot break a concurrent `git add`")
    return Check(
        name,
        False,
        "add `index/*.jsonl.tmp` to .fux/.gitignore - a background re-index "
        "leaves a temp file in the committed index directory, and a `git add -A` "
        "running at that moment fails with `unable to stat` (W-185)",
        level="warn",
    )


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
        # W-66 Phase 4 / SR-CLI, 2026-08-22: `doctor` had no machine-readable
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
            # SR-ACQUIRED and SR-URL-FRESHNESS both say to check their veto
            # with `fux doctor --json` — *"the `as-ingested` count against
            # total verified citations"* — and a caller doing that must not
            # have to parse an English sentence out of `detail`. An empty
            # object means no receipts are journalled, which is *unknown* and
            # not a zero share; `freshness_counts` says why they are different.
            payload["freshness"] = freshness_counts(root)
            # W-200, for the `runner`/`freshness` reason: a caller checking
            # whether its index is still the one its decoders would produce
            # must not have to parse an English sentence out of `detail`.
            # **Absent counts and zero counts are different** — an empty
            # object means no ledger, which is *unknown*, not *clean*.
            payload["provenance"] = provenance_counts(root)
        print(json_mod.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    for check in checks:
        # ASCII only — Windows' default console codepage (cp1252/"charmap")
        # can't encode U+2714/U+2717 and the process crashes on print()
        # rather than degrading; caught by CI's windows runners.
        mark = "OK" if check.ok else ("WARN" if check.level == "warn" else "FAIL")
        print(f"[{mark}] {check.name}: {check.detail}")
    return exit_code
