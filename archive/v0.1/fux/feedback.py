"""`fux feedback` — record + summarise on-the-fly generation outcomes (§18.4, $0).

The brain's learning loop: every Orff compose attempt (valid / rejected / repaired)
is appended as a JSON line, and `fux feedback` reports the acceptance rate and the
most common rejection reasons — so a recurring validator failure becomes a signal to
add a component, a prop, or a contract rule. Deterministic; no LLM, no memory writes.
"""
from __future__ import annotations

import datetime as _dt
import json
from collections import Counter
from pathlib import Path

from fux import paths

_FIELDS = ("prompt", "valid", "errors", "attempts", "provider", "model")


def _file(root: Path) -> Path:
    d = paths.Footprint(root).base / "capture"
    d.mkdir(parents=True, exist_ok=True)
    return d / "feedback.jsonl"


def record(root: Path, data: dict) -> dict:
    rec = {
        "ts": _dt.datetime.now().isoformat(timespec="seconds"),
        "prompt": str(data.get("prompt", ""))[:200],
        "valid": bool(data.get("valid")),
        "errors": list(data.get("errors") or []),
        "attempts": int(data.get("attempts", 1)),
        "provider": data.get("provider"),
        "model": data.get("model"),
    }
    with _file(root).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def load(root: Path) -> list[dict]:
    f = _file(root)
    return [json.loads(x) for x in f.read_text().splitlines() if x.strip()] if f.exists() else []


def _reason(err: str) -> str:
    for key in ("unknown component", "not on", "missing required prop",
                "data hook", "takes no children", "did not return"):
        if key in err:
            return key
    return err[:40]


def render(rows: list[dict]) -> str:
    if not rows:
        return "fux feedback: no generation outcomes recorded yet."
    ok = sum(1 for r in rows if r["valid"])
    first_try = sum(1 for r in rows if r["valid"] and r["attempts"] == 1)
    reasons = Counter(_reason(e) for r in rows if not r["valid"] for e in r["errors"])
    out = [f"fux feedback — {len(rows)} compose(s): {ok} valid "
           f"({100 * ok // len(rows)}%), {first_try} on first try."]
    if reasons:
        out.append("Top rejection reasons (candidate registry/rule gaps):")
        out += [f"  {n}× {r}" for r, n in reasons.most_common(5)]
    return "\n".join(out)
