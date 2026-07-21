"""Determinism: the hard requirement, proven at the byte level."""

from __future__ import annotations

import shutil

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
