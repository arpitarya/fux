"""`fux why <id>` and `fux refs <file>` — explain & reverse-lookup ($0, plan §10.4)."""
from __future__ import annotations

from pathlib import Path

from fux import config, loader, paths
from fux.model import Rule


def why(root: Path, rule_id: str) -> Rule | None:
    cfg = config.load(paths.Footprint(root).config)
    return loader.resolve(root, cfg).by_id().get(rule_id)


def refs(root: Path, file_rel: str) -> list[Rule]:
    """Which rules govern this file? Matches by code_refs path prefix."""
    cfg = config.load(paths.Footprint(root).config)
    target = file_rel.replace("\\", "/").lstrip("./")
    out: list[Rule] = []
    for r in loader.resolve(root, cfg).rules:
        for ref in r.code_refs:
            if ref.split("#")[0].rstrip("/") == target:
                out.append(r)
                break
    return out


def render_why(r: Rule) -> str:
    """Human/Claude-facing explanation: rule + rationale + linked code."""
    head = [f"# {r.id} ({r.type}) · {r.domain} · {r.status} · [{r.layer}]", ""]
    if r.code_refs:
        head.append("**Governs:** " + ", ".join(r.code_refs))
    if r.related:
        head.append("**Related:** " + ", ".join(r.related))
    edges = r.edges()
    if edges:
        head.append("**Edges:** " + "; ".join(f"{k}→{v}" for k, v in edges.items() if v))
    if r.fm.get("check"):
        head.append(f"**Invariant:** `{r.fm['check']}`")
    return "\n".join(head) + "\n\n" + r.body.strip() + "\n"
