"""Graph drift/tier stamps — deterministic, sourced from seal/check (plan §7, §17.22).

The viewer's drift pulse + constitutional crown read `drift` and `tier` off each
rule node in graph.json. Both must come from the existing $0 deterministic passes
(seal fingerprint / frontmatter tier), never be invented — these tests pin that.
"""
from __future__ import annotations

from fux import check, config, graph, loader, paths, seal
from tests.conftest import write_rule


def _build(root):
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    g = graph.build(root, rs, cfg)
    return {n["id"]: n for n in g["nodes"] if n["id"].startswith("rule:")}


def _rules(root):
    cfg = config.load(paths.Footprint(root).config)
    return loader.resolve(root, cfg).rules


def _seal_rule(root):
    (root / "src" / "calc.py").write_text("def pnl(v):\n    return v * 2\n", encoding="utf-8")
    write_rule(root, "pnl", "---\nid: pnl\ntype: formula\nstatus: active\n"
               "code_refs:\n  - src/calc.py#L1-L2\n---\n**Rule:** x.\n")
    seal.stamp(root, _rules(root))                         # affirm the seal


def test_rule_nodes_carry_tier_and_drift(project):
    write_rule(project, "r1", "---\nid: r1\ntype: rule\nstatus: active\n---\n**Rule:** a.\n")
    nodes = _build(project)
    n = nodes["rule:r1"]
    assert n["tier"] == "standard"        # default when no tier: in frontmatter
    assert n["drift"] is False            # nothing sealed → nothing to drift from


def test_unsealed_rule_is_not_drift(project):
    # A rule with code_refs but no stored seal: must NOT pulse — nothing affirmed.
    (project / "src" / "calc.py").write_text("def pnl(v):\n    return v * 2\n", encoding="utf-8")
    write_rule(project, "pnl", "---\nid: pnl\ntype: formula\nstatus: active\n"
               "code_refs:\n  - src/calc.py#L1-L2\n---\n**Rule:** x.\n")
    assert _build(project)["rule:pnl"]["drift"] is False


def test_sealed_then_structural_change_flips_drift_true(project):
    _seal_rule(project)
    assert _build(project)["rule:pnl"]["drift"] is False    # sealed + matching
    # Structural edit (operator flip) — same change the seal test uses.
    (project / "src" / "calc.py").write_text("def pnl(v):\n    return v - 2\n", encoding="utf-8")
    assert _build(project)["rule:pnl"]["drift"] is True


def test_drift_matches_check_unsealed(project):
    """The graph's `drift` flag is the same signal as `fux check`'s `unsealed`."""
    _seal_rule(project)
    (project / "src" / "calc.py").write_text("def pnl(v):\n    return v - 2\n", encoding="utf-8")
    drifted_in_graph = {nid[len("rule:"):] for nid, n in _build(project).items() if n["drift"]}
    unsealed_in_check = {f.rule_id for f in check.run(project) if f.kind == "unsealed"}
    assert drifted_in_graph == unsealed_in_check == {"pnl"}


def test_tier_is_read_from_frontmatter(project):
    # tier is a verbatim frontmatter read, not derived — the crown follows ratification.
    write_rule(project, "con", "---\nid: con\ntype: invariant\nstatus: active\n"
               "tier: constitutional\n---\n**Rule:** never.\n")
    assert _build(project)["rule:con"]["tier"] == "constitutional"
