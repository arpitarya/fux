"""Render `type: narrative` entries to a browsable view — `NARRATIVE.md` (§17.15).

Delivers the plan §11 promise that long-form prose (the WHAT/WHY/HOW + architecture
docs Fux absorbs) is "rendered to a browsable view". A single generated document:
a table of contents over the narrative entries, then each entry's body inline —
written by `fux build` and linked from `fux serve`. `$0`.
"""
from __future__ import annotations

from fux.model import RuleSet


def render(rs: RuleSet) -> str:
    items = sorted((r for r in rs.active() if r.type == "narrative"), key=lambda r: r.id)
    if not items:
        return ""
    lines = ["# Fux narrative", "",
             f"_{len(items)} narrative entr{'y' if len(items) == 1 else 'ies'} — "
             "the long-form prose absorbed into the substrate (plan §11)._", "",
             "## Contents", ""]
    lines += [f"- [{r.title}](#{r.id})" for r in items]
    lines.append("")
    for r in items:
        lines.append(f"## {r.title}")
        lines.append(f'<a id="{r.id}"></a>')
        meta = [f"`{r.id}`", r.domain]
        if r.layer != "project":
            meta.append(r.layer)
        if r.code_refs:
            meta.append("code: " + ", ".join(r.code_refs))
        lines.append("_" + " · ".join(meta) + "_")
        lines.append("")
        lines.append(r.body.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
