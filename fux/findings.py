"""Finding — one issue surfaced by `fux check` (plan §8, §10)."""
from __future__ import annotations

from dataclasses import dataclass

# Severity ordering drives strict-mode blocking and DRIFT.md grouping.
KINDS = ["tampered", "schema", "dead-ref", "stale", "plan-drift", "conflict",
         "invariant", "memory-stale", "unsealed", "extractor-drift"]
# Kinds that hard-block in `strict` mode (plan §8 strictness table). `tampered` is
# special-cased in blocking() to block in ANY mode (constitution layer, plan §6).
BLOCKING = {"tampered", "schema", "dead-ref", "invariant", "conflict"}


@dataclass
class Finding:
    kind: str           # one of KINDS
    rule_id: str
    message: str
    fixable: bool = False   # True if a mechanical $0 auto-fix exists (fix mode)
    tier: str = "standard"  # governing rule's tier (constitution layer, plan §6)

    def line(self) -> str:
        flag = " [auto-fixable]" if self.fixable else ""
        return f"[{self.kind}] {self.rule_id}: {self.message}{flag}"


def blocking(findings: list[Finding], mode: str = "strict") -> list[Finding]:
    """Findings that block, by tier (constitution layer, plan §6):

    `tampered` → ALWAYS (any tier/mode — a deleted rule has no tier to stamp);
    constitutional → ANY finding, regardless of `mode` (the thin apex; this also
    makes `unsealed` block for constitutional rules); standard → kind-based, but
    only under `strict`; advisory → never. `mode` defaults to `strict` so callers
    already gated on strict keep their exact semantics.
    """
    out: list[Finding] = []
    for f in findings:
        if f.kind == "tampered" or f.tier == "constitutional":
            out.append(f)
        elif f.tier == "advisory":
            continue
        elif f.kind in BLOCKING and mode == "strict":
            out.append(f)
    return out
