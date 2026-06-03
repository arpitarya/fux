"""`fux stats` — one-glance project health, derived from the other $0 commands.

Folds coverage, drift, lint, verify, recall corpus, graph shape, and the savings
multiplier into a single dashboard + a transparent **health score** (0–100). No new
analysis — it composes the existing deterministic signals, so it stays `$0`.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from fux import (check, config, coverage, findings, lint, loader, paths,
                 savings, verify)
from fux.model import RuleSet


@dataclass
class Stats:
    rules: int
    active: int
    deprecated: int
    by_type: dict
    by_domain: dict
    by_layer: dict
    coverage_pct: float
    uncovered: int
    drift: dict          # finding-kind -> count
    blocking: int
    lint: dict           # lint-kind -> count
    verify: dict         # status -> count
    savings_x: float
    graph: dict          # nodes/edges/communities (0 if no graph.json yet)
    score: int = 0
    components: dict = field(default_factory=dict)


def build(root: Path) -> Stats:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    cov = coverage.run(root)
    drift = check.run(root)
    lints = lint.run(root)
    vres = verify.run(root)
    sav = savings.build(root)

    st = Stats(
        rules=len(rs.rules), active=len(rs.active()),
        deprecated=sum(1 for r in rs.rules if not r.is_active),
        by_type=dict(Counter(r.type for r in rs.rules).most_common()),
        by_domain=dict(Counter(r.domain for r in rs.active()).most_common()),
        by_layer=dict(Counter(r.layer for r in rs.rules).most_common()),
        coverage_pct=cov.pct, uncovered=len(cov.uncovered),
        drift=dict(Counter(f.kind for f in drift)),
        blocking=len(findings.blocking(drift)),
        lint=dict(Counter(f.kind for f in lints)),
        verify=dict(Counter(v.status for v in vres)),
        savings_x=round(sav.avg_ratio(), 1),
        graph=_graph_shape(root),
    )
    _score(st, rs)
    return st


def _graph_shape(root: Path) -> dict:
    p = paths.Footprint(root).out / "graph.json"
    if not p.exists():
        return {"nodes": 0, "edges": 0, "communities": 0, "stale": True}
    try:
        g = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"nodes": 0, "edges": 0, "communities": 0, "stale": True}
    return {"nodes": len(g.get("nodes", [])), "edges": len(g.get("edges", [])),
            "communities": g.get("meta", {}).get("communities", 0), "stale": False}


def _score(st: Stats, rs: RuleSet) -> None:
    """Weighted, transparent: coverage 40 · verify 30 · authoring 30, minus drift."""
    passed = st.verify.get("pass", 0)
    failed = st.verify.get("fail", 0)
    verify_pct = 100.0 * passed / (passed + failed) if (passed + failed) else 100.0
    authoring_pct = max(0.0, 100.0 * (1 - sum(st.lint.values()) / max(st.active, 1)))
    penalty = min(30, st.blocking * 5)
    comp = {"coverage": st.coverage_pct, "verify": verify_pct,
            "authoring": authoring_pct, "drift_penalty": penalty}
    raw = 0.4 * comp["coverage"] + 0.3 * comp["verify"] + 0.3 * comp["authoring"] - penalty
    st.score = max(0, min(100, round(raw)))
    st.components = {k: round(v, 1) for k, v in comp.items()}


def _bar(pct: float, width: int = 20) -> str:
    fill = round(pct / 100 * width)
    return "█" * fill + "░" * (width - fill)


def grade(score: int) -> str:
    return "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else \
           "D" if score >= 40 else "F"


def render(st: Stats) -> str:
    L = [f"fux stats — health {st.score}/100  ({grade(st.score)})  {_bar(st.score)}", ""]
    L.append("Score components")
    for k in ("coverage", "verify", "authoring"):
        L.append(f"  {k:<10} {st.components.get(k, 0):>5.0f}   {_bar(st.components.get(k, 0))}")
    if st.components.get("drift_penalty"):
        L.append(f"  drift     −{st.components['drift_penalty']:.0f} (blocking findings)")
    L.append("")

    L.append("Corpus")
    L.append(f"  rules: {st.rules} ({st.active} active, {st.deprecated} deprecated)")
    L.append(f"  types: {_kv(st.by_type)}")
    L.append(f"  domains: {_kv(st.by_domain)}")
    L.append(f"  layers: {_kv(st.by_layer)}")
    L.append("")

    L.append("Signals")
    L.append(f"  coverage:  {st.coverage_pct:.0f}%  ({st.uncovered} important file(s) uncovered)")
    L.append(f"  verify:    {_kv(st.verify) or 'no checks'}")
    L.append(f"  drift:     {_kv(st.drift) or 'none'}   (blocking: {st.blocking})")
    L.append(f"  lint:      {_kv(st.lint) or 'clean'}")
    L.append(f"  savings:   ~{st.savings_x or 0}× cheaper per documented lookup")
    g = st.graph
    shape = "not built yet (run `fux build`)" if g.get("stale") else \
            f"{g['nodes']} nodes · {g['edges']} edges · {g['communities']} communities"
    L.append(f"  graph:     {shape}")
    return "\n".join(L)


def _kv(d: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in d.items())
