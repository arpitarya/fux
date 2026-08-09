"""The critique→act loop — deterministic core + a judge SEAM ($0, NO model import; plan §7c/§7d).

`critique()` gathers the principles relevant to a proposed change, runs the DETERMINISTIC
pass FIRST (a hard-invariant fail always blocks, no judge consulted), then routes only
`judgment` principles to a `judge` callable — the host agent (default, $0) or the opt-in
`[critic]` backend. Fux imports no model here; the deterministic/judgment split
(fux/critic.py) keeps deterministic principles away from the seam. **Advisory-first (§7d):**
judgment fails are *suggestions* that do NOT block until a repo escalates them via
`critic_block_judgment` (`true`, or a list of ids); deterministic fails always block.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fux import config, critic, paths, recall, verify
from fux.model import Rule


@dataclass
class Verdict:
    principle: str             # rule id
    status: str                # "pass" | "fail" | "needs-judgment"
    rationale: str = ""
    advisory: bool = False     # judgment fail that suggests, not blocks (advisory-first, F1)


@dataclass
class CriticResult:
    proposal: str
    verdicts: list[Verdict]

    @property
    def blocked(self) -> bool:
        """Only NON-advisory fails block: every deterministic fail, plus any judgment fail on
        a principle the repo has escalated via `critic_block_judgment`. Advisory fails suggest."""
        return any(v.status == "fail" and not v.advisory for v in self.verdicts)

    @property
    def suggestions(self) -> list[Verdict]:
        """Advisory judgment fails — surfaced as suggestions, do not fail the gate (F1)."""
        return [v for v in self.verdicts if v.status == "fail" and v.advisory]

    @property
    def pending(self) -> list[Verdict]:
        return [v for v in self.verdicts if v.status == "needs-judgment"]


Judge = Callable[[str, Rule], Verdict]


def _escalated(cfg: dict) -> Callable[[str], bool]:
    """Return a predicate: is this judgment principle id escalated to blocking? Driven by
    `critic_block_judgment` — `true` (all judgment principles block), a list of ids, or
    falsy/`false` (the advisory-first default: none block)."""
    raw = cfg.get("critic_block_judgment", False)
    if raw is True:
        return lambda _id: True
    if isinstance(raw, (list, tuple, set)):
        ids = {str(x) for x in raw}
        return lambda _id: _id in ids
    return lambda _id: False


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
    blocks; judge not consulted) → each judgment principle to `judge`, else `needs-judgment`.

    Judgment verdicts are *advisory by default* (F1): a judgment `fail` is marked advisory
    unless the repo has escalated that principle via `critic_block_judgment`. Deterministic
    verdicts are never advisory — they always block."""
    cfg = config.load(paths.Footprint(root).config)
    escalated = _escalated(cfg)
    principles = gather(root, proposal)
    verdicts = deterministic_pass(root, principles)
    for r in critic.for_ai(principles):
        v = judge(proposal, r) if judge else \
            Verdict(r.id, "needs-judgment", "host-agent self-critique required")
        v.advisory = not escalated(r.id)        # advisory-first: judgment suggests unless trusted
        verdicts.append(v)
    return CriticResult(proposal, verdicts)


def record(root: Path, result: CriticResult) -> Path:
    """Append verdicts + applied principle ids to .fux/out/critic.jsonl (audit trail, $0, no clock)."""
    p = paths.Footprint(root).out_file("critic.jsonl")
    line = json.dumps({"proposal": result.proposal,
                       "verdicts": [v.__dict__ for v in result.verdicts]}, sort_keys=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return p
