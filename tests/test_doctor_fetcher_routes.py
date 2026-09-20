"""`fux doctor`'s three routing rows — W-199 D3/D4, SR-DOCTOR's register.

🔴 **All three are offline and none imports a fetcher.** `doctor` is offline by
contract, and a fetcher is free to open a session at module level — so the
no-import guard is the property worth asserting, the same shape
`test_doctor_fetcher_bindings.py::test_it_never_imports_a_fetcher` uses.
"""

from __future__ import annotations

import importlib
import importlib.util

import pytest

from fux import doctor


def _repo(tmp_path, *, routes="", urls="", fetchers=("http",)):
    (tmp_path / ".git").mkdir(exist_ok=True)
    table = f"[sources.url.routes]\n{routes}" if routes else ""
    (tmp_path / "fux.toml").write_text(
        f'[sources]\n[sources.url]\nmax_parallel = 4\n{table}', encoding="utf-8"
    )
    d = tmp_path / ".fux" / "fetchers"
    d.mkdir(parents=True, exist_ok=True)
    for stem in fetchers:
        (d / f"{stem}.py").write_text("def fetch(url): ...\n", encoding="utf-8")
    src = tmp_path / ".fux" / "sources"
    src.mkdir(parents=True, exist_ok=True)
    (src / "urls").write_text(urls, encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    return tmp_path


def _row(root, name):
    return next(c for c in doctor.run(root) if c.name == name)


# --- fetcher routes ---------------------------------------------------------

def test_a_route_naming_no_file_is_a_FAILURE(tmp_path):
    root = _repo(tmp_path, routes='"x.test" = "glassbox"\n', urls="https://x.test/a fetch=http\n")
    row = _row(root, "fetcher routes")
    assert not row.ok and row.level == "error"
    assert "glassbox" in row.detail


def test_a_route_matching_no_listed_url_is_a_FINDING_not_a_failure(tmp_path):
    """A dead route is usually a typo and occasionally a table written before
    the URLs — never an error on its own."""
    root = _repo(tmp_path, routes='"nobody.test" = "http"\n', urls="")
    row = _row(root, "fetcher routes")
    assert not row.ok and row.level == "warn"
    assert "nobody.test" in row.detail


def test_a_collision_on_a_listed_host_is_a_FAILURE_naming_both(tmp_path):
    root = _repo(
        tmp_path,
        routes='"x.test" = "http"\n"re:^x\\\\.test$" = "http"\n',
        urls="https://x.test/a fetch=http\n",
    )
    row = _row(root, "fetcher routes")
    assert not row.ok and row.level == "error"
    assert "matches 2 routes" in row.detail


def test_a_clean_table_says_how_many_routes_there_are(tmp_path):
    root = _repo(tmp_path, routes='"x.test" = "http"\n', urls="https://x.test/a fetch=http\n")
    row = _row(root, "fetcher routes")
    assert row.ok and "1 route(s)" in row.detail


def test_no_table_and_no_claim_says_every_line_is_a_pin(tmp_path):
    root = _repo(tmp_path, urls="https://x.test/a fetch=http\n")
    assert _row(root, "fetcher routes").ok


def test_the_routes_row_never_imports_a_fetcher(tmp_path, monkeypatch):
    """🔴 The gate, scoped the way `test_doctor_fetcher_bindings`'s is.

    ⚠ **Patching `importlib.import_module` is too wide** — `doctor` imports its
    own modules and would trip it. What must never happen is loading a module
    **by path**, which is the only way a consumer's fetcher can be reached, so
    that is the one function patched.
    """
    root = _repo(tmp_path, routes='"x.test" = "boom"\n', urls="https://x.test/a fetch=boom\n",
                 fetchers=("http", "boom"))
    (root / ".fux" / "fetchers" / "boom.py").write_text(
        'raise AssertionError("doctor imported a fetcher")\n'
        'ROUTES = {"x.test": "boom"}\n', encoding="utf-8"
    )

    def explode(*a, **k):  # pragma: no cover - the point is it is not called
        raise AssertionError("doctor loaded a module by path")

    monkeypatch.setattr(importlib.util, "spec_from_file_location", explode)
    assert _row(root, "fetcher routes").ok


# --- pinned fetchers --------------------------------------------------------

def test_a_pin_the_table_would_resolve_differently_is_named(tmp_path):
    """🔴 The whole cost of SR-URL-LIST decision 16, made visible. Every line is
    a pin by design, so a route changed later moves nothing — this row is the
    only thing that says the two have drifted apart."""
    root = _repo(
        tmp_path, routes='"x.test" = "cdp"\n',
        urls="https://x.test/a fetch=http\n", fetchers=("http", "cdp"),
    )
    row = _row(root, "pinned fetchers")
    assert not row.ok and row.level == "warn"
    assert "pins http" in row.detail and "routes say cdp" in row.detail


def test_it_reports_and_never_rewrites(tmp_path):
    root = _repo(
        tmp_path, routes='"x.test" = "cdp"\n',
        urls="https://x.test/a fetch=http\n", fetchers=("http", "cdp"),
    )
    before = (root / ".fux" / "sources" / "urls").read_text(encoding="utf-8")
    _row(root, "pinned fetchers")
    assert (root / ".fux" / "sources" / "urls").read_text(encoding="utf-8") == before


def test_an_agreeing_pin_is_quiet(tmp_path):
    root = _repo(tmp_path, routes='"x.test" = "http"\n', urls="https://x.test/a fetch=http\n")
    assert _row(root, "pinned fetchers").ok


def test_no_table_means_nothing_for_a_pin_to_disagree_with(tmp_path):
    root = _repo(tmp_path, urls="https://x.test/a fetch=http\n")
    assert _row(root, "pinned fetchers").ok


# --- the register -----------------------------------------------------------

def test_the_register_row_is_quiet_with_no_index(tmp_path):
    root = _repo(tmp_path)
    assert _row(root, "register").ok


def test_the_register_row_reports_drift_against_the_index(tmp_path):
    from fux.ingest import register
    from fux.ingest.run import run

    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    fux = tmp_path / ".fux"
    (fux / "sources").mkdir(parents=True)
    (fux / "sources" / "dirs").write_text("docs\n", encoding="utf-8")
    (fux / "pii.toml").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    run(tmp_path)
    assert _row(tmp_path, "register").ok

    # A register committed from a different ingest than the index beside it —
    # the one thing a committed derived file can get wrong, and the one nobody
    # catches by eye.
    register.write(tmp_path, [register.Row(loc="gone.md", kind="file", sha="s", decoder="d")])
    row = _row(tmp_path, "register")
    assert not row.ok and row.level == "warn"
    assert "gone.md" in row.detail and "docs/a.md" in row.detail
