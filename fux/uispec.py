"""`fux validate-spec` — validate a declarative UISpec against the registry ($0, §18.3.3).

The mount-time guardrail for Orff's on-the-fly generation: a generated UI may only
compose **registry** components, with **declared** props, bound to **known** data
hooks. Anything else is rejected before it can render. This is what makes runtime
generation safe — the model emits a declarative tree, never code; the frontend
renders it from a whitelist. Pure structural validation; no code execution, no LLM.

UISpec node:  {"component": "Card", "props": {...}, "data": "useHoldings",
               "children": [ <node>, {"text": "literal"} ]}
"""
from __future__ import annotations

import json
from pathlib import Path

from fux import components


def validate(reg: dict, spec: object) -> list[str]:
    """Return a list of violations; empty means the spec is safe to mount."""
    by_name = {c["name"]: c for c in reg["components"]}
    hooks = {h["name"] for h in reg["hooks"]}
    errs: list[str] = []
    _node(spec, "$", by_name, hooks, errs)
    return errs


def _node(node: object, path: str, by_name: dict, hooks: set, errs: list[str]) -> None:
    if isinstance(node, dict) and "text" in node and "component" not in node:
        return                                       # literal text leaf
    if not isinstance(node, dict) or "component" not in node:
        errs.append(f"{path}: node needs a 'component' or 'text'")
        return
    name = node["component"]
    comp = by_name.get(name)
    if comp is None:
        errs.append(f"{path}: unknown component '{name}' — not in the registry")
        return
    prop_names = {p["name"] for p in comp["props"]}
    required = {p["name"] for p in comp["props"] if not p["optional"]} - {"children", "className"}
    here = f"{path}.{name}"
    props = node.get("props") or {}
    errs += [f"{here}: prop '{k}' not on {name}" for k in props if k not in prop_names]
    errs += [f"{here}: missing required prop '{r}'" for r in sorted(required - set(props))]
    if (data := node.get("data")) and data not in hooks:
        errs.append(f"{here}: data hook '{data}' not in the registry")
    children = node.get("children") or []
    if children and "children" not in prop_names:
        errs.append(f"{here}: {name} takes no children")
    for i, ch in enumerate(children):
        _node(ch, f"{here}[{i}]", by_name, hooks, errs)


def run(root: Path, spec_path: Path) -> tuple[bool, list[str]]:
    reg = components.registry(root)
    errs = validate(reg, json.loads(spec_path.read_text(encoding="utf-8")))
    return not errs, errs


def render(ok: bool, errs: list[str]) -> str:
    if ok:
        return "✔ spec valid — every component, prop, and data hook is in the registry\n"
    return "✘ spec rejected:\n" + "\n".join(f"  - {e}" for e in errs) + "\n"
