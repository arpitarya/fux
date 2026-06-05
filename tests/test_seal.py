"""Proof-carrying rules (AST seals) + knowledge archaeology (plan §17.22, §17.24)."""
from __future__ import annotations

import subprocess

from fux import check, explain, loader, config, paths, seal
from tests.conftest import write_rule


def _pyfile(root, body: str):
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "calc.py").write_text(body, encoding="utf-8")


def _rule(root, **extra):
    extra_lines = "".join(f"{k}: {v}\n" for k, v in extra.items())
    write_rule(root, "pnl", f"---\nid: pnl\ntype: formula\nstatus: active\n"
               f"code_refs:\n  - src/calc.py#L1-L3\n{extra_lines}---\n**Rule:** x.\n")


def _rules(root):
    cfg = config.load(paths.Footprint(root).config)
    return loader.resolve(root, cfg).rules


def test_fingerprint_ignores_rename_and_whitespace(project):
    a = "def pnl(v):\n    return v * 2\n"
    b = "def total(value):\n    return   value * 2\n"          # rename + spacing
    c = "def pnl(v):\n    return v + 2\n"                      # changed operator
    fa = seal.fingerprint(a, ".py", 1, 2)
    assert fa == seal.fingerprint(b, ".py", 1, 2)             # structure unchanged
    assert fa != seal.fingerprint(c, ".py", 1, 2)             # * → + breaks it


def test_seal_then_structural_change_flags_unsealed(project):
    _pyfile(project, "def pnl(v):\n    return v * 2\n# pad\n")
    _rule(project)
    seal.stamp(project, _rules(project))                      # affirm
    assert not [f for f in check.run(project) if f.kind == "unsealed"]
    # Cosmetic edit (comment) must NOT break the seal.
    _pyfile(project, "def pnl(v):\n    return v * 2\n# different comment\n")
    assert not [f for f in check.run(project) if f.kind == "unsealed"]
    # Structural edit (operator flip) MUST break it.
    _pyfile(project, "def pnl(v):\n    return v - 2\n# pad\n")
    flagged = [f for f in check.run(project) if f.kind == "unsealed"]
    assert flagged and flagged[0].rule_id == "pnl"


def test_seal_is_a_single_line_edit(project):
    # Inline lists and field order must survive sealing untouched (only +seal:).
    _pyfile(project, "def pnl(v):\n    return v * 2\n")
    path = write_rule(project, "pnl", "---\nid: pnl\ntype: formula\nstatus: active\n"
                      "aliases: [a, b]\ncode_refs:\n  - src/calc.py#L1-L2\n"
                      "---\n**Rule:** x.\n")
    before = path.read_text()
    seal.stamp(project, _rules(project))
    after = path.read_text().splitlines()
    assert "aliases: [a, b]" in after            # inline list NOT reformatted
    added = [ln for ln in after if ln not in before.splitlines()]
    assert added == [f"seal: {[ln for ln in after if ln.startswith('seal:')][0].split(': ')[1]}"]
    assert len([ln for ln in after if ln.startswith("seal:")]) == 1


def test_reseal_replaces_not_duplicates(project):
    _pyfile(project, "def pnl(v):\n    return v * 2\n")
    _rule(project)
    seal.stamp(project, _rules(project))
    _pyfile(project, "def pnl(v):\n    return v + 99\n")   # change → new fingerprint
    seal.stamp(project, _rules(project))
    body = (project / ".fux" / "rules" / "pnl.md").read_text()
    assert body.count("seal:") == 1                # replaced in place, not appended


def test_unsealed_is_advisory_not_blocking():
    from fux import findings
    assert "unsealed" not in findings.BLOCKING


def test_history_renders_commits(project):
    _pyfile(project, "def pnl(v):\n    return v * 2\n")
    _rule(project)
    r = explain.why(project, "pnl")
    for args in (["init"], ["add", "-A"],
                 ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "seed pnl rule"]):
        subprocess.run(["git", *args], cwd=project, capture_output=True)
    out = explain.render_history(project, r)
    assert "pnl — history" in out and "seed pnl rule" in out
