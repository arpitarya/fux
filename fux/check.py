"""`fux check` — validate schema, refs, staleness, conflicts; write DRIFT.md. plan §8/§10."""
from __future__ import annotations

import re
from pathlib import Path

from fux import config, gitutil, governance, loader, paths, schema, seal
from fux.findings import Finding
from fux.model import Rule

REF_RE = re.compile(r"^([^#]+)(?:#L(\d+)(?:-L?(\d+))?)?$")


def run(root: Path) -> list[Finding]:
    fp = paths.Footprint(root)
    cfg = config.load(fp.config)
    rs = loader.resolve(root, cfg)
    layered = loader.load_all_layers(root, cfg)
    findings: list[Finding] = []
    for r in rs.rules:
        findings += _schema(r)
        findings += _refs(r, root)
        findings += _stale(r, root)
        findings += _memory_decay(r, cfg)
        findings += _seal(r, root)
    findings += _conflicts(layered)
    findings += _extractor_drift(fp)
    tier_of = {r.id: str(r.fm.get("tier", "standard")) for r in rs.rules}
    for f in findings:
        f.tier = tier_of.get(f.rule_id, "standard")   # constitution layer (plan §6)
    findings.sort(key=lambda f: (f.kind, f.rule_id, f.message))  # canonical → baseline diff
    _write_drift(fp, findings)
    return findings


def _extractor_drift(fp) -> list[Finding]:
    """Advisory: graph.json was built with a different non-Python extractor than
    the one available now (e.g. committed with the [ast] extra, but it's not
    installed here). Keeps Fux honestly reproducible — the divergence is surfaced,
    not silent (plan §19a). Non-blocking; a `fux build` reconciles it."""
    import json

    from fux import astextract
    f = fp.out / "graph.json"
    if not f.exists():
        return []
    try:
        stored = json.loads(f.read_text(encoding="utf-8")).get("meta", {}).get("extractor")
    except (OSError, ValueError):
        return []
    if stored is None:
        return []
    current = astextract.backend_fingerprint()
    if stored != current:
        return [Finding("extractor-drift", "graph.json",
                        f"graph built with {stored.get('non_python', '?')} "
                        f"({stored.get('grammars', 'n/a')}), but this machine has "
                        f"{current.get('non_python', '?')} — run `fux build` to reconcile")]
    return []


def _memory_decay(r: Rule, cfg: dict) -> list[Finding]:
    if governance.is_decayed(r, cfg):
        return [Finding("memory-stale", r.id,
                        f"memory untouched > {governance.ttl(cfg)}d — re-confirm or deprecate")]
    return []


def _schema(r: Rule) -> list[Finding]:
    return [Finding("schema", r.id, e) for e in schema.validate(r.fm)]


def _seal(r: Rule, root: Path) -> list[Finding]:
    """A sealed rule whose governed code changed *structure* (plan §17.22).

    Advisory only — re-affirmed by a human via `fux seal <id>`, never auto-fixed.
    """
    stored = r.fm.get("seal")
    if not stored:
        return []
    actual = seal.current(root, r)
    if actual is None or actual == stored:
        return []
    return [Finding("unsealed", r.id,
                    "governed code changed structurally since sealed — review, "
                    "then `fux seal " + r.id + "` to re-affirm")]


def _refs(r: Rule, root: Path) -> list[Finding]:
    out: list[Finding] = []
    for ref in r.code_refs:
        m = REF_RE.match(ref.strip())
        rel = (m.group(1) if m else ref).rstrip("/")
        if not (root / rel).exists():
            out.append(Finding("dead-ref", r.id, f"code_ref missing: {rel}", fixable=True))
    return out


def _stale(r: Rule, root: Path) -> list[Finding]:
    if not gitutil.is_repo(root):
        return []
    updated = str(r.fm.get("updated") or r.fm.get("created") or "")
    out: list[Finding] = []
    for ref in r.code_refs:
        m = REF_RE.match(ref.strip())
        rel = (m.group(1) if m else ref).rstrip("/")
        target = root / rel
        if not target.exists():
            continue
        commit = gitutil.last_commit_date(target, root)
        if commit and updated and commit > updated:
            if r.type in ("task", "spec") and r.status not in ("done",):
                out.append(Finding("plan-drift", r.id,
                                   f"{r.type} not done but {rel} changed {commit} > updated {updated}"))
            else:
                out.append(Finding("stale", r.id,
                                   f"{rel} changed {commit} > rule updated {updated}", fixable=True))
    return out


def _conflicts(layered: list[Rule]) -> list[Finding]:
    out: list[Finding] = []
    seen: dict[str, Rule] = {}
    for r in layered:
        if r.id in seen and seen[r.id].layer != r.layer:
            out.append(Finding("conflict", r.id,
                              f"defined in both {seen[r.id].layer} and {r.layer} (project wins)"))
        seen[r.id] = r
    by_id = {r.id: r for r in layered}
    for r in layered:
        for target in r.edges().get("contradicts", []):
            if target in by_id:
                out.append(Finding("conflict", r.id, f"explicitly contradicts {target}"))
    return out


def _write_drift(fp: paths.Footprint, findings: list[Finding]) -> None:
    lines = ["# Fux DRIFT report", "",
             f"_{len(findings)} finding(s)._" if findings else "_No drift — all rules current._", ""]
    for kind in ("schema", "dead-ref", "conflict", "stale", "plan-drift", "invariant",
                 "memory-stale", "unsealed", "extractor-drift"):
        group = [f for f in findings if f.kind == kind]
        if group:
            lines.append(f"## {kind} ({len(group)})")
            lines += [f"- {f.rule_id}: {f.message}" for f in group]
            lines.append("")
    fp.out_file("DRIFT.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
