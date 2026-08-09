"""Constitution layer — Phase 4: the deterministic/judgment split (router + backfill guide)."""
from __future__ import annotations

from fux import check, critic
from fux.model import Rule


def _rule(rid, **fm):
    fm.setdefault("type", "rule")
    fm.setdefault("status", "active")
    return Rule(id=rid, type=fm["type"], fm={"id": rid, **fm}, body="**Rule:** x.",
               path=None, layer="project")


DET = _rule("det", principle="numbers reconcile to the cent", enforcement="deterministic",
            check="total == sum(parts)")
JUDGE = _rule("judge", principle="the answer hedges appropriately", enforcement="judgment")
# A judgment principle that *also* carries a check: — must still never be run deterministically.
JUDGE_FAKED = _rule("jf", principle="tone is respectful", enforcement="judgment",
                    check="len(x) > 0")


def test_deterministic_principle_never_reaches_ai_pass():
    routed = critic.for_ai([DET, JUDGE])
    assert DET not in routed and JUDGE in routed          # det excluded structurally


def test_judgment_principle_never_faked_deterministic():
    routed = critic.for_deterministic([DET, JUDGE_FAKED])
    assert DET in routed and JUDGE_FAKED not in routed    # judgment excluded despite its check:


def test_partitions_are_disjoint():
    rules = [DET, JUDGE, JUDGE_FAKED]
    ai, det = critic.for_ai(rules), critic.for_deterministic(rules)
    assert not (set(id(r) for r in ai) & set(id(r) for r in det))


def test_untagged_candidate_is_advisory_not_blocking(project):
    from conftest import write_rule
    from fux.findings import blocking
    # An invariant with a check: but no principle → a backfill candidate.
    write_rule(project, "inv", "---\nid: inv\ntype: invariant\nstatus: active\n"
                                "check: \"total == 1\"\n---\n**Invariant:** total is one.\n")
    findings = check.run(project)
    cand = [f for f in findings if f.kind == "untagged-candidate"]
    assert len(cand) == 1 and cand[0].rule_id == "inv"
    assert blocking(findings, "strict") == []             # advisory — never blocks, even strict


def test_existing_untagged_rules_produce_no_finding(project):
    from conftest import write_rule
    # A plain convention with no check: and a non-normative type → not a candidate.
    write_rule(project, "conv", "---\nid: conv\ntype: convention\nstatus: active\n---\n"
                                "**Convention:** name files by domain.\n")
    findings = check.run(project)
    assert not [f for f in findings if f.kind == "untagged-candidate"]
