"""Finding — one issue surfaced by `fux check` (plan §8, §10)."""
from __future__ import annotations

from dataclasses import dataclass

# Severity ordering drives strict-mode blocking and DRIFT.md grouping.
KINDS = ["schema", "dead-ref", "stale", "plan-drift", "conflict", "invariant",
         "memory-stale"]
# Kinds that hard-block in `strict` mode (plan §8 strictness table).
BLOCKING = {"schema", "dead-ref", "invariant", "conflict"}


@dataclass
class Finding:
    kind: str           # one of KINDS
    rule_id: str
    message: str
    fixable: bool = False   # True if a mechanical $0 auto-fix exists (fix mode)

    def line(self) -> str:
        flag = " [auto-fixable]" if self.fixable else ""
        return f"[{self.kind}] {self.rule_id}: {self.message}{flag}"


def blocking(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.kind in BLOCKING]
