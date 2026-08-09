"""§5b migration guard — snapshot findings, surface only the NEW ones ($0).

A *transient* upgrade guard, not a regression subsystem: `fux check --baseline-write`
snapshots current findings (canonical: kind, rule_id, message) pre-upgrade; `fux gate
--baseline` re-runs and fails only on findings absent from the snapshot, so a backward-
compatible upgrade is provably a no-op. Reuses the `Finding` serialization; stdlib only.
"""
from __future__ import annotations

from pathlib import Path

from fux.findings import Finding


def _sig(f: Finding) -> str:
    return f"{f.kind}\t{f.rule_id}\t{f.message}"


def write(path: Path, findings: list[Finding]) -> int:
    """Snapshot findings canonically sorted. Returns the count written."""
    sigs = sorted(_sig(f) for f in findings)
    path.write_text("\n".join(sigs) + ("\n" if sigs else ""), encoding="utf-8")
    return len(sigs)


def _read(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


def new_findings(path: Path, findings: list[Finding]) -> list[Finding]:
    """Findings absent from the baseline snapshot — the upgrade's new ones."""
    base = _read(path)
    return [f for f in findings if _sig(f) not in base]
