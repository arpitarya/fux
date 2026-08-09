"""Verification hardening: usage-weighted decay + contradiction suggest (§17.20)."""
from __future__ import annotations

import datetime as _dt

from fux import governance, lint, recall, usage
from fux.model import Rule
from tests.conftest import write_rule


def _memory(rid: str, updated: str) -> Rule:
    fm = {"id": rid, "type": "memory", "status": "active", "updated": updated}
    return Rule(id=rid, type="memory", fm=fm, body="note", path=None, layer="project")


def test_recent_use_keeps_an_old_memory_alive():
    cfg = {"memory_ttl_days": 30}
    today = _dt.date(2026, 6, 5)
    old = _memory("m1", "2026-01-01")                       # ~155 days → past TTL
    assert governance.is_decayed(old, cfg, today)           # decays on time alone
    served = today - _dt.timedelta(days=5)                  # but used 5 days ago
    assert not governance.is_decayed(old, cfg, today, last_served=served)


def test_unused_old_memory_still_decays():
    cfg = {"memory_ttl_days": 30}
    today = _dt.date(2026, 6, 5)
    old = _memory("m2", "2026-01-01")
    stale_serve = today - _dt.timedelta(days=200)           # last used long ago
    assert governance.is_decayed(old, cfg, today, last_served=stale_serve)


def test_usage_record_and_roundtrip(project):
    usage.record(project, ["a", "b"], today=_dt.date(2026, 6, 5))
    usage.record(project, ["a"], today=_dt.date(2026, 6, 5))
    data = usage.load(project)
    assert data["a"]["count"] == 2 and data["b"]["count"] == 1
    assert usage.last_served(project)["a"] == _dt.date(2026, 6, 5)


def test_recall_records_usage_when_enabled(project):
    write_rule(project, "pnl", "---\nid: pnl\ntype: rule\nstatus: active\n"
               "keywords: [profit]\n---\n**Rule:** profit today.\n")
    cfg = project / ".fux" / "config.toml"
    cfg.write_text(cfg.read_text().replace("usage_tracking = false", "usage_tracking = true")
                   if "usage_tracking" in cfg.read_text()
                   else cfg.read_text() + "\nusage_tracking = true\n")
    recall.run(project, "profit", top=3)
    assert "pnl" in usage.load(project)


def test_overlap_unlinked_rules_flagged(project):
    common = "code_refs:\n  - src/agg.py#L10-L20\n"
    write_rule(project, "rule-a", f"---\nid: rule-a\ntype: rule\nstatus: active\n{common}"
               "---\n**Rule:** A. **Why:** x.\n")
    write_rule(project, "rule-b", f"---\nid: rule-b\ntype: rule\nstatus: active\n{common}"
               "---\n**Rule:** B. **Why:** y.\n")
    kinds = [f.kind for f in lint.run(project)]
    assert "overlap-unlinked" in kinds


def test_linked_overlap_not_flagged(project):
    write_rule(project, "rule-a", "---\nid: rule-a\ntype: rule\nstatus: active\n"
               "code_refs:\n  - src/agg.py#L10-L20\nrelated: [rule-b]\n"
               "---\n**Rule:** A. **Why:** x.\n")
    write_rule(project, "rule-b", "---\nid: rule-b\ntype: rule\nstatus: active\n"
               "code_refs:\n  - src/agg.py#L10-L20\n---\n**Rule:** B. **Why:** y.\n")
    assert "overlap-unlinked" not in [f.kind for f in lint.run(project)]
