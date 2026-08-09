"""Rule Proposer (rule-proposer.md) — the §4 gate, dedup, retro, triage, and the
hard lines: drafts auto / ratify human / nothing auto-active or constitutional,
all on a $0/stdlib/deterministic harness path (no LLM, no network)."""
from __future__ import annotations

import inspect
from types import SimpleNamespace

from fux import candidates, check, cliquery, loader, proposer
from fux.findings import blocking
from tests.conftest import write_rule


def _magic(project, literal: str) -> None:
    (project / "src").mkdir(exist_ok=True)
    (project / "src" / f"m{literal}.py").write_text(
        f"a = {literal}\nb = {literal}\nc = {literal}\n", encoding="utf-8")


# ── §4 gate ──────────────────────────────────────────────────────────────────

def test_real_decision_drafts_with_why(project):
    added = proposer.from_json(project, [{
        "kind": "convention", "title": "avg-cost, never FIFO, for lot accounting",
        "why": "FIFO double-counts wash sales", "why_source": "PR #41",
        "code_refs": ["src/cost.py"]}])
    assert len(added) == 1
    c = added[0]
    assert c.has_why() and c.why_source == "PR #41" and c.state == "pending"
    assert candidates.path_of(project).exists()
    assert candidates.read(project)[0].why.startswith("FIFO")


def test_trivial_restatement_drafts_nothing(project):
    # not a rule, no why, not an invariant → pure code-restatement → dropped.
    added = proposer.from_json(project, [{
        "kind": "rule", "title": "x is assigned to x", "code_refs": ["src/a.py"]}])
    assert added == []
    assert candidates.read(project) == []


def test_invariant_without_why_flags_todo(project):
    added = proposer.from_json(project, [{
        "kind": "invariant", "title": "account balance never goes negative",
        "invariant": True, "code_refs": ["src/ledger.py"]}])
    assert len(added) == 1
    assert added[0].why == candidates.TODO and not added[0].has_why()


def test_duplicate_of_existing_rule_is_skipped(project):
    write_rule(project, "lots", "---\nid: lots\ntype: convention\nstatus: active\n"
               "code_refs:\n  - src/cost.py\n---\n**Convention:** avg cost. **Why:** x.\n")
    added = proposer.from_json(project, [{
        "kind": "convention", "title": "avg cost for lots", "why": "same idea",
        "code_refs": ["src/cost.py"]}])
    assert added == []                          # dedup vs the existing active rule


# ── retro (mine + git-history why), bounded ──────────────────────────────────

def test_retro_is_capped(project):
    for lit in ("86400", "3600", "1440"):
        _magic(project, lit)
    assert len(proposer.retro(project, cap=2)) == 2


def test_retro_dedups_on_rerun_and_flags_todo_without_git(project):
    for lit in ("86400", "3600", "1440"):
        _magic(project, lit)
    first = proposer.retro(project)
    assert len(first) == 3
    assert all(c.why == candidates.TODO for c in first)   # no git repo → no why
    assert proposer.retro(project) == []                  # deduped on rerun


# ── hard lines: nothing auto-active / constitutional; surface never blocks ────

def test_nothing_auto_activates_or_promotes_constitutional(project):
    proposer.from_json(project, [{"kind": "rule", "title": "t", "why": "w",
                                  "code_refs": ["src/a.py"]}])
    assert all(c.state == "pending" for c in candidates.read(project))
    rules = loader.resolve(project).rules
    assert not any(r.tier == "constitutional" for r in rules if hasattr(r, "tier"))
    assert all(r.fm.get("tier", "standard") != "constitutional" for r in rules)


def test_drafts_land_in_candidates_not_drift_and_never_block(project):
    proposer.from_json(project, [{"kind": "rule", "title": "scoped t", "why": "w",
                                  "code_refs": ["src/a.py"]}])
    findings = check.run(project)
    assert not any(f.kind == "candidate" for f in findings)
    assert not blocking([f for f in findings if f.kind == "candidate"])
    drift = (project / ".fux" / "out" / "DRIFT.md").read_text()
    assert "pending review" in drift                # one-line pointer only
    assert "scoped t" not in drift                  # the draft itself stays out of DRIFT


# ── triage: human accept promotes one draft to a standard active rule ─────────

def test_accept_promotes_to_active_standard_rule(project):
    added = proposer.from_json(project, [{
        "kind": "convention", "title": "tabs over spaces here", "why": "tooling",
        "code_refs": ["src/a.py"]}])
    cid = added[0].cid
    assert cliquery._accept_candidate(project, cid) == 0
    promoted = {c.cid: c for c in candidates.read(project)}[cid]
    assert promoted.state == "accepted"
    by_id = loader.resolve(project).by_id()
    new = next(r for r in by_id.values() if r.fm.get("source") == "session")
    assert new.status == "active" and new.fm.get("tier") == "standard"


def test_reject_records_so_it_is_not_reproposed(project):
    added = proposer.from_json(project, [{"kind": "rule", "title": "r", "why": "w",
                                          "code_refs": ["src/a.py"]}])
    cid = added[0].cid
    args = SimpleNamespace(action="reject", id=cid, pending=False, why_todo=False)
    assert cliquery.cmd_candidates(args) == 0
    assert {c.cid: c for c in candidates.read(project)}[cid].state == "rejected"


# ── guard: the harness path names no model / network client ──────────────────

def test_harness_path_has_no_model_or_network_import():
    for mod in (proposer, candidates):
        src = inspect.getsource(mod)
        for bad in ("anthropic", "openai", "requests", "httpx",
                    "urllib.request", "http.client", "socket"):
            assert bad not in src, f"{mod.__name__} references {bad}"
