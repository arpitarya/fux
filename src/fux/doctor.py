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


def run(start: Path | None = None) -> list[Check]:
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
    return checks


def _output_config_health(root: Path) -> Check:
    """`.fux/output.toml` absent — the repo that predates the file.

    ADR-OUTPUT decision 19 made a missing file a hard `FuxError` at load time.
    The file is write-if-missing (ADR-DOTFUX decision 6), so it reaches **new
    repos only** — which made `ask`, `find` and `doctor` exit 1 in every repo
    that predates it, `doctor` included, the verb you would run to find out
    why. Decision 20 ruled the fork: a missing file resolves to the engine
    defaults, and the repo is reached HERE instead.

    ⚠ **This is decision 6's own prescribed mechanism**, the same one
    `_types_health` implements for `sources/types`: *"if a change must reach
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
    """A committed types file with no live pattern — the shape that stops ingest.

    `read_types` refuses a types file whose every line is a comment, because a
    present file replaces the built-in default entirely (ADR-TYPES decision 2)
    and an empty allowlist would silently empty the index. `fux setup` used to
    write exactly that file, so **`setup` then `ingest` failed on every fresh
    repo** until 2026-08-27.

    ⚠ **The fixed template does not reach a repo that already has the file** —
    ADR-DOTFUX decision 6 is explicit that write-if-missing reaches new repos
    only, and that when a change must reach existing ones the mechanism is *a
    loader refusal or a `doctor` check, never a rewrite*. This is that check.
    """
    path = root / DEFAULT_TYPES_FILE
    if not path.is_file():
        return Check("types list usable", True, "absent - the built-in default applies")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return Check("types list usable", False, f"{DEFAULT_TYPES_FILE}: {exc}")
    live = [ln.lstrip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    allow = [ln for ln in live if not ln.startswith("!")]
    if allow:
        return Check("types list usable", True, f"{DEFAULT_TYPES_FILE}: {len(allow)} pattern(s)")
    return Check(
        "types list usable",
        False,
        f"{DEFAULT_TYPES_FILE} has no active pattern, so `fux ingest` refuses to run - "
        "delete the file to take the built-in default, or re-run `fux setup` after "
        "deleting it to get the default written out",
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
    duplicates = fuxignore.duplicate_warnings(
        root, dirs_file=DEFAULT_DIRS_FILE, types_file=DEFAULT_TYPES_FILE
    )
    if duplicates:
        return Check(
            "fuxignore usable",
            False,
            f"{len(duplicates)} pattern(s) stated in both {fuxignore.IGNORE_FILE} and a "
            f".fux/sources/ list - run `fux ingest --list-skipped` for the detail",
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
        print(json_mod.dumps(payload, indent=2, sort_keys=True))
        return exit_code

    for check in checks:
        # ASCII only — Windows' default console codepage (cp1252/"charmap")
        # can't encode U+2714/U+2717 and the process crashes on print()
        # rather than degrading; caught by CI's windows runners.
        mark = "OK" if check.ok else ("WARN" if check.level == "warn" else "FAIL")
        print(f"[{mark}] {check.name}: {check.detail}")
    return exit_code
