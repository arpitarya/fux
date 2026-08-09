"""`.fux/CANDIDATES.md` — the persistent shared review surface for draft candidates.

One Markdown table, one row per draft (proposed rule, mined invariant, ingested
draft) with triage state `pending|accepted|rejected`. PERSISTENT (survives `fux
build`/`check`) and NEVER blocks — `check`/`stats` only print a one-line pointer.
Dedup is vs existing active rules AND the queue; drafts-with-why sort first, `why:
TODO` last. $0, stdlib — the agent supplies content, the engine just files it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from fux import paths

CANDIDATES_REL = "CANDIDATES.md"
TODO = "TODO"
_COLS = ["cid", "kind", "source", "state", "why_source", "code_refs", "why", "title"]
_HEADER = "| " + " | ".join(_COLS) + " |"
_SEP = "| " + " | ".join(["---"] * len(_COLS)) + " |"
_DOC = ("Every row is a `status: draft` proposal awaiting triage — nothing here is "
        "active. Accept (`fux candidates accept <id>`) → active rule; reject drops it. "
        "Drafts-with-why first, `why: TODO` last. This surface NEVER blocks.")


@dataclass
class Candidate:
    kind: str                      # proposed rule type (convention|rule|invariant|…)
    title: str                     # the proposed rule statement (one line)
    why: str = ""                  # recovered why, or TODO (flagged, sorts last)
    why_source: str = ""           # session | "commit <hash>" | "PR #n" | …
    source: str = "session"        # session | mine | git | ingest
    code_refs: list[str] = field(default_factory=list)
    state: str = "pending"         # pending | accepted | rejected
    cid: str = ""

    def key(self) -> str:
        return _key(self.code_refs, self.title)

    def with_id(self) -> "Candidate":
        self.cid = self.cid or hashlib.sha1(self.key().encode()).hexdigest()[:8]
        return self

    def has_why(self) -> bool:
        return bool(self.why) and self.why != TODO

    def row(self) -> str:
        vals = [self.cid, self.kind, self.source, self.state, self.why_source,
                "; ".join(self.code_refs), self.why, self.title]
        return "| " + " | ".join(_cell(v) for v in vals) + " |"


def path_of(root: Path) -> Path:
    return paths.Footprint(root).base / CANDIDATES_REL


def read(root: Path) -> list[Candidate]:
    p = path_of(root)
    if not p.exists():
        return []
    out: list[Candidate] = []
    for line in (l.strip() for l in p.read_text(encoding="utf-8").splitlines()):
        if not line.startswith("|") or line == _HEADER or set(line) <= set("|- "):
            continue
        cells = [_uncell(c.strip()) for c in line.strip("|").split("|")]
        if len(cells) != len(_COLS):
            continue
        d = dict(zip(_COLS, cells))
        out.append(Candidate(
            kind=d["kind"], title=d["title"], why=d["why"], why_source=d["why_source"],
            source=d["source"], state=d["state"], cid=d["cid"],
            code_refs=[r.strip() for r in d["code_refs"].split(";") if r.strip()]))
    return out


def write(root: Path, items: list[Candidate]) -> None:
    p = path_of(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(["# Fux — candidate rules (persistent review surface)", "",
                 _DOC, "", _HEADER, _SEP, *[it.row() for it in _sorted(items)]]) + "\n",
                 encoding="utf-8")


def add(root: Path, new: list[Candidate], cap: int = 10) -> list[Candidate]:
    """Dedup vs existing active rules + the queue, cap per run, append as pending."""
    existing = read(root)
    seen = _rule_keys(root) | {c.key() for c in existing}
    added: list[Candidate] = []
    for c in sorted(new, key=lambda c: not c.has_why()):   # why-density: keep why-ful first
        c.with_id()
        if c.key() in seen:
            continue
        seen.add(c.key())
        added.append(c)
        if len(added) >= cap:
            break
    if added:
        write(root, existing + added)
    return added


def set_state(root: Path, cid: str, state: str) -> Candidate | None:
    items = read(root)
    for c in items:
        if c.cid == cid:
            c.state = state
            write(root, items)
            return c
    return None


def render(root: Path, pending: bool = False, why_todo: bool = False) -> str:
    items = _sorted(read(root))
    n = sum(c.state == "pending" for c in items)
    if pending:
        items = [c for c in items if c.state == "pending"]
    if why_todo:
        items = [c for c in items if c.why == TODO]
    if not items:
        return "No candidates — run `fux propose-rules --retro` or the propose-rules skill."
    body = [f"  [{c.state:8}] {c.cid}  ({c.source}/{c.kind}) {c.title}"
            f"{'  ⚑ why: TODO' if c.why == TODO else ''}"
            f"{('  [' + ', '.join(c.code_refs[:3]) + ']') if c.code_refs else ''}"
            for c in items]
    return "\n".join([f"Candidates: {len(items)} shown · {n} pending  ({path_of(root)})", *body])


def pending_count(root: Path) -> int:
    return sum(c.state == "pending" for c in read(root))


def pointer(root: Path) -> str:
    n = pending_count(root)
    return f"{n} draft(s) pending review → {CANDIDATES_REL}" if n else ""


def _rule_keys(root: Path) -> set[str]:
    from fux import config, loader
    rules = loader.resolve(root, config.load(paths.Footprint(root).config)).rules
    return {_key(r.code_refs, r.title) for r in rules}


def _sorted(items: list[Candidate]) -> list[Candidate]:
    return sorted(items, key=lambda c: (not c.has_why(), c.state != "pending", c.cid))

def _key(code_refs: list[str], title: str) -> str:
    """Dedup key: the code_refs set (line-stripped), else a title slug."""
    refs = tuple(sorted(r.split("#")[0].split(":")[0].strip() for r in code_refs if r.strip()))
    return "·".join(refs) if refs else _slug(title)

def _slug(s: str) -> str:
    return "-".join("".join(ch if ch.isalnum() else " " for ch in s.lower()).split()[:6])

def _cell(v: str) -> str:
    return str(v).replace("|", "\\|").replace("\n", " ").strip() or "—"

def _uncell(v: str) -> str:
    return "" if v == "—" else v.replace("\\|", "|")
