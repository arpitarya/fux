"""Semantic-drift scoped edit prompt (plan §8 auto-fix split).

When a rule's governed code changed, mechanical fixes can't know if the *prose*
is still right. This builds the tightly-scoped, in-session prompt the plan calls
for — the rule, its refs, and the actual git diff — so Claude can update the body.
No background LLM spend: it rides the session already open.
"""
from __future__ import annotations

from pathlib import Path

from fux import gitutil
from fux.model import Rule


def scoped_prompt(rule: Rule, root: Path) -> str:
    since = str(rule.fm.get("updated") or rule.fm.get("created") or "")
    refs = [ref.split("#")[0].rstrip("/") for ref in rule.code_refs]
    diffs = []
    for rel in refs:
        d = gitutil.diff_since(root / rel, since, root)
        if d:
            diffs.append(f"--- {rel} ---\n{d}")
    body = "\n\n".join(diffs) or "(no diff available)"
    return (f"⚑ Fux semantic-drift — rule [{rule.id}] governs {', '.join(refs)}, "
            f"which changed since the rule's updated={since}. Review the diff below "
            f"and edit the rule body if the logic changed (then run `fux check`):\n{body}")
