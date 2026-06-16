"""The critique→act loop — deterministic core + a judge SEAM ($0, NO model import; plan §7c).

`critique()` gathers the principles relevant to a proposed change, runs the DETERMINISTIC
pass FIRST (a hard-invariant fail blocks, no judge consulted), then routes only `judgment`
principles to a `judge` callable — supplied by the host agent (default, $0) or the opt-in
`[critic]` backend. Fux imports no model here; `judge` is the only AI seam, and the
deterministic/judgment split (fux/critic.py) keeps deterministic principles away from it.
The bounded revise + escalation loop is the caller's (the `critic` skill), not Fux's.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fux import critic, paths, recall, verify
from fux.model import Rule


@dataclass
class Verdict:
    principle: str             # rule id
    status: str                # "pass" | "fail" | "needs-judgment"
    rationale: str = ""


@dataclass
class CriticResult:
    proposal: str
    verdicts: list[Verdict]

    @property
    def blocked(self) -> bool:
        return any(v.status == "fail" for v in self.verdicts)

    @property
    def pending(self) -> list[Verdict]:
        return [v for v in self.verdicts if v.status == "needs-judgment"]


Judge = Callable[[str, Rule], Verdict]


def gather(root: Path, proposal: str, top: int = 6) -> list[Rule]:
    """Recall the principles (rules carrying a `principle`) most relevant to a change ($0)."""
    return [r for r, _ in recall.run(root, proposal, top=top) if critic.is_principle(r)]


def deterministic_pass(root: Path, principles: list[Rule]) -> list[Verdict]:
    """Verify `for_deterministic` principles via check:/examples → verdicts. NO LLM; runs first."""
    det = {r.id for r in critic.for_deterministic(principles)}
    if not det:
        return []
    return [Verdict(v.rule_id, "pass" if v.status == "pass" else "fail", v.detail)
            for v in verify.run(root) if v.rule_id in det and v.status != "skip"]


def critique(root: Path, proposal: str, judge: Judge | None = None) -> CriticResult:
    """One critique pass at the action boundary: gather → deterministic pass FIRST (a fail
    blocks; judge not consulted) → each judgment principle to `judge`, else `needs-judgment`."""
    principles = gather(root, proposal)
    verdicts = deterministic_pass(root, principles)
    for r in critic.for_ai(principles):
        verdicts.append(judge(proposal, r) if judge else
                        Verdict(r.id, "needs-judgment", "host-agent self-critique required"))
    return CriticResult(proposal, verdicts)


def record(root: Path, result: CriticResult) -> Path:
    """Append verdicts + applied principle ids to .fux/out/critic.jsonl (audit trail, $0, no clock)."""
    p = paths.Footprint(root).out_file("critic.jsonl")
    line = json.dumps({"proposal": result.proposal,
                       "verdicts": [v.__dict__ for v in result.verdicts]}, sort_keys=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return p
