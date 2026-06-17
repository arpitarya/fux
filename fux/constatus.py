"""`fux constitution` — the status view: what is constitutional, what each governs, violations.

One screen that collapses the whole apex: every ratified constitutional rule, its ratifier +
debate, what code/domain it governs, and any current blocking findings against it. $0, read-only,
deterministic — reuses the loader + the same `check` the gate runs. No LLM.
"""
from __future__ import annotations

from pathlib import Path

from fux import check, config, loader, paths, provenance
from fux.model import Rule


def _constitutional(rules: list[Rule]) -> list[Rule]:
    return sorted((r for r in rules if str(r.fm.get("tier")) == "constitutional"),
                  key=lambda r: r.id)


def _governs(r: Rule) -> str:
    refs = r.code_refs
    if refs:
        return ", ".join(refs)
    return f"domain: {r.domain}" if r.domain != "general" else "(no code_refs — principle/prose)"


def render(root: Path) -> str:
    cfg = config.load(paths.Footprint(root).config)
    rules = loader.resolve(root, cfg).rules
    con = _constitutional(rules)
    findings = [f for f in check.run(root) if f.tier == "constitutional"]
    by_rule: dict[str, list] = {}
    for f in findings:
        by_rule.setdefault(f.rule_id, []).append(f)

    out = ["fux constitution", ""]
    if not con:
        out.append("  (no constitutional rules — `/fux debate \"<rule>\" --tier constitutional`)")
        return "\n".join(out)

    lock = (root / ".fux" / "constitution.lock")
    out.append(f"  apex: {len(con)} constitutional rule(s)  ·  lock: "
               f"{'present' if lock.exists() else 'MISSING'}  ·  "
               f"{len(findings)} blocking finding(s)")
    out.append("")
    for r in con:
        rat = r.fm.get("ratification") or {}
        sealed = "✓ ratified" if rat.get("content_seal") else "✗ UN-RATIFIED"
        who = f"{rat.get('by', '?')}, {rat.get('date', '?')}" if rat else "—"
        out.append(f"  {r.id}  [{sealed}]")
        out.append(f"    title:    {r.title}")
        out.append(f"    governs:  {_governs(r)}")
        out.append(f"    ratified: {who}")
        dh = rat.get("debate_hash")
        if dh:
            tpath = provenance.transcript_path(root, r.id)
            ok = "✓" if tpath.is_file() and provenance.transcript_hash(tpath) == dh else "✗ DRIFT"
            out.append(f"    debate:   {dh} ({ok}, .fux/debates/{r.id}.md)")
        viol = by_rule.get(r.id, [])
        if viol:
            for f in viol:
                out.append(f"    ✗ {f.kind}: {f.message}")
        else:
            out.append("    ✔ no violations")
        out.append("")
    out.append("✗ apex has blocking violations — see above." if findings
               else "✔ apex clean — every constitutional rule is ratified and in sync.")
    return "\n".join(out)
