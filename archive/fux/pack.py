"""Optimal context packing — a budgeted 0/1 knapsack over rules (plan §17.25).

SessionStart injection and recall top-N are heuristics. When `context_budget_tokens`
is set, pick the **provably-optimal** rule subset: maximise total importance while
the INDEX one-liners stay within the budget. A real 0/1 knapsack (dynamic program),
not greedy — `$0`, deterministic, default-off (budget 0 ⇒ inject everything).
"""
from __future__ import annotations

from fux.model import Rule

# Importance by type — the *why*-bearing, code-bound entries outrank scaffolding.
TYPE_WEIGHT = {
    "invariant": 5, "regulatory": 5, "formula": 4, "convention": 4, "edge-case": 4,
    "rule": 3, "glossary": 3, "adr": 3, "runbook": 2, "memory": 2,
    "spec": 2, "task": 1, "narrative": 1,
}


def line_tokens(r: Rule) -> int:
    """Token cost of a rule's INDEX line (~4 chars/token, the savings.py model)."""
    return max(1, round(len(r.summary()) / 4))


def importance(r: Rule) -> float:
    return float(TYPE_WEIGHT.get(r.type, 2))


def select(rules: list[Rule], budget_tokens: int, value_of=importance) -> list[Rule]:
    """The optimal subset whose line tokens sum ≤ budget. Everything, if it fits."""
    items = [(r, line_tokens(r), max(1e-3, value_of(r))) for r in rules]
    if budget_tokens <= 0 or sum(w for _, w, _ in items) <= budget_tokens:
        return list(rules)
    chosen = set(_knapsack(items, budget_tokens))
    return [r for r in rules if id(r) in chosen]            # preserve input order


def _knapsack(items: list[tuple[Rule, int, float]], cap: int) -> list[int]:
    """0/1 knapsack by token weight; returns id()s of the chosen objects."""
    dp = [0.0] * (cap + 1)
    keep = [bytearray(cap + 1) for _ in items]
    for i, (_, w, v) in enumerate(items):
        ki = keep[i]
        for c in range(cap, w - 1, -1):
            if dp[c - w] + v > dp[c]:
                dp[c] = dp[c - w] + v
                ki[c] = 1
    out, c = [], cap
    for i in range(len(items) - 1, -1, -1):
        if keep[i][c]:
            out.append(id(items[i][0]))
            c -= items[i][1]
    return out
