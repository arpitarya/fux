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
LINT_KINDS = ["no-why", "no-code-refs", "dangling-edge", "no-provenance",
              "stub-body", "overlap-unlinked"]
_WHY = re.compile(r"\*\*\s*why[\s:：]*\*\*", re.I)
_REF = re.compile(r"^([^#]+)(?:#L(\d+)(?:-L?(\d+))?)?$")


def run(root: Path) -> list[Finding]:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    ids = {r.id for r in rs.rules}
    out: list[Finding] = []
    active = rs.active()
    for r in active:
        out += _lint_one(r, ids)
    out += _overlaps(active)
    return out


def _spans(r: Rule) -> list[tuple[str, int, int]]:
    """(file, lo, hi) for each code_ref; whole-file refs span (0, ∞)."""
    out: list[tuple[str, int, int]] = []
    for ref in r.code_refs:
        m = _REF.match(ref.strip())
        if not m:
            continue
        lo = int(m.group(2)) if m.group(2) else 0
        hi = int(m.group(3)) if m.group(3) else (lo if lo else 10 ** 9)
        out.append((m.group(1).rstrip("/"), lo, hi))
    return out


def _linked(a: Rule, b: Rule) -> bool:
    """True if the two rules already acknowledge each other (related or any edge)."""
    refs_a = set(a.related) | {t for ts in a.edges().values() for t in ts}
    refs_b = set(b.related) | {t for ts in b.edges().values() for t in ts}
    return b.id in refs_a or a.id in refs_b


def _overlaps(active: list[Rule]) -> list[Finding]:
    """Two unlinked rules governing the same code span — silent-contradiction risk.

    Deterministic guard for "stale knowledge silently lies" (plan §17.20b): suggests
    a human draw a `supersedes:`/`contradicts:` edge (or merge). Advisory only.
    """
    out: list[Finding] = []
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            if _linked(a, b):
                continue
            if any(fa == fb and la <= hb and lb <= ha
                   for fa, la, ha in _spans(a) for fb, lb, hb in _spans(b)):
                out.append(Finding("overlap-unlinked", a.id,
                                   f"governs the same code as '{b.id}' but they are "
                                   "unlinked — add supersedes:/contradicts: or merge"))
                break
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
