"""Opt-in capture queue + memory TTL governance ($0, plan §17.2/§17.3)."""
from __future__ import annotations

import datetime as _dt
import subprocess

from fux import capture, check, context, governance, loader
from conftest import write_rule

RULE = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
---
**Rule:** Today's P&L. **Why:** relative to yesterday.
"""


def _git_repo(project):
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "init"], cwd=project, check=True)


# ---- capture ------------------------------------------------------------
def test_capture_queues_changed_files_split_by_coverage(project):
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return sum(h)\n")
    write_rule(project, "day-pnl", RULE)
    _git_repo(project)
    # Change a governed file and add an uncovered one.
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return sum(h) + 1\n")
    (project / "src" / "new_mod.py").write_text("def helper():\n    return 1\n")
    new = capture.observe(project)
    paths = {o.path: o.governed for o in new}
    assert paths.get("src/agg.py") is True
    assert paths.get("src/new_mod.py") is False
    # Dedup: a second observe in the same session adds nothing.
    assert capture.observe(project) == []


def test_capture_skips_secrets(project):
    (project / ".env").write_text("SECRET=abc\n")
    _git_repo(project)
    (project / ".env").write_text("SECRET=xyz\n")
    assert all(o.path != ".env" for o in capture.observe(project))


def test_capture_clear_empties_queue(project):
    (project / "src" / "x.py").write_text("def a():\n    return 1\n")
    _git_repo(project)
    (project / "src" / "x.py").write_text("def a():\n    return 2\n")
    capture.observe(project)
    assert capture.pending(project)
    capture.clear(project)
    assert capture.pending(project) == []


# ---- memory governance --------------------------------------------------
def _memory(project, updated):
    write_rule(project, "old-pref", f"---\nid: old-pref\ntype: memory\nstatus: active\n"
               f"subtype: user\nscope: shared\ncreated: 2020-01-01\nupdated: {updated}\n---\n"
               "**Observation:** prefers probes. **Why:** faster. **How to apply:** use probes.\n")


def test_memory_decays_after_ttl(project):
    old = (_dt.date.today() - _dt.timedelta(days=400)).isoformat()
    _memory(project, old)
    cfg = {"memory_ttl_days": 180}
    rule = next(r for r in loader.resolve(project).rules if r.id == "old-pref")
    assert governance.is_decayed(rule, cfg)


def test_check_flags_and_context_excludes_decayed_memory(project):
    old = (_dt.date.today() - _dt.timedelta(days=400)).isoformat()
    _memory(project, old)
    kinds = {f.kind for f in check.run(project)}
    assert "memory-stale" in kinds
    assert "old-pref" not in context.run(project)      # excluded from injection


def test_fresh_memory_is_kept(project):
    _memory(project, _dt.date.today().isoformat())
    assert "old-pref" in context.run(project)
    assert "memory-stale" not in {f.kind for f in check.run(project)}
