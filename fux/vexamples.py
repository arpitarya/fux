"""Run a rule's structured examples against its `check:` (plan §10.1).

Examples whose ``given`` is a JSON object are evaluated; natural-language examples
are skipped (never a false fail). Returns (rule_id, status, detail) tuples so this
stays decoupled from verify's VResult.
"""
from __future__ import annotations

import json

from fux.model import Rule


def as_json(val):
    if not isinstance(val, str):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, ValueError):
        return None


def run_examples(rule: Rule, safe: dict) -> list[tuple[str, str, str]]:
    check = rule.fm.get("check")
    out: list[tuple[str, str, str]] = []
    for i, ex in enumerate(rule.fm.get("examples") or [], 1):
        given = as_json(ex.get("given"))
        if not isinstance(given, dict) or not check:
            continue
        rid = f"{rule.id}[ex{i}]"
        try:
            got = eval(str(check), {"__builtins__": {}}, {**safe, **given})
        except Exception as exc:  # noqa: BLE001
            out.append((rid, "fail", f"raised: {exc}"))
            continue
        want = as_json(ex.get("expect"))
        ok = (got == want) if want is not None else bool(got)
        out.append((rid, "pass" if ok else "fail",
                    "" if ok else f"got {got!r}, want {want!r}"))
    return out
