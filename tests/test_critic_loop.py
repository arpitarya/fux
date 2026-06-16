"""Constitution layer — Phase 5: the critique→act loop + the report-first coverage gate."""
from __future__ import annotations

import json

from fux import criticloop, gate
from fux.criticloop import Verdict
from conftest import write_rule

DET = ("---\nid: recon\ntype: rule\nstatus: active\nprinciple: totals reconcile to source\n"
       "enforcement: deterministic\ncheck: \"total == source\"\nkeywords: [reconcile, total]\n"
       "---\n**Rule:** totals reconcile to source.\n")
JUDGE = ("---\nid: tone\ntype: rule\nstatus: active\nprinciple: responses hedge appropriately\n"
         "enforcement: judgment\nkeywords: [hedge, tone, response]\n---\n**Rule:** hedge.\n")


def test_deterministic_pass_blocks_without_calling_judge(project):
    write_rule(project, "recon", DET)
    write_rule(project, "tone", JUDGE)
    (project / ".fux" / "verify").mkdir(parents=True, exist_ok=True)
    (project / ".fux" / "verify" / "recon.json").write_text('{"total": 1, "source": 2}')  # fails
    calls = []

    def judge(proposal, principle):
        calls.append(principle.id)
        return Verdict(principle.id, "pass")

    res = criticloop.critique(project, "reconcile the total against the source hedge tone", judge=judge)
    statuses = {v.principle: v.status for v in res.verdicts}
    assert statuses.get("recon") == "fail" and res.blocked    # deterministic fail blocks
    assert "recon" not in calls                                # never routed to the judge


def test_judgment_violation_is_critiqued_then_revised(project):
    write_rule(project, "tone", JUDGE)
    bad = criticloop.critique(project, "a blunt response about tone and hedge",
                              judge=lambda p, r: Verdict(r.id, "fail", "too blunt"))
    assert bad.blocked                                         # judgment fail blocks the change
    good = criticloop.critique(project, "a hedged response about tone and hedge",
                               judge=lambda p, r: Verdict(r.id, "pass", "ok"))
    assert not good.blocked                                    # revised proposal passes


def test_pending_when_no_judge(project):
    write_rule(project, "tone", JUDGE)
    res = criticloop.critique(project, "a response about tone and hedge")   # judge=None
    assert res.pending and res.pending[0].principle == "tone"
    assert not res.blocked                                     # pending is not a fail


def test_record_writes_audit_line(project):
    write_rule(project, "tone", JUDGE)
    res = criticloop.critique(project, "a response about tone and hedge")
    p = criticloop.record(project, res)
    assert p.exists()
    row = json.loads(p.read_text().splitlines()[-1])
    assert row["proposal"] and isinstance(row["verdicts"], list)


def test_coverage_gate_reports_not_blocks(project):
    # An important_glob path (**/*.py) governed by zero rules → reported, never blocks.
    (project / "src" / "ungoverned.py").write_text("x = 1\n", encoding="utf-8")
    code, report = gate.run(project)
    assert code == 0                                           # report-first: not a blocker
    assert "ungoverned" in report and "report-only" in report
