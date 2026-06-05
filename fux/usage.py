"""Usage tracking — which rules actually get served (plan §17.20c).

A `$0`, opt-in (`usage_tracking`) signal the agent-memory field never captures:
TTL decay is *time*-only, but a memory that keeps getting recalled is clearly still
live, while one never served is a better decay candidate. We record each served id
with a last-seen date in `.fux/usage.json`; `governance` reads it to keep *hot*
memories alive and let *cold* ones decay. Reads are the only side effect, and only
when the flag is on — the default path writes nothing.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from fux import paths


def _file(root: Path) -> Path:
    return paths.Footprint(root).base / "usage.json"


def load(root: Path) -> dict[str, dict]:
    f = _file(root)
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def record(root: Path, ids: list[str], today: _dt.date | None = None) -> None:
    """Bump the served-count + last-seen date for each id. Best-effort, never raises."""
    if not ids:
        return
    day = (today or _dt.date.today()).isoformat()
    data = load(root)
    for rid in ids:
        entry = data.get(rid) or {"count": 0, "last": day}
        entry["count"] = int(entry.get("count", 0)) + 1
        entry["last"] = day
        data[rid] = entry
    try:
        f = _file(root)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass


def last_served(root: Path) -> dict[str, _dt.date]:
    """{id: last-served date} for governance's usage-weighted decay."""
    out: dict[str, _dt.date] = {}
    for rid, entry in load(root).items():
        try:
            out[rid] = _dt.date.fromisoformat(str(entry.get("last"))[:10])
        except (ValueError, TypeError):
            continue
    return out
