"""Critic routing — the deterministic/judgment split as code ($0, NO LLM; plan §3, §7c).

A principle carries `enforcement` (plan §6): `deterministic` ones are decided by
check:/seal/matcher and may **never** reach the AI critic; `judgment` ones are decided by
AI self-critique and are **never** run as a deterministic check. This module is the
*router* that guarantees the split structurally — `for_ai` and `for_deterministic` are
disjoint partitions. The AI pass itself (the `[critic]` extra) lands in Phase 5 and must
consume ONLY `for_ai(...)`. No model is imported here or anywhere it can reach.
"""
from __future__ import annotations

from fux.findings import Finding
from fux.model import Rule

_NORMATIVE = {"invariant", "regulatory"}


def is_principle(r: Rule) -> bool:
    return bool(r.fm.get("principle"))


def for_ai(rules: list[Rule]) -> list[Rule]:
    """Judgment principles only — a `deterministic` principle can NEVER reach the AI pass."""
    return [r for r in rules if is_principle(r) and r.fm.get("enforcement") == "judgment"]


def for_deterministic(rules: list[Rule]) -> list[Rule]:
    """Deterministic principles only — a `judgment` principle is never run as a deterministic
    check (so it cannot be faked as deterministic), regardless of any stray `check:`."""
    return [r for r in rules if is_principle(r) and r.fm.get("enforcement") == "deterministic"]


def untagged_candidates(rules: list[Rule]) -> list[Finding]:
    """Advisory: project-layer active rules that look like principles (a `check:` or a
    normative type) but carry no `principle` — so backfill is *guided*, never auto-guessed.
    Whether a candidate is deterministic or judgment is always a human/debate call."""
    out: list[Finding] = []
    for r in rules:
        if r.layer != "project" or r.fm.get("principle") or r.status != "active":
            continue
        if r.fm.get("check") or r.type in _NORMATIVE:
            out.append(Finding("untagged-candidate", r.id,
                               "looks like a principle (has a check:/normative type) but is "
                               "untagged — add `principle:` + `enforcement: deterministic|judgment`"))
    return out
