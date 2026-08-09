"""`fux why <id>` and `fux refs <file>` — explain & reverse-lookup ($0, plan §10.4)."""
from __future__ import annotations

from pathlib import Path

from fux import config, gitutil, loader, paths
from fux.model import Rule


def why(root: Path, rule_id: str) -> Rule | None:
    cfg = config.load(paths.Footprint(root).config)
    r = loader.resolve(root, cfg).by_id().get(rule_id)
    if r is not None and cfg.get("usage_tracking"):
        from fux import usage          # opening a rule is a genuine "use" (§17.20c)
        usage.record(root, [rule_id])
    return r


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


def render_history(root: Path, r: Rule) -> str:
    """Knowledge archaeology: how this rule's *reasoning* evolved (plan §17.24).

    Git-blame for the *why*, not the lines — only possible because the rationale is
    a first-class versioned object. Reversed decisions surface via `supersedes:`.
    """
    out = [f"# {r.id} — history", ""]
    sup = r.edges().get("supersedes") or []
    if sup:
        out.append("**Supersedes:** " + ", ".join(sup) + "  _(a reversed/replaced decision)_")
        out.append("")
    if not gitutil.is_repo(root):
        return "\n".join(out + ["_(not a git repo — no recorded history)_"]) + "\n"
    rows = gitutil.file_history(r.path, root)
    if not rows:
        return "\n".join(out + ["_(not yet committed — no recorded history)_"]) + "\n"
    out += [f"- `{date}` {subject} ({sha})" for date, sha, subject in rows]
    return "\n".join(out) + "\n"
