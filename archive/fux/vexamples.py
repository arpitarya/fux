"""Run a rule's structured examples against its `check:` (plan §10.1).

An example's ``given`` is turned into name→value bindings, executed against the
rule's ``check:`` in the same restricted namespace as `fux verify`. Three input
shapes are accepted, all $0 and deterministic:

* a JSON object — ``{"holdings": [...], "total": 2000}``;
* an inline ``key=value`` / ``key: value`` pair string — ``"qty=100, pct=2"``,
  with numbers/booleans coerced;
* a mapping already parsed by the frontmatter loader.

Prose that fits none of these is skipped (never a false fail), preserving the
"no false failure" guarantee. ``expect`` is coerced the same way so bare numbers
like ``"2000"`` or ``"₹2,000"`` compare against a numeric ``check`` result.
"""
from __future__ import annotations

import json
import re

from fux.model import Rule

_PAIR = re.compile(r"^\s*([A-Za-z_]\w*)\s*[:=]\s*(.+?)\s*$")


def as_json(val):
    if not isinstance(val, str):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, ValueError):
        return None


def _coerce(token: str):
    """Best-effort coercion for a bare value token; falls back to the string."""
    token = token.strip()
    j = as_json(token)                       # lists, objects, JSON numbers/bools
    if j is not None and not isinstance(j, str):
        return j
    token = token.strip("\"'")
    if token.lower() in ("true", "false"):
        return token.lower() == "true"
    num = re.sub(r"^[^\d+\-.]+", "", token.replace(",", ""))  # drop leading currency
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return token


def as_bindings(val):
    """Return a {name: value} dict from ``given``, or None if not interpretable."""
    parsed = as_json(val)
    if isinstance(parsed, dict):
        return parsed
    if not isinstance(val, str):
        return None
    pairs = {}
    for part in _split_pairs(val):
        m = _PAIR.match(part)
        if not m:
            return None
        pairs[m.group(1)] = _coerce(m.group(2))
    return pairs or None


def _split_pairs(text: str) -> list[str]:
    """Split on commas/semicolons not inside brackets, so lists survive."""
    out, depth, cur = [], 0, []
    for ch in text:
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
        if ch in ",;" and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return [p for p in out if p.strip()]


def _expected(val):
    """Coerce ``expect`` to JSON, then to a scalar, else leave as the raw string."""
    parsed = as_json(val)
    if parsed is not None:
        return parsed
    return _coerce(val) if isinstance(val, str) else val


# Deterministic boundary set for example fuzzing (no randomness — reproducible).
_BOUNDARIES = (0, -1, 1, 10 ** 9, -(10 ** 9))


def fuzz_examples(rule: Rule, safe: dict) -> list[tuple[str, str, str]]:
    """Perturb each numeric example input to a boundary; report `check:` *crashes*.

    A boundary that merely makes the invariant False is fine (bad input *should*
    violate it). A boundary that makes `check:` raise `ZeroDivisionError` is a real
    robustness gap — an unguarded division (plan §17.20a). Other exception types are
    noisy (a scalar where a list was expected) and deliberately ignored. `$0`.
    """
    check = rule.fm.get("check")
    out: list[tuple[str, str, str]] = []
    for i, ex in enumerate(rule.fm.get("examples") or [], 1):
        given = as_bindings(ex.get("given"))
        if not isinstance(given, dict) or not check:
            continue
        numeric = [k for k, v in given.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        for k in numeric:
            for bv in _BOUNDARIES:
                try:
                    eval(str(check), {"__builtins__": {}}, {**safe, **given, k: bv})
                except ZeroDivisionError:
                    out.append((f"{rule.id}[fuzz {k}={bv}]", "fail",
                                "check divides by zero at the boundary — add a guard"))
                except Exception:  # noqa: BLE001 — only div-by-zero is a clean signal
                    pass
    return out


def run_examples(rule: Rule, safe: dict) -> list[tuple[str, str, str]]:
    check = rule.fm.get("check")
    out: list[tuple[str, str, str]] = []
    for i, ex in enumerate(rule.fm.get("examples") or [], 1):
        given = as_bindings(ex.get("given"))
        if not isinstance(given, dict) or not check:
            continue
        rid = f"{rule.id}[ex{i}]"
        try:
            got = eval(str(check), {"__builtins__": {}}, {**safe, **given})
        except Exception as exc:  # noqa: BLE001
            out.append((rid, "fail", f"raised: {exc}"))
            continue
        want = _expected(ex.get("expect"))
        ok = (got == want) if want is not None else bool(got)
        out.append((rid, "pass" if ok else "fail",
                    "" if ok else f"got {got!r}, want {want!r}"))
    return out
