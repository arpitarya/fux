"""Provenance drift — a ratified debate transcript is immutable evidence ($0, no LLM; plan §7a, 3b).

`fux ratify --debate <file>` pins the transcript at `.fux/debates/<id>.md` and stamps its hash
into `ratification.debate_hash`. `check_provenance` re-hashes that file on every `fux check` and
fires an always-blocking `tampered` finding when it drifts — for constitutional rules only. A
transcript is corrected by re-ratification, never by editing the file. Stdlib only, deterministic.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from fux.findings import Finding
from fux.model import Rule


def transcript_hash(path: Path) -> str:
    """The canonical debate-transcript fingerprint — sha256 of the raw bytes (prose, no AST)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def transcript_path(root: Path, rule_id: str) -> Path:
    """Where a ratified rule's immutable transcript lives."""
    return root / ".fux" / "debates" / f"{rule_id}.md"


def check_provenance(root: Path, rules: list[Rule]) -> list[Finding]:
    """`tampered` when a ratified constitutional rule's debate transcript drifts from its stamped
    `debate_hash` (missing file, or hash mismatch). Constitutional rules only."""
    out: list[Finding] = []
    for r in rules:
        if str(r.fm.get("tier")) != "constitutional":
            continue
        stamped = (r.fm.get("ratification") or {}).get("debate_hash")
        if not stamped:
            continue
        tpath = transcript_path(root, r.id)
        if not tpath.is_file():
            out.append(Finding("tampered", r.id,
                               f"debate transcript missing (.fux/debates/{r.id}.md) — "
                               "ratified provenance cannot be verified"))
        elif transcript_hash(tpath) != stamped:
            out.append(Finding("tampered", r.id,
                               "debate transcript changed since ratification — provenance is "
                               "immutable evidence; correct by re-ratification, never by editing"))
    return out
