"""Decommission-unblocking work: graph coverage, import, narrative, parity (§17.13–17)."""
from __future__ import annotations

import json

from fux import build, importer, loader, narrative, parity, paths
from fux.model import RuleSet
from conftest import write_rule


# ---- §17.13 full-repo graph coverage -----------------------------------
def test_graph_globs_covers_more_than_important(project):
    # A .js file is graphed (graph_globs) even though coverage's important_globs
    # in the written config.toml are py/ts/tsx only.
    (project / "src" / "util.js").write_text("function helper(){ return 1; }\n")
    (project / "src" / "app.py").write_text("def main():\n    return 1\n")
    build.run(project)
    g = json.loads((project / ".fux" / "out" / "graph.json").read_text())
    files = {n["id"] for n in g["nodes"] if n["type"] == "code-file"}
    assert "src/util.js" in files and "src/app.py" in files


def test_full_mode_graphs_every_file(project):
    (project / "NOTES.txt").write_text("free text\n")
    g_norm = build.run(project, full=False)
    g_full = build.run(project, full=True)
    nodes_full = json.loads((project / ".fux" / "out" / "graph.json").read_text())["nodes"]
    assert any(n["id"] == "NOTES.txt" for n in nodes_full)  # non-source file graphed
    assert g_full["code_files"] >= g_norm["code_files"]


# ---- §17.14 import docs → narrative ------------------------------------
def test_import_docs_stamps_narrative_frontmatter(project):
    docs = project / "legacy"
    docs.mkdir()
    (docs / "ARCHITECTURE.md").write_text("# Architecture\n\nHow Anton is laid out.\n")
    created, skipped = importer.import_docs(project, [str(docs)])
    assert len(created) == 1 and skipped == []
    text = created[0].read_text()
    assert "type: narrative" in text and "id: architecture" in text
    assert "How Anton is laid out." in text          # body preserved


def test_import_skips_existing_without_force(project):
    docs = project / "legacy"; docs.mkdir()
    (docs / "WHAT.md").write_text("# What\n\nThe product.\n")
    importer.import_docs(project, [str(docs)])
    created, skipped = importer.import_docs(project, [str(docs)])
    assert created == [] and len(skipped) == 1


# ---- §17.15 narrative rendering ----------------------------------------
def test_narrative_render_and_build_writes_file(project):
    write_rule(project, "anton-overview", "---\nid: anton-overview\ntype: narrative\n"
               "status: active\ncreated: 2026-06-01\nupdated: 2026-06-01\n---\n"
               "## Overview\n\nAnton is an investment terminal.\n")
    out = narrative.render(RuleSet(rules=loader.resolve(project).rules))
    assert "Fux narrative" in out and "investment terminal" in out
    build.run(project)
    assert (project / ".fux" / "out" / "NARRATIVE.md").exists()


# ---- §17.16 import-memory ----------------------------------------------
def test_import_memory_from_home_dir(project):
    home = paths.home_memory_dir(project)
    home.mkdir(parents=True)
    (home / "MEMORY.md").write_text("- index line\n")          # skipped
    (home / "project_broker_prime.md").write_text(
        "---\nname: project-broker-prime\nmetadata:\n  type: project\n---\n"
        "**Observation:** brokers prime async. **Why:** speed.\n")
    created, _ = importer.import_memory(project, scope="shared")
    assert len(created) == 1
    text = created[0].read_text()
    assert "type: memory" in text and "scope: shared" in text and "brokers prime" in text
    # Imported entry is now a known memory id → parity sees it.
    p = parity.build(project)
    assert p.mem_pending == []


# ---- §17.17 parity gate -------------------------------------------------
def test_parity_reports_not_ready_with_unmigrated_docs(project):
    (project / "docs").mkdir()
    (project / "docs" / "architecture.md").write_text("# Arch\n\nx\n")
    (project / "docs" / "conventions.md").write_text("# Conv\n\nstays\n")  # STAY-listed
    build.run(project)
    p = parity.build(project)
    assert "architecture.md" in p.docs_unmigrated
    assert "conventions.md" not in p.docs_unmigrated   # excluded — seeds global
    assert not p.docs_ok() and not p.ready()


def test_parity_graph_ok_when_no_legacy_store(project):
    build.run(project)
    p = parity.build(project)
    assert p.graph_legacy is None and p.graph_ok()
