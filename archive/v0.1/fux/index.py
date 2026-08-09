"""Derived index views: INDEX.md (compact TOC) + rules.json (lookup). plan §7."""
from __future__ import annotations

import json

from fux.model import Rule, RuleSet


def render_index(rs: RuleSet) -> str:
    """A compact, Tier-1 table of contents — ~1 line per rule (plan §4)."""
    active = [r for r in rs.active() if r.type not in ("narrative",)]
    by_domain: dict[str, list[Rule]] = {}
    for r in active:
        by_domain.setdefault(r.domain, []).append(r)
    lines = ["# Fux INDEX", "",
             f"_{len(active)} active entries across {len(by_domain)} domains. "
             "Read this first; open a rule (`fux why <id>`) only when relevant._", ""]
    for domain in sorted(by_domain):
        lines.append(f"## {domain}")
        for r in sorted(by_domain[domain], key=lambda x: x.id):
            tag = "" if r.layer == "project" else f" _[{r.layer}]_"
            lines.append(f"- **{r.id}** ({r.type}) — {r.title}{tag}")
        lines.append("")
    deprecated = [r for r in rs.rules if not r.is_active]
    if deprecated:
        lines.append("## deprecated (excluded from context)")
        lines += [f"- ~~{r.id}~~ — {r.title}" for r in sorted(deprecated, key=lambda x: x.id)]
    return "\n".join(lines).rstrip() + "\n"


def render_json(rs: RuleSet) -> str:
    """Machine lookup — lets a probe/backend assert invariants (plan §7)."""
    payload = {"version": 1, "count": len(rs.rules),
               "rules": [_entry(r) for r in rs.rules]}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _entry(r: Rule) -> dict:
    return {
        "id": r.id, "type": r.type, "domain": r.domain, "status": r.status,
        "title": r.title, "layer": r.layer, "path": str(r.path),
        "code_refs": r.code_refs, "related": r.related, "edges": r.edges(),
        "check": r.fm.get("check"), "examples": r.fm.get("examples") or [],
        "created": r.fm.get("created"), "updated": r.fm.get("updated"),
    }
