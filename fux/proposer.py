"""`fux propose-rules` — deterministic retro proposer + the forward-pass gate ($0).

RETRO (`--retro`): `fux mine` surfaces latent invariants (AST, $0); the why is
recovered from the git commit subjects touching the literal's sites. FORWARD
(`--from` JSON): the host agent reads the diff + its rationale and drafts
candidates-with-why (its tokens, like `/fux distill`); the engine only gates +
dedups + files them. The §4 gate: a rule with a recoverable why → draft; a genuine
invariant with no why → `why: TODO` (flagged, sorts last); a pure code-restatement
→ dropped. NOTHING here authors an active or constitutional rule — every candidate
is a `status: draft`, `tier: standard` proposal for human triage. No LLM, no
network on this path (guard test).
"""
from __future__ import annotations

from pathlib import Path

from fux import candidates, config, gitutil, mine, paths

CAP = 10                       # max drafts appended per run (§2: capped per run)


def retro(root: Path, cap: int = CAP) -> list[candidates.Candidate]:
    """Mine AST candidates + recover their why from git history; gate, dedup, cap."""
    cfg = config.load(paths.Footprint(root).config)
    out: list[candidates.Candidate] = []
    for c in mine.mine(root, cfg):
        why, src = _git_why(root, c.sites)
        out.append(candidates.Candidate(
            kind="convention", source="mine",
            title=f"name the magic number {c.key} ({len(c.sites)}× — extract a constant)",
            why=why or candidates.TODO, why_source=src,
            code_refs=c.sites[:6]))
    return candidates.add(root, out, cap)


def from_json(root: Path, payload: list[dict], cap: int = CAP) -> list[candidates.Candidate]:
    """Gate + file agent-drafted forward candidates (the §4 quality gate)."""
    drafts = [c for c in (gate(d) for d in payload) if c is not None]
    return candidates.add(root, drafts, cap)


def gate(d: dict) -> candidates.Candidate | None:
    """§4 gate. Returns a draft Candidate, or None to drop.

    Each item: {kind, title, why?, why_source?, code_refs?, invariant?: bool}.
    No why and not a flagged invariant ⇒ pure code-restatement ⇒ dropped. A genuine
    invariant with no why ⇒ draft with `why: TODO`. A why present ⇒ draft-with-why.
    """
    why = (d.get("why") or "").strip()
    if not why and not d.get("invariant"):
        return None                                   # pure code-restatement → drop
    return candidates.Candidate(
        kind=d.get("kind", "rule"), title=(d.get("title") or "").strip(),
        why=why or candidates.TODO,                   # invariant w/o why → flagged TODO
        why_source=(d.get("why_source") or ("session" if why else "")),
        source=d.get("source", "session"), code_refs=list(d.get("code_refs") or []))


def _git_why(root: Path, sites: list[str]) -> tuple[str, str]:
    """The most recent commit subject touching a site file → a recoverable why."""
    if not gitutil.is_repo(root):
        return "", ""
    for site in sites:
        rel = site.split(":")[0]
        hist = gitutil.file_history(root / rel, root, limit=1)
        if hist:
            _date, h, subject = hist[0]
            return subject, f"commit {h}"
    return "", ""
