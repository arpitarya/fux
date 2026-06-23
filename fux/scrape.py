"""Opt-in scrape re-verification — `fux scrape <id> --recheck` (handoff §A.5).

NETWORK-TOUCHING and lazily imported: nothing here runs on the default `fux check`
path. It re-fetches a drafted rule's `source`, recomputes the canonical
`source_hash`, and raises a `source-drift` finding when the page changed since
`fetched`. The fetch itself reuses `fetchrules` (stdlib urllib); turning the new
text back into rule prose is the host agent's job, never the engine's.

`source_hash` is `sha256(normalised-extracted-text)[:16]` — the same recipe the
scrape skill uses when it drafts, so a recheck is an apples-to-apples comparison.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fux import config, loader, paths
from fux.findings import Finding


def source_hash(text: str) -> str:
    """Canonical content hash: whitespace-collapsed, lower-cased, sha256[:16]."""
    norm = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def recheck(root: Path, rule_id: str | None = None) -> list[Finding]:
    """Re-fetch every drafted rule with a `source` (or just `rule_id`) and diff hashes."""
    from fux import fetchrules        # lazy: keeps urllib off every other import path
    cfg = config.load(paths.Footprint(root).config)
    rules = loader.resolve(root, cfg).rules
    findings: list[Finding] = []
    for r in rules:
        src = r.fm.get("source")
        if not src or (rule_id and r.id != rule_id):
            continue
        stored = str(r.fm.get("source_hash") or "")
        try:
            text = fetchrules.fetch_text(str(src))
        except fetchrules.FetchError as exc:
            findings.append(Finding("source-drift", r.id, f"could not re-fetch {src}: {exc}"))
            continue
        current = source_hash(text)
        if stored and current != stored:
            findings.append(Finding(
                "source-drift", r.id,
                f"source {src} changed since fetched {r.fm.get('fetched', '?')} "
                f"({stored} → {current}) — re-read it and re-draft, then re-ratify if it binds"))
    return findings


def recheck_cmd(root: Path, rule_id: str | None = None) -> int:
    findings = recheck(root, rule_id)
    for f in findings:
        print(f.line())
    if not findings:
        print("✔ No source-drift — drafted sources unchanged since fetched.")
    return 0
