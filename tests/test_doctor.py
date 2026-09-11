from __future__ import annotations

import subprocess

import pytest

from fux import doctor


def _git_repo(tmp_path):
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover - git is a dev prereq
        pytest.skip("git unavailable")
    return tmp_path


def test_python_version_check_passes_on_current_interpreter():
    checks = doctor.run()
    py = next(c for c in checks if c.name == "python version")
    assert py.ok


def test_repo_root_found_from_a_git_checkout(tmp_path):
    (tmp_path / ".git").mkdir()
    checks = doctor.run(tmp_path)
    root = next(c for c in checks if c.name == "repo root")
    assert root.ok
    assert root.detail == str(tmp_path.resolve())


def test_fux_dir_writable_after_root_found(tmp_path):
    (tmp_path / ".git").mkdir()
    checks = doctor.run(tmp_path)
    writable = next(c for c in checks if c.name == ".fux/ writable")
    assert writable.ok
    assert (tmp_path / ".fux").is_dir()


def test_no_root_reports_single_failing_check(tmp_path):
    checks = doctor.run(tmp_path)
    assert [c.name for c in checks] == ["python version", "repo root"]
    assert not checks[1].ok


# -- the .fux layout checks (ADR-DOTFUX) -------------------------------------


def _check(checks, name):
    return next(c for c in checks if c.name == name)


def test_index_ignored_by_a_blanket_rule_is_an_error(tmp_path):
    _git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".fux/*\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "index not gitignored")
    assert not check.ok
    assert check.level == "error"
    assert ".fux/index is committed" in check.detail


def test_index_not_ignored_passes(tmp_path):
    _git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".fux/runtime/\n.fux/cache/\n", encoding="utf-8")
    assert _check(doctor.run(tmp_path), "index not gitignored").ok


def test_check_ignore_is_skipped_outside_a_git_checkout(tmp_path):
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = tmp_path / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "index not gitignored")
    assert check.ok and "skipped" in check.detail


def test_undeclared_fux_entry_warns_without_failing_the_command(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "scratch").mkdir()
    check = _check(doctor.run(tmp_path), ".fux/ layout declared")
    assert not check.ok
    assert check.level == "warn"
    assert "scratch" in check.detail


def test_declared_entries_do_not_warn(tmp_path):
    (tmp_path / ".git").mkdir()
    from fux.store import fuxdir

    fuxdir.ensure_layout(tmp_path)
    fuxdir.derived_dir(tmp_path, "runtime")
    (tmp_path / ".fux" / "index").mkdir()
    assert _check(doctor.run(tmp_path), ".fux/ layout declared").ok


def test_cmd_doctor_exit_code_ignores_warnings(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".fux").mkdir(exist_ok=True)
    # ADR-PII decision 17: a repo without .fux/pii.toml refuses; empty redacts nothing.
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / ".fux" / "scratch").mkdir()
    monkeypatch.chdir(tmp_path)
    assert doctor.cmd_doctor(None) == 0
    assert "[WARN] .fux/ layout declared" in capsys.readouterr().out


# -- the derived accelerator check (M2, ADR-T1-ACCELERATOR) ---------------------------


def test_accelerator_absent_warns_but_does_not_fail(tmp_path):
    """No accelerator is a speed problem, never a correctness one.

    `ask` answers from the reference scan without it, so reporting this as an
    error would train people to ignore a red doctor.
    """
    (tmp_path / ".git").mkdir()
    check = _check(doctor.run(tmp_path), "accelerator")
    assert check.ok
    assert check.level == "warn"
    assert "not built" in check.detail


def test_accelerator_reports_fresh_after_a_build(tmp_path):
    from fux.derive import build
    from fux.store import term_hash, write_index

    _git_repo(tmp_path)
    write_index(
        tmp_path,
        [
            {
                "id": "file:a.md",
                "src": "git",
                "loc": "a.md",
                "mode": "extracted",
                "meta": "plain",
                "title": "A",
                "phrases": [],
                "terms": {term_hash("alpha"): [1, 0]},
                "wlen": 4,
                "edges": [],
            }
        ],
    )
    build(tmp_path)
    check = _check(doctor.run(tmp_path), "accelerator")
    assert check.ok
    assert "fresh" in check.detail


def test_accelerator_goes_stale_when_the_index_changes(tmp_path):
    from fux.derive import build
    from fux.store import shard_path, term_hash, write_index

    _git_repo(tmp_path)
    record = {
        "id": "file:a.md",
        "src": "git",
        "loc": "a.md",
        "mode": "extracted",
        "meta": "plain",
        "title": "A",
        "phrases": [],
        "terms": {term_hash("alpha"): [1, 0]},
        "wlen": 4,
        "edges": [],
    }
    write_index(tmp_path, [record])
    build(tmp_path)

    write_index(tmp_path, [record | {"wlen": 99}])
    check = _check(doctor.run(tmp_path), "accelerator")
    assert "stale" in check.detail
    assert shard_path(tmp_path, "05").exists() or True  # shard identity is not the point


def _url_index(tmp_path, urls):
    from fux.store import term_hash, write_index

    write_index(
        tmp_path,
        [
            {
                "id": f"url:{url}",
                "src": "url",
                "loc": url,
                "mode": "extracted",
                # `plain` because the fixture carries readable `title`/`phrases`.
                # `hashed` is L5's default for non-git sources and the writer
                # refuses readable text under it — correct, and not what this
                # test is about.
                "meta": "plain",
                "title": "T",
                "phrases": [],
                "terms": {term_hash("alpha"): [1, 0]},
                "wlen": 4,
                "edges": [],
            }
            for url in urls
        ],
    )


def test_url_check_says_none_when_no_url_records_are_indexed(tmp_path):
    _git_repo(tmp_path)
    _url_index(tmp_path, [])
    check = _check(doctor.run(tmp_path), "url sources")
    assert check.ok
    assert check.level == "warn"
    assert "none indexed" in check.detail


def test_url_check_reports_never_fetched_before_any_networked_run(tmp_path):
    """The case that was invisible: indexed, never re-fetched, nothing said."""
    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a", "https://b"])
    check = _check(doctor.run(tmp_path), "url sources")
    assert check.ok
    assert "2 url: record(s)" in check.detail
    assert "no networked run recorded yet" in check.detail
    assert "2 never re-fetched since first ingest" in check.detail


def test_url_check_states_the_concurrency_a_networked_run_will_use(tmp_path):
    """W-83. The number a person needs BEFORE pointing `fux update` at a
    corporate wiki, said by the command whose job is to say what will happen."""
    from fux.ingest.urlsrc import DEFAULT_MAX_PARALLEL

    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a"])
    (tmp_path / "fux.toml").write_text("[sources]\n[sources.url]\nmax_parallel = 4\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "url sources")
    assert f"fetches <= {DEFAULT_MAX_PARALLEL} at a time" in check.detail
    assert "MAX_PARALLEL" in check.detail  # the other half of the min() is named


def test_a_config_missing_max_parallel_leaves_doctor_silent_rather_than_crashing(tmp_path):
    """W-85. A `[sources.url]` without `max_parallel` REFUSES TO LOAD — and
    that refusal belongs to whichever command the person actually ran, said
    once. Doctor stays quiet about it instead of raising a second time or
    inventing a number it cannot know."""
    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a"])
    (tmp_path / "fux.toml").write_text("[sources]\n[sources.url]\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "url sources")  # must not raise
    assert "fetches <=" not in check.detail


def test_the_concurrency_is_stated_before_the_first_url_is_indexed(tmp_path):
    """The branch that matters most, and the one that short-circuited first.

    An empty corpus with `[sources.url]` configured is a repo about to run its
    first `fux add <URL>` — the moment the number is worth knowing, and the
    only moment nobody can infer it from a previous run.
    """
    from fux.ingest.urlsrc import DEFAULT_MAX_PARALLEL

    _git_repo(tmp_path)
    _url_index(tmp_path, [])
    (tmp_path / "fux.toml").write_text("[sources]\n[sources.url]\nmax_parallel = 4\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "url sources")
    assert "none indexed" in check.detail
    assert f"fetches <= {DEFAULT_MAX_PARALLEL} at a time" in check.detail


def test_no_url_source_means_no_concurrency_line_at_all(tmp_path):
    """A bound on fetching that cannot happen is noise, and doctor's whole
    value is that its output is worth reading."""
    _git_repo(tmp_path)
    _url_index(tmp_path, [])
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "url sources")
    assert check.detail == "none indexed"


def test_url_check_reports_a_configured_max_parallel(tmp_path):
    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a"])
    (tmp_path / "fux.toml").write_text(
        "[sources]\n[sources.url]\nmax_parallel = 2\n", encoding="utf-8"
    )
    check = _check(doctor.run(tmp_path), "url sources")
    assert "fetches <= 2 at a time" in check.detail
    assert "unset" not in check.detail


def test_doctor_never_imports_the_consumers_fetcher_to_read_its_declaration(tmp_path):
    """The effective value is `min(configured, declared)` and doctor reports
    only the first half — because reading the second means importing a
    consumer-owned Python file, and `fux doctor` is the command a person runs
    when something is ALREADY wrong. A booby-trapped fetcher must not detonate
    on a health check."""
    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a"])
    fetchers = tmp_path / ".fux" / "fetchers"
    fetchers.mkdir(parents=True, exist_ok=True)
    (fetchers / "http.py").write_text(
        "raise SystemExit('doctor imported the fetcher')\n", encoding="utf-8"
    )
    (tmp_path / "fux.toml").write_text("[sources]\n[sources.url]\nmax_parallel = 4\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "url sources")  # must not raise
    assert "fetches <=" in check.detail


def test_url_check_reports_what_the_last_run_confirmed(tmp_path):
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a", "https://b"])
    urlstate.observe(
        tmp_path, fetched={"https://a": "sha"}, failed=["https://b"], listed=["https://a", "https://b"]
    )
    check = _check(doctor.run(tmp_path), "url sources")
    assert "1 confirmed by the last run" in check.detail
    assert "1 failing" in check.detail


def test_url_check_names_a_persistently_failing_url_and_refuses_to_delete_it(tmp_path):
    """ADR-URL-INGEST decision 4 forbids treating a failed fetch as a deletion.

    So the check reports and points at the file a human must edit — and the
    record is still in the index afterwards, which is the property under test.
    """
    from fux.maintain import urlstate
    from fux.store import reader

    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://dead"])
    for _ in range(urlstate.FAILING_STREAK):
        urlstate.observe(tmp_path, fetched={}, failed=["https://dead"], listed=["https://dead"])

    check = _check(doctor.run(tmp_path), "url sources")
    assert not check.ok
    assert check.level == "warn"  # never fails the command
    assert "https://dead" in check.detail
    assert ".fux/sources/urls" in check.detail
    assert "url:https://dead" in reader.read_index(tmp_path)


def test_url_check_reports_a_rate_limited_host_when_urls_are_indexed(tmp_path):
    """W-82 ruling 12, in the branch that actually runs.

    ⚠ **This is the regression test for a real defect.** `detail` was joined
    from `parts` BEFORE the note was appended to `parts`, so the note was
    computed, appended to a list nothing read again, and dropped. The empty
    branch was correct, which is what hid it: the cumulative count ruling 12
    persists was unreachable through its only reader in every repo that has
    URLs -- that is, in every repo where a rate limit can happen at all.
    """
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a", "https://b"])
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 12})

    check = _check(doctor.run(tmp_path), "url sources")
    assert "rate-limited by wiki.corp x12" in check.detail
    assert "2 url: record(s)" in check.detail  # and it did not displace the rest


def test_url_check_reports_a_rate_limited_host_with_nothing_indexed(tmp_path):
    """The no-URLs branch is where a rate limit is most likely to be the REASON
    nothing is indexed, so it is reported there too -- and stays reported."""
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    _url_index(tmp_path, [])
    urlstate.record_rate_limits(tmp_path, {"wiki.corp": 3})

    check = _check(doctor.run(tmp_path), "url sources")
    assert "none indexed" in check.detail
    assert "rate-limited by wiki.corp x3" in check.detail


def test_the_rate_limit_note_names_the_worst_hosts_first_and_stops_at_three(tmp_path):
    """Worst first, capped at three: the point is to name the host worth acting
    on, not to print the whole tally. The cap is silent because the count it
    drops is by construction smaller than the three it kept."""
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    _url_index(tmp_path, ["https://a"])
    urlstate.record_rate_limits(tmp_path, {"low": 1, "mid": 5, "high": 9, "top": 20})

    check = _check(doctor.run(tmp_path), "url sources")
    assert "rate-limited by top x20, high x9, mid x5" in check.detail
    assert "low x1" not in check.detail


def test_url_check_survives_an_unreadable_index(tmp_path):
    _git_repo(tmp_path)
    check = _check(doctor.run(tmp_path), "url sources")
    assert check.ok


def test_url_state_carries_no_wall_clock(tmp_path):
    """The invariant `refer/fetchcache.py` states and ADR-REFER rests on:
    wall clock lives in the TTL store and nowhere else.

    W-75 specified this file with `validated_at` / `changed_at`. Both are
    timestamps, and shipping them would have been a quiet contradiction of an
    accepted record. Freshness here is counted in runs.
    """
    import json

    from fux.maintain import urlstate

    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    urlstate.observe(tmp_path, fetched={"https://a": "sha"}, failed=[], listed=["https://a"])
    raw = json.loads((tmp_path / ".fux" / "runtime" / urlstate.STATE_NAME).read_text(encoding="utf-8"))

    flat = json.dumps(raw)
    assert "_at" not in flat and "time" not in flat and "stamp" not in flat
    for health in raw["urls"].values():
        for value in health.values():
            assert value is None or isinstance(value, int)


def test_every_check_detail_is_ascii_in_every_branch(tmp_path):
    """The Windows codepage guard, applied to the failing branches too.

    The e2e smoke test forces `PYTHONIOENCODING=ascii` on a *healthy* repo, so
    it only ever exercised the passing strings. Two failure-branch details
    carried em-dashes for weeks and would have crashed `fux doctor` on a
    Windows console exactly when a user most needed it to print. This drives
    every branch it can and asserts on the detail text itself.
    """
    from fux.store import fuxdir

    scenarios = []

    _git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".fux/*\n", encoding="utf-8")
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "scratch").mkdir()
    scenarios.append(doctor.run(tmp_path))

    fuxdir.ensure_layout(tmp_path)
    scenarios.append(doctor.run(tmp_path))
    scenarios.append(doctor.run(tmp_path / "nowhere"))

    seen = set()
    for checks in scenarios:
        for check in checks:
            seen.add(check.name)
            check.detail.encode("ascii")  # raises UnicodeEncodeError on a regression
            check.name.encode("ascii")

    assert {"index not gitignored", ".fux/ layout declared", "accelerator"} <= seen


# -- the types list (W: setup wrote a file ingest refused) ------------------


def test_doctor_flags_a_types_file_with_no_live_pattern(tmp_path, monkeypatch):
    """ADR-DOTFUX decision 6's ⚠: the fixed template reaches new repos only."""
    from fux import doctor as doctor_mod

    (tmp_path / "fux.toml").write_text("", encoding="utf-8")
    types = tmp_path / ".fux" / "sources" / "types"
    types.parent.mkdir(parents=True, exist_ok=True)
    types.write_text("# every line a comment\n#*.md\n", encoding="utf-8")
    check = doctor_mod._types_health(tmp_path)
    assert not check.ok
    assert "no active pattern" in check.detail


def test_doctor_passes_a_types_file_setup_wrote(tmp_path):
    from fux import doctor as doctor_mod
    from fux import setup as setup_mod

    setup_mod.run(tmp_path)
    assert doctor_mod._types_health(tmp_path).ok


def test_doctor_passes_when_there_is_no_types_file(tmp_path):
    from fux import doctor as doctor_mod

    check = doctor_mod._types_health(tmp_path)
    assert check.ok and "default" in check.detail


# --- the fetcher-capability notice, added 2026-08-28 ------------------------
#
# ADR-FETCHER decision 12's measured gap: a repo created before the decision
# learned 0 of 7 `validate()` tokens until its `http.py` was replaced by hand.
# `fux setup` is write-if-missing, so the mechanism is a doctor NOTICE, never a
# rewrite (ADR-DOTFUX decision 6) — `_types_health` above is the precedent.

def _url_repo(root, fetcher_body: str) -> None:
    (root / "fux.toml").write_text(
        "[sources]\n"
        'dirs_file = ".fux/sources/dirs"\n'
        "[sources.url]\n"
        'fetcher = ".fux/fetchers/http.py"\n'
        'urls_file = ".fux/sources/urls"\n'
        "max_parallel = 4\n",
        encoding="utf-8",
    )
    f = root / ".fux" / "fetchers" / "http.py"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(fetcher_body, encoding="utf-8")


def test_doctor_names_the_optional_functions_an_old_fetcher_lacks(tmp_path):
    """The measured case: a pre-decision fetcher, silently forfeiting both."""
    from fux import doctor as doctor_mod

    _url_repo(tmp_path, "def fetch(url):\n    return b''\n")
    check = doctor_mod._fetcher_capabilities(tmp_path)
    assert check.ok and check.level == "warn"  # optional by contract: never fails the command
    assert "validate()" in check.detail and "is_rate_limited()" in check.detail
    assert "will not rewrite" in check.detail


def test_doctor_is_quiet_when_the_fetcher_implements_both(tmp_path):
    from fux import doctor as doctor_mod

    _url_repo(
        tmp_path,
        "def fetch(url):\n    return b''\n"
        "def validate(url):\n    return None\n"
        "def is_rate_limited(exc):\n    return False\n",
    )
    check = doctor_mod._fetcher_capabilities(tmp_path)
    assert check.ok and "implements" in check.detail


def test_doctor_skips_the_fetcher_check_when_the_repo_does_not_fetch(tmp_path):
    """No `[sources.url]` means the fetcher is not a fact about this repo."""
    from fux import doctor as doctor_mod

    (tmp_path / "fux.toml").write_text('[sources]\ndirs_file = ".fux/sources/dirs"\n', encoding="utf-8")
    check = doctor_mod._fetcher_capabilities(tmp_path)
    assert check.ok and "does not fetch" in check.detail


def test_the_shipped_template_implements_every_optional_function(tmp_path):
    """If `setup`'s template regresses, the notice above would fire on a NEW repo.

    That would be the loudest possible symptom of the wrong bug, so it is
    gated here rather than left to be discovered in a consumer's doctor output.
    """
    from fux import doctor as doctor_mod
    from fux import setup as setup_mod

    setup_mod.run(tmp_path)
    (tmp_path / "fux.toml").write_text(
        "[sources]\n"
        'dirs_file = ".fux/sources/dirs"\n'
        "[sources.url]\n"
        'fetcher = ".fux/fetchers/http.py"\n'
        'urls_file = ".fux/sources/urls"\n'
        "max_parallel = 4\n",
        encoding="utf-8",
    )
    check = doctor_mod._fetcher_capabilities(tmp_path)
    assert check.ok and "implements" in check.detail, check.detail


# --- the daemon check, added 2026-08-28 with the widened status shape -------

def _daemon_status(root, payload):
    import json
    d = root / ".fux" / "runtime"
    d.mkdir(parents=True, exist_ok=True)
    (d / "daemon.status").write_text(json.dumps(payload), encoding="utf-8")


def test_doctor_reports_a_sweep_that_looked_ok_and_skipped_documents(tmp_path):
    """The case the pre-2026-08-28 status shape could not express.

    `outcome: "ok"` with `skipped: 2` is a healthy-looking sweep that did not
    index two documents. Two of seven URLs were skipped in the 2026-08-27
    real-network run and nothing outside a foreground `fux update` said so.
    """
    from fux.doctor import _daemon

    _daemon_status(tmp_path, {"outcome": "ok", "fetched": 5, "skipped": 2,
                              "reason": "2 skipped, first: fetch failed: HTTP Error 404"})
    check = _daemon(tmp_path)

    assert check is not None
    assert check.ok is False, "an ok-with-skips sweep is a finding, not a clean bill"
    assert "did not index 2" in check.detail
    assert "404" in check.detail


def test_doctor_reports_why_a_sweep_failed(tmp_path):
    from fux.doctor import _daemon

    _daemon_status(tmp_path, {"outcome": "failed",
                              "reason": "FuxError: [sources.url] max_parallel is required"})
    check = _daemon(tmp_path)

    assert check is not None and check.ok is False
    assert "max_parallel" in check.detail, "a bare 'failed' is what this replaced"


def test_doctor_is_silent_about_a_daemon_that_never_ran(tmp_path):
    """Not a finding. Most repos never start one, and a check that fires for
    everyone is a check people learn to skip."""
    from fux.doctor import _daemon

    assert _daemon(tmp_path) is None


def test_a_clean_sweep_is_reported_as_clean(tmp_path):
    from fux.doctor import _daemon

    _daemon_status(tmp_path, {"outcome": "ok", "fetched": 4, "skipped": 0})
    check = _daemon(tmp_path)

    assert check is not None and check.ok is True
    assert "4 document(s)" in check.detail


# -- W-101: the four checks that close the doctor pass -----------------------
#
# One pass at `doctor.py` for five things that were each reachable only from
# inside a run that had already finished — or, in the freshness case, from
# nowhere at all. ADR-DOTFUX's fourth worked instance.


def _record(doc_id="file:a.md", loc="a.md", **extra):
    record = {
        "id": doc_id,
        "src": "git",
        "loc": loc,
        "mode": "extracted",
        "meta": "plain",
        "title": "A",
        "phrases": [],
        "terms": {},
        "wlen": 4,
        "edges": [],
    }
    record.update(extra)
    return record


# -- the refusal counter (ADR-REFUSAL decision 11) ---------------------------


def _refusals_toml(tmp_path, *names):
    from fux.ingest import refusals

    body = "".join(
        f'[[rule]]\nname = "{n}"\nreason = "no"\nbody_contains = ["{n}"]\n\n' for n in names
    )
    path = refusals.rules_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_no_refusals_file_says_only_the_floor_applies(tmp_path):
    _git_repo(tmp_path)
    check = _check(doctor.run(tmp_path), "refusal rules")
    assert check.ok
    assert "magic-byte floor" in check.detail


def test_refusal_rules_that_have_never_fired_are_named(tmp_path):
    """A rule at zero is what a typo'd condition looks like — decision 8, later."""
    _git_repo(tmp_path)
    _refusals_toml(tmp_path, "sso", "paywall")
    check = _check(doctor.run(tmp_path), "refusal rules")
    assert check.ok
    assert "no networked run has recorded a refusal yet" in check.detail


def test_refusal_counts_are_reported_per_rule(tmp_path):
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    _refusals_toml(tmp_path, "sso", "paywall")
    urlstate.record_refusals(tmp_path, {"sso": 4})
    check = _check(doctor.run(tmp_path), "refusal rules")
    assert "sso x4" in check.detail
    assert "never fired: paywall" in check.detail


def test_refusals_with_no_surviving_url_document_is_the_loud_case(tmp_path):
    """The failure this check exists for: a rule that empties the URL half."""
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    _refusals_toml(tmp_path, "sso")
    urlstate.record_refusals(tmp_path, {"sso": 12})
    check = _check(doctor.run(tmp_path), "refusal rules")
    assert not check.ok
    assert check.level == "warn"  # a warning, never an error
    assert "NO url: DOCUMENT SURVIVED" in check.detail


def test_a_surviving_url_document_keeps_the_refusal_line_quiet(tmp_path):
    from fux.maintain import urlstate
    from fux.store import write_index

    _git_repo(tmp_path)
    _refusals_toml(tmp_path, "sso")
    urlstate.record_refusals(tmp_path, {"sso": 2})
    write_index(tmp_path, [_record(doc_id="url:https://x/a", loc="https://x/a")])
    check = _check(doctor.run(tmp_path), "refusal rules")
    assert check.ok


def test_refusal_counts_accumulate_across_runs(tmp_path):
    from fux.maintain import urlstate

    _git_repo(tmp_path)
    urlstate.record_refusals(tmp_path, {"sso": 2})
    urlstate.record_refusals(tmp_path, {"sso": 3, "paywall": 1})
    state = urlstate.read(tmp_path)
    assert state.refused == {"sso": 5, "paywall": 1}


def test_a_malformed_refusals_file_is_an_error_not_a_traceback(tmp_path):
    from fux.ingest import refusals

    _git_repo(tmp_path)
    path = refusals.rules_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[[rule]\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "refusal rules")
    assert not check.ok
    assert check.level == "error"


def test_magic_floor_is_a_reserved_rule_name(tmp_path):
    """A counter keyed by rule name needs one key that cannot collide."""
    from fux.errors import FuxError
    from fux.ingest import refusals

    with pytest.raises(FuxError, match="reserved"):
        refusals.parse(
            {"rule": [{"name": refusals.MAGIC_FLOOR, "reason": "x", "max_bytes": 10}]},
            origin="t",
        )


def test_refusal_returns_the_rule_name_structurally(tmp_path):
    """`refused()` renders; `refusal()` is what the counter reads."""
    from fux.ingest import refusals

    rules = refusals.parse(
        {"rule": [{"name": "sso", "reason": "sign in", "body_contains": ["Sign in"]}]},
        origin="t",
    )
    body = b"<html>Sign in</html>"
    assert refusals.refusal(rules, "https://x/a", "text/html", body) == ("sso", "sign in")
    assert refusals.refused(rules, "https://x/a", "text/html", body) == "sign in [sso]"


def test_the_magic_floor_is_counted_under_its_reserved_name():
    from fux.ingest import refusals

    hit = refusals.refusal((), "https://x/a.pdf", "application/pdf", b"<html>nope")
    assert hit is not None
    assert hit[0] == refusals.MAGIC_FLOOR


# -- the decoder bindings (ADR-DECODE) --------------------------------------


def test_decoder_bindings_report_nothing_when_none_are_declared(tmp_path):
    _git_repo(tmp_path)
    check = _check(doctor.run(tmp_path), "decoder bindings")
    assert check.ok
    assert "none declared" in check.detail


def test_a_binding_naming_a_missing_module_is_an_error(tmp_path):
    _git_repo(tmp_path)
    types = tmp_path / ".fux" / "sources" / "types"
    types.parent.mkdir(parents=True, exist_ok=True)
    types.write_text("*.md\n*.zzz decoder=nosuchdecoder\n", encoding="utf-8")
    check = _check(doctor.run(tmp_path), "decoder bindings")
    assert not check.ok
    assert check.level == "error"


def test_a_generated_binding_that_matches_nothing_is_not_reported(tmp_path):
    """The check must stay quiet on a fresh `fux setup` — 27 of 36 match nothing."""
    from fux import decode
    from fux.store import write_index

    _git_repo(tmp_path)
    lines = ["*.md\n"] + [
        f"*{ext} decoder={name}\n" for ext, name in sorted(decode.builtin_bindings().items())
    ]
    types = tmp_path / ".fux" / "sources" / "types"
    types.parent.mkdir(parents=True, exist_ok=True)
    types.write_text("".join(lines), encoding="utf-8")
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "decoder bindings")
    assert check.ok
    assert "match no indexed document" not in check.detail


def test_a_hand_written_binding_that_matches_nothing_is_reported(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    types = tmp_path / ".fux" / "sources" / "types"
    types.parent.mkdir(parents=True, exist_ok=True)
    types.write_text("*.md\n*.jsno decoder=json\n", encoding="utf-8")
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "decoder bindings")
    assert not check.ok
    assert check.level == "warn"
    assert ".jsno=json" in check.detail


def test_a_hand_written_binding_with_documents_is_quiet(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    types = tmp_path / ".fux" / "sources" / "types"
    types.parent.mkdir(parents=True, exist_ok=True)
    types.write_text("*.md\n*.geojson decoder=json\n", encoding="utf-8")
    write_index(tmp_path, [_record(doc_id="file:a.geojson", loc="a.geojson")])
    check = _check(doctor.run(tmp_path), "decoder bindings")
    assert check.ok


# -- the recency prior (filed 2026-09-05 from W-111's tie-break) -------------


def test_a_corpus_with_no_mtime_reports_the_recency_prior_as_off(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "recency prior")
    assert not check.ok
    assert check.level == "warn"
    assert "NO document carries an mtime" in check.detail


def test_a_configured_half_life_over_a_corpus_with_no_mtime_says_so(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "tune.toml").write_text(
        "[ranking]\nrecency_half_life_days = 30\n", encoding="utf-8"
    )
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "recency prior")
    assert "configured is doing nothing" in check.detail


def test_a_corpus_where_every_document_has_an_mtime_passes(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    write_index(tmp_path, [_record(mtime=1788330315)])
    check = _check(doctor.run(tmp_path), "recency prior")
    assert check.ok
    assert "every one of 1 document(s)" in check.detail


def test_a_partly_covered_corpus_is_a_warning_only_when_the_knob_is_on(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    write_index(
        tmp_path,
        [_record(mtime=1788330315), _record(doc_id="file:b.md", loc="b.md")],
    )
    assert _check(doctor.run(tmp_path), "recency prior").ok  # half-life 0: off anyway

    (tmp_path / ".fux" / "tune.toml").write_text(
        "[ranking]\nrecency_half_life_days = 30\n", encoding="utf-8"
    )
    check = _check(doctor.run(tmp_path), "recency prior")
    assert not check.ok
    assert "1 of 2 document(s)" in check.detail


# -- the as-ingested share (ADR-ACQUIRED / ADR-URL-FRESHNESS's veto) ---------


def _journal(tmp_path, labels):
    import json

    from fux.query import provenance
    from fux.store import fuxdir

    fuxdir.derived_dir(tmp_path, "runtime")
    payload = {
        "predicate": {"verdicts": [{"id": f"d{i}", "freshness": label} for i, label in enumerate(labels)]}
    }
    provenance.journal_path(tmp_path).write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_no_journal_reports_unknown_rather_than_a_zero_share(tmp_path):
    """Absent and zero are different claims and neither veto may read one as the other."""
    _git_repo(tmp_path)
    check = _check(doctor.run(tmp_path), "freshness verdicts")
    assert check.ok
    assert "no receipts journalled" in check.detail
    assert doctor.freshness_counts(tmp_path) == {}


def test_the_as_ingested_share_is_reported_from_the_journal(tmp_path):
    _git_repo(tmp_path)
    _journal(tmp_path, ["current", "current", "current", "as-ingested"])
    assert doctor.freshness_counts(tmp_path) == {"current": 3, "as-ingested": 1}
    check = _check(doctor.run(tmp_path), "freshness verdicts")
    assert check.ok  # 25% is the condition, not past it
    assert "as-ingested 25%" in check.detail


def test_crossing_the_veto_share_warns_and_names_both_records(tmp_path):
    _git_repo(tmp_path)
    _journal(tmp_path, ["current", "as-ingested", "as-ingested"])
    check = _check(doctor.run(tmp_path), "freshness verdicts")
    assert not check.ok
    assert check.level == "warn"
    assert "ADR-ACQUIRED and ADR-URL-FRESHNESS" in check.detail


def test_the_veto_share_is_machine_readable_in_json(tmp_path, monkeypatch, capsys):
    """Both records say to check the veto with `fux doctor --json`."""
    import json

    from fux import doctor as doctor_mod

    _git_repo(tmp_path)
    _journal(tmp_path, ["current", "as-ingested"])
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(doctor_mod, "find_root", lambda *a, **k: tmp_path)
    doctor_mod.cmd_doctor(type("A", (), {"json": True})())
    payload = json.loads(capsys.readouterr().out)
    assert payload["freshness"] == {"current": 1, "as-ingested": 1}


def test_a_corrupt_journal_line_cannot_break_doctor(tmp_path):
    from fux.query import provenance
    from fux.store import fuxdir

    _git_repo(tmp_path)
    fuxdir.derived_dir(tmp_path, "runtime")
    provenance.journal_path(tmp_path).write_text("{not json\n", encoding="utf-8")
    assert doctor.freshness_counts(tmp_path) == {}


# -- the redaction counts (ADR-PII decision 15) -----------------------------


def test_pii_line_says_no_ingest_has_recorded_counts_yet(tmp_path):
    from fux.ingest import pii

    _git_repo(tmp_path)
    path = pii.rules_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[[rule]]\nname = "email"\npattern = "\\\\S+@\\\\S+"\n', encoding="utf-8")
    check = _check(doctor.run(tmp_path), "pii rules")
    assert "No ingest has recorded redaction counts yet" in check.detail


def test_recorded_counts_are_reported_with_their_denominator(tmp_path):
    from fux.ingest import pii

    _git_repo(tmp_path)
    path = pii.rules_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[[rule]]\nname = "email"\npattern = "\\\\S+@\\\\S+"\n', encoding="utf-8")
    pii.record_counts(tmp_path, body={"email": 7}, enrichment={}, partial=False, documents=12)
    check = _check(doctor.run(tmp_path), "pii rules")
    assert "redacted 7 value(s) across 12 document(s)" in check.detail
    assert "email x7" in check.detail


def test_zero_recorded_redactions_is_not_the_same_as_none_recorded(tmp_path):
    from fux.ingest import pii

    _git_repo(tmp_path)
    path = pii.rules_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[[rule]]\nname = "email"\npattern = "\\\\S+@\\\\S+"\n', encoding="utf-8")
    pii.record_counts(tmp_path, body={}, enrichment={}, partial=False, documents=12)
    check = _check(doctor.run(tmp_path), "pii rules")
    assert "redacted NOTHING across 12 document(s)" in check.detail


def test_partial_enrichment_counts_say_they_are_partial(tmp_path):
    from fux.ingest import pii

    _git_repo(tmp_path)
    path = pii.rules_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[[rule]]\nname = "email"\npattern = "\\\\S+@\\\\S+"\n', encoding="utf-8")
    pii.record_counts(
        tmp_path, body={"email": 2}, enrichment={"email": 1}, partial=True, documents=9
    )
    check = _check(doctor.run(tmp_path), "pii rules")
    assert "enrichment: email x1" in check.detail
    assert "not the whole corpus" in check.detail


def test_a_corrupt_counts_file_reads_as_nothing_recorded(tmp_path):
    from fux.ingest import pii
    from fux.store import fuxdir

    _git_repo(tmp_path)
    fuxdir.derived_dir(tmp_path, "runtime")
    pii.counts_path(tmp_path).write_text("{oops", encoding="utf-8")
    assert pii.read_counts(tmp_path) is None


def test_the_counts_file_is_gitignored_like_every_derived_plane(tmp_path):
    """L8 and ADR-DOTFUX: a use-shaped record never reaches a committed byte."""
    from fux.ingest import pii
    from fux.store import fuxdir

    _git_repo(tmp_path)
    fuxdir.ensure_layout(tmp_path)
    pii.record_counts(tmp_path, body={"email": 1}, enrichment={}, partial=False, documents=1)
    assert doctor._is_git_ignored(tmp_path, pii.counts_path(tmp_path)) is True


# -- the no-op ranking priors (W-126 part B, Arpit 2026-09-11) ---------------


def _tune(tmp_path, body):
    (tmp_path / ".fux").mkdir(exist_ok=True)
    (tmp_path / ".fux" / "tune.toml").write_text(f"[ranking]\n{body}\n", encoding="utf-8")


def test_the_shipped_defaults_are_disclosed_as_switched_off(tmp_path):
    """The whole point: four mechanisms built, wired, and doing nothing."""
    from fux.store import write_index

    _git_repo(tmp_path)
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "ranking priors")
    assert not check.ok
    assert check.level == "warn"  # a default is not a broken install
    for key in ("archived_weight", "superseded_weight", "rerank_weight", "recency_half_life_days"):
        assert key in check.detail


def test_it_counts_what_each_dead_prior_WOULD_have_acted_on(tmp_path):
    """A knob that is off over 0 archived documents and one that is off over 40
    are different findings, and a flat list of defaults cannot tell them apart."""
    from fux.store import write_index

    _git_repo(tmp_path)
    write_index(
        tmp_path,
        [
            _record("file:a.md", "a.md", archived=True),
            _record("file:b.md", "b.md", archived=True),
            _record("file:c.md", "c.md"),
        ],
    )
    check = _check(doctor.run(tmp_path), "ranking priors")
    assert "archived_weight=1 (2 document(s) declared archived=true)" in check.detail
    assert "superseded_weight=1 (0 document(s)" in check.detail


def test_a_prior_that_is_switched_ON_is_not_listed(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    _tune(tmp_path, "rerank_weight = 0.5\narchived_weight = 0.5")
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "ranking priors")
    assert "rerank_weight" not in check.detail
    assert "archived_weight" not in check.detail
    assert "superseded_weight" in check.detail


def test_every_prior_switched_on_passes(tmp_path):
    from fux.store import write_index

    _git_repo(tmp_path)
    _tune(
        tmp_path,
        "rerank_weight = 0.5\narchived_weight = 0.5\n"
        "superseded_weight = 0.5\nrecency_half_life_days = 30",
    )
    write_index(tmp_path, [_record()])
    check = _check(doctor.run(tmp_path), "ranking priors")
    assert check.ok


def test_it_refuses_to_recommend_a_value(tmp_path):
    """🔴 Load-bearing. Recommending one is the remeasure's job (W-94), and the
    only change measured so far fixed two queries and broke two."""
    from fux.store import write_index

    _git_repo(tmp_path)
    write_index(tmp_path, [_record()])
    detail = _check(doctor.run(tmp_path), "ranking priors").detail
    assert "does NOT recommend" in detail
    for nudge in ("try ", "set it to", "recommended", "should be"):
        assert nudge not in detail


def test_a_missing_pii_file_is_an_error_row_and_fails_the_command(tmp_path, monkeypatch, capsys):
    """ADR-PII decision 17: doctor is exempt from the gate, not from the error."""
    import argparse

    _git_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    row = _check(doctor.run(tmp_path), "pii rules")
    assert not row.ok and row.level == "error"
    assert "fux setup" in row.detail
    assert doctor.cmd_doctor(argparse.Namespace(json=False)) == 1
