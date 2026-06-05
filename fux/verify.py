"""`fux verify` — run invariant `check:` assertions + structured examples ($0, §10.1).

``check:`` is eval'd in a restricted namespace; data comes from ``verify_cmd:``
(a shell cmd printing JSON — the probes/just wiring), ``.fux/verify/<id>.json``,
or ``.fux/out/verify_context.json``. No data → *skip* (never a false fail).
Examples whose ``given`` is JSON are run too. No LLM is ever called.
"""
from __future__ import annotations

import builtins
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

from fux import config, loader, paths, vexamples
from fux.model import Rule

# Restricted, pure builtins for evaluating `check:` expressions (no __builtins__).
_SAFE = {n: getattr(builtins, n) for n in
         "abs sum min max len round all any zip range enumerate sorted map filter "
         "list dict set tuple".split()} | {"math": math}


@dataclass
class VResult:
    rule_id: str
    status: str   # "pass" | "fail" | "skip"
    detail: str = ""


def run(root: Path, fuzz: bool = False) -> list[VResult]:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    out: list[VResult] = []
    for r in rs.rules:
        if r.fm.get("check"):
            out.append(_verify_one(r, root))
        out += [VResult(*t) for t in vexamples.run_examples(r, _SAFE)]
        if fuzz:
            out += [VResult(*t) for t in vexamples.fuzz_examples(r, _SAFE)]
    return out


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
