"""Optimal context packing — knapsack picks the best subset under budget (§17.25)."""
from __future__ import annotations

from pathlib import Path

from fux import context, pack
from fux.model import Rule
from tests.conftest import write_rule


def _rule(rid: str, rtype: str, title: str) -> Rule:
    return Rule(id=rid, type=rtype, fm={"id": rid, "type": rtype, "status": "active"},
                body=f"**Rule:** {title}", path=Path("x"), layer="project")


def test_no_budget_or_fits_returns_everything():
    rules = [_rule("a", "rule", "x"), _rule("b", "task", "y")]
    assert pack.select(rules, 0) == rules
    assert pack.select(rules, 10_000) == rules


def test_knapsack_prefers_high_value_under_budget():
    # Equal-cost lines; importance should drive the pick when only some fit.
    inv = _rule("inv-one", "invariant", "must hold")        # weight 5
    task = _rule("task-one", "task", "do it")               # weight 1
    rules = [task, inv]
    budget = pack.line_tokens(inv)                          # room for exactly one
    picked = pack.select(rules, budget)
    assert picked == [inv]
    assert sum(pack.line_tokens(r) for r in picked) <= budget


def test_select_is_optimal_not_greedy():
    # Greedy-by-ratio would fail this; the DP must find the optimal value.
    a = _rule("aa", "task", "a")        # w≈? v=1
    b = _rule("bb", "invariant", "b")   # v=5
    c = _rule("cc", "invariant", "c")   # v=5
    rules = [a, b, c]
    budget = pack.line_tokens(b) + pack.line_tokens(c)
    picked = pack.select(rules, budget)
    assert set(r.id for r in picked) == {"bb", "cc"}        # both invariants, drop task


def test_context_respects_budget(project):
    for i in range(6):
        write_rule(project, f"r{i}",
                   f"---\nid: r{i}\ntype: {'invariant' if i < 2 else 'task'}\n"
                   f"status: active\n---\n**Rule:** entry number {i} with some text.\n")
    cfg = project / ".fux" / "config.toml"
    cfg.write_text(cfg.read_text().replace("context_budget_tokens = 0",
                                           "context_budget_tokens = 26"))
    out = context.run(project)
    assert "**r0**" in out and "**r1**" in out              # both invariants kept
    assert sum(f"**r{i}**" in out for i in range(6)) < 6     # budget dropped some tasks
