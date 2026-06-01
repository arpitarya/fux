"""`fux verify` — run invariant `check:` assertions ($0, plan §10.1).

A rule's ``check:`` is evaluated in a restricted namespace. Data comes from (in
order): the rule's optional ``verify_cmd:`` (a shell command printing JSON — wires
into the probes/just culture), ``.fux/verify/<id>.json``, then
``.fux/out/verify_context.json``. No data → the check is reported as *skipped*,
never failed. No LLM is ever called.
"""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

from fux import config, loader, paths
from fux.model import Rule

_SAFE = {"abs": abs, "sum": sum, "min": min, "max": max, "len": len,
         "round": round, "all": all, "any": any, "math": math}


@dataclass
class VResult:
    rule_id: str
    status: str   # "pass" | "fail" | "skip"
    detail: str = ""


def run(root: Path) -> list[VResult]:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    return [_verify_one(r, root) for r in rs.rules if r.fm.get("check")]


def _verify_one(r: Rule, root: Path) -> VResult:
    ctx = _context(r, root)
    if ctx is None:
        return VResult(r.id, "skip", "no verification data")
    try:
        ok = bool(eval(str(r.fm["check"]), {"__builtins__": {}}, {**_SAFE, **ctx}))
    except Exception as exc:  # noqa: BLE001 — surface any eval error as a fail
        return VResult(r.id, "fail", f"check raised: {exc}")
    return VResult(r.id, "pass" if ok else "fail", "" if ok else f"check false: {r.fm['check']}")


def _context(r: Rule, root: Path) -> dict | None:
    cmd = r.fm.get("verify_cmd")
    if cmd:
        try:
            out = subprocess.run(cmd, cwd=root, shell=True, capture_output=True,
                                text=True, timeout=60)
            if out.returncode == 0 and out.stdout.strip():
                return json.loads(out.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            return None
        return None
    for candidate in (root / ".fux" / "verify" / f"{r.id}.json",
                      root / ".fux" / "out" / "verify_context.json"):
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None
