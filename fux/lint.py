"""`fux lint` — rule *quality* checks, complementary to `fux check` ($0).

`check` validates structure (schema / refs / staleness / conflicts). `lint` judges
whether a rule earns its weight: does it carry the **why**, link to the code it
governs, point at real neighbours, and bear provenance? Advisory by default — it's
authoring guidance, not a gate (use `fux gate --strict-lint` to enforce).
"""
from __future__ import annotations

import re
from pathlib import Path

from fux import config, loader, paths
from fux.findings import Finding
from fux.model import LONGFORM, Rule

# Types that should ground in code (business-logic rules). glossary/convention/
# regulatory/narrative/memory are knowledge, not code-bound.
CODE_BOUND = {"rule", "formula", "invariant", "edge-case"}
LINT_KINDS = ["no-why", "no-code-refs", "dangling-edge", "no-provenance", "stub-body"]
_WHY = re.compile(r"\*\*\s*why[\s:：]*\*\*", re.I)


def run(root: Path) -> list[Finding]:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    ids = {r.id for r in rs.rules}
    out: list[Finding] = []
    for r in rs.active():
        out += _lint_one(r, ids)
    return out


def _lint_one(r: Rule, ids: set[str]) -> list[Finding]:
    out: list[Finding] = []
    body = r.body.strip()
    if r.type not in LONGFORM and not _WHY.search(r.body):
        out.append(Finding("no-why", r.id, "no **Why:** in the body — the why is the point"))
    if r.type in CODE_BOUND and not r.code_refs:
        out.append(Finding("no-code-refs", r.id, f"{r.type} with no code_refs (ungrounded)"))
    for rel in r.related:
        if rel not in ids:
            out.append(Finding("dangling-edge", r.id, f"related → unknown rule '{rel}'"))
    for kind, targets in r.edges().items():
        for t in targets:
            if t not in ids:
                out.append(Finding("dangling-edge", r.id, f"{kind} → unknown rule '{t}'"))
    if not (r.fm.get("created") and r.fm.get("updated")):
        out.append(Finding("no-provenance", r.id, "missing created/updated"))
    if len(body) < 30 or body.endswith(":") or "…" in body:
        out.append(Finding("stub-body", r.id, "body looks like an unfilled stub"))
    return out
