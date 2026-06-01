"""Minimal schema validator — $0, stdlib-only (no jsonschema dep)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from fux import paths


@lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads(paths.schema_path().read_text())


def validate(fm: dict) -> list[str]:
    """Return a list of human-readable validation errors ([] if valid)."""
    s = _schema()
    errs: list[str] = []
    for req in s.get("required", []):
        if req not in fm or fm[req] in (None, ""):
            errs.append(f"missing required field: {req}")
    for key, val in fm.items():
        spec = s["properties"].get(key)
        if spec is None:
            continue
        errs += _check(key, val, spec)
    return errs


def _check(key: str, val, spec: dict) -> list[str]:
    if val is None:
        return []
    t = spec.get("type")
    if t == "string" and not isinstance(val, str):
        return [f"{key}: expected string, got {type(val).__name__}"]
    if t == "array" and not isinstance(val, list):
        return [f"{key}: expected list"]
    if t == "object" and not isinstance(val, dict):
        return [f"{key}: expected mapping"]
    errs: list[str] = []
    if "enum" in spec and val not in spec["enum"]:
        errs.append(f"{key}: '{val}' not in {spec['enum']}")
    if "pattern" in spec and isinstance(val, str) and not re.match(spec["pattern"], val):
        errs.append(f"{key}: '{val}' does not match {spec['pattern']}")
    if t == "array" and isinstance(val, list) and "items" in spec:
        for item in val:
            errs += _check(f"{key}[]", item, spec["items"])
    if t == "object" and isinstance(val, dict):
        for req in spec.get("required", []):
            if req not in val:
                errs.append(f"{key}: missing '{req}'")
    return errs
