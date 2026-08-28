"""The daemon's sweep must actually reach the ingest. It did not, for days.

**Found by W-87 P5's follow-on**, running the full unit suite in an environment
that could run it. `_sweep` read:

    from ..ingest import run as ingest_run
    ingest_run.run(root, refresh_urls=True)

`fux/ingest/__init__.py` re-exports the FUNCTION `run` from the submodule of
the same name, so the first line binds a function and the second raises
`AttributeError`. **The broad `except Exception` that makes a daemon outlive a
bad sweep turned that into `"failed"`, every sweep, in every repository** — the
daemon started, held its pid file, wrote its status, slept its interval, and
never indexed one byte.

⚠ **The test that should have caught it patched the same wrong object**, so it
failed on its own monkeypatch line and never exercised the path it was named
for. A test written from the same misunderstanding as the code is not a check.

⚠ **This is the surface [W-82 ruling 3] is being held on** — *"narrow-by-default
does not land until the daemon has been proven to run in a real repo."* It had
not been, and this is what was underneath.
"""

from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

import pytest

from fux.maintain import daemon, runner

SRC = Path(__file__).resolve().parents[2] / "src" / "fux"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repo with URL sources declared, which is what a sweep needs."""
    (tmp_path / "fux.toml").write_text(
        "[sources]\n\n[sources.url]\n"
        'urls_file = ".fux/sources/urls"\nmax_parallel = 4\n',
        encoding="utf-8",
    )
    sources = tmp_path / ".fux" / "sources"
    sources.mkdir(parents=True)
    (sources / "dirs").write_text("docs\n", encoding="utf-8")
    (sources / "urls").write_text("", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nsweepterm body\n", encoding="utf-8")

    monkeypatch.setattr(runner, "acquire", lambda _root: True)
    monkeypatch.setattr(runner, "release", lambda _root: None)
    return tmp_path


def test_a_sweep_of_a_healthy_repo_returns_ok(repo):
    """The whole bug in one line: this returned `"failed"` unconditionally."""
    assert daemon._sweep(repo)["outcome"] == "ok"


def test_the_sweep_actually_indexed_something(repo):
    """⚠ **Not `== "ok"` alone.** `_sweep` swallows every exception, so a
    return value is the one thing that cannot prove work happened — that is
    exactly how the defect stayed invisible. Assert the index."""
    from fux.store import read_index

    daemon._sweep(repo)

    assert "file:docs/a.md" in read_index(repo)


def test_the_sweep_calls_the_real_ingest_and_a_patch_of_it_is_seen(repo, monkeypatch):
    """The seam the broken test was reaching for, on the right object."""
    calls = []
    ingest_run = import_module("fux.ingest.run")
    monkeypatch.setattr(ingest_run, "run", lambda *a, **k: calls.append((a, k)))

    assert daemon._sweep(repo)["outcome"] == "ok"
    assert len(calls) == 1, "the sweep did not reach fux.ingest.run.run"
    assert calls[0][1].get("refresh_urls") is True


def test_one_bad_sweep_still_returns_failed_rather_than_raising(repo, monkeypatch):
    """The resilience the broad handler is there for, kept."""

    def _boom(*_a, **_k):
        raise RuntimeError("the network went away")

    monkeypatch.setattr(import_module("fux.ingest.run"), "run", _boom)

    assert daemon._sweep(repo)["outcome"] == "failed"


def test_the_ingest_package_never_re_exports_run_under_the_submodule_s_name():
    """**The root cause, guarded where it lives** — not at each call site.

    ⚠ **This test was originally the opposite shape.** It swept `src/` for
    `from fux.ingest import run`, on the reasoning that the form binds a
    function. That reasoning was correct **only while the package re-exported
    `run` under the bare name**, and it stopped being true on 2026-08-27 when
    Arpit ruled the re-export aliased. A check that keeps asserting a repaired
    hazard is a check that forbids a safe thing for a false reason, so it was
    turned around to watch the one line that could bring the hazard back.

    With the alias in place, **every import form is safe**:
    `from fux.ingest import run` now imports the SUBMODULE, and
    `import fux.ingest.run as x` binds the module. Nothing at a call site needs
    to know this, which is the entire point of fixing it at the source.
    """
    tree = ast.parse((SRC / "ingest" / "__init__.py").read_text(encoding="utf-8"))

    offenders = [
        f"line {node.lineno}: from .{node.module} import {alias.name}"
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if alias.name == "run" and alias.asname is None
    ]

    assert not offenders, (
        "fux/ingest/__init__.py re-exports `run` under the submodule's own "
        "name again — that shadows `fux.ingest.run` and every attribute access "
        "on an imported `run` starts raising AttributeError. It cost three "
        "defects on 2026-08-27, one of them a daemon that reported success "
        "while indexing nothing for a day. Alias it:\n  " + "\n  ".join(offenders)
    )


def test_every_import_form_of_the_ingest_run_module_now_reaches_the_module():
    """Asserted by executing them, not by reasoning about them.

    ⚠ **The original defect was a wrong belief about what an import binds**, and
    a test that reasons about imports can hold the same wrong belief. These four
    lines are the four forms anyone would actually write.
    """
    from importlib import import_module
    from types import ModuleType

    import fux.ingest
    import fux.ingest.run as via_import_as
    from fux.ingest import run as via_from_package
    from fux.ingest.run import run as via_from_module

    assert isinstance(via_import_as, ModuleType)
    assert isinstance(via_from_package, ModuleType)
    assert isinstance(import_module("fux.ingest.run"), ModuleType)
    assert callable(via_from_module), "the function is still reachable, just not shadowing"
    assert not hasattr(fux.ingest, "run") or isinstance(
        getattr(fux.ingest, "run"), ModuleType
    ), "fux.ingest.run resolves to the module, never to a callable"


# --- The status shape, widened 2026-08-28 (Arpit) ---------------------------
#
# The sweep wrote {"outcome": ...} and nothing else, and both halves of that
# cost something real:
#
#   * a FuxError about `max_parallel` and a dead network were the SAME
#     "failed", so a misconfigured repo failed forever with nothing to go on;
#   * an "ok" sweep could skip URLs SILENTLY -- two of seven did in the
#     2026-08-27 real-network run, and the only surface that said so was a
#     foreground `fux update` nobody runs.

def test_a_failed_sweep_says_why(repo, monkeypatch):
    """The first half: a failure carries its reason and its exception type."""
    import fux.ingest.run as ingest_run
    from fux.errors import FuxError
    from fux.maintain import daemon


    def boom(*a, **k):
        raise FuxError("[sources.url] max_parallel is required")

    monkeypatch.setattr(ingest_run, "run", boom)
    result = daemon._sweep(repo)

    assert result["outcome"] == "failed"
    assert "max_parallel" in result["reason"], result
    assert "FuxError" in result["reason"], (
        "the TYPE distinguishes the repo's own refusal (fix your config) from a "
        "surprise (fix fux), and a bare message loses that"
    )


def test_an_ok_sweep_reports_what_it_skipped(repo, monkeypatch):
    """The second half, and the one the old shape could not express at all.

    `outcome: "ok"` with `skipped: 2` is a healthy-looking sweep that did not
    index two documents. Before this, that state was indistinguishable from a
    clean run.
    """
    import fux.ingest.run as ingest_run
    from fux.ingest.gitdir import Skipped
    from fux.maintain import daemon


    class Report:
        doc_count = 5
        skipped = [
            Skipped(rel_path="https://a.test/x", reason="fetch failed: HTTP Error 404"),
            Skipped(rel_path="https://b.test/y", reason="no decoder for image/png"),
        ]

    monkeypatch.setattr(ingest_run, "run", lambda *a, **k: Report())
    result = daemon._sweep(repo)

    assert result["outcome"] == "ok", "skips are not a failed sweep"
    assert result["skipped"] == 2
    assert result["fetched"] == 3
    assert "404" in result["reason"], "the first skip's reason is carried"


def test_the_reason_is_bounded(repo, monkeypatch):
    """A file written every sweep may not grow without someone deciding it should."""
    import fux.ingest.run as ingest_run
    from fux.maintain import daemon

    monkeypatch.setattr(
        ingest_run, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x" * 5000))
    )
    assert len(daemon._sweep(repo)["reason"]) <= 300


def test_a_clean_sweep_carries_no_reason(repo, monkeypatch):
    """`reason` explains something or is absent — never an empty string.

    A field that is always present but usually empty is one a reader learns to
    ignore, which is how the old bare `"failed"` earned its silence.
    """
    import fux.ingest.run as ingest_run
    from fux.maintain import daemon


    class Clean:
        doc_count = 4
        skipped = []

    monkeypatch.setattr(ingest_run, "run", lambda *a, **k: Clean())
    result = daemon._sweep(repo)

    assert result == {"outcome": "ok", "fetched": 4, "skipped": 0}
