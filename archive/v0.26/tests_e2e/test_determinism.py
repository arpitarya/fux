"""Determinism: the hard requirement, proven at the byte level."""

from __future__ import annotations

import shutil

import pytest

from conftest import fux_tree, run_fux


def test_double_ingest_byte_identical(project):
    run_fux(project, "ingest")
    first = fux_tree(project)
    run_fux(project, "ingest")
    assert fux_tree(project) == first


def test_fresh_reingest_byte_identical(project):
    run_fux(project, "ingest")
    first = fux_tree(project)
    shutil.rmtree(project / ".fux")
    run_fux(project, "ingest")
    assert fux_tree(project) == first


def test_query_outputs_identical_across_runs(ingested):
    ask1 = run_fux(ingested, "ask", "install the widget", "--json").stdout
    ask2 = run_fux(ingested, "ask", "install the widget", "--json").stdout
    assert ask1 == ask2
    ans1 = run_fux(ingested, "answer", "how fast are rollbacks", "--json").stdout
    ans2 = run_fux(ingested, "answer", "how fast are rollbacks", "--json").stdout
    assert ans1 == ans2


def test_lock_is_sorted_and_posix(ingested):
    lines = (ingested / "fux.lock").read_text(encoding="utf-8").splitlines()
    ids = [line.split('"id":"')[1].split('"')[0] for line in lines]
    assert ids == sorted(ids)
    assert not any("\\" in i for i in ids)


def test_lock_is_byte_identical_across_runs(ingested):
    first = (ingested / "fux.lock").read_bytes()
    run_fux(ingested, "ingest")
    assert (ingested / "fux.lock").read_bytes() == first


def test_manifest_is_sorted_and_posix(ingested):
    lines = (ingested / ".fux/index/manifest.jsonl").read_text(encoding="utf-8").splitlines()
    sources = [line.split('"source":"')[1].split('"')[0] for line in lines]
    assert sources == sorted(sources)
    assert not any("\\" in s for s in sources)


# -- debug output never touches stdout (handoff 0005 — the hard gate) --------
#
# This test is written at M1, before any dbg()/timer() call sites exist, and
# must stay green through M6: `off` and `--debug=trace` must always produce
# byte-identical stdout, because dbg() only ever writes to stderr/a file.
# As doctor/why ship (M3/M4) they join this list.

_FRESH_DEBUG_COMMANDS: list[tuple[str, ...]] = [("ingest", "--check")]  # read-only: safe to run twice
_INGESTED_DEBUG_COMMANDS: list[tuple[str, ...]] = [
    ("ask", "install the widget", "--json"),
    ("find", "install the widget", "--json"),
    ("answer", "how fast are rollbacks", "--json"),
    ("doctor",),
    ("doctor", "--json"),
    ("why", "install the widget", "--doc", "docs/guide.md", "--json"),
]


@pytest.mark.parametrize("args", _FRESH_DEBUG_COMMANDS, ids=lambda a: " ".join(a))
def test_debug_trace_flag_does_not_touch_stdout_fresh(project, args):
    off = run_fux(project, *args, check=False)
    trace = run_fux(project, "--debug=trace", *args, check=False)
    assert trace.stdout == off.stdout
    assert trace.returncode == off.returncode


@pytest.mark.parametrize("args", _INGESTED_DEBUG_COMMANDS, ids=lambda a: " ".join(a))
def test_debug_trace_flag_does_not_touch_stdout_ingested(ingested, args):
    off = run_fux(ingested, *args, check=False)
    trace = run_fux(ingested, "--debug=trace", *args, check=False)
    assert trace.stdout == off.stdout
    assert trace.returncode == off.returncode


@pytest.mark.parametrize("args", _INGESTED_DEBUG_COMMANDS, ids=lambda a: " ".join(a))
def test_fux_debug_env_does_not_touch_stdout(ingested, args, monkeypatch):
    off = run_fux(ingested, *args, check=False)
    monkeypatch.setenv("FUX_DEBUG", "trace")
    traced = run_fux(ingested, *args, check=False)
    assert traced.stdout == off.stdout
    assert traced.returncode == off.returncode


def test_debug_trace_flag_does_not_touch_stdout_first_ingest(tmp_path):
    """`ingest` mutates the cache, so compare two *independent* fresh trees
    rather than running it twice against the same one (which would then hit
    the incremental "unchanged" path on the second run).

    `ingest`'s own summary line prints wall-clock elapsed seconds (pre-existing,
    unrelated to debug) — normalize that one field before comparing, or two
    runs of the *same* command would occasionally disagree on the rounded
    tenth-of-a-second regardless of `--debug`.
    """
    import re

    from conftest import CORPUS

    def fresh(name: str):
        proj = tmp_path / name
        shutil.copytree(CORPUS, proj)
        run_fux(
            proj, "setup", "-y",
            "--docs", "docs,notes,office", "--code", "code",
            "--data", "data", "--images", "assets",
        )
        return proj

    def strip_elapsed(text: str) -> str:
        return re.sub(r"Elapsed: [\d.]+s", "Elapsed: Ns", text)

    off = run_fux(fresh("off"), "ingest", check=False)
    trace = run_fux(fresh("trace"), "--debug=trace", "ingest", check=False)
    assert strip_elapsed(trace.stdout) == strip_elapsed(off.stdout)
    assert trace.returncode == off.returncode


def test_two_trace_runs_produce_identical_stderr(ingested):
    first = run_fux(ingested, "--debug=trace", "ask", "install the widget", "--json")
    second = run_fux(ingested, "--debug=trace", "ask", "install the widget", "--json")
    assert first.stderr == second.stderr
