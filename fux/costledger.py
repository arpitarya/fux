"""Cumulative cost ledger — track the savings of *every* lookup ($0, plan §12).

`fux savings` estimates the win for one lookup; this persists the win of **every**
lookup into `.fux/cost.json` (mirroring graphify's `cost.json` name), so the project
can quote a real *lifetime* number — "Fux has saved N tokens across M lookups" —
not just a per-call estimate. Opt-in via `cost_tracking`; recorded on each
`fux recall` using the same `savings` token model. Deterministic, no LLM.

`tokens_without` = reading the governed source file(s) for the matched rules;
`tokens_with` = the matched Tier-2 rule(s) only (the realistic later-lookup cost,
since the Tier-1 INDEX is injected once per session). `saved = without − with`.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from fux import paths
from fux.model import Rule

_RECENT_CAP = 50  # keep the last N per-lookup entries; cumulative totals are exact


def _file(root: Path) -> Path:
    return paths.Footprint(root).base / "cost.json"


def _empty() -> dict:
    return {"lookups": 0, "tokens_without": 0, "tokens_with": 0, "tokens_saved": 0,
            "first": None, "last": None, "recent": []}


def load(root: Path) -> dict:
    f = _file(root)
    if not f.exists():
        return _empty()
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return {**_empty(), **data}
    except (OSError, ValueError):
        return _empty()


def reset(root: Path) -> None:
    f = _file(root)
    try:
        f.unlink()
    except OSError:
        pass


def record(root: Path, query: str, matched: list[Rule],
           today: _dt.date | None = None) -> dict:
    """Append one lookup's measured cost to the ledger; return the updated ledger.

    Best-effort — never raises (recording must not break a read path).
    """
    from fux import savings   # lazy: avoids a recall ↔ savings import cycle

    # Only *code-bound* matches are a real savings situation — same restriction as
    # `fux savings` ("topics"). A matched narrative/glossary with no governed file
    # would otherwise charge its whole body to `with` against a `without` of 0,
    # making "savings" negative and meaningless.
    with_tok = without_tok = 0
    files: set[str] = set()
    for r in matched:
        gov = 0
        for ref in r.code_refs:
            rel = savings._ref_file(ref)
            if rel and rel not in files and (root / rel).is_file():
                files.add(rel)
                gov += savings._read_tokens(root / rel)
        if gov > 0:                       # this rule governs real code → countable
            without_tok += gov
            with_tok += savings.rule_tokens(r)
    saved = without_tok - with_tok
    day = (today or _dt.date.today()).isoformat()

    led = load(root)
    led["lookups"] += 1
    led["tokens_without"] += without_tok
    led["tokens_with"] += with_tok
    led["tokens_saved"] += saved
    led["first"] = led["first"] or day
    led["last"] = day
    led["recent"] = (led.get("recent", []) + [{
        "date": day, "query": query[:120],
        "served": [r.id for r in matched],
        "without": without_tok, "with": with_tok, "saved": saved,
    }])[-_RECENT_CAP:]

    try:
        f = _file(root)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(led, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    return led


def overall_ratio(led: dict) -> float:
    w = led.get("tokens_with", 0)
    return (led.get("tokens_without", 0) / w) if w else 0.0


def render_summary(led: dict) -> str:
    if not led.get("lookups"):
        return ""
    span = led.get("first") or "?"
    ratio = overall_ratio(led)
    x = f"{ratio:.1f}×" if ratio else "—"
    return "\n".join([
        "",
        f"Cumulative (tracked across {led['lookups']} lookup(s) since {span})",
        f"  tokens without Fux:  {led['tokens_without']:>10,} tok",
        f"  tokens with Fux:     {led['tokens_with']:>10,} tok",
        f"  tokens saved:        {led['tokens_saved']:>10,} tok   → {x} overall",
    ])
