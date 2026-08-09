"""Memory governance — TTL decay for `type: memory` only (plan §17.3).

Borrowed from the agent-memory field (TTL/forgetting), but scoped tightly: *rules*
never decay (they're authored, code-linked, drift-checked). A `memory` entry,
however, is a cross-session observation that can go stale — so after
`memory_ttl_days` untouched it is flagged (`fux check`/`stats`/`gate`) and excluded
from `fux context` (the SessionStart injection), while staying on disk for history.
Deterministic and `$0`; supersession still rides the existing `supersedes:` edge.
"""
from __future__ import annotations

import datetime as _dt

from fux.model import Rule


def _age_days(rule: Rule, today: _dt.date) -> int | None:
    raw = str(rule.fm.get("updated") or rule.fm.get("created") or "")
    try:
        return (today - _dt.date.fromisoformat(raw[:10])).days
    except ValueError:
        return None


def ttl(cfg: dict) -> int:
    try:
        return int(cfg.get("memory_ttl_days", 180) or 0)
    except (TypeError, ValueError):
        return 0


def is_decayed(rule: Rule, cfg: dict, today: _dt.date | None = None,
               last_served: _dt.date | None = None) -> bool:
    if rule.type != "memory":
        return False
    days = ttl(cfg)
    if days <= 0:
        return False
    today = today or _dt.date.today()
    # Usage-weighted (plan §17.20c): a memory *served* within the TTL window is
    # demonstrably still live, so it stays even if its `updated` date is old.
    if last_served is not None and (today - last_served).days <= days:
        return False
    age = _age_days(rule, today)
    return age is not None and age > days


def for_context(rules: list[Rule], cfg: dict, today: _dt.date | None = None,
                served: dict[str, _dt.date] | None = None) -> list[Rule]:
    """Drop decayed memory entries from the context-injection set.

    ``served`` ({id: last-served date}, from ``usage``) keeps hot memories alive.
    """
    served = served or {}
    return [r for r in rules if not is_decayed(r, cfg, today, served.get(r.id))]
