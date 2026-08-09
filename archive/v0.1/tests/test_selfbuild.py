"""`fux self-build` + the `--self` scope (scrape-howto handoff §C / §4b).

The bundle is generated from fux's own source and ships in the wheel; these tests
prove (a) it regenerates byte-identically (self-knowledge can't drift from code),
(b) the committed bundle is fresh, and (c) `--self` answers from fux's own graph in
any repo, even one with no project `.fux/`.
"""
from __future__ import annotations

import os
from types import SimpleNamespace

from fux import cligraph, cliquery, selfbuild


def test_bundle_regenerates_byte_identically(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    selfbuild.build(dest=a)
    selfbuild.build(dest=b)
    for rel in (".fux/out/graph.json", ".fux/out/rules.json", ".fux/out/INDEX.md",
                ".fux/config.toml"):
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), rel


def test_committed_bundle_is_fresh(tmp_path):
    """The bundle checked into data/self/ must match a fresh build of fux's source —
    a stale bundle fails CI, so fux's self-knowledge stays pinned to its code."""
    fresh = tmp_path / "fresh"
    selfbuild.build(dest=fresh)
    committed = selfbuild.bundle_root()
    assert (fresh / ".fux" / "out" / "graph.json").read_bytes() == \
        (committed / ".fux" / "out" / "graph.json").read_bytes(), \
        "data/self/ is stale — run `fux self-build` and commit the result"


def test_bundle_is_hermetic(tmp_path):
    """The bundle config disables host-global rules so `recall --self` is reproducible
    regardless of what's installed in the host's ~/.claude/fux/global."""
    selfbuild.build(dest=tmp_path)
    cfg = (tmp_path / ".fux" / "config.toml").read_text(encoding="utf-8")
    assert "use_global = false" in cfg


def test_self_scope_works_with_no_project_fux(tmp_path, capsys):
    """`explain --self` answers from fux's own graph from a dir with no `.fux/`."""
    selfbuild.build()                       # ensure the committed bundle exists
    os.chdir(tmp_path)                       # a repo with no footprint
    rc = cligraph.cmd_explain(SimpleNamespace(term="check", **{"self": True}))
    out = capsys.readouterr().out
    assert rc == 0
    assert "check" in out and "neighbors" in out


def test_self_scope_recall(tmp_path, capsys):
    selfbuild.build()
    os.chdir(tmp_path)
    rc = cliquery.cmd_recall(SimpleNamespace(query="amendment", top=3,
                                             hybrid=False, expand=False, **{"self": True}))
    assert rc == 0
    assert "con-amendment" in capsys.readouterr().out
