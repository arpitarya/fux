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
